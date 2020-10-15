---
title: Run Koa.js on App Engine flexible environment
description: Learn how to deploy a Koa.js app to App Engine flexible environment.
author: jmdobry
tags: App Engine, Koa.js, Node.js
date_published: 2015-12-16
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Initialize a `package.json` file with the following command:

        npm init

1. Install Koa.js:

        npm install --save koa

## Create

Create a `server.js` file with the following contents:

```js
const Koa = require('koa');
const app = new Koa();

app.use((ctx) => {
  ctx.body = 'Hello World!';
});

app.listen(process.env.PORT || 8080);
```

## Run

1. Run the app with the following command:

        npm start

1. Visit [http://localhost:8080](http://localhost:8080) to see the `Hello World!`
message.

## Deploy

1. Create an `app.yaml` file with the following contents:

    ```yaml
    runtime: nodejs
    env: flex
    ```

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

[koa]: http://koajs.com
[nodejs-gcp]: running-nodejs-on-google-cloud
