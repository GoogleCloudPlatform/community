---
title: Create a Cloud Monitoring chart with data From BigQuery
description: Learn how to create Cloud Monitoring charts and dashboards using data from BigQuery.
author: xiangshen-dk
tags: monitoring, stackdriver, bigquery, cloud run
date_published: 2021-06-04
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to ingest data from [BigQuery](https://cloud.google.com/bigquery) to [Cloud Monitoring](https://cloud.google.com/monitoring) and 
visualize it on a dashboard. A typical use case is when you have some business metrics data stored in a BigQuery table and you want to plot the data along with
the infrastructure metrics, so that you can correlate the data and have a better understanding of your system.

## Objectives 

+   Create a serverless system to ingest data from BigQuery.
+   Visualize ingested metrics data in Cloud Monitoring.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

+   [Cloud Run](https://cloud.google.com/run/pricing)
+   [Cloud Scheduler](https://cloud.google.com/scheduler/pricing)
+   [BigQuery](https://cloud.google.com/bigquery/pricing)
+   [Chargeable external metrics](https://cloud.google.com/stackdriver/pricing#metrics-chargeable)

To generate a cost estimate based on your projected usage, use the
[pricing calculator](https://cloud.google.com/products/calculator#id=38ec76f1-971f-41b5-8aec-a04e732129cc).

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient 
    permissions to use the services listed above.

This tutorial uses [gcloud](https://cloud.google.com/sdk/gcloud) and [bq](https://cloud.google.com/bigquery/docs/bq-command-line-tool) command-line tools. 
Because [Cloud Shell](https://cloud.google.com/shell) includes these packages, we recommend that you run the commands in this tutorial in Cloud Shell, so that 
you don't need to install these packages locally.  

## Prepare your environment

### Set common variables  

You need to define several variables that control where elements of the infrastructure are deployed.

1.  In Cloud Shell, set the region, zone, and project ID:

        REGION=us-central1
        ZONE=${REGION}-b
        PROJECT_ID=[YOUR_PROJECT_ID]
   
    Replace `[YOUR_PROJECT_ID]` with your project ID. This tutorial uses the region `us-central1`. If you want to change the region, check that the zone 
    values are appropriate for the region that you specify.
   
1.  Enable all necessary services:

        gcloud services enable compute.googleapis.com
        gcloud services enable run.googleapis.com
        gcloud services enable monitoring.googleapis.com
        gcloud services enable bigquery.googleapis.com
        gcloud services enable logging.googleapis.com
        gcloud services enable cloudbuild.googleapis.com
        gcloud services enable cloudscheduler.googleapis.com
        gcloud services enable containerregistry.googleapis.com

1.  Set the zone and project ID so that you don't have to specify these values in subsequent commands:

        gcloud config set project ${PROJECT_ID}
        gcloud config set compute/zone ${ZONE}
        gcloud config set run/platform managed
        gcloud config set run/region ${REGION}

### Get the sample code

The sample code for this tutorial is in the Google Cloud Community GitHub repository.

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/monitoring-dashboard-from-bq

## Create the BigQuery dataset and table

1.  Set the dataset and table names:

        BIGQUERY_DATASET=cloud_monitoring_import_demo
        BIGQUERY_TABLE=sales

1.  Create a BigQuery dataset:

        bq mk $BIGQUERY_DATASET

1.  Create a table using the schema JSON file:

        bq mk --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}  ./bigquery_schema.json

## Ingest data into Cloud Monitoring using a Cloud Scheduler job

1.  Creating a service account for Cloud Scheduler:

        gcloud iam service-accounts create cloud-scheduler-run \
          --display-name "Demo account"

1.  Create the container image:

        gcloud builds submit --tag gcr.io/${PROJECT_ID}/monitoring-bq

    You can read the source file `main.py` for more details.

1.  Deploy to Cloud Run:

        gcloud run deploy --image gcr.io/${PROJECT_ID}/monitoring-bq \
          --platform managed \
          --region ${REGION} \
          --no-allow-unauthenticated \
          --set-env-vars "PROJECT_ID=$PROJECT_ID" \
          --set-env-vars "METRIC_NAME=sales-demo" \
          --set-env-vars "SCHEDULE_INTERVAL=3600" \
          --set-env-vars "BIGQUERY_DATASET=$BIGQUERY_DATASET" \
          --set-env-vars "BIGQUERY_TABLE=$BIGQUERY_TABLE"

1.  When you are prompted for the service name, press Enter to accept the default name `monitoring-bq`.

    Deployment can take a few minutes. When the deployment is complete, the command line displays the service URL.

1.  For Cloud Run, give your service account permission to invoke your service:

        gcloud run services add-iam-policy-binding monitoring-bq \
          --platform=managed \
          --region=${REGION} \
          --member=serviceAccount:cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com \
          --role=roles/run.invoker

1.  Create an App Engine app:

        gcloud app create --region=us-central
        
    Cloud Scheduler depends on App Engine.

1.  Create the Cloud Scheduler job:

        gcloud scheduler jobs create http monitoring-job --schedule "0 * * * *" \
          --http-method=POST \
          --uri=$(gcloud run services describe monitoring-bq --format="value(status.url)") \
          --oidc-service-account-email=cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com

    This example creates a Cloud Scheduler job that runs every hour. You can change the schedule based on your needs and data granularity.


The procedure in this section allows you to run a Cloud Run service to ingest BigQuery data to Cloud Monitoring. However, if you prefer an event-based 
system instead of a schedule-based system, you can use BigQuery events, which can also trigger a Cloud Run service. For more information, see
[How to trigger Cloud Run actions on BigQuery events](https://cloud.google.com/blog/topics/developers-practitioners/how-trigger-cloud-run-actions-bigquery-events).

## View metrics in Cloud Monitoring

In this section, you configure Cloud Monitoring and create a dashboard. 

To complete these steps, you must have one of the following IAM roles for the project:

+   Project Owner
+   Monitoring Editor
+   Monitoring Admin
+   Monitoring Accounts Editor

### Add testing data to BigQuery

Run the following shell script in Cloud Shell to insert some random data into the BigQuery table:

    cur_epoch=$(date +%s)
    for ((i=0;i<12;i++))
    do
      for ((j=1;j<=3;j++))
      do
        n=$(($RANDOM%10+1))
        d=$(date -d @$cur_epoch +'%Y-%m-%d %H:%M:%S'); 
        item='{"item_id":"item'$n'", "item_sold":'$(($n*100))', "report_time":"'$d'"}'
        echo "Insert item: ${item}"
        echo $item | bq insert ${BIGQUERY_DATASET}.${BIGQUERY_TABLE} 
      done
      cur_epoch=$(($cur_epoch-300))
    done

### Verify the data in BigQuery

1.  Go to the [BigQuery page in the Cloud Console](https://console.cloud.google.com/bigquery).

1.  In the query editor run the following query:

        SELECT * FROM `cloud_monitoring_import_demo.sales` ORDER BY report_time LIMIT 100

    You should see the query results similar to the following:

    ![BigQuery data](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/bigquery-test-data.png)

### Run the Cloud Scheduler job

Run the Cloud Scheduler job:

    gcloud scheduler jobs run monitoring-job

### Create a dashboard

1.  In the [Cloud Console](https://console.cloud.google.com/), select your Google Cloud project.
1.  Go to the [Cloud Monitoring **Metrics explorer** page](https://console.cloud.google.com/monitoring/metrics-explorer).
1.  In the **Find resource type and metric** field, enter `sales-demo`.
1.  Select the metric that starts with `custom.googleapis.com/sales-demo`.

    You might need to refresh the page to see the metric name.

1.  For the resource type, enter `Global` and select the **Global** resource type.
1.  In the **Group by** menu, select **item**.
1.  From the menu above the chart, choose **Stacked bar**.

    Within a few minutes, you should have a chart like the following:

    ![Metric chart](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/monitoring-chart.png)

1.  Click the **Save chart** button.
1.  Name the chart.
1.  In the **Dashboard** menu, select **New dashboard**.
4.  Enter the dashboard name `Demo dashboard` and click **Save**.

    There is now a new chart in this dashboard. You can find the dashboard from Cloud Monitoring. It should be similar to the following:

    ![Dashboard](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/dashboard.png)

## Cleaning up

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.  

1.  In the Cloud Console, go to the [**Manage resources**](https://console.cloud.google.com/iam-admin/projects) page.
1.  In the project list, select the project that you want to delete and then click **Delete**
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the individual resources

If you don't want to delete the whole project, you can delete the individual resources.

1.  Run the following commands to delete the respective resources: 

        gcloud scheduler jobs delete monitoring-job

        gcloud run services delete monitoring-bq --region ${REGION}

        gcloud iam service-accounts delete cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com

        bq rm --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}

        bq rm $BIGQUERY_DATASET

1.  Go to the [Container Registry page](https://console.cloud.google.com/gcr/), and remove all of the images that you created. 

1.  Go to the [Cloud Monitoring dashboards page](https://console.cloud.google.com/monitoring/dashboards), and delete the dashboard that you created.

## What's next

+   Learn about [running Cloud Run services on a schedule](https://cloud.google.com/run/docs/triggering/using-scheduler).
+   Learn about [creating custom metrics](https://cloud.google.com/monitoring/custom-metrics/creating-metrics). 
+   Learn about [using Cloud Monitoring dashboards and charts](https://cloud.google.com/monitoring/dashboards).
+   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
