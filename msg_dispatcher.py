#!/usr/bin/env python
import time
import beanstalkc
import sys
import json
import urllib2
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import pymongo

# Some variables
logfile = '/var/log/reimzul/reimzul.log'
#notify_list = {'x86_64': 'arrfab@centos.org', 'i386': 'arrfab@centos.org', 'armhfp': 'arrfab@centos.org', 'aarch64': 'arrfab@centos.org'}
notify_list = {'x86_64': 'hughesjr@centos.org, arrfab@centos.org', 'i386': 'hughesjr@centos.org, arrfab@centos.org', 'armhfp': 'hughesjr@centos.org, arrfab@centos.org', 'aarch64': 'hughesjr@centos.org, arrfab@centos.org, jperrin@centos.org', 'ppc64': 'hughesjr@centos.org, jpoc@centosproject.org, arrfab@centos.org','ppc64le': 'hughesjr@centos.org, jpoc@centosproject.org, arrfab@centos.org', 'ppc': 'hughesjr@centos.org, arrfab@centos.org, jpoc@centosproject.org'}
email_from = 'buildsys@centos.org'
base_url = 'http://localhost:11081/bstore/repo/'


def log2file(jbody):

  log_file = open(logfile,'a+')
  log_file.write('[%s] Build job SRPM %s (%s) for arch %s builder %s status %s [%s] \r\n' % (time.asctime(),jbody['srpm'],jbody['timestamp'],jbody['arch'],jbody['builder_fqdn'],jbody['status'],jbody['evr']) )
  log_file.close()

def sendmail(jbody):
  arch = jbody['arch']
  email_to = notify_list[arch]
  root_log = urllib2.urlopen("%s/%s/%s/%s/%s.%s/root.log" % (base_url,jbody['target'],jbody['pkgname'],jbody['timestamp'],jbody['evr'],jbody['arch']))
  root_log = root_log.readlines()
  build_log = urllib2.urlopen("%s/%s/%s/%s/%s.%s/build.log" % (base_url,jbody['target'],jbody['pkgname'],jbody['timestamp'],jbody['evr'],jbody['arch']))
  build_log = build_log.readlines()

  body = '#### Reimzul build results ##### \n'
  body += ' Builder   : %s \n' % jbody['builder_fqdn']
  body += ' Package   : %s \n' % jbody['pkgname']
  body += ' Timestamp   : %s \n' % jbody['timestamp']
  body += ' Status    : %s \n' % jbody['status']
  body += ' Full logs available at %s/%s/%s/%s/%s \n\n' % (base_url,jbody['target'],jbody['pkgname'],jbody['timestamp'],jbody['evr'])
  body += '#### Mock output logs ####\n'
  body += '    ========== Mock root log ============ \n'
  for line in root_log[-30:]:
    body += line

  body += '\n'  
  body += '    ========== Mock build log ========== \n\n'  
  for line in build_log[-80:]:
    body += line  

  msg = MIMEMultipart()
  msg['From'] = email_from
  msg['To'] = email_to
  msg['Subject'] = '[reimzul] Build task %s %s (arch: %s) target %s : %s' % (jbody['timestamp'],jbody['srpm'],jbody['arch'],jbody['target'],jbody['status'])

  msg.attach(MIMEText(body, 'plain'))
  smtp_srv = smtplib.SMTP('localhost',25)
  text = msg.as_string()
  smtp_srv.sendmail(email_from,email_to.split(','), text)
  smtp_srv.quit()

def log2mongo(jbody):
  mongo_client = pymongo.MongoClient()
  db = mongo_client.reimzul
  doc_id = db.notify_history.insert_one(jbody)
  mongo_client.close()


def main():

  bs = beanstalkc.Connection()
  bs.watch('notify')

  while True:
    job = bs.reserve()
    jbody = json.loads(job.body)
    log2file(jbody)
    log2mongo(jbody)
    if jbody['status'] == 'Success' or jbody['status'] == 'Failed':
      sendmail(jbody)
    job.delete()


if __name__ == '__main__':
  main()

