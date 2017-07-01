/* jslint es6 */
/* jslint white:true */

'use strict';

// We use the https library to confirm the SNS subscription
const https = require('https');

// import the Google Cloud Pubsub client library
const PubSub = require('@google-cloud/pubsub');

// the sns-validator package verifies the host an signature of SNS messages
var MessageValidator = require('sns-validator');
var validator = new MessageValidator();

// our pubsub client
const pubsub = PubSub();

// the cloud pubsub topic we will publish messages to
const topicName = 'sns-events';
const topic = pubsub.topic(topicName);

const expectedTopicArn = 'arn:aws:sns:us-west-2:681196457733:new-demo';

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
  }

  // all valid SNS requests should have this header
  var snsHeader = req.get('x-amz-sns-message-type');
  if (snsHeader === undefined) {
    res.status(403).end('invalid SNS message');
  }

  // use the sns-validator library to verify signature
  // we first parse the cloud function body into a javascript object
  validator.validate(JSON.parse(req.body), function (err, message) {
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
    var options;
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
            return;
          });
        }).on('error', (e) => {
          console.error(e);
          res.status(500).end('confirmation failed');
          return;
        });
        break;
      case 'notification':
        // this is a regular SNS notice, we relay to Pubsub
        console.log(message.MessageId + ': ' + message.Message);
        message = {
          data: message.Message,
          attributes: {
            snsMessageId: message.MessageId,
            snsSubject: message.Subject
          }
        };

        options = {
          raw: true
        };

        topic.publish(message, options).then(function (data) {
          console.log('message published ' + data[0]);
          // var messageIds = data[0];
          // var apiResponse = data[1];
        });
        res.status(200).end('ok');
        return;
      default:
        console.error('should not have gotten to default block');
        res.status(400).end('invalid SNS message');
    }
  });
};
