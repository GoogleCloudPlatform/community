---
title: Eventarc and Workflows Integration
description: Learn how to integrate Eventarc and Worklows.
author: meteatamel
tags: Eventarc, Workflows, PubSub, AuditLog, Cloud Storage
date_published: 2021-04-15
---

Mete Atamel | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you will see how to connect
[Eventarc](https://cloud.google.com/eventarc/docs) events to
[Workflows](https://cloud.google.com/workflows/docs).

More specifically, you will see how:

1. A Pub/Sub message to a topic triggers a Cloud Run service via Eventarc.
   In turn, the Cloud Run service executes a workflow with whole HTTP request
   from Eventarc passed to the workflow.
2. A file creation in a Cloud Storage bucket triggers a Cloud Run service
   via Eventarc. In turn, the Cloud Run service executes a workflow with the
   bucket and file name.

## Objectives

* Deploy a workflow.
* Deploy a Cloud Run service to trigger a workflow.
* Create an Eventarc trigger to connect Pub/Sub topic messages to a Cloud Run service.
* Create an Eventarc trigger to connect Cloud Storage bucket events to a Cloud Run service.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Cloud Storage](https://cloud.google.com/storage)
* [Cloud Run](https://cloud.google.com/run)
* [Eventarc](https://cloud.google.com/eventarc)
* [Pub/Sub](https://cloud.google.com/pubsub)
* [Workflows](https://cloud.google.com/workflows)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to
generate a cost estimate based on your projected usage.

## Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1. Create a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/).
1. Install [DBeaver Community for Windows](https://dbeaver.io/download/).

1. Create a project in the [Cloud Console](https://console.cloud.google.com/).
1. [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1. Use [Cloud Shell][shell] or install the [Cloud SDK][sdk].
1. Enable Cloud Run, Eventarc, Pub/Sub and Workflows APIs:

        gcloud services enable run.googleapis.com eventarc.googleapis.com pubsub.googleapis.com workflows.googleapis.com

## Eventarc Pub/Sub and Workflows Integration

In this section, you will see how a Pub/Sub message to a topic triggers a
Cloud Run service via Eventarc. In turn, the Cloud Run service executes a
workflow with whole HTTP request from Eventarc passed to the workflow.

### Deploy a workflow

First, deploy the [workflow.yaml](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-pubsub/workflow.yaml). It simply
decodes and logs out the received Pub/Sub message.

Deploy workflow:

    export WORKFLOW_NAME=workflow-pubsub
    export REGION=us-central1
    gcloud workflows deploy ${WORKFLOW_NAME} --source=workflow.yaml --location=${REGION}

### Deploy a Cloud Run service to execute the workflow

Next, deploy a Cloud Run service to execute workflow. It simply executes the
workflow with the HTTP request. You can see the source code in
[trigger-workflow](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-pubsub/trigger-workflow).

Build the container:

    export PROJECT_ID=$(gcloud config get-value project)
    export SERVICE_NAME=trigger-workflow-pubsub
    gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} .

Deploy the service:

    gcloud config set run/region ${REGION}
    gcloud config set run/platform managed
    gcloud run deploy ${SERVICE_NAME} \
      --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
      --region=${REGION} \
      --allow-unauthenticated \
      --update-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},WORKFLOW_REGION=${REGION},WORKFLOW_NAME=${WORKFLOW_NAME}

### Connect a Pub/Sub topic to the Cloud Run service

Connect a Pub/Sub topic to the Cloud Run service by creating an Eventarc Pub/Sub
trigger:

    gcloud config set eventarc/location ${REGION}
    gcloud eventarc triggers create ${SERVICE_NAME} \
      --destination-run-service=${SERVICE_NAME} \
      --destination-run-region=${REGION} \
      --location=${REGION} \
      --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished"

Find out the Pub/Sub topic that Eventarc created:

    export TOPIC_ID=$(basename $(gcloud eventarc triggers describe ${SERVICE_NAME} --format='value(transport.pubsub.topic)'))

### Trigger the workflow

Send a message to the Pub/Sub topic to trigger the workflow:

    gcloud pubsub topics publish ${TOPIC_ID} --message="Hello there"

In the logs for Workflows, you should see that Workflow received the Pub/Sub
message and decoded it.

## Eventarc AuditLog-Cloud Storage and Workflows Integration

In this section, you will see how a file creation in a Cloud Storage bucket
triggers a Cloud Run service via Eventarc. In turn, the Cloud Run service
executes a workflow with the bucket and file name.

### Deploy a workflow

First, deploy the [workflow.yaml](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-auditlog-storage/workflow.yaml). It
simply logs out the bucket and file name for the storage event.

Deploy workflow:

    export WORKFLOW_NAME=workflow-auditlog-storage
    export REGION=us-central1
    gcloud workflows deploy ${WORKFLOW_NAME} --source=workflow.yaml --location=${REGION}

### Deploy a Cloud Run service to execute the workflow

Next, deploy a Cloud Run service to execute workflow. It simply executes the
workflow with the bucket and file name. You can see the source code in
[trigger-workflow](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-auditlog-storage/trigger-workflow).

Build the container:

    export PROJECT_ID=$(gcloud config get-value project)
    export SERVICE_NAME=trigger-workflow-auditlog-storage
    gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} .

Deploy the service:

    gcloud config set run/region ${REGION}
    gcloud config set run/platform managed
    gcloud run deploy ${SERVICE_NAME} \
      --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
      --region=${REGION} \
      --allow-unauthenticated \
      --update-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},WORKFLOW_REGION=${REGION},WORKFLOW_NAME=${WORKFLOW_NAME}

### Connect Cloud Storage events to the Cloud Run service

Connect Cloud Storage events to the Cloud Run service by creating an Eventarc
AuditLog trigger for Cloud Storage.

First, one-time Eventarc setup:

    export PROJECT_NUMBER="$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
        --role='roles/eventarc.eventReceiver'

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
        --role='roles/iam.serviceAccountTokenCreator'

Create the trigger:

    gcloud eventarc triggers create ${SERVICE_NAME} \
      --destination-run-service=${SERVICE_NAME} \
      --destination-run-region=${REGION} \
      --location=${REGION} \
      --event-filters="type=google.cloud.audit.log.v1.written" \
      --event-filters="serviceName=storage.googleapis.com" \
      --event-filters="methodName=storage.objects.create" \
      --service-account=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com

### Trigger the workflow

Upload a file to a bucket to trigger the workflow.

Create a bucket:

    export BUCKET="$(gcloud config get-value core/project)-eventarc-workflows"
    gsutil mb -l $(gcloud config get-value run/region) gs://${BUCKET}

Create a file in the bucket:

    echo "Hello World" > random.txt
    gsutil cp random.txt gs://${BUCKET}/random.txt

In the logs, you should see that Workflow received the Cloud Storage event.

## What's next

* Learn more about [Eventarc](https://cloud.google.com/eventarc/docs).
* Learn more about [Workflows](https://cloud.google.com/workflows/docs).