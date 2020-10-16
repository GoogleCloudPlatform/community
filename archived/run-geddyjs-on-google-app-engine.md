---
title: Run Geddy.js on Google App Engine flexible environment
description: Learn how to deploy a Sails.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Geddy.js, Sails.js
date_published: 2017-01-10
---

## Geddy.js

[Geddy][geddy] is a simple, structured web framework for Node.js

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Install the Geddy.js CLI tool:

        npm install -g geddy

1. Create a new Geddy.js project (this may take a moment):

        geddy gen app testProject

1. Change directory into the new project:

        cd testProject

## Run

1. Run the app with the following command:

        geddy

1. Visit [http://localhost:4000](http://localhost:4000) to see the new project's
home page.

## Deploy

By default the Geddy.js app will listen on port 4000 in production mode, so it
must be updated to listen on the port specified by the `PORT` environment
variable available in the Google App Engine environment.

1. Open `config/production.js` and change `port: 4000` to `port: process.env.PORT || 4000`.

1. Now run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the deployed app.

Note: When the the Geddy.js app is deployed it will automatically switch to
production mode and listen on the correct port.

[geddy]: http://geddyjs.org/
[nodejs-gcp]: running-nodejs-on-google-cloud
