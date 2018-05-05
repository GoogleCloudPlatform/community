"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
const mqtt = require("mqtt");
const token_1 = require("./token");
require("rxjs/add/observable/fromEvent");
// import {BehaviorSubject} from 'rxjs/BehaviorSubject';
const ReplaySubject_1 = require("rxjs/ReplaySubject");
class IoTClient {
    // private _connected = new BehaviorSubject(new mqtt.IConnackPacket());
    // public readonly connected$: Observable<mqtt.IConnackPacket> = this._connected.asObservable();
    constructor(projectId, region, registryId, deviceId, privateKeyFile, algorithm = token_1.SignAlgorithm.ES256, port = 8883, tokenRefreshMinutes = 60) {
        this.projectId = projectId;
        this.region = region;
        this.registryId = registryId;
        this.deviceId = deviceId;
        this.privateKeyFile = privateKeyFile;
        this.algorithm = algorithm;
        this.port = port;
        this.tokenRefreshMinutes = tokenRefreshMinutes;
        this.tokenSource = new token_1.TokenGenerator(this.projectId, this.privateKeyFile, this.algorithm);
        // this.connections$ = Observable.create();
        this.connections$ = new ReplaySubject_1.ReplaySubject(1);
        this.disconnections$ = new ReplaySubject_1.ReplaySubject(1);
        this.messages$ = new ReplaySubject_1.ReplaySubject(1);
        this.publishConfirmations$ = new ReplaySubject_1.ReplaySubject(1);
        // use expiration period set in constructor
        this.refresh();
    }
    refresh() {
        this.jwt = this.tokenSource.create();
        if (this.client) {
            this.client.end();
        }
        this.connect();
        setTimeout(this.refresh.bind(this), (this.tokenRefreshMinutes * 60 * 1000) - 60000);
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
        this.client.on('message', (topic, message, packet) => {
            this.messages$.next(message);
        });
        this.client.on('connect', (connack) => {
            this.client.subscribe(`/devices/${this.deviceId}/config`, function (err, granted) {
                if (err) {
                    console.error("subscription failed");
                }
            });
            this.connections$.next(connack);
        });
        this.client.on('error', (error) => console.error(error));
    }
    publish(topic, payload) {
        this.client.publish(topic, payload, (ack) => this.publishConfirmations$.next(ack));
    }
}
exports.IoTClient = IoTClient;
