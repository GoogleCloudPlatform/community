---
title: Run a Loopback Node.js on Google App Engine Flexible Environment
description: Learn how to run a Loopback Node.js app on Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Loopback
date_published: 2017-11-02
---
## Loopback

> [LoopBack][loopback] is a highly-extensible, open-source Node.js framework
> that enables you to create dynamic end-to-end REST APIs with little or no
> coding.
>
> – loopback.io

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](/sdk/).
1. [Prepare your environment for Node.js development][nodejs]

## Prepare the app

1. Install the Loopback CLI:

        npm install -g loopback-cli

1.  Follow the [Loopback Getting Started guide](https://loopback.io/doc/en/lb3/Getting-started-with-LoopBack.html)
    to create a Loopback app.

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
