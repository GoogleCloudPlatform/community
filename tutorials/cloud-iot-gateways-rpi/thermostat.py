# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import sys
import socket
from colors import bcolors
from pprint import pprint
import random
import time
import Adafruit_DHT
import RPi.GPIO as GPIO

DHT_SENSOR_PIN = 4

ADDR = ''
PORT = 10000
# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (ADDR, PORT)

device_id = sys.argv[1]
if not device_id:
  sys.exit('The device id must be specified.')

print('Bringing up device {}'.format(device_id))

# return message received
def SendCommand(sock, message, log=True):
  if log:
    print >>sys.stderr, 'sending: "%s"' % message
  sock.sendto(message, server_address)

  # Receive response
  if log:
    print >>sys.stderr, 'waiting for response'
  response, _ = sock.recvfrom(4096)
  if log:
    print >>sys.stderr, 'received: "%s"' % response

  return response


print 'Bring up device 1'


def MakeMessage(device_id, action, data=''):
  if data:
    return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(device_id, action, data)
  else:
    return '{{ "device" : "{}", "action":"{}" }}'.format(device_id, action)


def RunAction(action):
  message = MakeMessage(device_id, action)
  if not message:
    return
  print('Send data: {} '.format(message))
  event_response = SendCommand(client_sock, message)
  print "Response " + event_response


try:
  random.seed()
  RunAction('detach')
  RunAction('attach')

  while True:
    h, t = Adafruit_DHT.read_retry(22, DHT_SENSOR_PIN)
    t = t * 9.0/5 + 32

    h = "{:.3f}".format(h)
    t = "{:.3f}".format(t)
    sys.stdout.write('\r >>' + bcolors.CGREEN+ bcolors.BOLD +
                       'Temp: {}, Hum: {}'.format(t,h)  + bcolors.ENDC + ' <<')
    sys.stdout.flush()

    message = MakeMessage(device_id, 'event',
                'temperature={}, humidity={}'.format(t, h))

    SendCommand(client_sock, message, False)
    time.sleep(2)


finally:
    print >>sys.stderr, 'closing socket'
    client_sock.close()
