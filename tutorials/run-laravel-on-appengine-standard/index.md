---
title: Run Laravel on Google App Engine Standard
description: Learn how to deploy a Laravel app to Google App Engine standard environment.
author: bshaffer
tags: App Engine, Laravel, PHP
date_published: 2019-01-31
---
## Laravel

[Laravel][laravel] is an open source web framework for PHP developers that encourages the use of the model-view-controller (MVC) pattern.

You can check out [PHP on Google Cloud Platform][php-gcp] (GCP) to get an
overview of PHP and learn ways to run PHP apps on GCP.

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/project).
1. Enable billing for your project.
1. Install the [Google Cloud SDK][cloud_sdk].

> All code for this tutorial is available in the [PHP samples repository][laravel-framework-sample].

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

        runtime: php72

        env_variables:
          # Put production environment variables here.
          LOG_CHANNEL: stackdriver
          APP_KEY: YOUR_APP_KEY
          APP_STORAGE: /tmp

1.  Replace `YOUR_APP_KEY` in `app.yaml` with an application key you generate
    with the following command:

        php artisan key:generate --show

    If you're on Linux or macOS, the following command will automatically
    update your `app.yaml`:

        sed -i '' "s#YOUR_APP_KEY#$(php artisan key:generate --show --no-ansi)#" app.yaml

1.  Modify [`bootstrap/app.php`][bootstrap-app-php] by adding the block
    of code below before the return statement. This will allow us to set
    the storage path to `/tmp` for caching in production.

        /*
        |--------------------------------------------------------------------------
        | Set Storage Path
        |--------------------------------------------------------------------------
        |
        | This script allows us to override the default storage location used by
        | the  application.  You may set the APP_STORAGE environment variable
        | in your .env file,  if not set the default location will be used
        |
        */
        $app->useStoragePath(env('APP_STORAGE', base_path() . '/storage'));

1.  Modify [`config/view.php`][config-view-php] by adding the block
    of code below to the returned array. This ensures our `/tmp` storage
    path is used for caching our templates.

        /*
        |--------------------------------------------------------------------------
        | Compiled View Path
        |--------------------------------------------------------------------------
        |
        | This option determines where all the compiled Blade templates will be
        | stored for your application. Typically, this is within the storage
        | directory. However, as usual, you are free to change this value.
        |
        */
        'compiled' => storage_path(),

1.  Run the following command to deploy your app:

        gcloud app deploy

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Laravel welcome page.
    Replace `YOUR_PROJECT_ID` with the ID of your GCP project.

    ![Laravel welcome page][laravel-welcome]

## Set up Database Sessions

**Note**: This section only works with Laravel 5.4.16. To use earlier versions of
Laravel, you need to manually add the `DB_SOCKET` value to
`config/database.php` (see [#4178](https://github.com/laravel/laravel/pull/4179/files))

1.  Follow the instructions to set up a
    [Google Cloud SQL Second Generation instance for MySQL][cloudsql-create].
    Keep track of your instance name and password, as they
    will be used below.

1.  Follow the instructions to
    [install the Cloud SQL proxy client on your local machine][cloudsql-install].
    The Cloud SQL proxy is used to connect to your Cloud SQL instance when running
    locally.

    *   Use the [Google Cloud SDK][cloud_sdk] from the command line to run the
        following command. Copy the `connectionName` value for the next step. Replace
        `YOUR_INSTANCE_NAME` with the name of your instance:

            gcloud sql instances describe YOUR_INSTANCE_NAME | grep connectionName

    *   Start the Cloud SQL proxy and replace `YOUR_CONNECTION_NAME` with the
        connection name you retrieved in the previous step.

            cloud_sql_proxy -instances=YOUR_CONNECTION_NAME=tcp:3306

    *   Use `gcloud` to create a database for the application.

            gcloud sql databases create laravel --instance=YOUR_INSTANCE_NAME

1.  Run the database migrations for Laravel. This can be done locally by setting
    your parameters in `.env` or by passing them in as environment variables. Be
    sure to replace `YOUR_DB_PASSWORD` below with the root password you
    configured:

        # create a migration for the session table
        php artisan session:table
        export DB_DATABASE=laravel DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD
        php artisan migrate --force

1.  Modify your `app.yaml` file with [the following contents][app-dbsessions-yaml]:

        runtime: php72

        env_variables:
          # Put production environment variables here.
          APP_LOG: errorlog
          APP_KEY: YOUR_APP_KEY
          APP_STORAGE: /tmp
          CACHE_DRIVER: database
          SESSION_DRIVER: database
          ## Set these environment variables according to your CloudSQL configuration.
          DB_DATABASE: YOUR_DB_DATABASE
          DB_USERNAME: YOUR_DB_USERNAME
          DB_PASSWORD: YOUR_DB_PASSWORD
          DB_SOCKET: "/cloudsql/YOUR_CONNECTION_NAME"

1.  Replace `YOUR_DB_DATABASE`, `YOUR_DB_USERNAME`, `YOUR_DB_PASSWORD`,
    and `YOUR_CONNECTION_NAME` with the values you created for your Cloud SQL
    instance above.

## Set up Stackdriver Logging and Error Reporting

Before we begin, install both of the Google Cloud client libraries for Stackdriver
Logging and Error Reporting:

    composer require google/cloud-logging google/cloud-error-reporting

### Stackdriver Logging

You can write logs to Stackdriver Logging from PHP applications by using the Stackdriver Logging library for PHP directly.

1.  First, create a custom logger in
    [`app/Logging/CreateStackdriverLogger.php`][app-logging-createstackdriverlogger-php]:

        namespace App\Logging;

        use Google\Cloud\Logging\LoggingClient;
        use Monolog\Handler\PsrHandler;
        use Monolog\Logger;

        class CreateStackdriverLogger
        {
            /**
             * Create a custom Monolog instance.
             *
             * @param  array  $config
             * @return \Monolog\Logger
             */
            public function __invoke(array $config)
            {
                $logName = isset($config['logName']) ? $config['logName'] : 'app';
                $psrLogger = LoggingClient::psrBatchLogger($logName);
                $handler = new PsrHandler($psrLogger);
                $logger = new Logger($logName, [$handler]);
                return $logger;
            }
        }

1.  Next, you'll need to add our new custom logger to the `channels` array in
    [`config/logging.php`][config-logging-php]:

        'channels' => [

            // Add the following lines to integrate with Stackdriver:
            'stackdriver' => [
                'driver' => 'custom',
                'via' => App\Logging\CreateCustomLogger::class,
                'level' => 'debug',
            ],

1.  Now you can log to Stackdriver Logging anywhere in your application!

        Log::info("Hello Stackdriver! This will show up as log level INFO!");
    

### Stackdriver Error Reporting

You can send error reports to Stackdriver Error Reporting from PHP applications by using the
[Stackdriver Error Reporting library for PHP][stackdriver-error-reporting-php].

1.  Add the following `use` statement at the beginning of the file
    [`app/Exceptions/Handler.php`][app-exceptions-handler-php]:

        use Google\Cloud\ErrorReporting\Bootstrap;

1.  Edit the `report` function in the same file
    [`app/Exceptions/Handler.php`][app-exceptions-handler-php] as follows:

        public function report(Exception $exception)
        {
            if (isset($_SERVER['GAE_SERVICE'])) {
                Bootstrap::init();
                Bootstrap::exceptionHandler($exception);
            } else {
                parent::report($exception);
            }
        }

1.  Now any PHP Exception will be logged to Stackdriver Error Reporting!

        throw new \Exception('PHEW! We will see this in Stackdriver Error Reporting!');

[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[laravel-install]: https://laravel.com/docs/5.4/installation
[laravel-welcome]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/welcome-page.png
[cloud_sdk]: https://cloud.google.com/sdk/
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/composer-json.png
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install
[laravel-framework-sample]: https://github.com/GoogleCloudPlatform/php-docs-samples/tree/master/appengine/php72/laravel-framework
[bootstrap-app-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/bootstrap/app.php
[config-view-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/config/view.php
[app-dbsessions-yaml]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/app-dbsessions.yaml
[app-logging-createstackdriverlogger-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/app/Logging/CreateStackdriverLogger.php
[config-logging-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/config/logging.php
[stackdriver-error-reporting-php]:http://googleapis.github.io/google-cloud-php/#/docs/cloud-error-reporting/v0.12.3/errorreporting/readme
[app-exceptions-handler-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/php72/laravel-framework/app/Exceptions/Handler.php
