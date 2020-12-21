---
title: Run Symfony Hello World on App Engine standard environment for PHP 5.5
description: Run Symfony Standard on App Engine standard environment for PHP 5.5.
author: jimtravis
tags: App Engine, Symfony, PHP
date_published: 2017-02-08
---

**Note**: This tutorial uses PHP 5.5, which is EOL. Please use the tutorial
for [Running Symfony on App Engine for PHP 7.2][symfony-appengine-php72]
instead.

You can use Symfony with PHP on Google App Engine to develop your web apps.
Getting to Hello World with Symfony on App Engine takes just a few
minutes. We've provided modified source code for Symfony on GitHub. You can
download the code and deploy it to App Engine by following the steps in this
tutorial.

[Symfony](https://symfony.com)
is a set of reusable PHP components and a PHP framework for websites and web
applications.

[Google App Engine's platform-as-a-service (PaaS) features](https://cloud.google.com/appengine/)
let you easily run on Google's infrastructure, so your app can automatically
scale to serve millions of users, while keeping your costs under control.

## Objectives

* Download the App Engine [Symfony Starter Project](https://github.com/GoogleCloudPlatform/appengine-symfony-starter-project).
* Run Hello World.
* Understand the source code.

## Prerequisites

* Develop using Mac OS X or Microsoft Windows.

* [Install Git](https://git-scm.com/downloads).

* [Install Composer](https://getcomposer.org/).
This tutorial assumes that you followed the instructions to [install Composer
globally](https://getcomposer.org/doc/00-intro.md#globally).
Ensure that your system meets the [system requirements](https://getcomposer.org/doc/00-intro.md#system-requirements).
Composer will require that your PHP installation supports
[cURL](http://php.net/manual/en/book.curl.php).

* Install and then initialize the
 [Google Cloud SDK](https://cloud.google.com/sdk/docs).

* Create a new Google Cloud Platform project or retrieve the project ID of
an existing project from the [Google Cloud Platform Console](https://console.cloud.google.com/iam-admin/projects). You can retrieve a
list of your existing project IDs by using the `gcloud` command-line tool. From the command line, run:

        gcloud projects list

## Deploying Hello World with Symfony on App Engine

To deploy Symfony to App Engine, follow these steps.

### Get the source code

1. Download the modified source code from GitHub. In a
terminal window, enter the following command:

        composer create-project google/appengine-symfony-starter-project

1. Change the current directory.

        cd appengine-symfony-starter-project

### Run the app on your local computer

The following steps will serve your application on `http://localhost:8080` using
the script `dev_appserver.py`, which was installed with the Google Cloud SDK.

1. Run the following command from the root of the project:

        composer run-script server --timeout=0

    This step is critical, as App Engine uses a read-only filesystem, so the
    cache files must be written first.

1. After the instance starts, open your browser to `http://localhost:8080`.

1. When the page loads, you see a simple text message that says
**Homepage.**, which is Symfony's "hello world" text.

If the page fails to load, select **Logs** in the Google App Engine
Launcher to see what error conditions caused the failure.

### Deploy the app to the cloud

1. To deploy the code to App Engine, enter the following command:

        composer run-script deploy --timeout=0

    Just like above, this script warms the Symfony file cache before deploying
    to App Engine, as App Engine uses a read-only filesystem.

1. When the deployment finishes, your app will be serving traffic at
`http://[YOUR_PROJECT_ID].appspot.com`.

    You can run the following command to open your browser to your app's URL:

        gcloud app browse

1. When the page loads, you will see the message: **Homepage**.

If the page fails to load,
[check the logs](https://console.cloud.google.com/project/_/logs).

### Building the Cache

This application includes two helper scripts, [`scripts/deploy.php`][deploy]
and [`scripts/server.php`][server], which can be run with `composer run-script`.
Both of these are used to prime the file cache, which is required for the
application to run due to App Engine Standard's read-only filesystem. The
scripts are convenient wrappers for Symfony's `cache:clear` and `cache:warmup`
commands, and are the equivalent to the following:

```sh
# This is equivalent to running `composer run-script server`
app/console cache:clear --no-debug --env=dev
app/console cache:warmup --no-debug --env=dev
dev_appserver.py .
```

```sh
# This is equivalent to running `composer run-script deploy`
app/console cache:clear --no-debug --env=prod
app/console cache:warmup --no-debug --env=prod
gcloud app deploy
```

[deploy]: https://github.com/GoogleCloudPlatform/appengine-symfony-starter-project/blob/master/scripts/deploy.php
[server]: https://github.com/GoogleCloudPlatform/appengine-symfony-starter-project/blob/master/scripts/server.php

## Using Cloud Storage as your Filesystem

### Setup

App Engine doesn't provide access to a file system, like the one you might
use on a local computer or a server. You can use [Cloud Storage][cloud_storage]
in place of a local file system.

1. Create and retrieve the name of your
   [Google Cloud Storage bucket][app_engine_cloud_storage_setup].
1. Edit `app/config/parameters.yml` and replace `YOUR_GCS_BUCKET_NAME` with the
   bucket name you created above.
1. Browse to `/storage`

This script will write a file "helloworld.txt" to the Cloud Storage bucket
specified in `parameters.yml`, and then reads it back and displays it in the
browser.

By registering Cloud Storage as a stream wrapper, the `gs://` path can be used
to read and write to a Cloud Storage bucket as if it was a filesystem.

## Configuring the App Engine application

App Engine applications require a configuration file, named `app.yaml`, to
[configure the app][app_config]. The Symfony project adds this file to the code
from the original branch. In the `handlers` section of the file, you can see the
URL routing handlers for the app. For example, you'll find the handler for your
static assets and front controller there. The handlers look like this:

```yaml
handlers:
# tell appengine where our static assets live
- url: /bundles
  static_dir: web/bundles
# the symfony front controller
- url: /.*
  script: web/app.php
```

The **url** setting defines the URL that is being handled. The value for
**script** points to the file that contains the scripting code to run when the
URL is requested.

## Next steps

* Take a look at the [App Engine PHP tutorials][app_engine_php_tutorials]

[symfony-appengine-php72]: https://cloud.google.com/community/tutorials/run-symfony-on-appengine-standard
[app_config]: https://cloud.google.com/appengine/docs/standard/php/config/appref
[app_engine_php_tutorials]: https://cloud.google.com/appengine/docs/standard/php/tutorials
[cloud_storage]: https://cloud.google.com/storage/docs/overview
[cloud_storage_setup]: https://cloud.google.com/googlestorage/setup
[app_engine_cloud_storage_setup]: https://cloud.google.com/appengine/docs/php/googlestorage/setup
