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

import * as functions from 'firebase-functions';
const Logging = require('@google-cloud/logging');

import { runInDebugContext } from 'vm';

const logging = new Logging({
  projectId: process.env.GCLOUD_PROJECT,
});

export const deviceLog = functions.pubsub.topic('device-logs').onPublish((message) => {
  const log = logging.log('device-logs');
  const metadata = {
    resource: {
      type: 'cloudiot_device',
      labels: {
        project_id: message.attributes.projectId,
        device_num_id: message.attributes.deviceNumId,
        device_registry_id: message.attributes.deviceRegistryId,
        location: message.attributes.location,
      }
    },
    labels: {
      // note device_id is not part of the monitored resource, but we can include it as another log label
      device_id: message.attributes.deviceId,
    }
  };
  const logData = message.json;
  const validSeverity = ['DEBUG','INFO', 'NOTICE', 'WARNING', 'ERROR', 'ALERT', 'CRITICAL', 'EMERGENCY']
  if (logData.severity && validSeverity.indexOf(logData.severity.toUpperCase()) > -1 ) {
    metadata['severity'] = logData.severity.toUpperCase();
    delete(logData.severity);
  }
  const entry = log.entry(metadata, logData);
  return log.write(entry);
});