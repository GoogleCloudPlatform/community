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
import RPi.GPIO as GPIO
from colors import bcolors
from pprint import pprint


LED_IOPIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_IOPIN, GPIO.OUT)

ADDR = ''
PORT = 10000
# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (ADDR, PORT)

device_id = sys.argv[1]
if not device_id:
  sys.exit('The device id must be specified.')

print('Bringing up device {}'.format(device_id))

def SendCommand(sock, message):
  print >>sys.stderr, 'sending "%s"' % message
  sock.sendto(message, server_address)

  # Receive response
  print >>sys.stderr, 'waiting for response'
  response, _ = sock.recvfrom(4096)
  print >>sys.stderr, 'received: "%s"' % response

  return response

print 'Bring up device'

def MakeMessage(device_id, action, data=''):
  if data:
    return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(device_id, action, data)
  else:
    return '{{ "device" : "{}", "action":"{}" }}'.format(device_id, action)

def RunAction(action, data=''):
  message = MakeMessage(device_id, action, data)
  if not message:
    return
  print('Send data: {} '.format(message))
  event_response = SendCommand(client_sock, message)
  print "Response " + event_response

try:
  RunAction('detach')
  RunAction('attach')
  RunAction('event', 'LED is online')
  RunAction('subscribe')

  while True:
    response, server = client_sock.recvfrom(4096)
    if response.upper() == "ON":
      GPIO.output(LED_IOPIN, GPIO.HIGH)
      sys.stdout.write('\r>> ' + bcolors.OKGREEN + bcolors.CBLINK +
                       " LED is ON " + bcolors.ENDC + ' <<')
      sys.stdout.flush()
    elif response.upper() == "OFF":
      GPIO.output(LED_IOPIN, GPIO.LOW)
      sys.stdout.write('\r >>' + bcolors.CRED + bcolors.BOLD +
                       " LED is OFF " + bcolors.ENDC + ' <<')
      sys.stdout.flush()


finally:
    print >>sys.stderr, 'closing socket'
    client_sock.close()


