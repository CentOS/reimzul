#!/usr/bin/env python

import sys
import beanstalkc
import json
import os
import subprocess, commands

# Some variables
reimzul_repo_basedir = '/srv/reimzul/bstore/repo/'
reimzul_repo_cachedir = '/srv/reimzul/bstore/repo/'


bs = beanstalkc.Connection(connect_timeout=2)
bs.watch('createrepo')

while True:
  job = bs.reserve()
  jbody = json.loads(job.body)

  job.delete()
  repodir = reimzul_repo_basedir + jbody['target'] + '/'
  print "Generating repodata in %s" % repodir
  createrepo_cmd = "/usr/bin/createrepo_c -d --update --workers 16 --cachedir %s %s" % (reimzul_repo_cachedir, repodir)
  process = subprocess.call(createrepo_cmd, shell=True)
