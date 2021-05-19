---
title: Create a Cloud Monitoring chart with data From BigQuery
description: Learn how to create Cloud Monitoring charts and dashboards using data from BigQuery.
author: xiangshen-dk
tags: monitoring, stackdriver, bigquery, cloud run
date_published: 2021-05-20
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to ingest data from [BigQuery](https://cloud.google.com/bigquery) to [Cloud Monitoring](https://cloud.google.com/monitoring) and visualize it on a dashboard. A typical use case is you have some business metric data stored in a BigQuery table and you want to plot the data along with the infrastructure metrics. Therefore, you can correlate the data and have a better understanding of your system.

## Objectives 

+   Create a serverless approach to ingest data from BigQuery
+   Visualize ingest metric data in Cloud Monitoring.

## Costs

This tutorial uses billable components of Google Cloud, including:

+   [Cloud Run](https://cloud.google.com/run/pricing)
+   [Cloud Scheduler](https://cloud.google.com/scheduler/pricing)
+   [BigQuery](https://cloud.google.com/bigquery/pricing)
+   Chargeable [external metrics](https://cloud.google.com/stackdriver/pricing#metrics-chargeable)

To generate a cost estimate based on your projected usage, use the [Pricing Calculator](https://cloud.google.com/products/calculator#id=38ec76f1-971f-41b5-8aec-a04e732129cc).

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see the "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  [Enable the Kubernetes Engine, Container Registry, and Cloud Monitoring APIs.](https://console.cloud.google.com/flows/enableapi?apiid=containerregistry.googleapis.com,container.googleapis.com,monitoring.googleapis.com,cloudbuild.googleapis.com)
1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient permissions to use the services listed above.

When you finish this tutorial, you can avoid continued billing by deleting the resources you created. See [Cleaning up](https://docs.google.com/document/d/1EUF3s4pZNPpR7wtI1EnIlQNio3FcI6KjeULL0HRTT6s/edit#heading=h.e6uzvad6vamz) for more detail.  
Using Cloud Shell  
This tutorial uses the following tool packages:

+   [gcloud](https://cloud.google.com/sdk/gcloud)
+   [bq](https://cloud.google.com/bigquery/docs/bq-command-line-tool)

Because [Cloud Shell](https://cloud.google.com/shell) automatically includes these packages, we recommend that you run the commands in this tutorial in Cloud Shell, so that you don't need to install these packages locally.  
Initializing common variables  
You need to define several variables that control where elements of the infrastructure are deployed.

1.  Open Cloud Shell that has **gcloud** installed and configured.
1.  Set the variables used in this tutorial and you need to use your own project id. The tutorial sets the region to us-central1. If you want to change the region, ensure that the zone values reference the region you specify.
    ```bash
    REGION=us-central1
    ZONE=${REGION}-b
    PROJECT_ID=[YOUR_PROJECT_ID]
    ```
1. Enable all necessary services:
    ```bash
    gcloud services enable compute.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable monitoring.googleapis.com
    gcloud services enable bigquery.googleapis.com
    gcloud services enable logging.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable cloudscheduler.googleapis.com
    ```
1.  Run the following commands to set the default zone and project ID so you don't have to specify these values in every subsequent command:
    ```bash
    gcloud config set project ${PROJECT_ID}
    gcloud config set compute/zone ${ZONE}
    gcloud config set run/platform managed
    gcloud config set run/region ${REGION}
    ```

## Preparing your environment

### Get the sample code

The sample code for this tutorial is in the Google Cloud Community GitHub repository.

1.  Clone the repository:
    ```bash
    git clone https://github.com/GoogleCloudPlatform/community.git
    ```

1.  Go to the tutorial directory:
    ```bash
    cd community/tutorials/monitoring-dashboard-from-bq
    ```

## Create the BigQuery dataset and table

1. Set the dataset and table names:
    ```bash
    BIGQUERY_DATASET=cloud_monitoring_import_demo
    BIGQUERY_TABLE=sales
    ```

1.  Create a BigQuery dataset:
    ```bash
    bq mk $BIGQUERY_DATASET
    ```

1.  Create a table using the schema JSON file:
    ```bash
    bq mk --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}  ./bigquery_schema.json
    ```

## Ingest data into Cloud Monitoring using a scheduler job

1.  Creating a service account for Cloud Scheduler
    ```bash
    gcloud iam service-accounts create cloud-scheduler-run \
      --display-name "Demo account"
    ```
1.  Create container image
    ```bash
    gcloud builds submit --tag gcr.io/${PROJECT_ID}/monitoring-bq
    ```

	Note: you can read the source file `main.p`y for more details.

1.  Deploy to Cloud Run

    ```bash
    gcloud run deploy --image gcr.io/${PROJECT_ID}/monitoring-bq \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --set-env-vars "PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "METRIC_NAME=sales-demo" \
    --set-env-vars "SCHEDULE_INTERVAL=3600" \
    --set-env-vars "BIGQUERY_DATASET=$BIGQUERY_DATASET" \
    --set-env-vars "BIGQUERY_TABLE=$BIGQUERY_TABLE"
    ```

    You will be prompted for the service name: press Enter to accept the default name `monitoring-bq`.

    Then wait a few moments until the deployment is complete. On success, the command line displays the service URL.

1.  For Cloud Run, give your service account permission to invoke your service:
    ```bash
    gcloud run services add-iam-policy-binding monitoring-bq \
    --platform=managed \
    --region=${REGION} \
    --member=serviceAccount:cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com \
      --role=roles/run.invoker
    ```

1.  Create Cloud Scheduler job

    Currently, there is a dependency for App Engine. If App Engine is never used in the project, we need run the following:

    ```bash
    gcloud app create --region=us-central
    ```

    Here we create a Cloud Scheduler job that runs every hour. You can change the schedule based on your needs and data granularity.

    ```bash
    gcloud scheduler jobs create http monitoring-job --schedule "0 * * * *" \
      --http-method=POST \
      --uri=$(gcloud run services describe monitoring-bq --format="value(status.url)") \
      --oidc-service-account-email=cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com
    ```

    The steps above allow us to run a Cloud Run service to ingest BigQuery data to Cloud Monitoring. However, If you don't want to use a scheduler job and prefer an event-based architecture, you can take advantage of BigQuery events. Those events can also trigger a Cloud Run service. Read [How to trigger Cloud Run actions on BigQuery events](https://cloud.google.com/blog/topics/developers-practitioners/how-trigger-cloud-run-actions-bigquery-events) for more details.

## Viewing metrics in Cloud Monitoring

In this section, you configure Monitoring and create a dashboard. To complete these steps, you must have one of the following IAM roles on that project:

+   Project Owner
+   Monitoring Editor
+   Monitoring Admin
+   Monitoring Accounts Editor

### Add testing data to BigQuery

Run the following `bash` commands to insert some random data to the BigQuery table.

```bash
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
```

### Verify the data in BigQuery

Open the [BigQuery console](https://pantheon.corp.google.com/bigquery), in the query editor run
the following query:

  ```sql
  SELECT * FROM `cloud_monitoring_import_demo.sales` ORDER BY report_time LIMIT 100
  ```

You should see the query results similar to the following:

![BigQuery data](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/bigquery-test-data.png)

### Run the schduler job manually

  ```bash
  gcloud scheduler jobs run monitoring-job
  ```

### Configure a Cloud Monitoring Workspace

1.  In the Cloud Console, select your Google Cloud project.  
**[Go to Cloud Console](https://console.cloud.google.com/)**
1.  In the navigation pane, select **[Monitoring](https://console.cloud.google.com/monitoring)**.  
If you have never used Cloud Monitoring, then on your first access of **Monitoring** in the Google Cloud Console, a Workspace is automatically created and your project is associated with that Workspace. Otherwise, if your project isn't associated with a Workspace, then a dialog appears and you can either create a Workspace or add your project to an existing Workspace. We recommend that you create a Workspace. After you make your selection, click **Add**.

### Create a dashboard

1.  In the Cloud Monitoring navigation pane, click **Metrics explorer**.
1.  In the **Find resource type and metric** field, enter `sales-demo`.
1.  Select the metric that starts with **custom.googleapis.com/sales-demo**.
    You might have to refresh the page to see the metric name.
1.  For the resource, enter **Global** and  select it
1.  In the **Group By** drop-down list, select `item`.
1.  At the top of the diagram, select **Stacked Bar**. Wait for a few moments and
    you should have a chart like the following:

![Metric chart](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/monitoring-chart.png)

1.  Click **Save Chart**. Name the chart.
1.  In the **Dashboard** drop-down list, select **New Dashboard**.
1.  Enter the dashboard name `Demo Dashboard` and click **Save**
1.  There is now a new chart in this dashboard.
    You can find the dashboard from Cloud Monitoring and it's similar to the following:

![Dashboard](https://storage.googleapis.com/gcp-community/tutorials/monitoring-dashboard-from-bq/dashboard.png)

## Cleaning up

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.  
**Caution**: Deleting a project has the following effects:

+   **Everything in the project is deleted.** If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the project.
+   **Custom project IDs are lost.** When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs that use the project ID, such as an **appspot.com** URL, delete selected resources inside the project instead of deleting the whole project.

    If you plan to explore multiple tutorials and quickstarts, reusing projects can help you avoid exceeding project quota limits.

1.  In the Cloud Console, go to the **Manage resources** page.  
[Go to the Manage resources page](https://console.cloud.google.com/iam-admin/projects)
1.  In the project list, select the project that you want to delete and then click **Delete**
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the individual resources

If you don't want to delete the whole project, run the following command to delete the resources: 

  ```bash
  gcloud scheduler jobs delete monitoring-job

  gcloud run services delete monitoring-bq --region ${REGION}

  gcloud iam service-accounts delete cloud-scheduler-run@${PROJECT_ID}.iam.gserviceaccount.com

  bq rm --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}

  bq rm $BIGQUERY_DATASET
  ```

Open [Container Registry](https://console.cloud.google.com/gcr/), remove all the images we created. 

Also, go to [Cloud Monitoring dashboards](https://pantheon.corp.google.com/monitoring/dashboards?), delete the dashboard you have created.

## What's next

+   Learn about [Running Cloud Run services on a schedule.](https://cloud.google.com/run/docs/triggering/using-scheduler)
+   Read about [creating custom metrics](https://cloud.google.com/monitoring/custom-metrics/creating-metrics). 
+   Learn about [using Cloud Monitoring dashboards and charts](https://cloud.google.com/monitoring/dashboards).
+   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
