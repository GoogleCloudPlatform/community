---
title: Cloud IoT Core device-to-device communication
description: Learn how to relay messages from one device to another using Cloud Functions.
author: gguuss
tags: Cloud IoT Core, Cloud IoT, Cloud Functions, internet of things
date_published: 2017-12-05
---

Sometimes you want to have one device control another device. For example, let's
say that you have a device (Device 1) that is a switch that reconfigures a
second device (Device 2) to be "awake". In this scenario, you would want for a
change on the first device (switch 1 set to "awake") to trigger a change on the
second device (Device 2 set to "awake").

One approach to triggering the configuration change is to do the following:

1. Send telemetry message from Device 1 to Cloud Pub/Sub using Cloud IoT Core bridge
1. Configure Cloud Function to receive message and send configuration change
1. Receive configuration change on Device 2

![Overview of device to device communication](https://storage.googleapis.com/gcp-community/tutorials/iot-device-to-device/overview.png)

This tutorial demonstrates how you can do each of these steps.

## Create a Cloud IoT Core topic

From the [Google Cloud Platform Console](https://console.cloud.google.com/iot), create
a Cloud IoT Core Device Registry. When you create it, either set the
event notification topic to an existing Cloud Pub/Sub topic or create a new topic to
be used for the demo.

## Upload the Cloud Function

The [dev2dev/ folder](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/iot-device-to-device/dev2dev)
of the tutorial contains an example Cloud Function that contains the
`getClient` and `setDeviceConfig` functions from the
[NodeJS manager sample](https://github.com/GoogleCloudPlatform/nodejs-docs-samples/tree/master/iot/manager).

Note that Application default credentials are used to authorize the client:

```js
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
  //...
}
```

The Cloud Function exported by the script is titled `relayCloudIot` and
is specifed as:

```js
exports.relayCloudIot = function (event, callback) {
```

Within the fuction, the first thing that happens is the message sent to the Cloud Pub/Sub queue is parsed:

```js
const record = JSON.parse(
    pubsubMessage.data ?
        Buffer.from(pubsubMessage.data, 'base64').toString() :
        '{}');
```

Next, we increment the hops counter from the parsed record and log the parsed
value, which can be checked with `gcloud beta functions logs read`:

```js
let messagesSent = record.hops;
messagesSent++;

console.log(`${record.deviceId} ${record.registryId} ${messagesSent}`);
```

Finally, we send a new configuration to the device specified in the record:

```js
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
```

To setup the Cloud Function, deploy it to trigger on the topic
configured with your device registry.

    gcloud beta functions deploy relayCloudIot \
        --stage-bucket=gs://your-gcs-bucket \
        --trigger-topic=your-topic-id

## Register a Device

Before you can connect a device, you must register its public key with the
Cloud IoT Core device manager. There are a number of ways to do this,
but for now, we'll use the terminal and `gcloud`.

The following command will generate a RSA-256 keypair:

    openssl req -x509 -newkey rsa:2048 -days 3650 -keyout rsa_private.pem -nodes -out \
        rsa_cert.pem -subj "/CN=unused"

After you have generated the keypair, use the public key to register your
device:

    gcloud beta iot devices create \
        --registry=[YOUR_REGISTRY_ID] \
        --region "europe-west1" \
        --public-key path=rsa_cert.pem,type=rs256 [YOUR_DEVICE_ID]

Now that you have registered a device, you can connect it using the virtual
device provided in the sample.

##  Connect your virtual device

The virtual device is based on the [NodeJS MQTT device sample](https://github.com/GoogleCloudPlatform/nodejs-docs-samples/tree/master/iot/mqtt_example)
with two small differences: the telemetry message that is sent is updated and
the handler for receieving messages is different.

The following code shows how the telemetry message is generated and sent:

```js
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
```

The following code shows how the demo app handles configuration change
messages:

```js
client.on('message', (topic, message, packet) => {
    console.log('message received: ', Buffer.from(message, 'base64').toString('ascii'));
    let payload = JSON.parse(Buffer.from(message, 'base64').toString('ascii'));
    console.log(`${payload.hops} to ${++payload.hops}`);
    publishAsync(payload.hops, payload.hops+1);
});
```

To run the demo after you have successfully setup your Device Registry and
deployed your Cloud Function, run the following command from the
`virtualdevice` folder:

    cd virtualdevice
    npm install
    node virtualdev.js --cloudRegion=<region-from-console> \
        --projectId=[YOUR_PROJECT_ID] \
        --deviceId=[YOUR_DEVICE_ID]\
        --privateKeyFile=../rsa_private.pem \
        --algorithm=RS256 \
        --numMessages=1 \
        --registryId=[YOUR_REGISTRY_ID]

When the virtual device connects, it transmits a telemetry message that is
turned into a Cloud Pub/Sub message that reaches the Cloud
Function. The Cloud Function then generates a callback message based on
the telemetry data, which contains the registry and device IDs, set to the
connecting device ID.

Because the connecting device ID is used, the device is be returned a
configuration change message from the Cloud IoT Core service.  When the device
receives the message, it will then send another telemetry message to the
server. This will then generate another configuration change message which
is transmitted back to the device.

After running the demo for a few seconds, you can look at the configuration
change messages in the console to see how many hops were made between the device
and configuration update call.

The following is an example of how the demo output looks:

First, running the virtual device demo:

    Google Cloud IoT Core MQTT example.
    connect
    Publishing message: { cloudRegion: 'europe-west1',
      deviceId: 'forthedocs',
      registryId: 'europop',
      hops: 1 }
    Closing connection to MQTT. Goodbye!
    close
    Waited long enough then.

Next, logs from Cloud Functions:

    D      relayCloudIot  42015704282425  2018-02-22 00:51:14.354  Function execution started
    I      relayCloudIot  42015704282425  2018-02-22 00:51:14.517  forthedocs europop 2
    I      relayCloudIot  42015704282425  2018-02-22 00:51:15.101  Set device config.
    I      relayCloudIot  42015704282425  2018-02-22 00:51:15.899  Success : { version: '2',
              cloudUpdateTime: '2018-02-22T00:51:15.829404Z',
              binaryData: '...=' }

At this point, a configuration message has been set on the device. Running the
sample again will pick up that configuration message when the demo begins:

    message received:  {"cloudRegion":"europe-west1","deviceId":"forthedocs","registryId":"europop","hops":2}
    2 to 3
    Publishing message: { cloudRegion: 'europe-west1',
      deviceId: 'forthedocs',
      registryId: 'europop',
      hops: 3 }
    Closing connection to MQTT. Goodbye!
    close
    Backing off for 1843.9829280920678ms before publishing.
    Waited long enough then.
    Waited long enough then.
    Publishing message: { cloudRegion: 'europe-west1',
      deviceId: 'forthedocs',
      registryId: 'europop',
      hops: 4 }
    Waited long enough then.
    Closing connection to MQTT. Goodbye!

At this point, the demo is pinging the Google Cloud Function and looping back
configuration updates to the device, demonstrating device to device communication.
