---
title: Send email with SparkPost and Node.js on App Engine flexible environment
description: Learn how to send email with SparkPost from a Node.js app to App Engine flexible environment.
author: ewandennis
tags: App Engine, SparkPost, Express.js, Node.js
date_published: 2017-03-22
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
    Remember to take note of your project ID; you'll need it later to access your app at http://YOUR_PROJECT_ID.appspot.com
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Sign up for a [SparkPost account](https://app.sparkpost.com/sign-up).

1. [Create an API key](https://app.sparkpost.com/account/credentials) with the "Transmissions: Read/Write" privilege.

1. Initialize a `package.json` file with the following command:

        npm init

1. Install some dependencies, including the [SparkPost Node.js client](https://github.com/sparkpost/node-sparkpost):

        npm install --save express body-parser pug sparkpost

## Create

1.  Create a `server.js` file with the following contents:

        'use strict';

        const http = require('http');
        const express = require('express');
        const path = require('path');
        const bodyParser = require('body-parser');

        const SparkPost = require('sparkpost');
        const spClient = new SparkPost(process.env.SPARKPOST_API_KEY);

        const app = express();
        const srv = http.Server(app);

        // Setup view engine
        app.set('views', path.join(__dirname, 'views'));
        app.set('view engine', 'pug');

        // Parse form data
        app.use(bodyParser.json());
        app.use(bodyParser.urlencoded({ extended: false }));

        app.get('/', (req, res) => res.render('index'));

        app.post('/hello', (req, res, next) => {
          spClient.transmissions.send({
            options: { sandbox: true },
            content: {
              from: 'appengine-node-demo@sparkpostbox.com',
              subject: 'Hello from Google AppEngine!',
              text: 'Google AppEngine + Node.js + SparkPost = awesome!'
            },
            recipients: [
              {address: req.body.email} 
            ]
          }).then(result => {
            res.render('index', {sent: true});
          }).catch(err => {
            res.render('index', {err: err});
            console.error(err);
          });
        });

        srv.listen(process.env.PORT || 8080, () => {
          console.log(`Listening on ${srv.address().port}`);
        });

1. Create a directory named `views`:

        mkdir views

1. Create a file named `index.pug` inside the `views` directory with the
following contents:

        doctype html
        html    
          head
            title= title
          body
            h1 hello world!
            p express.js + sparkpost on google app engine.
            hr
            if sent
              p email sent!
            if err
              p Oh my. Something's not right:
                ul
                  each e in err.errors
                    li
                      strong=e.message+': '
                      |#{e.description}
            else
              form(name="hello", action="/hello", method="post")
                input(type="email", placeholder="enter your email to send yourself a hello world message", name="email", style="width: 50%; margin-right: 15px;")
                input(type="submit", value="send")

## Run

1. Run the app with the following command:

        SPARKPOST_API_KEY=your-sparkpost-api-key npm start

1. Visit [http://localhost:8080](http://localhost:8080) to try sending an email.

## Deploy

1.  Create a file named `app.yaml` with the following contents:

        runtime: nodejs
        env: flex
        env_variables:
          SPARKPOST_API_KEY: your-sparkpost-api-key

    `app.yaml` describes how to deploy your app to App Engine. Read more about that [here](https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml).

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to try sending email. `YOUR_PROJECT_ID` is the project ID you created earlier in the
    [Cloud Console](https://console.cloud.google.com/).

[sparkpost]: https://www.sparkpost.com/
[nodejs-gcp]: https://cloud.google.com/nodejs/
