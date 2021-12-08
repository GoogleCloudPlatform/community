---
title: Mirroring Python Repositories to Artifact Registry
description: Using Storage Event Trigger in Eventarc to invoke Cloud Run to copy Python Packages from a GCS bucket to Artifact Registry
author: zhenyangbai
tags: Aritfact Registry, Google Cloud Storage, Cloud Run, Eventarc
date_published: 2021-12-08
---

Zhenyang Bai | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you set up [Eventarc](https://cloud.google.com/eventarc/) to sync Python Packages from [Google Cloud Storage](https://cloud.google.com/artifact-registry/) to [Artifact Registry](https://cloud.google.com/artifact-registry) using [Cloud Run](https://cloud.google.com/run/).

This allows a quick way to mirror the contents of another PyPI server whether on-prem or in the cloud and get started with Artifact Registry quickly.

## Architecture overview

The following diagram illustrates the architecture of the solution described in this tutorial:


![Architecture overview.](https://raw.githubusercontent.com/zhenyangbai/community/master/tutorials/gcs-artifact-registry/GCS%20-_%20Artifact%20Registry.png)


- Python Packages are uploaded to the Cloud Storage bucket.
- The Eventarc trigger sends events from the Cloud Storage bucket to the Cloud Run service.
- Cloud Run receives the event information and checks if the Python Package exists in Artifact Registry.
- If not, Cloud Run proceeds to copy the package from the Cloud Storage bucket to Artifact Registry.


## Objectives

*   Create a Cloud Storage Bucket to proxy the Python Packages
*   Create a Python & Docker Repository in Artifact Regsitry
*   Create a Service Account for Cloud Run
*   Create a Service Account for Eventarc
*   Build and create a Cloud Run Service
*   Create an Eventarc trigger to invoke Cloud run
*   Verify success of the job.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

In this tutorial, you set up [Eventarc](https://cloud.google.com/eventarc/) to sync Python Packages from [Google Cloud Storage](https://cloud.google.com/artifact-registry/) to [Artifact Registry](https://cloud.google.com/artifact-registry) using [Cloud Run](https://cloud.google.com/run/).

*   [Eventarc](https://cloud.google.com/eventarc/)
*   [Google Cloud Storage](https://cloud.google.com/artifact-registry/)
*   [Artifact Registry](https://cloud.google.com/artifact-registry)
*   [Cloud Run](https://cloud.google.com/run/)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

### Set up your Google Cloud project

To complete this tutorial, you need a
[Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project).
We recommend that you create a new project specifically for this tutorial.

You must have the [project owner](https://cloud.google.com/iam/docs/understanding-roles#basic-definitions) role for the project.

1.  In [Cloud Shell](https://cloud.google.com/shell), set a project ID environment variable, replacing `[YOUR_PROJECT_ID]` with your
    [Google Cloud project ID](https://cloud.google.com/resource-manager/docs/creating-managing-projects#before_you_begin):

        export PROJECT_ID=[YOUR_PROJECT_ID]

2.  Set the working project for the `gcloud` environment:

        gcloud config set project $PROJECT_ID


## Enabling Google APIs

```
gcloud services enable \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  eventarc.googleapis.com \
  logging.googleapis.com \
  cloudresourcemanager.googleapis.com
```

## Setup Up Env Variables

```
export REGION=asia-southeast1
export PYTHON_REPO_NAME=python-repo
export CONTAINER_REPO_NAME=docker-registry
export CONTAINER_NAME=ar-migrate
export BUCKET_NAME=python-repo-bucket
export REGION=asia-southeast1
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects list --filter="$(gcloud config get-value project)" --format="value(PROJECT_NUMBER)")
export STORAGE_SERVICE_ACCOUNT="$(gsutil kms serviceaccount -p ${PROJECT_ID})"
export SERVICE_NAME=ar-migrate
export RUN_SERVICE_ACCOUNT=run-artifact
export RUN_ROLE_NAME="roles/artifactregistry.writer"
export TRIGGER_SERVICE_ACCOUNT=trigger-run
export TRIGGER_ROLE_NAME="roles/run.invoker"
```

## Setup Repositories and Storage Bucket

1. [Create a Python Repository](https://cloud.google.com/artifact-registry/docs/python/quickstart#create)

```
gcloud artifacts repositories create ${PYTHON_REPO_NAME} \
    --repository-format=python \
    --location=${REGION} \
    --description="Python package repository"
```

2. [Create a Docker Repository](https://cloud.google.com/artifact-registry/docs/docker/quickstart#create)

```

gcloud artifacts repositories create ${CONTAINER_REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Docker repository"
```

3. [Create a Storage Bucket](https://cloud.google.com/eventarc/docs/run/quickstart-storage#create-bucket)
```
gsutil mb -l ${REGION} gs://${BUCKET_NAME}/
```

## Setup Service Accounts and Roles

1. Grant the pubsub.publisher role to the Cloud Storage service account
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${STORAGE_SERVICE_ACCOUNT}" \
    --role='roles/pubsub.publisher'
```

2. If you enabled the Pub/Sub service account on or before April 8, 2021, grant the iam.serviceAccountTokenCreator role to the Pub/Sub service account
```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
    --role='roles/iam.serviceAccountTokenCreator'
```

3. [Create a Cloud Run Service Account for Artifact Registry and Storage Bucket](https://cloud.google.com/artifact-registry/docs/access-control#grant-repo)
```
gcloud iam service-accounts create ${RUN_SERVICE_ACCOUNT} \
    --description="Cloud Run Service Account for Artifact Registry" \
    --display-name="Cloud Run Service Account for Artifact Registry"

gcloud artifacts repositories add-iam-policy-binding ${PYTHON_REPO_NAME} \
    --location ${REGION} \
    --member="serviceAccount:${RUN_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role=${RUN_ROLE_NAME}
    
gsutil iam ch serviceAccount:${RUN_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com:legacyBucketReader gs://${BUCKET_NAME}
gsutil iam ch serviceAccount:${RUN_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com:objectViewer gs://${BUCKET_NAME}
```

4. [Create a EventArc Service Account for invoking Cloud Run](https://cloud.google.com/run/docs/securing/managing-access)
```
gcloud iam service-accounts create ${TRIGGER_SERVICE_ACCOUNT} \
    --description="EventArc Service Account for Triggering Cloud Run" \
    --display-name="EventArc Service Account for Triggering Cloud Run"
```

## Deploying

1. Build the container and upload it to Cloud Build
```
git clone https://github.com/GoogleCloudPlatform/community.git
cd community/tutorials/gcs-artifact-registry
gcloud builds submit --tag $REGION-docker.pkg.dev/${PROJECT_ID}/${CONTAINER_REPO_NAME}/${CONTAINER_NAME}:v1
```

2. Deploy the container image to Cloud Run
```
gcloud run deploy ar-migrate \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${CONTAINER_REPO_NAME}/${CONTAINER_NAME}:v1 \
    --no-allow-unauthenticated \
    --service-account=${RUN_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars=PROJECT=${PROJECT_ID},BUCKET=${BUCKET_NAME},REGION=${REGION},REGISTRY_NAME=${PYTHON_REPO_NAME} \
    --no-use-http2 \
    --binary-authorization default \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID}
```

3. Enable EventArc Service Account to Invoke the specific Cloud Run Service
```
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
    --member="serviceAccount:${TRIGGER_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role=${TRIGGER_ROLE_NAME}
```

3. [Create an Eventarc trigger](https://cloud.google.com/eventarc/docs/run/quickstart-storage#trigger-setup)
```
gcloud eventarc triggers create storage-events-trigger \
     --location=${REGION} \
     --destination-run-service=${SERVICE_NAME} \
     --destination-run-region=${REGION} \
     --event-filters="type=google.cloud.storage.object.v1.finalized" \
     --event-filters="bucket=${BUCKET_NAME}" \
     --service-account="${TRIGGER_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
```

## Testing Artifact Registry with Vertex Workbench

With Artifact Registry setup, you would be able to run the below command from Vertex Workbench to install python packages from Artifact Registry.
Example [here](https://github.com/zhenyangbai/community/blob/master/tutorials/gcs-artifact-registry/ar-migrate.ipynb).
```
pip3 install --index-url https://${REGION}-python.pkg.dev/${PROJECT_ID}/${PYTHON_REPO_NAME}/simple [PACKAGE_NAME]
```

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
