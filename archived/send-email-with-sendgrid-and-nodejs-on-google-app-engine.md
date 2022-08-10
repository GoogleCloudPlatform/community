---
title: Send email with SendGrid and Node.js on App Engine flexible environment
description: Learn how to send email with SendGrid from a Node.js app to App Engine flexible environment.
author: jmdobry
tags: App Engine, SendGrid, Express.js, Node.js
date_published: 2016-12-13
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Sign up for a [SendGrid account](https://sendgrid.com/pricing/).

1. Create a new [API key](https://app.sendgrid.com/settings/api_keys).

1. Initialize a `package.json` file with the following command:

        npm init

1. Install some dependencies:

        npm install --save express body-parser pug sendgrid

## Create

1.  Create a `server.js` file with the following contents:

        'use strict';

        const express = require('express');
        const path = require('path');
        const bodyParser = require('body-parser');

        const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;
        const SENDGRID_SENDER = process.env.SENDGRID_SENDER;
        const Sendgrid = require('sendgrid')(SENDGRID_API_KEY);

        const app = express();

        // Setup view engine
        app.set('views', path.join(__dirname, 'views'));
        app.set('view engine', 'pug');

        // Parse form data
        app.use(bodyParser.json());
        app.use(bodyParser.urlencoded({ extended: false }));

        app.get('/', (req, res) => res.render('index'));

        app.post('/hello', (req, res, next) => {
          const sgReq = Sendgrid.emptyRequest({
            method: 'POST',
            path: '/v3/mail/send',
            body: {
              personalizations: [{
                to: [{ email: req.body.email }],
                subject: 'Hello World!'
              }],
              from: { email: SENDGRID_SENDER },
              content: [{
                type: 'text/plain',
                value: 'SendGrid on App Engine with Node.js.'
              }]
            }
          });

          Sendgrid.API(sgReq, (err) => {
            if (err) {
              next(err);
              return;
            }
            // Render the index route on success
            res.render('index', {
              sent: true
            });
            return;
          });
        });

        app.listen(process.env.PORT || 8080);

1.  Create a directory named `views`:

        mkdir views

1.  Create a file named `index.pug` inside the `views` directory with the following contents:

        doctype html
        html
          head
            title= title
          body
            h1 Hello World!
            p Express.js + SendGrid on App Engine.
            hr
            if sent
              p Email sent!
            else
              form(name="hello", action="/hello", method="post")
                input(type="email", placeholder="Enter your email to send yourself a Hello World message", name="email", style="width: 50%; margin-right: 15px;")
                input(type="submit", value="Send")

## Run

1.  Run the app with the following command:

        SENDGRID_SENDER=your-sendgrid-sender-email SENDGRID_API_KEY=your-sendgrid-api-key npm start

1. Visit [http://localhost:8080](http://localhost:8080) to try sending an email.

## Deploy

1.  Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex
        env_variables:
          SENDGRID_SENDER: your-sendgrid-sender-email
          SENDGRID_API_KEY: your-sendgrid-api-key

    The `app.yaml` makes the app deployable to App Engine managed VMs.

1.  Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to try sending an email.

[sendgrid]: https://sendgrid.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
