---
title: Create a Data Catalog tag history in BigQuery using Cloud Logging and Dataflow
description: Learn how to create a historical record of metadata in real time by capturing logs and processing them with Pub/Sub and Dataflow.
author: anantdamle
tags: Data Catalog, BigQuery, Dataflow
date_published: 2020-10-07
---

Anant Damle | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This solution is intended for technical practitioners—such as data engineers and analysts—who are responsible for metadata management, data governance, and 
related analytics.

Historical metadata about your data warehouse is a treasure trove for discovering insights about changing data patterns, data quality, and user behavior. The
challenge is that Data Catalog keeps a single version of metadata for fast searchability.

This tutorial suggests a solution to create a historical record of metadata Data Catalog tags by creating change records in real time by capturing and parsing
the [audit logs](https://cloud.google.com/data-catalog/docs/how-to/audit-logging) from [Cloud Logging](https://cloud.google.com/logging) and processing them in 
real time by using [Pub/Sub](https://cloud.google.com/pubsub) and [Dataflow](https://cloud.google.com/dataflow) to append into a 
[BigQuery](https://cloud.google.com/bigquery) table for historical analysis.

![Data Catalog tag history recording solution architecture](https://storage.googleapis.com/gcp-community/tutorials/datacatalog-tag-history/data_catalog_tag_recorder_arch.svg)

## Concepts

*   [Data Catalog](https://cloud.google.com/data-catalog) provides a single interface for searching and managing both
    [technical and business metadata](https://cloud.google.com/data-catalog/docs/concepts/overview#glossary) of your data warehouse or data lake in Google Cloud
    and beyond. Data Catalog uses [tags](https://cloud.google.com/data-catalog/docs/concepts/overview#tags) to organize metadata and make it discoverable.
*   [BigQuery](https://cloud.google.com/bigquery) is Google Cloud’s serverless, highly scalable, and cost-effective multi-cloud data warehouse designed for 
    business agility that you can use to run petabyte-sized queries. BigQuery also provides APIs for reading table schemas.
*   [Dataflow](https://cloud.google.com/dataflow) is Google Cloud’s serverless service for processing data in streams or batches.
*   [Pub/Sub](https://cloud.google.com/pubsub) is Google Cloud’s flexible, reliable, real-time messaging service for independent applications to publish and 
    subscribe to asynchronous events.
*   [Cloud Logging](https://cloud.google.com/logging) is Google Cloud's powerful log management service that allows you to search and route logs from
    applications and Google Cloud services.

## Prerequisites

This tutorial assumes some familiarity with shell scripts and basic knowledge of Google Cloud.

## Objectives

1. Set up a log sink to export Data Catalog audit logs to Pub/Sub.
2. Deploy a streaming Dataflow pipeline to parse the logs.
3. Enrich the logs with entry tag information from Data Catalog.
4. Store the metadata tags attached to the modified entry in a BigQuery table for historical reference.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Data Catalog](https://cloud.google.com/data-catalog/pricing)
*   [Dataflow](https://cloud.google.com/dataflow/pricing)
*   [Pub/Sub](https://cloud.google.com/pubsub/pricing)
*   [Cloud Logging](https://cloud.google.com/logging/pricing)
*   [Cloud Storage](https://cloud.google.com/storage/pricing)
*   [BigQuery](https://cloud.google.com/bigquery/pricing)
    *   Streaming API
    *   Storage

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make cleanup
easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google Cloud project.
1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

    At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session opens and displays a command-line prompt. Cloud 
    Shell is a shell environment with the Cloud SDK already installed, including the [gcloud](https://cloud.google.com/sdk/gcloud/) command-line tool, and with 
    values already set for your current project. It can take a few seconds for the session to initialize.

1.  Enable APIs for Data Catalog, BigQuery, Pub/Sub, Dataflow, and Cloud Storage services with the following command:

        gcloud services enable \
        bigquery.googleapis.com \
        storage_component \
        datacatalog.googleapis.com \
        dataflow.googleapis.com \
        pubsub.googleapis.com  

## Setting up your environment

1.  In Cloud Shell, clone the source repository and go to the directory for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/datacatalog-tag-history.git
        cd datacatalog-tag-history/

1.  Use a text editor to modify the `env.sh` file to set following variables:

        # The Google Cloud project to use for this tutorial
        export PROJECT_ID="your-project-id"

        # The BigQuery region to use for the tags table
        export BIGQUERY_REGION=""

        # The name of the BigQuery Dataset to create the tag records table
        export DATASET_ID=""

        # The name of the BigQuery table for tag records
        export TABLE_ID="EntityTagOperationRecords"

        # The Compute Engine region to use for running Dataflow jobs and create a temporary storage bucket
        export REGION_ID=""

        # define the bucket ID
        export TEMP_GCS_BUCKET=""

        # define the name of the Pub/Sub log sink in Cloud Logging
        export LOGS_SINK_NAME="datacatalog-audit-pubsub"

        # define Pub/Sub topic for receiving AuditLog events
        export LOGS_SINK_TOPIC_ID="catalog-audit-log-sink"

        # define the subscription ID
        export LOGS_SUBSCRIPTION_ID="catalog-tags-dumper"

        # name of the service account to use (not the email address)
        export TAG_HISTORY_SERVICE_ACCOUNT="tag-history-collector"
        export TAG_HISTORY_SERVICE_ACCOUNT_EMAIL="${TAG_HISTORY_SERVICE_ACCOUNT}@$(echo $PROJECT_ID | awk -F':' '{print $2"."$1}' | sed 's/^\.//').iam.gserviceaccount.com"

1.  Run the script to set the environment variables:

        source env.sh

## Creating resources

### Create the BigQuery table

1.  Set up a BigQuery dataset in the [region](https://cloud.google.com/bigquery/docs/locations) of your choice to store Data Catalog entry tags when a change
    event occurs:

        bq --location ${BIGQUERY_REGION} \
        --project_id=${PROJECT_ID} \
        mk --dataset ${DATASET_ID}

1.  Create a BigQuery table for storing tags using the provided schema:

        bq mk --table \
        --project_id=${PROJECT_ID} \
        --description "Catalog Tag snapshots" \
        --time_partitioning_field "reconcileTime" \
        "${DATASET_ID}.${TABLE_ID}" camelEntityTagOperationRecords.schema
    
    This creates a BigQuery table with `lowerCamelCase` column names. If you want `snake_case` column names, instead, use the following command:
    
        bq mk --table \
        --project_id=${PROJECT_ID} \
        --description "Catalog Tag snapshots" \
        --time_partitioning_field "reconcile_time" \
        "${DATASET_ID}.${TABLE_ID}" snakeEntityTagOperationRecords.schema

**Warning**: Apply restrictive access controls to the tag history BigQuery table. Access to Data Catalog results is based on requestors' permissions.

### Configure a Pub/Sub topic and subscription

1.  Create a Pub/Sub topic to receive audit log events:

        gcloud pubsub topics create ${LOGS_SINK_TOPIC_ID} \
        --project ${PROJECT_ID}

1.  Create a new Pub/Sub subscription:

        gcloud pubsub subscriptions create ${LOGS_SUBSCRIPTION_ID} \
        --topic=${LOGS_SINK_TOPIC_ID} \
        --topic-project=${PROJECT_ID}

    Using a subscription with a Dataflow pipeline ensures that all messages are processed even when the pipeline may be temporarily 
    down for updates or maintenance.

### Configure a log sink

1.  Create a log sink to send Data Catalog audit events to the Pub/Sub topic:

        gcloud logging sinks create ${LOGS_SINK_NAME} \
        pubsub.googleapis.com/projects/${PROJECT_ID}/topics/${LOGS_SINK_TOPIC_ID} \
        --log-filter="protoPayload.serviceName=\"datacatalog.googleapis.com\" \
        AND protoPayload.\"@type\"=\"type.googleapis.com/google.cloud.audit.AuditLog\""

    Cloud Logging pushes new [Data Catalog audit logs](https://cloud.google.com/data-catalog/docs/how-to/audit-logging) to the Pub/Sub topic for processing in 
    real time.

1.  Give the Pub/Sub `publisher` role to the logging service account to enable the pushing of log entries into the configured Pub/Sub topic:

        # Identify the log writer service account  
        export LOGGING_WRITER_IDENTITY="$(gcloud logging sinks describe ${LOGS_SINK_NAME} --format="get(writerIdentity)" --project ${PROJECT_ID})"

        # Grant publisher role to the Logging writer
        gcloud pubsub topics add-iam-policy-binding ${LOGS_SINK_TOPIC_ID} \
        --member=${LOGGING_WRITER_IDENTITY} \
        --role='roles/pubsub.publisher' \
        --project ${PROJECT_ID}

### Create service accounts

We recommend that you run pipelines with fine-grained access control to improve access partitioning. If your project does not have a user-created service 
account, create one using following instructions.

You can use your browser by going to [**Service accounts**](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts?supportedpurview=project)
in the Cloud Console.

1. Create a service account to use as the user-managed controller service account for Dataflow:

        gcloud iam service-accounts create  ${TAG_HISTORY_SERVICE_ACCOUNT} \
        --description="Service Account to run the Data Catalog tag history collection and recording pipeline." \
        --display-name="Data Catalog History collection account"

1.  Create a custom role with required permissions for accessing BigQuery, Pub/Sub, Dataflow, and Data Catalog:    

        export TAG_HISTORY_COLLECTOR_ROLE="tag_history_collector"

        gcloud iam roles create ${TAG_HISTORY_COLLECTOR_ROLE} --project=${PROJECT_ID} --file=tag_history_collector.yaml

1.  Apply the custom role to the service account:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${TAG_HISTORY_SERVICE_ACCOUNT_EMAIL}" \
        --role=projects/${PROJECT_ID}/roles/${TAG_HISTORY_COLLECTOR_ROLE}

1.  Assign the `dataflow.worker` role to allow the service account to run as a Dataflow worker:

        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${TAG_HISTORY_SERVICE_ACCOUNT_EMAIL}" \
        --role=roles/dataflow.worker

## Deploy the tag history recording pipeline

1.  Create a Cloud Storage bucket as a temporary and staging bucket for Dataflow:

        gsutil mb -l ${REGION_ID} \
        -p ${PROJECT_ID} \
        gs://${TEMP_GCS_BUCKET}

1.  Start the Dataflow pipeline using the following Maven command:    

        mvn clean generate-sources compile package exec:java \
          -Dexec.mainClass=com.google.cloud.solutions.catalogtagrecording.PipelineLauncher \
          -Dexec.cleanupDaemonThreads=false \
          -Dmaven.test.skip=true \
          -Dexec.args=" \
        --streaming=true \
        --project=${PROJECT_ID} \
        --serviceAccount=${TAG_HISTORY_SERVICE_ACCOUNT_EMAIL} \
        --runner=DataflowRunner \
        --gcpTempLocation=gs://${TEMP_GCS_BUCKET}/temp/ \
        --stagingLocation=gs://${TEMP_GCS_BUCKET}/staging/ \
        --workerMachineType=n1-standard-1 \
        --region=${REGION_ID} \
        --tagsBigqueryTable=${PROJECT_ID}:${DATASET_ID}.${TABLE_ID} \
        --catalogAuditLogsSubscription=projects/${PROJECT_ID}/subscriptions/${LOGS_SUBSCRIPTION_ID}"

    If you are using `snake_case` for column names, add the `--snakeCaseColumnNames` flag.

### Pipeline DAG

![Recording pipeline DAG](https://storage.googleapis.com/gcp-community/tutorials/datacatalog-tag-history/pipeline_dag.jpg)

## Manual test 

Follow the guide to [attach a tag](https://cloud.google.com/data-catalog/docs/quickstart-tagging) to a Data Catalog entry to verify 
that the tool captures all of the tags attached to the modified entry in the BigQuery table.

## Limitations

*   This implementation handles only the operations listed below:
    *   `CreateTag`
    *   `UpdateTag`
    *   `DeleteTag`
*   A single Data Catalog operation creates multiple tag record entries due to multiple `AuditLog` events.
*   The tool polls the Data Catalog service for entry/tag information, because the audit logs don't contain change information. This can result in some changes
    to entries or tags being missed.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.    
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

* Learn more about [Data Catalog](https://cloud.google.com/data-catalog)
* Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
* Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
