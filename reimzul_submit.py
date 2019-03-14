#!/usr/bin/env python

import json
import beanstalkc
import sys
import argparse
import getpass

# Build queue dictionnary : arched asked and mapped to queue
build_queues = {'x86_64': 'x86_64', 'noarch': 'noarch', 'armhfp': 'armv7l', 'aarch64': 'aarch64', 'i386': 'i386', 'i686': 'i386', 'ppc64': 'ppc64', 'ppc64le': 'ppc64le', 'ppc': 'ppc'}

parser = argparse.ArgumentParser(description='Reimzul CentOS distributed build client')

parser.add_argument('-s', '--srpm', action="store", dest="srpm", required=True, help='The src.rpm pkg already uploaded in controller node')
parser.add_argument('-a', '--arch', action="store", dest="arch", required=True, help='Defines the mock architecture to build against [example: x86_64,armhfp,aarch64,i386,ppc64le,ppc64]')
parser.add_argument('-t', '--target', action="store", dest="target", required=True, help='The target repo to build against/for, without any arch specified [example: c7.1708.u]')
parser.add_argument('-d', '--disttag', action="store", dest="disttag", required=True, help='Defines the mock disttag to use [example: .el7_4]')
parser.add_argument('--now', action="store_true", help='Will prioritize this job in front of the build queue')
parser.add_argument('--scratch', action="store_true", help='Will just build the pkg but not prepare it in staging-tosign area')

results = parser.parse_args()

if results.now:
  bs_priority = 1024
else:
  bs_priority = 8192

bs = beanstalkc.Connection()
job = {}
job['srpm'] = results.srpm
job['arch'] = results.arch
job['target'] = results.target+'.'+results.arch
job['disttag'] = results.disttag
job['scratch'] = results.scratch
job['submitter'] = getpass.getuser()
build_queue = build_queues[results.arch]

bs.use(build_queue)
bs.put(json.dumps(job), priority=bs_priority)

print 'Submitted SRPM %s to build queue %s for target %s (scratch: %s) by %s' % (results.srpm,build_queue,job['target'],job['scratch'],job['submitter'])

