---
title: How to deploy a Ruby Discourse app on Google Cloud
description: Learn how to set up a Ruby Discourse app on Google Cloud.
author: hxiong388
tags: App Engine, Ruby, Ruby on Rails, Discourse, Redis, Postgres
date_published: 2017-06-30
---

This tutorial shows how to create and configure a [Ruby Discourse](http://www.discourse.org/) application
to run on Google Cloud using the App Engine flexible environment.

## Objectives

* Set up dependency components, such as Redis and Postgres on Google Cloud.
* Deploy a Discourse application to App Engine flexible environment.
* Verify the application is launched properly.

## Before you begin

You'll need the following:

* A Google Cloud project. You can use an existing project or click the button to create a new project.
* [Ruby 2.3+ installation](https://www.ruby-lang.org/en/documentation/installation/).
* [Cloud SDK installation](https://cloud.google.com/sdk/downloads).
* A Redis instance running in your project. To set up Redis on Compute Engine, see [Setting up Redis](setting-up-redis.md). This tutorial assumes the Redis instance is running in the *default*
  network so that the App Engine services can access it without restriction. Note the internal IPv4 address for later use.
* A Postgres Cloud SQL instance running in your project. To set up a Postgres instance, see [Creating instances](https://cloud.google.com/sql/docs/postgres/create-instance).

## Costs

This tutorial uses billable components of Google Cloud including:

* App Engine flexible environment
* Cloud SQL instance
* Compute Engine instance

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. GCP users might be eligible for a
[free trial](https://cloud.google.com/free-trial).

## Configure Cloud SQL Postgres instance

We're going to create a database named `discourse` on the Cloud SQL Postgres instance. This is going to be the production
database your Discourse app will use.

1.  In the Cloud Console, go to the [Cloud SQL Postgres](https://console.cloud.google.com/sql/instances) instance you have
    created.

1.  Go to the **Databases** tab. Create a new database with name `discourse`.

1.  Go to **Access Control** tab, and then **Users** sub-tab. Create a new user with username `discourse` and
    password `discourse`.

1.  Go back to the **Overview** tab, and click on the **Connect using Cloud Shell** button.

1.  In the Cloud Shell terminal that appears, run the following command, replacing `[Cloud_SQL_instance_name]` with the 
    name of the Cloud SQL instance:

        gcloud beta sql connect [Cloud_SQL_instance_name] --user=discourse

1.  When prompted, type in the password `discourse`.

1.  After you connect to the instance, run:

        discourse=> GRANT ALL PRIVILEGES ON DATABASE discourse TO discourse;

1.  Close the Cloud Shell when done.

1.  On the same **Overview** page, note the **Instance connection name** for later use.

## Configure Discourse Rails application

To download and install the Discourse Rails application locally,
follow the official [Discourse Advanced Developer Install Guide](https://github.com/discourse/discourse/blob/master/docs/DEVELOPER-ADVANCED.md). You can
also set up the local Postgres database and Redis server to test the app on your local machine in a development environment.
We'll configure the Discourse app to run on the App Engine flexible environment with the production environment.

1. Under the `config/` directory in the Discourse app, create a file with name `discourse.conf`:

        # password used to access the db
        db_password = discourse

        # socket name for database connection
        db_host = /cloudsql/[Cloud_SQL_instance_connection_name]

        # Redis host address
        redis_host = [Redis_instance_internal_IPv4_address]

        # enable serve_static_assets for dockerized app
        serve_static_assets = true

  This file sets configuration parameters in the production environment for Discourse.

1. Open the `config/puma.rb` file, then change `APP_ROOT = '/home/discourse/discourse':

        APP_ROOT = Rails.root

1. In the same `config/puma.rb` file, delete the line that says `daemonize true`.
   This is because we shouldn't run a daemonized process in Docker container.

1. Save and close the file.

1. Add the `appengine` gem to the application's `Gemfile`:

        gem "appengine", "~> 0.4"

1. Install the gems:

        $ bundle install

## Deploy Discourse app to the App Engine flexible environment


1.  Under the application root directory of the Discourse app, create a file named `app.yaml`:

        runtime: ruby
        env: flex
        entrypoint: bundle exec rails s -p 8080
        beta_settings:
          cloud_sql_instances: [Cloud_SQL_instance_connection_name]

1.  In the same application root directory, run this gcloud SDK command to deploy:

        VERSION=$(date +%Y%m%dt%H%M%S); \
            gcloud app deploy --version=$VERSION --no-promote \
            && bundle exec rake appengine:exec -- bundle exec rake db:migrate \
            && gcloud app services set-traffic default $VERSION=1

    This will deploy the app to the App Engine flexible environment, run database migration, and then switch the load
    balancer to the new deployment.


## Verify deployment

In your local terminal, run `gcloud app browse`. This will launch a new browser window that points to your new deployment.
You should see the default Discourse welcome page.

Congratulations, you have successfully set up Discourse on the App Engine flexible environment with Redis and Postgres!

## Cleaning up

After you've finished this tutorial, you can clean up the GCP resources you created
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

1. In the Cloud Console, go to the **[App Engine Services](https://console.cloud.google.com/appengine/services)** page.
1. Click the checkbox next to the service you wish to delete.
1. Click **Delete** at the top of the page to delete the service.

You can't delete the *default* service. Instead, do the following:

1. Click the version number, which will take you to App Engine Versions page.
1. Select all the versions you want to disable, and click **Stop** at the top of the page. This frees
   all of the Compute Engine resources used for this App Engine service.
