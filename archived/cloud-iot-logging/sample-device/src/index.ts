/* eslint-disable no-process-exit */
/*
# Copyright Google Inc. 2018

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/

import {IoTClient} from './client';
import {SignAlgorithm} from './token';
import {first} from 'rxjs/operators';
import {Observable} from 'rxjs';

if (!process.env.GCLOUD_PROJECT) {
  console.error('Error: GCLOUD_PROJECT env variable unset');
  process.exit(1);
}
const client = new IoTClient(
  // projectId:
  process.env.GCLOUD_PROJECT as string,
  // region:
  process.env.CLOUD_REGION as string,
  // registryId:
  // '<set to your registry id>',
  process.env.REGISTRY_ID as string,
  // deviceId:
  'log-tester',
  // privateKeyFile:
  './ec_private.pem',
  // algorithm:
  SignAlgorithm.ES256,
  // private port: number = 8883,
  443,
  // private tokenRefreshMinutes
  20
);

// uncomment if you want to see that publish messages are getting through
// client.publishConfirmations$.subscribe(ack => console.log("message published"));

client.messages$.subscribe(msg => {
  const msgContent = Buffer.from(msg, 'base64').toString();
  let config;
  try {
    config = JSON.parse(msgContent);
  } catch (e) {
    console.error('latest config not valid json');
    return;
  }
  if (config.bounce) {
    if (config.bounce > 10) {
      client.publish(
        '/devices/log-tester/events/log',
        JSON.stringify({severity: 'CRITICAL', msg: 'Spring Failure'})
      );
    } else if (config.bounce > 5) {
      client.publish(
        '/devices/log-tester/events/log',
        JSON.stringify({severity: 'WARNING', msg: 'Spring damage detected'})
      );
    } else {
      client.publish(
        '/devices/log-tester/events/log',
        JSON.stringify({
          severity: 'INFO',
          msg: 'Spring back :' + 1.7 * (config.bounce as number),
        })
      );
    }
  }
});

let clientConnected = false;

const initialConnect = client.connections$.pipe(first());

// tslint:disable-next-line: no-any
initialConnect.subscribe((connected: any) => {
  if (!clientConnected) {
    console.log('Device Started');
    clientConnected = true;
    client.publish(
      '/devices/log-tester/events/log',
      JSON.stringify({severity: 'DEBUG', msg: 'Device Started'})
    );
  }
});
