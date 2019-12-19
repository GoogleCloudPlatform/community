# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from coral.enviro.board import EnviroBoard
from core import CloudIot
from luma.core.render import canvas
from PIL import ImageDraw
from time import sleep

import argparse
import itertools
import os

DEFAULT_CONFIG_LOCATION = os.path.join(os.path.dirname(__file__), 'cloud_config.ini')


def update_display(display, msg):
    with canvas(display) as draw:
        draw.text((0, 0), msg, fill='white')


def _none_to_nan(val):
    return float('nan') if val is None else val

def create_callback(enviro):
    callbacks = {}
    def on_message(unused_client, unused_userdata, message):
        payload = str(message.payload)
        print('received command msg: {}'.format(payload))
        update_display(enviro.display, payload)
    callbacks['on_message'] = on_message
    return callbacks

def main():
    # Pull arguments from command line.
    parser = argparse.ArgumentParser(description='Enviro Kit Demo')
    parser.add_argument('--display_duration',
                        help='Measurement display duration (seconds)', type=int,
                        default=5)
    parser.add_argument('--upload_delay', help='Cloud upload delay (seconds)',
                        type=int, default=300)
    parser.add_argument(
        '--cloud_config', help='Cloud IoT config file', default=DEFAULT_CONFIG_LOCATION)
    args = parser.parse_args()

    # Create instances of EnviroKit and Cloud IoT.
    enviro = EnviroBoard()
    with CloudIot(args.cloud_config) as cloud:
        # Indefinitely update display and upload to cloud.
        sensors = {}
        read_period = int(args.upload_delay / (2 * args.display_duration))
        cloud.register_message_callbacks(create_callback(enviro))
        for read_count in itertools.count():
            # First display temperature and RH.
            sensors['temperature'] = enviro.temperature
            sensors['humidity'] = enviro.humidity
            msg = 'Temp: %.2f C\n' % _none_to_nan(sensors['temperature'])
            msg += 'RH: %.2f %%' % _none_to_nan(sensors['humidity'])
            update_display(enviro.display, msg)
            sleep(args.display_duration)
            # After 5 seconds, switch to light and pressure.
            sensors['ambient_light'] = enviro.ambient_light
            sensors['pressure'] = enviro.pressure
            msg = 'Light: %.2f lux\n' % _none_to_nan(sensors['ambient_light'])
            msg += 'Pressure: %.2f kPa' % _none_to_nan(sensors['pressure'])
            update_display(enviro.display, msg)
            sleep(args.display_duration)
            # If time has elapsed, attempt cloud upload.
            if read_count % read_period == 0 and cloud.enabled():
                cloud.publish_message(sensors)


if __name__ == '__main__':
    main()
