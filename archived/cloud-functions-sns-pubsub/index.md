---
title: Connect Google Cloud Pub/Sub to Amazon SNS topics through Cloud Functions
description: Learn how to integrate Google Cloud Pub/Sub with Amazon SNS using Google Cloud Functions.
author: ptone
tags: Cloud Functions, AWS, SNS, Node.js
date_published: 2017-06-23
---

Preston Holmes | Senior Technical Solutions Consultant | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial and sample function demonstrates using [Google Cloud Functions][functions] as an integration point between the
[Amazon Simple Notification Service][sns] (SNS) and Google Cloud Pub/Sub. The function is implemented in [Node.js][node].

[functions]: https://cloud.google.com/functions
[node]: https://nodejs.org/en/
[sns]: https://aws.amazon.com/sns/

The SNS service makes a POST request to the Cloud Function URL when a
message is published to the corresponding SNS topic. The function validates the
sender and topic.

The function then publishes the message to Pub/Sub, tagging the message
with attributes of SNS subject, and message ID.

## Prerequisites

1.  Create a project in the [Cloud Console][console].
1.  [Enable billing][billing] for your project.
1.  Install the [Cloud SDK][sdk].
1.  Have an AWS console account with access to the SNS service.

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing


## Setting up the SNS topic

For this section you should already be familiar with Amazon SNS.
[Create an SNS topic for this tutorial][sns-create], if you do not already have
one you want to use. You will come back to the AWS console to create the
subscription.

[sns-create]: http://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html

## Create your Pub/Sub topic and subscription

1.  Read about [Pub/Sub concepts][pubsubconcepts].
1.  Run the following command to create the topic that will receive SNS messages:

        gcloud pubsub topics create sns-events

1.  Run the following commands to create a subscription to test the
	integration:

        gcloud pubsub subscriptions create sns-watcher --topic sns-events


## Preparing the Cloud Function

1.  Create a `package.json` file by running the following command:

        npm init

1.  Run the following command to install the dependencies that the function
	uses to validate the request:

        npm install --save sns-validator

1.  Run the following command to install the dependencies that the function uses to communicate with the Pub/Sub service:

        npm install --save --save-exact @google-cloud/pubsub@2.14.0

[AWS SNS]: https://aws.amazon.com/sns/

### Writing the Function code

Create a file named `index.js` with the following contents:

[embedmd]:# (index.js)
```js
'use strict';

// We use the https library to confirm the SNS subscription
const https = require('https');

// import the Google Cloud Pub/Sub client library
const { PubSub } = require('@google-cloud/pubsub');

// the sns-validator package verifies the host an signature of SNS messages
const MessageValidator = require('sns-validator');
const validator = new MessageValidator();

// our Pub/Sub client
const pubsub = new PubSub();

// the Pub/Sub topic we will publish messages to
const topicName = 'sns-events';
const topic = pubsub.topic(topicName);

const expectedTopicArn = process.env.SNS_TOPIC_ARN;

/**
 * Cloud Function.
 *
 * @param {req} request The web request from SNS.
 * @param {res} The response returned from this function.
 */
exports.receiveNotification = function receiveNotification (req, res) {
  // we only respond to POST method HTTP requests
  if (req.method !== 'POST') {
    res.status(405).end('only post method accepted');
    return;
  }

  // all valid SNS requests should have this header
  const snsHeader = req.get('x-amz-sns-message-type');
  if (snsHeader === undefined) {
    res.status(403).end('invalid SNS message');
    return;
  }

  // use the sns-validator library to verify signature
  // we first parse the Cloud Function body into a JavaScript object
  validator.validate(JSON.parse(req.body), async function (err, message) {
    if (err) {
      // the message did not validate
      res.status(403).end('invalid SNS message');
      return;
    }
    if (message.TopicArn !== expectedTopicArn) {
      // we got a request from a topic we were not expecting to
      // this sample is set up to only receive from one specified SNS topic
      // one could adapt this to accept an array, but if you do not check
      // the origin of the message, anyone could end up publishing to your
      // cloud function
      res.status(403).end('invalid SNS Topic');
      return;
    }

    // here we handle either a request to confirm subscription, or a new
    // message
    switch (message.Type.toLowerCase()) {
      case 'subscriptionconfirmation':
        console.log('confirming subscription ' + message.SubscribeURL);
        // SNS subscriptions are confirmed by requesting the special URL sent
        // by the service as a confirmation
        https.get(message.SubscribeURL, (subRes) => {
          console.log('statusCode:', subRes.statusCode);
          console.log('headers:', subRes.headers);

          subRes.on('data', (d) => {
            console.log(d);
            res.status(200).end('ok');
          });
        }).on('error', (e) => {
          console.error(e);
          res.status(500).end('confirmation failed');
        });
        break;
      case 'notification':
        // this is a regular SNS notice, we relay to Pub/Sub
        console.log(message.MessageId + ': ' + message.Message);

        const attributes = {
          snsMessageId: message.MessageId,
          snsSubject: message.Subject
        };

        const msgData = Buffer.from(message.Message);

        // Send a message to the topic
        try {
          const messageId = await topic.publish(msgData, attributes);
          console.log('message published ' + messageId);
          res.status(200).end('ok');
        } catch (error) {
          console.error(`Received error while publishing: ${error.message}`);
          res.status(400).end('failed to publish message');
        }
        break;
      default:
        console.error('should not have gotten to default block');
        res.status(400).end('invalid SNS message');
    }
  });
};

```

Notice the named export `receiveNotification`. This function executes when an
SNS message is sent to your SNS topic.

The `receiveNotification` function does the following:

1.  Validates that the request came from SNS. SNS signs each message.
1.  Confirms a pending subscription when the function is first set up as an SNS subscription.
1.  Relays messages published to the SNS topic into Google Cloud Pub/Sub.

Be sure to update the Pub/Sub topic if it is different in your project, and
update the `expectedTopicArn` to match the ARN of your SNS topic.

This is an important security point. Because HTTPS Cloud Function endpoints are
otherwise unauthenticated, you want to ensure that only the intended SNS
points of origin can relay messages into Pub/Sub.

## Deploying the Cloud Function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following command to deploy the function:

        gcloud functions deploy receiveNotification --trigger-http \
          --security-level=secure-always \
          --allow-unauthenticated \
          --entry-point=receiveNotification \
          --runtime=nodejs14 \
          --set-env-vars SNS_TOPIC_ARN=[YOUR_SNS_TOPIC_ARN]

    
    Replace [YOUR_SNS_TOPIC_ARN] with your SNS topic ARN.

1.  Copy the `httpsTrigger` URL in the output after the function deploys. You
use the URL in the next step.

## Creating the SNS subscription

1.  In the AWS console, go to your SNS topic and create a subscription.
1.  Choose HTTPS as the protocol.
1.  Enter the Cloud Function URL that you copied earlier.
1.  Click **Create Subscription**.

The new subscription is created in a pending state. SNS sends a confirmation
request to the Cloud Function. The function recognizes the request as
a confirmation request and confirms by fetching a specific URL provided by SNS.
If you refresh your topic's subscription list in a moment, you will see the
pending state replaced with a subscription ARN.

## Testing the integration

Use the Publish feature in the SNS section of the AWS console to generate a test
message in raw format. Wait a few seconds and then run the following command to
confirm that Cloud Function relayed the message to Google Cloud Pub/Sub:

	gcloud pubsub subscriptions pull sns-watcher --auto-ack

Note that the SNS subject was converted to a Pub/Sub attribute.

[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem
[pubsubconcepts]: https://cloud.google.com/pubsub/docs/overview#concepts
[ARN]: http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html 
