---
title: Introduction to IoT Core
description: Create an IoT Core device registry, add a device, and connect.
author: jscud
tags: Cloud IoT
date_published: 2019-07-31
---

# Introduction to IoT Core

<walkthrough-test-start-page url="/start?tutorial=iot_core_quickstart"/>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=iot_core_quickstart)

</walkthrough-alt>

<!-- {% setvar project_id "<your-project>" %} -->

## Introduction

[IoT Core](https://cloud.google.com/iot/docs/) is a fully managed service for connecting
and managing IoT devices. This tutorial uses the `gcloud` command-line tool to create an
IoT Core device registry, add a device, and run an MQTT sample to connect a device and
publish device telemetry events.

## Project setup

Google Cloud organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Using Cloud Shell

In this tutorial, you do all of your work in Cloud Shell, which is a built-in command-line tool for the Cloud Console.

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

## Enable the IoT Core API

To use the IoT Core API, you must first enable it.

Use the following to enable the API:

<walkthrough-enable-apis apis="cloudiot.googleapis.com"/>

<walkthrough-alt>
https://console.cloud.google.com/flows/enableapi?apiid=cloudiot.googleapis.com
</walkthrough-alt>

## Create your first Pub/Sub topic

A Pub/Sub topic is a named resource to which devices send messages. Create your first
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

## Clone the IoT Core Node.js sample files from GitHub

You use the MQTT sample to send messages to IoT Core.

Clone the sample program with the following command:

```bash
git clone https://github.com/googleapis/nodejs-iot.git
```

## Grant permission to the IoT Core service account

In this section, you use a helper script to add the
`cloud-iot@system.gserviceaccount.com` service account to the Pub/Sub
topic with the Publisher role.

### Navigate to the samples/ directory:

```bash
cd nodejs-iot/samples
```

### Install the dependencies:

```bash
npm install
```

<walkthrough-test-code-output text="node scripts/postinstall" />

### Run the helper script:

```bash
node scripts/iam.js my-topic
```

The script grants permission to the IoT Core service account on the
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

To authenticate to IoT Core, a device needs a private key and a public
key. Generate your signing keys by running the following command:

```bash
./scripts/generate_keys.sh
```

This script creates RS256 and ES256 keys in PEM format, but you'll only need the
RS256 keys for this tutorial. The private key must be securely stored on the
device and is used to sign the authentication
([JWT (JSON Web Token)](https://cloud.google.com/iot/docs/how-tos/credentials/jwts)). The public
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

## Download root credentials

Download [Google's CA root certificate](https://pki.goog/roots.pem) and note the
location where you downloaded it. You'll need the file path when you run the
Node.js command in the next step.

## Connect your device and publish messages

In this section, you send messages from a virtual device to Pub/Sub.

### Navigate to the MQTT sample directory

```bash
cd mqtt_example
```

### Install the Node.js dependencies

```bash
npm install
```

### Connect a virtual device to Cloud IoT Core using the MQTT bridge

```bash
node cloudiot_mqtt_example_nodejs.js \
    mqttDeviceDemo \
    --cloudRegion=us-central1 \
    --projectId={{project_id}} \
    --registryId=my-registry \
    --deviceId=my-node-device \
    --privateKeyFile=../rsa_private.pem \
    --serverCertFile=../roots.pem \
    --numMessages=25 \
    --algorithm=RS256 \
    --mqttBridgePort=443
```

The output shows that the virtual device is publishing messages to the telemetry
topic. 25 messages are published.

## Pull published messages

Pull the messages published by the device with the following command:

```bash
gcloud pubsub subscriptions pull --auto-ack \
    projects/{{project_id}}/subscriptions/my-subscription
```

Running this command returns the messages published by the device. The messages
have the following data, `my-registry/my-node-device-payload-[INTEGER]`, a
`MESSAGE_ID`, and an `ATTRIBUTES` list of information about the device. The
`MESSAGE_ID` is a unique ID assigned by the server.

**Note:** Pub/Sub doesn't guarantee the order of the messages. It is also
possible that you'll see only one message in Cloud Shell. In that case, run
the same command multiple times to see the other messages.

## View resources in the Cloud Console

This concludes the `gcloud` command-line tutorial, but you can also use the Cloud
Console to view the resources you just created.

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
then select **IoT Core**.

<walkthrough-menu-navigation sectionId="IOT_SECTION"/>

You can also use this graphical user interface to create and manage device registries and devices.

## Conclusion

<walkthrough-conclusion-trophy/>

Congratulations! You just walked through the basic concepts of Cloud IoT Core
using the `gcloud` command-line tool, and you used the Cloud Console to view
IoT Core resources. The next step is to create awesome applications! For more
information, see the [IoT Core documentation](https://cloud.google.com/iot/docs/).

### Here's what you can do next

View more IoT Core samples on GitHub in any of several programming languages:

-   [Node.js](https://github.com/googleapis/nodejs-iot/tree/master/samples/)
-   [Python](https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/iot/api-client/)
-   [Java](https://github.com/GoogleCloudPlatform/java-docs-samples/tree/master/iot/api-client)

[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
