#!/usr/bin/env python

import json
import beanstalkc
import sys


if len(sys.argv) > 1:
    bs = beanstalkc.Connection()
    job = {}
    job['target'] = sys.argv[1]

    bs.use('createrepo')
    bs.put(json.dumps(job))
else:
    print "You should use repo as parameter to this script"
