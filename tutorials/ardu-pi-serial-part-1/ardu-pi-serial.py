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
import json
import os
import sys
import platform
import random
import ssl
from time import sleep

import jwt
import paho.mqtt.client as mqtt
from rfc3339 import rfc3339


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
    help='Path to private key file.')
  parser.add_argument(
    '--algorithm',
    choices=('RS256', 'ES256'),
    default='RS256',
    help='Which encryption algorithm to use to generate the JWT.')
  parser.add_argument(
    '--cloud_region', default='us-central1', help='GCP cloud region')
  parser.add_argument(
    '--ca_certs',
    default='roots.pem',
    help=('CA root from https://pki.google.com/roots.pem'))
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
    default=8883,
    type=int,
    help='MQTT bridge port.')
  parser.add_argument(
    '--jwt_expires_minutes',
    default=60,
    type=int,
    help=('Expiration time, in minutes, for JWT tokens.'))
  parser.add_argument(
    '--device_type',
    choices=('sim', 'pi'),
    default='sim',
    required=True,
    help='Type of device: sim|pi.')
  parser.add_argument(
    '--serial_port',
    default='/dev/ttyACM0',
    help='Serial port device connected to the Arduino.')
  return parser.parse_args()


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
    'iat': datetime.datetime.utcnow(),
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
    'aud': project_id
  }

  with open(private_key_file, 'r') as f:
    private_key = f.read()

  print('Creating JWT using {} from private key file {}'.format(
    algorithm, private_key_file))

  return jwt.encode(token, private_key, algorithm=algorithm)


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
  client.username_pw_set(
    username='unused',
    password=create_jwt(
            project_id, private_key_file, algorithm))
  client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
  client.on_connect = on_connect
  client.on_publish = on_publish
  client.on_disconnect = on_disconnect
  client.on_message = on_message
  client.connect(mqtt_bridge_hostname, mqtt_bridge_port)
  mqtt_config_topic = '/devices/{}/config'.format(device_id)
  client.subscribe(mqtt_config_topic, qos=1)
  client.loop_start()
  return client


def error_str(rc):
  """Convert a Paho error to a human readable string."""
  return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
  """Callback for when a device connects."""
  print('gcp_on_connect', error_str(rc))


def on_disconnect(unused_client, unused_userdata, rc):
  """Paho callback for when a device disconnects."""
  print('gcp_on_disconnect', error_str(rc))


def on_publish(unused_client, unused_userdata, unused_mid):
  """Paho callback when a message is sent to the broker."""
  print('gcp_on_publish')


def on_message(unused_client, unused_userdata, message):
  """Callback when the device receives a message on a subscription."""
  payload = str(message.payload)
  print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
          payload, message.topic, str(message.qos)))


def publish(client, mqtt_topic, device, temp, pres, humi, solar, wind):
  """Function to publish sensor data to Cloud IoT Core."""
  payload = {}
  payload['clientid'] = platform.uname()[1]
  payload['windgen'] = float('{:.2f}'.format(wind))
  payload['solargen'] = float('{:.2f}'.format(solar))
  payload['humidity'] = float('{:.2f}'.format(humi))
  payload['temperature'] = float('{:.2f}'.format(temp))
  payload['pressure'] = float('{:.2f}'.format(pres))
  payload['timestamp'] = rfc3339(datetime.datetime.now())
  json_payload = json.dumps(payload)
  print('Publishing message: {}'.format(json_payload))
  client.publish(mqtt_topic, json_payload, qos=0)
  return


def read_sensors(device, sense_hat, ser, temp, pres, humi, solar, wind):
  """Read Pi Sense HAT sensors or simulate the readings."""
  try:
    if device == 'pi':
      temp = sense_hat.get_temperature()
      humi = sense_hat.get_humidity()
      pres = sense_hat.get_pressure()
      solar, wind = read_arduino_sensors(ser)
    else:
      temp = simulate_sensors(temp, 3, -40, 50)
      pres = simulate_sensors(pres, 6, 850, 1150)
      humi = simulate_sensors(humi, 3, 0, 100)
      solar = simulate_sensors(solar, 0.1, 0, 3.6)
      wind = simulate_sensors(wind, 0.1, 0, 3.6)
  except IOError:
    print('I/O Error')
  return temp, pres, humi, solar, wind


def read_arduino_sensors(ser):
  """Request and receive sensor readings from Arduino over serial."""
  s = {}
  response = serial_send_and_receive(ser, '0')
  response = response.rstrip()
  print('Received from Arduino: {}'.format(response))
  if response[0] == 'S':
    pairs = response.split(' ')
    for pair in pairs:
      if pair == 'S':
        continue
      else:
        name, value = pair.split(':')
        s[name] = value
  else:
    print('Error getting Arduino sensor values over serial')
    return 0
  solar = int(s['s']) * (5.0 / 1024.0)
  wind = int(s['w']) * (5.0 / 1024.0)
  return solar, wind


def serial_send_and_receive(ser, theinput):
  """Write string to serial connection and return any response."""
  ser.write(theinput)
  while True:
    try:
      sleep(0.01)
      state = ser.readline()
      if state:
        return state
    except:
      pass
  sleep(0.1)
  return 'E'


def simulate_sensors(prev, stdev, min, max):
  """Gaussian distribution for simulated sensor readings."""
  delta = random.gauss(0, stdev)
  new = prev + delta
  if new < min or new > max:
    new = prev - delta
  return new


def init_sense_hat_and_serial(serial_port):
  from sense_hat import SenseHat
  import serial
  print('Creating and flushing serial port. Rebooting Arduino..')
  ser = serial.Serial(serial_port)
  with ser:
    ser.setDTR(False)
    sleep(1)
    ser.flushInput()
    ser.setDTR(True)
  ser = serial.Serial(serial_port, 115200, timeout=0.1)
  print('Sleeping 3s..')
  sense_hat = SenseHat()
  sense_hat.get_humidity()
  sleep(3)
  return sense_hat, ser


def main(argv):
  args = parse_command_line_args()

  sub_topic = 'events' if args.message_type == 'event' else 'state'
  mqtt_topic = '/devices/{}/{}'.format(args.device_id, sub_topic)

  device = args.device_type
  if device == 'pi':
    sense_hat, ser = init_sense_hat_and_serial(args.serial_port)
  else:
    sense_hat = None
    ser = None

  # Default starting values for simulated sensor readings
  temp = 24
  pres = 1013
  humi = 50.0
  solar = -1.0
  wind = -1.0

  jwt_iat = datetime.datetime.utcnow()
  jwt_exp_mins = args.jwt_expires_minutes

  client = get_client(
    args.project_id, args.cloud_region, args.registry_id, args.device_id,
    args.private_key_file, args.algorithm, args.ca_certs,
    args.mqtt_bridge_hostname, args.mqtt_bridge_port)

  while True:
    seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
    if seconds_since_issue > 60 * (jwt_exp_mins - 2):
      print('Refreshing token after {}s').format(seconds_since_issue)
      client.loop_stop()
      jwt_iat = datetime.datetime.utcnow()
      client = get_client(
        args.project_id, args.cloud_region,
        args.registry_id, args.device_id, args.private_key_file,
        args.algorithm, args.ca_certs, args.mqtt_bridge_hostname,
        args.mqtt_bridge_port)
    temp, pres, humi, solar, wind = read_sensors(device, sense_hat, ser, temp,
                                                 pres, humi, solar, wind)
    publish(client, mqtt_topic, device, temp, pres, humi, solar, wind)
    sleep(1)


if __name__ == '__main__':
  main(sys.argv)
