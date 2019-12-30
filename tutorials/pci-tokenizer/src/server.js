/**
* Express server wrapper script used for running in Docker.
* This file is not used with Cloud Functions.
*
* See ../README.md for license and more info
*/

'use strict';
const app = require('./app.js');
const Express = require('express');
const bodyParser = require('body-parser');
const express = Express();
const port = process.env.PORT || 8080;

express.use(bodyParser.json());

express.get('/', (req, res) => {
  res.status(400).send('Invalid request format');
});

express.post('/detokenize', (req, res) => {
  return app.dlp_crypto_detokenize(req, res);
});

express.post('/tokenize', (req, res) => {
  return app.dlp_crypto_tokenize(req, res);
});

express.listen(port, (err) => {
  if (err) {
    return console.log('Express server error', err);
  }

  console.log(`server is listening on ${port}`);
});
