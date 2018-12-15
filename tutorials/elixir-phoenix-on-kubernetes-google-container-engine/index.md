---
title: Run an Elixir Phoenix app in containers using Google Kubernetes Engine
description: Learn how to deploy a Phoenix app in containers using Google Kubernetes Engine.
author: dazuma
tags: Kubernetes, Kubernetes Engine, Elixir, Phoenix, Docker
date_published: 2017-11-01
---

This tutorial helps you get started deploying your
[Elixir](http://elixir-lang.org/) app using the
[Phoenix](http://phoenixframework.org/) Framework to
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/),
Google's hosting solution for containerized applications. Kubernetes Engine,
earlier known as Google Kubernetes Engine, is based on the popular open-source
[Kubernetes](https://kubernetes.io/) system, and leverages Google's deep
expertise with container-based deployments.

You will create a new Phoenix application, and then you will learn how to:

*   Create an OTP release for your app using
    [Distillery](https://github.com/bitwalker/distillery)
*   Wrap your app release in a Docker image
*   Deploy your app on Google Kubernetes Engine
*   Scale and update your app using Kubernetes

This tutorial requires Elixir 1.4 and Phoenix 1.3 or later. It assumes you are
already familiar with basic Phoenix web development. For simplicity, the
tutorial app does not use Ecto or connect to a SQL database, but you can extend
it to connect to Google Cloud SQL or any other database service.

## Before you begin

Before running this tutorial, you must set up a Google Cloud Platform project,
and you need to have Docker and the Google Cloud SDK installed.

Create a project that will host your Phoenix application. You can also reuse
an existing project.

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `${PROJECT_ID}` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

1.  Enable billing for your project.

1.  Go to the [API Library](https://console.cloud.google.com/apis/library) in
    the Cloud Console. Use it to enable the following APIs:
    *   Google Cloud Container Builder API
    *   Google Kubernetes Engine API

Perform the installations:

1.  Install **Docker 17.05 or later** if you do not already have it. Find
    instructions on the [Docker website](https://www.docker.com/).

1.  Install the **[Google Cloud SDK](https://cloud.google.com/sdk/)** if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK and
    set the default project to the new project you created.

1.  Install the Kubernetes component of the Google Cloud SDK:

        gcloud components install kubectl

1.  Install **Elixir 1.4 or later** if you do not already have it. If you are
    on MacOS and have [Homebrew](https://brew.sh), you can run:

        brew install elixir

    Otherwise consult the [Elixir install](https://elixir-lang.org/install.html)
    guide for your operating system.

1.  Install the **hex**, **rebar**, and **phx_new** archives.

        mix local.hex
        mix local.rebar
        mix archive.install https://github.com/phoenixframework/archives/raw/master/phx_new.ez

1.  Install **Node.js** if you do not already have it. If you are on MacOS and
    have Homebrew, you can run:

        brew install node

    Otherwise consult the [Node download](https://nodejs.org/en/download/)
    guide for your operating system.

## Creating a new app and running it locally

In this section, you will create a new Phoenix app and make sure it runs. If
you already have an app to deploy, you can use it instead.

1.  Run the `phx.new` task to create a new Phoenix project called
    "hello". This tutorial omits Ecto for now.

        mix phx.new hello --no-ecto

    Answer "Y" when the tool asks you if you want to fetch and install
    dependencies.

1.  Go into the directory with the new application.

        cd hello

1.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port `4000`.

1.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

## Enabling releases with Distillery

Releases are the preferred way to package Elixir (and Erlang) applications for
deployment. You will configure the
[Distillery](https://github.com/bitwalker/distillery) tool to create releases
for your app.

**Note:** If you already have Distillery set up for your application, you can
skip this section. But make sure `include_erts: true` is set in your `:prod`
release configuration. This tutorial assumes ERTS is included in releases.

### Set up Distillery

1.  Add distillery to your application's dependencies. In the `mix.exs` file,
    add `{:distillery, "~> 1.5"}` to the `deps`. Then install it by running:

        mix do deps.get, deps.compile

1.  Create a default release configuration by running:

        mix release.init

1.  Prepare the Phoenix configuration for deployment by editing the prod
    config file `config/prod.exs`. In particular, set `server: true` to ensure
    the web server starts when the supervision tree is initialized. We
    recommend the following settings to start off:

        config :hello, HelloWeb.Endpoint,
          load_from_system_env: true,
          http: [port: "${PORT}"],
          check_origin: false,
          server: true,
          root: ".",
          cache_static_manifest: "priv/static/cache_manifest.json"

### Test a release

Now you can create a release to test out your configuration.

1.  Build and digest the application assets for production:

        cd assets
        npm install
        ./node_modules/brunch/bin/brunch build -p
        cd ..
        mix phx.digest

    Remember that if your app is an umbrella app, the assets directory might be
    located in one of the apps subdirectories.

1.  Build the release:

        MIX_ENV=prod mix release --env=prod

1.  Run the application from the release using:

        PORT=8080 _build/prod/rel/hello/bin/hello foreground

1.  Visit [http://localhost:8080](http://localhost:8080) to see the Phoenix
    welcome screen running locally from your release.

## Dockerizing your application

The next step is to produce a Docker image that builds and runs your
application in a Docker container. You will define this image using a
Dockerfile.

### Create a Dockerfile

Various considerations go into designing a good Docker image. The Dockerfile
used by this tutorial builds a release and runs it with Alpine Linux.
If you are experienced with Docker, you can customize your image.

1.  Create a file called `Dockerfile` in your `hello` directory. Copy the
    following content into it. Alternately, you can
    [download](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-kubernetes-google-container-engine/Dockerfile)
    a sample annotated Dockerfile to study and customize.

        FROM elixir:alpine
        ARG APP_NAME=hello
        ARG PHOENIX_SUBDIR=.
        ENV MIX_ENV=prod REPLACE_OS_VARS=true TERM=xterm
        WORKDIR /opt/app
        RUN apk update \
            && apk --no-cache --update add nodejs nodejs-npm \
            && mix local.rebar --force \
            && mix local.hex --force
        COPY . .
        RUN mix do deps.get, deps.compile, compile
        RUN cd ${PHOENIX_SUBDIR}/assets \
            && npm install \
            && ./node_modules/brunch/bin/brunch build -p \
            && cd .. \
            && mix phx.digest
        RUN mix release --env=prod --verbose \
            && mv _build/prod/rel/${APP_NAME} /opt/release \
            && mv /opt/release/bin/${APP_NAME} /opt/release/bin/start_server
        FROM alpine:latest
        RUN apk update && apk --no-cache --update add bash openssl-dev
        ENV PORT=8080 MIX_ENV=prod REPLACE_OS_VARS=true
        WORKDIR /opt/app
        EXPOSE ${PORT}
        COPY --from=0 /opt/release .
        CMD ["/opt/app/bin/start_server", "foreground"]

    **Note:** If your app is named something other than `hello`, you will need
    to modify the `APP_NAME` argument in the Dockerfile. If your app is an
    umbrella app, you will also need to modify the `PHOENIX_SUBDIR` to contain
    the path to the Phoenix application subdirectory, e.g. `apps/hello_web`.

1.  Create a file called `.dockerignore` in your `hello` directory. Copy the
    following content into it. Alternately, you can
    [download](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-kubernetes-google-container-engine/.dockerignore)
    a sample annotated file to study and customize.

        _build
        deps
        test
        assets/node_modules

    **Note:** if your app is an umbrella app, you might need to adjust the
    paths to include the build, deps, and node_modules directories of the
    constituent apps. In general, you want Docker to ignore artifacts that come
    from your development environment, so it can perform clean builds.

### Test the Dockerfile

Build the image locally and test running your application from the image:

    docker build --no-cache -t hello .
    docker run -it --rm -p 8080:8080 hello

The period at the end of the `docker build` command is required. It denotes the
root directory of the application you are building.

Visit [http://localhost:8080](http://localhost:8080) to see the Phoenix
welcome screen running locally from your Docker image.

## Deploying your application

Now you're ready to deploy your application to Kubernetes Engine!

### Build the production image

To deploy the app, you will use the
[Google Cloud Container Build](https://cloud.google.com/container-builder/)
service to build your Docker image in the cloud and store the resulting Docker
image in your project in the
[Google Cloud Container Registry](https://cloud.google.com/container-registry/).

Execute the following command to run the build:

    gcloud container builds submit --tag=gcr.io/${PROJECT_ID}/hello:v1 .

Replace `${PROJECT_ID}` with the ID of your Google Cloud Platform project.

After the build finishes, the image `gcr.io/${PROJECT_ID}/hello:v1` will be
available. You can list the images you have built in your project using:

    gcloud container images list

You can even push and pull the image directly from your registry. See the
[Container Registry how-to guides](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
for more details.

### Create a cluster

Kubernetes Engine lets you create Kubernetes clusters to host your application.
These are clusters of VMs in the cloud, managed by a Kubernetes server.

1.  Choose a cluster name. For the rest of these instructions, I'll assume that
    name is "hello-cluster".
    
1.  Choose a zone. You should 
[choose a zone](https://cloud.google.com/compute/docs/regions-zones/) 
which makes sense for you, such as `us-central1-a`.
    
1.  Create the cluster.

        gcloud container clusters create hello-cluster --num-nodes=2 --zone=us-central1-a

    This command creates a cluster of two machines. You can choose a different
    size, but two is a good starting point.

    It might take several minutes for the cluster to be created. You can check
    the cloud console at http://cloud.google.com/console, under the Kubernetes
    Engine section, to see that your cluster is running. You will also be able
    to see the individual running VMs under the Compute Engine section.
    
    Note that once the cluster is running, *you will be charged for the VM usage*.
    
1.  Configure the gcloud command-line tool to use your cluster by default, so
    you don't have to specify it every time for the remaining gcloud commands.

        gcloud config set container/cluster hello-cluster

    Replace the name if you named your cluster differently.

### Deploy to the cluster

A production deployment comprises two parts: your Docker container, and a
front-end load balancer (which also provides a public IP address.)

We'll assume that you built the image to `gcr.io/${PROJECT_ID}/hello:v1` and
you've created the Kubernetes cluster as described above.

1.  Create a deployment.

        kubectl run hello-web --image=gcr.io/${PROJECT_ID}/hello:v1 --port 8080

    This runs your image on a Kubernetes pod, which is the deployable unit in
    Kubernetes. The pod opens port 8080, which is the port your Phoenix
    application is listening on.

    You can view the running pods using:

        kubectl get pods

1.  Expose the application by creating a load balancer pointing at your pod.

        kubectl expose deployment hello-web --type=LoadBalancer --port 80 --target-port 8080

    This creates a service resource pointing at your running pod. It listens
    on the standard HTTP port 80, and proxies back to your pod on port 8080.

1.  Obtain the IP address of the service by running:

        kubectl get service

    Initially, the external IP field will be pending while Kubernetes Engine
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

        gcloud container builds submit --tag=gcr.io/${PROJECT_ID}/hello:v2 .

    Now you have two builds stored in your project, `hello:v1` and `hello:v2`.
    In general it's good practice to set the image tag for each build to a
    unique build number. This will let you identify and deploy any build,
    making updates and rollbacks easy.

1.  Set the deployment to use the new image:

        kubectl set image deployment/hello-web hello-web=gcr.io/${PROJECT_ID}/hello:v2

    This performs a rolling update of all the running pods.

1.  You can roll back to the earlier build by calling `kubectl set image`
    again, specifying the earlier build tag.

        kubectl set image deployment/hello-web hello-web=gcr.io/${PROJECT_ID}/hello:v1

**Note:** If a deployment gets stuck because an error in the image prevents
it from starting successfuly, you can recover by undoing the rollout. See the
[Kubernetes deployment documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
for more info.

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. To
clean up the resources, you can delete your Kubernetes Engine resources, or
delete the entire project.

### Deleting Kubernetes Engine resources

To delete your app from Kubernetes Engine, you must remove both the load
balancer and the Kubernetes Engine cluster.

1.  Delete the service, which deallocates the load balancer:

        kubectl delete service hello-web

1.  The load balancer will be deleted asynchronously. Wait for that process to
    complete by monitoring the output of:

        gcloud compute forwarding-rules list

    The forwarding rule will disappear when the load balancer is deleted.

1.  Delete the cluster, which deletes the resources used by the cluster,
    including virtual machines, disks, and network resources.

        gcloud container clusters delete hello-cluster

### Deleting the project

Alternately, you can delete the project in its entirety. To do so using the
gcloud tool, run:

    gcloud projects delete ${PROJECT_ID}

where `${PROJECT_ID}` is your Google Cloud Platform project ID.

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

If you want to procure a static IP address and connect your domain name, you
might find [this tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/configuring-domain-name-static-ip)
helpful.

See the [Kubernetes Engine documentation](https://cloud.google.com/kubernetes-engine/docs/)
for more information on managing Kubernetes Engine clusters.

See the [Kubernetes documentation](https://kubernetes.io/docs/home/) for more
information on managing your application deployment using Kubernetes.
