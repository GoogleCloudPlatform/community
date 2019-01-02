---
title: Run Hapi.js on Google App Engine Flexible Environment
description: Learn how to deploy a Hapi.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Hapi.js, Node.js
date_published: 2015-12-17
---
## Hapi.js

> [Hapi][hapi] is a rich framework for building applications and
> services. Hapi enables developers to focus on writing reusable application
> logic instead of spending time building infrastructure.
>
> – hapijs.com

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

1. Install Hapi.js:

        npm install --save hapi

## Create

Create a `server.js` file with the following contents:

```js
 const Hapi = require('hapi');

 // Create a server with a host and port
 const server = new Hapi.Server();
 server.connection({
   host: '0.0.0.0',
   port: process.env.PORT || 8080
 });

 server.route({
   method: 'GET',
   path:'/',
   handler: (request, reply) => {
     reply('Hello World!');
   }
 });

 server.start(() => {
   console.log('Server running at:', server.info.uri);
 });
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

[hapi]: http://hapijs.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
