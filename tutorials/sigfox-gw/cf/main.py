# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys


def callback_data(request):
  # [START functions_callback_data]
  """HTTP Cloud Function.
  Args:
       data (dict): The dictionary with data specific to the given event.
       context (google.cloud.functions.Context): The Cloud Functions event
       metadata.
  """
  import os
  import json
  import base64
  import datetime
  from flask import abort
  from rfc3339 import rfc3339
  from google.cloud import datastore, pubsub_v1

  if request.method == 'POST':
    http_user = os.environ.get('HTTP_USER')
    http_passwd = os.environ.get('HTTP_PASSWD')
    request_user = request.authorization["username"]
    request_passwd = request.authorization["password"]

    if request_user == http_user and request_passwd == http_passwd:
      request_dict = request.get_json()
      print('Received Sigfox message: {}'.format(request_dict))

      publisher = pubsub_v1.PublisherClient()
      topic = os.environ.get('PUBSUB_TOPIC_DATA')
      project_id = os.environ.get('GCP_PROJECT')
      if not topic or not project_id:
          print('Error reading Function environment variables')
          return abort(500)
      topic_name = 'projects/{project_id}/topics/{topic}'.format(
          project_id=project_id, topic=topic)

      try:
          time_int = int(request_dict['time'])
      except ValueError:
          time_int = float(request_dict['time'])
          time_int = int(time_int)
      event_time = rfc3339(time_int)
      request_json = json.dumps(request_dict)
      message_id = publisher.publish(topic_name, request_json.encode('utf-8'),
                                     ts=event_time.encode('utf-8'))
      print('Message published to Pub/Sub topic: {}'.format(topic_name))

      if 'ack' in request_dict:
        if (request_dict['ack'] == 'true' and request_dict['device'] and
            request_dict['deviceType']):
          device_type = request_dict['deviceType']
          ds_kind = os.environ.get('DATASTORE_KIND')
          ds_property = os.environ.get('DATASTORE_PROPERTY')

          ds_client = datastore.Client()
          ds_key = ds_client.key(ds_kind, device_type)
          e = ds_client.get(ds_key)
          if not e:
            print('Datastore entity not found for '
                  'deviceType: {}'.format(device_type))
            return '', 204
          elif ds_property not in e:
            print('Datastore property: {} not found for '
                  'deviceType: {}'.format(ds_property, device_type))
            return '', 204
          elif len(e[ds_property]) > 16:
            print('Datastore config: {} wrong length for deviceType: {}. '
                  'Should be max 16 HEX characters '
                  '(8 bytes)'.format(e[ds_property], device_type))
            return '', 204
          else:
            device = request_dict['device']
            response_dict = {}
            response_dict[device] = {'downlinkData': e[ds_property]}
            response_json = json.dumps(response_dict)
            print('Sending downlink message: {}'.format(response_json))
            return response_json, 200
        else:
          return '', 204
      else:
        return '', 204
    else:
      print('Invalid HTTP Basic Authentication: '
            '{}'.format(request.authorization))
      return abort(401)
  else:
      print('Invalid HTTP Method to invoke Cloud Function. '
            'Only POST supported')
      return abort(405)
  # [END functions_callback_data]


def callback_service(request):
  # [START functions_callback_service]
  """HTTP Cloud Function.
  Args:
       data (dict): The dictionary with data specific to the given event.
       context (google.cloud.functions.Context): The Cloud Functions event
       metadata.
  """
  import os
  import json
  import base64
  import datetime
  from flask import abort

  if request.method == 'POST':
    http_user = os.environ.get('HTTP_USER')
    http_passwd = os.environ.get('HTTP_PASSWD')
    request_user = request.authorization["username"]
    request_passwd = request.authorization["password"]

    if request_user == http_user and request_passwd == http_passwd:
      request_dict = request.get_json()
      print('Received Sigfox service message: {}'.format(request_dict))
      return '', 204
    else:
      print('Invalid HTTP Basic Authentication: '
            '{}'.format(request.authorization))
      return abort(401)
  else:
    print('Invalid HTTP Method to invoke Cloud Function. Only POST supported')
    return abort(405)
  # [END functions_callback_service]
