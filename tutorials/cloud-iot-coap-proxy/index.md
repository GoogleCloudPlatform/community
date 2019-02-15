---
title: IoT Core CoAP proxy demonstration
description: Deploy a CoAP proxy to GCP that bridges IoT Core devices to the HTTP data broker of IoT Core.
author: ptone
tags: IoT, Internet of Things, CoAP, prometheus
date_published: 2018-02-04
---


Preston Holmes | Solution Architect | Google Cloud

[CoAP](http://coap.technology/) is a specialized transfer protocol over UDP for use with constrained devices. This tutorial demonstrates how to deploy a server that will proxy requests from the CoAP protocol to [Google IoT Core](https://cloud.google.com/iot-core/).

## Objectives

* Deploy a basic instance of the CoAP proxy demonstration server.
* Create a sample device in IoT Core.
* Send messages as that device with sample CoAP client tool.

## Proxy design

CoAP was designed to resemble HTTP with request response actions similar to HTTP verbs such as GET and PUT.

IoT Core provides both an MQTT and HTTP interface, supporting requests that allow devices to push state or telemetry events, or retrieve device configuration over HTTP.

The COAP proxy listens at a specific path:
`/gcp`

The `proxy-uri` field of the CoAP request must be of this form:
`/{project-id}/{cloud-region}/{registry-id}/{device-id}/{config,publishEvent,setState}?jwt={jwt}`

The proxy will forward to the [IoT Core HTTP Bridge endpoints](https://cloud.google.com/iot/docs/reference/cloudiotdevice/rest/v1/projects.locations.registries.devices). It supports the following requests:

* `config`: Gets the configuration of a device.
* `publishEvent`: Publishes a telemetry event for a device.
* `setState`: Sets the state of a device.

The proxy provides pass-through authentication passively to the IoT Core. The server will relay the device credential directly to IoT Core without validating it, returning any auth errors to the CoAP client. 

The incoming CoAP payload is converted to the required format of the IoT Core HTTP Bridge (for example, the payload will automatically be base64-encoded and wrapped in a JSON object).

Responses from the IoT core HTTP Bridge will be returned to the client with an appropriate CoAP response code.

## Before you begin

You might want to create a new project to try this tutorial. This tutorial makes use of APIs that require billing being enabled on the project.

This tutorial assumes that all command-line steps are performed inside [Google Cloud Shell](https://cloud.google.com/shell/docs/quickstart), where all of the tools needed are pre-installed. If you want to use another environment, you will need to install tools like [gcloud](https://cloud.google.com/sdk/) and [mvn](https://maven.apache.org/install.html), and set the `GOOGLE_CLOUD_PROJECT` environment variable.

1.  Clone this tutorial repository:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/cloud-iot-coap-proxy

1.  Enable APIs:

        gcloud services enable cloudiot.googleapis.com cloudbuild.googleapis.com compute.googleapis.com containerregistry.googleapis.com

## Set up IoT Core registry

You'll need a registry set up in IoT Core if you haven't already done that.

    gcloud pubsub topics create coap-events
    gcloud iot registries create coap-demo --region us-central1 --event-notification-config topic=coap-events

## Build and run the proxy

### Build a dockerized version of the proxy with Cloud Build

    scripts/cloudbuild.sh

### Deploy the proxy to an instance

    gcloud compute instances create-with-container coap-proxy-demo \
    --tags=coap --container-image gcr.io/$GOOGLE_CLOUD_PROJECT/coap-proxy \
    --zone us-central1-a \
    --container-env=PSK_IDENTITY=my_identity,PSK_SECRET=some_secret

### Enable CoAP traffic with firewall rule

    gcloud compute firewall-rules create allow-coap --action=ALLOW \
    --rules=udp:5684 --source-ranges=0.0.0.0/0 --target-tags=coap

## Using the CoAP DTLS test client

The test client can be used to verify end-to-end COAP DTLS connectivity.

### Add a device

IoT Core devices are [authenticated](https://cloud.google.com/iot/docs/how-tos/credentials/keys#generating_an_es256_key) via private/public keys, so you’ll need to create a key pair with OpenSSL. This walkthrough assumes you have OpenSSL installed somewhere. Run the following commands from a terminal to generate an elliptic-curve keypair:

    cd coap-dtls-client/
    openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem
    openssl ec -in ec_private.pem -pubout -out ec_public.pem

**Note:** We use ES256 because the key is sent in the `proxy-uri` field of each CoAP request, which has a limited number of characters available, and ES256 is short.

    gcloud iot devices create --registry=coap-demo --region=us-central1 --public-key path=./ec_public.pem,type=es256-pem demo-device

Move the device private key into the client resources:

    mv ec_private.pem ./src/main/resources/

### Build the executable

Use maven to build the uber-jar file. The CoAP DTLS test client has been tested on Java 8.

    mvn clean package

#### Run the sample client

The CoAP DTLS client has been tested on Java 8. 

Assuming you have followed all of the defaults in this tutorial, you can now prepare the environment for the sample client. Otherwise open and edit those values:

    source client.env

Now set device state via CoAP:

    java -jar ./target/coap-dtls-client-1.0-SNAPSHOT.jar demo-device setState $COAPS_URI "hello from coap"

Retrieve the state directly from the device manager:

    gcloud iot devices describe --region us-central1 --registry coap-demo demo-device --format="value(state.binaryData)" | base64 --decode ; echo

Set a config value for the device directly in the device manager:

    gcloud iot devices configs update --project $GOOGLE_CLOUD_PROJECT --region us-central1 --registry coap-demo --device demo-device --config-data "Nice to meet you"

Retrieve it with CoAP:

    java -jar ./target/coap-dtls-client-1.0-SNAPSHOT.jar demo-device config $COAPS_URI

You can also see these state and config values in the GCP Console.


## Cleaning up and next steps

Shut down server and remove the firewall rule:

    gcloud compute instances delete coap-proxy-demo --zone us-central1-a
    gcloud compute firewall-rules delete allow-coap

Remove IoT resources:

    gcloud iot devices delete --region us-central1 --registry coap-demo demo-device
    gcloud iot registries delete --region us-central1 coap-demo
    gcloud pubsub topics delete coap-events

Learn more about [Cloud IoT](https://cloud.google.com/solutions/iot/).
