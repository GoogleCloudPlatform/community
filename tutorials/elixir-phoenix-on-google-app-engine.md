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

1.  Install Elixir and NodeJS. If you are on MacOS with Homebrew, you can run

        brew install node elixir

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

## Deploy your application

Now you will deploy your new app to App Engine.

1.  Create a file called `app.yaml` at the root of the application directory,
    with the following contents:

        env: flex
        runtime: gs://elixir-runtime/elixir.yaml

    This configuration selects the Elixir Runtime, an open source App Engine
    runtime that knows how to build Elixir and Phoenix applications. You can
    find more information about this runtime at its
    [Github page](https://github.com/GoogleCloudPlatform/elixir-runtime).

2.  Run the following command to deploy your app:

        gcloud app deploy

    If this is the first time you have deployed to App Engine in this project,
    gcloud will prompt you for a region. You may choose the default of
    "us-central", or select a region close to your location.

    The Elixir Runtime will take care of building your application in the
    cloud, including installing mix dependencies, compiling to BEAM files, and
    even using brunch to build and digest your assets.

    Deployment will also take a few minutes to requisition and configure the
    needed resources, especially the first time you deploy.

3.  Once the deploy command has completed, you can visit
    `http://YOUR_PROJECT_ID.appspot.com` to see your app running in
    production on App Engine.

## Update your application

Let's make a simple change and redeploy.

1.  Open the front page template
    `lib/appengine_example_web/templates/page/index.html.eex` in your editor.
    Make a change to the HTML template.

2.  Run the deployment command again:

        gcloud app deploy

    App Engine and the Elixir Runtime will take care of rebuilding your app,
    deploying the updated version, and switching traffic from the old to the
    new.

3.  Visit `http://YOUR_PROJECT_ID.appspot.com` to see your changes live.

## Clean up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. You can
accomplish this either by deleting the project, or by stopping the App Engine
service.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial.

To delete the project:

1.  In the Cloud Platform Console, go to the
    [project settings page](https://console.cloud.google.com/iam-admin/settings).
2.  Click the button to select a project, and select the project you created
    for this tutorial.
3.  Click the trash icon "shut down".

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
to Google Cloud, and examples of communicating with Google APIs from Elixir.

See the [App Engine documentation](https://cloud.google.com/appengine/docs/flexible/)
for more information on the features of App Engine, including scaling, health
checks, infrastructure customization, and so forth.
