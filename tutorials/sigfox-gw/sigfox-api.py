# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import sys
import time
import json
import base64
import requests
import argparse
import configparser
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


def parse_command_line_args():
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(description=(
      'Utility to manage Device Type Callbacks using Sigfox APIv2.'))
  parser.add_argument(
      '--config_file',
      default='sigfox-api.ini',
      required=False,
      help='Config file.')
  parser.add_argument(
      '--callbacks',
      choices=('list', 'delete-all', 'create'),
      required=True,
      help='Callbacks action: list|delete-all|create.')
  return parser.parse_args()


def list_callbacks(host, auth, id):
  try:
    url = "{}/device-types/{}/callbacks".format(host, id)
    payload = ""
    headers = {
        'Accept': "application/json",
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': auth,
        'cache-control': "no-cache"
    }
    response = requests.request("GET", url, data=payload, headers=headers)
  except requests.exceptions.RequestException as e:
    print("Exception when calling DeviceTypesApi->list_callbacks: %s\n" % e)
    exit(1)
  callbacks_unicode = json.loads(response.text)
  callbacks = []
  for c in callbacks_unicode['data']:
    c2 = {}
    for k in c.keys():
      c2[k.encode('utf-8')] = c[k]
    callbacks.append(c2)
  return callbacks


def delete_callbacks(api_instance, configuration, id, name):
  callbacks_list = list_callbacks(configuration.host,
                                  configuration.get_basic_auth_token(), id)
  if len(callbacks_list) == 0:
    print('No Callbacks configured for: {}. Nothing to do.'.format(name))
    exit(0)
  cids = []
  for c in callbacks_list:
    cids.append(c[b'id'])
  print('Deleting callbacks: {}'.format(cids))
  for cid in cids:
    try:
      api_instance.delete_callback(id, cid)
    except ApiException as e:
      print("Exception when calling DeviceTypesApi->delete_callback: %s\n" % e)
      exit(1)
  print('Deleted {} Callbacks for Device Type: {}'.format(len(cids), name))
  return


def read_config_file(config_file):
  config = configparser.ConfigParser()
  config.read(config_file)
  configuration = swagger_client.Configuration()
  if config.has_option('default', 'host'):
    configuration.host = config.get('default', 'host')
  else:
    print('Error: config parameter: host missing.')
    exit(1)
  if config.has_option('default', 'id'):
    id = config.get('default', 'id')
  else:
    print('Error: config parameter: id missing.')
    exit(1)
  if config.has_option('default', 'api_username'):
    configuration.username = config.get('default', 'api_username')
  else:
    print('Error: config parameter: api_username missing.')
    exit(1)
  if config.has_option('default', 'api_password'):
    configuration.password = config.get('default', 'api_password')
  else:
    print('Error: config parameter: api_password missing.')
    exit(1)
  if config.has_option('default', 'callbacks'):
    callbacks_config_file = config.get('default', 'callbacks')
  else:
    print('Error: config parameter: callbacks missing.')
    exit(1)
  if config.has_option('default', 'cf_data'):
    cf_data = config.get('default', 'cf_data')
  else:
    print('Error: config parameter: cf_data missing.')
    exit(1)
  if config.has_option('default', 'cf_service'):
    cf_service = config.get('default', 'cf_service')
  else:
    print('Error: config parameter: cf_service missing.')
    exit(1)
  if config.has_option('default', 'cf_username'):
    cf_username = config.get('default', 'cf_username')
  else:
    print('Error: config parameter: cf_username missing.')
    exit(1)
  if config.has_option('default', 'cf_password'):
    cf_password = config.get('default', 'cf_password')
  else:
    print('Error: config parameter: cf_password missing.')
    exit(1)
  return (id, configuration, callbacks_config_file, cf_data, cf_service,
          cf_username, cf_password)


def get_device_type_name(api_instance, id):
  try:
    api_response = api_instance.get_device_type(id)
  except ApiException as e:
    print("Exception when calling DeviceTypesApi->get_device_type: %s\n" % e)
  return api_response.name


def read_callbacks_config_file(callbacks_config_file):
  with open(callbacks_config_file) as f:
    callbacks = json.load(f)
  return callbacks


def create_callbacks(api_instance, configuration, id, name, cf_data,
                     cf_service, cf_auth, callbacks_config_file):
  callbacks_dicts = read_callbacks_config_file(callbacks_config_file)
  callbacks = []

  for d in callbacks_dicts:
    callbacks.append(dict_to_callback(d, cf_data, cf_service, name, cf_auth))
  print('Creating {} callbacks.'.format(len(callbacks)))

  for c in callbacks:
    try:
      api_instance.create_callback(c, id)
    except ApiException as e:
      print("Exception when calling DeviceTypesApi->create_callback: %s\n" % e)
      exit(1)
  print('Created {} Callbacks for Device Type: {}'.format(len(callbacks),
                                                          name))
  callbacks_list = list_callbacks(configuration.host,
                                  configuration.get_basic_auth_token(), id)
  for d in callbacks_list:
    if b'callbackSubtype' in d.keys():
      if d[b'callbackSubtype'] == 3:
        print('Enabling Downlink for BIDIR Callback')
        try:
          api_instance.enable_downlink_callback(id, d[b'id'])
        except ApiException as e:
          print("Exception when calling DeviceTypesApi->"
                "enable_downlink_callback: %s\n" % e)
          exit(1)
        print('Downlink enabled.')
  return


def dict_to_callback(d, cf_data, cf_service, name, cf_auth):
  """Returns swagger_client->callback object"""
  if d['type'] == 'data':
    url = cf_data
  elif d['type'] == 'service':
    url = cf_service
  else:
    print('Invalid value for: type in Callbacks configuration file.')
    exit(1)

  headers = {'Authorization': 'Basic ' + cf_auth.decode('utf-8')}

  d['bodyTemplate'] = d['bodyTemplate'].replace('{deviceTypeName}', name)

  subtype_value=d['callbackSubtype'] if 'callbackSubtype' in d.keys() else 7

  callback = swagger_client.CreateUrlCallback(
      channel=d['channel'],
      callback_type=d['callbackType'],
      callback_subtype=subtype_value,
      enabled=d['enabled'],
      send_duplicate=d['sendDuplicate'],
      url=url,
      http_method=d['httpMethod'],
      headers=headers,
      send_sni=d['sendSni'],
      body_template=d['bodyTemplate'],
      content_type=d['contentType']
  )
  return callback


def main(argv):
  args = parse_command_line_args()
  (id, configuration, callbacks_config_file, cf_data, cf_service, cf_username,
   cf_password) = read_config_file(args.config_file)
  api_instance = swagger_client.DeviceTypesApi(
      swagger_client.ApiClient(configuration))
  name = get_device_type_name(api_instance, id)

  cf_auth = base64.b64encode((cf_username + ':' + cf_password).encode("utf-8"))

  if args.callbacks == 'list':
    callbacks_list = list_callbacks(configuration.host,
                                    configuration.get_basic_auth_token(), id)

    for c in callbacks_list:
      print('Callback: {}:'.format(c[b'id']))
      pprint(c)
      print('')
    print('{} Callbacks configured'
          ' for Device Type: {}'.format(len(callbacks_list), name))
  elif args.callbacks == 'create':
    create_callbacks(api_instance, configuration, id, name, cf_data,
                     cf_service, cf_auth, callbacks_config_file)
  elif args.callbacks == 'delete-all':
    delete_callbacks(api_instance, configuration, id, name)
  else:
    exit(1)


if __name__ == '__main__':
  main(sys.argv)
