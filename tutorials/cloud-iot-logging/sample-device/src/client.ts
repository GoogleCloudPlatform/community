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

import mqtt = require('mqtt');
import {TokenGenerator, SignAlgorithm} from './token';
import {setInterval} from 'timers';
import {Observable} from 'rxjs';
import {ReplaySubject} from 'rxjs';

export class IoTClient {
  private jwt: string | undefined;
  private tokenSource: TokenGenerator;
  private client: mqtt.MqttClient;

  connections$: ReplaySubject<mqtt.IConnackPacket>;
  /* eslint-disable  @typescript-eslint/no-explicit-any */
  disconnections$: ReplaySubject<any>;
  messages$: ReplaySubject<any>;
  publishConfirmations$: ReplaySubject<any>;

  constructor(
    private projectId: string,
    private region: string,
    private registryId: string,
    private deviceId: string,
    private privateKeyFile: string,
    private algorithm: SignAlgorithm = SignAlgorithm.ES256,
    private port = 8883,
    private tokenRefreshMinutes = 60
  ) {
    this.tokenSource = new TokenGenerator(
      this.projectId,
      this.privateKeyFile,
      this.algorithm
    );
    // this.connections$ = Observable.create();
    this.connections$ = new ReplaySubject(1);
    this.disconnections$ = new ReplaySubject(1);
    this.messages$ = new ReplaySubject(1);
    this.publishConfirmations$ = new ReplaySubject(1);
    // use expiration period set in constructor
    this.refresh();
  }
  refresh() {
    this.jwt = this.tokenSource.create();
    if (this.client) {
      this.client.end();
    }
    this.connect();
    setTimeout(
      this.refresh.bind(this),
      this.tokenRefreshMinutes * 60 * 1000 - 60000
    );
  }
  connect() {
    const connectionArgs = {
      host: 'mqtt.googleapis.com',
      port: this.port,
      clientId: `projects/${this.projectId}/locations/${this.region}/registries/${this.registryId}/devices/${this.deviceId}`,
      username: 'unused',
      password: this.jwt,
      protocol: 'mqtts',
      secureProtocol: 'TLSv1_2_method',
    };
    this.client = mqtt.connect(connectionArgs);

    // tslint:disable-next-line: no-any
    this.client.on(
      'message',
      (topic: string, message: any, packet: mqtt.IPacket) => {
        this.messages$.next(message);
      }
    );

    this.client.on('connect', (connack: mqtt.IConnackPacket) => {
      this.client.subscribe(
        `/devices/${this.deviceId}/config`,
        (err, granted) => {
          if (err) {
            console.error('subscription failed');
          }
        }
      );
      this.connections$.next(connack);
    });

    this.client.on('error', error => console.error(error));
  }

  publish(topic: string, payload: string | Buffer) {
    this.client.publish(topic, payload, ack =>
      this.publishConfirmations$.next(ack)
    );
  }
}
