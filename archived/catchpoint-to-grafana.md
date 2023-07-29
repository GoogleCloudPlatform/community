---
title: Catchpoint data pipeline to Grafana
description: Learn to ingest data from Catchpoint into Google Cloud for visualization and analysis with Grafana.
author: drit
tags: telemetry, probes, monitors
date_published: 2021-04-20
---

Dritan Suljoti | Chief Product and Technology Officer | Catchpoint Systems, Inc.

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

[Catchpoint’s digital experience monitoring platform](https://www.catchpoint.com/platform) provides an extensive fleet of network telemetry probes, as well as 
tools for capturing real user experience metrics, which give instant insight into the performance of networks, apps, and digital services.
You can use [Cloud Monitoring](https://cloud.google.com/monitoring), in conjunction with the open-source analytics and interactive visualization web application
[Grafana](https://grafana.com/oss/), for all of your network performance monitoring and analysis.

This tutorial and its companion tutorial provide two methods of ingesting and visualizing data from Catchpoint within Google Cloud:

- This tutorial shows you how to deliver data to Grafana for visualization and analysis.
- The [companion tutorial](https://cloud.google.com/community/tutorials/catchpoint-to-cloud-monitoring) shows you how to set up a pipeline that ingests data
  captured by Catchpoint into Cloud Monitoring and use Metrics Explorer for visualization and analysis.

This tutorial uses Node.js, the Cloud Console, and `gcloud` commands on the Cloud SDK command line.

The fully configured data pipeline from Catchpoint to Grafana is illustrated in the following diagram:

![integration pipeline](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/integration-pipeline.png)

1.  Catchpoint posts data to an HTTP webhook set up in App Engine.
1.  App Engine publishes the data to a Pub/Sub channel.
1.  A Cloud Dataflow job listens to the Pub/Sub channel and inserts a BigQuery-accessible dataset.
1.  Data is sent to BigQuery along with the Catchpoint schema.
1.  Grafana's BigQuery plugin is used as a data source to visualize the data.

## Objectives

1. Create a Pub/Sub Topic.
1. Build a webhook in Google Cloud.
1. Configure Catchpoint.
1. Build your pipeline.
1. Configure Grafana.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- [Cloud Functions](https://cloud.google.com/functions)
- [App Engine](https://cloud.google.com/appengine/docs/flexible/python)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Initial setup

1.  Create a new Google Cloud project or select an existing project.

    For information about creating and selecting projects, see
    [Creating and managing projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
    
    You need the Google Cloud project ID when you configure the Catchpoint script.

1.  [Create two BigQuery tables](https://cloud.google.com/bigquery/docs/tables):

    -   Main table:

            {
              "fields": [
                {
                  "mode": "NULLABLE",
                  "name": "TestName",
                  "type": "STRING"
                },
                {
                  "mode": "NULLABLE",
                  "name": "TestURL",
                  "type": "STRING"
                },
                {
                  "mode": "NULLABLE",
                  "name": "TimeStamp",
                  "type": "TIMESTAMP"
                },
                {
                  "mode": "NULLABLE",
                  "name": "NodeName",
                  "type": "STRING"
                },
                {
                  "mode": "NULLABLE",
                  "name": "DNSTime",
                  "type": "NUMERIC"
                },
                {
                  "mode": "NULLABLE",
                  "name": "Connect",
                  "type": "NUMERIC"
                },
                {
                  "mode": "NULLABLE",
                  "name": "SSL",
                  "type": "NUMERIC"
                },
                {
                  "mode": "NULLABLE",
                  "name": "SendTime",
                  "type": "NUMERIC"
                },
                {
                  "mode": "NULLABLE",
                  "name": "WaitTime",
                  "type": "NUMERIC"
                },
                {
                  "mode": "NULLABLE",
                  "name": "Total",
                  "type": "NUMERIC"
                }
              ]
            }

    -   Dead letter table:

            {
              "fields": [
                {
                  "mode": "NULLABLE",
                  "name": "inputData",
                  "type": "STRING"
                },
                {
                  "mode": "NULLABLE",
                  "name": "errorMessage",
                  "type": "STRING"
                }
              ]
            }

1.  Deploy Grafana and the BigQuery Plugin for Grafana.

    For details about deploying Grafana and adding the BigQuery plugin for Grafana, see the 
    [Grafana deployment guide](https://console.cloud.google.com/marketplace/details/click-to-deploy-images/grafana) and
    [BigQuery Grafana plugin guide](https://grafana.com/grafana/plugins/doitintl-bigquery-datasource/?tab=installation).


## Create a Pub/Sub topic

This section covers publishing and subscribing to a topic with the Cloud Console. You can also configure Pub/Sub using the `gcloud` command-line tool or the API.
For more information about these methods, see the [`gcloud` documentation](https://cloud.google.com/sdk/gcloud/reference/pubsub).

1. Go to the [Pub/Sub topics page](https://console.cloud.google.com/cloudpubsub/topicList) in the Cloud Console.
1. Click **Create a Topic**.
1. Enter a unique topic name in the **Topic ID** field. This example uses `catchpoint-topic`.
1. Click **Save**. 
1. Display the menu for the topic you just created, and click **New Subscription**.
1. Enter a name for the subscription. This example uses `catchpoint-bq-dataset`.
1. Leave the delivery type set to **Pull**.
1. Click **Create**.

For more information about configuring Pub/Sub in the Cloud Console, see
[Quickstart: Using the Cloud Console](https://cloud.google.com/pubsub/docs/quickstart-console).

## Build a webhook in Google Cloud

A webhook (web application) provides a URL where vendors can post data to your application. The app listens on the defined URL and pushes posted data to the 
Pub/Sub topic created in the previous step.

1.  Download the Go script in the Cloud Storage bucket [here](https://storage.googleapis.com/webhook-catchpoint/main.go).
1.  Edit the script and replace the `DefaultCloudProjectName` value with your project ID.
1.  If you chose a Pub/Sub topic name other than `catchpoint-topic`, change the `CatchpointTopicProd` value to your chosen topic name. 

    You may keep `/cppush` as the `CatchpointPushURL` value or use another value of your choosing. After deploying the script, be sure to capture the entire 
    webhook URL, which you need when configuring Catchpoint.

1.  Deploy the script on App Engine by following the 
    [App Engine deployment](https://cloud.google.com/appengine/docs/standard/go/building-app#deploying_your_web_service_on) instructions.

## Configure Catchpoint

1.  Go to [Catchpoint API Detail](https://portal.catchpoint.com/ui/Content/Administration/ApiDetail.aspx). 
1.  Select **Add URL** under **Test Data Webhook**.
1.  Enter the entire URL for your webhook in the URL field.
1.  Under **Format** either choose **JSON** to have Catchpoint send its default data payload in JSON format, or choose **Template** to customize the data 
    payload.
    
    If you chose **Template**, then do the following:
    
    1.  Click **Select Template**.
    1.  Click **Add New**.
    1.  Enter a name for this template and select **JSON** as the format.
    1.  Enter valid JSON specifying the format of the payload that will be posted to the webhook. Each value in the template is set using a macro, which will be
        replaced with actual data at run time. See [Test Data Webhook Macros](https://support.catchpoint.com/hc/en-us/articles/360008476571) for all available
	options.
	
	Here is a sample JSON template containing recommended macros:
	
            {
            "TestName": "${TestName}",
            "TestURL": "${testurl}",
            "TimeStamp": "${timestamp}",
            "NodeName": "${nodeName}",
            "PacketLoss": "${pingpacketlosspct}",
            "RTTAvg": "${pingroundtriptimeavg}",
            "DNSTime": "${timingdns}", 
            "Connect": "${timingconnect}", 
            "SSL": "${timingssl}", 
            "SendTime": "${timingsend}",
            "WaitTime": "${timingwait}", 
            "Total": "${timingtotal}"
            }
	    
1.  Click **Save** at the bottom of the page.
 
For more information about configuring Catchpoint, see the [Catchpoint webhook document](https://support.catchpoint.com/hc/en-us/articles/115005282906).

## Build your pipeline

1.  Clone the [data loader repository](https://github.com/pupamanyu/beam-pipelines/tree/master/perf-data-loader).
1.  Change the `metric.java` file to match Catchpoint’s test data schema. You can download a ready `metric.java` file
    from [this Cloud Storage bucket](https://storage.cloud.google.com/netperf-bucket/CatchPoint%20-%20metric.java).
1.  Switch to Java 8 in Cloud Shell:

        sudo update-java-alternatives \
          -s java-1.8.0-openjdk-amd64 && \
          export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre

1.  Build the uber JAR file (the JAR file with dependencies) by running the following command in the project root directory:

        ./gradlew clean && ./gradlew shadowJar

1.  Replace the placeholders in the following command with values for your environment, and then run the command in the project root directory:

        cd build/libs && java -jar perf-data-loader-1.0.jar \
          --dataSet=[TARGET_DATASET] \
          --table=[TARGET_TABLE] \
          --deadLetterDataSet=[DEAD_LETTER_DATASET] \
          --deadLetterTable=[DEAD_LETTER_TABLE] \
          --runner=DataflowRunner \
          --project=[GOOGLE_CLOUD_PROJECT_NAME] \
          --subscription=projects/[GOOGLE_CLOUD_PROJECT_NAME]/subscriptions/[PUBSUB_SUBSCRIPTION] \
          --jobName=[PIPELINE_JOB_NAME]

    If you need to update or change the pipeline, run the command with updated values and include `--update` as an additional argument.

If the job deployed successfully, then you should see it listed in the **Jobs** view:

![sample-deployed-job](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/sample-deployed-job.png)
 
At this point, your data pipeline configuration is complete. Data posted to the webhook by Catchpoint should be propagating to your BigQuery tables and available 
for visualization in Grafana. For details, see the [Grafana documentation](https://grafana.com/docs).
    
## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1. In the Cloud Console, go to the **Projects** page.
1. In the project list, select the project that you want to delete and click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.
