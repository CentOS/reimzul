#!/usr/bin/env python
import beanstalkc

bs = beanstalkc.Connection()

for tube in bs.tubes():
  if 'default' not in tube:
    readyjobs = bs.stats_tube(tube)['current-jobs-ready']
    workers = bs.stats_tube(tube)['current-watching']
    print 'Current job in queue in '+tube+': '+str(readyjobs)
    print 'Number of connected workers for '+tube+': '+str(workers)

