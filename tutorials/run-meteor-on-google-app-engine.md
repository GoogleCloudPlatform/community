---
title: Run Meteor on Google Cloud Platform
description: Learn how to deploy a Meteor app to App Engine
author: anassri
tags: App Engine, Meteor, Node.js
date_published: 10/10/2016
---
## Meteor

> [Meteor](https://meteor.com) is an open source platform for web, mobile, and desktop.
>
> – meteor.com

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare
[Install Meteor](https://meteor.com/install).

## Creation

### Initialize a Meteor project
Initialize a Meteor project by `cd`ing to the target folder and running the following command:

    meteor create [YOUR_APP_NAME]

Replace `[YOUR_APP_NAME]` with your app name.

## Running

Run the Meteor project by `cd`ing into the project's directory and running the command below:

    cd [YOUR_APP_NAME]
    meteor

Go to your Meteor app's location (`http://localhost:3000` by default) to see the `Welcome to Meteor!` message.

When you're done, use CTRL-C to exit Meteor.

## Deployment

### Initialize a Mongo instance
Create a Mongo instance as described [here](/nodejs/getting-started/deploy-mongodb). Remember your `MONGO_URL` - you'll need that during the deployment process.

### Configure
Create an `app.yaml` file with the following contents:

    runtime: custom
    vm: true
    env_variables:
        MONGO_URL: [MONGO_URL]

Replace `[MONGO_URL]` with a valid Mongo URL as described in [this tutorial](/nodejs/getting-started/deploy-mongodb).

Then, configure a [custom runtime](/appengine/docs/flexible/custom-runtimes/), by creating a `Dockerfile` as follows:

    # Extending the generic Node.js image
    FROM gcr.io/google_appengine/nodejs
    COPY . /app/

    # Install Meteor
    RUN curl "https://install.meteor.com" | sh

    # Install dependencies
    RUN npm install --unsafe-perm


The `app.yaml` makes the app deployable to Google App Engine Managed VMs.

### Deploy
Run the following command to deploy your app:

    gcloud app deploy app.yaml --promote

Go to `http://<your-project-id>.appspot.com` to see the `Welcome to Meteor!` message.
