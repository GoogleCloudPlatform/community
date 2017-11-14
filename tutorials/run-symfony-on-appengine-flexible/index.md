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

1.  Create an `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: web
          front_controller_file: app.php

1.  Replace `post-install-cmd` in `composer.json` with the following script:

        "post-install-cmd": [
            "chmod -R ug+w $APP_DIR/var"
        ],

    In the context of Symfony's `composer.json`, it will look like this:

    ![Add post-install-cmd scripts to composer.json][composer-json]

1. Run the following command to deploy your app:

        gcloud app deploy

1. Visit `http://YOUR_PROJECT_ID.appspot.com` to see the Symfony welcome page!

    ![Symfony welcome page][symfony-welcome]

## Connect to CloudSQL with Doctrine

### Setup

1. Follow the instructions to set up a
   [Google Cloud SQL Second Generation instance for MySQL][cloudsql-create].

1. Follow the instructions to
   [install the Cloud SQL proxy client on your local machine][cloudsql-install].
   The Cloud SQL proxy is used to connect to your Cloud SQL instance when
   running locally.

1.  Enable the [CloudSQL APIs][cloudsql-apis] in your project.

1.  Use the [Cloud SDK][cloud_sdk] from the command line to run the following
    command. Copy the `connectionName` value for the next step. Replace
    `YOUR_INSTANCE_NAME` with the name of your instance:

        gcloud sql instances describe YOUR_INSTANCE_NAME

1.  Start the Cloud SQL proxy and replace `YOUR_INSTANCE_CONNECTION_NAME` with
    the connection name you retrieved in the previous step:

        cloud_sql_proxy -instances=YOUR_INSTANCE_CONNECTION_NAME=tcp:3306 &

    **Note:** Include the `-credential_file` option when using the proxy, or
    authenticate with `gcloud`, to ensure proper authentication.

### Configure

1.  Modify `app/config/parameters.yml` so the database fields pull from
    environment variables. We've also added some default values for environment
    variables which are not needed for all environments. Notice we've added the
    parameter `database_socket`, as Cloud SQL uses sockets to connect:

        parameters:
            database_host: '%env(DB_HOST)%'
            database_name: '%env(DB_DATABASE)%'
            database_port: '%env(DB_PORT)%'
            database_user: '%env(DB_USERNAME)%'
            database_password: '%env(DB_PASSWORD)%'
            database_socket: '%env(DB_SOCKET)%'

            # Set sane environment variable defaults.
            env(DB_HOST): ""
            env(DB_PORT): 3306
            env(DB_SOCKET): ""

            # Mailer configuration
            # ...

1.  Modify your Doctrine configuration in `app/config/config.yml` and add a line
    for "unix_socket" using the parameter we added:

        # Doctrine Configuration
        doctrine:
            dbal:
                driver: pdo_mysql
                host: '%database_host%'
                port: '%database_port%'
                dbname: '%database_name%'
                user: '%database_user%'
                password: '%database_password%'
                charset: UTF8
                # add this parameter
                unix_socket: '%database_socket%'

            # ORM configuration
            # ...

1.  Use the symfony CLI to connect to your instance and create a database for
    the application. Be sure to replace `YOUR_DB_PASSWORD` below with the root
    password you configured:

        # create the database using doctrine
        DB_HOST="127.0.0.1" DB_DATABASE=symfony DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD \
            php bin/console doctrine:database:create

1.  Modify your `app.yaml` file with the following contents:

        runtime: php
        env: flex

        runtime_config:
          document_root: web
          front_controller_file: app.php

        env_variables:
          ## Set these environment variables according to your CloudSQL configuration.
          DB_DATABASE: symfony
          DB_USERNAME: root
          DB_PASSWORD: YOUR_DB_PASSWORD
          DB_SOCKET: "/cloudsql/YOUR_CLOUDSQL_CONNECTION_NAME"

        beta_settings:
          # for Cloud SQL, set this value to the Cloud SQL connection name,
          # e.g. "project:region:cloudsql-instance"
          cloud_sql_instances: "YOUR_CLOUDSQL_CONNECTION_NAME"

1.  Replace each instance of `YOUR_DB_PASSWORD` and
    `YOUR_CLOUDSQL_CONNECTION_NAME` with the values you created for your Cloud
    SQL instance above.

### Run

1.  In order to test that our connection is working, modify the Default
    Controller in `src/AppBundle/Controller/DefaultController.php` so that it
    validates our Doctrine connection:

        namespace AppBundle\Controller;

        use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
        use Symfony\Bundle\FrameworkBundle\Controller\Controller;
        use Symfony\Component\HttpFoundation\Request;

        class DefaultController extends Controller
        {
            /**
             * @Route("/", name="homepage")
             */
            public function indexAction(Request $request)
            {
                $entityManager = $this->get('doctrine.orm.entity_manager');
                if ($entityManager->getConnection()->connect()) {
                    echo 'DOCTRINE WORKS';
                }
                // replace this example code with whatever you need
                return $this->render('default/index.html.twig', [
                    'base_dir' => realpath($this->getParameter('kernel.project_dir')).DIRECTORY_SEPARATOR,
                ]);
            }
        }

1.  Now you can run locally and verify the connection works as expected.

        DB_HOST="127.0.0.1" DB_DATABASE=symfony DB_USERNAME=root DB_PASSWORD=YOUR_DB_PASSWORD \
            php bin/console server:run

1.  Reward all your hard work by running the following command and deploying
    your application to App Engine:

        gcloud app deploy

[php-gcp]: https://cloud.google.com/php
[laravel]: http://laravel.com
[laravel-install]: https://laravel.com/docs/5.4/installation
[laravel-welcome]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/welcome-page.png
[cloud_sdk]: https://cloud.google.com/sdk/
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-laravel-on-appengine-flexible/composer-json.png
[cloudsql-create]: https://cloud.google.com/sql/docs/mysql/create-instance
[cloudsql-install]: https://cloud.google.com/sql/docs/mysql/connect-external-app#install
[cloudsql-apis]:https://pantheon.corp.google.com/apis/library/sqladmin.googleapis.com/?pro

[create-project]: https://cloud.google.com/resource-manager/docs/creating-managing-projects
[enable-billing]: https://support.google.com/cloud/answer/6293499?hl=en
[php-gcp]: https://cloud.google.com/php
[symfony]: http://symfony.com
[symfony-install]: http://symfony.com/doc/current/setup.html
[symfony-welcome]: https://symfony.com/doc/current/_images/welcome.png
[composer-json]: https://storage.googleapis.com/gcp-community/tutorials/run-symfony-on-appengine-flexible/composer-json.png
