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


bs = beanstalkc.Connection(connect_timeout=2)

bs.watch(builder_arch)

def bs_notify(jbody):
  bs.use('notify')
  bs.put(json.dumps(jbody))

def bs_createrepo(jbody):
  bs.use('createrepo')
  bs.put(json.dumps(jbody))

def main():
  while os.path.isfile('stop') == False:
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
    hdr = ts.hdrFromFdno(rpm_file)
    os.close(rpm_file)
    jbody['evr'] = hdr[rpm.RPMTAG_VERSION] +'-'+ hdr[rpm.RPMTAG_RELEASE]
    jbody['pkgname'] = hdr[rpm.RPMTAG_NAME]
    jbody['timestamp'] = timestamp  
    bs_notify(jbody)

    # launching job
    build_cmd = "/srv/build/code/submit_mock.sh -s %s -d %s -t %s -a %s -p %s" % (local_srpm, jbody['disttag'], jbody['target'], jbody['arch'], timestamp)
    print build_cmd
    print jbody['evr']
    process = subprocess.call( build_cmd, shell = True) 
    if process == 0:
      jbody['status'] = 'Success'
      bs_notify(jbody)
      bs_createrepo(jbody)
    else:
      jbody['status'] = 'Failed'
      bs_notify(jbody)
    shutil.rmtree(tmp_dir)
    time.sleep(1)

if __name__ == '__main__':
  main()

