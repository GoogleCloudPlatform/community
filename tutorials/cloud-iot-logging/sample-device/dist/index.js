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
const client_1 = require("./client");
const token_1 = require("./token");
// import "rxjs/add/operator/first";
const operators_1 = require("rxjs/operators");
require("rxjs/add/observable/timer");
require("rxjs/add/observable/merge");
// tsc && rsync -av ./dist pi@192.168.86.81:agent/ && ssh -t pi@192.168.86.81 'sudo node /home/pi/agent/dist/index.js'
const zone = "zone-a";
if (!process.env.GCLOUD_PROJECT) {
    console.error("Error: GCLOUD_PROJECT env variable unset");
    process.exit(1);
}
const client = new client_1.IoTClient(
// projectId: 
process.env.GCLOUD_PROJECT, 
// region: 
process.env.CLOUD_REGION, 
// registryId: 
// '<set to your registry id>',
process.env.REGISTRY_ID, 
// deviceId: 
'log-tester', 
// privateKeyFile: 
'./ec_private.pem', 
// algorithm: 
token_1.SignAlgorithm.ES256, 
// private port: number = 8883,
443, 
// private tokenRefreshMinutes
20);
// client.publishConfirmations$.subscribe(ack => console.log("message published"));
client.messages$.subscribe(msg => {
    const msgContent = Buffer.from(msg, 'base64').toString();
    let config;
    try {
        config = JSON.parse(msgContent);
    }
    catch (e) {
        console.error("invalid json config");
        return;
    }
    if (config.bounce) {
        if (config.bounce > 10) {
            client.publish('/devices/log-tester/events/log', JSON.stringify({ severity: 'CRITICAL', msg: "Spring Failure" }));
        }
        else if (config.bounce > 5) {
            client.publish('/devices/log-tester/events/log', JSON.stringify({ severity: 'WARNING', msg: "Spring damage detected" }));
        }
        else {
            client.publish('/devices/log-tester/events/log', JSON.stringify({ severity: 'INFO', msg: "Spring back :" + 1.7 * config.bounce }));
        }
    }
});
let clientConnected = false;
const initialConnect = client.connections$.pipe(operators_1.first());
initialConnect.subscribe(connected => {
    if (!clientConnected) {
        console.log("Device Started");
        clientConnected = true;
        client.publish('/devices/log-tester/events/log', JSON.stringify({ severity: 'DEBUG', msg: "Device Started" }));
    }
});
