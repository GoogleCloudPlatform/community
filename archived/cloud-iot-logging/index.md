---
title: Using Cloud Logging with IoT Core devices
description: Learn how to use Cloud Logging for application logs from devices.
author: ptone
tags: iot, logging, internet of things
date_published: 2018-05-23
---

Preston Holmes | Solution Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to configure Cloud Functions for Firebase to relay device application logs from [IoT Core](https://cloud.google.com/iot) to
[Cloud Logging](https://cloud.google.com/logging/).

## Objectives

- Send application logs from device software over [MQTT](https://www.mqtt.org/) and IoT Core
- View device logs in Cloud Logging
- Use sorting and searching features of Cloud Logging to find logs of interest
- Use the monitored resource type for IoT devices to see multiple log entries from different sources for a given device

![Architecture diagram for tutorial components](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/architecture.png)


## Before you begin

This tutorial assumes you already have a Google Cloud account set up and have completed the IoT Core [quickstart](https://cloud.google.com/iot/docs/quickstart).

You need to associate Firebase to your Google Cloud project. Visit the [Firebase Console](https://console.firebase.google.com/?authuser=0) and choose to add a project. You can then choose to add Firebase to an existing Google Cloud project.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- IoT Core
- Pub/Sub
- Cloud Functions for Firebase
- Cloud Logging

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Set up the environment

If you do not already have a development environment set up with [gcloud](https://cloud.google.com/sdk/downloads) and [Firebase](https://firebase.google.com/docs/cli/) tools, it is recommended that you use [Cloud Shell](https://cloud.google.com/shell/docs/) for any command line instructions.

### Get the sample code

The sample code for this tutorial is in the
[Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/metrics-export-with-mql).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/cloud-iot-logging

### Set the environment variables

```sh
export REGISTRY_ID=[your registry here]
export CLOUD_REGION=[your region, such as us-central1]
export GCLOUD_PROJECT=$(gcloud config list project --format "value(core.project)")
```

## Create a logs topic, and associate it with a device registry

Create a Cloud Pub/Sub topic that you will use for device logs:

```sh
gcloud pubsub topics create device-logs
```

Assuming you have a registry already created from the required quickstart pre-requisite, add this topic as a notification config for a specific MQTT topic match:


```sh
gcloud iot registries update $REGISTRY_ID --region $CLOUD_REGION --event-notification-config subfolder=log,topic=device-logs
```

This configures IoT Core to send any messages written to the MQTT topic of `/devices/{device-id}/events/log` to be published to a specific Pub/Sub topic created above.

## Deploy the relay function

You can use either Google Cloud Functions or Cloud Functions for Firebase to run the relay (they use the same underlying systems). Here you are using Cloud Functions for Firebase as the tools are a little more straightforward and there are nice [Typescript starting samples](https://firebase.google.com/docs/functions/typescript).

The main part of the function handles a Pub/Sub message from IoT Core, extracts the log payload and device information, and then writes a structured log entry to Cloud Logging:

[embedmd]:# (functions/src/index.ts /import/ $)
```ts
import * as functions from 'firebase-functions';
const { Logging } = require('@google-cloud/logging');

// create the Cloud Logging client
const logging = new Logging({
  projectId: process.env.GCLOUD_PROJECT,
});

// start cloud function
exports.deviceLog =
  functions.pubsub.topic('device-logs').onPublish((message) => {
    const log = logging.log('device-logs');
    const metadata = {
      // Set the Cloud IoT Device you are writing a log for
      // you extract the required device info from the PubSub attributes
      resource: {
        type: 'cloudiot_device',
        labels: {
          project_id: message.attributes.projectId,
          device_num_id: message.attributes.deviceNumId,
          device_registry_id: message.attributes.deviceRegistryId,
          location: message.attributes.location,
        },
      },
      labels: {
        // note device_id is not part of the monitored resource, but you can
        // include it as another log label
        device_id: message.attributes.deviceId,
      },
    };
    const logData = message.json;

    // Here you optionally extract a severity value from the log payload if it
    // is present
    const validSeverity = [
      'DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'ALERT', 'CRITICAL',
      'EMERGENCY',
    ];
    if (logData.severity &&
      validSeverity.indexOf(logData.severity.toUpperCase()) > -1) {
      (metadata as any)['severity'] = logData.severity.toUpperCase();
      delete (logData.severity);


      // write the log entry to Cloud Logging
      const entry = log.entry(metadata, logData);
      return log.write(entry);
    }
  });
```

To deploy the Cloud Function, you use the Firebase CLI tool:

```sh
cd functions
npm install
firebase use $GCLOUD_PROJECT
firebase deploy --only functions
```

## Write logs from a device

create a dummy sample device:

```sh
cd ../sample-device
npm install

gcloud iot devices create log-tester --region $CLOUD_REGION --registry $REGISTRY_ID --public-key path=./ec_public.pem,type=ES256

node build/index.js &
```

**Important:** Do not use this device for any real workloads, because the keypair is included in this sample and should not be considered secret.

## Explore the logs that are written

If you open up the [Cloud Logging console](https://console.cloud.google.com/logs/viewer).

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c1.png)

Because you send the device ID as part of the log record, you can choose to pull that up into the summary line:

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c2.png)

Which then looks like this:

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c3.png)

### Combine system and Applications logs

Now you will exercise a part of our sample device code that responds to config changes. Use the following `gcloud` command to update the devices config telling it to "bounce to a level of 2":

```sh
gcloud iot devices configs update --device log-tester --registry $REGISTRY_ID --region $CLOUD_REGION --config-data '{"bounce": 2}'
```

Now in just a few moments, you will see two new entries in Cloud Logging. One is from IoT Core system noting that a devices config was updated (the `ModifyCloudToDeviceConfig` call).

This is then followed by a device application log reporting the imaginary "spring back" value. This shows how we can view both system logs from IoT Core and device application logs in one place.

You can use the refresh button in the Google Cloud Console, or use the play button to stream logs.

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c4.png)

### Use severity to convey log level

Let's send a couple more config updates (you should send one, wait a second or two, then send the next):

```sh
gcloud iot devices configs update --device log-tester --registry $REGISTRY_ID --region $CLOUD_REGION --config-data '{"bounce": 7}'

# pause

gcloud iot devices configs update --device log-tester --registry $REGISTRY_ID --region $CLOUD_REGION --config-data '{"bounce": 17}'

```

As these are received and responded to by the sample device, you can see the use of a severity level to indicate the importance of the log.

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c5.png)

### Filter logs to a specific device

So far you have been looking at a log that contains entries for all devices. But given these are structured log entries, you can use the numeric ID of the resource to limit our view to only one device in the more realistic scenario when multiple devices are writing log events.

You open up the log entry, find the resource, labels, and choose `device_num_id`, click it and
choose **Show matching entries**:

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c6.png)

This creates a quick filter of the log:

![console image](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-logging/c7.png)

You can get a sense the filter syntax. You can even do things like a substring match on a field in the JSON payload of the log message, try adding `jsonPayload.msg:"Spring"`. See the [docs](https://cloud.google.com/logging/docs/view/advanced-filters) for more on using advanced filters.


## Cleaning up

Kill the sample device:

```sh
killall node
```
Because the test device uses a non-secret key, you should delete it:

```sh
gcloud iot devices delete log-tester --registry $REGISTRY_ID --region $CLOUD_REGION
```

All of the resource in this tutorial cost nothing at rest, or scale to zero. You can delete [Cloud Functions](https://console.cloud.google.com/functions/list), [Device Registry](https://console.cloud.google.com/iot/registries/), and [Pub/Sub topics](https://console.cloud.google.com/cloudpubsub/topicList) from Google Cloud.

