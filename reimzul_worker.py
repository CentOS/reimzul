#!/usr/bin/env python

import sys
import beanstalkc
import json
import os
import subprocess, commands
import time

builder_arch = os.uname()[4]
builder_fqdn = os.uname()[1]

bs = beanstalkc.Connection(connect_timeout=2)

bs.watch(builder_arch)


while os.path.isfile('stop') == False:
  print 'Waiting for jobs in queue %s' % builder_arch
  job = bs.reserve()
  jbody = json.loads(job.body)

  job.delete()
  print "building %s for arch %s on builder %s" % (jbody['srpm'],jbody['arch'],builder_fqdn)
  build_cmd = "/srv/build/code/submit_mock.sh -s %s -d %s -t %s -a %s" % (jbody['srpm'], jbody['disttag'], jbody['target'], jbody['arch'])
  print build_cmd
  process = subprocess.call( build_cmd, shell = True) 
  time.sleep(1)

