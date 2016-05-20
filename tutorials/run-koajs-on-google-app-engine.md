---
title: Run Koa.js on Google App Engine
author: jmdobry
tags: App Engine, Node.js, Koa.js
date_published: 12/16/2015
---
## Koa.js

> [koa](http://koajs.com) is a next generation web framework for Node.js.
>
> – koajs.com

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enabled billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Initialize a `package.json` file with the following command:

    npm init

Install Koa.js:

    npm install --save koa

## Create

Create a `server.js` file with the following contents:

    var koa = require('koa');
    var app = koa();

    app.use(function *(){
      this.body = 'Hello World!';
    });

    app.listen(process.env.PORT || 8080);

## Run

Run the app with the following command:

    node --harmony server.js

Go to `http://localhost:8080` to see the `Hello World!` message.

Update `package.json` so App Engine can run the app:

    "scripts": {
      "start": "node --harmony server.js"
    }

## Deploy

Create an `app.yaml` file with the following contents:

    runtime: nodejs
    vm: true

The `app.yaml` makes the app deployable to Google App Engine Managed VMs.

Run the following command to deploy your app:

    gcloud preview app deploy app.yaml

Go to `http://<your-project-id>.appspot.com` to see the `Hello World!` message.