# Reimzul Git repository #
This git repository will host the code/scripts used to build CentOS distro for various arches
All processes are launched on all nodes with unprivileged user "reimzul"

## Overview
![Reimzul schema](/docs/Reimzul.png)

Reimzul consists only of some python scripts, that are used as wrappers around mock.

The following components are used to orchestrate the builds and notifications:
 * [beanstalkd](http://kr.github.io/beanstalkd/) : used as build queues, per arches
 * [stunnel](http://www.stunnel.org/) : all components are using TLS connections , so including workers connecting to beanstalkd, to "watch" the queues and pick the build jobs landing in those queues, as well as for http (to retrieve the src.rpm to build) and then also for rsync (transferring artifacts - logs,rpm - to bstore node)
 * MQTT : python-paho-mqtt : sending results to a mqtt broker, with other subscribers used for notifications (including IRC)
 * [MongoDB](http://www.mongodb.org) : just use as document store to load build results and so be able to track/query build history

## Controller
This is the node that runs beanstalkd for the various tubes/queues
To build a .src.rpm, it has to be uploaded under /srv/reimzul/incoming

From that point, one can use /srv/reimzul/code/reimzul_submit.py (it has embedded help with --help or when called with no args)
Example when willing to submit same src.rpm (already uploaded !) to multiple arches :
```
for arch in x86_64 aarch64 armhfp ; do /srv/reimzul/code/reimzul_submit.py -s time-1.7-45.el7.src.rpm -d .el7 -a $arch -t c7.1708.u ; done
```
Important to know that there is no need to submit for i386 : it will be done automatically in parallel on the builder doing the x86_64 build, with the same timestamp

The controller has also a dispatcher worker (msg_dispatcher.py) that watches the notify tube, and will :
 * send mails to specific rcpts for each failed/successful build
 * log to /var/log/reimzul/reimzul.log
 * add each job to local mongodb instance
 * also send json payload over mqtt (so then various subscribers can reuse those payloads, including for example for irc notifications)

To control those notifications, reimzul uses a config file /etc/reimzul/reimzul.ini (see reimzul.ini.sample for reference)

## Builders (workers) : 
 * reimzul_worker.py

These nodes are the ones that :
 * watch for jobs in $arch (exception being x86_64, watching also i386 tube)
 * download the src.rpm from controller (stunnel)
 * submit it to mock
 * upload results to bstore node (central http repo holding all the repositories)
 * sending results back in notify tube

## Bstore :
 * tosign_worker.py
 * repogen_worker.py

Central storage node that will accept all build artifacts under specific target repos.
Worth noting that all communication, including rsyncd, happen over tls (through stunnel)
It has also a worker itself, just watching the "createrepo" channel.
When a build finishes and has a successful build, one job is added to the createrepo tube (you can have multiple parallel workers for this too) and repo metadata is launched through createrepo_c, with multiple workers per process and cache directory

## Client

Actually the only way to submit builds to Reimzul is to launch reimzul_submit.py : 
```
usage: reimzul_submit.py [-h] -s SRPM -a ARCH -t TARGET -d DISTTAG [--now]
                         [--scratch]

Reimzul CentOS distributed build client

optional arguments:
  -h, --help            show this help message and exit
  -s SRPM, --srpm SRPM  The src.rpm pkg already uploaded in controller node
  -a ARCH, --arch ARCH  Defines the mock architecture to build against
                        [example: x86_64,armhfp,aarch64,i386,ppc64le,ppc64]
  -t TARGET, --target TARGET
                        The target repo to build against/for, without any arch
                        specified [example: c7.1708.u]
  -d DISTTAG, --disttag DISTTAG
                        Defines the mock disttag to use [example: .el7_4]
  --now                 Will prioritize this job in front of the build queue
  --scratch             Will just build the pkg but not prepare it in staging-
                        tosign area
```

That means that first a src.rpm package is prepared in the /srv/reimzul/incoming directory, and then reimzul_submit.py is called to queue the rebuild in the different arch workers/tubes (using beanstalk)

