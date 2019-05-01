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
'use strict';

import cbor = require('cbor');

import * as admin from "firebase-admin";
import * as functions from 'firebase-functions';
const iot = require('@google-cloud/iot');
const client = new iot.v1.DeviceManagerClient();

// start cloud function
exports.configUpdate = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs/{deviceId}')
  .onWrite(async (change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      const request = generateRequest(context.params.deviceId, change.after.data(), false);
      return client.modifyCloudToDeviceConfig(request);
    } else {
      throw(Error("no context from trigger"));
    }
  });

exports.configUpdateBinary = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs-binary/{deviceId}')
  .onWrite(async (change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      const request = generateRequest(context.params.deviceId, change.after.data(), true);
      return client.modifyCloudToDeviceConfig(request);
    } else {
      throw(Error("no context from trigger"));
    }
  });

function generateRequest(deviceId:string, configData:any, isBinary:Boolean) {
  const formattedName = client.devicePath(process.env.GCLOUD_PROJECT, functions.config().iot.core.region, functions.config().iot.core.registry, deviceId);
  let dataValue;
  if (isBinary) {
    const encoded = cbor.encode(configData);
    dataValue = encoded.toString("base64");
  } else {
    dataValue = Buffer.from(JSON.stringify(configData)).toString("base64");
  }
  return {
    name: formattedName,
    binaryData: dataValue
  };
}
