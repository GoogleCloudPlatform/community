/**
 * Copyright 2018, Google, Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const Compute = require('@google-cloud/compute');
const Buffer = require('safe-buffer').Buffer;

const compute = new Compute();

/**
 * Deletes unused Compute Engine instances.
 *
 * Expects a Pub/Sub message with JSON-formatted event data containing the
 * following attributes:
 *  zone (OPTIONAL) - the Google Cloud zone the instances are located in.
 *  label - the label of instances to start.
 *
 * @param {!object} event Cloud Function Pub/Sub message event.
 * @param {object} context The event metadata.
 * @param {!object} callback Cloud Function Pub/Sub callback indicating
 *  completion.
 */
exports.cleanUnusedInstances = (event, context, callback) => {
  try {
    const payload = _validatePayload(
      JSON.parse(Buffer.from(event.data, 'base64').toString())
    );
    console.log('Checking instances matching payload: ' + payload);
    const options = { filter: `labels.${payload.label}` };

    compute.getVMs(options).then((vms) => {
      vms[0].forEach((instance) => {
        // Extracts Compute Engine instance metadata
        const ttl = instance.metadata.labels.ttl; // TTL in minutes
        const zone = instance.zone.id;

        // Current Datetime
        const date = new Date();
        const now = Math.round(date.getTime() / 1000); // epoch in seconds

        // Calculates Compute Engine instance creation time
        const creationDate = new Date(instance.metadata.creationTimestamp);
        const creationTime = Math.round(creationDate.getTime() / 1000);

        const diff = (now - creationTime) / 60; // in minutes.
        if (diff > ttl) {
          compute
            .zone(zone)
            .vm(instance.name)
            .delete()
            .then((data) => {
              // Operation pending.
              const operation = data[0];
              return operation.promise();
            })
            .then(() => {
              // Operation complete. Instance successfully started.
              const message = 'Successfully deleted instance ' +
                  instance.name;
              console.log(message);
              callback(null, message);
            })
            .catch((err) => {
              console.log(err);
              callback(err);
            });
        }
      });
    });
  } catch (err) {
    console.log(err);
    callback(err);
  }
};

/**
 * Validates that a request payload contains the expected fields.
 *
 * @param {!object} payload the request payload to validate.
 * @return {!object} the payload object.
 */
function _validatePayload (payload) {
  if (!payload.label) {
    throw new Error('Attribute \'label\' missing from payload');
  }
  return payload;
}
