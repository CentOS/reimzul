#!/usr/bin/env python

import sys
import beanstalkc
import json
import os
import subprocess
import commands
import time

# Some variables
reimzul_repo_basedir = '/srv/reimzul/bstore/repo/'
reimzul_tosign_basedir = '/srv/reimzul/bstore/tosign/'


def main():
    bs_connection = False
    while True:
        try:
            if not bs_connection:
                bs = beanstalkc.Connection(connect_timeout=2)
                bs.watch('tosign')
            bs_connection = True
            print 'Waiting for jobs in queue tosign'

            job = bs.reserve()
            jbody = json.loads(job.body)

            job.delete()
            src_dir = reimzul_repo_basedir + \
                jbody['target'] + '/' + jbody['pkgname'] + \
                '/' + jbody['timestamp'] + '/'
            target_dir = reimzul_tosign_basedir + jbody['target'] + '/'
            print "Copying RPM pkgs from %s to %s" % (src_dir, target_dir)
            copy_cmd = "test -d %s || mkdir -p %s ; find %s -iname '*.rpm' -exec cp {} %s \;" % (
                target_dir, target_dir, src_dir, target_dir)
            process = subprocess.call(copy_cmd, shell=True)

        except beanstalkc.SocketError:
            bs_connection = False
            time.sleep(2)
            continue

if __name__ == '__main__':
    main()
