/**
 * Copyright 2019 Google LLC
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
const {BigQuery} = require('@google-cloud/bigquery');
const bigquery = new BigQuery();

/**
 * Cloud Function entry point, Cloud Pub/Sub trigger.
 * Extracts the metrics data from payload and insert to BigQuery
 * @param {Object} event The event payload.
 * @param {object} context The event metadata.
 */
exports.enviro = (event, context) => {
  const pubsubMessage = event.data;
  const deviceId = event.attributes.deviceId;
  const objStr = Buffer.from(pubsubMessage, 'base64').toString();
  const msgObj = JSON.parse(objStr);
  const timestamp = BigQuery.timestamp(new Date());
  let rows = [{
    device_id: deviceId,
    time: timestamp,
    pressure: msgObj.pressure,
    ambient_light: msgObj.ambient_light,
    temperature: msgObj.temperature,
    humidity: msgObj.humidity
  }];
  insertRowsAsStream(rows);
};

function insertRowsAsStream (rows) {
  bigquery
    .dataset(process.env.DATASET)
    .table(process.env.TABLE)
    .insert(rows);
}
