#!/usr/bin/env python

import sys
import beanstalkc
import json
import os
import subprocess, commands
import time

# Some variables
reimzul_repo_basedir = '/srv/reimzul/bstore/repo/'
reimzul_repo_cachedir = '/srv/reimzul/bstore/cache/'


def main():
  bs_connection = False
  while True:
    try:
      if not bs_connection:
        bs = beanstalkc.Connection(connect_timeout=2)
        bs.watch('createrepo')
      bs_connection = True
      print 'Waiting for jobs in queue createrepo'

      job = bs.reserve()
      jbody = json.loads(job.body)

      job.delete()
      repodir = reimzul_repo_basedir + jbody['target'] + '/'
      print "Generating repodata in %s" % repodir
      createrepo_cmd = "test -d %s || mkdir -p %s ; /usr/bin/createrepo_c -d --update --workers 16 --cachedir %s %s" % (repodir, repodir, reimzul_repo_cachedir, repodir)
      process = subprocess.call(createrepo_cmd, shell=True)

    except beanstalkc.SocketError:
      bs_connection = False
      time.sleep(2)
      continue

if __name__ == '__main__':
  main()
