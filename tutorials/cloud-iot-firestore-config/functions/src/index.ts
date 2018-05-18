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
import { runInDebugContext } from 'vm';
import { DeviceManager } from './devices';

// create a device manager instance with a registry id, optionally pass a region
const dm = new DeviceManager('config-demo');

// start cloud function
exports.configUpdate = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs/{deviceId}')
  .onWrite((change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      // get the new config data
      const configData = change.after.data();
      return dm.updateConfig(context.params.deviceId, configData);
    } else {
      throw(Error("no context from trigger"));
    }

  })


  exports.configUpdateBinary = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs-binary/{deviceId}')
  .onWrite((change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      // get the new config data
      const configData = change.after.data();
      const encoded = cbor.encode(configData);

      return dm.updateConfigBinary(context.params.deviceId, encoded);
    } else {
      throw(Error("no context from trigger"));
    }

  })