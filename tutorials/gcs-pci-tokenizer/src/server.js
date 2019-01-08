/**
* github ianmaddox/gcs-cf-tokenizer
* Express server wrapper script used for Docker style running.
* This file is not used with Cloud Functions.
*
* See ../README.md for license and more info
*/

'use strict';
const app = require('/tokenizer/index.js');
const Express = require('express');
const bodyParser = require('body-parser');
const express = Express();
const port = 80;

express.use(bodyParser.json());

express.get('/', (req, res) => {
  app.tokenize(req, res);
  res.send('OK');
});

express.post('/detokenize', (req, res) => {
  return app.detokenize(req, res);
});

express.post('/tokenize', (req, res) => {
  return app.tokenize(req, res);
});

express.listen(port, (err) => {
  if (err) {
    return console.log('Express server error', err);
  }

  console.log(`server is listening on ${port}`);
});
