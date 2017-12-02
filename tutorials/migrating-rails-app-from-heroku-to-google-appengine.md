---
title: Migrating a Rails App from Heroku to Google App Engine
description: Learn how to move a Rails application from Heroku to Google App Engine by following an example migration of a Spree e-commerce app.
author: dazuma
tags: App Engine, Ruby, Rails, Heroku, Migration
date_published: 2017-12-18
---

This tutorial walks through the process of migrating a typical
[Ruby on Rails](http://rubyonrails.org) application from
[Heroku](https://heroku.com/) to
[Google App Engine](https://cloud.google.com/appengine/). You can use an
ecommerce app built with [Spree](https://spreecommerce.org/), or your own app
using Rails and Postgres.

In this tutorial, you will:

*   Start with an app deployed to Heroku.
*   Migrate the Postgres database to Google Cloud SQL.
*   Migrate application configuration to Google Cloud for use by App Engine.
*   Learn how to deploy and maintain the app on App Engine.

## Before you begin

Before running this tutorial, take the following steps to set up your Google
Cloud project and tools.

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project. Remember the name of this project
    (generally three words or numbers separated by hyphens). We will refer to
    the project as `${PROJECT_ID}` when we need it later in this tutorial.

2.  Enable billing for your project.

3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

4.  Install client tools for [Postgres](https://www.postgresql.org/download/).
    You will need Postgres 9.6 or later.

You should also start with an app deployed to Heroku, using a Heroku-hosted
Posgres database. If you do not have your own app, you can use a default
ecommerce app based on Spree. The Spree website provides a
[basic guide](https://guides.spreecommerce.org/developer/heroku.html) you can
use to set this up.

## Moving your database to Google Cloud SQL

Your first step is to reproduce your Heroku database using Google Cloud SQL. In
this section, you will create a new Google Cloud SQL database, and copy the
data from your existing Heroku database. You will also learn about some tools
you can use to manage your Google Cloud SQL database.

Heroku provides commands to dump a database contents to your local workstation,
and Google Cloud provides commands to upload a dump file to Google Cloud SQL.
Unfortunately, the two commands curently don't speak the same language; Heroku
export produces "custom format" files, whereas Google import requires plain
text format. For this tutorial, you will bypass Google's import command, and
instead learn how to connect directly to the Google Cloud SQL database so you
can `pg_restore` to it directly.

### Create a Cloud SQL database

Your first step is to provision and create a new Google Cloud SQL database.

1.  Create a Google Cloud SQL instance. Create a Postgres database because
    you are migrating data from a Postgres database on Heroku.

        gcloud sql instances create mydbinstance \
          --database-version=POSTGRES_9_6 --tier=db-g1-small

    At the time of this writing, Heroku Postgres databases use Postgres 9.6 by
    default. If that changes, you may need to create a Cloud SQL instance with
    a newer version.

2.  Get the connection name for your new instance, as you will need it later.
    The connection name is a string that looks something like
    `${PROJECT_ID}:us-central1:mydbinstance`. You can find it by running:

        gcloud sql instances describe mydbinstance

    and looking at the `connectionName` field. We will refer to the connection
    name as `${DB_CONNECTION_NAME}` when we need it later in this tutorial.

3.  Secure your new database instance by setting a password on the default
    postgres user. Execute this command and type a password at the prompt:

        gcloud sql users set-password postgres no-host \
          --instance=mydbinstance --prompt-for-password

4.  Create a database:

        gcloud sql databases create mydb --instance=mydbinstance

For now your database will be owned by the default user `postgres`. You can
change the ownership to an unprivileged user later, but for now you should
keep the default to ensure the data migration steps go smoothly.

### Connect to your Cloud SQL instance

By default, Google Cloud SQL instances are locked down, requiring your IP
address to be whitelisted in order to connect using the standard Postgres
protocols. Although this is a security best practice, it does make it difficult
to establish _ad hoc_ database connections.
To mitigate this problem, Cloud SQL provides a tool called the
[Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy). It
opens a database endpoint that you can connect to locally, and then proxies
back to the database instance via a secure API.

You will now set up a Cloud SQL Proxy locally so you can connect to your new
database.

1.  Enable the Google Cloud SQL API in the cloud console
    [on this page](https://console.cloud.google.com/apis/library/sqladmin.googleapis.com/).

2.  Download and install the proxy, using the instructions for your OS
    [on this page](https://cloud.google.com/sql/docs/postgres/sql-proxy#install).
    Subsequent steps will assume that `cloud_sql_proxy` is in your `PATH`.

3.  The proxy will create local unix sockets connected to your database
    instances. In your Rails app directory, create a directory to hold those
    unix sockets.

        cd /path/to/my/rails/app
        mkdir -p tmp/cloudsql

4.  And start the proxy:

        cloud_sql_proxy -dir=tmp/cloudsql

    Note this will run the proxy in the foreground, so subsequent commands
    would need to be run in a separate shell. If you prefer, feel free to
    background the process instead.

5.  The Cloud SQL Proxy tool opens a unix socket in the directory
    `/path/to/my/rails/app/tmp/cloudsql/${DB_CONNECTION_NAME}/`. You can then
    connect to the database simply by pointing at that socket. If you like, you
    can test connecting with psql:

        psql -h /path/to/my/rails/app/tmp/cloudsql/${DB_CONNECTION_NAME} \
          -U postgres

### Copy data from Heroku to Cloud SQL

Now that you have a way to connect directly to your database instance, you can
copy the data over from heroku.

1.  Dump the contents of the heroku database:

        heroku pg:backups:capture
        heroku pg:backups:download

    Those commands should create a file `latest.dump` in the current directory.

2.  Restore the data to your Cloud SQL database. Use the socket provided by
    the Cloud SQL Proxy to connect to the database instance.

        pg_restore --verbose --clean --no-acl --no-owner -d mydb -U postgres \
          -h /path/to/my/rails/app/tmp/cloudsql/${DB_CONNECTION_NAME} \
          latest.dump

There will probably be some warnings during the migration, but if there are no
outright errors, your database should now be migrated!

When you are done, you may terminate the `cloud_sql_proxy` process.

## Configuring your app for Google App Engine

Google App Engine prefers to be more explicit than Heroku does when it comes
to configuration. In this section, you will learn how to find the key
configuration parameters in your Heroku deployment and transfer them to Google
App Engine.

### Create the app config file

Google App Engine deployment controlled by a file called `app.yaml`. Create
this file in your Rails application directory, and include these contents:

    env: flex
    runtime: ruby

This tells App Engine that your application should be deployed to the
[Flexible Environment](https://cloud.google.com/appengine/docs/flexible/)
using the [Ruby Runtime](https://cloud.google.com/appengine/docs/flexible/ruby/runtime).

The Ruby Runtime selects the OS software needed to run a Ruby app, similar to
a Ruby buildpack for Heroku. It also enables some Ruby-specific analysis and
behavior, as you will see later.

### Configure the database connection

Heroku handles database configuration by injecting a connection URL into the
environment. Google App Engine uses the more traditional approach of using
fields in the `database.yml` file. This section steps you through setting up
your database configuration.

1.  Configure the App Engine runtime to connect to your database. To do this,
    add the following to your `app.yaml` file:

        beta_settings:
          cloud_sql_instances: ${DB_CONNECTION_NAME}

    Replace `${DB_CONNECTION_NAME}` with the connection name you obtained
    earlier. It is also possible to connect to multiple database instances,
    by providing multiple connection names delimited by commas.

2.  When App Engine connects to a database, it launches the Cloud SQL Proxy,
    which provides access by opening unix sockets in the `/cloudsql` directory.
    Your app should connect to the appropriate sockets. Edit the production
    configuration in your `database.yml` as follows:

        production:
          adapter: postgresql
          encoding: unicode
          pool: 5
          timeout: 5000
          host: "/cloudsql/${DB_CONNECTION_NAME}"
          database: mydb
          username: postgres
          password: <%= ENV['DATABASE_PASSWORD'] %>

    Again, make sure you replace `${DB_CONNECTION_NAME}` with your actual
    database connection name.

    Notice we're reading the password from an environment variable. We'll set
    that up below when we deal with secrets.

### Configure the entrypoint

The _entrypoint_ is the command run to start your application. For example,
`bundle exec rails s`. Heroku sometimes can infer an entrypoint for a Ruby
applications, but they recommend that you provide explicit boot instructions
via a [Procfile](https://devcenter.heroku.com/articles/procfile).

Similarly, Google App Engine can often infer an entrypoint, but recommends that
you explicitly provide a command to run to start your application. To do so,
provide the command in the `entrypoint` field of the `app.yaml` file. Add this
line to your `app.yaml` to tell it how to start your Rails app. (You may modify
it if your application boots differently.)

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
will inject into your app's runtime environment. For example:

    env_variables:
      DATABASE_USER: postgres
      RAILS_MAX_THREADS: "5"

This is useful for simple configuration. However, you will typically want to
save your `app.yaml` config file to source control, so it is not a good place
for secrets such as your database password or your `SECRET_KEY_BASE`. This
kind of sensitive data can instead be managed securely using the
[Runtime Configuration Service](https://cloud.google.com/deployment-manager/runtime-configurator/),
a Google service similar to the Heroku config system.

In your app, you probably need to manage at least two secret values: the
`DATABASE_PASSWORD`, and the `SECRET_KEY_BASE`. Let's store them in Runtime
Configuration.

1.  Enable the Runtime Config API in the Cloud Console
    [on this page](https://console.cloud.google.com/apis/library/runtimeconfig.googleapis.com/).

2.  Create a configuration called `my-env` as follows:

        gcloud beta runtime-config configs create my-env

3.  View the config values for your Heroku app.

        heroku config

    Copy the `SECRET_KEY_BASE` value so you can paste it in the next command.

4.  Set the `SECRET_KEY_BASE` in your Google Runtime Config.

        gcloud beta runtime-config configs variables set \
          --config-name=my-env --is-text \
          SECRET_KEY_BASE "VeryLongStringCopiedFromHeroku"

5.  Previously you set up your `database.yml` configuration to read from the
    `DATABASE_PASSWORD` environment variable. Set that up:

        gcloud beta runtime-config configs variables set \
          --config-name=my-env --is-text \
          DATABASE_PASSWORD ${MY_DATABASE_PASSWORD}

    Replace `${MY_DATABASE_PASSWORD}` with the password that you used to secure
    your database.

If you have any other sensitive configuration fields, copy them over in the
same way.

Next we'll instruct your application to load this configuration into
environment variables.

1.  First, add the following to your `app.yaml`:

        runtime_config:
          dotenv_config: my-env

    This tells App Engine to load the current configuration values from the
    Runtime Configuration Service and build a `.env` file in your application.
    App Engine will do this when your app is deployed. (That is, it won't
    modify the file on your workstation, but will merely include it in the
    image that gets deployed to App Engine.)

2.  Next, App Engine requires permission to load this configuration at build
    time. To grant the necessary permission, go to your
    [permissions page](https://console.cloud.google.com/iam-admin/iam/project)
    in the Cloud Console. Find the "cloudbuild" service account (which will
    have an ID that ends with `@cloudbuild.gserviceaccount.com`). This is the
    service account that performs builds on behalf of App Engine. By default
    you'll see it has "Cloud Container Builder" permission. Use the pull-down
    to grant it "Project->Editor" permission in addition.

3.  Finally, use the [dotenv](https://github.com/bkeepers/dotenv) tool to load
    the `.env` file into your environment at runtime. For a Rails app, in most
    cases, you can simply add the `dotenv-rails` gem to your Gemfile:

        gem "dotenv-rails"

Note that App Engine sets a few environment variables automatically for all
Ruby apps by default. You can find these variables documented in the
[Ruby Runtime docs](https://cloud.google.com/appengine/docs/flexible/ruby/runtime#environment_variables).

### Configure the Ruby version

Heroku determines the Ruby version that should run for your app by looking at
the ruby setting in your Gemfile. Google App Engine, by contrast, looks at the
`.ruby-version` file used by [rbenv](https://github.com/rbenv/rbenv).

If you have set a specific Ruby version for Heroku in your Gemfile, create a
corresponding `.ruby-version` file in your Rails application root directory.
For example, if the Gemfile specifies `ruby "2.4.2"`, then the contents of your
`.ruby-version` file should be a single line:

    2.4.2

Even if your Gemfile does not contain a `ruby` entry, it is still recommended
that your app provide a `.ruby-version` when running on App Engine. If you do
not specify a version, App Engine will choose a default (which is 2.3.5 at
this writing), but that default is subject to change over time.

### To summarize...

You have now moved the critical configuration over from Heroku to Google App
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

We'll now create an App Engine service and prepare for deployment.

1.  Double-check that the needed APIs are enabled and the cloudbuild service
    account has needed permissions. These steps are documented earlier in
    this tutorial. Specifically:

    *   The [Google Cloud SQL API](https://console.cloud.google.com/apis/library/sqladmin.googleapis.com/)
        should be enabled.
    *   The [Google Cloud RuntimeConfig API](https://console.cloud.google.com/apis/library/runtimeconfig.googleapis.com/)
        should be enabled.
    *   The "cloudbuild" service account should have Project Editor permissions
        in the [IAM page](https://console.cloud.google.com/iam-admin/iam/project).

2.  Create the app with

        gcloud app create

    The command will prompt you for a region. Each App Engine app is deployed
    to data centers in a particular geographic region. Generally, you should
    choose the same region where your database lives; you can find it by
    looking at the middle section of the connection name. In many cases, this
    will default to "us-central".

3.  You can now deploy your app with:

        gcloud app deploy

    This step will take a few minutes, especially on the first deployment, as
    it procures virtual machines and other cloud resources for you.

4.  Once deployment is done, if all went well, you should be able to view your
    running app with:

        gcloud app browse

Your app should now be fully transitioned to App Engine. Now, when you need to
update your app, you can simply rerun `gcloud app deploy`.

## Next steps

See the [App Engine documentation](https://cloud.google.com/appengine/docs/flexible/)
for more information on App Engine features including scaling, health checks,
and infrastructure customization.

Check out the [Stackdriver gem](https://rubygems.org/gems/stackdriver) which
activates the logging, error reporting, latency tracing, and debugging features
of App Engine.
