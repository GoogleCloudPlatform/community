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
