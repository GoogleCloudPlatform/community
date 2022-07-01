---
title: Run Laravel on App Engine flexible environment
description: Learn how to deploy a Laravel app to the App Engine flexible environment.
author: bshaffer
tags: App Engine, Laravel, PHP
date_published: 2017-03-15
---

Brent Shaffer  | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Laravel][laravel] is an open source web framework for PHP developers that encourages the use of the model-view-controller (MVC) pattern.

You can check out [PHP on Google Cloud][php-gcp] to get an
overview of PHP and learn ways to run PHP apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/project).
1. Enable billing for your project.
1. Install the [Cloud SDK][cloud_sdk].

## Prepare

Follow the official documentation for [installing Laravel][laravel-install]
from laravel.com.

## Run

1. Run the app with the following command:

        php artisan serve

1. Visit [http://localhost:8000](http://localhost:8000) to see the Laravel
   Welcome page.

## Deploy

1.  Create an `app.yaml` file with the following contents:

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

1.  Replace `YOUR_APP_KEY` in `app.yaml` with an application key you generate
    with the following command:

        php artisan key:generate --show

    If you're on Linux or macOS, the following command will automatically
    update your `app.yaml`:

        sed -i '' "s#YOUR_APP_KEY#$(php artisan key:generate --show --no-ansi)#" app.yaml

1.  Add the following under `scripts` in `composer.json`:

        "post-install-cmd": [
            "chmod -R 755 bootstrap\/cache",
            "php artisan cache:clear"
        ]

    In the context of Laravel's `composer.json` file, it will look like this:

    ![Add post-install-cmd scripts to composer.json][composer-json]

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Laravel welcome page. Replace `YOUR_PROJECT_ID`
    with the ID of your Google Cloud project.

    ![Laravel welcome page][laravel-welcome]

## Set up database sessions

**Note**: This section only works with Laravel 5.4.16. To use earlier versions of
Laravel, you need to manually add the `DB_SOCKET` value to
`config/database.php` (see [#4178](https://github.com/laravel/laravel/pull/4179/files))

1. [Enable the Cloud SQL API][cloudsql-enable-api] in your project.

1. Follow the instructions to set up a
   [Google Cloud SQL Second Generation instance for MySQL][cloudsql-create].

1.  Follow the instructions to
    [install the Cloud SQL proxy client on your local machine][cloudsql-install].
    The Cloud SQL proxy is used to connect to your Cloud SQL instance when running
    locally.

1.  Use the [Cloud SDK][cloud_sdk] from the command line to run the following command. Copy
    the `connectionName` value for the next step. Replace `YOUR_INSTANCE_NAME` with the name
    of your instance:

        gcloud sql instances describe YOUR_INSTANCE_NAME

1.  Start the Cloud SQL proxy and replace `YOUR_INSTANCE_CONNECTION_NAME` with
    the connection name you retrieved in the previous step:

        cloud_sql_proxy -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306

1.  Use the MySQL client, or a similar program, to connect to your instance and
    create a database for the application. When prompted, use the root password
    you configured.

        mysql -h 127.0.0.1 -u root -p -e "CREATE DATABASE laravel;"

1.  Run the database migrations for Laravel. This can be done locally by setting
    your parameters in `.env` or by passing them in as environment variables. Be
    sure to replace `YOUR_DB_PASSWORD` below with the root password you
    configured:

        # create a migration for the session table
        php artisan session:table
        DB_DATABASE=laravel DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD php artisan migrate --force

1.  Modify your `app.yaml` file with the following contents:

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
          CACHE_DRIVER: database
          SESSION_DRIVER: database
          ## Set these environment variables according to your CloudSQL configuration.
          DB_HOST: localhost
          DB_DATABASE: laravel
          DB_USERNAME: root
          DB_PASSWORD: YOUR_DB_PASSWORD
          DB_SOCKET: "/cloudsql/YOUR_CLOUDSQL_CONNECTION_NAME"

        beta_settings:
            # for Cloud SQL, set this value to the Cloud SQL connection name,
            # e.g. "project:region:cloudsql-instance"
            cloud_sql_instances: "YOUR_CLOUDSQL_CONNECTION_NAME"
   
1.  Replace each instance of `YOUR_DB_PASSWORD` and `YOUR_CLOUDSQL_CONNECTION_NAME`
    with the values you created for your Cloud SQL instance above.

[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[laravel-install]: https://laravel.com/docs/5.4/installation
[laravel-welcome]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/welcome-page.png
[cloud_sdk]: https://cloud.google.com/sdk/
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/composer-json.png
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-enable-api]: https://console.cloud.google.com/flows/enableapi?apiid=sqladmin
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install
