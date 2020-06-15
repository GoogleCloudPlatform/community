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

import argparse
import binascii
from construct import BitStruct, BitsInteger, Flag


sensit_v3_config = BitStruct(
    "MESSAGE_PERIOD" / BitsInteger(2),
    "MAGNET_MODE_FLAG" / Flag,
    "VIBRATION_MODE_FLAG" / Flag,
    "DOOR_MODE_FLAG" / Flag,
    "LIGHT_MODE_FLAG" / Flag,
    "TEMP_MODE_FLAG" / Flag,
    "STANDBY_MODE_FLAG" / Flag,
    "B1_SPARE" / BitsInteger(2),
    "TEMPERATURE_LOW_THRESHOLD" / BitsInteger(6),
    "B2_SPARE" / BitsInteger(2),
    "TEMPERATURE_HIGH_THRESHOLD" / BitsInteger(6),
    "HUMIDITY_LOW_THRESHOLD" / BitsInteger(4),
    "HUMIDITY_HIGH_THRESHOLD" / BitsInteger(4),
    "LIMITATION_FLAG" / Flag,
    "BRIGHTNESS_THRESHOLD" / BitsInteger(7),
    "VIBRATION_ACCELERATION_THRESHOLD" / BitsInteger(8),
    "B6_SPARE" / BitsInteger(2),
    "VIBRATION_BLANK_TIME" / BitsInteger(2),
    "VIBRATION_DEBOUNCE_COUNT" / BitsInteger(4),
    "RESET_BIT" / BitsInteger(1),
    "DOOR_OPEN_THRESHOLD" / BitsInteger(4),
    "DOOR_CLOSE_THRESHOLD" / BitsInteger(3)
)


def parse_command_line_args():
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(description=(
      'Data and config payload parser for Sigfox Sens\'it Discovery V3.'))
  parser.add_argument(
      '--parser-mode',
      choices=('encode-config', 'decode-data'),
      default='decode_data',
      required=True,
      help='Parser mode: encode-config|decode-data.')
  parser.add_argument(
      '--hex-string',
      type=str,
      default='',
      help='Sens\'it V3 payload HEX string.')
  parser.add_argument(
      '--in-file',
      help='Sens\'it V3 config input file.')
  parser.add_argument(
      '--out-file',
      required=False,
      help='Sens\'it V3 config output file, generated from '
           'parsed payload config data.')
  return parser.parse_args()


def decode_data(data):
  b0 = data[0:2]
  b1 = data[2:4]
  b2 = data[4:6]
  b3 = data[6:8]

  b0b = bin(bytearray.fromhex(b0)[0])[2:].zfill(8)
  b1b = bin(bytearray.fromhex(b1)[0])[2:].zfill(8)
  b2b = bin(bytearray.fromhex(b2)[0])[2:].zfill(8)
  b3b = bin(bytearray.fromhex(b3)[0])[2:].zfill(8)

  print('Data HEX:\t{}\n'.format(data))
  print('Bit:\t\t76543210\n\t\t--------')
  print('Byte0:\t{}\t{}\nByte1:\t{}\t{}\nByte2:\t{}\t{}\nByte3:\t{}\t{}'
        '\n'.format(b0, b0b, b1, b1b, b2, b2b, b3, b3b))

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
    exit(1)

  s = sensit_v3.parse(bytearray.fromhex(data))
  print(s)

  d = {}

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

  print('\n{}'.format(d))
  return


def decode_config(data):
  b0 = data[0:2]
  b1 = data[2:4]
  b2 = data[4:6]
  b3 = data[6:8]
  b4 = data[8:10]
  b5 = data[10:12]
  b6 = data[12:14]
  b7 = data[14:16]

  b0b = bin(bytearray.fromhex(b0)[0])[2:].zfill(8)
  b1b = bin(bytearray.fromhex(b1)[0])[2:].zfill(8)
  b2b = bin(bytearray.fromhex(b2)[0])[2:].zfill(8)
  b3b = bin(bytearray.fromhex(b3)[0])[2:].zfill(8)
  b4b = bin(bytearray.fromhex(b4)[0])[2:].zfill(8)
  b5b = bin(bytearray.fromhex(b5)[0])[2:].zfill(8)
  b6b = bin(bytearray.fromhex(b6)[0])[2:].zfill(8)
  b7b = bin(bytearray.fromhex(b7)[0])[2:].zfill(8)

  print('\nConfig HEX:\t{}\n'.format(data))
  print('Bit:\t\t76543210\n\t\t--------')
  print('Byte0:\t{}\t{}\nByte1:\t{}\t{}\nByte2:\t{}\t{}\nByte3:\t{}\t{}'
        '\n'.format(b0, b0b, b1, b1b, b2, b2b, b3, b3b))
  print('Byte5:\t{}\t{}\nByte5:\t{}\t{}\nByte6:\t{}\t{}\nByte7:\t{}\t{}'
        '\n'.format(b4, b4b, b5, b5b, b6, b6b, b7, b7b))

  c = sensit_v3_config.parse(bytearray.fromhex(data))
  for key in c.keys():
    if key is not '_io':
      print('{} = {}'.format(key, c[key]))
  return c


def encode_config(in_file):
  print('Reading config from input file: {}'.format(in_file))
  try:
    f = open(in_file, 'r')
  except IOError:
    print('Error reading file')
    exit(1)
  c = {}
  for row in f:
    key, foo, value = row.split()
    if value == 'True':
      c[key] = True
    elif value == 'False':
      c[key] = False
    else:
      c[key] = int(value)
  data = sensit_v3_config.build(c)
  print('Config HEX: {}'.format(binascii.hexlify(data).decode()))
  return


def write_config_file(out_file, c):
  f = open(out_file, 'w')
  for key in c.keys():
    if key is not '_io':
      f.write('{} = {}\n'.format(key, c[key]))
  f.close()
  print('\nConfig file written to: {}'.format(out_file))
  return


args = parse_command_line_args()
if args.parser_mode == 'decode-data':
  if not args.hex_string:
    print('Error. Argument --hex-string missing.')
    exit(1)
  data_len = len(args.hex_string)
  if not (data_len == 8 or data_len == 16 or data_len == 24):
    print('Invalid Sensit V3 payload HEX string length. Must be 8, 16 or '
          '24 characters.')
    exit(1)
  elif data_len == 8:
    decode_data(args.hex_string)
  elif data_len == 16:
    c = decode_config(args.hex_string)
    if args.out_file:
      write_config_file(args.out_file, c)
  elif data_len == 24:
    decode_data(args.hex_string[:8])
    c = decode_config(args.hex_string[8:])
    if args.out_file:
      write_config_file(args.out_file, c)
  else:
    exit(1)
elif args.parser_mode == 'encode-config':
  if not args.in_file:
    print('Error. Argument --in-file missing.')
    exit(1)
  encode_config(args.in_file)
exit(0)
