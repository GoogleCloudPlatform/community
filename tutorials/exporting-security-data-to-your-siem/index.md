---
title: Export Google Cloud security data to your SIEM system
description: Learn how to deploy a unified export pipeline to stream your Google Cloud logs, asset changes, and security findings to your existing SIEM system.
author: rarsan
tags: logging, monitoring, alerts, security, siem, dataflow, scc
date_published: 2021-05-14
---

Roy Arsan | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial is for security practitioners who need to aggregate all security-relevant data (logs, alerts, and asset metadata) from their Google Cloud 
environment into their existing security information and event management (SIEM) tools.

In this tutorial, you deploy a unified export pipeline that uses Cloud Pub/Sub and Dataflow to aggregate and stream logs from Cloud Logging, security findings 
from Security Command Center, and asset changes from Cloud Asset Inventory.

![Google Cloud data export to SIEM diagram](https://storage.googleapis.com/gcp-community/tutorials/exporting-security-data-to-your-siem/siem-unified-export-pipeline.png)

## Objectives

*   Create a Pub/Sub topic and subscription to aggregate data.
*   Set up log sinks in Cloud Logging to export logs.
*   Set up a notification feed in Security Command Center to export security findings.
*   Set up an asset feed in Cloud Asset Inventory to export asset changes.
*   Deploy a Dataflow job to stream data from Pub/Sub to your SIEM system.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Pub/Sub](https://cloud.google.com/pubsub)
*   [Cloud Dataflow](https://cloud.google.com/dataflow)
*   [Security Command Center](https://cloud.google.com/security-command-center)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

This tutorial assumes that you already have your security analytics system set up to take in data from Google Cloud, which is commonly done by either pulling 
data from Pub/Sub or receiving data pushed by Dataflow. This tutorial also assumes that you have sufficient organization-wide permissions, which are required for
several steps below, such as setting up an organization-wide log sink and organization-wide feeds for security findings and asset changes.

1.  In Google [Cloud Console](https://console.cloud.google.com/), in the project selector dropdown, select or create a Google Cloud project.
1.  Activate [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell#launching_from_the_console), which provides an interactive command-line
    interface with the Cloud SDK installed.
1.  Set environment variables for your project ID and organization ID:

        export PROJECT_ID=[YOUR_PROJECT_ID]
        export ORG_ID=[YOUR_ORGANIZATION_ID]

1.  Set the project for your active session:

        gcloud config set project $PROJECT_ID

1.  Enable the Pub/Sub, Dataflow, Cloud Security Command Center, and Cloud Asset Inventory APIS:

        gcloud services enable pubsub.googleapis.com
        gcloud services enable dataflow.googleapis.com
        gcloud services enable securitycenter.googleapis.com
        gcloud services enable cloudasset.googleapis.com

## Create a Pub/Sub topic and subscription for aggregation

1.  Create a Pub/Sub topic to which the data will be sent:

        gcloud pubsub topics create export-topic

1.  Create a Pub/Sub subscription where the data will be aggregated:

        gcloud pubsub subscriptions create export-subscription \
          --topic=export-topic \
          --expiration-period="never"

## Set up an organization-wide log sink in Cloud Logging

1.  Create an organization log sink to capture Cloud audit logs from all Google Cloud projects in your organization:

        gcloud logging sinks create org-audit-logs-all \
          pubsub.googleapis.com/projects/$PROJECT_ID/topics/export-topic \
          --organization=$ORG_ID \
          --include-children \
          --log-filter="logName:logs/cloudaudit.googleapis.com"

    The `log-filter` option specifies that Cloud audit logs are routed to the Pub/Sub topic `export-topic`. You may want to edit the log filter or create 
    additional log sinks to export more logs such as VPC flow logs, load balancing request logs, or virtual machine logs such as application logs and system 
    logs, depending on your security requirements.

    This command returns the service account of the log sink writer, usually in the form `o#####-####@gcp-sa-logging.iam.gserviceaccount.com`

1.  Set an environment variable to the service account of the log sink:

        export LOG_SINK_SA=[YOUR_SERVICE_ACCOUNT]@gcp-sa-logging.iam.gserviceaccount.com

1.  Give permissions to the log sink service account to publish to the Pub/Sub topic:

        gcloud pubsub topics add-iam-policy-binding export-topic \
          --member=serviceAccount:$LOG_SINK_SA \
          --role=roles/pubsub.publisher

## Set up a notification feed in Security Command Center

1.  Set the `gcloud` tool account that you're using:

        export GCLOUD_ACCOUNT=[EMAIL_ADDRESS]

1.  Set up temporary permissions for the `gcloud` tool account that you're using, so that you can create an organization-wide finding notification feed in the 
    next step:

        gcloud pubsub topics add-iam-policy-binding \
          projects/$PROJECT_ID/topics/export-topic \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/pubsub.admin"

        gcloud organizations add-iam-policy-binding $ORG_ID \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/securitycenter.notificationConfigEditor"

1.  Create the notification feed to publish active security findings from Security Command Center to the same destination Pub/Sub topic that you used for logs
    in the previous section:

        gcloud scc notifications create scc-notifications-all-active \
          --organization="$ORG_ID" \
          --description="Notifications for active security findings" \
          --pubsub-topic=projects/$PROJECT_ID/topics/export-topic \
          --filter="state=\"ACTIVE\""

    This command creates a service account for you, usually in the form `service-org-ORGANIZATION_ID@gcp-sa-scc-notification.iam.gserviceaccount.com`, and grants
    it the `securitycenter.notificationServiceAgent` role at the organization level and the topic level, which is required for notifications to function.

1.  (Optional) You can remove the temporary permissions that you granted your `gcloud` tool account. Don't do this if you plan to continue to modify this
    notification's filter or create new notification feeds.
    
    To remove the temporary permissions, run the following commands:

        gcloud pubsub topics remove-iam-policy-binding \
          projects/$PROJECT_ID/topics/export-topic \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/pubsub.admin"

        gcloud organizations remove-iam-policy-binding $ORG_ID \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/securitycenter.notificationConfigEditor"

## Set up an asset change feed in Cloud Asset Inventory

1.  Set up temporary permissions for the `gcloud` tool account that you're using:

        gcloud organizations add-iam-policy-binding $ORG_ID \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/cloudasset.owner"
          
    This lets you create an organization-wide asset feed in the next step.

1.  Create a Cloud Asset Inventory service account for your current project:

        gcloud beta services identity create --service=cloudasset.googleapis.com --project=$PROJECT_ID

    This command returns the service account of the Cloud Asset Inventory service agent in your project, usually in the form
    `service-[YOUR_PROJECT_NUMBER]@gcp-sa-cloudasset.iam.gserviceaccount.com`.

1.  Set an environment variable to the service account of the Cloud Asset Inventory service agent:

        export ASSET_SA=service-[YOUR_PROJECT_NUMBER]@gcp-sa-cloudasset.iam.gserviceaccount.com

1.  Give the service account the permissions necessary to publish to the Pub/Sub topic `export-topic`:

        gcloud pubsub topics add-iam-policy-binding \
          projects/$PROJECT_ID/topics/export-topic \
          --member=serviceAccount:$ASSET_SA \
          --role=roles/pubsub.publisher

1.  Create an asset feed to monitor any change in resource or policy metadata of the resource itself:

        gcloud asset feeds create org-assets-all-feed \
          --organization=$ORG_ID \
          --asset-types="compute.googleapis.com.*,storage.googleapis.com.*,bigquery.googleapis.com.*,iam.googleapis.com.*" \
          --content-type=resource \
          --pubsub-topic="projects/$PROJECT_ID/topics/export-topic"
          
    In this example, as determined by the `asset-types` parameter, changing any resources of the following types anywhere in your entire organization will 
    trigger a notification:

    - Compute Engine resources
    - Cloud Storage buckets
    - BigQuery tables and datasets
    - IAM roles and service accounts
    
    Cloud Asset Inventory supports more than 120 resource types. For more information, see
    [Supported resource types](https://cloud.google.com/asset-inventory/docs/supported-asset-types#supported_resource_types).

1.  (Optional) You can remove the temporary Cloud Asset Inventory permissions that you granted your `gcloud` tool account. Don't remove these permissions if
    you plan to continue to modify this asset feed (for example, adding asset types or specific asset names).
    
    To remove the temporary permissions, run the following command:

        gcloud organizations remove-iam-policy-binding $ORG_ID \
          --member="user:$GCLOUD_ACCOUNT" \
          --role="roles/cloudasset.owner"

## Verify that logs and events are published and aggregated in Pub/Sub

You should now have three different types of events being aggregated as messages (individual JSON payloads) in a single Pub/Sub subscription,
`export-subscription`:

| Event or log                             | Schema reference |
|------------------------------------------|------------------|
| Cloud audit log                          | [`LogEntry`](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry)
| Security Command Center security finding | [`NotificationMessage`](https://cloud.google.com/security-command-center/docs/how-to-api-manage-notifications)
| Cloud Asset Inventory asset change       | [`TemporalAsset`](https://cloud.google.com/asset-inventory/docs/reference/rpc/google.cloud.asset.v1#google.cloud.asset.v1.TemporalAsset)

Verify the logs:

1.  In the Cloud Console, go to the [Pub/Sub subscriptions page](https://console.cloud.google.com/cloudpubsub/subscription).
1.  Select the `export-subscription` subscription.
1.  Click **View Messages** to open the messages viewer.
1.  Click **Pull**. Leave **Enable ack messages** unselected.
1.  Inspect the messages for audit logs, security findings, and asset change events.

## Deploy a Dataflow job to stream data from Pub/Sub

Depending on your SIEM system's support for Pub/Sub, it may retrieve messages directly from a Pub/Sub subscription as a pull delivery or a push delivery. For
details about these kinds of delivery, see [Subscriber overview](https://cloud.google.com/pubsub/docs/subscriber).

For a more flexible, managed, and scalable approach with exactly-once processing of Pub/Sub message streams, you can use
[Cloud Dataflow](https://cloud.google.com/dataflow), which is a fully-managed data streaming service with multiple supported sources and sinks, including
Pub/Sub, Cloud Storage, BigQuery, and some third-party products. There are purpose-built
[Dataflow templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-streaming) that handle the reliable delivery of data to specific 
destinations, including batching, retries, exponential backoff, and fallback to deadletter for any undeliverable messages.

For example, if you use Splunk as a SIEM tool, you can deploy the
[Pub/Sub to Splunk Dataflow template](https://cloud.google.com/blog/products/data-analytics/connect-to-splunk-with-a-dataflow-template) to deliver messages to 
the Splunk HTTP Event Collector (HEC).

1.  In Cloud Shell, create a Pub/Sub topic and subscription to hold any undeliverable messages:

        gcloud pubsub topics create export-topic-dl
        gcloud pubsub subscriptions create export-subscription-dl \
          --topic export-topic-dl \
          --expiration-period="never"

1.  Set environment variables for your Splunk HEC endpoint and token:

        export SPLUNK_HEC_URL=[YOUR_SPLUNK_URL]
        export SPLUNK_HEC_TOKEN=[YOUR_SPLUNK_TOKEN]
        
1.  Set the Dataflow pipeline job name:

        JOB_NAME=pubsub-to-splunk-`date +"%Y%m%d-%H%M%S"`

1.  Run the Dataflow job:

        gcloud beta dataflow jobs run ${JOB_NAME} \
          --gcs-location=gs://dataflow-templates/latest/Cloud_PubSub_to_Splunk \
          --region=us-central1 \
          --network=default \
          --subnetwork=regions/default/subnetworks/default \
          --parameters \
        inputSubscription=projects/${PROJECT_ID}/subscriptions/export-subscription,\
        outputDeadletterTopic=projects/${PROJECT_ID}/topics/export-topic-dl,\
        url=${SPLUNK_HEC_URL},\
        token=${SPLUNK_HEC_TOKEN}
        
    This example deploys in the `us-central1` region and in the project's `default` network.

    Within a few minutes, the Dataflow pipeline workers are provisioned and start streaming data. You can search and analyze these events in your Splunk Search
    interface.

    For a more comprehensive guide on deploying log export to Splunk, see
    [Deploying production-ready log exports to Splunk using Dataflow](https://cloud.google.com/architecture/deploying-production-ready-log-exports-to-splunk-using-dataflow).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the organization-level objects such as 
log sink and feeds and the project in which the Pub/Sub and Dataflow resources reside.

To delete all organization-wide log sinks and feeds created, run the following commands in Cloud Shell:

    gcloud logging sinks delete org-audit-logs-all \
      --organization=$ORG_ID

    gcloud scc notifications delete scc-notifications-all-active \
      --organization=$ORG_ID

    gcloud asset feeds delete org-assets-all-feed \
      --organization=$ORG_ID

To delete the project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [aggregated sinks in Cloud Logging](https://cloud.google.com/logging/docs/export/aggregated_sinks).
- Learn more about [filtering notifications in Security Command Center](https://cloud.google.com/security-command-center/docs/how-to-api-filter-notifications).
- Learn more about [monitoring asset changes in Cloud Asset Inventory](https://cloud.google.com/asset-inventory/docs/monitoring-asset-changes).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
