#!/usr/bin/env python
import paho.mqtt.client as mqtt
import os
import ConfigParser
import json
import time
import subprocess
import tempfile
import shutil
import json
import beanstalkc

# Config file used for variables
config_file = '/etc/reimzul/reimzul.ini'

config = ConfigParser.SafeConfigParser()
config.read(config_file)
mqtt_host = config.get('mqtt', 'host')
mqtt_port = config.get('mqtt', 'port')
mqtt_tls_cert = config.get('mqtt', 'tls_cert')
mqtt_tls_key = config.get('mqtt', 'tls_key')
mqtt_tls_insecure = config.get('mqtt', 'tls_insecure')
mqtt_cacert = config.get('mqtt', 'ca_cert')
mqtt_master_topic = config.get('mqtt', 'topic')
mqtt_topic = mqtt_master_topic+'/submit/#'
git_url = config.get('scm', 'git_url')

# Build queue dictionnary : arched asked and mapped to queue
build_queues = {'x86_64': 'x86_64', 'armhfp': 'armv7l', 'aarch64': 'aarch64', 'i386': 'i386', 'i686': 'i386', 'ppc64': 'ppc64', 'ppc64le': 'ppc64le', 'ppc': 'ppc'}

def on_connect(client, userdata, flags, rc):
  print("Connected to broker ", mqtt_host ,rc)
  client.subscribe(mqtt_topic)

def on_message(client, userdata, message):
  jbody = json.loads(str(message.payload.decode("utf-8")))
  topic = str(message.topic.decode("utf-8"))
  arch = topic.split('/')[-1]
  build_srpm(jbody,topic,arch)

def on_subscribe(client, userdata, topic, qos):
  print "subscribed to "+topic

def build_srpm(jbody,topic,arch):
  print jbody
  print "submitting job to %s.%s" % (jbody['target'], arch)
  jbody['arch'] = arch
  tmp_dir = tempfile.mkdtemp()
  os.chdir(tmp_dir)
  srpm_build_cmd = "/srv/reimzul/code/git-to-srpm.sh -p %s -b %s -c %s -s %s -d '%s'" % (jbody['pkg'],jbody['git_branch'],jbody['git_ref'],git_url,jbody['disttag'])
  srpm_build = subprocess.call( srpm_build_cmd, shell = True)
  if srpm_build == 0:
    print 'srpm built ok'
    srpm_path = subprocess.check_output(['find', './', '-iname', '*src.rpm']).strip('\n')
    srpm = srpm_path.split('/')[-1]
    shutil.copy(srpm_path, '/srv/reimzul/incoming/')
    os.chdir(jbody['pkg'])
    if len(jbody['disttag']) == 0:
      check_disttag_cmd = "%s/git/centos-git-common/return_disttag.sh" % (os.getenv('HOME'))
      jbody['disttag'] = subprocess.check_output(check_disttag_cmd).strip('\n')
    jbody['srpm'] = srpm
    jbody['target'] = jbody['target']+'.'+arch
    shutil.rmtree(tmp_dir)
    submit_build(jbody)
  else:
    print 'error building srpm for %s' % (jbody['pkg'])
    shutil.rmtree(tmp_dir)

def submit_build(job):
  bs = beanstalkc.Connection()
  build_queue = build_queues[job['arch']]
  bs.use(build_queue)
  bs.put(json.dumps(job), priority=8192)

  
def main():
  mqtt_client_id = '%s-%s' % (os.uname()[1],str(time.time()).split('.')[0])
  client = mqtt.Client(client_id=mqtt_client_id, clean_session=False)
  client.tls_set(ca_certs=mqtt_cacert,certfile=mqtt_tls_cert,keyfile=mqtt_tls_key,tls_version=2)
  client.tls_insecure_set(mqtt_tls_insecure)
  client.connect(mqtt_host,mqtt_port)
  client.subscribe(mqtt_topic)
  client.on_connect = on_connect
  client.on_message = on_message

  client.loop_forever()

  while True:
    time.sleep(1)

if __name__ == '__main__':
    main()

