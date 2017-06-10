---
title: Connect Google Cloud Pubsub to AWS SNS topics through Cloud Functions
description: Learn how to integrate Google Cloud Pubsub with AWS SNS using
Google Cloud Functions.
author: ptone
tags: Cloud Functions, AWS, SNS, Node.js
date_published: x
---
## Introduction

This tutorial and sample demonstrates using [Google Cloud Functions][functions]
to act as an integration point between the AWS Simple Notification Service
(SNS) and Google Cloud Pubsub.  The Cloud Function is implemented in
[Node.js][node].

[functions]: https://cloud.google.com/functions
[twilio]: https://www.twilio.com/
[node]: https://nodejs.org/en/

The sample Cloud Function is triggered by a webhook request from SNS when a
message is published to the corresponding SNS topic. The function validates the
sender and topic.

The function then publishes the message to Cloud Pubsub - decorating with
attributes of SNS subject, and message id.

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK][sdk].
1.  Have an AWS console account with access to the SNS service.

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/

## Setting up the SNS topic

For this section it is assumed that you are already familiar with AWS SNS,
please see the documentation for creating topics. We will come back to the AWS
console to create the subscription.

## Create your Cloud Pubsub topic and subscription

1.  Read about [Cloud Pubsub concepts][pubsubconcepts].
1.  Run the following to create your topic that will receive SNS messages

	gcloud beta pubsub topics create sns-events

1.  Run the following to create a subscription to test the integration

	gcloud beta pubsub subscriptions create sns-watcher --topic sns-events


## Preparing the Cloud Function

1.  Create a `package.json` file by running the following:

        npm init

1.  Install the dependencies used by the Cloud Function:

        npm install --save sns-validator

    This dependency is used by the Cloud Function to validate the request.
    
        npm install --save google-cloud/pubsub

    This dependency is used by the Cloud Function to publish to Cloud Pubsub

### Writing the Function Code

Create a file named `index.js` with the following contents:

[embedmd]:# (index.js)
```js
'use strict';

const twilio = require('twilio');
const config = require('./config.json');

const MessagingResponse = twilio.twiml.MessagingResponse;

const projectId = process.env.GCLOUD_PROJECT;
const region = 'us-central1';

exports.reply = (req, res) => {
  let isValid = true;

  // Only validate that requests came from Twilio when the function has been
  // deployed to production.
  if (process.env.NODE_ENV === 'production') {
    isValid = twilio.validateExpressRequest(req, config.TWILIO_AUTH_TOKEN, {
      url: `https://${region}-${projectId}.cloudfunctions.net/reply`
    });
  }

  // Halt early if the request was not sent from Twilio
  if (!isValid) {
    res
      .type('text/plain')
      .status(403)
      .send('Twilio Request Validation Failed.')
      .end();
    return;
  }

  // Prepare a response to the SMS message
  const response = new MessagingResponse();

  // Add text to the response
  response.message('Hello from Google Cloud Functions!');

  // Send the response
  res
    .status(200)
    .type('text/xml')
    .end(response.toString());
};
```

Notice the named export `receiveNotification`—this is the function that will be executed
whenever an SNS message is sent to your SNS topic.

The `receiveNotification` function does the following:

1.  Validates that the request came from SNS, SNS signs all messages.
1.  Confirms a pending subscription if this is the first time the function is
	being set up
1.  Relays messages published to the SNS topic into Cloud Pubsub

Be sure to update the Cloud Pubsub topic if it different, and update the
`expectedTopicArn` to match the ARN of your SNS topic. This is an important
security point as HTTP Cloud Function endpoints are world reachable and you
only want to relay messages into Cloud Pubsub from your intended SNS origins.

## Deploying the Cloud Function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following to deploy the function:

        gcloud beta functions deploy reply --trigger-http --stage-bucket [YOUR_STAGE_BUCKET]

    Replacing `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

1.  Note and copy the `httpsTrigger url` in the output once the function is
	deployed, we will use that in the next step.

## Creating the SNS subscription

1.  In the AWS console, go to your SNS topic and create a subscription.
1.  Choose `HTTPS` as the protocol
1.  Enter the Cloud Function url you copied earlier as the endpoint
1.  Click "Create Subscription"

You will see the new subscription created in a pending state. SNS sends
a confirmation to the Cloud Function, and the Function confirms this
subscription by calling back to a specific URL. If you refresh your topic's
subscription list you will see the pending state replaced with a subscription
ARN.

## Testing the integration

Use the Publish feature in AWS console to generate a test message in raw
format. In a few seconds you can confirm this message was relayed by the
Function into Pubsub by running the following:

	gcloud beta pubsub subscriptions pull sns-watcher --auto-ack

Note that the SNS subject was converted to a Cloud Pubsub attribute.



[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem
[pubsubconcepts]: 
[ARN]: 
