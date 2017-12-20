---
title: Migrating a Rails App from Heroku to Google App Engine
description: Learn how to move a Rails application from Heroku to Google App Engine by following an example migration of a Spree e-commerce app.
author: dazuma
tags: App Engine, Ruby, Rails, Heroku, Migration
date_published: 2017-12-18
---

This tutorial teaches you how to migrate a
[Ruby on Rails](http://rubyonrails.org) application from
[Heroku](https://heroku.com/) to
[Google App Engine](https://cloud.google.com/appengine/). You can use an
e-commerce app built with [Spree](https://spreecommerce.org/), or you can
use your own app that uses Rails and Postgres.

In this tutorial, you complete the following objectives:

*   Migrate a Heroku-based Postgres database to Google Cloud SQL.
*   Migrate a Heroku application configuration to Google Cloud for use by App Engine.
*   Learn how to deploy and maintain the app on App Engine.

## Before you begin

Before running this tutorial, take the following steps to set up your Google
Cloud Platform (GCP) project and tools:

1.  [Create a new GCP project](https://console.cloud.google.com/projectcreate).
    Remember the name of your project (generally three words or numbers separated
    by hyphens). We refer to the project as `[PROJECT-ID]` throughout this tutorial.
    When you create a project, GCP automatically enables the Cloud SQL API.

1.  [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project)
    for your project.

1.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). The Cloud SDK
    contains the `gcloud` command-line tool, which is the primary tool for
    interacting with GCP.
    
1.  [Initialize the `gcloud` command-line tool](https://cloud.google.com/sdk/docs/initializing) by
    running `gcloud init` from your shell or terminal. Set the default project to the project you
    created. Configure Google Compute Engine to set the default _compute zone_ to a zone in your
    nearest geographical region, such as `us-central1-a`. We refer to the compute zone as
    `[COMPUTE-ZONE]` throughout this tutorial.

1.  Install client tools for [Postgres](https://www.postgresql.org/download/).
    For this tutorial, you need Postgres 9.6 or later.

1.  Deploy an app to Heroku, using a Heroku-hosted Posgres database. If you do not have
    your own app, you can use a default e-commerce app based on Spree. Spree provides a
    [basic guide](https://guides.spreecommerce.org/developer/heroku.html) you can 
    use to set this up.

## Moving your database to Cloud SQL

In this section, you create a new Cloud SQL database and copy the
data from your existing Heroku database. You also learn about some tools
you can use to manage your Cloud SQL database.

Heroku provides commands to export the content of a database to your local
workstation, and Google Cloud provides commands to upload files to Cloud
SQL. However, the two commands curently don't speak the same language:
Heroku export produces "custom format" files, whereas Cloud SQL requires plain
text format. For this tutorial, you instead learn how to connect directly to
the Cloud SQL database and restore your Postgres data.

### Create a Cloud SQL database

1.  Create a Cloud SQL instance named `mydbinstance` with a Postgres
    database by running the following command:

        gcloud sql instances create mydbinstance \
          --database-version=POSTGRES_9_6 --tier=db-g1-small

    Currently, Heroku Postgres databases use Postgres 9.6 by default. When
    Heroku updates the default Postgres version, you might need to create
    a Cloud SQL instance with the newer version.

1.  Get the _connection name_ for your Cloud SQL instance by running the
    following command:

        gcloud sql instances describe mydbinstance

    In the output, look for the connection name in the `connectionName` field.
    The connection name has this format: `[PROJECT-ID]:[COMPUTE-ZONE]:mydbinstance` We
    refer to the connection name as `[CONNECTION-NAME]` throughout this tutorial.

1.  Secure your new database instance by setting a password on the default
    postgres user:

        gcloud sql users set-password postgres no-host \
          --instance=mydbinstance --prompt-for-password
          
      When prompted, enter a password for the database.

1.  Create a database:

        gcloud sql databases create mydb --instance=mydbinstance

Currently, your database is owned by the default user, `postgres`. You can
change the ownership to an unprivileged user later, but for now you should
keep the default user to ensure that the data migration goes smoothly.

### Connect to your Cloud SQL instance

By default, Cloud SQL instances are secured: to connect using standard
Postgres protocols, you are required to whitelist your your IP address.
This security measure, while necessary, makes it challenging to establish
_ad hoc_ database connections.

Cloud SQL provides the [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
command-line tool, which opens a database endpoint that you can connect to locally and which
proxies back to the database instance via a secure API.

To set up Cloud SQL Proxy, perform the following steps:



1.  [Install Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy#install).
    Ensure that `cloud_sql_proxy` is in your environment's `PATH` variable.

1.  The proxy creates local sockets connected to your database instances. In your Rails app
    directory, create a directory to hold those sockets:

        cd /path/to/my/rails/app
        mkdir -p tmp/cloudsql

1.  To start the proxy, run the following command:

        cloud_sql_proxy -dir=tmp/cloudsql

    Note: This runs the proxy in the foreground, so subsequent commands
    need to be run in a separate shell. If you prefer, feel free to
    background the process instead.

5.  The proxy opens a socket in the directory
    `/path/to/my/rails/app/tmp/cloudsql/[CONNECTION-NAME]/`. You can then
    connect to the database simply by pointing at that socket. If you like, you
    can test connecting with `psql:`

        psql -h /path/to/my/rails/app/tmp/cloudsql/[CONNECTION-NAME] \
          -U postgres

### Copy data from Heroku to Cloud SQL

Now that you have a way to connect directly to your database instance, you can
copy the data over from your Heroku database.

1.  Export the contents of the Heroku database:

        heroku pg:backups:capture
        heroku pg:backups:download

    Those commands create a file `latest.dump` in the current working directory.

1.  Restore the data to your Cloud SQL database. Use the socket provided by
    the proxy to connect to the database instance:

        pg_restore --verbose --clean --no-acl --no-owner -d mydb -U postgres \
          -h /path/to/my/rails/app/tmp/cloudsql/[CONNECTION-NAME] \
          latest.dump

    Note: You might encounter permissible warnings during the migration.

1. Terminate the `cloud_sql_proxy` process.

Your database is now migrated!

## Configuring your app for App Engine

App Engine prefers to be more explicit than Heroku when it comes
to configuration. In this section, you learn how to find the key
configuration parameters in your Heroku deployment and transfer them
to App Engine.

### Create the app config file

App Engine deployments are controlled by an `app.yaml` file. Create this file
in your Rails application directory, and include these contents:

    env: flex
    runtime: ruby

This instructs App Engine to deploy your application to its
[Flexible Environment](https://cloud.google.com/appengine/docs/flexible/)
using the [Ruby Runtime](https://cloud.google.com/appengine/docs/flexible/ruby/runtime).

The Ruby Runtime selects the operating system needed to run a Ruby app, similar to
a Ruby buildpack for Heroku. It also enables some Ruby-specific analysis and
behavior.

### Configure the database connection

Heroku handles database configuration by injecting a connection URL into the
environment. App Engine uses the more traditional approach of using fields in
the `database.yml` file.

To configure your database connection, perform the following steps:

1.  Configure the App Engine runtime to connect to your database. To do this,
    add the following to your `app.yaml` file:

        beta_settings:
          cloud_sql_instances: [CONNECTION-NAME]

    where `[CONNECTION-NAME]` is your database's connection name. You can also 
    connect to multiple database instances by providing multiple, comma-delimited
    connection names.

2.  When App Engine connects to a database, it launches the Cloud SQL Proxy,
    which provides access by opening sockets in the `/cloudsql` directory.
    Your app should connect to the appropriate sockets. Edit the production
    configuration in your `database.yml` as follows:

        production:
          adapter: postgresql
          encoding: unicode
          pool: 5
          timeout: 5000
          host: "/cloudsql/[CONNECTION-NAME]"
          database: mydb
          username: postgres
          password: <%= ENV['DATABASE_PASSWORD'] %>

    Note that `password` refers to an environment variable. This is configured later
    in the tutorial.
    
### Configure the entrypoint

The entrypoint, a command such as `bundle exec rails s`, is used to start your
application. Heroku sometimes can infer an entrypoint for a Ruby
applications, but they recommend that you provide explicit boot instructions
via a [Procfile](https://devcenter.heroku.com/articles/procfile).

Similarly, App Engine can often infer an entrypoint, but recommends that
you explicitly provide a command to run to start your application. To do so,
provide the command in the `entrypoint` field of the `app.yaml` file. Add this
line to your `app.yaml` to tell it how to start your Rails app. You may modify
it if your application boots differently:

    entrypoint: bundle exec rails s -p $PORT

App Engine provides the `$PORT` environment variable for you, to tell your app
which port it should listen on. (Usually it is set to 8080.) Many web
frameworks automatically honor this environment variable, but it is good
practice to reference it explicitly in your entrypoint.

### Configure environment variables and secrets

Heroku provides a way to manage configuration via
[config vars](https://devcenter.heroku.com/articles/config-vars). It injects
them as environment variables into your app's runtime environment.

App Engine provides two ways to set environment variables, depending on how
you'd like to manage and secure the content. First, you can set them directly
in the `app.yaml` file by creating an `env_variables` section, which App Engine
injects into your app's runtime environment. For example:

    env_variables:
      DATABASE_USER: postgres
      RAILS_MAX_THREADS: "5"

This is useful for simple configuration. However, you typically want to
save your `app.yaml` config file to source control, so it is not a good place
for secrets such as your database password or your `SECRET_KEY_BASE`. This
kind of sensitive data can instead be managed securely using the
[Runtime Configuration Service](https://cloud.google.com/deployment-manager/runtime-configurator/),
a Google service similar to the Heroku config system.

In your app, you likely need to manage at least two secret values: the
`DATABASE_PASSWORD`, and the `SECRET_KEY_BASE`. Let's store them in Runtime
Configuration:

1. [Enable the Runtime Config API in the Cloud Console](https://console.cloud.google.com/apis/library/runtimeconfig.googleapis.com).

1.  Create a configuration named `my-env` by running the following command:

        gcloud beta runtime-config configs create my-env

1.  View the config values for your Heroku app:

        heroku config

    Copy the `SECRET_KEY_BASE` value so you can paste it in the next command.

1.  Set the `SECRET_KEY_BASE` in your Google Runtime Config:

        gcloud beta runtime-config configs variables set \
          --config-name=my-env --is-text \
          SECRET_KEY_BASE "VeryLongStringCopiedFromHeroku"

1.  Previously you set up your `database.yml` configuration to read from the
    `DATABASE_PASSWORD` environment variable. Set that up:

        gcloud beta runtime-config configs variables set \
          --config-name=my-env --is-text \
          DATABASE_PASSWORD [MY_DATABASE_PASSWORD]

    Replace `${MY_DATABASE_PASSWORD}` with the password that you used to secure
    your database.

If you have any other sensitive configuration fields, copy them over in the
same way.

Next we instruct your application to load this configuration into
environment variables.

1.  First, add the following to your `app.yaml`:

        runtime_config:
          dotenv_config: my-env

    This tells App Engine to load the current configuration values from the
    Runtime Configuration Service and build a `.env` file in your application.
    App Engine does this when your app is deployed. (That is, it does not
    modify the file on your workstation, but merely includes it in the
    image deployed to App Engine.)

1.  Next, App Engine requires permission to load this configuration at build
    time. To grant the necessary permission, go to your
    [permissions page](https://console.cloud.google.com/iam-admin/iam/project)
    in the Cloud Console. Find the "cloudbuild" service account (which
    has an ID that ends with `@cloudbuild.gserviceaccount.com`). This is the
    service account that performs builds on behalf of App Engine. By default
    you see it has "Cloud Container Builder" permission. Use the pull-down
    to grant it "Project->Editor" permission in addition.

1.  Finally, use the [dotenv](https://github.com/bkeepers/dotenv) tool to load
    the `.env` file into your environment at runtime. For a Rails app, in most
    cases, you can simply add the `dotenv-rails` gem to your Gemfile:

        gem "dotenv-rails"

Note that App Engine sets a few environment variables automatically for all
Ruby apps by default. You can find these variables documented in the
[Ruby Runtime docs](https://cloud.google.com/appengine/docs/flexible/ruby/runtime#environment_variables).

### Configure the Ruby version

Heroku determines the Ruby version that should run for your app by looking at
the ruby setting in your Gemfile. App Engine, by contrast, looks at the
`.ruby-version` file used by [rbenv](https://github.com/rbenv/rbenv).

If you have set a specific Ruby version for Heroku in your Gemfile, create a
corresponding `.ruby-version` file in your Rails application root directory.
For example, if the Gemfile specifies `ruby "2.4.2"`, then the contents of your
`.ruby-version` file should be a single line:

    2.4.2

Even if your Gemfile does not contain a `ruby` entry, it is still recommended
that your app provide a `.ruby-version` when running on App Engine. If you do
not specify a version, App Engine chooses a default (which is 2.3.5 at
this writing), but that default is subject to change over time.

### To summarize...

You have now moved the critical configuration over from Heroku to App
Engine. This included:

*   Creating an `app.yaml` file that:
    *   Specifies the Ruby runtime using `runtime: ruby`
    *   Connects to your database using a `cloud_sql_instances:` field
    *   Specifies the entrypoint using the `entrypoint:` field
    *   Tells App Engine to create a `.env` file using the `dotenv_config`
        field.
    *   (Optionally) adds non-secure `env_variables:` as needed by your app
*   Modifying your `database.yml` to point to your Cloud SQL database in
    production
*   Creating a Runtime Config called `my-env` and populating it with the
    `SECRET_KEY_BASE` and `DATABASE_PASSWORD` secrets
*   Adding the `dotenv-rails` gem to read the secure configs from the
    generated `.env` file
*   Creating a `.ruby-version` file that specifies which version of the Ruby
    VM should be installed.

## Deploying to App Engine

To create an App Engine service and prepare for deployment, perform the following steps:

1.  Ensure that the needed APIs are enabled and the cloudbuild service
    account has needed permissions. These steps are documented earlier in
    this tutorial. Specifically:

    *   [Cloud SQL API](https://console.cloud.google.com/apis/library/sqladmin.googleapis.com/)
        should be enabled.
    *   [Google Cloud RuntimeConfig API](https://console.cloud.google.com/apis/library/runtimeconfig.googleapis.com/)
        should be enabled.
    *   The "cloudbuild" service account should have Project Editor permissions
        in the [IAM page](https://console.cloud.google.com/iam-admin/iam/project).

2.  Create the app:

        gcloud app create

3.  Deploy your app:

        gcloud app deploy

    This step takes a few minutes, especially on the first deployment, as
    it procures virtual machines and other cloud resources for you.

4.  Once deployment is complete, you should be able to view your running app with:

        gcloud app browse

Your app should now be fully transitioned to App Engine. Now, when you need to
update your app, you can simply rerun `gcloud app deploy`.

## Next steps

* For more information about App Engine features, including scaling, health checks,
  and infrastructure customization, refer to the
  [App Engine documentation](https://cloud.google.com/appengine/docs/flexible/)

* Check out the [Stackdriver gem](https://rubygems.org/gems/stackdriver) which
  activates the logging, error reporting, latency tracing, and debugging features
  of App Engine.
