---
title: Integrate Eventarc and Workflows
description: Learn how to integrate Eventarc and Worklows to trigger Cloud Run in response to Pub/Sub and Cloud Storage activity.
author: meteatamel
tags: Eventarc, Workflows, AuditLog, Cloud Storage
date_published: 2021-05-07
---

Mete Atamel | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to connect [Eventarc](https://cloud.google.com/eventarc/docs) events to
[Workflows](https://cloud.google.com/workflows/docs).

In this tutorial, you deploy two workflows, Cloud Run services to run the workflows, and Eventarc triggers to initiate the workflows. In the first example,
you use an Eventarc trigger that responds to a Pub/Sub message to a topic. In the second example, you use an Eventarc trigger that
responds to the creation of a file in a Cloud Storage bucket.

**Important**: You can now trigger Workflows directly using Eventarc without Cloud Run. For details, see the
[eventarc-pubsub](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-pubsub)
and
[eventarc-storage](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-storage)
examples. However, this tutorial is still useful if you want to perform additional data transformation and processing in Cloud Run before invoking
Workflows.

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

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  In the Cloud Console, activate [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell).

    You run the commands in this tutorial on the Cloud Shell command line.

1.  Enable Cloud Run, Eventarc, Pub/Sub, and Workflows APIs:

        gcloud services enable run.googleapis.com eventarc.googleapis.com pubsub.googleapis.com workflows.googleapis.com

1.  Clone the sample repository:

        git clone https://github.com/GoogleCloudPlatform/eventarc-samples.git

    The sample repository includes the samples for Eventarc.

1.  Go to the directory for this tutorial in the cloned repository:

        cd eventarc-samples/eventarc-workflows-integration/

## Create a workflow that responds to a Pub/Sub message

In this section, you see how a Pub/Sub message to a topic triggers a Cloud Run service with Eventarc and how the Cloud Run
service executes a workflow with an HTTP request from Eventarc.

1.  Deploy the workflow defined in the
    [`eventarc-pubsub-cloudrun/workflow.yaml`](https://github.com/GoogleCloudPlatform/eventarc-samples/blob/main/eventarc-workflows-integration/eventarc-pubsub-cloudrun/workflow.yaml)
    file:

        export WORKFLOW_NAME=workflow-pubsub
        export REGION=us-central1
        gcloud workflows deploy ${WORKFLOW_NAME} --source=eventarc-pubsub-cloudrun/workflow.yaml --location=${REGION}
    
    This workflow decodes and logs the received Pub/Sub message.

1.  Build the container for the service that will run the workflow:

        export PROJECT_ID=$(gcloud config get-value project)
        export SERVICE_NAME=trigger-workflow-pubsub
        gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
            ./eventarc-pubsub-cloudrun/trigger-workflow

1.  Deploy a Cloud Run service to execute workflow:

        gcloud config set run/region ${REGION}
        gcloud config set run/platform managed
        gcloud run deploy ${SERVICE_NAME} \
          --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
          --region=${REGION} \
          --allow-unauthenticated \
          --update-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},WORKFLOW_REGION=${REGION},WORKFLOW_NAME=${WORKFLOW_NAME}

    This Cloud Run service executes the workflow with the HTTP request.
    
    You can see the source code in the
    [`trigger-workflow`](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-pubsub-cloudrun/trigger-workflow)
    file.

1.  Connect a Pub/Sub topic to the Cloud Run service by creating an Eventarc Pub/Sub trigger:

        gcloud config set eventarc/location ${REGION}
        gcloud eventarc triggers create ${SERVICE_NAME} \
          --destination-run-service=${SERVICE_NAME} \
          --destination-run-region=${REGION} \
          --location=${REGION} \
          --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished"

1.  Export the Pub/Sub topic that Eventarc created:

        export TOPIC_ID=$(basename $(gcloud eventarc triggers describe ${SERVICE_NAME} --format='value(transport.pubsub.topic)'))

1.  Send a message to the Pub/Sub topic to trigger the workflow:

        gcloud pubsub topics publish ${TOPIC_ID} --message="Hello there"

    In the logs for Workflows, you should see that the workflow received the Pub/Sub
    message and decoded it.

## Create a workflow that responds to file creation in Cloud Storage

In this section, you see how the creation of a file in a Cloud Storage bucket
triggers a Cloud Run service with Eventarc and the Cloud Run service
executes a workflow with the bucket and filename.

1.  Deploy the workflow defined in the
    [`eventarc-auditlog-storage-cloudrun/workflow.yaml`](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-auditlog-storage-cloudrun/workflow.yaml)
    file:

        export WORKFLOW_NAME=workflow-auditlog-storage
        export REGION=us-central1
        gcloud workflows deploy ${WORKFLOW_NAME} \
            --source=eventarc-auditlog-storage-cloudrun/workflow.yaml --location=${REGION}

    This workflow logs the bucket and filename for the storage event.

1.  Build the container for the service that will run the workflow:

        export PROJECT_ID=$(gcloud config get-value project)
        export SERVICE_NAME=trigger-workflow-auditlog-storage
        gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
            ./eventarc-auditlog-storage-cloudrun/trigger-workflow

1.  Deploy a Cloud Run service to execute the workflow:

        gcloud config set run/region ${REGION}
        gcloud config set run/platform managed
        gcloud run deploy ${SERVICE_NAME} \
          --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
          --region=${REGION} \
          --allow-unauthenticated \
          --update-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},WORKFLOW_REGION=${REGION},WORKFLOW_NAME=${WORKFLOW_NAME}

    This service executes the workflow with the bucket and filename.

    You can see the source code in the
    [`trigger-workflow`](https://github.com/GoogleCloudPlatform/eventarc-samples/tree/main/eventarc-workflows-integration/eventarc-auditlog-storage/trigger-workflow)
    file.

1.  Set up Eventarc:

        export PROJECT_NUMBER="$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')"

        gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
            --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
            --role='roles/eventarc.eventReceiver'

        gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
            --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
            --role='roles/iam.serviceAccountTokenCreator'

1.  Create the Eventarc audit log trigger:

        gcloud eventarc triggers create ${SERVICE_NAME} \
          --destination-run-service=${SERVICE_NAME} \
          --destination-run-region=${REGION} \
          --location=${REGION} \
          --event-filters="type=google.cloud.audit.log.v1.written" \
          --event-filters="serviceName=storage.googleapis.com" \
          --event-filters="methodName=storage.objects.create" \
          --service-account=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com
          
    Creation of the trigger can take a few minutes.

1.  Enable **Data Write** logging for Cloud Storage audit logs. For instructions, see
    [Enable audit logs](https://cloud.google.com/logging/docs/audit/configure-data-access#config-console-enable).

1.  Create a Cloud Storage bucket:

        export BUCKET="$(gcloud config get-value core/project)-eventarc-workflows"
        gsutil mb -l $(gcloud config get-value run/region) gs://${BUCKET}

1.  Create a file in the bucket, which triggers the workflow:

        echo "Hello World" > random.txt
        gsutil cp random.txt gs://${BUCKET}/random.txt

    In the logs, you should see that Workflows received the Cloud Storage event.

## What's next

* Learn more about [Eventarc](https://cloud.google.com/eventarc/docs).
* Learn more about [Workflows](https://cloud.google.com/workflows/docs).
