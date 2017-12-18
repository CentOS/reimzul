# Reimzul Git repository #
This git repository will host the code/scripts used to build CentOS distro for various arches
All processes are launched on all nodes with unprivileged user "reimzul"

## Controller
This is the node that runs beanstalkd for the various tubes/queues
To build a .src.rpm, it has to be uploaded under /srv/reimzul/incoming

From that point, one can use /srv/reimzul/code/reimzul_submit.py (it has embedded help with --help or when called with no args)
Example when willing to submit same src.rpm (already uploaded !) to multiple arches :
```
for arch in x86_64 aarch64 armhfp ; do /srv/reimzul/code/reimzul_submit.py -s time-1.7-45.el7.src.rpm -d .el7 -a $arch -t c7.1708.u ; done
```
Important to know that there is no need to submit for i386 : it will be done automatically in parallel on the builder doing the x86_64 build, with the same timestamp

The controller has also a dispatcher worker that watches the notify tube, and will :
 * send mails to specific rcpts for each failed/successful build
 * log to /var/log/reimzul/reimzul.log
 * add each job to local mongodb instance

## Builders (workers)

These nodes are the ones that :
 * watch for jobs in $arch (exception being x86_64, watching also i386 tube)
 * download the src.rpm from controller (stunnel)
 * submit it to mock
 * upload results to bstore node (central http repo holding all the repositories)
 * sending results back in notify tube

## Bstore

Central storage node that will accept all build artifacts under specific target repos.
Worth noting that all communication, including rsyncd, happen over tls (through stunnel)
It has also a worker itself, just watching the "createrepo" channel.
When a build finishes and has a successful build, one job is added to the createrepo tube.
repo metadata is launched through createrepo_c, with multiple workers per process and cache directory

