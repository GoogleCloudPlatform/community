---
title: Deploying Ghost on App Engine flexible environment
description: Learn how to deploy a Ghost blog to App Engine flexible environment.
author: jmdobry
tags: App Engine, Ghost, Node.js
date_published: 2018-07-15
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how to deploy and scale a [Ghost blog][ghost] on the
[App Engine flexible environment][flex].

Ghost is a simple blogging platform that can be self-hosted. It's built with
Node.js, and it can be customized or transformed into a bigger site. It serves as a
template for a larger application.

App Engine makes it easy to run web applications that must scale to meet
worldwide demand. It lets you focus on your code without having to worry about
operations, load balancing, servers, or scaling to satisfy incoming traffic.

App Engine can take a Ghost web application and scale it to handle your growing
global demand, while giving you all the benefits of Google Cloud,
including Cloud SQL, Cloud Source Repositories, Cloud Debugger, Error
Reporting, Logging, Monitoring, Trace, and more.

## Objectives

* Create a Cloud SQL instance, a database, and a user.
* Download Ghost.
* Run Ghost locally.
* Configure Ghost for App Engine.
* Deploy Ghost to App Engine.

## Costs

This tutorial uses billable components of Google Cloud, including:

* Google Cloud SQL
* App Engine flexible environment

Use the [pricing calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Select or create a [Google Cloud][console] project.
    [Go to the projects page][projects].
1.  Enable billing for your project. [Enable billing][billing].
1.  Install the [Cloud SDK][sdk].
1.  Authenticate `gcloud` with Google Cloud:

        gcloud init

1.  Create a new [Second Generation Cloud SQL instance][sql]. You can do this
    from the [Cloud Console][console] or via the [Cloud SDK][sdk].

    1.  In order for some of the commands below to work, you need to enable the
        [Cloud SQL Admin API](https://console.cloud.google.com/apis/api/sqladmin-json.googleapis.com/overview).
    1.  Create it via the following SDK command:

            gcloud sql instances create YOUR_INSTANCE_NAME \
                --activation-policy=ALWAYS \
                --tier=db-f1-micro

        `YOUR_INSTANCE_NAME` is a name of your choice.
        You may want to set your region: `--region=YOUR_REGION_NAME`
        
    1.  Set the root password on your Cloud SQL instance:

            gcloud sql instances set-root-password root% YOUR_INSTANCE_NAME --password YOUR_INSTANCE_ROOT_PASSWORD

        `YOUR_INSTANCE_NAME` is the name you chose in step 1.
        `YOUR_INSTANCE_ROOT_PASSWORD` is a password of your choice.

    1.  Create and download a [service account key file][service] for your
        project. You will use this service account to connect to your Cloud SQL
        instance locally.

    1.  Download and install the [Cloud SQL Proxy][proxy].

    1.  [Start the proxy][start] to allow connecting to your instance from your
        local machine:

            ./cloud_sql_proxy \
                -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306 \
                -credential_file=PATH_TO_YOUR_SERVICE_ACCOUNT_JSON_FILE &

        `YOUR_INSTANCE_CONNECTION_NAME` is the connection name of your
        instance on its overview page in the Cloud Console, or
        use `YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME`.

    1.  Use the MySQL command-line tools (or a management tool of your choice) to
        create a [new user][user] and [database][database] for your application:

            mysql -u root -p -h 127.0.0.1
              mysql> create database `YOUR_DATABASE`;
              mysql> create user 'YOUR_USER'@'%' identified by 'PASSWORD';
              mysql> grant all on YOUR_DATABASE.* to 'YOUR_USER'@'%';

        You will be asked to enter the root password you chose earlier.

    1.  Set the `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` environment
        variables (see below). This allows your local Ghost app to connect to your
        Cloud SQL instance through the proxy.
    
    1.  In adding Cloud SQL, dependencies need to be added in `package.json` for Google Cloud Node.

            "dependencies": {
              "express": "^4.16.3",
              "mysql": "^2.15.0",
              "prompt": "^1.0.0"
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

## Install Ghost as an NPM module

Follow the instructions on the Ghost website to [install Ghost](https://ghost.org/docs/install/local/).

## Configure

1. Create a `config.development.json` file from the default configuration file:

        cp node_modules/ghost/core/server/config/env/config.development.json config.development.json

1. Create a `config.production.json` file from the default config file:

        cp node_modules/ghost/core/server/config/env/config.production.json config.production.json

### Run the app locally

1. Edit `config.development.json` and set it to the following:

    ```json
    {
        "url": "http://localhost:2368",
        "fileStorage": false,
        "mail": {},
        "database": {
            "client": "mysql",
            "connection": {
                "host": "127.0.0.1",
                "user": "YOUR_MYSQL_USERNAME",
                "password": "YOUR_MYSQL_PASSWORD",
                "database": "YOUR_MYSQL_DATABASE_NAME",
                "charset": "utf8"
            },
            "debug": false
        },
        "paths": {
            "contentPath": "content/"
        },
        "privacy": {
            "useRpcPing": false,
            "useUpdateCheck": true
        },
        "useMinFiles": false,
        "caching": {
            "theme": {
                "maxAge": 0
            },
            "admin": {
                "maxAge": 0
            }
        }
    }
    ```

1. Install dependencies:

        npm install --production

1. Start the app:

        npm start

1. To view the app, browse to:

        http://localhost:2368

1. Now stop your app by pressing Ctrl+C.


## Deploy

1. Edit `config.production.json` and set it to the following:

    ```json
    {
        "url": "https://YOUR_PROJECT_ID.appspot.com",
        "fileStorage": false,
        "mail": {},
        "database": {
            "client": "mysql",
            "connection": {
                "user": "YOUR_MYSQL_USERNAME",
                "password": "YOUR_MYSQL_PASSWORD",
                "database": "YOUR_MYSQL_DATABASE_NAME",
                "charset": "utf8"
            },
            "debug": false
        },
        "server": {
            "host": "0.0.0.0",
            "port": "8080"
        },
        "paths": {
            "contentPath": "content/"
        },
        "logging": {
            "level": "info",
            "rotation": {
                "enabled": true
            },
            "transports": ["file", "stdout"]
        }
    }
    ```

    Here's some information about each setting:

    * `url`: The URL at which the blog will be deployed. This is the URL users will use to access the blog.
    * `fileStorage`: Setting this value to `false` forces image uploads to use an image URL because App Engine doesn't have persistent disks. Without this setting, any photos uploaded to the blog will eventually disappear.
    * `mail`: Configure this setting according to the instructions at http://support.ghost.org/mail/.
    * `database`: Tells Ghost how to connect to the Cloud SQL instance.
    * `server`: Tells Ghost how to listen for web traffic.

1. Prepare for deployment. Create an `app.yaml` file with the following contents:

    ```yaml
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
      # The connection name of your instance on its Overview page in the
      # Cloud Console, or use `YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME`
      cloud_sql_instances: YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME
    skip_files:
      - ^(.*/)?#.*#$
      - ^(.*/)?.*~$
      - ^(.*/)?.*\.py[co]$
      - ^(.*/)?.*/RCS/.*$
      - ^(.*/)?\..*$
      - ^(.*/)?.*\.ts$
      - ^(.*/)?config\.development\.json$
    ```

    Here's some information about each setting:

    * `runtime`: Tells App Engine to use the Node.js runtime.
    * `manual_scaling`: Forces App Engine to run one and only one instance. To automatically scale, remove this setting or change to `automatic_scaling` and configure according to [the documentation][scaling].
    * `resources`: You didn't change this setting, but the default instance size corresponds to a `g1.small` virtual machine. You can configure smaller or larger instances sizes as required. See the [documentation][resources].

    Read more about [using `app.yaml`][appyaml].

1. Migrate the database to allow use in production:

        NODE_ENV=production knex-migrator init --mgpath node_modules/ghost

1. Add `"socketPath": "/cloudsql/YOUR_INSTANCE_NAME"` in the connection properties section of your `config.production.json`, so you end up with the following:

    ```json
    {
        "url": "http://YOUR_PROJECT_ID.appspot.com",
        "fileStorage": false,
        "mail": {},
        "database": {
            "client": "mysql",
            "connection": {
                "socketPath": "/cloudsql/YOUR_INSTANCE_NAME",
                "user": YOUR_MYSQL_USERNAME,
                "password": YOUR_MYSQL_PASSWORD,
                "database": YOUR_MYSQL_DATABASE_NAME,
                "charset": "utf8"
            },
            "debug": false
        },
        "server": {
            "host": "0.0.0.0",
            "port": "8080"
        },
        "paths": {
            "contentPath": "content/"
        },
        "logging": {
            "level": "info",
            "rotation": {
                "enabled": true
            },
            "transports": ["file", "stdout"]
        }
    }
    ```

It's very important that you only do this step after migrating the database. The `socketPath` property is required to deploy on App Engine, but it causes `knex-migrator` to throw an error.

1. Deploy the app:

        gcloud app deploy

[scaling]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#auto-scaling
[resources]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml#resource-settings
[appyaml]: https://cloud.google.com/appengine/docs/flexible/nodejs/configuring-your-app-with-app-yaml

1. After deployment completes, view your deployed app at `https://YOUR_PROJECT_ID.appspot.com` (in which `YOUR_PROJECT_ID` is your Google Cloud project ID).

## What's next

[Monitoring Ghost on App Engine flexible environment - Part 2][monitoring]

[monitoring]: https://cloud.google.com/community/tutorials/ghost-on-app-engine-part-2-monitoring
[ghost]: https://ghost.org/
[flex]: https://cloud.google.com/appengine/docs/flexible/nodejs/
