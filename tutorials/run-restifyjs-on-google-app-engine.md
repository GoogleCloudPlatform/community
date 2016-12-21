---
title: Run Restify.js on Google App Engine Flexible Environment
description: Learn how to deploy a Restify.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Restify.js
date_published: 12/15/2015
---
## Restify.js

> [Restify](http://restify.com/) is a Node.js module built specifically to
> enable you to build correct REST web services.
>
> – restify.com

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

Install Restify.js:

    npm install --save restify

## Create

Create a `server.js` file with the following contents:

    var restify = require('restify');

    var server = restify.createServer({
      name: 'appengine-restify',
      version: '1.0.0'
    });

    server.use(restify.acceptParser(server.acceptable));
    server.use(restify.queryParser());
    server.use(restify.bodyParser());

    server.get('/', function (req, res) {
      res.send('Hello World!');
    });

    server.listen(process.env.PORT || 8080, function () {
      console.log('%s listening at %s', server.name, server.url);
    });

## Run

Run the app with the following command:

    node server.js

Go to `http://localhost:8080` to see the `Hello World!` message.

## Deploy

Create an `app.yaml` file with the following contents:

    runtime: nodejs
    vm: true

The `app.yaml` makes the app deployable to Google App Engine Managed VMs.

Run the following command to deploy your app:

    gcloud preview app deploy app.yaml

Go to `http://<your-project-id>.appspot.com` to see the `Hello World!` message.

[nodejs-gcp]: running-nodejs-on-google-cloud
