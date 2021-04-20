---
title: Run Laravel on Google App Engine standard environment
description: Learn how to deploy a Laravel app to Google App Engine standard environment.
author: bshaffer
tags: App Engine, Laravel, PHP
date_published: 2019-01-31
---

Brent Shaffer | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Laravel][laravel] is an open source web framework for PHP developers that encourages the use of the
model-view-controller (MVC) pattern.
This tutorial uses Laravel 8.

You can check out [PHP on Google Cloud][php-gcp] to get an
overview of PHP and learn ways to run PHP apps on Google Cloud.

## Prerequisites

1. Create a project in the [Cloud Console](https://console.cloud.google.com/project).
1. Enable billing for your project.
1. Install and initialize the [Cloud SDK][cloud_sdk].

All code for the original version of this tutorial is available in the 
[PHP samples repository][laravel-framework-sample].

## Prepare

Follow the official documentation for [installing Laravel][laravel-install]
and create a sample laravel app with one of the methods provided on the
installation page.

## Run

1. From your Laravel project run the app with the following command:

        php artisan serve

1. Visit [http://localhost:8000](http://localhost:8000) to see the Laravel
   Welcome page.

## Deploy

1.  Create an `app.yaml` file with the following contents:

        runtime: php74

        env_variables:
          GCP_APP_ENGINE_LARAVEL: true
    
        handlers:
          - url: /css
            static_dir: public/css
          - url: /js
            static_dir: public/js
          - url: /(.+\.(ico|json|txt))$
            static_files: public/\1
            upload: public/.+\.(ico|json|txt)$
          - url: /.*
            script: auto
    
    This tutorial makes minimal use of environment variables.
    Instead, we will be caching our configuration.

    The `handlers` section ensures that we properly serve:

    - Compiled assets from `public/css` and `public/js` directories.
    - Files in the `public` directory, such as `favicon.ico` and `robots.txt`.
    
    The last handler is required by App Engine to serve the entrypoint to our 
    Laravel application, `public/index.php`.

1.  Create an `.env.gae` file with the following contents:

        APP_KEY=%%APP_KEY%%
        APP_ENV=production
        APP_DEBUG=false
    
    This file is where you should keep all production configuration.

1.  Replace `%%APP_KEY%%` in `.env.gae` with an application key you generate
    with the following command:

        php artisan key:generate --show

    On macOS, the following command will automatically update your `.env.gae`:

        sed -i '' "s#%%APP_KEY%%#$(php artisan key:generate --show --no-ansi)#" .env.gae
    
    On Linux, use this command instead:
    
        sed -i "s#%%APP_KEY%%#$(php artisan key:generate --show --no-ansi)#" .env.gae

1.  Modify `bootstrap/app.php` by adding the following block of code before the
    return statement. This will allow you to change storage path using an 
    environment variable. We will redirect all runtime storage into the `/tmp` 
    directory, which is the only writable directory for App Engine applications.

        # [START] Add the following block to `bootstrap/app.php`
        /*
        |--------------------------------------------------------------------------
        | Set Storage Path
        |--------------------------------------------------------------------------
        |
        | This script allows you to override the default storage location used by
        | the  application.  You may set the APP_STORAGE environment variable
        | in your .env file,  if not set the default location will be used
        |
        */
        $app->useStoragePath(env('APP_STORAGE', base_path() . '/storage'));
        # [END]

    If you've added the code correctly, your file [will look like this][bootstrap-app-php].

    In this tutorial we will actually be hard-coding storage path in later 
    step, so the `APP_STORAGE` configuration remains only for testing locally. 
    This is because `env()` function should not be called after caching Laravel 
    configuration, which we will be doing later.
    
    Still, don't skip this step, and don't modify the characters within 
    `useStoragePath(...)`, as they will be matched and substituted by `sed` 
    later on.

1.  Modify `public/index.php` by adding the following block of code after the 
    definition of `'LARAVEL_START'`. This helps to avoid the error when Laravel 
    tries to write into storage directory that does not exist.

    We have to do this at runtime because each instance in App Engine gets its 
    own writable in-memory `/tmp` directory. Creating these directories during 
    deployment would be a waste of time, because the runtime version of `/tmp` 
    is not yet mounted at that time.

        # [START] Add the following block to `public/index.php`
        /*
        |--------------------------------------------------------------------------
        | GCP App Engine Writable Directories
        |--------------------------------------------------------------------------
        |
        | Before we start up Laravel, let's check if we are running in GCP App Engine,
        | and, if so, make sure that the Laravel's storage directory structure is
        | present.
        |
        */

        if (getenv('GCP_APP_ENGINE_LARAVEL')
            && !file_exists('/tmp/.dirs_created')) {
            foreach (['/tmp/app/public',
                        '/tmp/framework/cache/data',
                        '/tmp/framework/sessions',
                        '/tmp/framework/testing',
                        '/tmp/framework/views',
                        '/tmp/logs'] as $tmpdir) {
                if (!file_exists($tmpdir)) {
                    mkdir($tmpdir, 0755, true);
                }
            }
            touch('/tmp/.dirs_created');
        }
        # [END]
    
    This code is where the `GCP_APP_ENGINE_LARAVEL` environment variable from 
    `app.yaml` comes into play. This avoids running this code in local 
    development environment.

    If your code writes into any storage directory, you should make sure to 
    create the necessary directory structure here.

1.  Modify `composer.json` file by adding a few scripts scripts. To do this 
    automatically, use the following commands:

        composer config scripts.post-autoload-dump "Illuminate\Foundation\ComposerScripts::postAutoloadDump" "mkdir -p bootstrap/cache" "@php artisan package:discover --ansi"
        composer config scripts.gcp-build "sed -i -e \"s|env('APP_STORAGE', base_path() . '/storage')|'/tmp'|g\" bootstrap/app.php && mkdir -p /tmp/framework/views && mv .env.gae .env && php artisan config:cache && rm -f .env && php artisan route:cache"

    In the end your `"scripts"` section should look similar to this:

        "scripts": {
            "post-autoload-dump": [
                "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
                "mkdir -p bootstrap/cache",
                "@php artisan package:discover --ansi"
            ],
            "post-root-package-install": [
                "@php -r \"file_exists('.env') || copy('.env.example', '.env');\""
            ],
            "post-create-project-cmd": [
                "@php artisan key:generate --ansi"
            ],
            "gcp-build": "sed -i -e \"s|env('APP_STORAGE', base_path() . '/storage')|'/tmp'|g\" bootstrap/app.php && mkdir -p /tmp/framework/views && mv .env.gae .env && php artisan config:cache && rm -f .env && php artisan route:cache"
        }
    
    In `"scripts"` -> `"post-autoload-dump"` we add the following script right 
    before `package:discover` command to ensure that the package discovery 
    command has the directory to write into:

        ...
        "mkdir -p bootstrap/cache",
        ...
    
    In `"scripts"` we add the `"gcp-build"` field, which is a (currently 
    undocumented) way of running custom logic during deployment to App Engine.

        ...
        "gcp-build": "sed -i -e \"s|env('APP_STORAGE', base_path() . '/storage')|'/tmp'|g\" bootstrap/app.php && mkdir -p /tmp/framework/views && mv .env.gae .env && php artisan config:cache && rm -f .env && php artisan route:cache"
        ...
    
    Unfortunately at this time App Engine does not support an array of commands 
    under `"gcp-build"`. Here are the details on the chained commands:

    -   `sed -i -e \"s|env('APP_STORAGE', base_path() . '/storage')|'/tmp'|g\" bootstrap/app.php`

        This will remove a call to `env()` function and hard-code the storage 
        directory path. This is required because we will be caching Laravel 
        configuration, after which calls to `env()` will only return `null`.

    -   `mkdir -p /tmp/framework/views`

        As stated above, manipulating `/tmp` directory during deployment is a 
        waste of time, but we do it anyway, in order for Laravel config to be 
        cached properly. In `config/view.php` the path to compiled views is 
        calculated by calling `realpath()` which returns an empty string if the 
        directory does not exist at the time of calling.
    
    -   `mv .env.gae .env`

        Moving our GCP configuration into place, from where it will be cached.
    
    -   `php artisan config:cache`

        Caching Laravel configuration into `bootstrap/cache/config.php`. We can 
        do that because the filesystem becomes read-only only at runtime.

    -   `rm -f .env`

        Removing now-useless configuration. This is mostly a symbolic gesture, 
        as the values will still be visible to persons browsing the deployed 
        source code, under `bootstrap/cache/config.php`.
    
    -   `php artisan route:cache`

        Caching Laravel routes into `bootstrap/cache/route-v7.php`.

    -   We don't pre-cache views because:
    
        -   It would only make sense to cache them into `/tmp` directory, 
            since they must remain writable in runtime. For example, 
            Laravel will create cached versions of its custom error views 
            only at runtime.
        -   The version of `/tmp` during deployment is not the same as the one 
            that is mounted at runtime.
        -   Instead of pre-caching, Laravel will gradually generate cached 
            versions of views as they are first served.
    
    -   We don't optimize autoloader because it's already done. Laravel's 
        `composer.json` includes configuration `"optimize-autoloader": true`, 
        which forces Composer to run this optimization after every `install` 
        command. App Engine automatically calls this on every deployment:
        
            composer install --no-dev --no-progress --no-suggest --no-interaction

1.  Run the following command to deploy your app:

        gcloud app deploy --no-cache

1.  Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Laravel welcome page.
    Replace `YOUR_PROJECT_ID` with the ID of your Google Cloud project.

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

    *   Enable the [Cloud SQL Admin API][cloudsql-admin-api] in order to use the
        Cloud SQL Proxy Client.

    *   Use the [Google Cloud SDK][cloud_sdk] from the command line to run the
        following command. Copy the `connectionName` value for the next step. Replace
        `YOUR_INSTANCE_NAME` with the name of your instance:

            gcloud sql instances describe YOUR_INSTANCE_NAME | grep connectionName

    *   Start the Cloud SQL proxy and replace `YOUR_CONNECTION_NAME` with the
        connection name you retrieved in the previous step.

            ./cloud_sql_proxy -instances=YOUR_CONNECTION_NAME=tcp:3306

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

1.  Modify your `.env.gae` file with the following contents:

        APP_KEY=%%APP_KEY%%
        APP_ENV=production
        APP_DEBUG=false

        CACHE_DRIVER: database
        SESSION_DRIVER: database

        ## Set these environment variables according to your CloudSQL configuration.
        DB_DATABASE: YOUR_DB_DATABASE
        DB_USERNAME: YOUR_DB_USERNAME
        DB_PASSWORD: YOUR_DB_PASSWORD

        ## for MYSQL, use DB_SOCKET:
        DB_SOCKET: "/cloudsql/YOUR_CONNECTION_NAME"
        ## for PostgreSQL, use DB_HOST:
        # DB_HOST: "/cloudsql/YOUR_CONNECTION_NAME"

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
    `config/logging.php`:

        'channels' => [

            // Add the following lines to integrate with Stackdriver:
            'stackdriver' => [
                'driver' => 'custom',
                'via' => App\Logging\CreateStackdriverLogger::class,
                'level' => 'debug',
            ],

    If you've added the code correctly, your file [will look like this][config-logging-php].

1.  Modify your `.env.gae` file to set the `LOG_CHANNEL` environment variable to
    the value `stackdriver`:

        LOG_CHANNEL=stackdriver
        # The rest of your environment variables remain unchanged below
        # ...

1.  Now you can log to Stackdriver Logging anywhere in your application!

        Log::info("Hello Stackdriver! This will show up as log level INFO!");

    For example, add the following route to `routes/web.php` and browse to
    `/log/some-message-here` to see a log entry in Logging:

        Route::get('/log/{message}', function ($message) {
            Log::info("Hello my log, message: $message");
            return view('welcome');
        });

    These entries appear in the log of the request they occurred under,
    as well as in the individual log specified by their log name (`app`, in this
    case).

    **Note**: The first time you deploy, you may get the log message `This
    request caused a new process to be started for your application, and thus
    caused your application code to be loaded for the first time. This request
    may thus take longer and use more CPU than a typical request for your
    application.`. If you see this, ignore it and make a second request. On your
    next request, your logged message should appear in the logs as expected.

### Stackdriver Error Reporting

You can send error reports to Stackdriver Error Reporting from PHP applications by using the
[Stackdriver Error Reporting library for PHP][stackdriver-error-reporting-php].

1.  Add the following `use` statement at the beginning of the file
    [`app/Exceptions/Handler.php`][app-exceptions-handler-php]:

        use Google\Cloud\ErrorReporting\Bootstrap;

1.  Edit the `report` function in the same file `app/Exceptions/Handler.php` as 
    follows:

        public function report(Throwable $e)
        {
            if (isset($_SERVER['GAE_SERVICE'])) {
                $this->reportToStackdriver($e);
            } else {
                parent::report($e);
            }
        }
    
1.  Below in the same file `app/Exceptions/Handler.php`, implement the function 
    `reportToStackdriver()` like so:

        private function reportToStackdriver(Throwable $e)
        {
            $e = $this->mapException($e);

            if ($this->shouldntReport($e)) {
                return;
            }

            if (Reflector::isCallable($reportCallable = [$e, 'report'])) {
                if ($this->container->call($reportCallable) !== false) {
                    return;
                }
            }

            foreach ($this->reportCallbacks as $reportCallback) {
                if ($reportCallback->handles($e)) {
                    if ($reportCallback($e) === false) {
                        return;
                    }
                }
            }

            Bootstrap::init();
            Bootstrap::exceptionHandler($e);
        }
    
    Most of the code in `reportToStackdriver()` function is lifted directly 
    from the `parent::report()` function. We resort to this to retain the 
    benefit of Laravel's built-in Exception handling. For example, with this 
    copy-pasted code, thanks to Laravel's handling we will not be getting 
    alerts for `NotFoundHttpException`'s in Stackdriver Error Reporting every 
    time someone mistypes the URL and gets a 404.

1.  Now any PHP Exception will be logged to Stackdriver Error Reporting!

        throw new \Exception('PHEW! We will see this in Stackdriver Error Reporting!');

    For example, add the following route to `routes/web.php` and browse to
    `/exception/my-test-exception` to see an exception appear in Error Handling:

        Route::get('/exception/{message}', function ($message) {
            throw new Exception("Intentional exception, message: $message");
        });

## Secrets

The `.env.gae` file will likely end up containing production credentials and 
secrets, which are best kept out of version control. We can achieve this by 
using [Cloud Build][cloud-build] in combination with [Cloud Secret Manager][cloud-secret-manager].

Creating and versioning secrets is outside of the scope of this tutorial, but 
can be easily done [in the UI][cloud-secret-manager-ui].

To give an example, we will go back to our original version of `.env.gae`:

    APP_KEY=%%APP_KEY%%
    APP_ENV=production
    APP_DEBUG=false

Now, instead of manually substituting the `%%APP_KEY%%` value, we will keep our 
secret in Secret Manager and paste it in securely during deployment.

Create a file `cloudbuild.yaml` with the following content:

    steps:
        - name: gcr.io/google.com/cloudsdktool/cloud-sdk
            entrypoint: bash
            args:
            - -c
            - sed -i -e "s#%%APP_KEY%%#$$APP_KEY#g" .env.gae && gcloud app deploy --no-cache
            secretEnv:
            - APP_KEY
    timeout: 1600s
    availableSecrets:
        secretManager:
            - versionName: projects/<PROJECT-ID>/secrets/<SECRET-NAME>/versions/<SECRET-VERSION>
            env: APP_KEY

We use `sed` to paste the secrets. The secret values do not show up in the 
Cloud Build log. Substitute `<PROJECT-ID>`, `<SECRET-NAME>`, and 
`<SECRET-VERSION>` with appropriate values. You also need to give Cloud Build 
permission to access secrets, as detailed in [documentation][cloud-build-with-secrets].

**Note**: The secrets in unencrypted form **will** be visible in the source 
code of deployed App Engine application. Be mindful about who has the 
`appengine.versions.getFileContents` permission or the 
`roles/appengine.codeViewer` role.

In this set-up, deploy your App Engine Laravel application using:

    gcloud builds submit

You can even set up a [trigger][cloud-build-triggers] to automatically deploy 
to App Engine, e.g., on commit to the `main` branch.


[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[laravel-install]: https://laravel.com/docs/8.x/installation
[laravel-welcome]: welcome-page.png
[cloud_sdk]: https://cloud.google.com/sdk/
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-admin-proxy#install
[cloudsql-admin-api]: https://console.cloud.google.com/flows/enableapi?apiid=sqladmin
[laravel-framework-sample]: https://github.com/GoogleCloudPlatform/php-docs-samples/tree/master/appengine/standard/laravel-framework
[bootstrap-app-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/standard/laravel-framework/bootstrap/app.php
[app-dbsessions-yaml]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/standard/laravel-framework/app-dbsessions.yaml
[app-logging-createstackdriverlogger-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/standard/laravel-framework/app/Logging/CreateStackdriverLogger.php
[config-logging-php]: https://github.com/GoogleCloudPlatform/php-docs-samples/blob/master/appengine/standard/laravel-framework/config/logging.php
[stackdriver-error-reporting-php]:http://googleapis.github.io/google-cloud-php/#/docs/cloud-error-reporting/v0.12.3/errorreporting/readme
[cloud-build]: https://cloud.google.com/cloud-build
[cloud-secret-manager]: https://cloud.google.com/secret-manager
[cloud-build-with-secrets]: https://cloud.google.com/cloud-build/docs/securing-builds/use-secrets
[cloud-build-triggers]: https://cloud.google.com/cloud-build/docs/automating-builds/create-manage-triggers
[cloud-secret-manager-ui]: https://console.cloud.google.com/security/secret-manager
