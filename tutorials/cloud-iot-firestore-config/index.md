---
title: Using Cloud Firestore with Cloud IoT Core for device configuration
description: Learn how to use Cloud Firestore to manage fine-grained configuration updates for devices managed by Cloud IoT Core.
author: ptone
tags: iot, firestore, functions, internet of things
date_published: 2018-05-14
---

Preston Holmes | Solution Architect | Google

This tutorial demonstrates how to configure Cloud Functions for Firebase to relay document changes in [Cloud Firestore](https://firebase.google.com/docs/firestore/) as configuration updates for [Cloud IoT Core](https://cloud.google.com/iot) Devices.

Cloud IoT Core provides a way to send configuration to devices over MQTT or HTTP. The structure of this payload is unspecified and delivered as raw bytes. This means that if you have different parts of your IoT system wanting to write parts of the configuration, each has to parse, patch, then re-write the configuration value in IoT Core.

If you want to payload delivered to a device as a binary format, such as [CBOR](http://cbor.io/), that means each of these participating components of your system also need to deserialize and re-serialize the structured data.

By using Cloud Firestore to serve as a layer in between the systems that update a device's configuration and IoT Core, you can take advantage of Firestore's structured [data types](https://firebase.google.com/docs/firestore/manage-data/data-types) and partial document updates.

## Objectives

- Manage structured device configuration in a managed cloud database.
- Easily perform partial updates of configuration by changing only some fields in device configuration.
- Use queries to find all devices in a specific configuration state.
- Convert human-friendly configuration to binary form before sending to device automatically.


**Figure 1.** *Architecture diagram for tutorial components*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/architecture.png)

## Before you begin

This tutorial assumes you already have a GCP account and have completed the IoT Core [quickstart documentation](https://cloud.google.com/iot/docs/quickstart).

You need to associate Firebase to your GCP project. Visit the [Firebase Console](https://console.firebase.google.com/?authuser=0) and choose to add a project. You can then choose to add Firebase to an existing GCP project.

## Costs

This tutorial uses billable components of GCP, including:

- Cloud IoT Core
- Cloud Firestore
- Cloud Functions for Firebase

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Set up the environment

If you do not already have a development environment set up with the [gcloud](https://cloud.google.com/sdk/downloads) tool and [Firebase](https://firebase.google.com/docs/cli/) tools, you can use [Cloud Shell](https://cloud.google.com/shell/docs/) for any command line instructions.

Set the name of the Cloud IoT Core settings you are using as environment variables:


	export REGISTRY_ID=config-demo
	export CLOUD_REGION=us-central1 # or change to an alternate region;
	export GCLOUD_PROJECT=$(gcloud config list project --format "value(core.project)")


## Create a Cloud IoT Core registry for this tutorial

Create a Cloud Pub/Sub topic to use for device logs:

    gcloud pubsub topics create device-events

Create the IoT Core registry:

    gcloud iot registries create $REGISTRY_ID --region=$CLOUD_REGION --event-notification-config=subfolder="",topic=device-events

## Deploy the relay function

You use a Firestore document trigger to run a function every time a qualifying document is updated.

The function runs only when documents in the `device-configs` collection are updated.

The document key is used as the corresponding device key.

[embedmd]:# (functions/src/index.ts /import/ $)
```ts
import cbor = require('cbor');

import * as admin from "firebase-admin";
import * as functions from 'firebase-functions';
const iot = require('@google-cloud/iot');
const client = new iot.v1.DeviceManagerClient();

// start cloud function
exports.configUpdate = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs/{deviceId}')
  .onWrite(async (change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      const request = generateRequest(context.params.deviceId, change.after.data(), false);
      return client.modifyCloudToDeviceConfig(request);
    } else {
      throw(Error("no context from trigger"));
    }
  });
```

To deploy the Cloud Function, you use the Firebase CLI tool:

    cd functions
    npm install
		firebase functions:config:set \
		iot.core.region=$CLOUD_REGION \
		iot.core.registry=$REGISTRY_ID
    firebase use $GCLOUD_PROJECT
    firebase deploy --only functions

## Create our device

Create a dummy sample device:

    cd ../sample-device
    gcloud iot devices create sample-device --region $CLOUD_REGION --registry $REGISTRY_ID --public-key path=./ec_public.pem,type=ES256

Note: Do not use this device for any real workloads, as the key-pair is included in this sample and therefore is not secret.


### Establish a device configuration in Firestore

Open the [Firebase Console](https://console.firebase.google.com/).

1. Choose the project you previously associated with Firebase. On the left-hand side list of services, choose **Database** and choose to use Firestore.
1. Choose **+ ADD COLLECTION** and name the collection "device-configs".
1. You will be prompted to add your first document, use "sample-device" for the Document Id.
1. For the field, type, and value use the following:

![config-doc](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/config-doc.png)

Note that the different fields in the config can have different data types.  Save this document.

Now open the [Cloud IoT Core console](https://console.cloud.google.com/iot/locations/us-central1/registries/config-demo/devices/sample-device), choose the device and look at the `Configuration & state history` pane:

![config-choose](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/choose-config.png)

If the Function ran succesfully, you should be able to select and see the initial configuration saved with the device.

![initial config](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/initial-config.png)

## Modify the config

Start up the sample device now in your shell, still in the sample-device subfolder:

    npm install
    node build/index.js

You should see output that looks like:

    Device Started
    Current Config:
    { energySave: false, mode: 'heating', tempSetting: 35 }

Now update the config document in the Firestore console to change the `tempSetting` value to 18.

When this document edit is saved, it triggers a function, which will push the new config down to the device:

![field update](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/update.png)

You should see this new config arrive at the sample device in a moment.

    Current Config:
    { energySave: false, mode: 'heating', tempSetting: 18 }

To do this programatically with only the IoT Core APIs, you would have to read the current config from the IoT Core Device Manager, update the value, then write back the new config to IoT Core. IoT Core provides an incrementing version number you can send with these writes to check that another process has not concurrently attempted to update the config.

This solution assumes that the path using Firestore and functions are not sharing the config update job with other processes, but are acting as a flexible intermediate.  Both single Firestore Documents and IoT Core device configurations are limited to one update per second.


## Perform Queries with Firestore

You can use the [query capabilities](https://firebase.google.com/docs/firestore/query-data/queries) of Firestore to find devices with specific configurations:

    var configs = db.collection('device-configs');
    var hotDevices = configs.where('tempSetting', '>', 40);

The above snippet is for Node.js, but see the [Firestore quickstart](https://firebase.google.com/docs/firestore/quickstart) for how to set up and query from a number of different runtimes.


## Binary data with CBOR

Sometimes, with constrained devices and constrained networks, you want to work with data in a compact binary format.  Concise Binary Object Representation [(CBOR)](http://cbor.io/) is a binary format that strikes a balance between the compactness of binary, with the self-describing format of JSON. IoT Core device configuration API and MQTT both fully support binary messages.

In cloud software and databases, binary might not be as convenient to work with, or other binary formats such as protocol buffers might be used.

By using a function as an intermediate between Firestore and IoT Core, you can not only watch documents for change to trigger an update, but you can use the same function to encode the payload into the CBOR binary representation.

For clarity, this tutorial implements this with a different function, and uses a different Firestore collection.

Add the following function definition code to your `index.ts` source file so that it should look like the following:

[embedmd]:# (functions/src/index.ts /import/ $)
```ts
import cbor = require('cbor');

import * as admin from "firebase-admin";
import * as functions from 'firebase-functions';
const iot = require('@google-cloud/iot');
const client = new iot.v1.DeviceManagerClient();

// start cloud function
exports.configUpdate = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs/{deviceId}')
  .onWrite(async (change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      const request = generateRequest(context.params.deviceId, change.after.data(), false);
      return client.modifyCloudToDeviceConfig(request);
    } else {
      throw(Error("no context from trigger"));
    }
  });

exports.configUpdateBinary = functions.firestore
  // assumes a document whose ID is the same as the deviceid
  .document('device-configs-binary/{deviceId}')
  .onWrite(async (change: functions.Change<admin.firestore.DocumentSnapshot>, context?: functions.EventContext) => {
    if (context) {
      console.log(context.params.deviceId);
      const request = generateRequest(context.params.deviceId, change.after.data(), true);
      return client.modifyCloudToDeviceConfig(request);
    } else {
      throw(Error("no context from trigger"));
    }
  });

function generateRequest(deviceId:string, configData:any, isBinary:Boolean) {
  const formattedName = client.devicePath(process.env.GCLOUD_PROJECT, functions.config().iot.core.region, functions.config().iot.core.registry, deviceId);
  let dataValue;
  if (isBinary) {
    const encoded = cbor.encode(configData);
    dataValue = encoded.toString("base64");
  } else {
    dataValue = Buffer.from(JSON.stringify(configData)).toString("base64");
  }
  return {
    name: formattedName,
    binaryData: dataValue
  };
}
```

You can deploy this new function with:

    firebase deploy --only functions

Press CTRL-C to stop the sample device script if it is still running, then create another sample device variation. This one will be named `sample-binary`:

    gcloud iot devices create sample-binary --region $CLOUD_REGION --registry $REGISTRY_ID --public-key path=./ec_public.pem,type=ES256

Create another Firestore collection as you did above, but call it `device-configs-binary` and add a document for the `sample-binary` device.

Now start the device with the `-b` flag to indicate we want to use the binary version of the sample device:

    node build/index.js -b

You can update the device config settings in Firestore, and you will see the decoded config printed on the screen. However the payload of the config is transmitted encoded as CBOR.

Note: When data is encoded as CBOR - you will not be able to see or edit this in the IoT-Core console, as it is in a compact encoded format that the console does not parse for display.

![field update](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-firestore-config/cbor.png)

## Cleaning up

Stop the sample device by pressing CTRL-C.

Because the test devices uses a visible key, you should delete it:

    gcloud iot devices delete sample-device --registry $REGISTRY_ID --region $CLOUD_REGION
    gcloud iot devices delete sample-binary --registry $REGISTRY_ID --region $CLOUD_REGION
