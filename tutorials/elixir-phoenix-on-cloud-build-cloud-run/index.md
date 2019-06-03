---
title: Run an Elixir Phoenix App with Google Cloud Run
description: Learn how to create a CI CD pipeline for an Elixir Phoenix app with Google Cloud Run and Google Cloud Build
author: arciola
tags: Cloud Run, Cloud Build, Elixir, Phoenix
date_published: 2019-06-3
---

**Note:** [Google Cloud Run](https://cloud.google.com/run/) is in beta. Google Cloud Platform products in beta are not covered under any SLA’s.

[Google Cloud Run](https://cloud.google.com/run/)
is an easy way to deploy your apps to the same infrastructure that powers
Google's products. Using Cloud Build, Cloud Run, and Github you can create a CI/CD pipeline for your
app written in [Elixir](http://elixir-lang.org/) with the
[Phoenix](http://phoenixframework.org/) Framework and have it up and running in minutes. 
**Note:** Due to processes being managed and throttled by Cloud Run some features may not work (websockets, presence, pubsub).

This tutorial will help you get started deploying a Phoenix app (without ecto) to Google Cloud Run using Google Cloud Build. You will create a new Phoenix application, and learn how to configure, build, deploy, and update it. 

This tutorial requires Elixir 1.5 and Phoenix 1.4 or later. It assumes you are
already familiar with basic Phoenix web development. 

## Before you begin

Before running this tutorial, take the following steps:

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new GCP project.

2.  Enable billing for your project.

3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

    Version 248.0.0 or later of the SDK is required. If you have an earlier
    version installed, you may upgrade it by running:

        gcloud components update

4. [Install git](https://help.github.com/en/articles/set-up-git#setting-up-git) for use with Github. Follow the 3 steps to setup git on your local machine.

If you have not yet installed Elixir and Phoenix, do so.

1.  Install Elixir and Node.js. If you are on macOS with Homebrew, you can run:

        brew install elixir node

    Otherwise consult the [Node download](https://nodejs.org/en/download/) and
    [Elixir install](https://elixir-lang.org/install.html) guides for your
    operating system.

2. Install the hex, rebar3, and phx_new archives:

        mix local.hex
        mix local.rebar
        mix archive.install hex phx_new 1.4.5

## Create a new app and run it locally

In this section, you will create a new Phoenix app **without** a database, and make
sure it runs locally in development. If you already have an app to deploy, you
may use it instead.

### Create a new Phoenix app

1.  Run the `phx.new` task to create a new Phoenix project called `hello`:

        mix phx.new hello --no-ecto

    Answer `Y` when the tool asks you if you want to fetch and install
    dependencies.

2.  Go into the directory with the new application:

        cd hello

3.  Run the app with the following command:

        mix phx.server

    This compiles your server and runs it on port 4000.

4.  Visit [http://localhost:4000](http://localhost:4000) to see the Phoenix
    welcome screen running locally on your workstation.

## Enable Source Control with Github

[Github](https://github.com/) is a web-based hosting service for version control using Git. It is completely free and connects to Google Cloud Platform via Github Apps.

1.  Create or login into your Github account and install the [Google Cloud Build App](https://github.com/marketplace/google-cloud-build). This gives your GCP account access to your repo.

2.  Next we will [create the new repo](https://help.github.com/en/articles/creating-a-new-repository). We suggest you create a private repo, with no Readme as Phoenix creates one for you. 

3.  Now follow the prompts to push your local Phoenix app to your new Github repo. The following steps are listed below for convenience:

        git init
        git add .
        git commit -m "first commit"
        git remote add origin https://github.com/{USERNAME}/{REPO_NAME}.git
        git push -u origin master

4. You should now see your code in the Github repository.

## Setup Cloud Build Trigger

Now you setup Cloud Build to build on every code change in your Github repo.

1.  Go to the [Cloud Build](http://console.cloud.google.com/cloud-build) and navigate to the “Triggers” page.

2.  Create a new trigger for your Phoenix app and follow the prompt. You will need to set the “Build Configuration” to Cloud Build configuration file on the trigger settings page, everything else can stay as the default. 

## Prepare your Phoenix App

You will now configure the build files for Cloud Build and Cloud Run.

1.  [Create your own dockerfile](https://cloud.google.com/cloud-build/docs/quickstart-docker) or use [this template for Phoenix](./elixir-phoenix-on-cloud-build-cloud-run/Dockerfile). This will be used by Cloud Build to build your container.

2.  Next you will need to create the Cloud Build configuration file, which we said we would use in the Cloud Build Trigger. You can [create your own build configuration file](https://cloud.google.com/cloud-build/docs/build-config), or use [this template for Phoenix](./elixir-phoenix-on-cloud-build-cloud-run/cloudbuild.yaml).

**Note:** If you use the template you will need to replace {GITHUB_USERNAME} and {REPO_NAME} on 4 different lines. 

3. Lastly, you will need to edit your .gitginore file to allow prod.secrets.exs to be included in the repo (**Note:** this step is only included to get your demo up and running. Do not use in production). Open .gitignore in the root folder and comment out the “/config/*.secret.exs” in the last line. For production ready secrets management take a look at Cloud Key Management Service.

4. Now you will push the code changes to Github.

        git add .
        git commit -m "Configuration for Cloud Build and Cloud Run"
        git push -u origin master

## Live Application

Your Phoenix application should now be live. 

1. If you visit the [Cloud Build History page](http://console.cloud.google.com/cloud-build) you should see your build either building, successfully built, or possibly failed. 

2. If if has successfully built, you can check the [Cloud Run Services page](console.cloud.google.com/run) to see if your service has successfully launched. Assuming it has, you can click the service, and then follow the URL on the page to view your Phoenix app.

**Note:** if you encountered an error on either step, [view the logs](https://cloud.google.com/run/docs/logging) to further debug the issue. Issues generally arise from misspelling.

## Update your application

Let's make a simple change and redeploy.

1.  Open the front page template
    `lib/hello_web/templates/page/index.html.eex` in your editor.
    Make a change to the HTML template.

2.  Push the changes to Github:

        git add .
        git commit -m "Homepage updates"
        git push -u origin master

Cloud Build will take care of rebuilding your app and trigger a deployment of the updated    version on successful complication. Then Cloud Run will migrating traffic to the newly deployed version.

3.  View your changes live by visiting the URL link on the Cloud Run services page.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. To clean
up the resources, you can delete the project or stop the individual services.

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

### Deleting individual services

In this tutorial, you created a Cloud Build instance and deployed a Cloud run service. Here is how to stop these two services.

1.  To delete the Cloud Build instance visit the Triggers page and delete the Trigger. This will prevent Cloud Build from running automatically on code pushes.

2. To delete the Cloud Run instance visit the Cloud Run services page, highlight the services, and select delete. This will stop the current service.

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
