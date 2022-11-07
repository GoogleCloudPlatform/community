---
title: Run Hapi.js on App Engine flexible environment
description: Learn how to deploy a Hapi.js app to App Engine flexible environment.
author: jmdobry
tags: App Engine, Hapi.js, Node.js
date_published: 2015-12-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Initialize a `package.json` file with the following command:

        npm init

1. Install Hapi.js:

        npm install --save @hapi/hapi

## Create

Create a `server.js` file with the following contents:

        "use strict";

        const Hapi = require("@hapi/hapi");

        const init = async () => {
          const server = Hapi.server({
            port: process.env.PORT || 8080,
            host: "0.0.0.0"
          });

          server.route({
            method: "GET",
            path: "/",
            handler: (request, h) => {
              return "Hello World!";
            }
          });

          await server.start();
          console.log("Server running on %s", server.info.uri);
        };

        process.on("unhandledRejection", err => {
          console.log(err);
          process.exit(1);
        });

        init();


## Run

1.  Run the app with the following command:

        npm start

1.  Visit [http://localhost:8080](http://localhost:8080) to see the `Hello World!` message.

## Deploy

1.  Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex

1.  Deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

[hapi]: http://hapijs.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
