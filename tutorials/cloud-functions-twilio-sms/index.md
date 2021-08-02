---
title: Respond to SMS messages with Twilio and Cloud Functions
description: Learn how to receive and respond to SMS messages with Twilio and Cloud Functions.
author: jmdobry
tags: Cloud Functions, Twilio, Node.js
date_published: 2017-02-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using [Cloud Functions][functions] to
reply to an SMS message using [Twilio][twilio]. The Cloud Function is
implemented in [Node.js][node].

[functions]: https://cloud.google.com/functions
[twilio]: https://www.twilio.com/
[node]: https://nodejs.org/en/

The sample Cloud Function is triggered by a webhook request from Twilio when an
SMS message is sent to your Twilio phone number. The webhook validates that the
request came from Twilio and then sends a simple reply.

## Prerequisites

1.  Create a project in the [Cloud Console][console].
1.  Enable billing for your project.
1.  Install the [Cloud SDK][sdk].

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/

## Getting started with Twilio

1.  [Create a Twilio account][try].
1.  In your Twilio console, [create a phone number][number].
1.  Once you have a phone number, click [**Manage Numbers**][manage] and then
    click on your phone number.

1.  Under **Messaging**:
    1.  Set **Configure with** to **Webhooks/TwiML**.
    1.  Set **A Message Comes In** to **Webhook** and enter the following URL:

            https://us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/reply

        Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

    1.  Click **Save**.

1.  Return to your [**Twilio Account Settings**][settings] and take note of the
    Auth Token for your Live Credentials. You will need it later in this
    tutorial.

[try]: https://www.twilio.com/try-twilio
[number]: https://www.twilio.com/user/account/phone-numbers/getting-started
[manage]: https://www.twilio.com/console/phone-numbers/incoming
[settings]: https://www.twilio.com/console/account/settings

## Preparing the Cloud Function

1.  Create a `package.json` file by running the following:

        npm init

    or

        yarn init

1.  Install the single dependency used by the Cloud Function:

        npm install --save twilio

    or

        yarn add twilio

    This dependency is used by the Cloud Function validate the request and
    formulate the response.

1.  Create a file named `config.json` with the following contents:

        {
          "TWILIO_AUTH_TOKEN": "[YOUR_TWILIO_AUTH_TOKEN]"
        }

    Replace `[YOUR_TWILIO_AUTH_TOKEN]` with your Twilio Auth Token from step 5
    of the **Getting Started with Twilio** section.

### Writing the Function code

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

Notice the named export `reply`—this is the function that will be executed
whenever an SMS message is sent to your Twilio number.

The `reply` function does the following:

1.  Validates that the request came from Twilio.
1.  Sends a reply to the SMS message.

## Deploying and testing the Cloud Function

1.  Run the following to deploy the function:

        gcloud functions deploy reply --trigger-http --runtime nodejs10

1.  Send an SMS message to your Twilio phone number and observe the response you
    receive from the Cloud Function.

To view the logs for the Cloud Function, run the following:

    gcloud functions logs read reply

[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem
