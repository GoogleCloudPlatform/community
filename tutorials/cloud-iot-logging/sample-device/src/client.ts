/**
 * Copyright 2018 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import mqtt = require('mqtt');
import { TokenGenerator, SignAlgorithm } from "./token"
import { setInterval } from 'timers';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/observable/fromEvent';
// import {BehaviorSubject} from 'rxjs/BehaviorSubject';
import {ReplaySubject} from 'rxjs/ReplaySubject';

export class IoTClient {
    private jwt: string;
    private tokenSource: TokenGenerator;
    private client: mqtt.MqttClient;

    public connections$: ReplaySubject<mqtt.IConnackPacket>;
    public disconnections$: ReplaySubject<any>;
    public messages$: ReplaySubject<any>;
    public publishConfirmations$: ReplaySubject<any>;

    // private _connected = new BehaviorSubject(new mqtt.IConnackPacket());
    // public readonly connected$: Observable<mqtt.IConnackPacket> = this._connected.asObservable();

    constructor (
        private projectId: string,
        private region: string,
        private registryId: string,
        private deviceId: string,
        private privateKeyFile: string,
        private algorithm: SignAlgorithm = SignAlgorithm.ES256,
        private port: number = 8883,
        private tokenRefreshMinutes: number = 60,
        ) { 
            this.tokenSource = new TokenGenerator(this.projectId, this.privateKeyFile, this.algorithm);
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
        setTimeout(this.refresh.bind(this), (this.tokenRefreshMinutes * 60 * 1000) - 60000)
    }
    connect() {

        let connectionArgs = {
            host: 'mqtt.googleapis.com',
            port: this.port,
            clientId: `projects/${this.projectId}/locations/${this.region}/registries/${this.registryId}/devices/${this.deviceId}`,
            username: 'unused',
            password: this.jwt,
            protocol: 'mqtts',
            secureProtocol: 'TLSv1_2_method'
          };
        this.client = mqtt.connect(connectionArgs);

        this.client.on('message', (topic:string, message:any, packet:mqtt.IPacket) =>{
            this.messages$.next(message);
        });

        this.client.on('connect', (connack:mqtt.IConnackPacket) => {
            this.client.subscribe(`/devices/${this.deviceId}/config`, function(err, granted) {
                if (err) {
                    console.error("subscription failed");
                }
            })
            this.connections$.next(connack)


        });
            
        this.client.on('error', (error) =>
            console.error(error))
        
    }
    
    publish(topic: string, payload: string | Buffer) {
        this.client.publish(topic, payload, (ack) => this.publishConfirmations$.next(ack));
    }
}