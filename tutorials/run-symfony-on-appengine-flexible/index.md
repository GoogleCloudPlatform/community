---
title: Run Symfony on Google App Engine Flexible Environment
description: Learn how to deploy a Symfony app to Google App Engine flexible environment.
author: bshaffer
tags: App Engine, Symfony, PHP
date_published: 2017-03-15
---
## Symfony

> [Symfony][symfony] is a set of PHP Components, a Web Application framework, a
> Philosophy, and a Community — all working together in harmony.
>
> – symfony.com

You can check out [PHP on Google Cloud Platform][php-gcp] to get an
overview of PHP itself and learn ways to run PHP apps on Google Cloud
Platform.

## Prerequisites

1. [Create a project][create-project] in the Google Cloud Platform Console
   and make note of your project ID.
1. [Enable billing][enable-billing] for your project.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Prepare

Follow the official documentation for [installing symfony][symfony-install] from
symfony.com.

## Run

1. Run the app with the following command:

        php bin/console server:run

1. Visit [http://localhost:8000](http://localhost:8000) to see the Symfony
Welcome page.

## Deploy

1. Create an `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: web

1. Create an `nginx-app.conf` file with the following contents:

        location / {
          # try to serve file directly, fallback to front controller
          try_files $uri /app.php$is_args$args;
        }

1. Add the following under "scripts" in `composer.json`:

        "post-deploy-cmd": [
            "chmod -R ug+w $APP_DIR/var"
        ]

    In the context of Symfony's `composer.json`, it will look like this:
    ![Add post-deploy-cmd scripts to composer.json][composer-json]

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Symfony welcome page!

    ![Symfony welcome page][symfony-welcome]

[create-project]: https://cloud.google.com/resource-manager/docs/creating-managing-projects
[enable-billing]: https://support.google.com/cloud/answer/6293499?hl=en
[php-gcp]: https://cloud.google.com/php
[symfony]: http://symfony.com
[symfony-install]: http://symfony.com/doc/current/setup.html
[symfony-welcome]: http://symfony.com/doc/current/_images/welcome.png
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-symfony-on-google-app-engine/composer-json.png
