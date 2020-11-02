---
title: Running a Botkit Slack bot on Google Kubernetes Engine
description: Learn how to run a Botkit Slack bot on Google Kubernetes Engine.
author: tswast
tags: Kubernetes Engine, Node.js, Botkit, Slack
date_published: 2017-02-03
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to build a [Slack bot](https://api.slack.com/bot-users)
using the [Botkit toolkit](https://howdy.ai/botkit/) and run it on [Google
Kubernetes Engine](https://cloud.google.com/kubernetes-engine/).

You will build a "Hello, World" Slack bot that responds with a greeting in
response to messages.

## Objectives

1. Create a bot internal integration in Slack.
1. Build a Node.js image in Docker.
1. Upload a Docker image to a private Google Container Registry.
1. Run a Slack bot on Google Kubernetes Engine.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- Google Kubernetes Engine
- Compute Engine (with Google Kubernetes Engine)
- Cloud Storage (with Google Container Registry)

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1.  Set up your development environment.
    1.  Select or create a [Google Cloud][console] project.
        [Go to the projects page][projects].
    1.  Enable billing for your project. [Enable billing][billing].
    1.  Install the [Cloud SDK][sdk].
    1.  Authenticate `gcloud` with Google Cloud.

            gcloud init

    1.  Install [Node.js](https://nodejs.org/en/). See [how to prepare a Node.js
        development
        environment](https://cloud.google.com/community/tutorials/how-to-prepare-a-nodejs-dev-environment)
        for more detailed instructions.
    1.  Install [Docker](https://www.docker.com/products/overview).
1.  [Create a new Slack team][new-slack-team], or use one you already have if
    you have permissions to add new integrations to it.

[console]: https://console.cloud.google.com/
[projects]: https://console.cloud.google.com/project
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing
[sdk]: https://cloud.google.com/sdk/
[new-slack-team]: https://slack.com/create

## Getting the sample code

The code for this tutorial is [hosted on GitHub][repo].

1.  Clone the repository with Git or [download and extract the code as a ZIP file][repo-zip].

        git clone https://github.com/googlecodelabs/cloud-slack-bot.git

1.  Change to the sample code directory `cloud-slack-bot/start`.

        cd cloud-slack-bot/start

1.  Install the dependencies, including Botkit. Run this command in the
    `cloud-slack-bot/start` directory.

        npm install

[repo]: https://github.com/googlecodelabs/cloud-slack-bot
[repo-zip]: https://github.com/googlecodelabs/cloud-slack-bot/archive/master.zip

## Creating a Slack bot

A [bot user][bot-user] can listen to messages on Slack, post messages, and
upload files. In this tutorial, you will create a bot post a simple greeting
message.

1.  Create a [new Slack app](https://api.slack.com/apps).
    1.  Give the app a name, such as "Kittenbot".
    1.  Choose the Slack team where you want it installed.
1.  Add a new bot user to the app.
    1.  Select **Bot users** under the features heading on the left-hand side
        navigation of the app configuration page.
    1.  Click the **Add a bot user** button.
    1.  Give it a nice username, like @kittenbot.
    1.  This tutorial uses the Realtime Messaging (RTM) API, so keep the
        **Always show the bot as online** option selected as **Off**. The bot
        user will show as online only when there is a connection from the bot.
    1.  Click the **Add bot user** button.
1.  Get the OAuth access token to allow the bot to connect to your team.
    1.  Select **OAuth & Permissions** under the features heading on the
        left-hand side navigation of the app configuration page.
    1.  Click the **Reinstall app** button. This will reinstall the app to your
        team and add the bot user you just created.
    1.  Click the **Copy** button to copy the **Bot user OAuth access token**
        text into your clipboard. 

        You'll use the token in the next step. Don't worry. You can come back
        this configuration page from the [apps management
        page](https://api.slack.com/apps) if you need to get this token again.

[Be careful](https://api.slack.com/docs/oauth-safety) with your bot user OAuth
access token. Treat it like you would any other secret token. Do not store
tokens in version control or share them publicly.

[bot-user]: https://api.slack.com/bot-users

## Running the bot locally

To run the bot locally on your development machine,


1.  Edit the [kittenbot.js
    file](https://github.com/googlecodelabs/cloud-slack-bot/blob/master/start/kittenbot.js)
    and enter your Slack bot token.

1.  Run your bot using Node.js.

        node kittenbot.js

    In your Slack team, you should now see that Kitten Bot is online. If you do
    not see Kitten Bot in your direct messages list, open a direct message to the
    bot with the + icon.

    ![open direct message](https://storage.googleapis.com/gcp-community/tutorials/run-botkit-on-google-container-engine/open-direct-message.png)

    ![add kittenbot](https://storage.googleapis.com/gcp-community/tutorials/run-botkit-on-google-container-engine/open-direct-message-2.png)

1.  Say hello to `@kittenbot` in a direct message (or if you added Kitten Bot
    to a channel, the bot will respond to mentions there, too). It should meow
    back at you.

    ![meow](https://storage.googleapis.com/gcp-community/tutorials/run-botkit-on-google-container-engine/meow.png)

1.  In your terminal, press Control-C to stop the bot server.

## Loading the API token from a file

Hard-coding an API token in the source code makes it likely to accidentally
expose your token by publishing it to version control. Instead, you can load
the token from a file, which is in the `.gitignore` file to prevent accidentally
checking it into version control.

1.  Write your API token to a plain text file called `slack-token` (no file
    extension).

1.  Modify
    [kittenbot.js](https://github.com/googlecodelabs/cloud-slack-bot/blob/master/step-1-token-file/kittenbot.js)
    to load the API token from the path specified by the `slack_token_path`
    environment variable.

        cp ../step-1-token-file/kittenbot.js kittenbot.js

1.  Run the bot locally to test it out.

        export slack_token_path=./slack-token
        node kittenbot.js

    You should see the bot online again in Slack and be able to chat with it.

1.  Press Ctrl-C to shut down the bot.

## Containerizing your bot

Use Docker to containerize your bot. A Docker image bundles all of your
dependencies (even the compiled ones) so that it can run in a lightweight
sandbox.

### Building a Docker container image

1.  Create the
    [Dockerfile](https://github.com/googlecodelabs/cloud-slack-bot/blob/master/step-2-docker/Dockerfile).

        cp ../step-2-docker/Dockerfile Dockerfile

1.  Save your Google Cloud Project ID to the `PROJECT_ID` environment variable.
    To [get your project ID with the Cloud
    SDK](http://stackoverflow.com/a/35606433/101923), run

        export PROJECT_ID=$(gcloud config list --format 'value(core.project)')

1.  Build the Docker image.

        docker build -t gcr.io/${PROJECT_ID}/slack-codelab:v1 .

    This step takes some time to download and extract everything.

### Running a Docker container locally

1.  Run the newly-created container image as a daemon.

        docker run -d \
            -v $(pwd)/:/config \
            -e slack_token_path=/config/slack-token \
            gcr.io/${PROJECT_ID}/slack-codelab:v1

    The `-v` argument mounts the current directory as a volume inside the
    container to give it access to the `slack-token` file. The `-e` argument
    sets the `slack_token_path` environment variable within the running
    container.

    See the [full documentation for the `docker
    run`](https://docs.docker.com/engine/reference/run/) command for details.

1.  You should see that Kitten Bot is online again.

### Stopping a Docker container

1.  Get the ID of the running container.

        docker ps

1.  Stop the container. Replace the docker container ID (`fab8b7a0d6ee` in the
    example) with the ID of your container.

        docker stop fab8b7a0d6ee

### Pushing a Docker image to Google Container Registry

Now that the image works as intended, push it to the [Google Container
Registry])(https://cloud.google.com/container-registry/), a private repository
for your Docker images.

    gcloud docker -- push gcr.io/${PROJECT_ID}/slack-codelab:v1

If all goes well, you should be able to see the container image listed in the
[Google Cloud console](https://console.cloud.google.com/gcr).

Your Docker image is now published to your private repository, which
Kubernetes can access and orchestrate.

## Deploying a bot to Kubernetes Engine

Now that the Docker image is in Google Container Registry, you can run the
[`gcloud docker -- pull`
command](https://cloud.google.com/container-registry/docs/pulling) to save this
image on any machine and run it with the Docker command-line tool.

If you want to make sure your bot keeps running after it is started, you'll have
to run another service to monitor your Docker container and restarts it if it
stops. This gets even harder if you want to make sure the bot keeps running even
if the machine it is running on fails.

Kubernetes solves this. You tell it that you want there to always be a replica
of your bot running, and the Kubernetes master will keep that target state. It
starts the bot up when there aren't enough running, and shuts bot replicas down
when there are too many.

### Creating a Kubernetes cluster with Kubernetes Engine

A Kubernetes Engine cluster is a managed Kubernetes cluster. It consists of a
Kubernetes master API server hosted by Google and a set of worker nodes. The
worker nodes are Compute Engine virtual machines.

Create a cluster with two
[n1-standard-1](https://cloud.google.com/compute/docs/machine-types) nodes (this
will take a few minutes to complete):

    gcloud container clusters create my-cluster \
          --num-nodes=2 \
          --zone=us-central1-f \
          --machine-type n1-standard-1

Alternatively, you could create this cluster [via the Cloud
Console](https://console.cloud.google.com/kubernetes/add).

### Deploying to Kubernetes Engine

Kubernetes has a [Secrets](https://kubernetes.io/docs/user-guide/secrets/#creating-a-secret-using-kubectl-create-secret)
API for storing secret information such as passwords that containers need at
runtime. Create a secret to store your Slack API token.

    kubectl create secret generic slack-token --from-file=./slack-token

Next, create a [Kubernetes
Deployment](https://kubernetes.io/docs/user-guide/deployments/) for your bot. A
deployment describes how to configure the container and configures a replication
controller to keep the bot running.

1.  Copy the [deployment.yaml](https://github.com/googlecodelabs/cloud-slack-bot/blob/master/step-3-kubernetes/slack-codelab-deployment.yaml) file.

        cp ../step-3-kubernetes/slack-codelab-deployment.yaml slack-codelab-deployment.yaml

2.  Modify the image name in `slack-codelab-deployment.yaml` with your project
    ID.

        # Replace PROJECT_ID with your project ID.
        image: gcr.io/PROJECT_ID/slack-codelab:v1

3.  Deploy your bot to Kubernetes.

        kubectl create -f slack-codelab-deployment.yaml --record

4.  Check that the bot is running.

        kubectl get pods

    When the bot is running, the output will be similar to

        NAME                             READY     STATUS    RESTARTS   AGE
        slack-codelab-3871250905-dknvp   1/1       Running   0          3m

    You should also see that the bot is online in Slack.

**Troubleshooting** See the Kubernetes documentation for help with [debugging
a pod that is stuck
pending](https://kubernetes.io/docs/user-guide/debugging-pods-and-replication-controllers/).

## Cleaning up

Congratulations. You now have a Slack bot running on Google Kubernetes Engine.

You can follow these steps to clean up resources and save on costs.

1.  Delete the Deployment (which also deletes the running pods).

        kubectl delete deployment slack-codelab

2.  Delete your cluster.

        gcloud container clusters delete my-cluster

    This deletes all of the Compute Engine instances that are running the
    cluster.

3.  Delete the Docker registry storage bucket hosting your image(s).

    1.  List the Cloud Storage buckets to get the bucket path.

            gsutil ls

        Command output

            gs://artifacts.[PROJECT_ID].appspot.com/

    2.  Delete the bucket and all the images it contains.

            gsutil rm -r gs://artifacts.${PROJECT_ID}.appspot.com/

Of course, you can also delete the entire project but you would lose any billing
setup you have done (disabling project billing first is required). Additionally,
deleting a project will only happen after the current billing cycle ends.

## Next steps

- Learn more about Kubernetes with the [Kubernetes interactive
  tutorials](https://kubernetes.io/docs/tutorials/kubernetes-basics/).
- Try out other [Slack samples for Google Cloud](https://github.com/GoogleCloudPlatform/slack-samples).
- Read the [Slack API reference](https://api.slack.com/) for other ways to
  integrate your app with Slack.
