---
title: Run Restify.js on Google App Engine Flexible Environment
description: Learn how to deploy a Restify.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Node.js, Restify.js
date_published: 2015-12-15
---
## Restify.js

> [Restify][restify] is a Node.js module built specifically to
> enable you to build correct REST web services.
>
> – restify.com

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Initialize a `package.json` file with the following command:

        npm init

1. Install Restify.js:

        npm install --save restify

## Create

Create a `server.js` file with the following contents:

```js
 const restify = require('restify');

 const server = restify.createServer({
   name: 'appengine-restify',
   version: '1.0.0'
 });

 server.use(restify.acceptParser(server.acceptable));
 server.use(restify.queryParser());
 server.use(restify.bodyParser());

 server.get('/', (req, res) => {
   res.send('Hello World!');
 });

 server.listen(process.env.PORT || 8080, () => {
   console.log(`${server.name} listening at ${server.url}`);
 });
 ```

## Run

1. Run the app with the following command:

        node server.js

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

1. Go to `http://YOUR_PROJECT_ID.appspot.com` to see the `Hello World!` message.

[restify]: http://restify.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
