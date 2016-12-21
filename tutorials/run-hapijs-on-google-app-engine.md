---
title: Run Hapi.js on Google App Engine Flexible Environment
description: Learn how to deploy a Hapi.js app to Google App Engine flexible environment
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

Install Hapi.js:

    npm install --save hapi

## Create

Create a `server.js` file with the following contents:

    const Hapi = require('hapi');

    // Create a server with a host and port
    const server = new Hapi.Server();
    server.connection({
      host: '0.0.0.0',
      port: process.env.PORT || 8080
    });

    server.route({
      method: 'GET',
      path:'/',
      handler: (request, reply) => {
        reply('Hello World!');
      }
    });

    server.start(() => {
      console.log('Server running at:', server.info.uri);
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
