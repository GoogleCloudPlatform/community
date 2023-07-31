---
title: Event-driven serverless scheduling architecture with Cloud Data Loss Prevention
description: Learn how to use a simple, effective, and scalable event-driven serverless scheduling architecture with Google Cloud services.
author: codingphun
tags: DLP, serverless, schedule jobs, Cloud Functions, Cloud Scheduler, BigQuery
date_published: 2020-11-04
---

Tristan Li and Wayne Davis | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows a simple yet effective and scalable event-driven serverless scheduling architecture with Google Cloud services. The example included
demonstrates how to work with the Cloud Data Loss Prevention (Cloud DLP) API to inspect BigQuery data. Cloud Data Loss Prevention can help you to discover,
inspect, and classify sensitive elements in your data. The architecture is also extensible and can be easily replaced with any type of job or API with SDK 
support.

## Objectives

*   Enable Cloud Data Loss Prevention and BigQuery APIs.
*   Create two Pub/Sub topics to handle events.
*   Create two Cloud Functions to process events.
*   Create a Cloud Scheduler job that triggers the job.
*   Run the Cloud Scheduler job.
*   Verify success of the job.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   BigQuery
*   Cloud Data Loss Prevention
*   Pub/Sub
*   Cloud Functions
*   Cloud Scheduler

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Reference architecture

The following diagram shows the architecture of the solution:

![Example Architecture](https://storage.googleapis.com/gcp-community/tutorials/event-driven-serverless-scheduling-framework-dlp/arch.png)

## Before you begin

1.  Select or create a Google Cloud project:

    [Go to the Resource Manager page.](https://console.cloud.google.com/cloud-resource-manager)
    
1.  Make sure that [billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

1.  Enable the BigQuery and Cloud Data Loss Prevention APIs:

    [Enable the APIs.](https://console.cloud.google.com/flows/enableapi?apiid=bigquery.googleapis.com,dlp.googleapis.com)

## Setup instructions

1.  Create two Pub/Sub topics by following the instructions in the [Pub/Sub quickstart guide](https://cloud.google.com/scheduler/docs/quickstart).

    - The first topic is used by Cloud Scheduler to start a scheduled job.
    - The second topic is used by the Cloud DLP API to notify when a scanning job is complete.

1.  Create two Cloud Functions with the trigger type **Cloud Pub/Sub** by following the instructions in the
    [Cloud Functions quickstart guide](https://cloud.google.com/functions/docs/quickstart-python).
    
    - Make the first Cloud Function subscribe to the first Pub/Sub topic so that the function is triggered when Cloud Scheduler starts a scheduled job. Add both
    [`main.py`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/event-driven-serverless-scheduling-framework-dlp/main-function/main.py) 
    and
    [`requirements.txt`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/event-driven-serverless-scheduling-framework-dlp/main-function/requirements.txt)
    to the Cloud Function, and make sure that the **Entry Point** is pointing to the **job_request** function.
    - Make the second Cloud Function subscribe to the second Pub/Sub topic so that the function is triggered when the Cloud DLP API finishes the scanning job. 
    Add both
    [`main.py`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/event-driven-serverless-scheduling-framework-dlp/main-function/main.py) 
    and
    [`requirements.txt`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/event-driven-serverless-scheduling-framework-dlp/main-function/requirements.txt)
    to the Cloud Function and make sure that the **Entry Point** is pointing to the **job_complete** function.

1.  Create a Cloud Scheduler job by following the instructions in the [Cloud Scheduler quickstart guide](https://cloud.google.com/scheduler/docs/quickstart).

    - Use the first Pub/Sub topic created in the first step in this section.
    - In the payload section, use the 
      [`payload.json`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/event-driven-serverless-scheduling-framework-dlp/payload.json) 
      file. The `payload.json` file is a convenient way to pass parameters to the Cloud Function for processing. You can add or remove InfoTypes to match what
      you want to detect in the dataset. In this example, be sure to replace the placeholder values such as `ProjectID` and `PubSubTopic` with your values.
    
    ![Cloud Scheduler](https://storage.googleapis.com/gcp-community/tutorials/event-driven-serverless-scheduling-framework-dlp/cloud-scheduler.png)

## Run the example

Start Cloud Scheduler by clicking the **Run now** button in the Cloud Console.

This publishes a message to the first Pub/Sub topic, which triggers the first Cloud Function to submit a Cloud DLP scanning job.
    
After the Cloud DLP scanning job completes, it will publish a message to the second Pub/Sub topic, which triggers the second Cloud Function for further 
processing. 

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [Cloud Data Loss Prevention](https://cloud.google.com/dlp).
- Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
