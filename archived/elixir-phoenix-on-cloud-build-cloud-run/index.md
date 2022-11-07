---
title: Run an Elixir Phoenix app with Cloud Run
description: Learn how to create a CI/CD pipeline for an Elixir Phoenix app with Cloud Run and Cloud Build.
author: marciola
tags: Cloud Run, Cloud Build, Elixir, Phoenix
date_published: 2019-06-06
---

Michael Arciola | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Run](https://cloud.google.com/run/) is an easy way to deploy your apps to the same infrastructure that powers
Google's products. Using Cloud Build, Cloud Run, and GitHub, you can create a CI/CD pipeline for your
app written in [Elixir](http://elixir-lang.org/) with the [Phoenix Framework](http://phoenixframework.org/) and have it up
and running in minutes. 

**Note:** Due to processes being managed and throttled by Cloud Run, some features (such as websockets, presence, and Pub/Sub) may not work.

This tutorial will help you to get started deploying a Phoenix app (without Ecto) to Cloud Run using Cloud Build. You will
create a new Phoenix application and learn how to configure, build, deploy, and update it. 

This tutorial requires Elixir 1.5 and Phoenix 1.4 or later. It assumes that you are already familiar with basic Phoenix web
development. 

## Before you begin

Before running this tutorial, take the following steps:

1.  Use the [Cloud Console](https://console.cloud.google.com/) to create a new Google Cloud project.

1.  Enable billing for your project.

1.  Install the [Cloud SDK](https://cloud.google.com/sdk/).

    Make sure that you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

    Version 248.0.0 or later of the SDK is required. If you have an earlier
    version installed, you may upgrade it by running the following command:

        gcloud components update

1.  [Install git](https://help.github.com/en/articles/set-up-git#setting-up-git) for use with Github. Follow the
    steps to set git up on your local machine.

    If you have not yet installed Elixir and Phoenix, do so.

1.  Install Elixir and Node.js. If you are on macOS with Homebrew, you can run the following command:

        brew install elixir node

    Otherwise, see the [Node download](https://nodejs.org/en/download/) and
    [Elixir install](https://elixir-lang.org/install.html) guides for your operating system.

1.  Install the hex, rebar3, and phx_new archives:

        mix local.hex
        mix local.rebar
        mix archive.install hex phx_new 1.4.5

## Create a new app and run it locally

In this section, you will create a new Phoenix app *without* a database and make
sure that it runs locally in development. If you already have an app to deploy, you
may use it instead.

### Create a new Phoenix app

1.  Run the `phx.new` task to create a new Phoenix project called `hello`:

        mix phx.new hello --no-ecto

    Answer `Y` when the tool asks you if you want to fetch and install
    dependencies.

1.  Go into the directory with the new application:

        cd hello

1.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port 4000.

1.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

## Enable source control with Github

[GitHub](https://github.com/) is a web-based hosting service for version control using Git. It is free and connects to
Google Cloud through GitHub Apps.

1.  Create or log in to your GitHub account and install the
    [Google Cloud Build app](https://github.com/marketplace/google-cloud-build).
    
    This app gives your Google Cloud account access to your repository.

1.  [Create the new repository](https://help.github.com/en/articles/creating-a-new-repository). We suggest
    that you create a private repository, with no Readme file, because Phoenix creates one for you. 

3.  Follow the prompts to push your local Phoenix app to your new GitHub repository. The steps are listed here
    for convenience:

        git init
        git add .
        git commit -m "first commit"
        git remote add origin https://github.com/{USERNAME}/{REPO_NAME}.git
        git push -u origin master

You should now see your code in the GitHub repository.

## Set up a Cloud Build trigger

Now you set up Cloud Build to build on every code change in your GitHub repository.

1.  Go to the Cloud Build [**Triggers** page](https://console.cloud.google.com/cloud-build/triggers) in the Cloud Console.

1.  Create a new trigger for your Phoenix app, following the on-screen prompts. On the **Trigger settings** page, 
    set the **Build configuration** to **Cloud Build configuration file**; everything else can stay at the default values. 

## Prepare your Phoenix app

You will now configure the build files for Cloud Build and Cloud Run.

1.  [Create your own dockerfile](https://cloud.google.com/cloud-build/docs/quickstart-docker) or use
    [this template for Phoenix](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-cloud-build-cloud-run/Dockerfile).
    
    This will be used by Cloud Build to build your container.

1.  Create the Cloud Build configuration file, which is used by the Cloud Build trigger. You can
    [create your own build configuration file](https://cloud.google.com/cloud-build/docs/build-config),
    or use [this template for Phoenix](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/elixir-phoenix-on-cloud-build-cloud-run/cloudbuild.yaml).

    **Note:** If you use the template, replace {GITHUB_USERNAME} and {REPO_NAME} on 4 different lines. 

1.  Edit your `.gitginore` file to allow `prod.secrets.exs` to be included in the repository.

    **Note:** This step is only included to get your demo up and running. Do not use in production.

    Open `.gitignore` in the root folder and comment out the `/config/*.secret.exs` in the last line.
    For production-ready secrets management, take a look at Cloud Key Management Service.

1. Push the code changes to GitHub, using the following commands:

        git add .
        git commit -m "Configuration for Cloud Build and Cloud Run"
        git push -u origin master

## Live application

Your Phoenix application should now be live. 

If you visit the [Cloud Build History page](http://console.cloud.google.com/cloud-build), you should see your build
either building, successfully built, or possibly failed. 

If it has successfully built, you can check the [Cloud Run page](https://console.cloud.google.com/run) to see if your 
service has successfully launched. When it has, click the service and follow the URL on the page to view your Phoenix app.

**Note:** If you encountered an error, [view the logs](https://cloud.google.com/run/docs/logging) to debug the issue.
Issues generally arise from misspelling.

## Update your application

Let's make a simple change and redeploy.

1.  Open the front page template `lib/hello_web/templates/page/index.html.eex` in your editor.

1.  Make a change to the HTML template.

2.  Push the changes to GitHub:

        git add .
        git commit -m "Homepage updates"
        git push -u origin master

    Cloud Build will take care of rebuilding your app and trigger a deployment of the updated version on successful 
    compilation. Then Cloud Run will migrate traffic to the newly deployed version.

1.  View your changes live by visiting the URL on the Cloud Run services page.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the individual services.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. To do so using `gcloud`, run the following command:

    gcloud projects delete [YOUR_PROJECT_ID]

where `[YOUR_PROJECT_ID]` is your Google Cloud project ID.

**Warning**: Deleting a project has the following consequences: If you used an existing project, you'll also delete any 
other work you've done in the project. You can't reuse the project ID of a deleted project. If you created a custom project 
ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs 
that use the project ID, such as an appspot.com URL, remain available.

### Deleting individual services

In this tutorial, you created a Cloud Build instance and deployed a Cloud Run service. Here is how to stop these two 
services.

*   To delete the Cloud Build instance, visit the **Triggers** page and delete the trigger. This will prevent Cloud Build 
    from running automatically on code pushes.

*   To delete the Cloud Run instance, visit the Cloud Run services page, highlight the services, and select delete. This
    will stop the current service.

## Next steps

The [Elixir Samples](https://github.com/GoogleCloudPlatform/elixir-samples)
repository contains a growing set of sample Elixir applications ready to deploy
to Google Cloud and examples of communicating with Google APIs from Elixir.

See the [Cloud Build documentation](https://cloud.google.com/cloud-build/docs/)
for more information on Cloud Build features including dockerfiles, build configurations,
and build automation.

See the [Cloud Run documentation](https://cloud.google.com/run/docs/)
for more information on Cloud Run features including services, health checks,
and traffic migration.

You can also try the tutorials on deploying Phoenix applications
[to Kubernetes Engine](https://cloud.google.com/community/tutorials/elixir-phoenix-on-kubernetes-google-container-engine), [to Compute Engine](https://cloud.google.com/community/tutorials/elixir-phoenix-on-google-compute-engine), and [to App Engine Flex](https://cloud.google.com/community/tutorials/elixir-phoenix-on-google-app-engine).
