---
title: How to deploy Ruby Discourse app onto Google Cloud Platform
description: Learn how to setup a Ruby Discourse app on Google Cloud Platform.
author: hxiong388
tags: App Engine, Ruby, Ruby on Rails, Discourse, Redis, Postgres
date_published: 2017-06-30
---
This tutorial shows how to create and configure a [Ruby Discourse](http://www.discourse.org/) application 
to run on Google Cloud Platform using App Engine Flex.

## Objectives

* Setup dependency components, such as Redis and Postgres on Google Cloud Platform
* Deploy a Discourse application to Google App Engine flexible environment
* Verify the application is launched properly

## Before you begin

You'll need the following:

* A Google Cloud Platform (GCP) project. You can use an existing project or click the button to create a new project
* [Ruby 2.3+ installed](https://www.ruby-lang.org/en/documentation/installation/)
* [Google Cloud SDK installed](https://cloud.google.com/sdk/downloads)
* A Redis instance running in your project. Follow [this guide](setting-up-redis.md)
  to set up Redis on Google Compute Engine. This tutorial assumes the Redis instance is running in the *default*
  network so that the App Engine services can access it without restriction. Take a note of the internal IPv4 address for later use.
* A Postgres Cloud SQL instance running in your project. Follow [this guide](https://cloud.google.com/sql/docs/postgres/create-instance)
  to create the instance. 

## Costs

This tutorial uses billable components of GCP including:

* Google App Engine flexible environment
* Google Cloud SQL instance
* Google Compute Engine instance

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. GCP users might be eligible for a
[free trial](https://cloud.google.com/free-trial).

## Configure Cloud SQL Postgres instance

We're going to create a database on the Cloud SQL Postgres instance with name `discourse`. This is going to be the production
database your Discourse app will use.

1. On Google Cloud Console, go to the [Cloud SQL Postgres](https://console.cloud.google.com/sql/instances) instance you have created.

1. Go to the **Databases** tab. Create a new database with name `discourse`.

1. Go to **Access Control** tab, and then **Users** sub-tab. Create a new user with username `discourse` and password `discourse`.

1. Go back to the **Overview** tab, and click on the **Connect using Cloud Shell** button.

1. In the popped up Cloud Shell terminal, run:

  ```sh
  $ gcloud beta sql connect <The Cloud SQL instance name> --user=discourse
  ```

1. When prompted, type in the password `discourse`

1. After connected to the instance, run

  ```sh
  discourse=> GRANT ALL PRIVILEGES ON DATABASE discourse TO discourse;
  ```

1. Close the Cloud Shell when done.

1. On the same **Overview** page, take a note of the **Instance connection name** for later use.

## Configure Discourse Rails application

You can download and install the Discourse Rails application locally 
by following the [official guide](https://github.com/discourse/discourse/blob/master/docs/DEVELOPER-ADVANCED.md). Feel free to 
also setup the local Postgres database and Redis server to test the app on your local machine in development environment. 
We'll configure the Discourse app to run on Google Cloud App Engine Flex with the production environment.

1. Under the `config/` directory in the Discourse app, create a file with name `discourse.conf`:

  ```
  # password used to access the db
  db_password = discourse

  # socket name for database connection
  db_host = /cloudsql/<Cloud SQL instance connection name>

  # Redis host addrss
  redis_host = <Redis instance internal IPv4 address>

  # enable serve_static_assets for dockerized app
  serve_static_assets = true
  ```

  This file sets configuration parameters in production environment for Discourse.

1. Edit `config/puma.rb` file, Find the line that says `APP_ROOT = '/home/discourse/discourse'`
1. Change the `'/home/discourse/discourse'` to `Rails.root`:

  ```ruby
  APP_ROOT = Rails.root
  ```
1. In the same `config/puma.rb` file, remove the line that says `daemonize true`.
   This is because we shouldn't run daemonized process in Docker container.

1. Save and close the file.


## Deploy Discourse app to App Engine Flex


1. Under the application root directory of the Discourse app, create this file with name `app.yaml`:
  ```
    runtime: ruby
    env: flex
    entrypoint: bundle exec rails s -p 8080
    beta_settings:
      cloud_sql_instances: <Cloud SQL Instance connection name>
  ```

1. In the same application root directory, run this gcloud SDK command to deploy:
  ```sh
    $ VERSION=$(date +%Y%m%dt%H%M%S); \
        gcloud app deploy --version=$VERSION --no-promote \
        && gcloud app exec --service=default -- bin/rails db:migrate \
        && gcloud app services set-traffic default $VERSION=1
  ```
  This will deploy the app to App Engine Flex, run database migration, then switch over load balancer to the new deployment.


## Verify deployment

In your local terminal, run `gcloud app browse`. This will launch a new browser window that points to your new deployment.
You should see the default Discourse welcome page.

Congratulations, you have successfully set up Discourse on Google App Engine Flex with Redis and Postgres!

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created on Google Cloud Platform
so you won't be billed for them in the future. The following sections describe how to delete or turn off these
resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Platform Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

### Deleting App Engine services

To delete an App Engine service:

1. In the Cloud Platform Console, go to the **[App Engine Services](https://console.cloud.google.com/appengine/services)** page.
1. Click the checkbox next to the service you wish to delete.
1. Click **Delete** at the top of the page to delete the service.

If you are trying to delete the *default* service, you cannot. Instead:

1. Click on the number of versions which will navigate you to App Engine Versions page.
1. Select all the versions you wish to disable and click **Stop** at the top of the page. This will free
   all of the Google Compute Engine resources used for this App Engine service.
