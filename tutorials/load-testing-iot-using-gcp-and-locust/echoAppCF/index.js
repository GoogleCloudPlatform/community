
'use strict';

const {google} = require('googleapis');

const API_VERSION = 'v1';
const DISCOVERY_API = 'https://cloudiot.googleapis.com/$discovery/rest';
const discoveryUrl = `${DISCOVERY_API}?version=${API_VERSION}`;

// Sends a command to a device.
function sendCommand (client, deviceId, registryId, projectId, region, command) {
  const parentName = `projects/${projectId}/locations/${region}`;
  const registryName = `${parentName}/registries/${registryId}`;
  const binaryData = Buffer.from(command).toString('base64');
  const request = {
    name: `${registryName}/devices/${deviceId}`,
    binaryData: binaryData
  };

  return new Promise((resolve, reject) => {
    client.projects.locations.registries.devices.sendCommandToDevice(request,
      (err, data) => {
        if (err) {
          console.log('*** error sending command', err);
          reject(err);
        } else {
          resolve('ok');
        }
      });
  });
}

exports.echoAppCF = async (data, context) => {
  console.log('*** data=', data);

  // extract attributes needed for sendCommand call
  const deviceAttributes = data.attributes;
  const deviceId = deviceAttributes.deviceId;
  const registryId = deviceAttributes.deviceRegistryId;
  const projectId = deviceAttributes.projectId;
  const region = deviceAttributes.deviceRegistryLocation;

  try {
    // build message to send back
    const deviceMessage = Buffer.from(data.data, 'base64').toString();
    console.log('*** received', deviceMessage);

    const messageToSend = deviceMessage + ' ack';

    // get the auth client
    let authClient = await google.auth.getClient().catch((error) => {
      console.log('*** caught error on getClient', error);
      throw new Error('getClient');
    });

    // set auth
    google.options({
      auth: authClient
    });

    // get API client
    const apiClient = await google.discoverAPI(discoveryUrl).catch((error) => {
      console.log('*** caught error on discoverAPI', error);
      throw new Error('discoverAPI');
    });

    // send the command to the device
    console.log(`*** sending ${messageToSend}`);
    await sendCommand(apiClient, deviceId, registryId, projectId, region, messageToSend).catch((error) => {
      console.log('*** caught error on sendCommand', error);
      throw new Error('sendCommand');
    });
  } catch (error) {
    console.log('*** caught error', error);
  }
};
