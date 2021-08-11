#!/usr/bin/env python

import sys
import beanstalkc
import json
import os
import subprocess, commands
import time
import tempfile
import rpm
import urllib
import shutil

# Some variables
builder_arch = os.uname()[4]
builder_fqdn = os.uname()[1]
srpm_baseurl = 'http://localhost:11080/reimzul-incoming/'

def bs_notify(bs,jbody):
  bs.use('notify')
  bs.put(json.dumps(jbody))

def bs_createrepo(bs,jbody):
  bs.use('createrepo')
  bs.put(json.dumps(jbody))

def main():
  bs_connection = False
  while True:
    try:
      if not bs_connection:
        bs = beanstalkc.Connection(connect_timeout=2)
        bs.watch(builder_arch)
        # Special case for x86_64, watching also i386
        if builder_arch == 'x86_64':
          bs.watch('i386')
          bs.watch('noarch')
        if builder_arch == 'ppc64':
          bs.watch('ppc')
      bs_connection = True

      print 'Waiting for jobs in queue %s' % builder_arch
   
      job = bs.reserve()
      jbody = json.loads(job.body)

      job.delete()

      # Notifying controller
      jbody['status'] = 'Building'
      jbody['builder_fqdn'] = builder_fqdn

      print "building %s for arch %s on builder %s" % (jbody['srpm'],jbody['arch'],builder_fqdn)
      timestamp = os.popen('date +%Y%m%d%H%M%S').read().strip('\n')
      tmp_dir = tempfile.mkdtemp()
      remote_srpm = srpm_baseurl + jbody['srpm']
      local_srpm = tmp_dir+'/'+ jbody['srpm']
      urllib.urlretrieve(remote_srpm, local_srpm)
      rpm_file = os.open(local_srpm, os.O_RDONLY)
      ts = rpm.ts()
      ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
      hdr = ts.hdrFromFdno(rpm_file)
      os.close(rpm_file)
      jbody['evr'] = hdr[rpm.RPMTAG_VERSION] +'-'+ hdr[rpm.RPMTAG_RELEASE]
      jbody['pkgname'] = hdr[rpm.RPMTAG_NAME]
      jbody['timestamp'] = timestamp  
      bs_notify(bs,jbody)

      # launching job
      build_cmd = "/srv/reimzul/code/submit_mock.sh -s %s -d %s -t %s -a %s -p %s" % (local_srpm, jbody['disttag'], jbody['target'], jbody['arch'], timestamp)
      print build_cmd
      process = subprocess.call( build_cmd, shell = True) 
      if process == 0:
        jbody['status'] = 'Success'
        bs_notify(bs,jbody)
        bs_createrepo(bs,jbody)
      else:
        jbody['status'] = 'Failed'
        bs_notify(bs,jbody)

      # Specific case : chaining i386/ppc automatically for x86_64/ppc64 builds
      if jbody['arch'] == 'x86_64' or jbody['arch'] == 'ppc64':
        if jbody['arch'] == 'x86_64':
          jbody['arch'] = 'i386'
        if jbody['arch'] == 'ppc64':
         jbody['arch'] = 'ppc'        
        jbody['status'] = 'Building'
        bs_notify(bs,jbody)
        build_cmd = "/srv/reimzul/code/submit_mock.sh -s %s -d %s -t %s -a %s -p %s" % (local_srpm, jbody['disttag'], jbody['target'], jbody['arch'], timestamp)
        print build_cmd
        process = subprocess.call( build_cmd, shell = True) 
        if process == 0:
          jbody['status'] = 'Success'
          bs_notify(bs,jbody)
          bs_createrepo(bs,jbody)
        else:
          jbody['status'] = 'Failed'
          bs_notify(bs,jbody)

     # Specific kernel case (needs noarch builds after x86_64,i386 ones)
      if (jbody['pkgname'] == 'kernel' or jbody['pkgname'] == 'kernel-plus') and (builder_arch == 'x86_64' or builder_arch == 'i386'):
        jbody['arch'] = 'noarch'
        jbody['status'] = 'Building'
        bs_notify(bs,jbody)
        build_cmd = "/srv/reimzul/code/submit_mock.sh -s %s -d %s -t %s -a %s -p %s" % (local_srpm, jbody['disttag'], jbody['target'], jbody['arch'], timestamp)
        print build_cmd
        process = subprocess.call( build_cmd, shell = True) 
        if process == 0:
          jbody['status'] = 'Success'
          bs_notify(bs,jbody)
          bs_createrepo(bs,jbody)
        else:
          jbody['status'] = 'Failed'
          bs_notify(bs,jbody)

 
      shutil.rmtree(tmp_dir)
      time.sleep(1)
    except beanstalkc.SocketError:
      bs_connection = False
      time.sleep(2)
      continue

if __name__ == '__main__':
  main()

