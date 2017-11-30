---
title: Run an Elixir Phoenix app on the Google App Engine Flexible Environment
description: Learn how to deploy a Phoenix app to the Google App Engine flexible environment.
author: dazuma
tags: App Engine, Elixir, Phoenix
date_published: 2017-10-11
---

The [Google App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. Using the open source
[Elixir Runtime](https://github.com/GoogleCloudPlatform/elixir-runtime), your
app written in [Elixir](http://elixir-lang.org/) with the
[Phoenix](http://phoenixframework.org/) Framework can be up and running in App
Engine in minutes.

This tutorial will help you get started deploying a Phoenix app to App Engine.
You will create a new Phoenix application, and learn how to configure, deploy,
and update it. For simplicity, this tutorial app will not use Ecto or connect
to a SQL database, but you can extend it to connect to Google Cloud SQL or any
other database service.

This tutorial requires Elixir 1.4 and Phoenix 1.3 or later. It assumes you are
already familiar with basic Phoenix web development.

## Before you begin

Before running this tutorial, take the following steps:

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project.

2.  Enable billing for your project.

3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

    Version 175.0.0 or later of the SDK is required.

If you have not yet installed Elixir and Phoenix, do so:

1.  Install Elixir and Node.js. If you are on MacOS with Homebrew, you can run

        brew install elixir node

    Otherwise consult the [Node download](https://nodejs.org/en/download/) and
    [Elixir install](https://elixir-lang.org/install.html) guides for your
    operating system.

2. Install the hex and phx_new archives.

        mix local.hex
        mix archive.install https://github.com/phoenixframework/archives/raw/master/phx_new.ez

## Create a new app and run it locally

In this section, you will create a new Phoenix app and make sure it runs. If
you already have an app to deploy, you may use it instead.

1.  Run the `phx.new` task to create a new Phoenix project called
    "appengine_example". This tutorial will omit Ecto for now.

        mix phx.new appengine_example --no-ecto

    Answer "Yes" when the tool asks you if you want to fetch and install
    dependencies.

2.  Go into the directory with the new application.

        cd appengine_example

3.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port 4000.

4.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

## Enable releases with Distillery

Releases are the Elixir community's preferred way to package Elixir (and
Erlang) applications for deployment. You will configure the
[Distillery](https://github.com/bitwalker/distillery) tool to create releases
for your app.

**Note:** If you already have Distillery set up for your application, you can
skip this section. But make sure `include_erts: true` is set in your `:prod`
release configuration. The Elixir Runtime assumes ERTS is included in releases.

### Set up Distillery

1.  Add distillery to your application's dependencies. In the `mix.exs` file,
    add `{:distillery, "~> 1.5"}` to the `deps`. Then install it by running:

        mix do deps.get, deps.compile

2.  Create a default release configuration by running:

        mix release.init

    This will create a file `rel/config.exs`. You can examine and edit it if
    you wish, but the defaults should be sufficient for this tutorial.

3.  Prepare the Phoenix configuration for deployment by editing the prod
    config file `config/prod.exs`. In particular, set `server: true` to ensure
    the web server starts when the supervision tree is initialized. We
    recommend the following settings to start off:

        config :appengine_example, AppengineExampleWeb.Endpoint,
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

2.  Build the release:

        MIX_ENV=prod mix release --env=prod

3.  Run the application from the release using:

        PORT=8080 _build/prod/rel/appengine_example/bin/appengine_example foreground

4.  Visit [http://localhost:8080](http://localhost:8080) to see the Phoenix
    welcome screen running locally from your release.

## Deploy your application

Now you will deploy your new app to App Engine.

1.  Create a file called `app.yaml` at the root of the application directory,
    with the following contents:

        env: flex
        runtime: gs://elixir-runtime/elixir.yaml
        runtime_config:
          release_app: appengine_example

    This configuration selects the Elixir Runtime, an open source App Engine
    runtime that knows how to build Elixir and Phoenix applications. You can
    find more information about this runtime at its
    [Github page](https://github.com/GoogleCloudPlatform/elixir-runtime).
    The configuration also tells the runtime to build and deploy a Distillery
    release for the application `appengine_example`.

2.  Run the following command to deploy your app:

        gcloud app deploy

    If this is the first time you have deployed to App Engine in this project,
    gcloud will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    The Elixir Runtime will take care of building your application in the
    cloud, including installing mix dependencies, compiling to BEAM files, and
    even using Brunch to build and digest your assets.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

3.  Once the deploy command has completed, you can run

        gcloud app browse

    to see your app running in production on App Engine.

## Update your application

Let's make a simple change and redeploy.

1.  Open the front page template
    `lib/appengine_example_web/templates/page/index.html.eex` in your editor.
    Make a change to the HTML template.

2.  Run the deployment command again:

        gcloud app deploy

    App Engine and the Elixir Runtime will take care of rebuilding your app,
    deploying the updated version, and migrating traffic to the newly deployed
    version.

3.  View your changes live by running

        gcloud app browse

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the App Engine service.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. To do so using `gcloud`, run:

    gcloud projects delete [YOUR_PROJECT_ID]

where `[YOUR_PROJECT_ID]` is your Google Cloud Platform project ID.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that
use the project ID, such as an appspot.com URL, remain available.

### Stopping App Engine services

To disable an App Engine service:

1.  In the Cloud Platform Console, go to the
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
