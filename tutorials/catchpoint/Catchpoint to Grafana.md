---
title: Catchpoint data pipeline to Grafana
description: Learn to ingest data from Catchpoint into Google Cloud Platform for visualization and analysis via Grafana.
author: drit
tags: telemetry, probes, monitors
date_published: 2021-02-16
---

Dritan Suljoti | Chief Product and Technology Officer | Catchpoint Systems, Inc.

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

[Google Cloud Monitoring](https://cloud.google.com/monitoring), in conjunction with the open-source analytics and interactive visualization web application [Grafana](https://grafana.com/oss/), can be used to realize the vision of a single pane for all network performance monitoring and analysis. [Catchpoint’s digital experience monitoring platform](https://www.catchpoint.com/platform) provides the most extensive fleet of network telemetry probes in the world, as well as tools for capturing Real User experience metrics. In this tutorial, you will learn how to set up a pipeline that takes data captured by Catchpoint and processes it to Google Cloud Platform for visualization and analysis in Grafana.

The fully configured data pipeline from Catchpoint to Grafana will work as follows:

![integration pipeline](integration-pipeline.png)
 
1.	Catchpoint posts data to an HTTP webhook set up in App Engine.
1.	App Engine publishes the data to a Pub/Sub channel.
1.	A Cloud Dataflow job listens to the Pub/Sub channel and inserts a BigQuery-accessible dataset.
1.	Data is sent to BigQuery along with the Catchpoint schema.
1.	Grafana's BigQuery plugin is used as a data source to visualize the data.

## Objectives

The configuration process consists of five main objectives:
1.	Create a Pub/Sub Topic
2.	Build a Webhook in GCP
3.	Configure Catchpoint
4.	Build your Pipeline
5.	Configure Grafana


## Costs

This tutorial uses billable components of Google Cloud, including the following:

- [Cloud Functions](https://cloud.google.com/functions)
- [App Engine](https://cloud.google.com/appengine/docs/flexible/python)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

### 1. Create a new project in Google Console or reuse an existing project
Refer to [Creating and managing projects | Resource Manager Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects) for steps to create a new project. You will need the Google Project ID when configuring the Catchpoint script.
### 2. Create BigQuery Tables
This integration uses BigQuery to run analytics. You need to create two BigQuery tables: the “main” table and the “dead_letter” table. Refer to [How to create a BigQuery table](https://cloud.google.com/bigquery/docs/tables) for general information on creating BigQuery tables, and use the following sample scripts to create the [main table](https://storage.cloud.google.com/netperf-bucket/CatchPoint%20-%20main%20table?cloudshell=true) and [dead_letter table](https://github.com/pupamanyu/beam-pipelines/tree/master/perf-data-loader).
### 3. Deploy Grafana and the BigQuery Plugin for Grafana
Please use the following resources to deploy Grafana in your GCP project and to add the BigQuery Grafana plugin:

[Deploy Grafana Guide](https://console.cloud.google.com/marketplace/details/click-to-deploy-images/grafana)<br>
[BigQuery Grafana plugin](https://grafana.com/grafana/plugins/doitintl-bigquery-datasource)


***Note:** Some steps in this tutorial are performed via the Cloud Console, and others via the gcloud command-line tool. The tutorial assumes you are familiar with accessing and using these tools.*

## Tutorial body

### Create a Pub/Sub Topic<br>
This section covers publishing and subscribing to a topic via Google Cloud Console. It is also possible to configure Pub/Sub using the gcloud command-line tool or the API. Refer to [gcloud pubsub reference](https://cloud.google.com/sdk/gcloud/reference/pubsub) for more information on these methods.

1.	Go to the [Pub/Sub topics page](https://console.cloud.google.com/cloudpubsub/topicList) in the Cloud Console.
1.	Click Create a Topic.
1.	Input a unique topic name in the Topic ID. We will use “catchpoint-topic” for our example.
1.	Click Save. 
1.	Display the menu for the topic you just created, and click New Subscription.

1.	Type a name for the Subscription. We will call ours “catchpoint-bq-dataset”.

1.	Leave the delivery type as Pull.
1.	Click Create.

Need additional help configuring Pub/Sub in the Cloud Console? See [Quickstart: using the Google Cloud Console](https://cloud.google.com/pubsub/docs/quickstart-console).

### Build a Webhook in GCP
A webhook (web application) provides a URL where vendors can post data to your application. The app will listen on the defined URL and push posted data to the Pub/Sub Topic created in the previous step.

1.	Download the go script in the GCS bucket [here](https://storage.googleapis.com/webhook-catchpoint/main.go).
1.	Edit the script and replace the DefaultCloudProjectName value with your project's Project ID.
1. If you chose a different Pub/Sub topic name than "catchpoint-topic", change the CatchpointTopicProd value to your chosen topic name.  
***Note:** You may keep "/cppush" as the CatchpointPushURL value or use another value of your choosing. After deploying the script, be sure to capture the entire Webhook URL, as you will need this when configuring Catchpoint.*

1. Deploy the script on App Engine per the instructions in [App Engine Deployment](https://cloud.google.com/appengine/docs/standard/go/building-app#deploying_your_web_service_on).

### Configure Catchpoint
1.	Navigate to [Catchpoint API Detail](https://portal.catchpoint.com/ui/Content/Administration/ApiDetail.aspx). 
1.	Select Add URL under Test Data Webhook
1.	Input the entire URL for your Webhook in the URL field.
1.	Select a data payload format. Choose “JSON” to have Catchpoint send its default data payload in JSON format, or choose “Template” if you want to customize the data payload. Steps 5-8 are only necessary if you choose Template.
1.	Click Select Template
1.	Click Add New
1.	Input a Name for this template and select "JSON" as the format.
1.	Input valid JSON specifying the format of the payload that will be posted to the Webhook. Each value in the template is set using a Macro, which will be replaced with actual data at runtime. See [Test Data Webhook Macros](https://support.catchpoint.com/hc/en-us/articles/360008476571) for all available options.

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

9.	Click Save at the bottom of the page.

For more help configuring Catchpoint, see the [Catchpoint Webhook document](https://support.catchpoint.com/hc/en-us/articles/115005282906).

### Build your Pipeline
1.	Clone the [Cloud DataFlow repository](https://github.com/pupamanyu/beam-pipelines/tree/master/perf-data-loader).
2.	Change the Metric.java file to match Catchpoint’s test data schema. You can download a ready metric.java file [here](https://storage.cloud.google.com/netperf-bucket/CatchPoint%20-%20metric.java).
3.	Switch to Java8 on cloud shell by running this command:

        sudo update-java-alternatives \
        -s java-1.8.0-openjdk-amd64 && \
        export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre

4.	Build the Fat Jar by executing the following command from within the project root directory:

		./gradlew clean && ./gradlew shadowJar

5.	Replace the placeholders in the following command with valid values, then execute it from within the project root directory:

        cd build/libs && java -jar perf-data-loader-1.0.jar \
        --dataSet=<target-dataset> \
        --table=<target-table> \
        --deadLetterDataSet=<dead-letter-dataset> \
        --deadLetterTable=<dead-letter-table> \
        --runner=DataflowRunner \
        --project=<gcp-project-name> \
        --subscription=projects/<gcp-project- name>/subscriptions/<pub-sub-subscription> \
        --jobName=<pipeline-job-name>

    ***Note:** If you need to update/change the pipeline, run the above command with updated values and include --update as an additional argument.*

If the job deployed successfully then you should see it listed in the Jobs view as in this example:

![sample-deployed-job](sample-deployed-job.png)
 

At this point your data pipeline configuration is complete. Data posted to the Webhook by Catchpoint should be propagating to your BigQuery tables and available for visualization in Grafana. Please refer to the [Grafana Documentation](https://grafana.com%2Fdocs) for details on its visualization/analytics capabilities.
    
## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:
- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

To delete a project, do the following:
1.	In the Cloud Console, go to the Projects page.
1.	In the project list, select the project you want to delete and click Delete.
1.	In the dialog, type the project ID, and then click Shut down to delete the project.