---
title: Export Firebase Crashlytics BigQuery logs to Datadog using Dataflow
description: Learn how to export Firebase Crashlytics logs from BigQuery tables to Datadog on a daily basis.
author: anantdamle
tags: log analytics, monitoring, bulk export
date_published: 2021-04-14
---

Anant Damle | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to export [Firebase Crashlytics](https://firebase.google.com/docs/crashlytics) logs from BigQuery tables to
[Datadog](https://www.datadoghq.com/).

Firebase Crashlytics is a lightweight, real-time crash reporter that helps you track, prioritize, and fix stability issues that decrease your app quality.
Crashlytics saves you troubleshooting time by intelligently grouping crashes and highlighting the circumstances that cause them.

You can [export Firebase Crashlytics data to BigQuery](https://firebase.google.com/docs/crashlytics/bigquery-export) 
to enable further analysis in BigQuery. You can combine this data with your
[data exported to BigQuery from Cloud Logging](https://cloud.google.com/logging/docs/export/bigquery) and your own first-party data and use
[Data Studio](https://firebase.googleblog.com/2018/11/using-google-data-studio-with-crashlytics.html) to visualize the data.

Datadog is a log monitoring platform [integrated with Google Cloud](https://console.cloud.google.com/marketplace/details/datadog-saas/datadog) that provides 
application and infrastructure monitoring services. 

This document is intended for a technical audience whose responsibilities include log management or data analytics. 
This document assumes that you're familiar with [Dataflow](https://cloud.google.com/dataflow) and have some familiarity with using shell scripts and basic 
knowledge of Google Cloud.

## Architecture

![Architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/crashlytics-logs-to-datadog/crashlytics_bq_datadog_arch.svg)
 
The batch Dataflow pipeline to process the Crashlytics logs in BigQuery is as follows:
 
1.  Read the BigQuery table or partition.
2.  Transform the BigQuery TableRow into a JSON string in Datadog log entry format.

The pipeline uses two optimizations:

*  Bundle log messages into batches of 5 MB or 1000 entries to reduce the number of API calls.
*  Compress requests using GZip to reduce the size of requests sent across the network.  

## Objectives

*   Create a service account with limited access.
*   Create a Dataflow Flex template pipeline to send Crashlytics logs to
   [Datadog](https://www.datadoghq.com/) using [the Datadog API for sending logs](https://docs.datadoghq.com/api/latest/logs/#send-logs)
*   Verify that Crashlytics imported the Crashlytics logs.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Dataflow](https://cloud.google.com/dataflow)
*   [Cloud Storage](https://cloud.google.com/storage)
*   [Network egress](https://cloud.google.com/vpc/network-pricing#internet_egress)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make
cleanup easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google
    Cloud project.
1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

    At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session opens and
    displays a command-line prompt. Cloud Shell is a shell environment with the Cloud SDK already installed, including
    the [gcloud](https://cloud.google.com/sdk/gcloud/) command-line tool, and with values already set for your current
    project. It can take a few seconds for the session to initialize.

1.  Enable APIs for Compute Engine, Cloud Storage, Dataflow, BigQuery, and Cloud Build services:

        gcloud services enable \
          compute.googleapis.com \
          storage.googleapis.com \
          dataflow.googleapis.com \
          bigquery.googleapis.com \
          cloudbuild.googleapis.com

## Setting up your environment

1.  In Cloud Shell, clone the source repository and go to the directory for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/crashlytics-logs-to-datadog.git
        cd crashlytics-logs-to-datadog/

1.  Use a text editor to modify the `set_environment.sh` file to set the required environment variables:

        # The Google Cloud project to use for this tutorial
        export PROJECT_ID="[YOUR_PROJECT_ID]"
        
        # The Compute Engine region to use for running Dataflow jobs
        export REGION_ID="[COMPUTE_ENGINE_REGION]"
        
        # define the Cloud Storage bucket to use for Dataflow templates and temporary location.
        export GCS_BUCKET="[NAME_OF_CLOUD_STORAGE_BUCKET]"
        
        # Name of the service account to use (not the email address)
        export PIPELINE_SERVICE_ACCOUNT_NAME="[SERVICE_ACCOUNT_NAME_FOR_RUNNER]"
        
        # The API key created in Datadog for making API calls
        # https://app.datadoghq.com/account/settings#api
        export DATADOG_API_KEY="[YOUR_DATADOG_API_KEY]"

1.  Run the script to set the environment variables:

        source set_environment.sh

## Creating resources

The tutorial uses following resources:

 * A service account to run Dataflow pipelines, enabling fine-grained access control
 * A Cloud Storage bucket for temporary data storage and test data

### Create service accounts

We recommend that you run pipelines with fine-grained access control to improve access partitioning,
by provisioning the least permissions required for each service-account.

If your project doesn't have a user-created service account, create one using following instructions.

1.  Create a service account to use as the user-managed controller service account for Dataflow:

        gcloud iam service-accounts create  "${PIPELINE_SERVICE_ACCOUNT_NAME}" \
          --project="${PROJECT_ID}" \
          --description="Service Account for Datadog export pipelines." \
          --display-name="Datadog logs exporter"

1.  Create a custom role with the permissions required, as specified in the
    [`datadog_sender_permissions.yaml`](https://github.com/GoogleCloudPlatform/crashlytics-logs-to-datadog/blob/main/datadog_sender_permissions.yaml) file:

        export DATADOG_SENDER_ROLE_NAME="datadog_sender"

        gcloud iam roles create "${DATADOG_SENDER_ROLE_NAME}" \
          --project="${PROJECT_ID}" \
          --file=datadog_sender_permissions.yaml

1.  Apply the custom role to the service account:

        gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
          --member="serviceAccount:${PIPELINE_SERVICE_ACCOUNT_EMAIL}" \
          --role="projects/${PROJECT_ID}/roles/${DATADOG_SENDER_ROLE_NAME}"

1.  Assign the `dataflow.worker` role to allow a Dataflow worker to run with the service account credentials:

        gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
          --member="serviceAccount:${PIPELINE_SERVICE_ACCOUNT_EMAIL}" \
          --role="roles/dataflow.worker"
        
### Create the Cloud Storage bucket

Create a Cloud Storage bucket for storing test data and Dataflow staging location:

    gsutil mb -p "${PROJECT_ID}" -l "${REGION_ID}" "gs://${GCS_BUCKET}"


## Build and launch the Dataflow pipeline

1.  Build the pipeline code:

        ./gradlew clean build shadowJar

1.  Define the table fully qualified BigQuery table ID for the Crashlytics data:

        export CRASHLYTICS_BIGQUERY_TABLE="[YOUR_PROJECT_ID]:[YOUR_DATASET_ID].[YOUR_TABLE_ID]"

    Make sure that the service account has access to this BigQuery table.

1.  Run the pipeline:

        bq_2_datadog_pipeline \
          --project="${PROJECT_ID}" \
          --region="${REGION_ID}" \
          --runner="DataflowRunner" \
          --serviceAccount="${PIPELINE_SERVICE_ACCOUNT_EMAIL}" \
          --gcpTempLocation="gs://${GCS_BUCKET}/temp" \
          --stagingLocation="gs://${GCS_BUCKET}/staging" \
          --tempLocation="gs://${GCS_BUCKET}/bqtemp" \
          --datadogApiKey="${DATADOG_API_KEY}" \
          --sourceBigQueryTableId="${CRASHLYTICS_BIGQUERY_TABLE}"

    You can run the pipeline with the following options:

    | parameter               | Default value               | Description                                                |
    | ----------------------- | --------------------------- | ---------------------------------------------------------- |
    | `sourceBigQueryTableId` |                             | Fully qualified BigQuery table ID                          |
    | `bigQuerySqlQuery`      |                             | BigQuery SQL query results to send to Datadog              |
    | `shardCount`            | `10`                        | Number of parallel processes to send to Datadog (Too high a number can overload the Datadog API.) |
    | `preserveNulls`         | `false`                     | Allow null values from BigQuery source to be serialized. |
    | `datadogApiKey`         |                             | API key from the [Datadog console](https://app.datadoghq.com/account/settings#api) |
    | `datadogEndpoint`       | `https://http-intake.logs.datadoghq.com/v1/input` | See [Datadog logging endpoints](https://docs.datadoghq.com/logs/log_collection/?tab=host#logging-endpoints).|
    | `datadogSource`         | `crashlytics-bigquery`      |  |
    | `datadogTags`           | `user:crashlytics-pipeline` |  |
    | `datadogLogHostname`    | `crashlytics`               |  |
    
    For information about `datadogSource`, `datadogTags`, and `datadogLogHostname`, see
    [Datadog log entry structure](https://docs.datadoghq.com/api/latest/logs/#send-logs). You can customize these parameters to suit your needs.

    Use either `sourceBigQueryTableId` or `bigQuerySqlQuery`, not both.

1.  Monitor the Dataflow job in Cloud Console.

    The following diagram shows the pipeline DAG:

    ![Pipeline DAG](https://storage.googleapis.com/gcp-community/tutorials/crashlytics-logs-to-datadog/pipeline_dag.png)

### Create a Dataflow Flex Template

[Dataflow templates](https://cloud.google.com/dataflow/docs/concepts/dataflow-templates) allow you to use the Cloud Console, the `gcloud` command-line tool, or
REST API calls to set up your pipelines on Google Cloud and run them. Classic templates are staged as execution graphs on Cloud Storage; Flex Templates bundle
the pipeline as a container image in your project’s registry in Container Registry. This allows you to decouple building and running pipelines, as well as
integrate with orchestration systems for daily execution. For more information, see
[Evaluating which template type to use](https://cloud.google.com/dataflow/docs/concepts/dataflow-templates#comparing-templated-jobs) in the Dataflow 
documentation.

1.  Define the location to store the template spec file containing all of the necessary information to run the job:

        export TEMPLATE_PATH="gs://${GCS_BUCKET}/dataflow/templates/bigquery-to-datadog.json"
        export TEMPLATE_IMAGE="us.gcr.io/${PROJECT_ID}/dataflow/bigquery-to-datadog:latest"

1.  Build the Dataflow Flex template:

        gcloud dataflow flex-template build "${TEMPLATE_PATH}" \
          --image-gcr-path="${TEMPLATE_IMAGE}" \
          --sdk-language="JAVA" \
          --flex-template-base-image=JAVA11 \
          --metadata-file="bigquery-to-datadog-pipeline-metadata.json" \
          --service-account-email="${PIPELINE_SERVICE_ACCOUNT_EMAIL}" \
          --jar="build/libs/crashlytics-logs-to-datadog-all.jar" \
          --env="FLEX_TEMPLATE_JAVA_MAIN_CLASS=\"com.google.cloud.solutions.bqtodatadog.BigQueryToDatadogPipeline\""    
    
### Run the pipeline using the Flex Template

Run the pipeline using the Flex Template that you created in the previous step:

    gcloud dataflow flex-template run "bigquery-to-datadog-`date +%Y%m%d-%H%M%S`" \
      --region "${REGION_ID}" \
      --template-file-gcs-location "${TEMPLATE_PATH}" \
      --service-account-email "${PIPELINE_SERVICE_ACCOUNT_EMAIL}" \
      --parameters sourceBigQueryTableId="${CRASHLYTICS_BIGQUERY_TABLE}" \
      --parameters datadogApiKey="${DATADOG_API_KEY}"
    
### Verify logs in the Datadog console

Visit the Datadog [log viewer](https://app.datadoghq.com/logs?query=status%3Ainfo+host%3Acrashlytics) to verify that the logs are available in Datadog.

![Datadog screenshot](https://storage.googleapis.com/gcp-community/tutorials/crashlytics-logs-to-datadog/datadog_screenshot.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [Firebase Crashlytics](https://firebase.google.com/docs/crashlytics)
- Learn more about [Cloud Logging](https://cloud.google.com/logging) and [Cloud Monitoring](https://cloud.google.com/monitoring).
- Learn more about deploying [Datadog on Google Cloud](https://console.cloud.google.com/marketplace/details/datadog-saas/datadog?).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
