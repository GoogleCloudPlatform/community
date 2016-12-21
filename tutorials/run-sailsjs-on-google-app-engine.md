---
title: Run Sails.js on Google App Engine Flexible Environment
description: Learn how to deploy a Sails.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Sails.js
date_published: 05/20/2016
---
## Sails.js

> [Sails](http://sailsjs.org/) makes it easy to build custom, enterprise-grade
> Node.js apps.
>
> – sailsjs.org

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enabled billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Install the Sails.js CLI tool:

    npm install -g sails

Create a new Sails.js project (this may take a moment):

    sails new testProject

Change directory into the new project:

    cd testProject

## Run

Run the app with the following command:

    sails lift

Visit [http://localhost:1337](http://localhost:1337) to see the new project's
home page.

## Deploy

Run the following command to deploy your app:

    gcloud app deploy

Visit `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

Note: When the the Sails.js app is deployed it will automatically switch to
production mode and listen on the correct port.

[nodejs-gcp]: running-nodejs-on-google-cloud
