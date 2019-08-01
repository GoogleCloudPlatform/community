/*
# Copyright Google Inc. 2019
#
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
const fs = require('fs');
const jwt = require('jsonwebtoken');
const mqtt = require("async-mqtt");
const config = require("./client_config.json");

function createJwt(projectId, privateKeyFile, algorithm) {
  const token = {
    iat: parseInt(Date.now() / 1000),
    exp: parseInt(Date.now() / 1000) + 60 * 60,
    aud: projectId,
  };
  const privateKey = fs.readFileSync(privateKeyFile);
  return jwt.sign(token, privateKey, {algorithm: algorithm});
}

function initializeIoTCoreClient() {
  const connectionArgs = {
    host: config.cloud.mqttBridgeHostname,
    port: config.cloud.mqttBridgePort,
    clientId: mqttClientId,
    username: 'unused',
    password: createJwt(config.cloud.projectId, config.cloud.privateKeyFile, config.cloud.algorithm),
    protocol: 'mqtts',
    secureProtocol: 'TLSv1_2_method',
  };
  const mqttClient = mqtt.connect(connectionArgs);
  return new Promise((resolve, reject) => {
    mqttClient.on("connect",() => {
      console.log("Connected to Cloud IoT Core!");
      resolve(mqttClient);
    });
    mqttClient.on("error", err => {reject(err);});
  });
}

const mqttClientId = `projects/${config.cloud.projectId}/locations/${config.cloud.region}/registries/${config.cloud.registryId}/devices/${config.cloud.deviceId}`;
const eventTopic = `/devices/${config.cloud.deviceId}/events`;

module.exports.initializeIoTCoreClient = initializeIoTCoreClient;
module.exports.eventTopic = eventTopic;