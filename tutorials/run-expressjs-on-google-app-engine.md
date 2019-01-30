---
title: Run Express.js on Google App Engine Flexible Environment
description: Learn how to deploy a Express.js app to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Express.js, Node.js
date_published: 2016-01-07
---
## Express.js

> [Express][express] is a minimal and flexible Node.js web
> application framework that provides a robust set of features for web and
> mobile applications.
>
> – expressjs.com

You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).
1. Install [Node.js](https://nodejs.org/en/download/) on your local machine. 

## Prepare

1. Initialize a `package.json` file with the following command:

        npm init
        
1. Add a start script to your `package.json` file:

    ```json
    "scripts": {
        "start": "node index.js"
    }
    ```

1. Install Express.js:

        npm install --save express

## Create

Create an `index.js` file with the following contents:

```js
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello World!');
});

const server = app.listen(8080, () => {
  const host = server.address().address;
  const port = server.address().port;

  console.log(`Example app listening at http://${host}:${port}`);
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

[express]: http://expressjs.com
[nodejs-gcp]: running-nodejs-on-google-cloud
