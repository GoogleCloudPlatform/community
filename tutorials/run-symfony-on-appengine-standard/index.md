---
title: Run Symfony on Google App Engine standard environment
description: Learn how to deploy a Symfony app to Google App Engine standard environment.
author: bshaffer
tags: App Engine, Symfony, PHP
date_published: 2019-02-01
---

## Symfony

"[Symfony][symfony] is a set of PHP Components, a Web Application framework, a Philosophy, 
and a Community — all working together in harmony." – symfony.com

You can check out [PHP on Google Cloud Platform][php-gcp] to get an
overview of PHP itself and learn ways to run PHP apps on Google Cloud
Platform.

## Prerequisites

1. [Create a project][create-project] in the GCP Console
   and make note of your project ID.
1. [Enable billing][enable-billing] for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Install

This tutorial uses the [Symfony Demo][symfony-demo] application. Run the
following command to install it:

    PROJECT_DIR='symfony-on-appengine'
    composer create-project symfony/symfony-demo:^1.2 $PROJECT_DIR

## Run

1.  Run the app with the following command:

        php bin/console server:run

1.  Visit [http://localhost:8000](http://localhost:8000) to see the Symfony
Welcome page.

## Deploy

1.  Remove the `scripts` section from `composer.json` in the root of your
    project. You can do this manually, or by running the following line of code
    in the root of your Symfony project:

        php -r "file_put_contents('composer.json', json_encode(array_diff_key(json_decode(file_get_contents('composer.json'), true), ['scripts' => 1]), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));"

    **Note**: The composer scripts run on the [Cloud Build][cloud-build] server.
    This is a temporary fix to prevent errors prior to deployment.

1.  Copy the [`app.yaml`][app_yaml] file from this repository into the root of
    your project and replace `YOUR_APP_SECRET` with a new secret or the generated
    secret in `.env`:

        runtime: php72

        env_variables:
          APP_ENV: prod
          APP_SECRET: YOUR_APP_SECRET

        handlers:
          # Declare the build and bundles directory as static assets to be served by the
          # App Engine CDN.
          - url: /build
            static_dir: public/build
          - url: /bundles
            static_dir: public/bundles

          # Declare any media files in the public directory as static assets as well.
          - url: /(.*\.(ico|txt|gif|png|jpg))$
            static_files: public/\1
            upload: public/.*\.(ico|txt|gif|png|jpg)$

    **Note**: Read more about the [env][symfony-env] and [secret][symfony-secret]
    parameters in Symfony's documentation.

1.  [Override the cache and log directories][symfony-override-cache] so that
    they use `/tmp` in production. This is done by modifying the functions
    `getCacheDir` and `getLogDir` to the following in `src/Kernel.php`:

        class Kernel extends BaseKernel
        {
            //...

            public function getCacheDir()
            {
                if ($this->environment === 'prod') {
                    return sys_get_temp_dir();
                }
                return $this->getProjectDir() . '/var/cache/' . $this->environment;
            }

            public function getLogDir()
            {
                if ($this->environment === 'prod') {
                    return sys_get_temp_dir();
                }
                return $this->getProjectDir() . '/var/log';
            }

            // ...
        }
   
    **Note**: This is required because App Engine's file system is **read-only**.

1.  Deploy your application to App Engine:

        gcloud app deploy

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Symfony demo landing
    page.

The homepage will load when you view your application, but browsing to any of
the other demo pages will result in a **500** error. This is because you haven't
set up a database yet. Let's do that now!

## Connect to Cloud SQL with Doctrine

Next, connect your Symfony demo application with a [Cloud SQL][cloud-sql]
database. This tutorial uses the database name `symfonydb` and the username
`root`, but you can use whatever you like.

### Setup

1.  Follow the instructions to set up a
    [Google Cloud SQL Second Generation instance for MySQL][cloud-sql-create].

1.  Create a database for your Symfony application. Replace `INSTANCE_NAME`
    with the name of your instance:

        gcloud sql databases create symfonydb --instance=INSTANCE_NAME

1.  Enable the [Cloud SQL APIs][cloud-sql-apis] in your project.

1.  Follow the instructions to
    [install and run the Cloud SQL proxy client on your local machine][cloud-sql-install].
    The Cloud SQL proxy is used to connect to your Cloud SQL instance when
    running locally. This is so you can run database migrations locally to set up
    your production database.

      * Use the [Cloud SDK][cloud-sdk] from the command line to run the following
        command. Copy the `connectionName` value for the next step. Replace
        `INSTANCE_NAME` with the name of your instance:

            gcloud sql instances describe INSTANCE_NAME

      * Start the Cloud SQL proxy and replace `INSTANCE_CONNECTION_NAME` with
        the connection name you retrieved in the previous step:

            cloud_sql_proxy -instances=INSTANCE_CONNECTION_NAME=tcp:3306 &

        **Note**: Include the `-credential_file` option when using the proxy, or
        authenticate with `gcloud`, to ensure proper authentication.

### Configure

1.  Modify your Doctrine configuration in `config/packages/doctrine.yml` and
    change the parameters under `doctrine.dbal` to be the following:

        # Doctrine Configuration
        doctrine:
            dbal:
                driver: pdo_mysql
                url: '%env(resolve:DATABASE_URL)%'

            # ORM configuration
            # ...

1.  Use the Symfony CLI to connect to your instance and create a database for
    the application. Be sure to replace `DB_PASSWORD` with the root password you
    configured:

        # create the database using doctrine
        DATABASE_URL="mysql://root:DB_PASSWORD@127.0.0.1:3306/symfonydb" \
            bin/console doctrine:schema:create

1.  Modify your `app.yaml` file with the following contents. Be sure to replace
    `DB_PASSWORD` and `INSTANCE_CONNECTION_NAME` with the values you created for
    your Cloud SQL instance:

        runtime: php72

        env_variables:
          APP_ENV: prod
          APP_SECRET: YOUR_APP_SECRET

          # Add the DATABASE_URL environment variable
          DATABASE_URL: mysql://root:DB_PASSWORD@localhost?unix_socket=/cloudsql/INSTANCE_CONNECTION_NAME;dbname=symfonydb

        # URL handlers
        # ...

### Run

1.  Now you can run locally and verify the connection works as expected.

        DB_HOST="127.0.0.1" DB_DATABASE=symfony DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD \
            php bin/console server:run

1.  Reward all your hard work by running the following command and deploying
    your application to App Engine:

        gcloud app deploy

## Set up Stackdriver Logging and Error Reporting

Install the Google Cloud libraries for Stackdriver integration:

    # Set the environment variable below to the local path to your symfony project
    SYMFONY_PROJECT_PATH="/path/to/my-symfony-project"
    cd $SYMFONY_PROJECT_PATH
    composer require google/cloud-logging google/cloud-error-reporting

### Copy over App Engine files

For your Symfony application to integrate with Stackdriver Logging and Error Handling,
you will need to copy over the `monolog.yaml` config file and the `ExceptionSubscriber.php`
Exception Subscriber:

    # clone the Google Cloud Platform PHP samples repo somewhere
    cd /path/to/php-samples
    git clone https://github.com/GoogleCloudPlatform/php-docs-samples

    # enter the directory for the symfony framework sample
    cd appengine/php72/symfony-framework/

    # copy monolog.yaml into your Symfony project
    cp config/packages/prod/monolog.yaml \
        $SYMFONY_PROJECT_PATH/config/packages/prod/

    # copy ExceptionSubscriber.php into your Symfony project
    cp src/EventSubscriber/ExceptionSubscriber.php \
        $SYMFONY_PROJECT_PATH/src/EventSubscriber

The files needed are as follows:

[`config/packages/prod/monolog.yaml`](https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/symfony-framework/config/packages/prod/monolog.yaml): Adds Stackdriver Logging to your Monolog configuration.

[`src/EventSubscriber/ExceptionSubscriber.php`](https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/symfony-framework/src/EventSubscriber/ExceptionSubscriber.php): Event subscriber that sends exceptions to Stackdriver Error Reporting.

If you'd like to test the logging and error reporting, you can also copy over `LoggingController.php`, which
exposes the routes `/en/logging/notice` and `/en/logging/exception` for ensuring your logs are being sent to
Stackdriver:

    # copy LoggingController.php into your Symfony project
    cp src/Controller/LoggingController.php \
        $SYMFONY_PROJECT_PATH/src/Controller


[`src/Controller/LoggingController.php`](https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/symfony-framework/src/Controller/LoggingController.php): Controller for testing logging and exceptions.

### View application logs and errors

Once you've redeployed your application using `gcloud app deploy`, you'll be able to view
Application logs in the [Stackdriver Logging UI][stackdriver-logging-ui], and errors in
the [Stackdriver Error Reporting UI][stackdriver-errorreporting-ui]! If you copied over the
`LoggingController.php` file, you can test this by pointing your browser to
`https://YOUR_PROJECT_ID.appspot.com/en/logging/notice` and
`https://YOUR_PROJECT_ID.appspot.com/en/logging/exception`

[php-gcp]: https://cloud.google.com/php
[cloud-sdk]: https://cloud.google.com/sdk/
[app_yaml]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/symfony-framework/app.yaml
[cloud-build]: https://cloud.google.com/cloud-build/
[cloud-sql]: https://cloud.google.com/sql/docs/
[cloud-sql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloud-sql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install
[cloud-sql-apis]:https://console.cloud.google.com/apis/library/sqladmin.googleapis.com/?pro
[create-project]: https://cloud.google.com/resource-manager/docs/creating-managing-projects
[enable-billing]: https://support.google.com/cloud/answer/6293499?hl=en
[symfony]: http://symfony.com
[symfony-install]: http://symfony.com/doc/current/setup.html
[symfony-demo]: https://github.com/symfony/demo
[symfony-secret]: http://symfony.com/doc/current/reference/configuration/framework.html#secret
[symfony-env]: https://symfony.com/doc/current/configuration/environments.html#executing-an-application-in-different-environments
[symfony-override-cache]: https://symfony.com/doc/current/configuration/override_dir_structure.html#override-the-cache-directory
[symfony-welcome]: https://storage.googleapis.com/gcp-community/tutorials/run-symfony-on-appengine-standard/welcome-page.png
[stackdriver-logging-ui]: https://console.cloud.google.com/logs
[stackdriver-errorreporting-ui]: https://console.cloud.google.com/errors
