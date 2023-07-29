---
title: Run an Elixir Phoenix app on Compute Engine
description: Learn how to deploy a Phoenix app to Compute Engine.
author: dazuma
tags: Compute Engine, Elixir, Phoenix
date_published: 2019-07-22
---

Daniel Azuma | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial helps you get started deploying your
[Elixir](http://elixir-lang.org/) app using the
[Phoenix](http://phoenixframework.org/) Framework to
[Compute Engine](https://cloud.google.com/compute/), taking
advantage of Google's deep expertise with scalable infrastructure.

In this tutorial, you do the following:

*   Create a new Phoenix application
*   Connect your app to a database running in
    [Cloud SQL](https://cloud.google.com/sql)
*   Create an OTP release for your app using
    [Distillery](https://github.com/bitwalker/distillery)
*   Deploy your app to Compute Engine instances
*   Set up load balancing and autoscaling for your app

This tutorial requires Elixir 1.5 and Phoenix 1.4 or later. It assumes you are
already familiar with basic Phoenix web development. It also requires the
PostgreSQL database to be installed on your local development workstation.

This tutorial was updated in January 2019 to cover Phoenix 1.4, Distillery 2.0,
and connecting Ecto to a Cloud SQL database. It was updated in July 2019 to
improve the build procedure and cover changes in Distillery 2.1.

## Before you begin

Before running this tutorial, you must set up a Google Cloud project.
You also need to have Docker, PostgreSQL, and the Cloud SDK installed on
your workstation.

### Create a Google Cloud project

Create a project to host your Phoenix application. You can also reuse
an existing project.

To create a new project:

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project. Remember the project ID; you will
    need it later. Commands in this tutorial use `${PROJECT_ID}` as
    a substitution, so you consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.

1.  In the Cloud Console, enable the following APIs:
    *   [Compute Engine API](http://console.cloud.google.com/apis/library/compute.googleapis.com)
    *   [Cloud SQL Admin API](http://console.cloud.google.com/apis/library/sqladmin.googleapis.com)

### Install required applications and services

After you have set up a Google Cloud project, perform the following
tasks on your workstation:

1.  Install Docker if you do not already have it. Find instructions on the
    [Docker website](https://www.docker.com/).

1.  Install the [Cloud SDK](https://cloud.google.com/sdk/) if you do
    not already have it. Make sure that you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project that you created.

    Version 227.0.0 or later of the SDK is required. If you have an earlier
    version installed, upgrade it:

        gcloud components update

1.  Install Elixir 1.8 or later if you do not already have it.

    If you are on macOS and have [Homebrew](https://brew.sh), you can run the following command to install Elixir:

        brew install elixir

    Otherwise, consult the [Elixir installation](https://elixir-lang.org/install.html)
    guide for your operating system.

1.  Install the `hex`, `rebar`, and `phx_new` archives:

        mix local.hex
        mix local.rebar
        mix archive.install hex phx_new 1.4.9

1.  Install Node.js if you do not already have it.

    If you are on macOS and have Homebrew, you can run the following command to install Node.js:

        brew install node

    Otherwise, consult the [Node.js download](https://nodejs.org/en/download/)
    guide for your operating system.

1.  Install PostgreSQL if you do not already have it.

    Consult the [PostgreSQL downloads page](https://www.postgresql.org/download/) for
    information on downloading and installing PostgreSQL for your operating system.

## Creating a new app and running it locally

In this section, you create a new Phoenix app with a database and make
sure that it runs locally in development. If you already have an app to deploy, you
can use it instead.

### Create a new Phoenix app

1.  Run the `phx.new` task to create a new Phoenix project called `hello`:

        mix phx.new hello

    Answer `Y` when the tool asks you if you want to fetch and install
    dependencies.

1.  Go into the directory with the new application:

        cd hello

1.  Update the development database settings in `config/dev.exs` to specify a
    valid database user and credentials. You may also update the database name.
    The resulting configuration may look something like this:

        # Configure your database
        config :hello, Hello.Repo,
            username: "my_name",
            password: "XXXXXXXX",
            database: "hello_dev",
            hostname: "localhost",
            pool_size: 10

1.  Create the development database with the following command:

        mix ecto.create

1.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port 4000.

1.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

### Create and test a development database

Next you will populate a simple development database and verify that your
Phoenix app can access it.

1.  Create a simple schema:

        mix phx.gen.schema User users name:string email:string

1.  Migrate your development database:

        mix ecto.migrate

1.  Add some very simple code to show that the application can access the
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

1.  Recompile and run the app:

        mix phx.server

1.  Visit [http://localhost:4000](http://localhost:4000) to verify that your
    new code is running. You can log into your database and add new rows, and
    reload the page to verify that the count has changed.

For more information on using Ecto to access a SQL database, see the
[Phoenix Ecto guide](https://hexdocs.pm/phoenix/ecto.html).

## Create a production database in Cloud SQL

In this section, you will create your "production" database using Cloud SQL, a
fully-managed database service providing PostgreSQL and MySQL in the cloud. If
you already have a database hosted elsewhere, you may skip this section, but
you may need to ensure your production configuration is set up to connect to
your database.

Before you begin this section, make sure you have enabled billing and the
needed APIs in your cloud project. You should also set the default project for
your gcloud SDK if you have not already done so:

    gcloud config set project ${PROJECT_ID}

### Create a Cloud SQL instance

First you will create a new database in the cloud.

1.  Create a Cloud SQL instance named `hellodb` with a PostgreSQL database:

        gcloud sql instances create hellodb --region=us-central1 \
            --database-version=POSTGRES_9_6 --tier=db-g1-small

    You may choose a region other than `us-central1` if there is one closer to
    your location.

1.  Get the _connection name_ for your Cloud SQL instance:

        gcloud sql instances describe hellodb

    In the output, look for the connection name in the `connectionName` field.
    The connection name has this format: `[PROJECT-ID]:[COMPUTE-ZONE]:hellodb`
    This tutorial refers to the connection name as `[CONNECTION-NAME]`.

1.  Secure your new database instance by setting a password on the default
    postgres user:

        gcloud sql users set-password postgres \
            --instance=hellodb --prompt-for-password

    When prompted, enter a password for the database.

### Connect to your Cloud SQL instance

In this section you learn how to connect to your Cloud SQL instance from
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

1.  Create a directory `/tmp/cloudsql`. This is where the Cloud SQL Proxy will
    create database connection sockets. You may put this in a different
    location, but if you do, you will need to update some of the commands below
    accordingly.

        mkdir -p /tmp/cloudsql

1.  Start the proxy, telling it to open sockets in the directory you created:

        cloud_sql_proxy -dir=/tmp/cloudsql

    This runs the proxy in the foreground, so subsequent commands
    need to be run in a separate shell. If you prefer, feel free to
    background the process instead.

1.  The proxy will open a socket in the directory
    `/tmp/cloudsql/[CONNECTION-NAME]/`. You can point `psql` to that socket to
    connect to the database instance. Test this now:

        psql -h /tmp/cloudsql/[CONNECTION-NAME] -U postgres

You can learn more about using the Cloud SQL Proxy to connect to your instance
from [the documentation](https://cloud.google.com/sql/docs/postgres/connect-admin-proxy).

### Create and migrate the production database

Next you will configure your Phoenix app to point to your production database
instance, and tell Ecto to create and migrate the database.

1.  Start the Cloud SQL Proxy, if it is not already running from the previous
    section. Remember that this runs in the foreground by default.

        cloud_sql_proxy -dir=/tmp/cloudsql

1.  Configure your production database configuration to communicate with the
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

1.  Hard-code `secret_key_base` in `config/prod.secret.exs`. (If you're doing a
    real application, you might want to create a different mechanism to inject
    the database password and the secret key base into this file, but this tutorial keeps things simple.)

1.  Now you can use Phoenix to create and migrate your production database:

        MIX_ENV=prod mix ecto.create
        MIX_ENV=prod mix ecto.migrate

1.  Stop the Cloud SQL Proxy when you are finished.

## Enabling releases with Distillery

Releases are the preferred way to package Elixir (and Erlang) applications for
deployment. You will configure the
[Distillery](https://github.com/bitwalker/distillery) tool to create releases
for your app.

Elixir 1.9 or later can build basic releases by itself, but this
tutorial requires additional capabilities provided by Distillery, specifically
the ability to create a self-extracting executable.

If you already have Distillery set up for your application, you can
skip this section. But make sure `include_erts: true` is set in your `:prod`
release configuration. This tutorial assumes ERTS is included in releases.

### Set up Distillery

1.  Add distillery to your application's dependencies. In the `mix.exs` file,
    add `{:distillery, "~> 2.1"}` to the `deps`. Then install it:

        mix deps.get

1.  Create a default release configuration:

        mix distillery.init

    This will create a file `rel/config.exs`. You can examine and edit it if
    you wish, but the defaults should be sufficient for this tutorial.

1.  Prepare the Phoenix configuration for deployment by editing the prod
    config file `config/prod.exs`. In particular, set `server: true` to ensure
    the web server starts when the supervision tree is initialized, and set the
    port to honor the `PORT` environment variable. We recommend the following
    settings to start off:

        config :hello, HelloWeb.Endpoint,
            load_from_system_env: true,
            http: [port: {:system, "PORT"}],
            check_origin: false,
            server: true,
            root: ".",
            cache_static_manifest: "priv/static/cache_manifest.json"

    Some versions of phoenix override the `http` key when creating a new
    `config/prod.secret.exs` file. Delete that line if it is present, so that
    it does not interfere with your config.

### Test a release

Now you can create a release to test out your configuration.

1.  Make sure assets have been built for production:

        pushd assets
        npm install
        ./node_modules/webpack/bin/webpack.js --mode production
        popd
        mix phx.digest

    Remember that if your app is an umbrella app, the assets directory might be
    located in one of the apps subdirectories.

1.  Build the release:

        MIX_ENV=prod mix distillery.release --env=prod --executable

1.  Start the Cloud SQL Proxy so that Phoenix can connect to your database.
    Remember that this runs in the foreground by default.

        cloud_sql_proxy -dir=/tmp/cloudsql

1.  Run the application from the release with:

        PORT=8080 _build/prod/rel/hello/bin/hello.run foreground

    If your application is named something other than `hello`, the release
    executable might be in a different path.

1.  Visit [http://localhost:8080](http://localhost:8080) to see the Phoenix
    welcome screen running locally from your release.

1.  After you stop the application, delete the `tmp` directory (which is where
    `hello.run` extracts to). Otherwise, if you make changes and try running
    again, `hello.run` may use the existing extraction rather than the new
    code. Additionally, make sure you stop `cloud_sql_proxy` when you are done
    testing.

## Building a release for deployment

Building a release for deploying to the cloud is a bit more complicated
because your build needs to take place in the same operating system and
architecture as your deployment environment. In this section, you will use
Docker to cross-compile a release. (However, your app will eventually run
directly on a Compute Engine VM, not in a Docker container.) Then, you will
upload your release to a Cloud Storage bucket.

### Prepare a Cloud Storage bucket

Created a Cloud Storage bucket for your releases:

1.  Choose a bucket name. A good name might be related to your project ID, e.g.

        export BUCKET_NAME="${PROJECT_ID}-releases"

1.  Create the bucket:

        gsutil mb gs://${BUCKET_NAME}

### Prepare a build script

In this section, you create a Dockerfile script to build your app.

This is *not* an image that can be deployed or run directly. This tutorial simply uses
Docker to cross-compile your application for Debian. If you are
interested in building a Docker image that can be deployed to a container-based
environment such as Kubernetes, see the companion tutorial on
[deploying Phoenix to Kubernetes Engine](https://cloud.google.com/community/tutorials/elixir-phoenix-on-kubernetes-google-container-engine).

1.  Create a file called `Dockerfile` in your `hello` directory, and copy the
    following content into it:

        FROM elixir:latest
        ARG app_name=hello
        ARG phoenix_subdir=.
        ARG build_env=prod
        ENV MIX_ENV=${build_env} TERM=xterm
        WORKDIR /app
        RUN apt-get update -y \
            && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
            && apt-get install -y -q --no-install-recommends nodejs \
            && mix local.rebar --force \
            && mix local.hex --force
        COPY . .
        RUN mix do deps.get, compile
        RUN cd ${phoenix_subdir}/assets \
            && npm install \
            && ./node_modules/webpack/bin/webpack.js --mode production \
            && cd .. \
            && mix phx.digest
        RUN mix distillery.release --env=${build_env} --executable --verbose \
            && mv _build/${build_env}/rel/${app_name}/bin/${app_name}.run start_release

1.  Create a file called `.dockerignore` in your `hello` directory, and copy the
    following content into it:

        /_build/
        /assets/node_modules/
        /deps/
        /doc/
        /priv/static/
        /test/
        /tmp/

    If your app is an umbrella app, you might need to adjust the
    paths to include the build, deps, and node_modules directories of the
    constituent apps. In general, you want Docker to ignore artifacts that come
    from your development environment, so it can perform clean builds.

### Build and upload to Cloud Storage

In this section, you build the application image, extract the executable release file, and
upload it to Cloud Storage.

1.  Build the application image.

        docker build -t hello-image .

    This tutorial assumes you have named your image `hello-image`, though you
    can give it a different name.

1.  Copy the executable out of the image. Docker doesn't provide a
    command to do this directly, so you create a temporary container from
    the image and copy the executable from there.

        container_id=$(docker create hello-image)
        docker cp ${container_id}:/app/start_release start_release
        docker rm ${container_id}

    The executable release is now available in your current directory as
    `start_release`. (Note that you might not be able to run this executable
    release directly from your workstation, because it has been cross-compiled
    for Debian.)

1.  Push the release to Cloud Storage:

        gsutil cp start_release gs://${BUCKET_NAME}/hello-release

Whenever you want to do a new build, you only need to repeat the steps to
perform a production build as described in this subsection. You do not need
to modify the Dockerfile.

## Deploying your application to a single instance

You can now deploy your application to Compute Engine.

Compute Engine instances may provide a startup script that is executed whenever
the instance is started or restarted. You will use this to install and start
your app.

### Create a startup script

Create a file called `instance-startup.sh` in your application's root directory.
Copy the following content into it:

    #!/bin/sh
    set -ex
    export HOME=/app
    mkdir -p ${HOME}
    cd ${HOME}
    RELEASE_URL=$(curl \
        -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/release-url" \
        -H "Metadata-Flavor: Google")
    gsutil cp ${RELEASE_URL} hello-release
    chmod 755 hello-release
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 \
        -O cloud_sql_proxy
    chmod +x cloud_sql_proxy
    mkdir /tmp/cloudsql
    PROJECT_ID=$(curl \
        -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" \
        -H "Metadata-Flavor: Google")
    ./cloud_sql_proxy -projects=${PROJECT_ID} -dir=/tmp/cloudsql &
    PORT=8080 ./hello-release start

The startup script downloads the Cloud SQL Proxy from Google Cloud, and the
release you built from Cloud Storage, and executes both. It reads the Cloud
Storage URL from an *instance attribute*, which is key-value metadata that can
be associated with a Compute Engine instance. You will set that attribute when
you actually create the instance. It also obtains the project ID from a project
attribute that is set automatically by Compute Engine.

### Create and configure a Compute Engine instance

Now you will start a Compute Engine instance.

1.  Create an instance:

        gcloud compute instances create hello-instance \
            --image-family debian-9 \
            --image-project debian-cloud \
            --machine-type g1-small \
            --scopes "userinfo-email,cloud-platform" \
            --metadata-from-file startup-script=instance-startup.sh \
            --metadata release-url=gs://${BUCKET_NAME}/hello-release \
            --zone us-central1-f \
            --tags http-server

    This command creates a new instance named `hello-instance`, grants it
    access to Google Cloud services, and provides your startup script. It
    also sets an instance attribute with the Cloud Storage URL of your release.

1.  Check the progress of instance creation:

        gcloud compute instances get-serial-port-output hello-instance \
            --zone us-central1-f

    This will include the output of the `instance-startup.sh` script. You can
    continue when you see Cloud SQL Proxy report that it is receiving database
    connections from your app.

1.  Create a firewall rule to allow traffic to your instance:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

1.  Get the external IP address of your instance:

        gcloud compute instances list

1.  To see your application running, go to `http://${IP_ADDRESS}:8080` where
    `${IP_ADDRESS}` is the external address you obtained above.

## Horizontal scaling with multiple instances

Compute Engine can easily scale horizontally. By using a managed instance
group and the Compute Engine Autoscaler, Compute Engine can automatically
create new instances of your application when needed, and shut down instances
when demand is low. You can set up an HTTP load balancer to distribute traffic
to the instances in a managed instance group.

### Create a managed instance group

A managed instance group is a group of homogeneous instances based on an
instance template. Here you will create a group of instances running your
Phoenix app.

1.  Create an instance template:

        gcloud compute instance-templates create hello-template \
            --image-family debian-9 \
            --image-project debian-cloud \
            --machine-type g1-small \
            --scopes "userinfo-email,cloud-platform" \
            --metadata-from-file startup-script=instance-startup.sh \
            --metadata release-url=gs://${BUCKET_NAME}/hello-release \
            --tags http-server

    Notice that the template provides most of the information needed to create
    instances.

1.  Now create an instance group using that template:

        gcloud compute instance-groups managed create hello-group \
            --base-instance-name hello-group \
            --size 2 \
            --template hello-template \
            --zone us-central1-f

    The `size` parameter specifies the number of instances in the group. You
    can set it to a different value as needed.

1.  If you did not create the firewall rule while configuring a single instance
    above, do so now:

        gcloud compute firewall-rules create default-allow-http-8080 \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow port 8080 access to http-server"

1.  Get the names and external IP addresses of the instances that were created:

        gcloud compute instances list

    The managed instances in the group have names that start with the
    base-instance-name, i.e. `hello-group`. You can use the names to check the
    progress of instance creation as you did above with a single instance, and
    then you can use the IP addresses to see your application running on port
    8080 of each instance.

### Create a load balancer

You will now create a load balancer to direct traffic automatically to
available instances in the group. Follow these steps.

1.  Create a health check. The load balancer uses a health check to determine
    which instances are capable of serving traffic. The health check simply
    ensures that the root URL returns a page, such as the Phoenix default page.
    If you are using a different application, you can specify a different
    request path.

        gcloud compute http-health-checks create hello-health-check \
            --request-path / \
            --port 8080

1.  Create a named port. The HTTP load balancer directs traffic to a port
    named `http`, so we map that name to port 8080 to indicate that the
    instances listen on that port.

        gcloud compute instance-groups managed set-named-ports hello-group \
            --named-ports http:8080 \
            --zone us-central1-f

1.  Create a backend service. The backend service is the "target" for
    load-balanced traffic. It defines which instance group the traffic should
    be directed to and which health check to use.

        gcloud compute backend-services create hello-service \
            --http-health-checks hello-health-check \
            --global

1.  Add your instance group to the backend service:

        gcloud compute backend-services add-backend hello-service \
            --instance-group hello-group \
            --global \
            --instance-group-zone us-central1-f

1.  Create a URL map. This defines which URLs should be directed to which
    backend services. In this sample, all traffic is served by one backend
    service. If you want to load balance requests between multiple regions or
    groups, you can create multiple backend services.

        gcloud compute url-maps create hello-service-map \
            --default-service hello-service

1.  Create a proxy that receives traffic and forwards it to backend services
    using the URL map:

        gcloud compute target-http-proxies create hello-service-proxy \
            --url-map hello-service-map

1.  Create a global forwarding rule. This ties a public IP address and port to
    a proxy.

        gcloud compute forwarding-rules create hello-http-rule \
            --target-http-proxy hello-service-proxy \
            --ports 80 \
            --global

1.  You are now done configuring the load balancer. It will take a few minutes
    for it to initialize and get ready to receive traffic. You can check on its
    progress:

        gcloud compute backend-services get-health hello-service \
            --global

    Continue checking until it lists at least one instance in state `HEALTHY`.

1.  Get the forwarding IP address for the load balancer:

        gcloud compute forwarding-rules list --global

    Your forwarding-rules IP address is in the `IP_ADDRESS` column.

    You can now enter the IP address into your browser and view your
    load-balanced app running on port 80!

### Configure an autoscaler

As traffic to your site changes, you can adjust the instance group size
manually, or you can configure an autoscaler to adjust the size automatically
in response to traffic demands.

Create an autoscaler to monitor utilization and automatically create and delete
instances up to a maximum of 10:

    gcloud compute instance-groups managed set-autoscaling hello-group \
        --max-num-replicas 10 \
        --target-load-balancing-utilization 0.6 \
        --zone us-central1-f

After a few minutes, if you send traffic to the load balancer, you might see
that additional instances have been added to the instance group.

A wide variety of autoscaling policies are available to maintain target CPU
utilization and request-per-second rates across your instance groups. For
more information, see the
[documentation](https://cloud.google.com/compute/docs/autoscaler/).

### Manage and monitor your deployment

You can use the Cloud Console to monitor load balancing, autoscaling,
and your managed instance group.

In the [Compute > Compute Engine](https://console.cloud.google.com/compute/instances)
section, you can view individual running instances and connect using SSH.
You can manage your instance group and autoscaling configuration using the
[Compute > Compute Engine > Instance groups](https://console.cloud.google.com/compute/instanceGroups)
section. You can manage load balancing configuration, including URL maps and
backend services, using the
[Compute > Compute Engine > HTTP load balancing](https://console.cloud.google.com/net-services/loadbalancing)
section.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud so you won't be billed for them in the future. You
can delete the resources individually, or delete the entire project.

### Delete individual resources

Delete the load balancer on the Cloud Console
[network services page](https://console.cloud.google.com/net-services). Also
delete the related resources when it asks.

Delete the compute engine instance group on the Cloud Console
[instance groups page](https://console.cloud.google.com/compute/instanceGroups).

Delete the remaining single instance on the Cloud Console
[instances page](https://console.cloud.google.com/compute/instances).

Delete the Cloud Storage bucket hosting your OTP release from the
[Cloud Storage browser](https://console.cloud.google.com/storage/browser).

Delete the Cloud SQL instance, which will delete all the databases it hosts, by
running:

    gcloud sql instances delete hellodb

### Delete the project

Alternatively, you can delete the entire project:

    gcloud projects delete ${PROJECT_ID}

## Next steps

The [Elixir Samples](https://github.com/GoogleCloudPlatform/elixir-samples)
repository contains a growing set of sample Elixir applications ready to deploy
to Google Cloud and examples of communicating with Google APIs from Elixir.

See the [Compute Engine documentation](https://cloud.google.com/compute/docs/)
for more information on managing Compute Engine deployments.
