---
title: Run Kraken.js on Google App Engine Flexible Environment
description: Learn how to deploy a Kraken.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine Flexible, Kraken.js, Node.js
date_published: 01/10/2017
---
## Kraken.js

> [Kraken][kraken] is a secure and scalable layer that extends Express.js by
> providing structure and convention.
>
> – krakenjs.com

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Install the Kraken.js CLI and supporting tools:

        npm install -g yo generator-kraken bower grunt-cli

1. Create a new Kraken.js project (this may take a moment):

        yo kraken

1. Change directory into the new project:

        cd testProject

## Run

1. Run the app with the following command:

        npm start

1. Visit [http://localhost:8000](http://localhost:8000) to see the new project's
home page.

## Deploy

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

Note: When the the Kraken.js app is deployed it will automatically switch to
production mode and listen on the correct port.

[kraken]: http://krakenjs.com
[nodejs-gcp]: running-nodejs-on-google-cloud
