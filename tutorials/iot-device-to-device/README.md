# Device to Device demo

Demonstrates how to relay messages from one device to another device using
Google Cloud functions.

## Setup

Make sure that you have enabled the [Cloud IoT Core API](https://console.cloud.google.com/apis/library/cloudiot.googleapis.com/)
from the Google Cloud Console.

## Running

### Create a Google Cloud IoT Core topic

From the [Google Cloud Console](https://console.cloud.google.com/iot) create
a Google Cloud IoT Core Device Registry. When you create it, either set the
event notification topic to an existing PubSub topic or create a new topic to
be used for the demo.

### Upload the Google Cloud Function

[The dev2dev instructions](dev2dev/README.md) explain how to upload the
Google Cloud function to relay messages from one device to another.

Set it to trigger on the topic configured with your device registry.

```
    gcloud beta functions deploy relayCloudIot \
        --stage-bucket=gs://your-gcs-bucket \
        --trigger-topic=your-topic-id
```

#### Register a Device

1. Generate an RSA256 keypair:

```
    openssl req -x509 -newkey rsa:2048 -days 3650 -keyout rsa_private.pem -nodes -out \
        rsa_cert.pem -subj "/CN=unused"
```

2. Use the keypair to register your device:

```
    gcloud beta iot devices create \
        --registry=<your-registry-id> \
        --region "europe-west1" \
        --public-key path=rsa_cert.pem,type=rs256 <deviceId>
```

###  Connect your virtual device

```
    cd virtualdevice
    npm install
    node virtualdev.js --cloudRegion=<region-from-console> \
        --projectId<your-project-id> \
        --deviceId=<your-device-id>\
        --privateKeyFile=../rsa_private.pem \
        --algorithm=RS256 \
        --numMessages=1 \
        --registryId=<your-registry-id>
```

When the sample runs, the virtual device will trigger configuration updates
from the Google Cloud Functions.

## Troubleshooting

When you run the sample code, run the following command to print the output
from the Google Cloud Function:

```
    gcloud beta functions logs read
```

This is useful for debugging aspects of the demo that run on the Google Cloud
Functions callback.
