---
title: Run Express.js on Google App Engine Flexible Environment
description: Learn how to deploy a Express.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Express.js, Node.js
date_published: 01/07/2016
---
## Express.js

> [Express](http://expressjs.com) is a minimal and flexible Node.js web
> application framework that provides a robust set of features for web and
> mobile applications.
>
> – expressjs.com

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enabled billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Initialize a `package.json` file with the following command:

    npm init

Install Express.js:

    npm install --save express

## Create

Create a `server.js` file with the following contents:

    const express = require('express');
    const app = express();

    app.get('/', (req, res) => {
      res.send('Hello World!');
    });

    const server = app.listen(8080, () => {
      const host = server.address().address;
      const port = server.address().port;

      console.log(`Example app listening at http://${host}:${port}`);
    });

## Run

Run the app with the following command:

    npm start

Visit [http://localhost:8080](http://localhost:8080) to see the `Hello World!`
message.

## Deploy

Create an `app.yaml` file with the following contents:

    runtime: nodejs
    env: flex

The `app.yaml` makes the app deployable to Google App Engine Managed VMs.

Run the following command to deploy your app:

    gcloud app deploy

Visit `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

[nodejs-gcp]: running-nodejs-on-google-cloud
