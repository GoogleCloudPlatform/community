---
title: Run Express.js on Google Cloud Platform
author: jmdobry
tags: App Engine, Node.js, Express.js
date_published: 01/07/2016
---
## Express.js

> [Express](http://expressjs.com) is a minimal and flexible Node.js web
> application framework that provides a robust set of features for web and
> mobile applications.
>
> – expressjs.com

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

    var express = require('express');
    var app = express();

    app.get('/', function (req, res) {
      res.send('Hello World!');
    });

    var server = app.listen(8080, function () {
      var host = server.address().address;
      var port = server.address().port;

      console.log('Example app listening at http://%s:%s', host, port);
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

    gcloud preview app deploy app.yaml --promote

Go to `http://<your-project-id>.appspot.com` to see the `Hello World!` message.
