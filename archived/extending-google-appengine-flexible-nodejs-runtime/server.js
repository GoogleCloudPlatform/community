'use strict';

const exec = require('child_process').exec;
const express = require('express');

const app = express();

app.get('/', (req, res, next) => {
  // Get the output from the "fortune" program. This is installed into the
  // environment by the Dockerfile.
  exec('/usr/games/fortune', (err, stdout) => {
    if (err) {
      next(err);
      return;
    }

    res.set('Content-Type', 'text/plain');
    res.status(200).send(stdout);
  });
});

if (module === require.main) {
  const PORT = process.env.PORT || 8080;
  app.listen(PORT, () => {
    console.log(`App listening on port ${PORT}`);
    console.log('Press Ctrl+C to quit.');
  });
}

module.exports = app;
