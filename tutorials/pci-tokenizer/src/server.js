/**
Express server wrapper script used for running in containers.

See ../index.md for usage info and Apache 2.0 license
*/
/* jslint node: true */
/* jshint esversion: 8 */
'use strict';

const app = require('./app.js');
const Express = require('express');
const bodyParser = require('body-parser');
const express = Express();
const port = process.env.PORT || 8080; // Port may be set by runtime environment

express.use(bodyParser.json());

express.get('/', (req, res) => {
  res.status(400).send('Invalid request method');
});

express.post('/detokenize', (req, res) => {
  return app.dlp_crypto_detokenize(req, res);
});

express.post('/tokenize', (req, res) => {
  return app.dlp_crypto_tokenize(req, res);
});

express.post('/detokenize/dlp', (req, res) => {
  return app.dlp_crypto_detokenize(req, res);
});

express.post('/tokenize/dlp', (req, res) => {
  return app.dlp_crypto_tokenize(req, res);
});

express.post('/detokenize/kms', (req, res) => {
  return app.kms_crypto_detokenize(req, res);
});

express.post('/tokenize/kms', (req, res) => {
  return app.kms_crypto_tokenize(req, res);
});

express.listen(port, (err) => {
  if (err) {
    return console.log('Express server error', err);
  }

  console.log(`server is listening on ${port}`);
});
