---
title: Send email with Mailgun and Node.js on App Engine flexible environment
description: Learn how to send email with Mailgun from a Node.js app to App Engine flexible environment.
author: jmdobry
tags: App Engine, Mailgun, Express.js, Node.js
date_published: 2017-01-10
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

You can check out [Node.js and Google Cloud][nodejs-gcp] to get an
overview of Node.js itself and learn ways to run Node.js apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

1. Sign up for a [Mailgun account](https://mailgun.com/signup).

1. Add a [new domain](https://documentation.mailgun.com/en/latest/user_manual.html). Find your API key in your new domain's settings.

1. Initialize a `package.json` file with the following command:

        npm init

1. Install some dependencies:

        npm install --save express body-parser pug mailgun

## Create

1.  Create a `server.js` file with the following contents:

        'use strict';

        const express = require('express');
        const path = require('path');
        const bodyParser = require('body-parser');

        const Mailgun = require('mailgun').Mailgun;
        const mg = new Mailgun(process.env.MAILGUN_API_KEY);

        const app = express();

        // Setup view engine
        app.set('views', path.join(__dirname, 'views'));
        app.set('view engine', 'pug');

        // Parse form data
        app.use(bodyParser.json());
        app.use(bodyParser.urlencoded({ extended: false }));

        app.get('/', (req, res) => res.render('index'));

        app.post('/hello', (req, res, next) => {
          const servername = '';
          const options = {};

          mg.sendText(
            // From
            'no-reply@appengine-mailgun-demo.com',
            // To
            req.body.email,
            // Subject
            'Hello World!',
            // Body
            'Mailgun on App Engine with Node.js',
            servername,
            options,
            (err) => {
              if (err) {
                next(err);
                return;
              }
              // Render the index route on success
              res.render('index', {
                sent: true
              });
            }
          );
        });

        app.listen(process.env.PORT || 8080);

1.  Create a directory named `views`:

        mkdir views

1.  Create a file named `index.pug` inside the `views` directory with
    the following contents:

        doctype html
        html
          head
            title= title
          body
            h1 Hello World!
            p Express.js + Mailgun on App Engine.
            hr
            if sent
              p Email sent!
            else
              form(name="hello", action="/hello", method="post")
                input(type="email", placeholder="Enter your email to send yourself a Hello World message", name="email", style="width: 50%; margin-right: 15px;")
                input(type="submit", value="Send")

## Run

1.  Run the app with the following command:

        MAILGUN_API_KEY=your-mailgun-api-key npm start

1.  Visit [http://localhost:8080](http://localhost:8080) to try sending an email.

## Deploy

1.  Create an `app.yaml` file with the following contents:

        runtime: nodejs
        env: flex
        env_variables:
          MAILGUN_API_KEY: your-mailgun-api-key

    The `app.yaml` makes the app deployable to Google App Engine Managed VMs.

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to try sending an email.

[mailgun]: https://www.mailgun.com/
[nodejs-gcp]: running-nodejs-on-google-cloud
