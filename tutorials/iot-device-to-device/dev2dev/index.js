// [START iot_relay_message_js]
'use strict';
const {google} = require('googleapis');

const projectId = 'replace-with-your-project-id';
const cloudRegion = 'replace-with-your-region';

exports.relayCloudIot = function (event, callback) {
  console.log(event.data);
  const record = JSON.parse(
    event.data
      ? Buffer.from(event.data, 'base64').toString()
      : '{}');
  console.log(record);

  let messagesSent = record.hops;
  messagesSent = messagesSent + 1;
  console.log(`${record.deviceId} ${record.registryId} ${messagesSent}`);

  const config = {
    cloudRegion: record.cloudRegion,
    deviceId: record.deviceId,
    registryId: record.registryId,
    hops: messagesSent
  };

  google.auth.getClient().then(client => {
    google.options({
      auth: client
    });
    console.log('START setDeviceConfig');
    const parentName = `projects/${projectId}/locations/${cloudRegion}`;
    const registryName = `${parentName}/registries/${config.registryId}`;
    const binaryData = Buffer.from(JSON.stringify(config)).toString('base64');
    const request = {
      name: `${registryName}/devices/${config.deviceId}`,
      versionToUpdate: 0,
      binaryData: binaryData
    };
    console.log('Set device config.');
    return google.cloudiot('v1').projects.locations.registries.devices.modifyCloudToDeviceConfig(request);
  }).then(result => {
    console.log(result);
    console.log(result.data);
  });
};
// [END iot_relay_message_js]
