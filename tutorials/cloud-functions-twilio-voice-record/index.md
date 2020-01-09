---
title: Record and Analyze Voice Calls with Twilio and the Google Machine Learning APIs on Google Cloud Functions
description: Learn how to record, transcribe, and analyze voice calls with Twilio and the Google Machine Learning APIs on Google Cloud Functions.
author: jmdobry
tags: Cloud Functions, Twilio, Cloud Speech API, Cloud Natural Language API, Node.js
date_published: 2017-02-20
---
## Introduction

This tutorial demonstrates using [Google Cloud Functions][functions] to
record incoming voice calls using [Twilio][twilio]. The recordings are then
transcribed by the [Google Cloud Speech API][speech] and analyzed by the
[Google Cloud Natural Language API][nl]. The final results are stored in a
[Google Cloud Storage][storage] bucket. The Cloud Function is implemented in
[Node.js][node].

[functions]: https://cloud.google.com/functions
[twilio]: https://www.twilio.com/
[speech]: https://cloud.google.com/speech
[nl]: https://cloud.google.com/natural-language
[storage]: https://cloud.google.com/storage
[node]: https://nodejs.org/en/

The sample Cloud Function is triggered by a webhook request from Twilio when a
voice call is made to your Twilio phone number. The webhook validates that the
request came from Twilio, prompts the user to leave a recording, then records
the call. When the recording becomes available, the recording is transcribed
and analyzed for sentiment, entities, and syntax. The final results are stored
in a Cloud Storage bucket.

## Objectives

1.  Obtain a phone number from Twilio.
1.  Deploy a Cloud Function that can receive and record voice calls.
1.  Deploy a Cloud Function that can download voice recordings from Twilio and
    save them to Cloud Storage.
1.  Deploy a Cloud Function that can transcribe the voice recordings, analyze
    them, and save the results to Cloud Storage.

## Costs

Twilio has a free trial, but you need to upgrade to disable the default message
that is played for anyone who calls your Twilio phone number.

This tutorial uses billable components of Google Cloud Platform, including:

- Google Cloud Functions
- Google Cloud Natural Language API
- Google Cloud Speech API
- Google Cloud Storage

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  [Enable the Google Cloud Functions API][enable_functions].
1.  [Enable the Google Cloud Speech API][enable_speech].
1.  [Enable the Google Cloud Natural Language API][enable_nl].
1.  Create a Cloud Storage bucket in which to store voice recordings and the
    results of your analysis:

        gsutil mb -p [YOUR_PROJECT_ID] gs://[RESULTS_BUCKET]

    * Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.
    * Replace `[RESULTS_BUCKET]` with the name you want for your new bucket.
      You'll need the name of this bucket later in this tutorial.

    You can also create a bucket in the [Google Cloud Console][make_bucket].

1.  Install and initialize the [Google Cloud SDK][sdk].

    1. After initializing the SDK, install the Beta components:

            gcloud components install beta

[console]: https://console.cloud.google.com/
[enable_functions]: https://console.cloud.google.com/apis/api/cloudfunctions.googleapis.com/overview
[enable_speech]: https://console.cloud.google.com/apis/api/speech.googleapis.com/overview
[enable_nl]: https://console.cloud.google.com/apis/api/language.googleapis.com/overview
[make_bucket]: https://cloud.google.com/storage/docs/quickstart-console
[sdk]: https://cloud.google.com/sdk/

## Getting started with Twilio

1.  [Create a Twilio account][try]. It is recommended that you upgrade your
    Twilio account to a paid account to avoid the trial restrictions, namely a
    message played to anyone who calls your Twilio phone number.
1.  In your Twilio console, [create a phone number][number].
1.  Once you have a phone number, click [**Manage Numbers**][manage] and then
    click on your phone number.

1.  Under **Voice**:
    1.  Set **Configure with** to **Webhooks/TwiML**.
    1.  Set **A Call Comes In** to **Webhook** and enter the following URL:

            https://us-central1-[YOUR_PROJECT_ID].cloudfunctions.net/handleCall

        Replace `[YOUR_PROJECT_ID]` with your Google Cloud Platform project ID.

    1.  Click **Save**.

1.  Return to your [**Twilio Account Settings**][settings] and take note of the
    Auth Token for your Live Credentials. You will need it later in this
    tutorial.

[try]: https://www.twilio.com/try-twilio
[number]: https://www.twilio.com/user/account/phone-numbers/getting-started
[manage]: https://www.twilio.com/console/phone-numbers/incoming
[settings]: https://www.twilio.com/console/account/settings

## Preparing the function

1.  Create a `package.json` file by running the following:

        npm init

    or

        yarn init

1.  Install the dependencies used by the Cloud Function:

        npm install --save twilio got @google-cloud/speech @google-cloud/language @google-cloud/storage

    or

        yarn add twilio got @google-cloud/speech @google-cloud/language @google-cloud/storage

1.  Create a file named `config.json` with the following contents:

        {
          "RESULTS_BUCKET": "[RESULTS_BUCKET]",
          "TWILIO_AUTH_TOKEN": "[YOUR_TWILIO_AUTH_TOKEN]"
        }

    * Replace `[RESULTS_BUCKET]` with the name of the bucket you created in step
      7 of the **Prerequisites** section.
    * Replace `[YOUR_TWILIO_AUTH_TOKEN]` with your Twilio Auth Token from step 5
      of the **Getting Started with Twilio** section.

## Writing the function code

### Receiving a phone call

First, you'll write a function that will:

1.  Trigger when someone calls your Twilio phone number.
1.  Prompt the caller to leave a message.
1.  Record the caller's message.
    * Maximum message length specified as 60 seconds.
    * The recording status callback URL set to a second function you'll
      implement later in this tutorial.
1.  Finally, hang up.

Create a file named `index.js` with the following contents:

[embedmd]:# (index.js /'use/ /\s};/)
```js
'use strict';

const config = require('./config.json');
const twilio = require('twilio');

const VoiceResponse = twilio.twiml.VoiceResponse;

const projectId = process.env.GCLOUD_PROJECT;
const region = 'us-central1';

exports.handleCall = (req, res) => {
  if (!isValidRequest(req, res, 'handleCall')) {
    return;
  }

  const recordingStatusCallbackUrl = `https://${region}-${projectId}.cloudfunctions.net/getRecording`;

  // Prepare a response to the voice call
  const response = new VoiceResponse();

  // Prompt the user to leave a message
  response.say('Hello from Cloud Functions. Please leave a message after the beep.');

  console.log('Recording message.');

  // Record the user's message
  response.record({
    // Limit the recording to 60 seconds
    maxLength: 60,
    // Give Twilio the deployed url of the other function for when the recorded
    // audio is available
    recordingStatusCallback: recordingStatusCallbackUrl
  });

  // End the call
  response.hangup();

  // Send the response
  res
    .status(200)
    .type('text/xml')
    .send(response.toString())
    .end();
};
```

### Validating the request

Next, you need to add the helper function that validates requests. Add the
following to your `index.js` file:

[embedmd]:# (index.js /function isValidRequest/ /;\s}/)
```js
function isValidRequest (req, res, pathname) {
  let isValid = true;

  // Only validate that requests came from Twilio when the function has been
  // deployed to production.
  if (process.env.NODE_ENV === 'production') {
    isValid = twilio.validateExpressRequest(req, config.TWILIO_AUTH_TOKEN, {
      url: `https://${region}-${projectId}.cloudfunctions.net/${pathname}`
    });
  }

  // Halt early if the request was not sent from Twilio
  if (!isValid) {
    res
      .type('text/plain')
      .status(403)
      .send('Twilio Request Validation Failed.')
      .end();
  }

  return isValid;
}
```

### Retrieving the recording

Next, you need to retrieve the voice recording from Twilio. You'll add a second
function that will:

1.  Trigger when the audio recording is available for retrieval. Twilio will
    send a webhook request to this function.
1.  Download the audio file from Twilio and save it to Cloud Storage.

Add the following to your `index.js` file:

[embedmd]:# (index.js /exports\.getRecording/ /;\s};/)
```js
exports.getRecording = (req, res) => {
  if (!isValidRequest(req, res, 'getRecording')) {
    return;
  }

  const got = require('got');
  const path = require('path');
  const {Storage} = require('@google-cloud/storage');
  const storage = new Storage();

  const filename = `recordings/${path.parse(req.body.RecordingUrl).name}/audio.wav`;
  const file = storage
    .bucket(config.RESULTS_BUCKET)
    .file(filename);

  console.log(`Saving recording to: ${filename}`);

  got.stream(req.body.RecordingUrl)
    .pipe(file.createWriteStream({
      metadata: {
        contentType: 'audio/x-wav'
      }
    }))
    .on('error', (err) => {
      console.error(err);
      res
        .status(500)
        .send(err)
        .end();
    })
    .on('finish', () => {
      res
        .status(200)
        .end();
    });
};
```

### Analyzing the recording

Finally, you need to transcribe and analyze the voice recording. Now you'll
add a third function that will:

1.  Trigger when the audio recording is saved to Cloud Storage.
1.  Transcribe the audio using the Cloud Speech API.
1.  Analyze the transcription using the Cloud Natural Language API.
1.  Save the analysis to Cloud Storage.

Add the following to your `index.js` file:

[embedmd]:# (index.js /exports\.analyzeRecording/ /;\s};/)
```js
exports.analyzeRecording = (event) => {
  const object = event.data;

  if (object.resourceState === 'not_exists') {
    // Ignore file deletions
    return true;
  } else if (!/^recordings\/\S+\/audio\.wav$/.test(object.name)) {
    // Ignore changes to non-audio files
    return true;
  }

  console.log(`Analyzing gs://${object.bucket}/${object.name}`);

  // Import the Google Cloud client libraries
  const language = require('@google-cloud/language').v1beta2;
  const speech = require('@google-cloud/speech');
  const storage = require('@google-cloud/storage')();

  const nlclient = new language.LanguageServiceClient();
  const spclient = new speech.SpeechClient();
  const bucket = storage.bucket(object.bucket);
  const dir = require('path').parse(object.name).dir;

  // Configure audio settings for Twilio voice recordings
  const audioConfig = {
    sampleRateHertz: 8000,
    encoding: 'LINEAR16',
    languageCode: 'en-US'
  };

  const audioPath = {
    uri: `gs://${object.bucket}/${object.name}`
  };

  const audioRequest = {
    audio: audioPath,
    config: audioConfig,
  };

  // Transcribe the audio file
  return spclient.recognize(audioRequest)
    // Perform Sentiment, Entity, and Syntax analysis on the transcription
    .then(data => { 
      const sresponse = data[0];
      const transcription = sresponse.results
        .map(result => result.alternatives[0].transcript)
        .join('\n');
      return nlclient.analyzeSentiment({document: {content: `${transcription}`, type: 'PLAIN_TEXT'}});
    })
    // Finally, save the analysis
    .then(responses => {
      const filename = `${dir}/analysis.json`;
      console.log(`Saving gs://${object.bucket}/${dir}/${filename}`);
      return bucket
        .file(filename)
        .save(JSON.stringify(responses[0].documentSentiment, null, 1));
      });
};
```

## Deploying and testing the function

1.  Read about [deploying Cloud Functions][deploying].
1.  Run the following to deploy the `handleCall` function:

        gcloud beta functions deploy handleCall --trigger-http --stage-bucket=[YOUR_STAGE_BUCKET] --runtime=nodejs10

    Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

1.  Run the following to deploy the `getRecording` function:

        gcloud beta functions deploy getRecording --trigger-http --stage-bucket=[YOUR_STAGE_BUCKET] --runtime=nodejs10

    Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

1.  Run the following to deploy the `analyzeRecording` function:

        gcloud beta functions deploy analyzeRecording --trigger-bucket=[RESULTS_BUCKET] --stage-bucket=[YOUR_STAGE_BUCKET] --timeout=240 --runtime=nodejs10

    * Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.
    * Replace `[RESULTS_BUCKET]` with the name of the bucket you created in step
      7 of the **Prerequisites** section.
    * Replace `[YOUR_STAGE_BUCKET]` with your Cloud Functions staging bucket.

    Note that you used `--timeout=240` to deploy the `analyzeRecording`
    function. This is because `analyzeRecording` does a lot and may take a
    while, and you don't want the function stopped prematurely.

1.  Call your Twilio phone number and leave a recording.
1.  Open your results bucket in the [Google Cloud Console][browser] to view the
    saved analyses.

To view the logs for the Cloud Functions, run the following:

    gcloud beta functions logs view handleCall
    gcloud beta functions logs view getRecording
    gcloud beta functions logs view analyzeRecording

[browser]: https://console.cloud.google.com/storage/browser
[deploying]: https://cloud.google.com/functions/docs/deploying/filesystem

## Cleaning up

Congratulations, you've now deployed several functions to Google Cloud
Functions, and can receive and analyze phone calls.

You can follow these steps to clean up resources and save on costs.

1.  Delete the functions:

        gcloud beta functions delete -q handleCall
        gcloud beta functions delete -q getRecording
        gcloud beta functions delete -q analyzeRecording

1.  Release your Twilio phone number.
1.  Remove all files in your results bucket:

        gsutil rm -r gs://[RESULTS_BUCKET]/

    * Replace `[RESULTS_BUCKET]` with the name of the bucket you created in step
      6 of the **Prerequisites** section.

Of course, you can also delete the entire project, but you would have to disable billing and lose any
setup you have done. Additionally,
deleting a project will only happen after the current billing cycle ends.

## Next steps

- Learn more about [Twilio and Programmable Voice](https://www.twilio.com/docs/guides/voice).
- View other [Cloud Functions community tutorials](https://cloud.google.com/community/tutorials/search?q=cloud%20functions).
- View other [Twilio community tutorials](https://cloud.google.com/community/tutorials/search?q=twilio).
- View other [Cloud Speech API community tutorials](https://cloud.google.com/community/tutorials/search?q=cloud%20speech%20api).
- View other [Cloud Natural Language API community tutorials](https://cloud.google.com/community/tutorials/search?q=cloud%20natural%20language%20api).
- View other [Node.js community tutorials](https://cloud.google.com/community/tutorials/search?q=node).
