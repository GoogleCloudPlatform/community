---
title: Run Laravel on Google App Engine Flexible Environment
description: Learn how to deploy a Laravel app to Google App Engine flexible environment.
author: bshaffer
tags: App Engine, Laravel, PHP
date_published: 2017-03-15
---
## Laravel

> [Laravel][laravel]: The PHP Framework For Web Artisans.
>
> – laravel.com

You can check out [PHP on Google Cloud Platform][php-gcp] to get an
overview of PHP itself and learn ways to run PHP apps on Google Cloud
Platform.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Follow the official documentation for [installing Laravel][laravel-install]
from laravel.com.

## Run

1. Run the app with the following command:

        php artisan serve

1. Visit [http://localhost:8000](http://localhost:8000) to see the Laravel
Welcome page.

## Deploy

1. Create an `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: public

        # required on some platforms so ".env" is not skipped
        skip_files: false

        env_variables:
          # The values here will override those in ".env". This is useful for
          # production-specific configuration. However, feel free to set these
          # values in ".env" instead if you prefer.
          APP_LOG: errorlog
          STORAGE_DIR: /tmp

1. Add the following under `scripts` in `composer.json`:

        "post-deploy-cmd": [
            "chmod -R 755 bootstrap\/cache"
        ]

    In the context of Laravel's `composer.json`, it will look like this:

    ![Add post-deploy-cmd scripts to composer.json][composer-json]

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Laravel welcome page!

    ![Laravel welcome page][laravel-welcome]

## Set up Database Sessions

1. Follow the instructions to set up a
[Cloud SQL Second Generation instance for MySQL][cloudsql-create].

1. Follow the instructions to
[install the Cloud SQL proxy client on your local machine][cloudsql-install].
The Cloud SQL proxy is used to connect to your Cloud SQL instance when running
locally.

1. Use the Cloud SDK from the command line to run the following command. Copy
the `connectionName` value for the next step.

        gcloud beta sql instances describe YOUR_INSTANCE_NAME

1. Start the Cloud SQL proxy using the connection name from the previous step:

        cloud_sql_proxy -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306

1. Use the MySQL client or a similar program to connect to your instance and
  create a database for the application. When prompted, use the root password
  you configured.

        mysql -h 127.0.0.1 -u root -p -e "CREATE DATABASE laravel;"

1. Run the database migrations for Laravel. This can be done by setting your
  parameters in `.env` or by passing them in as environment variables. Be sure
  to replace `YOUR_DB_PASSWORD` below with the root password you configured:

        # create a migration for the session table
        php artisan session:table
        DB_DATABASE=laravel DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD php artisan migrate --force

1. Edit `config/database.php` and add a line for `unix_socket` to the
  'mysql' connection configuration:

        'mysql' => [
            // ...
            'unix_socket' => env('DB_SOCKET', ''),

1. Modify your `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: public

        # required on some platforms so ".env" is not skipped
        skip_files: false

        env_variables:
          # The values here will override those in ".env". This is useful for
          # production-specific configuration. However, feel free to set these values
          # in ".env" instead if you prefer.
          APP_LOG: errorlog
          STORAGE_DIR: /tmp
          CACHE_DRIVER: database
          SESSION_DRIVER: database
          ## Set these environment variables according to your CloudSQL configuration.
          DB_HOST: localhost
          DB_DATABASE: laravel
          DB_USERNAME: root
          DB_PASSWORD: YOUR_DB_PASSWORD
          DB_SOCKET: /cloudsql/YOUR_CLOUDSQL_CONNECTION_NAME

        beta_settings:
            # for Cloud SQL, set this value to the Cloud SQL connection name,
            # e.g. "project:region:cloudsql-instance"
            cloud_sql_instances: "YOUR_CLOUDSQL_CONNECTION_NAME"

1. Replace each instance of `YOUR_DB_PASSWORD` and `YOUR_CLOUDSQL_CONNECTION_NAME`
with the values you created for your CloudSQL instance above.

[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[laravel-install]: https://laravel.com/docs/5.4/installation
[laravel-welcome]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/welcome-page.png
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/composer-json.png
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install

