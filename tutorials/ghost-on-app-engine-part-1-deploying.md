---
title: Ghost on App Engine Flexibe Environment Part 1 - Deploying
description: Learn how to deploy a Ghost blog to Google App Engine flexible environment.
author: jmdobry
tags: App Engine, Ghost, Node.js
date_published: 2016-05-26
---
This tutorial explains how to deploy and scale a [Ghost blog][ghost] on
[Google App Engine Flexible Environment][flex].

Ghost is a simple blogging platform that can be self hosted. It's built with
Node.js, and can be customized or transformed into a bigger site. It serves as a
template for a larger application.

Google App Engine makes it easy to run web applications that must scale to meet
worldwide demand. It lets you focus on your code without having to worry about
operations, load balancing, servers, or scaling to satisfy incoming traffic.

App Engine can take a Ghost web application and scale it to handle your growing
global demand, while giving you all the benefits of Google Cloud Platform,
including Cloud SQL, Cloud Source Repositories, Stackdriver Debugger, Error
Reporting, Logging, Monitoring, Trace, and more.

## Objectives

* Create a Cloud SQL instance, a database, and a user.
* Download Ghost.
* Run Ghost locally.
* Configure Ghost for App Engine.
* Deploy Ghost to App Engine.

## Costs

This tutorial uses billable components of Cloud Platform, including:

* Google Cloud SQL
* Google App Engine Flexible Environment

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1. Select or create a [Google Cloud Platform Console][console] project.
[Go to the projects page][projects].
1. Enable billing for your project. [Enable billing][billing].
1. Install the [Google Cloud SDK][sdk].
1. Authenticate `gcloud` with Google Cloud Platform.

        gcloud init

1. Create a new [Second Generation Cloud SQL instance][sql]. You can do this
from the [Cloud Console][console] or via the [Cloud SDK][sdk].
    1. In order for some of the commands below to work, you need to enable the
    [Cloud SQL Admin API](https://console.cloud.google.com/apis/api/sqladmin-json.googleapis.com/overview).
    1. Create it via the following SDK command:

            gcloud sql instances create YOUR_INSTANCE_NAME \
                --activation-policy=ALWAYS \
                --tier=db-n1-standard-1

        where `YOUR_INSTANCE_NAME` is a name of your choice.

    1. Set the root password on your Cloud SQL instance:

            gcloud sql instances set-root-password YOUR_INSTANCE_NAME --password YOUR_INSTANCE_ROOT_PASSWORD

        where `YOUR_INSTANCE_NAME` is the name you chose in step 1 and
        `YOUR_INSTANCE_ROOT_PASSWORD` is a password of your choice.

    1. Create and download a [Service Account key file][service] for your
    project. You will use this service account to connect to your Cloud SQL
    instance locally.

    1. Download and install the [Cloud SQL Proxy][proxy].

    1. [Start the proxy][start] to allow connecting to your instance from your
    local machine:

            ./cloud_sql_proxy \
                -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306 \
                -credential_file=PATH_TO_YOUR_SERVICE_ACCOUNT_JSON_FILE

        where `YOUR_INSTANCE_CONNECTION_NAME` is the connection name of your
        instance on its Overview page in the Google Cloud Platform Console, or
        use `YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME`.

    1. Use the MySQL command line tools (or a management tool of your choice) to
    create a [new user][user] and [database][database] for your application:

            mysql -h 127.0.0.1 -P 3306 -u root -p
              mysql> create database `YOUR_DATABASE`;
              mysql> create user 'YOUR_USER'@'%' identified by 'PASSWORD';
              mysql> grant all on YOUR_DATABASE.* to 'YOUR_USER'@'%';

        Note: you will be asked to enter the root password you chose earlier.

    1. Set the `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` environment
    variables (see below). This allows your local Ghost app to connect to your
    Cloud SQL instance through the proxy.
    
    1. In adding Cloud SQL, dependencies need to be added in `package.json` for Google Cloud Node.

            "dependencies": {
              "express": "4.14.1",
              "mysql": "2.13.0",
              "prompt": "1.0.0"
            }

[console]: https://console.cloud.google.com/
[projects]: https://console.cloud.google.com/project
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing
[sdk]: https://cloud.google.com/sdk/
[service]: https://cloud.google.com/sql/docs/external#createServiceAccount
[proxy]: https://cloud.google.com/sql/docs/external#install
[start]: https://cloud.google.com/sql/docs/external#6_start_the_proxy
[user]: https://cloud.google.com/sql/docs/create-user
[database]: https://cloud.google.com/sql/docs/create-database
[sql]:  https://cloud.google.com/sql/docs/quickstart

## Download Ghost

1. Download Ghost:

        curl -L https://ghost.org/zip/ghost-latest.zip -o ghost.zip

1. Extract the files:

        unzip -uo ghost.zip -d ./ghost

1. Change directory:

        cd ghost

## Configure

Create a `config.js` file from the default config file:

    cp config.example.js config.js

### Run the app locally

1. Edit the `development` configuration in `config.js` and set it to the following:

        // Development configuration, activated when you run locally
        development: {
          // If you've configured a custom domain, set this to https://your-custom-domain.com
          url: 'http://localhost:2368',
          // Disable file storage
          fileStorage: false,
          // Configure email. See   http://support.ghost.org/mail/
          mail: {},
          // Configure Ghost to use the Cloud SQL instance
          database: {
            client: 'mysql',
            connection: {
              host: '127.0.0.1',
              user: process.env.MYSQL_USER,
              password: process.env.MYSQL_PASSWORD,
              database: process.env.MYSQL_DATABASE,
              charset  : 'utf8'
            },
            debug: true
          },
          server: {
            host: '127.0.0.1',
            port: '2368'
          }
        }

1. Install Dependencies:

        npm install --production

1. Start the app:

        npm start

1. To view the app, browse to:

        http://localhost:2368

1. Now stop your app by pressing Ctrl+C.


## Deploy

1. Edit the `production` configuration in `config.js` and set it to the following:

        // Production configuration, activated when deployed to App Engine
        production: {
          // If you've configured a custom domain, set this to https://your-custom-domain.com
          url: 'https://' + process.env.GCLOUD_PROJECT + '.appspot.com',
          // Disable file storage, as App Engine disks are not persistent
          fileStorage: false,
          // Configure email. See http://support.ghost.org/mail/
          mail: {},
          // Configure Ghost to use the Cloud SQL instance
          database: {
            client: 'mysql',
            connection: {
              socketPath: '/cloudsql/' + process.env.INSTANCE_CONNECTION_NAME,
              user: process.env.MYSQL_USER,
              password: process.env.MYSQL_PASSWORD,
              database: process.env.MYSQL_DATABASE,
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

1. Optimize the Ghost web application for deployment on App Engine. Create an
`appengine.js` file with the following contents:

        var express = require('express');
        var router = module.exports = express.Router();

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
        env: flex
        manual_scaling:
          instances: 1
        env_variables:
          MYSQL_USER: YOUR_MYSQL_USER
          MYSQL_PASSWORD: YOUR_MYSQL_PASSWORD
          MYSQL_DATABASE: YOUR_MYSQL_DATABASE
          # e.g. my-awesome-project:us-central1:my-cloud-sql-instance-name
          INSTANCE_CONNECTION_NAME: YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME
        beta_settings:
          # The connection name of your instance on its Overview page in the Google
          # Cloud Platform Console, or use `YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME`
          cloud_sql_instances: YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME

    Here's some information about each setting:

    * `runtime` - Tells App Engine to use the Node.js runtime.
    * `manual_scaling` - Forces App Engine to run one and only one instance. To automatically scale, remove this setting or change to `automatic_scaling` and configure according to [the documentation][scaling].
    * `resources` - You didn't change this setting, but the default instance size corresponds to a `g1.small` virtual machine. You can configure smaller or larger instances sizes as required. See the [documentation][resources].

    Read more about [using `app.yaml`][appyaml].

1. Run the following command to deploy the app:

    gcloud app deploy

[scaling]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#auto-scaling
[resources]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#resource-settings
[appyaml]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml

1. After deployment completes, view your deployed app at:

        https://YOUR_PROJECT_ID.appspot.com

    Where `YOUR_PROJECT_ID` is your Google Cloud Platform project ID.

## What's next

[Ghost on App Engine Part 2 - Monitoring][monitoring]

[monitoring]: https://cloud.google.com/community/tutorials/ghost-on-app-engine-part-2-monitoring
[ghost]: https://ghost.org/
[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
