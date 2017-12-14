#!/usr/bin/env python

import json
import beanstalkc
import sys
import argparse

build_queues = {'x86_64': 'x86_64', 'armhfp': 'armv7l'}

parser = argparse.ArgumentParser(description='Reimzul CentOS distributed build client')

parser.add_argument('-s', action="store", dest="srpm", required=True, help='The src.rpm pkg already uploaded in controller node')
parser.add_argument('-a', action="store", dest="arch", required=True, help='Define the mock architecture to build against')
parser.add_argument('-t', action="store", dest="target", required=True, help='The target repo to build against/for')
parser.add_argument('-d', action="store", dest="disttag", required=True, help='Define the mock disttag to use [example: .el7_4]')

results = parser.parse_args()



bs = beanstalkc.Connection()
job = {}
job['srpm'] = results.srpm
job['arch'] = results.arch
job['target'] = results.target
job['disttag'] = results.disttag
build_queue = build_queues[results.arch]

bs.use(build_queue)
bs.put(json.dumps(job))

print 'Submitted SRPM %s to build queue %s for target %s' % (results.srpm,build_queue,results.target)

