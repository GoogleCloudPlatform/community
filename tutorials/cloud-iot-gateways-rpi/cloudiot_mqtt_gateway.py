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

import argparse
import datetime
import os
import random
import ssl
import time
import json
import jwt
import socket
from time import ctime
import paho.mqtt.client as mqtt
from colors import bcolors
import threading


HOST = ''
PORT = 10000
BUFSIZE = 2048
ADDR = (HOST, PORT)

udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSerSock.setblocking(0)
udpSerSock.bind(ADDR)


class GatewayState:
  # This is the topic that the device will receive configuration updates on.
  mqtt_config_topic = ''

  # Host the gateway will connect to
  mqtt_bridge_hostname = ''
  mqtt_bridge_port = 8883

  # for all PUBLISH messages which are waiting for PUBACK. The key is 'mid'
  # returned by publish().
  pending_responses = {}

  # for all SUBSCRIBE messages which are waiting for SUBACK. The key is 'mid'.
  pending_subscribes = {}

  # for all SUBSCRIPTIONS. The key is subscription topic.
  subscriptions = {}

  # Indicates if MQTT client is connected or not
  connected = False


gateway_state = GatewayState()


def create_jwt(project_id, private_key_file, algorithm):
  """Creates a JWT (https://jwt.io) to establish an MQTT connection.
      Args:
       project_id: The cloud project ID this device belongs to
       private_key_file: A path to a file containing either an RSA256 or
               ES256 private key.
       algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
      Returns:
          An MQTT generated from the given project_id and private key, which
          expires in 20 minutes. After 20 minutes, your client will be
          disconnected, and a new JWT will have to be generated.
      Raises:
          ValueError: If the private_key_file does not contain a known key.
      """

  token = {
      # The time that the token was issued at
      'iat': datetime.datetime.utcnow(),
      # The time the token expires.
      'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
      # The audience field should always be set to the GCP project id.
      'aud': project_id
  }

  # Read the private key file.
  with open(private_key_file, 'r') as f:
      private_key = f.read()

  print('Creating JWT using {} from private key file {}'.format(
      algorithm, private_key_file))

  return jwt.encode(token, private_key, algorithm=algorithm)
# [END iot_mqtt_jwt]


# [START iot_mqtt_config]
def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', mqtt.connack_string(rc))

    gateway_state.connected = True

    # Subscribe to the config topic.
    client.subscribe(gateway_state.mqtt_config_topic, qos=1)

def on_disconnect(client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print('on_disconnect', error_str(rc))
    gateway_state.connected = False

    # re-connect
    # NOTE: should implement back-off here, but it's a tutorial
    client.connect(gateway_state.mqtt_bridge_hostname, gateway_state.mqtt_bridge_port)

def on_publish(unused_client, userdata, mid):
  """Paho callback when a message is sent to the broker."""
  print('on_publish, userdata {}, mid {}'.format(userdata, mid))

  try:
    client_addr, message = gateway_state.pending_responses.pop(mid)
    udpSerSock.sendto(message, client_addr)
    print('pending response count {}'.format(
        len(gateway_state.pending_responses)))
  except KeyError:
    print('Unable to find key {}'.format(mid))


def on_subscribe(unused_client, unused_userdata, mid, granted_qos):
  print('on_subscribe: mid {}, qos {}'.format(mid, granted_qos))
  try:
    client_addr, response = gateway_state.pending_subscribes[mid]
    udpSerSock.sendto(response, client_addr)
  except KeyError:
    print('Unable to find key {}'.format(mid))


def on_message(unused_client, unused_userdata, message):
  """Callback when the device receives a message on a subscription."""
  payload = str(message.payload)
  print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
      payload, message.topic, str(message.qos)))
  try:
    client_addr = gateway_state.subscriptions[message.topic]
    udpSerSock.sendto(payload, client_addr)
  except KeyError:
    print('Nobody subscribes to topic {}'.format(message.topic))


def get_client(
        project_id, cloud_region, registry_id, device_id, private_key_file,
        algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port):
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    client = mqtt.Client(
        client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                   .format(
                       project_id,
                       cloud_region,
                       registry_id,
                       device_id)))

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
        username='unused',
        password=create_jwt(
            project_id, private_key_file, algorithm))

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    # Connect to the Google MQTT bridge.
    client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

    return client
# [END iot_mqtt_config]


def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=(
        'Example Google Cloud IoT Core MQTT device connection code.'))
    parser.add_argument(
        '--project_id',
        default=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        help='GCP cloud project name')
    parser.add_argument(
        '--registry_id', required=True, help='Cloud IoT Core registry id')
    parser.add_argument(
        '--device_id', required=True, help='Cloud IoT Core device id')
    parser.add_argument(
        '--private_key_file',
        required=True, help='Path to private key file.')
    parser.add_argument(
        '--algorithm',
        choices=('RS256', 'ES256'),
        required=True,
        help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
        '--cloud_region', default='us-central1', help='GCP cloud region')
    parser.add_argument(
        '--ca_certs',
        default='roots.pem',
        help=('CA root from https://pki.google.com/roots.pem'))
    parser.add_argument(
        '--num_messages',
        type=int,
        default=100,
        help='Number of messages to publish.')
    parser.add_argument(
        '--message_type',
        choices=('event', 'state'),
        default='event',
        help=('Indicates whether the message to be published is a '
              'telemetry event or a device state message.'))
    parser.add_argument(
        '--mqtt_bridge_hostname',
        default='mqtt.googleapis.com',
        help='MQTT bridge hostname.')
    parser.add_argument(
        '--mqtt_bridge_port',
        choices=(8883, 8884, 443),
        default=8883,
        type=int,
        help='MQTT bridge port.')
    parser.add_argument(
        '--jwt_expires_minutes',
        default=1200,
        type=int,
        help=('Expiration time, in minutes, for JWT tokens.'))

    return parser.parse_args()


def attach_device(client, device):
  attach_topic = '/devices/{}/attach'.format(device)
  print(attach_topic)
  client.publish(attach_topic,  "", qos=1)


# [START iot_mqtt_run]
def main():
  global gateway_state

  args = parse_command_line_args()

  gateway_state.mqtt_config_topic = '/devices/{}/config'.format(parse_command_line_args().device_id)
  gateway_state.mqtt_bridge_hostname = args.mqtt_bridge_hostname
  gateway_state.mqtt_bridge_port = args.mqtt_bridge_hostname

  # Publish to the events or state topic based on the flag.
  sub_topic = 'events' if args.message_type == 'event' else 'state'

  jwt_iat = datetime.datetime.utcnow()
  jwt_exp_mins = args.jwt_expires_minutes
  client = get_client(
      args.project_id, args.cloud_region, args.registry_id, args.device_id,
      args.private_key_file, args.algorithm, args.ca_certs,
      args.mqtt_bridge_hostname, args.mqtt_bridge_port)

  # Publish num_messages mesages to the MQTT bridge once per second.
  while True:
    client.loop()
    if gateway_state.connected == False:
      print('connect status {}'.format(gateway_state.connected))
      time.sleep(1)
      continue

    # print "...waiting for message..."
    try:
      data, client_addr = udpSerSock.recvfrom(BUFSIZE)
    except socket.error:
      continue
    print "[%s]: From Address %s:%s receive data: %s" % (
        ctime(), client_addr[0], client_addr[1], data)

    command = json.loads(data)
    if not command:
      print('invalid json command {}'.format(data))
      continue

    action = command["action"]
    device_id = command["device"]

    if action == 'event':
      # attach_device(client, device_id)

      print('Sending telemetry event for device {}'.format(device_id))
      payload = command["data"]
      mqtt_topic = '/devices/{}/{}'.format(device_id,  'events')
      print('Publishing message to topic {} with payload \'{}\''.format(
          mqtt_topic, payload))
      rc, event_mid = client.publish(mqtt_topic, payload, qos=1)
      response = '{{ "device": {}, "command": "event", "status" : "ok"}}'.format(
          device_id)
      print('Save mid {} for response {}'.format(event_mid, response))
      gateway_state.pending_responses[event_mid] = (client_addr, response)
    elif action == 'attach':
      print('attach device {}'.format(device_id))
      attach_topic = '/devices/{}/attach'.format(device_id)
      rc, attach_mid = client.publish(attach_topic, "", qos=1)
      response = (
          '{{ "device": {}, "command": "attach", "status" : "ok" }}'.format(device_id))
      print('Save mid {} for response {}'.format(attach_mid, response))
      gateway_state.pending_responses[attach_mid] = (client_addr, response)
    elif action == 'detach':
      print('detach device {}'.format(device_id))
      detach_topic = '/devices/{}/detach'.format(device_id)
      rc, detach_mid = client.publish(detach_topic, "", qos=1)
      response = (
          '{{ "device": {}, "command": "detach", "status" : "ok" }}'.format(device_id))
      print('Save mid {} for response {}'.format(detach_mid, response))
      gateway_state.pending_responses[detach_mid] = (client_addr, response)
    elif action == "subscribe":
      print('subscribe config for {}'.format(device_id))
      subscribe_topic = '/devices/{}/config'.format(device_id)
      rc, mid = client.subscribe(subscribe_topic, qos=1)
      response = (
          '{{ "device": {}, "command": "subscribe", "status" : "ok" }}'.format(device_id))
      gateway_state.subscriptions[subscribe_topic] = (client_addr)
      print('Save mid {} for response {}'.format(mid, response))
      gateway_state.pending_subscribes[mid] = (client_addr, response)
  else: 
      print('undefined action {}'.format(action))

      print('Finished.')
# [END iot_mqtt_run]


if __name__ == '__main__':
    main()
