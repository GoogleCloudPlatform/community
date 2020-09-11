---
title: Conditional IAM roles with Cloud Run
description: Learn how to set up conditional IAM roles for Cloud Run applications.
author: mike-ensor
tags: cloud-run
date_published: 2020-09-14
---

## Overview

This tutorial shows you how to run a managed Cloud Run application with a Google Service Account using conditional IAM roles using a Cloud Storage bucket.

Applications that use Google Cloud services such as Pub/Sub, Cloud Storage, and Cloud SQL require authentication. Authentication and authorization are provided 
using Cloud Identity Access Management (IAM) through a combination of roles and accounts. Google Service Accounts are often used to provide an authentication and
authorization mechanism for Google Cloud resources. More information can be found in the [official documentation](https://cloud.google.com/docs/authentication).

Authentication is often tied to a series of conditional parameters such as the time of day or day of the week to enhance security measures preventing 
applications from accessing resources outside of compliance or governance rules. Within Google Cloud, this concept is implemented as
IAM [conditional role bindings](https://cloud.google.com/iam/docs/managing-conditional-role-bindings). Managed Cloud Run has an advanced option allowing a Google
Service Account to act as the user authenticating with other Google Cloud resources such as Cloud Storage.

This tutorial demonstrates how to set up Service Accounts with conditional IAM role bindings on Cloud Run using a Cloud Storage bucket, as illustrated in the 
following diagram.

![Architectural overview](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-conditional-iam/cloud-run-conditional-iam.png)

## Objectives

1.  Create a simple application that lists contents of a [Cloud Storage][gcs] bucket.
1.  Create a [Google Service Account][gsa] to manage the application's Google Service interaction.
1.  Bind the Google Service Account with a [conditional IAM role][conditional-iam] `storage.objectViewer`.

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
    * roles/iam.serviceAccountAdmin - Enables the user to create & manage the lifecycle of Google Service Accounts
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
1. Create a Google Service Account (GSA)
1. Create managed Cloud Run instance using the GSA
1. Setup conditional IAM permissions

### Workflow Variables

The following variables will be used in some or all of the below workflow steps. All variables are required unless noted.

* `PROJECT_ID` - Google project ID where the managed Cloud Run instance is to be deployed to
    * `export PROJECT_ID=$(gcloud config get-value core/project)`
* `REGION` - Region to deploy managed Cloud Run instance application into
    * >NOTE: Check list of regions in Always Free tier to ensure costs are included
    * `export REGION=us-west1`
* `GSA_NAME` - Name of Google Service Account to be created and used for the Cloud Run instance
    * Alphanumeric and dashed name consisting of 5-20 characters.
    * `export GSA_NAME=bucket-list-gsa`

### 1. Creating Cloud Storage Bucket

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
#### Sample Output
```text
$ gsutil ls gs://${BUCKET}
gs://cloud-run-tutorial-bucket-*****/item-1.txt
gs://cloud-run-tutorial-bucket-*****/item-2.txt
gs://cloud-run-tutorial-bucket-*****/item-3.txt
gs://cloud-run-tutorial-bucket-*****/item-4.txt
gs://cloud-run-tutorial-bucket-*****/item-5.txt
```

### 2. Create Application Container

A simple Golang app used to list-display the contents of a GCS bucket can be built and pushed to the project's private [Google Container Registry](https://cloud.google.com/container-registry). The recommended application to deploy is [Cloud Run Bucket App](https://gitlab.com/mike-ensor/cloud-run-bucket-app/). More details on how to modify and deploy the app can be found within the README file.  This tutorial will deploy an opinionated and summarized version of this app.

#### Create & Deploy Container
```bash
# Clone Repository
git clone https://gitlab.com/mike-ensor/cloud-run-bucket-app

# Build & Push image
gcloud builds submit --substitutions=_PROJECT_ID=${PROJECT_ID}

# Verify image was pushed (if "Listed 0 items", build was not successful)
gcloud container images list --filter="name:(*cloud-run-bucket-app)" --repository=gcr.io/${PROJECT_ID}
```

### 3. Create & Setup Google Service Account (GSA)

Creating a [Google Service Account](https://cloud.google.com/iam/docs/service-accounts) (also known as GSA) for an application allows granular and specific access to Google managed resources thus reducing the security threat.

```bash
export GSA_NAME="bucket-list-gsa"

gcloud iam service-accounts create ${GSA_NAME} \
    --description="Service account for Cloud Storage Bucket Listing App" \
    --display-name="${GSA_NAME}"
```

#### Sample Output
```text
$ gcloud iam service-accounts create ${GSA_NAME} \
>     --description="Service account for Cloud Storage Bucket Listing App" \
>     --display-name="${GSA_NAME}"
Created service account [bucket-list-gsa].
```

### 4. Create managed Cloud Run service w/ GSA

```bash
export SERVICE=bucket-list-app # Or choose a new name for the app
export REGION=us-west1 # Region to deploy
export IMAGE_NAME=$(gcloud container images list --filter="name:(*cloud-run-bucket-app)" --repository=gcr.io/${PROJECT_ID} --format="value(name)")

gcloud run deploy ${SERVICE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --image ${IMAGE_NAME} \
    --service-account ${GSA_NAME}
```

#### Verify App Deployed

1. After deploy, open a browser given the URL in the output.

    ```bash
    # Get the previously setup bucket name
    echo $BUCKET
    ```

1. Add the following query parameter (ie, to the end of the URL): `https://${PROJECT_ID}...run.app/?bucket=<bucket name>`
    > NOTE: This SHOULD display an error indicating a `403` error (access forbidden)

1. **Keep this browser open** (Browser used later in this tutorial)

### 5. Setup Conditional IAM Role Bindings

The last step is to add permissions to view the bucket contents to the GSA created in step 3. Following the [official conditional IAM documentation](https://cloud.google.com/iam/docs/managing-conditional-role-bindings#iam-conditions-add-binding-gcloud):

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

# Bind role and condition to GSA
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer" \
    --condition="expression=${EXPRESSION},description=${DESCRIPTION},title=${TITLE}"
```

### 6. Verify

>Note: IAM conditional conditions CAN take 1-2 minutes to go "live". If permission isn't granted immediately wait a minute and try again.

1. Using the same browser window as in step 4-1. Simply refresh the browser to see the contents.

1. Wait for 5 minutes and refresh page to see the "403" error code returned.

## Conclusion

This tutorial has shown that creating a Cloud Run application, specifying a Google Service Account to control access to resources using Conditional IAM can be a part of a comprehensive security layer.

## Clean up

The following will remove any of the "cost" attributing resources.

### Removing the Cloud Run service

```bash
gcloud run services delete ${SERVICE}
```

### Removing the GCS bucket

```bash
gsutil rm -r gs://${BUCKET}
```

### Remove App Service Account

```bash
gcloud iam service-accounts delete ${GSA_NAME}
```

### Remove App Images

```bash
gcloud container images delete ${IMAGE_NAME} --force-delete-tags --quiet
```

[gsa]: https://cloud.google.com/iam/docs/service-accounts
[gcs]: https://cloud.google.com/storage
[conditional-iam]: https://cloud.google.com/iam/docs/managing-conditional-role-bindings

