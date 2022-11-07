---
title: Run a LoopBack Node.js app on App Engine flexible environment
description: Learn how to run a LoopBack Node.js app on App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Loopback
date_published: 2017-11-02
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](/sdk/).
1. [Prepare your environment for Node.js development][nodejs]

## Prepare the app

1. Install the LoopBack command-line interface:

        npm install -g loopback-cli

1.  Follow the [LoopBack Getting Started guide](https://loopback.io/doc/en/lb3/Getting-started-with-LoopBack.html)
    to create a LoopBack app.

## Deploy the app

1.  Create an `app.yaml` file with the following content:

    ```yaml
    runtime: nodejs
    env: flex
    ```

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  View the deployed app:

        gcloud app browse

[loopback]: https://loopback.io
[nodejs-gcp]: running-nodejs-on-google-cloud
[nodejs]: /nodejs/docs/setup
