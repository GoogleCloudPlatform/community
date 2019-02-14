---
title: Extending the Node.js runtime of App Engine flexible environment
description: Learn how to extend the Node.js runtime of the App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Docker
date_published: 2017-01-23
---

This tutorial shows how to extend the Node.js runtime of the App Engine
flexible environment.

You will create a small Node.js web application that requires customizations to
the default Node.js runtime of the [App Engine flexible environment][flex].

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Initialize a `package.json` file with the following command:

        npm init

1. Install Express.js:

        npm install --save express

1. Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex

## Creating the app

1.  Create a file named `server.js` with the following contents:

    [embedmd]:# (server.js)

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

Notice how the app shells out to `/usr/games/fortune` in order to respond to the
request. The `fortune` binary is not available in the default Node.js runtime,
so you need to extend the runtime in order to make the binary available to your
app after it's deployed.

## Extending the runtime

1.  Run the following command to extend the runtime:

        gcloud beta app gen-config --custom

    This will generate `Dockerfile` and `.dockerignore` files, and modify the
    `app.yaml` file to include `runtime: custom` instead of `runtime: nodejs`.

1.  Modify the generated `Dockerfile` to look like the following:

        # Dockerfile extending the generic Node image with application files for a
        # single application.
        FROM gcr.io/google_appengine/nodejs

        # Install the fortunes game
        RUN apt-get update && apt-get install -y fortunes

        # Check to see if the the version included in the base runtime satisfies
        # '>=6.9.0', if not then do an npm install of the latest available
        # version that satisfies it.
        RUN /usr/local/bin/install_node '>=6.9.0'

        # Copy application code.
        COPY . /app/

        # You have to specify "--unsafe-perm" with npm install
        # when running as root.  Failing to do this can cause
        # install to appear to succeed even if a preinstall
        # script fails, and may have other adverse consequences
        # as well.
        # This command will also cat the npm-debug.log file after the
        # build, if it exists.
        RUN npm install --unsafe-perm || \
          ((if [ -f npm-debug.log ]; then \
              cat npm-debug.log; \
            fi) && false)

        # Run the app, default is "npm start"
        CMD npm start

    When the app is deployed, the image will be built using the custom
    `Dockerfile`.

You can view the source code and its tests [here](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/extending-google-appengine-flexible-nodejs-runtime);

## Deploying the app

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the app.

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js and learn ways to run Node.js apps on Google Cloud Platform.

[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
[nodejs-gcp]: running-nodejs-on-google-cloud
