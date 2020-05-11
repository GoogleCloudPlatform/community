# Copyright 2020 Google LLC
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


def pubsub_bigquery(event, context):
  # [START functions_pubsub_bigquery]
  """Triggered from a message on a Cloud Pub/Sub topic.
  Args:
       event (dict): Event payload.
       context (google.cloud.functions.Context): Metadata for the event.
  """
  import os
  import base64
  import json
  from rfc3339 import rfc3339
  from construct import BitStruct, BitsInteger, Flag
  from google.cloud import bigquery

  project_id = os.environ.get('GCP_PROJECT')
  bigquery_dataset = os.environ.get('BIGQUERY_DATASET')
  bigquery_table = os.environ.get('BIGQUERY_TABLE')
  device_type = os.environ.get('DEVICE_TYPE')
  if (not project_id or not bigquery_dataset or not
      bigquery_table or not device_type):
    print('Error reading Function environment variables')
    return

  client = bigquery.Client(project=project_id)
  table_ref = client.dataset(bigquery_dataset).table(bigquery_table)
  table = client.get_table(table_ref)

  pubsub_data = base64.b64decode(event['data']).decode('utf-8')
  print('Data JSON: {}'.format(pubsub_data))

  d = json.loads(pubsub_data)

  # Only process the payload if the device type is correct
  if 'deviceType' in d:
    if d['deviceType'] == device_type:
      try:
        time_int = int(d['time'])
      except ValueError:
        time_int = float(d['time'])
        time_int = int(time_int)
      d['time'] = rfc3339(time_int)

      data = d['data']
      b1 = data[2:4]
      b1b = bin(bytes.fromhex(b1)[0])[2:].zfill(8)

      mode = int(b1b[:5], 2)
      if mode == 0:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "spare" / BitsInteger(2),
            "firmware_version_major_increment" / BitsInteger(4),
            "firmware_version_minor_increment_msb" / BitsInteger(4),
            "firmware_version_minor_increment_lsb" / BitsInteger(2),
            "firmware_version_patch_increment" / BitsInteger(6)
        )
      elif mode == 1:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "temperature_msb" / BitsInteger(2),
            "temperature_lsb" / BitsInteger(8),
            "humidity" / BitsInteger(8)
        )
      elif mode == 2:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "spare" / BitsInteger(2),
            "brightness_msb" / BitsInteger(8),
            "brightness_lsb" / BitsInteger(8)
        )
      elif mode == 3:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "door_status" / BitsInteger(2),
            "event_count_msb" / BitsInteger(8),
            "event_count_lsb" / BitsInteger(8)
        )
      elif mode == 4:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "vibration_status" / BitsInteger(2),
            "event_count_msb" / BitsInteger(8),
            "event_count_lsb" / BitsInteger(8)
        )
      elif mode == 5:
        sensit_v3 = BitStruct(
            "battery_level" / BitsInteger(5),
            "reserved" / BitsInteger(3),
            "mode" / BitsInteger(5),
            "button_alert_flag" / Flag,
            "magnet_status" / BitsInteger(2),
            "event_count_msb" / BitsInteger(8),
            "event_count_lsb" / BitsInteger(8)
        )
      else:
        print("Unsupported Sens'it V3 device mode: {}".format(mode))
        return

      s = sensit_v3.parse(bytes.fromhex(data))

      if 'battery_level' in s.keys():
        d['battery_level'] = s['battery_level'] * 0.05 + 2.7
      if 'mode' in s.keys():
        d['mode'] = s['mode']
      if 'button_alert_flag' in s.keys():
        d['button_alert_flag'] = s['button_alert_flag']
      if 'temperature_msb' in s.keys():
        msb = bin(s['temperature_msb'])[2:].zfill(8)
        lsb = bin(s['temperature_lsb'])[2:].zfill(8)
        d['temperature'] = (int(msb + lsb, 2) - 200) / 8.0
      if 'humidity' in s.keys():
        d['humidity'] = s['humidity'] / 2.0
      if 'brightness_msb' in s.keys():
        msb = bin(s['brightness_msb'])[2:].zfill(8)
        lsb = bin(s['brightness_lsb'])[2:].zfill(8)
        d['brightness'] = int(msb + lsb, 2) / 2.0
      if 'door_status' in s.keys():
        d['door_status'] = s['door_status']
      if 'event_count_msb' in s.keys():
        msb = bin(s['event_count_msb'])[2:].zfill(8)
        lsb = bin(s['event_count_lsb'])[2:].zfill(8)
        d['event_count'] = int(msb + lsb, 2)
      if 'vibration_status' in s.keys():
        d['vibration_status'] = s['vibration_status']
      if 'magnet_status' in s.keys():
        d['magnet_status'] = s['magnet_status']
      if 'firmware_version_major_increment' in s.keys():
        msb = bin(s['firmware_version_minor_increment_msb'])[2:].zfill(8)
        lsb = bin(s['firmware_version_minor_increment_lsb'])[2:].zfill(8)
        fw_minor = int(msb + lsb, 2)
        fw = str(s['firmware_version_major_increment']) + '.' \
            + str(fw_minor) + '.' + str(s['firmware_version_patch_increment'])
        d['firmware'] = fw

      print('Data Dict: {}'.format(d))

      rows_to_insert = [(
          d.get('device'),
          d.get('time'),
          d.get('data'),
          d.get('seqNumber'),
          d.get('battery_level'),
          d.get('mode'),
          d.get('button_alert_flag'),
          d.get('temperature'),
          d.get('humidity'),
          d.get('brightness'),
          d.get('door_status'),
          d.get('vibration_status'),
          d.get('magnet_status'),
          d.get('event_count'),
          d.get('firmware'),
          d.get('lqi'),
          d.get('fixedLat'),
          d.get('fixedLng'),
          d.get('operatorName'),
          d.get('countryCode'),
          d.get('computedLocation')
      )]
      print('BQ Row: {}'.format(rows_to_insert))
      errors = client.insert_rows(table, rows_to_insert)
      try:
        assert errors == []
      except AssertionError:
        print("BigQuery insert_rows error: {}".format(errors))
  return
  # [END functions_pubsub_bigquery]
