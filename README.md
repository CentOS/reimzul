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

### Processes :
  * msg_dispatcher.py

One reimzul notifier worker is enough to send notifications
```
cp systemd/reimzul-notifier.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable reimzul-notifier --now

```


## Builders (workers) : 

These nodes are the ones that :
 * watch for jobs in $arch (exception being x86_64, watching also i386 tube)
 * download the src.rpm from controller (stunnel)
 * submit it to mock
 * upload results to bstore node (central http repo holding all the repositories)
 * sending results back in notify tube

### Processes :
 * reimzul_worker.py 

You can launch as many workers/builder threads you want : there is a .service systemd unit file (see systemd/reimzul-worker@.service) that you can then launch multiple times. For example, let's assume that we want 4 parallel workers : 
```
cp systemd/reimzul-worker@.service /etc/systemd/system/
systemctl daemon-reload
for i in {1..4} ; do systemctl enable reimzul-worker@${i} --now; done

```

## Bstore :

Central storage node that will accept all build artifacts under specific target repos.
Worth noting that all communication, including rsyncd, happen over tls (through stunnel)
It has also a worker itself, just watching the "createrepo" channel.
When a build finishes and has a successful build, one job is added to the createrepo tube (you can have multiple parallel workers for this too) and repo metadata is launched through createrepo_c, with multiple workers per process and cache directory

### Processes
 * tosign_worker.py (will collect built pkgs in a staging area, waiting for pkgs to be then signed)
 * repogen_worker.py (will regenerate repodata on each successful build)

You can launch as many repogen workers threads as you want : there is a .service systemd unit file (see systemd/reimzul-repoogen-worker@.service) that you can then launch multiple times. For example, let's assume that we want 3 parallel workers : 
```
cp systemd/reimzul-repogen-worker@.service /etc/systemd/system/
systemctl daemon-reload
for i in {1..3} ; do systemctl enable reimzul-repogen-worker@${i} --now; done

```

One signer worker is enough (it will just copy the rpm files in a staging area, waiting to be collected for signing)
```
cp systemd/reimzul-signer.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable reimzul-signer --now

```

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

