---
title: Export Cloud Monitoring metrics using Monitoring Query Language (MQL) 
description: Learn how to export Cloud Monitoring metrics using Monitoring Query Language (MQL).
author: xiangshen-dk
tags: monitoring, stackdriver, mql, functions
date_published: 2020-11-11
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes a solution that uses the Google Cloud [Monitoring Query Language (MQL)](https://cloud.google.com/monitoring/mql) to
export specific monitoring metrics. 

The following diagram shows the high-level architecture of this solution:

![export-metrics-arch](https://storage.googleapis.com/gcp-community/tutorials/metrics-export-with-mql/export-metrics.png)

## Costs

This tutorial uses billable components of Google Cloud, including the following:

-  [Cloud Functions](https://cloud.google.com/functions/pricing)
-  [Pub/Sub](https://cloud.google.com/pubsub/pricing)
-  [Cloud Scheduler](https://cloud.google.com/scheduler/pricing)
-  [BigQuery](https://cloud.google.com/bigquery/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a 
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the  "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

1.  [Enable the Cloud Functions, Cloud Scheduler, Pub/Sub, Cloud Build, and BigQuery APIs.](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions.googleapis.com,cloudscheduler.googleapis.com,pubsub.googleapis.com,bigquery.googleapis.com,cloudbuild.googleapis.com)

1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient 
    permissions to use the services listed above.

## Using Cloud Shell

This tutorial uses the following tool packages:

* [`gcloud`](https://cloud.google.com/sdk/gcloud)
* [`bq`](https://cloud.google.com/bigquery/docs/bq-command-line-tool)

Because [Cloud Shell](https://cloud.google.com/shell) automatically includes these packages, we recommend that you run the commands in this tutorial in Cloud
Shell, so that you don't need to install these packages locally.

## Preparing your environment

### Get the sample code

The sample code for this tutorial is in the
[Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/metrics-export-with-mql).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/metrics-export-with-mql

## Implementation steps

### Set the environment variables

    export PROJECT_ID=`gcloud config get-value core/project`
    export PUBSUB_TOPIC=mql_metric_export
    export BIGQUERY_DATASET=metric_export
    export BIGQUERY_TABLE=mql_metrics

### Update configuration

1.  Update the variables in the configuration file:

        envsubst < config-template.py > config.py
        
    If you don't have `envsubst` installed, you can open the `config-template.py` file, update the variables, and save it as `config.py`.

1.  Add and update the MQL queries as needed in the `config.py` file. You can find examples in the 
    [MQL documentation](https://cloud.google.com/monitoring/mql/examples).

### Create the export pipeline

1.  Create a BigQuery dataset:

        bq mk $BIGQUERY_DATASET
        
1.  Create a table using the schema JSON file:

        bq mk --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}  ./bigquery_schema.json

1.  Create a service account for the export Cloud Function:

        gcloud iam service-accounts create mql-export-metrics \
            --display-name "MQL export metrics SA" \
            --description "Used for the function that export monitoring metrics"

        export EXPORT_METRIC_SERVICE_ACCOUNT=mql-export-metrics@$PROJECT_ID.iam.gserviceaccount.com 

1.  Assign IAM roles to the service account:

        gcloud projects add-iam-policy-binding  $PROJECT_ID --member="serviceAccount:$EXPORT_METRIC_SERVICE_ACCOUNT" --role="roles/compute.viewer"
        gcloud projects add-iam-policy-binding  $PROJECT_ID --member="serviceAccount:$EXPORT_METRIC_SERVICE_ACCOUNT" --role="roles/monitoring.viewer"
        gcloud projects add-iam-policy-binding  $PROJECT_ID --member="serviceAccount:$EXPORT_METRIC_SERVICE_ACCOUNT" --role="roles/bigquery.dataEditor"
        gcloud projects add-iam-policy-binding  $PROJECT_ID --member="serviceAccount:$EXPORT_METRIC_SERVICE_ACCOUNT" --role="roles/bigquery.jobUser"

1.  Create the Pub/Sub topic:

        gcloud pubsub topics create $PUBSUB_TOPIC

1.  Deploy the Cloud Function:

        gcloud functions deploy mql_export_metrics \
        --trigger-topic $PUBSUB_TOPIC \
        --runtime python38 \
        --entry-point export_metric_data \
        --service-account=$EXPORT_METRIC_SERVICE_ACCOUNT

1. Deploy the Cloud Scheduler job with a schedule to run it every 5 minutes:

        gcloud scheduler jobs create pubsub get_metric_mql \
        --schedule "*/5 * * * *" \
        --topic $PUBSUB_TOPIC \
        --message-body "Exporting metric..."

   If the command fails and requests a location, you can add the location flag with your current region. For example, you can use `--location us-central1`.

## Verify the result

1.  Manually invoke the scheduled job:

        gcloud scheduler jobs run get_metric_mql

1.  Verify the setup by running the following query:

        bq query \
        --use_legacy_sql=false \
        "SELECT
        *
        FROM
        ${PROJECT_ID}.${BIGQUERY_DATASET}.${BIGQUERY_TABLE}
        LIMIT 10
        "
        
    If you have metrics data in Cloud Monitoring, they should be exported, and you will receive some query results.

    Here is an example if you export the metric `compute.googleapis.com/instance/cpu/utilization`:

        bq query \
        --use_legacy_sql=false \
        "
        SELECT
            EXTRACT(HOUR FROM pointData.timeInterval.end_time) AS extract_date,
            min(pointData.values.double_value) as min_cpu_util,
            max(pointData.values.double_value) as max_cpu_util,
            avg(pointData.values.double_value) as avg_cpu_util
        FROM
            ${PROJECT_ID}.${BIGQUERY_DATASET}.${BIGQUERY_TABLE}
        WHERE
            pointData.timeInterval.end_time > TIMESTAMP(DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY))
            AND  pointData.timeInterval.end_time <= CURRENT_TIMESTAMP
            
        GROUP BY extract_date
        ORDER BY extract_date
        "

Alternatively, you can open the [BigQuery console](https://console.cloud.google.com/bigquery) and query the export data there.


## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the resources that you created. You can either 
delete the entire project or delete individual resources.

Deleting a project has the following effects:

* Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, delete selected resources inside the project instead of deleting the whole project.

If you plan to explore multiple tutorials, reusing projects can help you to avoid exceeding project quota limits.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial. 

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).  
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the resources

If you don't want to delete the project, you can delete the provisioned resources:

    gcloud scheduler jobs delete get_metric_mql

    gcloud functions delete mql_export_metrics

    gcloud pubsub topics delete $PUBSUB_TOPIC

    gcloud iam service-accounts delete $EXPORT_METRIC_SERVICE_ACCOUNT

    bq rm --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}

    bq rm $BIGQUERY_DATASET

## What's next

-  Learn more about using the [MQL query editor](https://cloud.google.com/monitoring/mql/query-editor).
-  Learn more about to export metrics from multiple projects [Cloud Monitoring metric export](https://cloud.google.com/solutions/stackdriver-monitoring-metric-export).
-  Try out other Google Cloud features for yourself. Have a look at those [tutorials](https://cloud.google.com/docs/tutorials).
