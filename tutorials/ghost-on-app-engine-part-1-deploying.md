---
title: Ghost on App Engine Part 1 - Deploying
author: jmdobry
tags: App Engine, Ghost
date_published: 05/26/2016
---
This tutorial explains how to deploy and scale a [Ghost blog][ghost] on [Google App Engine Flexible Environment][flex].

Ghost is a simple blogging platform that can be self hosted. It's built with Node.js, and can be customized or transformed into a bigger site. It serves as a template for a larger application.

Google App Engine makes it easy to run web applications that must scale to meet worldwide demand. It lets you focus on your code without having to worry about operations, load balancing, servers, or scaling to satisfy incoming traffic.

App Engine can take a Ghost web application and scale it to handle your growing global demand, while giving you all the benefits of Google Cloud Platform, including Cloud SQL, Cloud Source Repositories, Stackdriver Logging, Monitoring, Error Reporting, Trace, and Debugging, and more.

## Objectives

* Create a Cloud SQL instance, a database, and a user.
* Download Ghost.
* Configure Ghost for App Engine.
* Deploy Ghost to App Engine.

## Costs

This tutorial uses billable components of Cloud Platform, including:

* Google Cloud SQL
* Google App Engine Flexible Environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1. Select or create a [Google Cloud Platform Console][console] project. [Go to the projects page][projects].
1. Enable billing for your project. [Enable billing][billing].
1. Install the [Google Cloud SDK][sdk].
1. Authenticate `gcloud` with Google Cloud Platform.

        gcloud init

1. Create a new [Cloud SQL instance][sql].
  1. Create a user.
  1. Create a database called `ghost` (or another name if you prefer).

[console]: https://console.cloud.google.com/
[projects]: https://console.cloud.google.com/project
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing
[sdk]: https://cloud.google.com/sdk/
[sql]:  https://cloud.google.com/sql/docs/quickstart

## Download Ghost

1. Download Ghost:

        curl -L https://ghost.org/zip/ghost-latest.zip -o ghost.zip

1. Extract the files:

        unzip -uo ghost.zip -d ./ghost

1. Change directory:

        cd ghost

## Configure

1. Create a `config.js` file from the default config file:

        cp config.default.js config.js

1. Edit the `production` configuration in `config.js` and set it to the following:

        // Production configuration, activated when deployed to App Engine
        production: {
          // If you've configured a custom domain, set this to https://your-custom-domain.com
          url: 'https://<your-project-id>.appspot.com',
          // Disable file storage, as App Engine disks are not persistent
          fileStorage: false,
          // Configure email. See   http://support.ghost.org/mail/
          mail: {},
          // Configure Ghost to use the Cloud SQL instance
          database: {
            client: 'mysql',
            connection: {
              host: '<ip-address-of-cloud-sql-instance>',
              user: '<your-user>',
              password: '<your-password>',
              // "ghost", or whatever you named the database
              database: 'ghost',
              charset  : 'utf8'
            },
            debug: false
          },
          server: {
            // Important. This MUST be set to 0.0.0.0
            host: '0.0.0.0',
            // App Engine expects the app to listen on port 8080, which is what
            // process.env.PORT will be set to in production
            port: process.env.PORT || '2368'
          }
        }

    Here's some information about each setting:

    * `url` - The url at which the blog will be deployed. This is the url users will use to access the blog.
    * `fileStorage` - Setting this value to `false` forces image uploads to use an image url because App Engine doesn't have persistent disks.  Without this setting, any photos uploaded to the blog will eventually disappear.
    * `mail` - Configure this setting according to the instructions at http://support.ghost.org/mail/.
    * `database` - Tells Ghost how to connect to the Cloud SQL instance.
    * `server` - Tells Ghost how to listen for web traffic.

1. Optimize the Ghost web application for deployment on App Engine. Create an `appengine.js` file with the following contents:

        var express = require('express');
        var router = module.exports = express.Router();

        /**
         * App Engine doesn't set the X-Forwarded-Proto header, but instead sets the
         * X-AppEngine-Https header to "on" if the request was made over https, in which
         * case we update the X-Forwarded-Proto header to "https" because that's what
         * Express expects to find for https requests.
         */
        router.use(function (req, res, next) {
          if (req.get('x-appengine-https') === 'on' && !req.get('x-forwarded-proto')) {
            req.headers['x-forwarded-proto'] = 'https';
          }
          next();
        });

        /**
         * App Engine lifecycle event. See the following for more information:
         *
         * https://cloud.google.com/appengine/docs/flexible/custom-runtimes/build#lifecycle_events
         */
        router.get('/_ah/start', function (req, res) {
          res.status(200).send('ok').end();
        });

        /**
         * App Engine health check. See the following for configuring health check
         * behavior:
         *
         * https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#health_checks
         */
        router.get('/_ah/health', function (req, res) {
          res.status(200).send('ok').end();
        });

        /**
         * App Engine lifecycle event. See the following for more information:
         *
         * https://cloud.google.com/appengine/docs/flexible/custom-runtimes/build#lifecycle_events
         */
        router.get('/_ah/stop', function (req, res) {
          res.status(200).send('ok').end();
        });

1. Edit `index.js` and insert the following lines after `parentApp = express();`:

        parentApp = express();

        // Add these two lines for Google App Engine
        parentApp.set('trust proxy', true);
        parentApp.use(require('./appengine'));

1. Prepare for deployment. Create an `app.yaml` file with the following contents:

        runtime: nodejs
        vm: true
        manual_scaling:
          instances: 1

   Here's some information about each setting:

    * `runtime` - Tells App Engine to use the Node.js runtime.
    * `manual_scaling` - Forces App Engine to run one and only one instance. To automatically scale, remove this setting or change to `automatic_scaling` and configure according to [the documentation][scaling].
    * `resources` - You didn't change this setting, but the default instance size corresponds to a `g1.small` virtual machine. You can configure smaller or larger instances sizes as required. See the [documentation][resources].

    Read more about [using `app.yaml`][appyaml].

[scaling]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#auto-scaling
[resources]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#resource-settings
[appyaml]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml

## Deploy

Run the following command to deploy the app:

    gcloud preview app deploy

## What's next

[Ghost on App Engine Part 2 - Monitoring][monitoring]

[monitoring]: https://cloud.google.com/community/tutorials/ghost-on-app-engine-part-2-monitoring
[ghost]: https://ghost.org/
[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
