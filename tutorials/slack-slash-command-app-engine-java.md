---
title: Running a Slack Slash command on App Engine using Java
description: Run a "hello, world" Slack slash command on App Engine using Java.
author: tswast
tags: App Engine, Slack
date_published: 2017-05-26
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to build and deploy a 
[slash command for Slack](https://api.slack.com/slash-commands) on [Google Cloud](https://cloud.google.com/).

Slash commands provide a way to call external web services from a [Slack](https://slack.com/)
conversation. For example, the 
[Giphy app](https://get.slack.help/hc/en-us/articles/204714258-Add-Giphy-search-to-Slack) can be run by
`/giphy` in a conversation.

## Objectives

- Deploy a Java application to the [App Engine flexible environment][flexible].
- Create a [slash command for Slack](https://api.slack.com/slash-commands).
- Load tokens from the [Google Cloud Runtime Config API](https://cloud.google.com/deployment-manager/runtime-configurator/)

[flexible]: https://cloud.google.com/appengine/docs/flexible/java/

## Before you begin

1.  Follow the [Quickstart for Java in the App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/java/quickstart) to
    set up your environment to deploy the sample applications App Engine.
    1.  Download and install the [Cloud SDK](https://cloud.google.com/sdk/docs/).
    1.  [Install and configure Apache Maven](http://maven.apache.org/index.html).
    1.  [Create a new Google Cloud project, or use an existing
        one](https://console.cloud.google.com/project).
    1.  [Enable billing for your
        project](https://support.google.com/cloud/answer/6293499#enable-billing).
    1. Initialize the Cloud SDK:

           gcloud init

1.  Create a [new Slack team](https://slack.com/), or use a team where you have
    permissions to add custom integrations.

## Costs

This tutorial uses billable components of Google Cloud, including App Engine flexible environment.

Use the [Pricing Calculator][cloud-pricing] to generate a cost estimate based on
your projected usage.

Slack is free for up to 10 apps and integrations. Check the [Slack pricing
page][slack-pricing] for details.

[cloud-pricing]: https://cloud.google.com/products/calculator
[slack-pricing]: https://slack.com/pricing

## Getting the sample code

Get the latest sample code from GitHub using Git or download the repository as a ZIP file.
([Download](https://github.com/GoogleCloudPlatform/slack-samples/archive/master.zip))

    git clone https://github.com/GoogleCloudPlatform/slack-samples.git

The `java/command/1-start` directory contains a simple application, which you will
modify to support Slack slash commands.

    cd java/command/1-start

## Create a Slack app

To create a new Slack app, go to the [app management
page](https://api.slack.com/apps) and click **Create new app**.

1.  Give the app a name, such as "Hello World".
1.  Choose the Slack team for development and where you will eventually install it.

### Create a slash command

1.  On the left navigation panel, click **Slash commands** > **Create new command**.
1.  Enter a command name, such as `/greet`.
1.  Enter `https://YOUR_PROJECT.appspot.com/hello` as your request URL, replacing `YOUR_PROJECT`
    with your Google Cloud project ID.
1.  Enter a short description, such as "Sends a greeting."

### Install the command to your workspace

1.  On the left navigation panel, click **Basic information**.
1.  Expand **Install your app to your workspace**, then click **Install app to workspace**.

## Deploying your app

Your app requires some configuration. This sample uses the [RuntimeConfig
API](https://cloud.google.com/deployment-manager/runtime-configurator/) to store configuration
values, such as secret tokens.

### Create a configuration

Using the command-line [Cloud SDK](https://cloud.google.com/sdk/), create a new runtime
configuration:

    gcloud beta runtime-config configs create slack-samples-java

### Copy the verification token

To ensure that HTTP requests to your app originate from Slack, Slack provides a
validation token. You check that the token field of an incoming request matches
the expected value.

1.  Select your app on the [app management page](https://api.slack.com/apps).
1.  Go to the **Basic information** page.
1.  Scroll to **App credentials** and copy the **Verification token** text.

### Add verification token to the configuration

Create a variable called `slack-token` in the runtime configuration. Use the
Cloud SDK from the command-line to add the variable:

    gcloud beta runtime-config configs variables set \
        slack-token "YOUR-TOKEN-VALUE" \
        --is-text --config-name slack-samples-java

Replace `YOUR-TOKEN-VALUE` with the verification token value you copied from the
Slack app management page.

### [Optional] Running locally

To run the application locally, use the Maven Spring Boot plugin:

    mvn clean spring-boot:run

View the app at http://localhost:8080.

Since Slack requires a public URL to send webhooks, you may wish to [use a
service like ngrok to test your Slack application
locally](https://api.slack.com/tutorials/tunneling-with-ngrok).

### Deploying to App Engine

To deploy the app to App Engine, run the following command:

    mvn clean appengine:deploy

After the deploy finishes (can take up to 10 minutes), you can view your
application at https://YOUR_PROJECT.appspot.com, where YOUR_PROJECT is your
Google Cloud project ID. You can see the new version deployed on the App Engine
section of the Cloud Console.

For a more detailed walkthrough, see the [Quickstart for Java in the App Engine flexible environment](https://cloud.google.com/appengine/docs/flexible/java/quickstart).

## Trying the slash command

When you run the slash command, Slack will send a request to your app and show the result.

-   Type `/greet` in your Slack team.

You should see the text `Hello, world.` in response.

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this
tutorial.

1. [Disable the App Engine application](https://cloud.google.com/appengine/kb/#disable).
2. Remove the app from your Slack team.

## Next steps

- Explore the other [Slack APIs](https://api.slack.com/).
- Check out the [other Slack samples for Google Cloud](https://github.com/GoogleCloudPlatform/slack-samples)
