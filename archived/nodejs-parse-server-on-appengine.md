---
title: Run Node.js Parse server on App Engine flexible environment
description: Learn how to run a Node.js Parse server on the App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Parse-server
date_published: 2017-11-02
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Tutorial for deploying a [Parse Server](https://github.com/ParsePlatform/parse-server/wiki/Parse-Server-Guide)
to the App Engine flexible environment.

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](/sdk/).
1. [Prepare your environment for Node.js development][nodejs]

### Create a MongoDB database

There are multiple options for creating a new MongoDB database. For example:

- Create a Compute Engine virtual machine with [MongoDB pre-installed](/launcher/?q=mongodb).
- Use [mLab](https://mlab.com/google/) to create a free MongoDB deployment on Google Cloud.

## Download and run the app

1.  Clone the [parse-server example app](https://github.com/parse-community/parse-server-example) and change directory to it:

        git clone https://github.com/parse-community/parse-server-example.git
        cd parse-server-example

1.  Install dependencies:

        npm install

1.  Run the app locally:

        APP_ID=your-app-id DATABASE_URL=your-mongodb-uri MASTER_KEY=your-master-key npm start

## Deploy the app

1.  Make sure your `app.yaml` file looks something like this (update the
    variables with your own values):

        runtime: nodejs
        env: flex

        env_variables:
          # --REQUIRED--
          DATABASE_URI: mongodb://localhost:27017/dev
          APP_ID: YOUR_APP_ID
          MASTER_KEY: YOUR_MASTER_KEY
          SERVER_URL: https://YOUR_PROJECT_ID.appspot.com/parse
          # --OPTIONAL--
          # FILE_KEY: YOUR_FILE_KEY
          # PARSE_MOUNT: /parse
          # CLOUD_CODE_MAIN:

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  View the deployed app:

        gcloud app browse

[nodejs-gcp]: running-nodejs-on-google-cloud
[nodejs]: /nodejs/docs/setup
