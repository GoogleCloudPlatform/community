
import time
import ssl
import datetime
import jwt
import json
import sys
from os import environ as env, path
from locust import Locust, TaskSet, events, task
import paho.mqtt.client as mqtt
import socket
import csv
import string
import random

"""
The device behavior in this code is to publish a sequence-numbered payload and wait for
a response before publishing the next payload. If a response is not received in N seconds,
then an error is recorded in Locust and the next payload is sent. 

To enforce this protocol, the following variables are used:
lastSent - sequence number of last message sent, 0 = none sent yet
lastRcvd - sequence number of last message received, 0 = none received
numSkips - how many times skipped sending a message because we have not received a response
skipLimit - how many skips we allow before firing a Locust error and moving on

The publish frequency is controlled by min_wait and max_wait in the Locust subclass.
For example, if the min_wait and max_wait are 1000, each device will publish once per second,
and if skipLimit is 120 then the code will timeout waiting for a response after 120 seconds.
"""

skipLimit = 120
deviceList = None

class LtkDevice(TaskSet):

    def get_loggedId(self):
        return self.deviceId

    def get_clientId(self):
        # convert <paho.mqtt.client.Client object at 0x10d51af10> to 0x10d51af10
        return '{}'.format(self.mqtt_client).split(' ')[3].replace('>','')

    def fix_pem_format(self):
        # csv has key as a flat string, add newlines to put key in proper pem format for jwt.encode
        self.privateKey = (
            '-----BEGIN RSA PRIVATE KEY-----\n' +
            self.privateKey
                .replace('-----BEGIN RSA PRIVATE KEY----- ','')
                .replace('-----END RSA PRIVATE KEY-----','')
                .replace(' ','\n') +
            '-----END RSA PRIVATE KEY-----\n')

    def get_jwt(self):
        token = {
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440),
            'aud': env['PROJECT_ID']
        }
        return jwt.encode(token, self.privateKey, 'RS256')

    def setup_mqtt_client(self):
        self.mqtt_client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                   .format(
                           env['PROJECT_ID'],
                           env['REGION'],
                           env['REGISTRY_ID'],
                           self.deviceId)))
                    
        self.mqtt_client.username_pw_set(
            username='unused',
            password=self.get_jwt())

        certs = path.join(path.dirname(__file__), "./iot_rootCAs.pem")
        self.mqtt_client.tls_set(ca_certs=certs, tls_version=ssl.PROTOCOL_TLSv1_2)

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        # self.mqtt_client.on_publish = self.on_publish
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_client.on_message = self.on_message
        # self.mqtt_client.on_log = self.on_log

        self.connectStartTime = time.time()
        # Use the long-term support domain, mqtt.googleapis.com should be considered deprecated.
        # Use of mqtt.googleapis.com requires a different trust bundle, located at https://pki.goog/roots.pem.
        self.mqtt_client.connect('mqtt.2030.ltsapis.goog', '443')
        self.mqtt_client.loop_start()
        sys.stdout.write('*** clientId {} set up for deviceId {}'.format(self.get_clientId(), self.deviceId))

    def on_connect(self, client, userdata, flags, rc):
        sys.stdout.write('*** ON_CONNECT {} CONNACK received with code {}'.format(self.get_loggedId(), rc))
        if rc == 0:
            # Fire locust event for initial connect only
            if self.connectStartTime:
                # want connectLatency to be in milliseeconds
                connectLatency = int((time.time() - self.connectStartTime) * 1000)
                events.request_success.fire(request_type='MQTT connect', name='', response_time=connectLatency, response_length=0)
                self.connectStartTime = None
                self.subscribeStartTime = time.time()
            self.connected = True
            self.mqtt_client.subscribe('/devices/{}/commands/#'.format(self.deviceId))
        else:
            msg = 'deviceId {} CONNACK error code {}'.format(self.deviceId, rc)
            events.request_failure.fire(request_type='MQTT connect', name='', response_time=0, exception=msg)

    def on_disconnect(self, client, userdata, rc):
        sys.stdout.write('*** ON_DISCONNECT {} disconnect with code {}'.format(self.get_loggedId(), rc))
        self.connected = False
        self.ready = False

    def on_publish(self, client, userdata, mid):
        sys.stdout.write('*** ON_PUBLISH {} published mid {}'.format(self.get_loggedId(), mid))
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        sys.stdout.write('*** ON_SUBSCRIBE {} subscribed mid {} qos {}'.format(self.get_loggedId(), mid, granted_qos[0]))
        # Paho returns qos 128 if subscribe fails, granted_qos is a tuple with value in first element
        if granted_qos[0] == 128:
            msg = 'SUBSCRIBE rejected by broker'
            events.request_failure.fire(request_type='MQTT subscribe', name='', response_time=0, exception=msg)        
        else:
            # Fire locust event for initial subscribe only
            if self.subscribeStartTime:
                # want subscribeLatency in milliseconds
                subscribeLatency = int((time.time() - self.subscribeStartTime) * 1000)
                events.request_success.fire(request_type='MQTT subscribe', name='', response_time=subscribeLatency, response_length=0)
                self.subscribeStartTime = None
            self.ready = True

    def on_message(self, client, userdata, message):
        # calculate the latency for this message
        recvTime = time.time()
        # sys.stdout.write('*** recvTime {:.5f}'.format(recvTime))
        tokens = message.payload.split(' ')
        clientId = tokens[1]
        # paranoia should never happen
        if clientId != self.get_clientId():
            msg = '{} received message for {}'.format(self.get_clientId(), clientId)
            events.request_failure.fire(request_type='wrong client', name='', response_time=0, exception=msg)        
        else:
            seqNum = int(tokens[3])
            sendTime = int(tokens[5])
            now = int(recvTime * 100000)
            # now and sendTime are ints, in tens of microseconds, so divide by 100 to convert to millisec 
            echoLatency = int((now - sendTime) / 100)
            # verbose message but needed to get latencies
            sys.stdout.write('*** ON_MESSAGE {} latency {} msec'.format(message.payload, echoLatency))
            # success if this is the message we are expecting, failure otherwise
            if seqNum == self.lastSent:
                self.lastRcvd = seqNum 
                events.request_success.fire(request_type='echo receive', name='', response_time=echoLatency, response_length=0)
                self.numSkips = 0
            else:
                # treat as spurious, must have received after echo timeout
                events.request_failure.fire(request_type='echo late', name='', response_time=echoLatency, exception=message.payload)        

    def on_log(self, client, userdata, level, buf):
        sys.stdout.write('*** ON_LOG {} {} '.format(self.get_loggedId(), buf))

    # Called by Locust when the client is started.
    def on_start(self):
        global deviceList
        self.connected = False
        self.ready = False
        if len(deviceList) > 0:
            # Locust does not spawn threads for clients, so this is safe.
            self.deviceId, self.privateKey = deviceList.pop()
            # Note setup_mqtt_client calls loop_start, so this creates a thread per client.
            self.fix_pem_format()
            self.setup_mqtt_client()
            self.lastSent = 0
            self.lastRcvd = 0
            self.numSkips = 0
        else:
            sys.stdout.write('*** exhausted devices in csv')

    # Called by Locust when the client is stopped.
    def on_stop(self):
        # Wait for any straggling message. This might read data being written to by 
        # on_message in another thread (loop thread), which is OK.
        numWaits = 0
        while self.lastSent > self.lastRcvd and numWaits < 10:
            sys.stdout.write('*** {} waiting for last message'.format(self.get_loggedId()))
            numWaits += 1
            time.sleep(1)
        if numWaits == 10:
            msg = '{} {} payload {}'.format(self.deviceId, self.get_clientId(), self.lastSent)
            events.request_failure.fire(request_type='last message timeout', name='', response_time=0, exception=msg)        
        sys.stdout.write('*** {} published {} messages'.format(self.get_loggedId(), self.lastSent))
        self.mqtt_client.disconnect()
        # wait for disconnect to finish before returning
        numWaits = 0
        while self.connected and numWaits < 10:
            numWaits += 1
            time.sleep(1)

    @task(1)
    def ltkPublish(self):
        global skipLimit
        if self.ready:
            # publish to default telemetry topic
            if self.lastSent == self.lastRcvd:
                # we're up to date on messages received, so send the next seqNum
                topic = '/devices/{}/events'.format(self.deviceId)
                seqNum = self.lastSent + 1
                # optional - add pad to force larger payload
                # pad = ''.join(random.choice(string.letters + string.digits) for _ in range(0))
                sendTime = time.time()
                # sys.stdout.write('*** sendTime {:.5f} '.format(sendTime))
                payload = '{} {} payload {} at {}'.format(self.deviceId, self.get_clientId(), seqNum, int(sendTime * 100000))
                # optional - if using padding, add to end of payload as follows (note: payload format and contents affects code in on_message)
                # payload = '{} {} payload {} at {} {}'.format(self.deviceId, self.get_clientId(), seqNum, int(sendTime * 100000), pad)
                self.mqtt_client.publish(topic, payload)
                self.lastSent = seqNum
                # verbose message but needed for tracing cases of "echo timeout" events
                sys.stdout.write('*** TASK published {}'.format(payload))
            elif self.numSkips == skipLimit:
                # waited too long for response to last message sent, so fire error and move on
                msg = '{} {} payload {}'.format(self.deviceId, self.get_clientId(), self.lastSent)
                events.request_failure.fire(request_type='echo timeout', name='', response_time=0, exception=msg)        
                self.numSkips = 0
                self.lastRcvd = self.lastSent
                # publish will be on next task tick
            else:
                # still waiting for response
                self.numSkips += 1


# min_wait and max_wait are in milliseconds
# Min and max time between repetitions of tasks for a client
# When both are 1000, will run task every second
class LtkWorker(Locust):
    task_set = LtkDevice
    min_wait = 1000
    max_wait = 1000

    def __init__(self):
        super(LtkWorker, self).__init__()
        global deviceList
        # events.request_success += self.hook_request_success
        if (deviceList == None):
            try:
                with open('devicelist.csv', 'rb') as f:
                    reader = csv.reader(f)
                    deviceList = list(reader)
                # get this pod's devices
                self.shardDeviceList()
                sys.stdout.write('*** have {} devices from devicelist.csv'.format(len(deviceList)))
            except IOError:
                sys.stdout.write('*** no devicelist.csv')
                sys.exit(1)

    # def setup(self):
    #     sys.stdout.write('*** in device setup (called once for all devices)')

    # def teardown(self):
    #     sys.stdout.write('*** in device teardown (called once for all devices)')

    # This was logging N repeated messages per single request, where N is number of clients
    # def hook_request_success(self, request_type, name, response_time, response_length, **kw):
    #    sys.stdout.write('*** request_success {} {} {} {}'.format(request_type, name, response_time, response_length))

    def shardDeviceList(self):
        global deviceList

        # kubernetes StatefulSet assigns ordinal to pod
        # ordinal is accessible from host name
        # we use the ordinal to index into this pod's block of devices
        # (i is block number in device list)
        hostname = socket.gethostname()
        sys.stdout.write('*** hostname is ' + hostname)

        # block index
        try:
            i = int(hostname.split('-')[-1])
        except ValueError:
            i = 0
        sys.stdout.write('*** block index is {}'.format(i))

        # block size
        try:
            b = int(env['BLOCK_SIZE'])
        except (KeyError, ValueError):
            b = len(deviceList)
        sys.stdout.write('*** block size is {}'.format(b))

        # delete devices above my block, if any
        # b*(i+1) is index of first row above my block
        if b*(i+1) <= len(deviceList)-1:
            del deviceList[b*(i+1):len(deviceList)]

        # delete devices below my block, if any
        # b*i-1 is index of first row below my block
        if b*i-1 > 0:
            del deviceList[0:b*i]

        # validate block
        sys.stdout.write('*** sharded device list, first device {}'.format(deviceList[0][0]))
        sys.stdout.write('*** sharded device list, last device  {}'.format(deviceList[-1][0]))
