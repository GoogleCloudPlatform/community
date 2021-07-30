---
title: Migrate from Cloud Functions to Cloud Run with Cloud Buildpacks
description: Learn how to migrate from Cloud Functions to Cloud Run with no code changes
author: tth
tags:
date_published: 2021-07-30
---

Tan Tze Hon | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial is for engineers who deploy code to [Cloud Functions](https://cloud.google.com/functions) and want to migrate their code to [Cloud Run](https://cloud.google.com/run).

You will learn how to use the [Functions Framework](https://cloud.google.com/functions/docs/functions-framework) and Functions Framework [buildpack](https://github.com/GoogleCloudPlatform/buildpacks#functions-framework-buildpacks) to migrate code written for Cloud Functions to Cloud Run without making any code changes.

Basic knowledge of Cloud Functions and Cloud Run is required.

## Objectives

* Introduce the Functions Framework
* Test code written for Cloud Functions locally using the Functions Framework
* Deploy code to Cloud Functions
* Migrate Cloud Functions code to Cloud Run using the Functions Framework buildpack

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Run](https://cloud.google.com/run)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easier, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://cloud.google.com/billing/docs/how-to/modify-project#enable-billing)

1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient
    permissions to use the services listed above.

## Using Cloud Shell

This tutorial uses the following tool packages:

* [`gcloud`](https://cloud.google.com/sdk/gcloud)
* [`pip3`](https://pip.pypa.io/en/stable/)
* [`pack`](https://buildpacks.io/docs/tools/pack/)
* [`docker`](https://www.docker.com/)

Because [Cloud Shell](https://cloud.google.com/shell) automatically includes these packages, you run the commands in this tutorial in Cloud Shell, so that you don't need to install these packages locally.

## Preparing your environment

### Open Cloud Shell

Open Cloud Shell by clicking the **Activate Cloud Shell** button in the upper-right corner of the Cloud Console.

### Get the sample code

The sample code for this tutorial is in the
[Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/migrate-cloud-functions-cloud-run-buildpacks

## Implementation steps

### Introduce the Functions Framework

The Functions Framework lets you write lightweight functions that run in many different environments, such as:

* Your local development machine
* Cloud Functions
* Cloud Run

Using the Functions Framework, you can write portable code that works across these environments without making additional code changes.

### Set the environment variables

1.  Modify the `set_variables.sh` file to set the required environment variables:

        PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
        REGION=${REGION}
        FUNCTION_NAME=${FUNCTION_NAME}

1. Run the script to set the environment variables:

        source set_variables.sh

### Enable the required APIs

1.  Enable the required APIs:

        gcloud services enable \
          cloudfunctions.googleapis.com \
          cloudbuild.googleapis.com \
          run.googleapis.com

### Isolate project dependencies

1. Use the `venv` command to create a virtual copy of the entire Python installation. This tutorial creates a virtual copy in a folder named `venv`, but you can specify any name for the folder:

        python3 -m venv venv

1. Set your shell to use the `venv` paths for Python by activating the virtual environment:

        source venv/bin/activate

### Install the Functions Framework

1. Install the Functions Framework via `pip`:

        pip3 install -r requirements.txt

### Test your function locally with the Functions Framework

The Functions Framework makes it easy to test your code locally without needing to deploy it to Cloud Functions beforehand.
1. In your current terminal, start your function locally using the Functions Framework:

        functions-framework --target hello --debug

1. In another terminal, send a request to your local function:

        curl localhost:8080

1. You should get back:

        Hello world!

   Stop your function in the previous terminal by entering `Ctrl-c`.

### Deploy your function to Cloud Functions

1. Deploy the function on your local machine to Cloud Functions:

        gcloud functions deploy ${FUNCTION_NAME} \
          --entry-point hello \
          --region ${REGION} \
          --runtime python39 \
          --trigger-http \
          --allow-unauthenticated

1. Test your deployed function:

        FUNCTION_URL="$(gcloud functions describe $FUNCTION_NAME --region ${REGION} | awk '/url:/ {print $2}')"
        curl "${FUNCTION_URL}"

1. You should get back:

        Hello world!

### Understand what happens when a Cloud Function is deployed

When you deploy a Cloud Function, [two main things](https://cloud.google.com/functions/docs/running/overview#abstraction_layers) happen:

1. Cloud Functions uses the Functions Framework to unmarshal incoming HTTP requests into language-specific function invocations. This is what allows you to test your function as a locally-runnable HTTP service, and is what you have done in the previous steps.

1. Cloud Native buildpacks are then used to wrap the HTTP service created by the Function Framework and build them into runnable Docker containers, which then run on Cloud Functions' container-based architecture. You will learn how to do this using Cloud Native buildpacks next.

### Build a container image of your Cloud Functions code

1. Use the Functions Framework buildpack to build a container image of your Cloud Functions code:

        pack build \
          --builder gcr.io/buildpacks/builder:v1 \
          --env GOOGLE_FUNCTION_SIGNATURE_TYPE=http \
          --env GOOGLE_FUNCTION_TARGET=hello \
          ${FUNCTION_NAME}

### Test your container image locally

1. Test your Cloud Functions container image locally:

        docker run --rm -p 8080:8080 ${FUNCTION_NAME}

1. In another terminal, send a request to your local function:

        curl localhost:8080

1. You should get back:

        Hello world!

   Stop your function in the previous terminal by entering `Ctrl-c`.

### Publish your container image

1. Publish the build image to the cloud directly with `pack`:

        pack build \
          --builder gcr.io/buildpacks/builder:v1 \
          --publish gcr.io/${PROJECT_ID}/${FUNCTION_NAME} \
          --env GOOGLE_FUNCTION_SIGNATURE_TYPE=http \
          --env GOOGLE_FUNCTION_TARGET=hello

### Deploy container to Cloud Run

1. Deploy your Cloud Function to Cloud Run:

        gcloud run deploy ${FUNCTION_NAME} \
          --image gcr.io/${PROJECT_ID}/${FUNCTION_NAME} \
          --platform managed \
          --region ${REGION} \
          --allow-unauthenticated

1. Visit your service:

        SERVICE_URL="$(gcloud run services describe $FUNCTION_NAME --region ${REGION} | awk '/URL:/ {print $2}')"
        curl "${SERVICE_URL}"

1. You should get back:

        Hello world!

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following effects:

* Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, delete selected resources inside the project instead of deleting the whole project.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

1.  In the Cloud Console, go to the [**Manage resources page**](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

-  Learn how to
   [use Cloud Run and Go to create a customizable serverless proxy for Cloud Storage](https://cloud.google.com/community/tutorials/cloud-run-golang-gcs-proxy).
-  Learn more about how to [rate-limit serverless functions with Redis and VPC Connector](https://cloud.google.com/community/tutorials/cloud-functions-rate-limiting).
-  Try out other Google Cloud features for yourself. Have a look at those [tutorials](https://cloud.google.com/docs/open-tutorials).
