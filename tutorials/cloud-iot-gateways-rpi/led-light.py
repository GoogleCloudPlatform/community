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

from __future__ import print_function

import socket
import sys

import RPi.GPIO as GPIO
from colors import bcolors


LED_IOPIN = 14
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
    print('sending "{}"'.format(message))
    sock.sendto(message.encode(), server_address)

    # Receive response
    print('waiting for response')
    response = sock.recv(4096)
    print('received: "{}"'.format(response))

    return response


def MakeMessage(device_id, action, data=''):
    if data:
        return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(
            device_id, action, data)
    else:
        return '{{ "device" : "{}", "action":"{}" }}'.format(
            device_id, action)


def RunAction(action, data=''):
    global client_sock
    message = MakeMessage(device_id, action, data)
    if not message:
        return
    print('Send data: {} '.format(message))
    event_response = SendCommand(client_sock, message)
    print('Response: {}'.format(event_response))


try:
    RunAction('detach')
    RunAction('attach')
    RunAction('event', 'LED is online')
    RunAction('subscribe')

    while True:
        response = client_sock.recv(4096).decode('utf8')
        print('Client received {}'.format(response))
        if response.upper() == 'ON' or response.upper() == b'ON':
            GPIO.output(LED_IOPIN, GPIO.HIGH)
            sys.stdout.write('\r>> ' + bcolors.OKGREEN + bcolors.CBLINK +
                             " LED is ON " + bcolors.ENDC + ' <<')
            sys.stdout.flush()
        elif response.upper() == "OFF" or response.upper() == b'OFF':
            GPIO.output(LED_IOPIN, GPIO.LOW)
            sys.stdout.write('\r >>' + bcolors.CRED + bcolors.BOLD +
                             ' LED is OFF ' + bcolors.ENDC + ' <<')
            sys.stdout.flush()
        else:
            print('Invalid message {}'.format(response))

finally:
    print('closing socket', file=sys.stderr)
    client_sock.close()
