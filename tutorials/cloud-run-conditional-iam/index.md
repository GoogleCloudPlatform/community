---
title: Manage a Cloud Run application with conditional IAM roles
description: Learn how to set up conditional IAM roles for Cloud Run applications.
author: mike-ensor
tags: cloud-run
date_published: 2020-09-14
---

## Overview

This tutorial shows you how to run a managed Cloud Run application with a Google service account using conditional IAM roles using a Cloud Storage bucket. This 
tutorial shows that creating a Cloud Run application and specifying a Google service account to control access to resources using conditional IAM roles can be 
part of a comprehensive security layer.

Applications that use Google Cloud services such as Pub/Sub, Cloud Storage, and Cloud SQL require authentication. Authentication and authorization are provided 
using Cloud Identity and Access Management (IAM) through a combination of roles and accounts. Google service accounts are often used to provide an authentication
and authorization mechanism for Google Cloud resources. For more information, see the [official documentation](https://cloud.google.com/docs/authentication).

Authentication is often tied to a series of conditional parameters such as the time of day or day of the week to enhance security measures preventing 
applications from accessing resources outside of compliance or governance rules. Within Google Cloud, this concept is implemented as
IAM [conditional role bindings](https://cloud.google.com/iam/docs/managing-conditional-role-bindings). Managed Cloud Run has an advanced option allowing a Google
service account to act as the user authenticating with other Google Cloud resources such as Cloud Storage.

This tutorial demonstrates how to set up service accounts with conditional IAM role bindings on Cloud Run using a Cloud Storage bucket, as illustrated in the 
following diagram.

![Architectural overview](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-conditional-iam/cloud-run-conditional-iam.png)

## Objectives

1.  Create a simple application that lists contents of a [Cloud Storage](https://cloud.google.com/storage) bucket.
1.  Create a [service account](https://cloud.google.com/iam/docs/service-accounts) to manage the application's Google Service interaction.
1.  Bind the service account with a [conditional IAM role](https://cloud.google.com/iam/docs/managing-conditional-role-bindings), `storage.objectViewer`.

## Prerequisites and setup

The following details are intended for helping to set up the development environment and understanding the costs associated with the tutorial.

* Costs
    * The Cloud Run portion of this tutorial fits into the [Always Free](https://cloud.google.com/free) tier of Google Cloud if implemented using the selected regions & suggested application and the application usage is exclusively used for the tutorial. See [Cloud Run pricing criteria](https://cloud.google.com/run/pricing) for more information around Cloud Run pricing. [Review the pre-filled pricing calculator](https://cloud.google.com/products/calculator/#id=638ffec4-1903-47c2-8616-1cc37a83a1f5).
    * Cloud Storage bucket costs are up to you, but can easily be constrained into the [Always Free](https://cloud.google.com/free) tier (below 5GB of regional storage). Storing small text files is a simple method to eliminate Cloud Storage costs and still show a sufficient amount of files in a Cloud Storage bucket.
* Google Cloud Configuration
    * This tutorial requires a [Google Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and an associated billing account. While the costs are within the [Always Free](https://cloud.google.com/free) tier, a billing account is required.
    * >Note: Using a test project specifically for this tutorial is recommended (optional)
* Executing commands on either Local Machine or Cloud Shell
    * [Cloud Shell](https://cloud.google.com/shell) (preferred)
        * No extra installation required
    * On a local machine
        * Requires a BASH or ZSH shell
        * Installation and authentication of [Google Cloud SDK](https://cloud.google.com/sdk/install) `gcloud` is required
            * Once the binary is installed, run `gcloud init` and follow the prompts to authenticate `gcloud`
        * Install `gsutil` using `gcloud` by running: `gcloud components install gsutil`
* Tutorial gcloud user must have the following permissions
    * roles/editor or roles/owner
    * roles/iam.serviceAccountAdmin - Enables the user to create & manage the lifecycle of Google service accounts
    * roles/storage.admin - Enables the user to create & manage lifecycle of Cloud Storage Buckets
    * roles/cloudbuild.builds.editor - Enables the user to create & manage lifecycle of Cloud Build instances
* Enabled API & Services
    ```bash
        gcloud services enable \
            cloudbuild.googleapis.com \
            storage-component.googleapis.com \
            run.googleapis.com \
            containerregistry.googleapis.com
    ```

## Solution

### Overview of the workflow

1. Create a protected Cloud Storage bucket
1. Create an application container to access Cloud Storage bucket
1. Create a Google service account.
1. Create managed Cloud Run instance using the service account.
1. Setup conditional IAM permissions

### Workflow Variables

The following variables will be used in some or all of the below workflow steps. All variables are required unless noted.

* `PROJECT_ID` - Google project ID where the managed Cloud Run instance is to be deployed to
    * `export PROJECT_ID=$(gcloud config get-value core/project)`
* `REGION` - Region to deploy managed Cloud Run instance application into
    * >NOTE: Check list of regions in Always Free tier to ensure costs are included
    * `export REGION=us-west1`
* `GSA_NAME` - Name of Google service account to be created and used for the Cloud Run instance
    * Alphanumeric and dashed name consisting of 5-20 characters.
    * `export GSA_NAME=bucket-list-gsa`

### Create a Cloud Storage bucket

```bash
# Generate random lower-case alphanumeric suffix
export SUFFIX=$(head -3 /dev/urandom | tr -cd '[:alnum:]' | cut -c -5 | awk '{print tolower($0)}')
# BUCKET variable
export BUCKET="cloud-run-tutorial-bucket-${SUFFIX}"
# Create bucket
gsutil mb gs://${BUCKET}
# Add text documents to bucket
for i in {1..5}; do echo "task $i" > item-$i.txt; done
gsutil cp *.txt gs://${BUCKET}
# Verify contents
gsutil ls gs://${BUCKET}
```
The output should look similar to the following:

```text
gs://cloud-run-tutorial-bucket-*****/item-1.txt
gs://cloud-run-tutorial-bucket-*****/item-2.txt
gs://cloud-run-tutorial-bucket-*****/item-3.txt
gs://cloud-run-tutorial-bucket-*****/item-4.txt
gs://cloud-run-tutorial-bucket-*****/item-5.txt
```

### Create and deply an application container

A simple app written in the Go programming language used to list the contents of a Cloud Storage bucket can be built and pushed to the project's private
[Google Container Registry](https://cloud.google.com/container-registry). The recommended application to deploy is
[Cloud Run Bucket App](https://gitlab.com/mike-ensor/cloud-run-bucket-app/). More details on how to modify and deploy the app can be found in the
README file. In this tutorial, you deploy a summarized version of this app.

1.  Clone the repository:

        git clone https://gitlab.com/mike-ensor/cloud-run-bucket-app

1.  Build and push the image:

        gcloud builds submit --substitutions=_PROJECT_ID=${PROJECT_ID}

1.  Verify that the image was pushed:

        gcloud container images list --filter="name:(*cloud-run-bucket-app)" --repository=gcr.io/${PROJECT_ID}

     If the output says `Listed 0 items`, then the build was not successful.

### Create and set up a Google service account

Creating a [Google service account](https://cloud.google.com/iam/docs/service-accounts) for an application allows granular and specific access to Google-managed
resources, thus reducing the security threat.

    export GSA_NAME="bucket-list-gsa"

    gcloud iam service-accounts create ${GSA_NAME} \
        --description="Service account for Cloud Storage bucket listing app" \
        --display-name="${GSA_NAME}"

The output should be similar to the following:

    Created service account [bucket-list-gsa].

### Create a managed Cloud Run service with the Google service account

Run the following commands to create a Cloud Run service with a Google service account:

1.  Set the name of the app:

        export SERVICE=bucket-list-app

1.  Set the region to which to deploy the app:

        export REGION=us-west1
        
1.  Set the image name:

        export IMAGE_NAME=$(gcloud container images list --filter="name:(*cloud-run-bucket-app)" --repository=gcr.io/${PROJECT_ID} --format="value(name)")

1.  Deploy the app:

        gcloud run deploy ${SERVICE} \
            --platform managed \
            --region ${REGION} \
            --allow-unauthenticated \
            --image ${IMAGE_NAME} \
            --service-account ${GSA_NAME}

#### Verify that the app has been deployed

1.  Open a browser and go to the URL given in the output.

1.  Get the bucket name:

        echo $BUCKET

1. Add the `?bucket=[YOUR_BUCKET_NAME]` query parameter to the end of the URL: `https://${PROJECT_ID}...run.app/?bucket=[YOUR_BUCKET_NAME]`
   
   This should display an error indicating a `403` (access forbidden) error.

1. Keep this browser window open, because you will use it in a later step to verify conditional IAM role bindings.

### Set up conditional IAM role bindings

In this section, you give the Google service account permission to view the bucket contents. Following the
[official conditional IAM documentation](https://cloud.google.com/iam/docs/managing-conditional-role-bindings#iam-conditions-add-binding-gcloud):

```bash
# Best practices use UTC for date calculations
export TIME_ZONE=GMT/UTC
export MINUTES_IN_FUTURE=$((60*5)) # 5 minutes

# Condition Description and Title (human readable, required fields)
export DESCRIPTION="Example conditional that is true until ${MINUTES_IN_FUTURE} minutes from the time of execution"
export TITLE="Expire In ${MINUTES_IN_FUTURE} minutes"

# Create a timestamp of NOW
export TIMESTAMP=$(TZ=${TIME_ZONE} date +"%FT%T.00Z")
# Build Condition Expression: if (time.now < TIMESTAMP+5 minutes)
export EXPRESSION="request.time < timestamp(\"${TIMESTAMP}\") + duration(\"${MINUTES_IN_FUTURE}s\")"

# Lint/Validate condition
gcloud alpha iam policies lint-condition --expression="${EXPRESSION}" --title="${TITLE}" --description="${DESCRIPTION}"

# Bind role and condition to Google service account
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer" \
    --condition="expression=${EXPRESSION},description=${DESCRIPTION},title=${TITLE}"
```

### Verify

IAM conditions can take a few minutes to take effect. If permission isn't granted immediately, wait a minute and try again.

1. Using the same browser window as in step 4-1. Simply refresh the browser to see the contents.

1. Wait for 5 minutes and refresh page to see the "403" error code returned.

## Clean up

To avoid incurring charges to your Google Cloud account, remove the resources used in this tutorial:

1.  Remove the Cloud Run service:

        gcloud run services delete ${SERVICE}

1.  Remove the Cloud Storage bucket:

        gsutil rm -r gs://${BUCKET}

1.  Remove the service account:

        gcloud iam service-accounts delete ${GSA_NAME}

1.  Remove the app image:

        gcloud container images delete ${IMAGE_NAME} --force-delete-tags --quiet
