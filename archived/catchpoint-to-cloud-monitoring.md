---
title: Catchpoint data pipeline to Cloud Monitoring
description: Learn to ingest data from Catchpoint into Cloud Monitoring for visualization and analysis with Metrics Explorer.
author: drit
tags: telemetry, probes, monitors
date_published: 2021-04-20
---

Dritan Suljoti | Chief Product and Technology Officer | Catchpoint Systems, Inc.

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

[Catchpoint’s digital experience monitoring platform](https://www.catchpoint.com/platform) provides an extensive fleet of network telemetry probes, as well as 
tools for capturing real user experience metrics, which give instant insight into the performance of networks, apps, and digital services.
[Cloud Monitoring](https://cloud.google.com/monitoring) provides visibility into the performance, uptime, and overall health of applications.

This tutorial and its companion tutorial provide two methods of ingesting and visualizing data from Catchpoint within Google Cloud:

- This tutorial shows you how to set up a pipeline that ingests data captured by Catchpoint into Cloud Monitoring and use Metrics Explorer for visualization and
  analysis.
- The [companion tutorial](https://cloud.google.com/community/tutorials/catchpoint-to-grafana) shows you how to deliver data to 
  Grafana for visualization and analysis.
  
This tutorial uses Node.js, the Cloud Console, and the Cloud SDK command line.

The data flow from Catchpoint to Cloud Monitoring is illustrated in the following diagram:

![data-ingestion-pipeline](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/data-ingestion-pipeline.png)

1.  Catchpoint posts data to a Cloud Function (HTTP webhook).
1.  The Cloud Function uses Pub/Sub to propagate the data to configured channels.
1.  Cloud Monitoring receives the data from the Pub/Sub channel, where it's available for visualization using Metrics Explorer

## Objectives

1.  Set up the Google Cloud data pipeline.
1.  Configure Catchpoint.
1.  Set up Cloud Monitoring.
1.  Configure Metrics Explorer in Cloud Monitoring.

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

1.  Install the Cloud Monitoring Client Libraries and set up authentication.

    For details, see [Cloud Monitoring Client Libraries](https://cloud.google.com/monitoring/docs/reference/libraries).

1.  Enable the Monitoring API v3 and authorize users.

    For details, see [Enabling the Monitoring API](https://cloud.google.com/monitoring/api/enable-api).

1.  Enable the Cloud Functions and Pub/Sub APIs.

    For details, see [Cloud Pub/Sub Tutorial](https://cloud.google.com/functions/docs/tutorials/pubsub).

## Set up the Google Cloud data pipeline

1.  Clone [the repository with the integration between Catchpoint and Cloud Monitoring](https://github.com/catchpoint/Integrations.GoogleCloudMonitoring) 
    (formerly _Stackdriver_) to your local machine.

    The `Stackdriver-Webhook` folder has the required Node.js script to set up the ingestion of data and writing of data to Cloud Monitoring.
    
1.  Edit [`Stackdriver-Webhook/.env`](https://github.com/catchpoint/Integrations.GoogleCloudMonitoring/blob/master/Stackdriver-Webhook/.env) and update the
    value of the `GoogleProjectId` variable to the project ID for your Google Cloud project.
   
    For more information about environment variables, see [Using environment variables](https://cloud.google.com/functions/docs/configuring/env-var).

1.  On the Cloud SDK command line, go to the directory where you cloned the Node.js scripts:

        cd [PATH_TO_CLONED_DIRECTORY]

1.  Set the project property to the current project:

        gcloud config set project [YOUR_PROJECT_ID]

1.  Deploy the Catchpoint publish function:

        gcloud functions deploy catchpointPublish \
          --trigger-http \
          --runtime nodejs10 \
          --trigger-http \
          --allow-unauthenticated

    This function creates a topic using the `TopicName` value from the `.env` file. By default, this name is `catchpoint-webhook`. If you want to use a different
    name, then you must change this value in the `.env` file before running the command.
    
1.  Capture the HTTP Trigger URL after the deployment is successful.

    ![sample-publish-function](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/sample-publish-function.png)
    
    You need this when configuring Catchpoint.

1.  Deploy the Catchpoint subscribe function:

        gcloud functions deploy catchpointSubscribe \
          --trigger-topic catchpoint-webhook \
          --runtime nodejs10 \
          --allow-unauthenticated \
 
    This command assumes that you have used the default topic name, `catchpoint-webhook`. If you used a different topic name, then replace the topic name in this
    command with yours.
    
    ![sample-subscribe-function](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/sample-subscribe-function.png)

## Configure Catchpoint

1.  Go to [Catchpoint API Detail](https://portal.catchpoint.com/ui/Content/Administration/ApiDetail.aspx).

    For more information, see [Catchpoint Webhook document](https://support.catchpoint.com/hc/en-us/articles/115005282906).
    
1.  Click **Add URL** under **Test Data Webhook**.
1.  In the URL field, enter the HTTP Trigger URL that you generated in the previous section.
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
 
## Set up Cloud Monitoring

1.  In the Cloud Console, go to the [**Monitoring** page](https://console.cloud.google.com/monitoring), and select **Overview**, which creates a Workspace.
1.  Select **Metrics Explorer** in the **Monitoring** navigation pane.
1.  Enter the monitored resource name in the **Find resource type and metric** text box.
    
    ![GCM Metrics](https://storage.googleapis.com/gcp-community/tutorials/catchpoint/gcm-metrics.png)
    
Catchpoint metrics are represented in Metrics Explorer using custom metrics with `catchpoint_` prepended to their original names. For example, if a metric is
named `DNS` in Catchpoint, the corresponding custom metric in Metrics Explorer is named `catchpoint_DNS`.
    
You can filter your query results based on the Catchpoint node name and test ID, which are included as labels on each data point.
    
For more information on custom metrics, see [Creating custom metrics](https://cloud.google.com/monitoring/custom-metrics/creating-metrics).
    
At this point your data pipeline is fully configured and you can create custom [charts and dashboards](https://cloud.google.com/monitoring/charts/) in Cloud
Monitoring to visualize your Catchpoint data.
    
## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1. In the Cloud Console, go to the **Projects** page.
1. In the project list, select the project that you want to delete and click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.
