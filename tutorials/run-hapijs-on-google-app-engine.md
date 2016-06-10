---
title: Run Hapi.js on Google App Engine
description: Learn how to deploy a Hapi.js app to App Engine Flexible Environment
author: jmdobry
tags: App Engine, Hapi.js, Node.js
date_published: 12/17/2015
---
## Hapi.js

> [Hapi](http://hapijs.com/) is a rich framework for building applications and
> services. Hapi enables developers to focus on writing reusable application
> logic instead of spending time building infrastructure.
>
> – hapijs.com

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enabled billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Initialize a `package.json` file with the following command:

    npm init

Install Hapi.js:

    npm install --save hapi

## Create

Create a `server.js` file with the following contents:

    var Hapi = require('hapi');

    // Create a server with a host and port
    var server = new Hapi.Server();
    server.connection({
      host: '0.0.0.0',
      port: process.env.PORT || 8080
    });

    server.route({
      method: 'GET',
      path:'/',
      handler: function (request, reply) {
        reply('Hello World!');
      }
    });

    server.start(function () {
      console.log('Server running at:', server.info.uri);
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