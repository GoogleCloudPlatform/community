---
title: Control access for a Cloud Run application with conditional IAM roles
description: Learn how to set up conditional IAM roles for Cloud Run applications.
author: mike-ensor
tags: authentication
date_published: 2020-09-14
---

Mike Ensor | Solutions Architect | Google 

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to control access to resources for a Cloud Run application using a Google service account and conditional IAM roles.

Applications that use Google Cloud services such as Pub/Sub, Cloud Storage, and Cloud SQL require authentication. Authentication and authorization are provided 
using Cloud Identity and Access Management (IAM) through a combination of roles and accounts. Google service accounts are often used to provide an authentication
and authorization mechanism for Google Cloud resources. For more information, see the [official documentation](https://cloud.google.com/docs/authentication).

Authentication is often tied to a series of conditional parameters such as time of day or day of the week to enhance security measures, preventing 
applications from accessing resources outside of compliance or governance rules. Within Google Cloud, this concept is implemented as
IAM [conditional role bindings](https://cloud.google.com/iam/docs/managing-conditional-role-bindings). Managed Cloud Run has an advanced option allowing a Google
service account to act as the user authenticating with other Google Cloud resources such as Cloud Storage.

This tutorial demonstrates how to set up service accounts with conditional IAM role bindings on Cloud Run using a Cloud Storage bucket, as illustrated in the 
following diagram.

![Architectural overview](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-conditional-iam/cloud-run-conditional-iam.png)

## Objectives

1.  Create a simple application that lists the contents of a [Cloud Storage](https://cloud.google.com/storage) bucket.
1.  Create a [service account](https://cloud.google.com/iam/docs/service-accounts) to manage the application's Google service interactions.
1.  Bind the service account with a [conditional IAM role](https://cloud.google.com/iam/docs/managing-conditional-role-bindings), `storage.objectViewer`.

## Costs

The Cloud Run portion of this tutorial fits into the [always free](https://cloud.google.com/free) tier of Google Cloud if implemented using the selected regions
with the suggested application. For more information, see [Cloud Run pricing criteria](https://cloud.google.com/run/pricing).

You can use the [pricing calculator](https://cloud.google.com/products/calculator/#id=638ffec4-1903-47c2-8616-1cc37a83a1f5) to estimate your costs.

Cloud Storage usage for this tutorial fits within the [always free](https://cloud.google.com/free) limits (below 5GB of regional storage) by storing 
small text files.

## Prerequisites and setup

This tutorial requires a [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and an associated billing account. 
Though the costs are within the [always free](https://cloud.google.com/free) tier, a billing account is required. We recommend that you create a new project for 
this tutorial, so that cleaning up the tutorial's resources at the end is easiest.

You execute commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell). If you prefer to execute the commands on your local machine, you must
[install the Cloud SDK and gsutil](https://cloud.google.com/storage/docs/gsutil_install#sdk-install).

The `gcloud` user must have the following permissions for this tutorial:

  * `roles/editor` or `roles/owner`
  * `roles/iam.serviceAccountAdmin` (enables the user to create and manage the life cycle of Google service accounts)
  * `roles/storage.admin` (enables the user to create and manage the lifecycle of Cloud Storage buckets)
  * `roles/cloudbuild.builds.editor` (enables the user to create and manage the life cycle of Cloud Build instances)

## Solution

### Summary of the workflow

1. Set variables and enable APIs and services.
1. Create a protected Cloud Storage bucket and add files to it.
1. Create an application container to access the Cloud Storage bucket.
1. Create a Google service account.
1. Create a managed Cloud Run instance using the service account.
1. Set up conditional IAM permissions.

### Set environment variables

1.  Set the project ID of the Google Cloud project where the managed Cloud Run instance is to be deployed to:

        export PROJECT_ID=$(gcloud config get-value core/project)

1.  Set the region to deploy the managed Cloud Run application into:

        export REGION=us-west1

    Check the list of regions in the [always free](https://cloud.google.com/free/docs/gcp-free-tier) tier to ensure that costs are included.

1.  Set the name of the Google service account to be created and used for the Cloud Run instance:

        export GSA_NAME=bucket-list-gsa

    Use alphanumeric characters and dashes, for a name between 5 and 20 characters.

### Enable APIs and services

Run the following command to enable the necessary APIs and services:

    gcloud services enable \
        cloudbuild.googleapis.com \
        storage-component.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com

### Create a Cloud Storage bucket and add files to it

1.  Generate a random lowercase alphanumeric suffix:

        export SUFFIX=$(head -3 /dev/urandom | tr -cd '[:alnum:]' | cut -c -5 | awk '{print tolower($0)}')

1.  Set a variable to contain the name of the bucket:
   
        export BUCKET="cloud-run-tutorial-bucket-${SUFFIX}"
        
1.  Create the bucket:

        gsutil mb gs://${BUCKET}

1.  Add text documents to the bucket:

        for i in {1..5}; do echo "task $i" > item-$i.txt; done
        gsutil cp *.txt gs://${BUCKET}

1.  List the bucket contents to verify that they were created:

        gsutil ls gs://${BUCKET}

The output should look similar to the following:

```text
gs://cloud-run-tutorial-bucket-*****/item-1.txt
gs://cloud-run-tutorial-bucket-*****/item-2.txt
gs://cloud-run-tutorial-bucket-*****/item-3.txt
gs://cloud-run-tutorial-bucket-*****/item-4.txt
gs://cloud-run-tutorial-bucket-*****/item-5.txt
```

### Create and deploy an application container

In this section, you build and push a simple app written in the Go programming language to the project's private
[Google Container Registry](https://cloud.google.com/container-registry). The app used for this tutorial
([Cloud Run Bucket App](https://gitlab.com/mike-ensor/cloud-run-bucket-app/)) lists the contents of a Cloud Storage bucket.

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

    gcloud iam service-accounts create ${GSA_NAME} \
        --description="Service account for Cloud Storage bucket listing app" \
        --display-name="${GSA_NAME}"

The output should be similar to the following:

    Created service account [bucket-list-gsa].

### Create a managed Cloud Run service with the Google service account

Run the following commands to create a Cloud Run service with a Google service account:

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

In this section, you give the Google service account permission to view the bucket contents.

1.  Set time zone to UTC for date calculations:

        export TIME_ZONE=GMT/UTC
        
1.  Set a time interval in seconds equal to 5 minutes:

        export MINUTES_IN_FUTURE=$((60*5))

1.  Create a human-readable description and title for the condition:

        export DESCRIPTION="Example conditional that is true until ${MINUTES_IN_FUTURE} minutes from the time of execution"
        export TITLE="Expire In ${MINUTES_IN_FUTURE} minutes"

1.  Create a timestamp of the current time:

        export TIMESTAMP=$(TZ=${TIME_ZONE} date +"%FT%T.00Z")
        
1.  Build a condition expression that tests whether `(time.now < TIMESTAMP+5 minutes)`:

        export EXPRESSION="request.time < timestamp(\"${TIMESTAMP}\") + duration(\"${MINUTES_IN_FUTURE}s\")"

1.  Validate the condition:

        gcloud alpha iam policies lint-condition --expression="${EXPRESSION}" --title="${TITLE}" --description="${DESCRIPTION}"

1.  Bind the role and condition to the Google service account:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="roles/storage.objectViewer" \
            --condition="expression=${EXPRESSION},description=${DESCRIPTION},title=${TITLE}"

For more information, see
[Managing conditional role bindings](https://cloud.google.com/iam/docs/managing-conditional-role-bindings#iam-conditions-add-binding-gcloud)

### Verify

IAM conditions can take a few minutes to take effect. If permission isn't granted immediately, wait a minute and try again.

1. Using the same browser window that you used to verify that the app was deployed, refresh the page to see the contents.

1. Wait for 5 minutes and refresh page to see the `403` error code returned.

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
