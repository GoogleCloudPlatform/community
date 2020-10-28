---
title: Run an Elixir Phoenix app in the App Engine flexible environment
description: Learn how to deploy a Phoenix app to the App Engine flexible environment.
author: dazuma
tags: App Engine, Elixir, Phoenix
date_published: 2019-07-22
---

Daniel Azuma | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

The [App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. Using the open source
[Elixir Runtime](https://github.com/GoogleCloudPlatform/elixir-runtime), your
app written in [Elixir](http://elixir-lang.org/) with the
[Phoenix](http://phoenixframework.org/) Framework can be up and running in App
Engine in minutes.

This tutorial will help you get started deploying a Phoenix app to App Engine.
You will create a new Phoenix application, and learn how to configure, deploy,
and update it. The application will also demonstrate how to connect to a
PostgreSQL database running on [Cloud SQL](https://cloud.google.com/sql).

This tutorial requires Elixir 1.9 and Phoenix 1.4 or later. It assumes you are
already familiar with basic Phoenix web development. It also requires the
PostgreSQL database to be installed on your local development workstation.

This tutorial was updated in January 2019 to cover Phoenix 1.4, Distillery 2.0,
and connecting Ecto to a Cloud SQL database. It was updated in July 2019 to
cover changes in Elixir 1.9 and Distillery 2.1.

## Before you begin

Before running this tutorial, take the following steps:

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project.

2.  Enable billing for your project.

3.  [Enable the Cloud SQL Admin API in the Cloud Console](https://console.cloud.google.com/apis/library/sqladmin.googleapis.com/).

4.  Install the [Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

    Version 227.0.0 or later of the SDK is required. If you have an earlier
    version installed, you may upgrade it by running:

        gcloud components update

If you have not yet installed Elixir and Phoenix, do so.

1.  Install Elixir and Node.js. If you are on macOS with Homebrew, you can run:

        brew install elixir node

    Otherwise consult the [Node download](https://nodejs.org/en/download/) and
    [Elixir install](https://elixir-lang.org/install.html) guides for your
    operating system.

2. Install the hex, rebar3, and phx_new archives:

        mix local.hex
        mix local.rebar
        mix archive.install hex phx_new 1.4.9

## Create a new app and run it locally

In this section, you will create a new Phoenix app with a database, and make
sure it runs locally in development. If you already have an app to deploy, you
may use it instead.

### Create a new Phoenix app

1.  Run the `phx.new` task to create a new Phoenix project called `hello`:

        mix phx.new hello

    Answer `Y` when the tool asks you if you want to fetch and install
    dependencies.

2.  Go into the directory with the new application:

        cd hello

3.  Update the development database settings in `config/dev.exs` to specify a
    valid database user and credentials. You may also update the database name.
    The resulting configuration may look something like this:

        # Configure your database
        config :hello, Hello.Repo,
            username: "my_name",
            password: "XXXXXXXX",
            database: "hello_dev",
            hostname: "localhost",
            pool_size: 10

4.  Create the development database with the following command:

        mix ecto.create

5.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port 4000.

6.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

### Create and test a development database

Next you will populate a simple development database and verify that your
Phoenix app can access it.

1.  Create a simple schema:

        mix phx.gen.schema User users name:string email:string

2.  Migrate your development database:

        mix ecto.migrate

3.  Add some very simple code to show that the application can access the
    database, by querying for the number of user records.
    Open `lib/hello_web/controllers/page_controller.ex` and rewrite
    the `index` function as follows:

        def index(conn, _params) do
            count = Hello.Repo.aggregate(Hello.User, :count, :id)
            conn
            |> assign(:count, count)
            |> render("index.html")
        end

    You can also display the value of `@count` by adding it to the template
    `lib/hello_web/templates/page/index.html.eex`.

4.  Recompile and run the app:

        mix phx.server

5.  Visit [http://localhost:4000](http://localhost:4000) to verify that your
    new code is running. You can log into your database and add new rows, and
    reload the page to verify that the count has changed.

For more information on using Ecto to access a SQL database, see the
[Phoenix Ecto guide](https://hexdocs.pm/phoenix/ecto.html).

## Create a production database in Cloud SQL

In this section, you will create your production database using Cloud SQL, a
fully-managed database service providing PostgreSQL and MySQL in the cloud. If
you already have a database hosted elsewhere, you may skip this section, but
you may need to ensure your production configuration is set up to connect to
your database.

### Create a Cloud SQL instance

First you will create a new database in the cloud.

1.  Create a Cloud SQL instance named `hellodb` with a Postgres database
    by running the following command:

        gcloud sql instances create hellodb --region=us-central1 \
            --database-version=POSTGRES_9_6 --tier=db-g1-small

    You may choose a region other than `us-central1` if there is one closer to
    your location.

2.  Get the _connection name_ for your Cloud SQL instance by running the
    following command:

        gcloud sql instances describe hellodb

    In the output, look for the connection name in the `connectionName` field.
    The connection name has this format: `[PROJECT-ID]:[COMPUTE-ZONE]:hellodb`
    We will refer to the connection name as `[CONNECTION-NAME]` throughout this
    tutorial.

3.  Secure your new database instance by setting a password on the default
    postgres user:

        gcloud sql users set-password postgres \
            --instance=hellodb --prompt-for-password

    When prompted, enter a password for the database.

### Connect to your Cloud SQL instance

In this section you will learn how to connect to your Cloud SQL instance from
your local workstation. Generally, you will not need to do this often, but it
is useful for the initial creation and migration of your database, as well as
for creating _ad hoc_ database connections for maintenance.

By default, Cloud SQL instances are secured: to connect using the standard
`psql` tool, you must whitelist your IP address. This security measure can make
it challenging to establish _ad hoc_ database connections. So, Cloud SQL
provides a command line tool called the
[Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy). This
tool communicates with your database instance over a secure API, using your
Cloud SDK credentials, and opens a local endpoint (such as a Unix socket) that
`psql` can connect to.

To set up Cloud SQL Proxy, perform the following steps:

1.  [Install Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy#install).
    Make sure that `cloud_sql_proxy` is executable and is available in your
    environment's `PATH`.

2.  Create a directory `/tmp/cloudsql`. This is where the Cloud SQL Proxy will
    create database connection sockets. You may put this in a different
    location, but if you do, you will need to update some of the commands below
    accordingly.

        mkdir -p /tmp/cloudsql

3.  Start the proxy, telling it to open sockets in the directory you created:

        cloud_sql_proxy -dir=/tmp/cloudsql

    This runs the proxy in the foreground, so subsequent commands
    need to be run in a separate shell. If you prefer, feel free to
    background the process instead.

4.  The proxy will open a socket in the directory
    `/tmp/cloudsql/[CONNECTION-NAME]/`. You can point `psql` to that socket to
    connect to the database instance. Test this now:

        psql -h /tmp/cloudsql/[CONNECTION-NAME] -U postgres

You can learn more about using the Cloud SQL Proxy to connect to your instance
from [the documentation](https://cloud.google.com/sql/docs/postgres/connect-admin-proxy).

### Create and migrate the production database

Next you will configure your Phoenix app to point to your production database
instance, and tell Ecto to create and migrate the database.

1.  Start the Cloud SQL Proxy, if it is not already running from the previous
    section:

        cloud_sql_proxy -dir=/tmp/cloudsql

2.  Configure your production database configuration to communicate with the
    sockets opened by the running Cloud SQL Proxy. Edit the
    `config/prod.secret.exs` file to include something like this:

        # Configure your database
        config :hello, Hello.Repo,
          username: "postgres",
          password: "XXXXXXXX",
          database: "hello_prod",
          socket_dir: "/tmp/cloudsql/[CONNECTION-NAME]",
          pool_size: 15

    Remember to replace `[CONNECTION-NAME]` with your database's connection
    name, and include the password you set for the "postgres" user.

3.  Hard-code `secret_key_base` in `config/prod.secret.exs`. (If you're doing a
    real application, you might want to create a different mechanism to inject
    the database password and the secret key base into this file, but we will
    keep things simple for this tutorial.)

4.  Now you can use Phoenix to create and migrate your production database:

        MIX_ENV=prod mix ecto.create
        MIX_ENV=prod mix ecto.migrate

5.  Stop the Cloud SQL Proxy when you are finished.

### Access the production database from App Engine

The App Engine runtime also runs a Cloud SQL Proxy for you, and makes your
databases available via Unix sockets. In the App Engine environment, these are
located in the directory `/cloudsql` at the root of the file system. So, to
prepare your app for deployment into App Engine, edit your
`config/prod.secret.exs` file again, and modify the `socket_dir` database
setting to point to the correct location for App Engine:

      socket_dir: "/cloudsql/[CONNECTION-NAME]",

Remember to replace `[CONNECTION-NAME]` with your database's connection name.

Further information on connecting to your database from App Engine is available
[in the documentation](https://cloud.google.com/sql/docs/postgres/connect-app-engine).

Note that if you need to run another Ecto migration or open another `psql`
session from your local workstation, you can temporarily revert `socket_dir` to
`/tmp/cloudsql` so that Phoenix can talk to your local Cloud SQL Proxy. If you
do, make sure you change it back to `/cloudsql` before you deploy to App Engine.
Alternatively, if you have the ability to create the directory `/cloudsql` on
your local workstation, you can configure Cloud SQL Proxy to open its sockets
there instead, and avoid the need to revert `socket_dir`.

## Enable releases

Releases are the Elixir community's preferred way to package Elixir (and
Erlang) applications for deployment. You will configure your app to create
deployable releases.

You can also use the [Distillery](https://github.com/bitwalker/distillery)
tool to create releases for your app. Distillery's configuration mechanism is
somewhat different from that provided by Elixir's built-in releases, so if you
choose to use Distillery, be sure to adjust these steps accordingly.

1.  Initialize release configuration by running:

        mix release.init

    This will create a `rel` directory containing several configuration files
    and templates. You can examine and edit these if if you wish, but the
    defaults should be sufficient for this tutorial.

    If you are using Distillery 2.1 or later, the corresponding command is
    `mix distillery.init`.

2.  Configure releases in your `mix.exs` project configuration.

    Add a `releases` section to the `project` function. For now, it should look
    like this:

        def project do
          [
            app: :hello,
            # Add this section...
            releases: [
              hello: [
                include_erts: true,
                include_executables_for: [:unix],
                applications: [
                  runtime_tools: :permanent
                ]
              ]
            ],
            version: "0.0.1",
            # additional fields...
          ]
        end

    If you are using Distillery, this information will appear in the file
    `rel/config.exs` instead. The defaults created by Distillery should be
    sufficient. In particular, make sure `include_erts` is set to `true`
    because the Elixir Runtime assumes ERTS is included in releases.

3.  Prepare the Phoenix configuration for deployment by editing the prod
    config file `config/prod.exs`. In particular, set `server: true` to ensure
    the web server starts when the supervision tree is initialized, and set the
    port to honor the `PORT` environment variable. We recommend the following
    settings to start off:

        config :hello, Hello.Endpoint,
            load_from_system_env: true,
            http: [port: {:system, "PORT"}],
            check_origin: false,
            server: true,
            root: ".",
            cache_static_manifest: "priv/static/cache_manifest.json"

    Alternatively, if you are using Elixir 1.9 or later, you can provide this
    information in the runtime configuration file `config/releases.exs`.

## Deploy your application

Now you will deploy your new app to App Engine.

1.  Create a file called `app.yaml` at the root of the application directory,
    with the following contents:

        env: flex
        runtime: gs://elixir-runtime/elixir.yaml
        runtime_config:
            release_app: hello
        beta_settings:
            cloud_sql_instances: [CONNECTION-NAME]

    This configuration selects the Elixir Runtime, an open source App Engine
    runtime that knows how to build Elixir and Phoenix applications. You can
    find more information about this runtime at its
    [Github page](https://github.com/GoogleCloudPlatform/elixir-runtime).
    The configuration also tells the runtime to build and deploy a Distillery
    release for the application `hello`.
    Finally, the configuration also informs App Engine that you want to connect
    to a Cloud SQL instance. (Remember to substitute your connection name for
    `[CONNECTION-NAME]`.) App Engine will respond by creating the Unix socket
    needed to connect to the database.

2.  Run the following command to deploy your app:

        gcloud app deploy

    If this is the first time you have deployed to App Engine in this project,
    `gcloud` will prompt you for a region. It is generally a good idea to choose
    the same region as you did for your database above, to minimize latency.

    The Elixir Runtime will take care of building your application in the
    cloud, including installing mix dependencies, compiling to BEAM files, and
    even using Webpack or Brunch to build your assets.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

3.  Once the deploy command has completed, you can run:

        gcloud app browse

    to see your app running in production on App Engine.

## Update your application

Let's make a simple change and redeploy.

1.  Open the front page template
    `lib/hello_web/templates/page/index.html.eex` in your editor.
    Make a change to the HTML template.

2.  Run the deployment command again:

        gcloud app deploy

    App Engine and the Elixir Runtime will take care of rebuilding your app,
    deploying the updated version, and migrating traffic to the newly deployed
    version.

3.  View your changes live by running:

        gcloud app browse

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the individual services.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. To do so using `gcloud`, run:

    gcloud projects delete [YOUR_PROJECT_ID]

where `[YOUR_PROJECT_ID]` is your Google Cloud project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

### Deleting individual services

In this tutorial, you created a Cloud SQL instance and deployed an App Engine
service. Here is how to stop these two services.

To delete the Cloud SQL instance, including all databases it hosts, run:

    gcloud sql instances delete hellodb

You generally cannot completely delete an App Engine service. However, you can
disable it so that it does not consume resources.

1.  In the Cloud Console, go to the
    [App Engine Versions page](https://console.cloud.google.com/appengine/versions).
2.  Make sure your project is selected. If necessary, pull down the project
    selection dropdown at the top, and choose the project you created for this
    tutorial.
3.  If you deployed to a service other than "default", make sure it is selected
    in the Service dropdown.
4.  Select all the versions you wish to disable and click **Stop** at the top
    of the page. This will free all of the Google Compute Engine resources used
    for this App Engine service.

## Next steps

The [Elixir Samples](https://github.com/GoogleCloudPlatform/elixir-samples)
repository contains a growing set of sample Elixir applications ready to deploy
to Google Cloud and examples of communicating with Google APIs from Elixir.

See the [App Engine documentation](https://cloud.google.com/appengine/docs/flexible/)
for more information on App Engine features including scaling, health checks,
and infrastructure customization.

You can also try the tutorials on deploying Phoenix applications
[to Kubernetes Engine](https://cloud.google.com/community/tutorials/elixir-phoenix-on-kubernetes-google-container-engine)
and [to Compute Engine](https://cloud.google.com/community/tutorials/elixir-phoenix-on-google-compute-engine).
