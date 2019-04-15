---
title: Introduction to Cloud IoT Core
description: Create a Cloud IoT Core device registry, add a device, and connect.
author: jscud
tags: Cloud IoT
date_published: 2019-04-15
---

# Introduction to Cloud IoT Core

<walkthrough-test-start-page url="/start?tutorial=iot_core_quickstart"/>

<walkthrough-tutorial-url url="https://cloud.google.com/iot/docs/quickstart"/>

<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/nodejs-docs-samples.git" %} -->

<!-- {% setvar repo_name "nodejs-docs-samples" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=iot_core_quickstart)

</walkthrough-alt>

## Introduction

Google Cloud Internet of Things (IoT) Core is a fully managed service for
securely connecting and managing IoT devices, from a few to millions. This
tutorial shows you how to use the `gcloud` command line tool to create a Cloud
IoT Core device registry and add a device. It also shows you how to run an MQTT
sample to connect a device and publish device telemetry events.

This tutorial will walk you through:

-   Creating a Cloud Pub/Sub topic
-   Creating a device registry
-   Adding a device to the registry
-   Setting up credentials on the device
-   Creating a subscription to the Pub/Sub topic to send and receive messages
-   Connecting a virtual device and viewing telemetry data

## Project setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

<walkthrough-project-billing-setup/>

## Using Google Cloud Shell

In this tutorial, you will do all of your work in the Cloud Shell.

### Open Google Cloud Shell

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Turn on Google Cloud APIs

This will enable the Cloud IoT Core API.

<walkthrough-enable-apis apis="cloudiot.googleapis.com"/>

## Create your first topic

A topic is a named resource to which devices send messages. Create your first
topic with the following command:

```bash
gcloud pubsub topics create my-topic
```

You will send several messages to this topic later.

## Create a subscription to the device's topic

Run the following command to create a subscription, which allows you to view the
messages published by your device:

```bash
gcloud pubsub subscriptions create \
    projects/{{project_id}}/subscriptions/my-subscription \
    --topic=my-topic
```

<walkthrough-test-code-output text="Created subscription|Failed to create subscription" />

## Clone the Cloud IoT Core Node.js sample files from GitHub

You'll use the MQTT sample to send messages to Cloud IoT Core.

Note: If the directory already exists, remove the previous files before cloning:

```bash
rm -rf {{repo_name}}
```

Clone the sample program with the following command:

```bash
git clone {{repo_url}}
```

## Grant permission to the Cloud IoT Core service account

Using the helper script in the `/iot/scripts` folder, add the
`cloud-iot@system.gserviceaccount.com` service account to the Cloud Pub/Sub
topic with the Publisher role.

### Navigate to the iot/ directory:

```bash
cd nodejs-docs-samples/iot/
```

### Install the dependencies:

```bash
npm --prefix ./scripts install
```

<walkthrough-test-code-output text="node scripts/postinstall" />

### Run the helper script:

```bash
node scripts/iam.js my-topic
```

The script grants permission to the Cloud IoT Core service account on the
`my-topic` topic.

## Create a device registry

A device registry contains devices and defines properties shared by all of the
contained devices. Create your device registry with the following command:

```bash
gcloud iot registries create my-registry \
    --project={{project_id}} \
    --region=us-central1 \
    --event-notification-config=topic=projects/{{project_id}}/topics/my-topic
```

<walkthrough-test-code-output text="Created registry|ALREADY_EXISTS" />

## Generate your signing keys

To authenticate to Cloud IoT core, a device needs a private key and a public
key. Generate your signing keys by running the following command:

```bash
./scripts/generate_keys.sh
```

This script creates RS256 and ES256 keys in PEM format, but you'll only need the
RS256 keys for this tutorial. The private key must be securely stored on the
device and is used to sign the authentication JWT ([JSON Web
Token](https://cloud.google.com/iot/docs/how-tos/credentials/jwts)). The public
key is stored in the device registry.

## Create a device and add it to the registry

Run the following command to create a device and add it to the registry:

```bash
gcloud iot devices create my-node-device \
    --project={{project_id}} \
    --region=us-central1 \
    --registry=my-registry \
    --public-key path=rsa_cert.pem,type=rs256
```

<walkthrough-test-code-output text="Created device|ALREADY_EXISTS" />

## Connect your device and view telemetry data

In this step, you'll send messages from a virtual device to Pub/Sub. Then,
you'll pull the messages and view them.

### Navigate to the MQTT sample directory:

```bash
cd mqtt_example
```

### Install the Node.js dependencies:

```bash
npm install
```

### Run the following command to connect a virtual device to Cloud IoT Core using the MQTT bridge:

```bash
node cloudiot_mqtt_example_nodejs.js \
    mqttDeviceDemo \
    --cloudRegion=us-central1 \
    --projectId={{project_id}} \
    --registryId=my-registry \
    --deviceId=my-node-device \
    --privateKeyFile=../rsa_private.pem \
    --numMessages=25 \
    --algorithm=RS256 \
    --mqttBridgePort=443
```

The output shows that the virtual device is publishing messages to the telemetry
topic. Twenty-five messages are published.

## Pull published messages

Pull the messages published by the device with the following command:

```bash
gcloud pubsub subscriptions pull --auto-ack \
    projects/{{project_id}}/subscriptions/my-subscription
```

Running this command returns the messages published by the device. The messages
have the following data, `my-registry/my-node-device-payload-<INTEGER>`, a
`MESSAGE_ID`, and an `ATTRIBUTES` list of information about the device. The
`MESSAGE_ID` is a unique ID assigned by the server.

Note: Cloud Pub/Sub doesn't guarantee the order of the messages. It is also
possible that you'll see only one message in Cloud Shell. In that case, try
running the same command several times until you see the other messages.

## View resources in the Google Cloud Platform Console

This concludes the `gcloud` command line tutorial, but you can also use the GCP
Console to view the resources you just created.

Open the [menu](walkthrough://spotlight-pointer?spotlightId=console-nav-menu) on
the left side of the console.

Then select **IoT Core**.

<walkthrough-menu-navigation sectionId="IOT_SECTION"/>

The UI also lets you to create and manage device registries and devices.

## Conclusion

<walkthrough-conclusion-trophy/>

Congratulations! You just walked through the basic concepts of Cloud IoT Core
using the `gcloud` command line tool, and you used the GCP Console to view Cloud
IoT Core resources. The next step is to create awesome applications! For more
information, see [IoT Core documentation](https://cloud.google.com/iot/docs/).

### Here's what you can do next

View more Cloud IoT Core samples on GitHub:

-   [C](https://github.com/GoogleCloudPlatform/cpp-docs-samples/tree/master/iot/mqtt-ciotc)
-   [Java](https://github.com/GoogleCloudPlatform/java-docs-samples/tree/master/iot/api-client)
-   [Node.js](https://github.com/GoogleCloudPlatform/nodejs-docs-samples/tree/master/iot)
-   [Python](https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/iot/api-client)

[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
