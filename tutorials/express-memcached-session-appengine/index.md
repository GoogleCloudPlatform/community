---
title: Use Memcache for sessions with Express.js on App Engine flexible environment
description: Learn how to deploy an Express.js app to App Engine flexible environment that uses Memcache for user sessions.
author: jmdobry
tags: App Engine, Express.js, Node.js, Memcache
date_published: 2017-02-08
---

This tutorial shows a sample Node.js app built with Express.js that uses
Memcache for user sessions. The end of the tutorial shows deploying the app to
App Engine flexible environment.

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/).
1.  If you do not have a Memcached instance already, get a free one from
    [Redis Labs][redis].

## Preparing the app

1.  Download the sample [`server.js`][server] file.
1.  Create a `package.json` file with NPM or Yarn:

        npm init

    or

        yarn init

1.  Install dependencies with NPM or Yarn:

        npm install --save connect-memjs cookie-parser express express-session public-ip

    or

        yarn add connect-memjs cookie-parser express express-session public-ip

## Running the app

1.  Start the app with NPM or Yarn:

        MEMCACHE_URL=YOUR_MEMCACHE_URL npm start

    or

        MEMCACHE_URL=YOUR_MEMCACHE_URL yarn start

    replacing `YOUR_MEMCACHE_URL` with your Memcache URL, e.g. `"http://example.com:11211"`.

    Optionally set the `MEMCACHE_USERNAME` and `MEMCACHE_PASSWORD` environment
    variables as well.

1.  Visit [http://localhost:8080](http://localhost:8080) to see the app.

## Deploying the app

1.  Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex

        env_variables:
          # If you are using the App Engine Memcache service (currently in alpha),
          # uncomment this section and comment out the other Memcache variables.
          # USE_GAE_MEMCACHE: 1

          MEMCACHE_URL: your-memcache-url
          # If you are using a Memcached server with SASL authentication enabled,
          # fill in these values with your username and password.
          MEMCACHE_USERNAME: your-memcache-username
          MEMCACHE_PASSWORD: your-memcache-password

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the deployed app.

[express]: http://expressjs.com
[nodejs-gcp]: running-nodejs-on-google-cloud
[redis]: https://redislabs.com/
[server]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/express-memcached-session-appengine/server.js
