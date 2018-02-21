'use strict';

const fs = require('fs');
const google = require('googleapis');

const API_VERSION = 'v1';
const DISCOVERY_API = 'https://cloudiot.googleapis.com/$discovery/rest';
const discoveryUrl = `${DISCOVERY_API}?version=${API_VERSION}`;

// From nodejs-docs-samples/iot/manager.js ... with getApplicationDefault creds
function getClient (serviceAccountJson, cb) {
  google.auth.getApplicationDefault(function (err, authClient, projectId) {
    if (err) {
      console.log('Authentication failed because of ', err);
      return;
    }
    if (authClient.createScopedRequired && authClient.createScopedRequired()) {
      var scopes = ['https://www.googleapis.com/auth/cloud-platform'];
      client = authClient.createScoped(scopes);
    }

    google.options({auth: authClient});
    google.discoverAPI(discoveryUrl, {}, (err, client) => {
      if (err) {
        console.log('Error during API discovery', err);
        return undefined;
      }
      cb(client);
    });
  });
}

// From nodejs-docs-samples/iot/manager.js#605...636
function setDeviceConfig (client, deviceId, registryId, projectId,
    cloudRegion, data, version) {
  const parentName = `projects/${projectId}/locations/${cloudRegion}`;
  const registryName = `${parentName}/registries/${registryId}`;

  const binaryData = Buffer.from(data).toString('base64');
  const request = {
    name: `${registryName}/devices/${deviceId}`,
    versionToUpdate: version,
    binaryData: binaryData
  };

  console.log('Set device config.');

  client.projects.locations.registries.devices.modifyCloudToDeviceConfig(
      request,
      (err, data) => {
        if (err) {
          console.log('Could not update config:', deviceId);
          console.log('Message: ', err);
        } else {
          console.log('Success :', data);
        }
      });
}

exports.relayCloudIot = function (event, callback) {
  // [START iot_relay_message_js]
  const pubsubMessage = event.data;
  const record = JSON.parse(
      pubsubMessage.data ?
          Buffer.from(pubsubMessage.data, 'base64').toString() :
          '{}');

  let messagesSent = record.hops;
  messagesSent = messagesSent+1;
  console.log(`${record.deviceId} ${record.registryId} ${messagesSent}`);

  const config = {
    cloudRegion: record.cloudRegion,
    deviceId: record.deviceId,
    registryId: record.registryId,
    hops: messagesSent
  };

  const cb = function (client) {
    setDeviceConfig(client, record.deviceId, record.registryId,
        process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT,
        record.cloudRegion, JSON.stringify(config), 0);
  };

  getClient(process.env.GOOGLE_APPLICATION_CREDENTIALS, cb);
  // [END iot_relay_message_js]
};

