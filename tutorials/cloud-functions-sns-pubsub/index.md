---
title: Connect Google Cloud Pub/Sub to AWS SNS topics through Cloud Functions
description: Learn how to integrate Google Cloud Pub/Sub with AWS SNS using Google Cloud Functions.
author: ptone
tags: Cloud Functions, AWS, SNS, Node.js
date_published: 2017-06-23
---
## Introduction

This tutorial and sample function demonstrates using [Google Cloud
Functions][functions] as an integration point between the [Amazon Simple
Notification Service][sns] (SNS) and Google Cloud Pub/Sub (Cloud Pub/Sub).  The
function is implemented in [Node.js][node].

[functions]: https://cloud.google.com/functions
[twilio]: https://www.twilio.com/
[node]: https://nodejs.org/en/
[sns]: https://aws.amazon.com/sns/

The SNS service makes a POST request to the Cloud Function URL when a
message is published to the corresponding SNS topic. The function validates the
sender and topic.

The function then publishes the message to Cloud Pub/Sub - tagging the message
with attributes of SNS subject, and message id.

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  [Enable billing][billing] for your project.
1.  Install the [Google Cloud SDK][sdk].
1.  Have an AWS console account with access to the SNS service.

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing


## Setting up the SNS topic

For this section it is assumed that you are already familiar with AWS SNS,
[create an SNS topic for this tutorial][sns-create] if you do not already have
one you want to use. We will come back to the AWS console to create the
subscription.

[sns-create]: http://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html

## Create your Cloud Pub/Sub topic and subscription

1.  Read about [Cloud Pubsub concepts][pubsubconcepts].
1.  Run the following command to create the topic that will receive SNS messages:

	gcloud beta pubsub topics create sns-events

1.  Run the following commands to create a subscription to test the
	integration:

	gcloud beta pubsub subscriptions create sns-watcher --topic sns-events


## Preparing the Cloud Function

1.  Create a `package.json` file by running the following command:

        npm init

1.  Run the following command to install the dependencies that the function
	uses to validate the request:

        npm install --save sns-validator

1.  Run the following command to install the dependencies that the function
	uses to communicate with Cloud Pub/Sub service:

		npm install --save @google-cloud/pubsub

[AWS SNS]: https://aws.amazon.com/sns/

### Writing the Function Code

Create a file named `index.js` with the following contents:

[embedmd]:# (index.js)
```js
TODO - embed
```

Notice the named export `receiveNotification` - this function executes when an
SNS message is sent to your SNS topic.

The `receiveNotification` function does the following:

1.  Validates that the request came from SNS. SNS signs each message.
1.  Confirms a pending subscription when the function is first set up as an SNS
	subscription.
1.  Relays messages published to the SNS topic into Cloud Pub/Sub

Be sure to update the Cloud Pub/Sub topic if it is different in your project, and
update the `expectedTopicArn` to match the ARN of your SNS topic.

This is an important security point. Because HTTPS Cloud Function endpoints are
otherwise unauthenticated, you want to ensure that only the intended SNS
points of origin can relay messages into Cloud Pub/Sub.

## Deploying the Cloud Function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following command to deploy the function:

        gcloud beta functions deploy reply --trigger-http --stage-bucket [YOUR_STAGE_BUCKET]

    Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

1.  Copy the httpsTrigger URL in the output after the function deploys. You
	will use the URL in the next step.

## Creating the SNS subscription

1.  In the AWS console, go to your SNS topic and create a subscription.
1.  Choose `HTTPS` as the protocol.
1.  Enter the Cloud Function URL that you copied earlier.
1.  Click *Create Subscription*.

The new subscription is created in a pending state. SNS sends a confirmation
request to the Cloud Function. The function recognizes the request as
a confirmation request and confirms by fetching a specific URL provided by SNS.
If you refresh your topic's subscription list in a moment, you will see the
pending state replaced with a subscription ARN.

## Testing the integration

Use the Publish feature in SNS section of the AWS console to generate a test
message in raw format. Wait a few seconds and then run the following command to
confirm that Cloud Function relayed the message to Cloud Pub/Sub:

	gcloud beta pubsub subscriptions pull sns-watcher --auto-ack

Note that the SNS subject was converted to a Cloud Pub/Sub attribute.

[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem
[pubsubconcepts]: https://cloud.google.com/pubsub/docs/overview#concepts
[ARN]: http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html 
