---
title: Run your own DocsPen for your Company
description: Setup your own DocsPen Instance on Google Cloud to make your Company Documentation Awesome.
author: Yoginth
tags: App Engine, DocsPen, Laravel, PHP, Documentation
date_published: 2018-02-18
---

You can use DocsPen on Google App Engine to develop your company documentation.

[DocsPen](https://docspen.ga)
is a platform to publish your own documentation for projects through online,
it is a right choice for Professors & Teachers for publishing the content,
which provides a pleasant and simple out of the box experience. New users 
to an instance should find the experience intuitive and only basic word-processing
skills should be required to get involved in creating content on DocsPen. 
The platform should provide advanced power features to those that desire 
it but they should not interfere with the core simple user experience.

[Google App Engine's platform-as-a-service (PaaS) features](https://cloud.google.com/appengine/)
let you easily run on Google's infrastructure, so your app can automatically
scale to serve millions of users, while keeping your costs under control.

## Objectives

* Create a Cloud SQL instance, a database, and a user.
* Clone [DocsPen](https://github.com/DocsPen/DocsPen) from GitHub.
* Run DocsPen locally.
* Configure DocsPen for App Engine.
* Deploy DocsPen to App Engine.

## Run

1. Run the app with the following command:

        php artisan serve

1. Visit [http://localhost:8000](http://localhost:8000) to see the DocsPen Page.

## Deploy

1. Replace `YOUR_APP_KEY` in `app.yaml` with an application key you generate
  with the following command:

        php artisan key:generate --show

    If you're on Linux or macOS, the following command will automatically
    update your `app.yaml`:

        sed -i '' "s#YOUR_APP_KEY#$(php artisan key:generate --show --no-ansi)#" app.yaml

1. Add the following under `scripts` in `composer.json`:

        "post-install-cmd": [
            "chmod -R 755 bootstrap\/cache",
            "php artisan cache:clear"
        ]

    In the context of DocsPen's `composer.json` file, it will look like this:

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the DocsPen home page. Replace `YOUR_PROJECT_ID`
   with the ID of your GCP project.

## Set up Database Sessions


1. Follow the instructions to set up a
   [Google Cloud SQL Second Generation instance for MySQL][cloudsql-create].

1. Follow the instructions to
   [install the Cloud SQL proxy client on your local machine][cloudsql-install].
   The Cloud SQL proxy is used to connect to your Cloud SQL instance when running
   locally.

1. Use the [Cloud SDK][cloud_sdk] from the command line to run the following command. Copy
   the `connectionName` value for the next step. Replace `YOUR_INSTANCE_NAME` with the name
   of your instance:

        gcloud sql instances describe YOUR_INSTANCE_NAME

1. Start the Cloud SQL proxy and replace `YOUR_INSTANCE_CONNECTION_NAME` with
   the connection name you retrieved in the previous step:

        cloud_sql_proxy -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306

1. Use the MySQL client, or a similar program, to connect to your instance and
  create a database for the application. When prompted, use the root password
  you configured.

        mysql -h 127.0.0.1 -u root -p -e "CREATE DATABASE docspen;"

1. Run the database migrations for DocsPen. This can be done locally by setting
  your parameters in `.env` or by passing them in as environment variables. Be
  sure to replace `YOUR_DB_PASSWORD` below with the root password you
  configured:

        # create a migration for the session table
        php artisan session:table
        DB_DATABASE=docspen DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD php artisan migrate --force

1. Modify your `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: public

        # Ensure we skip ".env", which is only for local development
        skip_files:
          - .env

        env_variables:
          # Put production environment variables here.
          APP_LOG: errorlog
          APP_KEY: YOUR_APP_KEY
          STORAGE_DIR: /tmp
          CACHE_DRIVER: database
          SESSION_DRIVER: database
          ## Set these environment variables according to your CloudSQL configuration.
          DB_HOST: localhost
          DB_DATABASE: docspen
          DB_USERNAME: root
          DB_PASSWORD: YOUR_DB_PASSWORD
          DB_SOCKET: "/cloudsql/YOUR_CLOUDSQL_CONNECTION_NAME"

        beta_settings:
            # for Cloud SQL, set this value to the Cloud SQL connection name,
            # e.g. "project:region:cloudsql-instance"
            cloud_sql_instances: "YOUR_CLOUDSQL_CONNECTION_NAME"

1. Replace each instance of `YOUR_DB_PASSWORD` and `YOUR_CLOUDSQL_CONNECTION_NAME`
   with the values you created for your Cloud SQL instance above.

[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[cloud_sdk]: https://cloud.google.com/sdk/
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install
