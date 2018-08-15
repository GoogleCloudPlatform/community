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

'use strict';

const fs = require('fs');
const jwt = require('jsonwebtoken');
const mqtt = require('mqtt');

// The initial backoff time after a disconnection occurs, in seconds.
var MINIMUM_BACKOFF_TIME = 1;

// The maximum backoff time before giving up, in seconds.
var MAXIMUM_BACKOFF_TIME = 32;

// Whether to wait with exponential backoff before publishing.
var shouldBackoff = false;

// The current backoff time.
var backoffTime = 1;

// Whether an asynchronous publish chain is in progress.
var publishChainInProgress = false;

console.log('Google Cloud IoT Core MQTT example.');
var argv = require(`yargs`)
  .options({
    projectId: {
      default: process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT,
      description: 'The Project ID to use. Defaults to the value of the GCLOUD_PROJECT or GOOGLE_CLOUD_PROJECT environment variables.',
      requiresArg: true,
      type: 'string'
    },
    cloudRegion: {
      default: 'us-central1',
      description: 'GCP cloud region.',
      requiresArg: true,
      type: 'string'
    },
    registryId: {
      description: 'Cloud IoT registry ID.',
      requiresArg: true,
      demandOption: true,
      type: 'string'
    },
    deviceId: {
      description: 'Cloud IoT device ID.',
      requiresArg: true,
      demandOption: true,
      type: 'string'
    },
    privateKeyFile: {
      description: 'Path to private key file.',
      requiresArg: true,
      demandOption: true,
      type: 'string'
    },
    algorithm: {
      description: 'Encryption algorithm to generate the JWT.',
      requiresArg: true,
      demandOption: true,
      choices: ['RS256', 'ES256'],
      type: 'string'
    },
    numMessages: {
      default: 100,
      description: 'Number of messages to publish.',
      requiresArg: true,
      type: 'number'
    },
    tokenExpMins: {
      default: 20,
      description: 'Minutes to JWT token expiration.',
      requiresArg: true,
      type: 'number'
    },
    messageType: {
      default: 'events',
      description: 'Message type to publish.',
      requiresArg: true,
      choices: ['events', 'state'],
      type: 'string'
    }
  })
  .example(`node $0 cloudiot_mqtt_example_nodejs.js --projectId=blue-jet-123 --registryId=my-registry --deviceId=my-node-device --privateKeyFile=../rsa_private.pem --algorithm=RS256`)
  .wrap(120)
  .recommendCommands()
  .epilogue(`For more information, see https://cloud.google.com/iot-core/docs`)
  .help()
  .strict()
  .argv;

// Create a Cloud IoT Core JWT for the given project id, signed with the given
// private key.
function createJwt (projectId, privateKeyFile, algorithm) {
  // Create a JWT to authenticate this device. The device will be disconnected
  // after the token expires, and will have to reconnect with a new token. The
  // audience field should always be set to the GCP project id.
  const token = {
    'iat': parseInt(Date.now() / 1000),
    'exp': parseInt(Date.now() / 1000) + 20 * 60, // 20 minutes
    'aud': projectId
  };
  const privateKey = fs.readFileSync(privateKeyFile);
  return jwt.sign(token, privateKey, { algorithm: algorithm });
}

function publishAsync (messagesSent, numMessages) {
  // If we have published enough messages or backed off too many times, stop.
  if (messagesSent > numMessages || backoffTime >= MAXIMUM_BACKOFF_TIME) {
    if (backoffTime >= MAXIMUM_BACKOFF_TIME) {
      console.log('Backoff time is too high. Giving up.');
    }
    console.log('Closing connection to MQTT. Goodbye!');
    client.end();
    publishChainInProgress = false;
    return;
  }

  // Publish and schedule the next publish.
  publishChainInProgress = true;
  var publishDelayMs = 0;
  if (shouldBackoff) {
    publishDelayMs = 1000 * (backoffTime + Math.random());
    backoffTime *= 2;
    console.log(`Backing off for ${publishDelayMs}ms before publishing.`);
  }

  setTimeout(function () {
    // The following code will assign the current device as the recipient of
    // the message relayed by the Google Cloud function and will increment the
    // "hops" counter.
    // [START demo_echo]
    const payload = {
      cloudRegion: argv.cloudRegion,
      deviceId: argv.deviceId,
      registryId: argv.registryId,
      hops: messagesSent
    };
    console.log('Publishing message:', payload);
    client.publish(mqttTopic, JSON.stringify(payload), { qos: 1 }, function (err) {
      if (!err) {
        shouldBackoff = false;
        backoffTime = MINIMUM_BACKOFF_TIME;
      }
    });
    // [END demo_echo]

    var schedulePublishDelayMs = argv.messageType === 'events' ? 1000 : 2000;
    setTimeout(function () {
      let secsFromIssue = parseInt(Date.now() / 1000) - iatTime;
      if (secsFromIssue > argv.tokenExpMins * 60) {
        iatTime = parseInt(Date.now() / 1000);
        console.log(`\tRefreshing token after ${secsFromIssue} seconds.`);

        client.end();
        connectionArgs.password = createJwt(argv.projectId, argv.privateKeyFile, argv.algorithm);
        client = mqtt.connect(connectionArgs);

        client.on('connect', (success) => {
          console.log('connect');
          if (!success) {
            console.log('Client not connected...');
          } else if (!publishChainInProgress) {
            publishAsync(1, argv.numMessages);
          }
        });

        client.on('close', () => {
          console.log('close');
          shouldBackoff = true;
        });

        client.on('error', (err) => {
          console.log('error', err);
        });

        client.on('message', (topic, message, packet) => {
          console.log('message received: ', Buffer.from(message, 'base64').toString('ascii'));
          let payload = JSON.parse(Buffer.from(message, 'base64').toString('ascii'));
          console.log(`${payload.hops} to ${++payload.hops}`);
          publishAsync(payload.hops, payload.hops + 1);
        });

        client.on('packetsend', () => {
          // Note: logging packet send is very verbose
        });
      }
      publishAsync(messagesSent + 1, numMessages);
    }, schedulePublishDelayMs);
  }, publishDelayMs);
  setTimeout(function () {
    console.log(`Waited long enough then.`);
  }, 2000);
}
const mqttClientId = `projects/${argv.projectId}/locations/${argv.cloudRegion}/registries/${argv.registryId}/devices/${argv.deviceId}`;

let connectionArgs = {
  host: `mqtt.googleapis.com`,
  port: 443, // 8883
  clientId: mqttClientId,
  username: 'unused',
  password: createJwt(argv.projectId, argv.privateKeyFile, argv.algorithm),
  protocol: 'mqtts',
  secureProtocol: 'TLSv1_2_method'
};

// Create a client, and connect to the Google MQTT bridge.
let iatTime = parseInt(Date.now() / 1000);
let client = mqtt.connect(connectionArgs);

client.subscribe(`/devices/${argv.deviceId}/config`);
const mqttTopic = `/devices/${argv.deviceId}/${argv.messageType}`;

client.on('connect', (success) => {
  console.log('connect');
  if (!success) {
    console.log('Client not connected...');
  } else if (!publishChainInProgress) {
    publishAsync(1, argv.numMessages);
  }
});

client.on('close', () => {
  console.log('close');
  shouldBackoff = true;
});

client.on('error', (err) => {
  console.log('error', err);
});

client.on('message', (topic, message, packet) => {
  console.log('message received: ', Buffer.from(message, 'base64').toString('ascii'));
  try {
    let payload = JSON.parse(Buffer.from(message, 'base64').toString('ascii'));
    console.log(`${payload.hops} to ${++payload.hops}`);
    publishAsync(payload.hops, payload.hops + 1);
  } catch (e) {
    console.log('No payload in message');
  }
});

client.on('packetsend', () => {
});
