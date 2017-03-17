---
title: How to Run Symfony Hello World on App Engine Standard Environment
description: Run Symfony Standard on Google App Engine standard environment. Symfony is a popular set of reusable PHP components and a PHP framework for websites and web applications.
author: jimtravis
tags: App Engine, Symfony, PHP
date_published: 2017-02-08
---

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

* Create a new Google Cloud Platform project or retrieve the project ID of
an existing project from the [Google Cloud Platform Console](https://console.cloud.google.com/iam-admin/projects). You can retrieve a
list of your existing project IDs by using the `gcloud` command-line tool. From the command line, run:

        gcloud projects list

* Install and then initialize the
 [Google Cloud SDK](https://cloud.google.com/sdk/docs).

* Create and retrieve the name of your
  [Google Cloud Storage bucket](https://cloud.google.com/appengine/docs/php/googlestorage/setup).

## Deploying Hello World with Symfony on App Engine

To deploy Symfony to App Engine, follow these steps.

### Get the source code

1. Download the modified source code from GitHub. In a
terminal window, enter the following command:

        composer create-project google/appengine-symfony-starter-project

1. Change the current directory.

        cd appengine-symfony-starter-project

### Modify the app configuration

1. Edit `app.yaml` and replace `YOUR_GCS_BUCKET_NAME` with the bucket name you
   created above.
1. Edit `php.ini` and replace `YOUR_GCS_BUCKET_NAME` with the bucket name you
   created above.

### Run the app on your local computer

To run the app locally, use Google App Engine Launcher. Follow these steps.

1. Run **GoogleAppEngineLauncher**. This application was installed with the App
   Engine SDK.

1. Select **File** > **Add Existing Application**.

1. Set "Application ID" to `appengine-symfony-starter-project`.

1. Set "Application Directory" to the *parent directory* of your project.

1. Verify "Runtime" is set to **PHP**.

1. Select **Create**. You should see the app in the list, now. Note the **Port**.

1. To start the local web server, select **Run**.

1. After the instance starts, select **Browse**. This will open a default
   browser window to `http://localhost:[PORT]`, where `[PORT]` is
   the port number of your instance, usually `8080`.

When the page loads, you see a simple text message that says
**Homepage.**, which is Symfony's "hello world" text.

Note: If the page fails to load, select **Logs** in the Google App Engine
Launcher to see what error conditions caused the failure.

### Deploy the app to the cloud

1. To deploy the code to App Engine, enter the following command:

        gcloud app deploy

1. When the deployment finishes, your app will be serving traffic at
`http://[YOUR_PROJECT_ID].appspot.com`.

    You can run the following command to open your browser to your app's URL:

        gcloud app browse

    It can take some time for the app to load for the first time, while the
    Cloud Platform Console generates cache files in Cloud Storage. When the page
    loads, you will see the message: **Homepage**.

Note: If the page fails to load,
[check the logs](https://console.cloud.google.com/project/_/logs).
If you see an error message that tells
you the Cloud Storage bucket can't be found, follow the instructions in
[Setup](https://cloud.google.com/googlestorage/setup).

#### Redeploying the app

When you redeploy your Symfony app, you might need to clear the cache afterwards.
The app includes a handler that enables you to clear the cache by browsing to
the following URL:

    http://[YOUR-PROJECT-ID].appspot.com/clear_cache.php

App Engine prompts you for your administrator credentials.

### Configuring the App Engine application

App Engine applications require a configuration file, named `app.yaml`, to
[configure the app](https://cloud.google.com/config/appconfig). The Symfony project adds this file to the
code from the original branch. In the `handlers` section of the file, you can
see the URL routing handlers for the app. For example, you'll find the handler
for the `clear_cache` command there. The handler for clearing the cache looks
like this:

    handlers:
    # a script to clear our cache
    - url: /clear_cache
      script: web/clear_cache.php
      login: admin


The **url** setting defines the URL that is being handled. The value for
**script** points to the file that contains the scripting code to run when the
URL is requested; in this case, it is `clear_cache.php`.

### Specifying the database

App Engine provides [Google Cloud SQL](https://cloud.google.com/sql/docs/)
as a managed, relational MySQL database. Cloud SQL can be used with Doctrine the
same as any other MySQL database in `app/config/config_prod.yml`.

### Overriding directories to use Cloud Storage

App Engine doesn't provide access to a file system, like the one you might
use on a local computer or a server. The Symfony app uses
[Cloud Storage](https://cloud.google.com/storage/docs/overview) in place of a local file system.

Cloud Storage organizes data storage into *buckets*, and each App Engine
application has a default bucket. In the `env_variables` section of `app.yaml`,
the declarations for `CACHE_DIR` and `LOG_DIR` specify the paths where cached
data and logs are stored.

    env_variables:
      GCS_BUCKET_NAME: "YOUR_GCS_BUCKET_NAME"

The `gs://` protocol signifies that the URI for the location is pointing to a
Cloud Storage bucket, and `#default#` is replaced by the default bucket name, at
run time. You can change the paths of these environment variables to point to
specific Cloud Storage buckets, if you prefer. For more information about the
default bucket, see [Setup](https://cloud.google.com/googlestorage/setup), in the App
Engine documentation.

## Next steps

* Try the [App Engine PHP tutorial](https://cloud.google.com/gettingstarted/introduction)
