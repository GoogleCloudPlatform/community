---
title: Run an Elixir Phoenix app in containers using Google Kubernetes Engine
description: Learn how to deploy a Phoenix app in containers using Google Kubernetes Engine.
author: dazuma
tags: Kubernetes, Kubernetes Engine, Elixir, Phoenix, Docker
date_published: 2019-07-22
---

Daniel Azuma | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial helps you get started deploying your
[Elixir](http://elixir-lang.org/) app using the
[Phoenix](http://phoenixframework.org/) Framework to
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/),
Google's hosting solution for containerized applications. Google Kubernetes Engine is
based on the popular open-source [Kubernetes](https://kubernetes.io/) system,
and leverages Google's deep expertise with container-based deployments.

You will create a new Phoenix application, and then you will learn how to:

*   Connect your app to a database running in
    [Cloud SQL](https://cloud.google.com/sql)
*   Create an OTP release for your app using
    [Distillery](https://github.com/bitwalker/distillery)
*   Wrap your app release in a Docker image
*   Deploy your app on Google Kubernetes Engine
*   Scale and update your app using Kubernetes

This tutorial requires Elixir 1.5 and Phoenix 1.4 or later. It assumes you are
already familiar with basic Phoenix web development. It also requires the
PostgreSQL database to be installed on your local development workstation.

This tutorial was updated in January 2019 to cover Phoenix 1.4, Distillery 2.0,
and connecting Ecto to a Cloud SQL database. It was updated in July 2019 to
cover changes in Elixir 1.9 and Distillery 2.1.

## Before you begin

Before running this tutorial, you must set up a Google Cloud project,
and you need to have Docker, PostgreSQL, and the Cloud SDK installed.

Create a project that will host your Phoenix application. You can also reuse
an existing project.

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `${PROJECT_ID}` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

1.  Enable billing for your project.

1.  In the Cloud Console, enable the following APIs:
    *   [Cloud Build API](http://console.cloud.google.com/apis/library/cloudbuild.googleapis.com)
    *   [Kubernetes Engine API](http://console.cloud.google.com/apis/library/container.googleapis.com)
    *   [Cloud SQL Admin API](http://console.cloud.google.com/apis/library/sqladmin.googleapis.com)

Perform the installations:

1.  Install Docker 17.05 or later if you do not already have it. Find
    instructions on the [Docker website](https://www.docker.com/).

1.  Install the [Cloud SDK](https://cloud.google.com/sdk/) if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK and
    set the default project to the new project you created.

    Version 227.0.0 or later of the SDK is required. If you have an earlier
    version installed, you may upgrade it by running:

        gcloud components update

1.  Install the Kubernetes component of the Cloud SDK:

        gcloud components install kubectl

1.  Install Elixir 1.9 or later if you do not already have it. If you are
    on macOS and have [Homebrew](https://brew.sh), you can run:

        brew install elixir

    Otherwise consult the [Elixir install](https://elixir-lang.org/install.html)
    guide for your operating system.

1.  Install the `hex`, `rebar`, and `phx_new` archives:

        mix local.hex
        mix local.rebar
        mix archive.install hex phx_new 1.4.9

1.  Install Node.js if you do not already have it. If you are on macOS and
    have Homebrew, you can run:

        brew install node

    Otherwise consult the [Node.js download](https://nodejs.org/en/download/)
    guide for your operating system.

1.  Install PostgreSQL if you do not already have it. Consult the
    [PostgreSQL downloads page](https://www.postgresql.org/download/) for
    information on downloading and installing PostgreSQL for your operating
    system.

## Create a new app and run it locally

In this section, you will create a new Phoenix app with a database, and make
sure it runs locally in development. If you already have an app to deploy, you
may use it instead.

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

    This compiles your server and runs it on port `4000`.

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

In this section, you will create your production database using Cloud SQL, a
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

1.  Create a Cloud SQL instance named `hellodb` with a Postgres database
    by running the following command:

        gcloud sql instances create hellodb --region=us-central1 \
            --database-version=POSTGRES_9_6 --tier=db-g1-small

    You may choose a region other than `us-central1` if there is one closer to
    your location.

1.  Get the connection name for your Cloud SQL instance by running the
    following command:

        gcloud sql instances describe hellodb

    In the output, look for the connection name in the `connectionName` field.
    The connection name has this format: `[PROJECT-ID]:[COMPUTE-ZONE]:hellodb`
    We will refer to the connection name as `[CONNECTION-NAME]` throughout this
    tutorial.

1.  Secure your new database instance by setting a password on the default
    `postgres` user:

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

1.  Create a directory `/tmp/cloudsql`. This is where the Cloud SQL Proxy will
    create database connection sockets. You may put this in a different
    location, but if you do, you will need to update some of the commands below
    accordingly.

        mkdir -p /tmp/cloudsql

1.  Start the proxy, telling it to open sockets in the directory you created:

        cloud_sql_proxy -dir=/tmp/cloudsql

    **Note**: This runs the proxy in the foreground, so subsequent commands
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
    the database password and the secret key base into this file, but we will
    keep things simple for this tutorial.)

1.  Now you can use Phoenix to create and migrate your production database:

        MIX_ENV=prod mix ecto.create
        MIX_ENV=prod mix ecto.migrate

1.  Stop the Cloud SQL Proxy when you are finished.

## Enabling releases

Releases are the Elixir community's preferred way to package Elixir (and
Erlang) applications for deployment. You will configure your app to create
deployable releases.

**Note:** You can also use the [Distillery](https://github.com/bitwalker/distillery)
tool to create releases for your app. Distillery's configuration mechanism is
somewhat different from that provided by Elixir's built-in releases, so if you
choose to use Distillery, be sure to adjust these steps accordingly.

### Configure releases

1.  Initialize release configuration by running:

        mix release.init

    This will create a `rel` directory containing several configuration files
    and templates. You can examine and edit these if you wish, but the
    defaults should be sufficient for this tutorial.

    If you are using Distillery 2.1 or later, the corresponding command is
    `mix distillery.init`.

1.  Configure releases in your `mix.exs` project configuration.

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

    Alternatively, if you are using Elixir 1.9 or later, you can provide this
    information in the runtime configuration file `config/releases.exs`.

### Test a release

Now you can create a release to test out your configuration.

1.  Build and digest the application assets for production:

        cd assets
        npm install
        ./node_modules/webpack/bin/webpack.js --mode production
        cd ..
        mix phx.digest

    Remember that if your app is an umbrella app, the assets directory might be
    located in one of the apps subdirectories.

1.  Build the release:

        MIX_ENV=prod mix release hello

1.  Start the Cloud SQL Proxy so that Phoenix can connect to your database.
    Remember that this runs in the foreground by default.

        cloud_sql_proxy -dir=/tmp/cloudsql

1.  Run the application from the release using:

        PORT=8080 _build/prod/rel/hello/bin/hello start

1.  Visit [http://localhost:8080](http://localhost:8080) to see the Phoenix
    welcome screen running locally from your release.

1.  Stop the Cloud SQL Proxy and the application when you are finished.

## Dockerizing your application

The next step is to produce a Docker image that builds and runs your
application in a Docker container. You will define this image using a
Dockerfile.

Various considerations go into designing a good Docker image. The Dockerfile
used by this tutorial builds a release and runs it with Alpine Linux.
If you are experienced with Docker, you can customize your image.

1.  Create a file called `Dockerfile` in your `hello` directory. Copy the
    following content into it. Alternately, you can
    [download](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-kubernetes-google-container-engine/Dockerfile)
    a sample annotated Dockerfile to study and customize.

        FROM elixir:alpine
        ARG app_name=hello
        ARG phoenix_subdir=.
        ARG build_env=prod
        ENV MIX_ENV=${build_env} TERM=xterm
        WORKDIR /opt/app
        RUN apk update \
            && apk --no-cache --update add nodejs nodejs-npm \
            && mix local.rebar --force \
            && mix local.hex --force
        COPY . .
        RUN mix do deps.get, compile
        RUN cd ${phoenix_subdir}/assets \
            && npm install \
            && ./node_modules/webpack/bin/webpack.js --mode production \
            && cd .. \
            && mix phx.digest
        RUN mix release ${app_name} \
            && mv _build/${build_env}/rel/${app_name} /opt/release \
            && mv /opt/release/bin/${app_name} /opt/release/bin/start_server
        FROM alpine:latest
        ARG project_id
        RUN apk update \
            && apk --no-cache --update add bash ca-certificates openssl-dev \
            && mkdir -p /usr/local/bin \
            && wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 \
                -O /usr/local/bin/cloud_sql_proxy \
            && chmod +x /usr/local/bin/cloud_sql_proxy \
            && mkdir -p /tmp/cloudsql
        ENV PORT=8080 GCLOUD_PROJECT_ID=${project_id} REPLACE_OS_VARS=true
        EXPOSE ${PORT}
        WORKDIR /opt/app
        COPY --from=0 /opt/release .
        CMD (/usr/local/bin/cloud_sql_proxy \
              -projects=${GCLOUD_PROJECT_ID} -dir=/tmp/cloudsql &); \
            exec /opt/app/bin/start_server start

    Note that there is a required argument called `project_id`, so if you build
    this image locally, you must provide a value via `--build-arg`.

    If you are using Distillery instead of Elixir's built-in releases, you will
    need to modify the `mix release` command appropriately, and use the
    `foreground` command rather than the `start` command.

    If your app is named something other than `hello`, you must modify the
    `app_name` argument in the Dockerfile. If your app is an umbrella app, you
    will also need to modify the `phoenix_subdir` argument to contain the path
    to the Phoenix application subdirectory, e.g. `apps/hello_web`.

1.  Create a file called `.dockerignore` in your `hello` directory. Copy the
    following content into it. Alternately, you can
    [download](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-kubernetes-google-container-engine/.dockerignore)
    a sample annotated file to study and customize.

        /_build/
        /assets/node_modules/
        /deps/
        /doc/
        /priv/static/
        /test/
        /tmp/

    **Note:** if your app is an umbrella app, you might need to adjust the
    paths to include the build, deps, and node_modules directories of the
    constituent apps. In general, you want Docker to ignore artifacts that come
    from your development environment, so it can perform clean builds.

1.  Create a file called `.gcloudignore` in your `hello` directory. Copy the
    following single line into it:

        #!include:.dockerignore

    This file controls which files are ignored by Google Cloud Build. If you do
    not provide it, `gcloud` will ignore everything in your `.gitignore` by
    default. That would cause your `config/prod.secret.exs` to be omitted,
    which would cause the build to fail. By specifying this line, you instruct
    `gcloud` to use the contents of your `.dockerignore` file instead.

## Deploying your application

Now you're ready to deploy your application to Google Kubernetes Engine!

### Build the production image

To deploy the app, you will use the
[Cloud Build](https://cloud.google.com/cloud-build/) service to build
your Docker image in the cloud and store the resulting Docker image in the
[Container Registry](https://cloud.google.com/container-registry/).

1.  Create a file called `cloudbuild.yaml` in your `hello` directory. Copy the
    following content into it. Alternately, you can
    [download](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-kubernetes-google-container-engine/cloudbuild.yaml)
    a sample annotated file to study and customize.

        steps:
        - name: "gcr.io/cloud-builders/docker"
          args: ["build", "-t", "gcr.io/$PROJECT_ID/hello:$_TAG",
               "--build-arg", "project_id=$PROJECT_ID", "."]
        images: ["gcr.io/$PROJECT_ID/hello:$_TAG"]

    The `cloudbuild.yaml` file specifies how to perform a build. You can find
    more information on the structure and syntax of a build configuration
    [in the documentation](https://cloud.google.com/cloud-build/docs/build-config).

    For your app, the build procedure simply performs a docker build. Note that
    it passes the value `$PROJECT_ID` for the required `project_id` argument in
    your Dockerfile. `$PROJECT_ID` is a standard substitution provided by Cloud
    Build. You'll notice there is also a `$_TAG` substitution; you must provide
    its value when you run a build, as shown below.

1.  Execute the following command to run the build:

        gcloud builds submit --substitutions=_TAG=v1 .
    
    The period at the end is required. It indicates that the build should be
    performed using the files in the current `hello` application directory.

    Note that you provide the value `v1` for the `_TAG` substitution. The build
    configuration uses this value as the docker image tag for the docker image
    being built.

After the build finishes, the image `gcr.io/${PROJECT_ID}/hello:v1` will be
available. You can list the images you have built in your project using:

    gcloud container images list

You can even push and pull the image directly from your registry. See the
[Container Registry how-to guides](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
for more details.

### Create a cluster

Google Kubernetes Engine lets you create Kubernetes clusters to host your application.
These are clusters of VMs in the cloud, managed by a Kubernetes server.

1.  Choose a cluster name. For the rest of these instructions, I'll assume that
    name is "hello-cluster".
    
1.  Choose a zone. You should 
    [choose a zone](https://cloud.google.com/compute/docs/regions-zones/) 
    that makes sense for you, such as `us-central1-a`. It is a good idea to
    select a zone in the same region where your database is located.
    
1.  Create the cluster:

        gcloud container clusters create hello-cluster --num-nodes=2 \
            --zone=us-central1-a --scopes=gke-default,sql-admin

    This command creates a cluster of two machines. You can choose a different
    size, but two is a good starting point. It is also important to include the
    `sql-admin` scope so that VMs in your cluster can talk to Cloud SQL.

    It might take several minutes for the cluster to be created. You can check
    the Cloud Console at http://console.cloud.google.com/, under the Kubernetes
    Engine section, to see that your cluster is running. You will also be able
    to see the individual running VMs under the Compute Engine section.

    Note that once the cluster is running, *you will be charged for VM usage*.

1.  Configure the `gcloud` command-line tool to use your cluster by default, so
    you don't have to specify it every time for the remaining `gcloud` commands:

        gcloud container clusters get-credentials --zone=us-central1-a hello-cluster
        gcloud config set container/cluster hello-cluster

    Replace the cluster name and zone if you used different values.

### Deploy to the cluster

A production deployment comprises two parts: your Docker container, and a
front-end load balancer (which also provides a public IP address.)

We'll assume that you built the image to `gcr.io/${PROJECT_ID}/hello:v1` and
you've created the Kubernetes cluster as described above.

1.  Create a deployment:

        kubectl run hello-web --image=gcr.io/${PROJECT_ID}/hello:v1 --port 8080

    This runs your image on a Kubernetes pod, which is the deployable unit in
    Kubernetes. The pod opens port 8080, which is the port your Phoenix
    application is listening on.

1.  Check that your pod is running.

    View the running pods using:

        kubectl get pods

    Once the status changes to `Running`, your pod is ready.

    If the status changes to `CrashLoopBackoff`, something is wrong. You could
    try examining the logs by running the following, substituting the pod name.

        kubectl logs {POD-NAME}

    (As of mid-2019, you might encounter `dlsym: Resource temporarily unavailable`
    which happens because the Elixir Alpine image is not compatible with the
    latest Alpine Linux. Fix this by editing your Dockerfile, changing the
    second stage from `FROM alpine:latest` to `FROM alpine:3.9`.)

1.  Expose the application by creating a load balancer pointing at your pod:

        kubectl expose pod hello-web \
            --type=LoadBalancer --port 80 --target-port 8080

    This creates a service resource pointing at your running pod. It listens
    on the standard HTTP port 80, and proxies back to your pod on port 8080.

1.  Obtain the IP address of the service by running:

        kubectl get service

    Initially, the external IP field will be pending while Google Kubernetes Engine
    procures an IP address for you. If you rerun the `kubectl get service`
    command repeatedly, eventually the IP address will appear. You can then
    point your browser at that URL to view the running application.

Congratulations! Your application is now up and running!

## Scaling and updating your application

You'll now explore a few of the basic features of Kubernetes for managing your
running app.

### Set the replica count

Initially your deployment runs a single instance of your application. You can
add more replicas using the `kubectl scale` command. For example, to add two
additional replicas (for a total of three), run:

    kubectl scale deployment hello-web --replicas=3

Once the additional replicas are running, you can see the list of three pods
by running:

    kubectl get pods

Kubernetes automatically allocates your running pods on the virtual machines
in your cluster. You can configure pods in your deployment with specific
resource requirements such as memory and CPU. See the
[Kubernetes documentation](https://kubernetes.io/docs/home/) for more details.

### Update your application

After you make a change to your app, redeploying is just a matter of
building a new image and pointing your deployment to it.

1.  Make a change to the app. (For example, modify the front page template.)

1.  Perform a new build with a new version tag "v2":

        gcloud builds submit --substitutions=_TAG=v2 .

    Now you have two builds stored in your project, `hello:v1` and `hello:v2`.
    In general it's good practice to set the image tag for each build to a
    unique build number. This will let you identify and deploy any build,
    making updates and rollbacks easy.

1.  Set the deployment to use the new image:

        kubectl set image deployment/hello-web hello-web=gcr.io/${PROJECT_ID}/hello:v2

    This performs a rolling update of all the running pods.

1.  You can roll back to the earlier build by calling `kubectl set image`
    again, specifying the earlier build tag:

        kubectl set image deployment/hello-web hello-web=gcr.io/${PROJECT_ID}/hello:v1

**Note:** If a deployment gets stuck because an error in the image prevents
it from starting successfully, you can recover by undoing the rollout. See the
[Kubernetes deployment documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
for more info.

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. To
clean up the resources, you can delete the individual resources used, or delete
the entire project.

### Deleting individual resources

To delete your app from Google Kubernetes Engine, you must remove both the load
balancer and the Google Kubernetes Engine cluster.

1.  Delete the service, which deallocates the load balancer:

        kubectl delete service hello-web

1.  The load balancer will be deleted asynchronously. Wait for that process to
    complete by monitoring the output of:

        gcloud compute forwarding-rules list

    The forwarding rule will disappear when the load balancer is deleted.

1.  Delete the cluster, which deletes the resources used by the cluster,
    including virtual machines, disks, and network resources:

        gcloud container clusters delete --zone=us-central1-a hello-cluster

    Be sure to specify the same zone you used to create the cluster.

Finally, delete the Cloud SQL instance, which will delete all databases it
hosts.

    gcloud sql instances delete hellodb

### Deleting the project

Alternately, you can delete the project in its entirety. To do so using the
`gcloud` tool, run:

    gcloud projects delete ${PROJECT_ID}

where `${PROJECT_ID}` is your Google Cloud project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

## Next steps

The [Elixir Samples](https://github.com/GoogleCloudPlatform/elixir-samples)
repository contains a growing set of sample Elixir applications ready to deploy
to Google Cloud and examples of communicating with Google APIs from Elixir.

See [this guide](https://cloud.google.com/sql/docs/postgres/connect-kubernetes-engine)
to learn about more options for connecting to Cloud SQL from Google Kubernetes Engine,
including using a Private IP address or a container sidecar.

If you want to procure a static IP address and connect your domain name, you
might find [this tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/configuring-domain-name-static-ip)
helpful.

See the [Google Kubernetes Engine documentation](https://cloud.google.com/kubernetes-engine/docs/)
for more information on managing Google Kubernetes Engine clusters.

See the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more
information on managing your application deployment using Kubernetes.
