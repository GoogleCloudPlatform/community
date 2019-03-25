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

import { IoTClient } from './client';
import { SignAlgorithm } from './token';
import { first } from 'rxjs/operators';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/timer';
import 'rxjs/add/observable/merge';
import cbor = require('cbor');

if (!process.env.GCLOUD_PROJECT) {
    console.error("Error: GCLOUD_PROJECT env variable unset");
    process.exit(1);
}

let useBinary = false;
let deviceId = 'sample-device';
if (process.argv.length > 2 && process.argv[2] == '-b') {
    useBinary = true;
    deviceId = 'sample-binary';
    console.log("Device uses binary config");
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
    deviceId,
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
    let config;
    if (useBinary) {
        config = cbor.decodeFirstSync(msg);

    } else {
        const msgContent = Buffer.from(msg, 'base64').toString();
        try {
            config = JSON.parse(msgContent);
        }
        catch (e) {
            console.error("latest config not valid json");
            return;
        }
    }
    console.log("Current Config: ");
    console.log(config);

});

let clientConnected = false;

const initialConnect = client.connections$.pipe(first());

// tslint:disable-next-line: no-any
initialConnect.subscribe((connected: any) => {
    if (!clientConnected) {
        console.log("Device Started");
        clientConnected = true;
    }
});