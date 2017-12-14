#!/usr/bin/env python

import json
import beanstalkc
import sys

repo = sys.argv[1]

if len(repo) > 0:
  bs = beanstalkc.Connection()
  job = {}
  job['target'] = sys.argv[1]

  bs.use('createrepo')
  bs.put(json.dumps(job))
else:
  print "you should use this script with repo as paramater"
