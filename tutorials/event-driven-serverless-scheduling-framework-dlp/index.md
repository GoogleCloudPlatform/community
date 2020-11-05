---
title: Event-driven serverless scheduling architecture with Cloud Data Loss Prevention
description: Learn how to use a simple, effective, and scalable event-driven serverless scheduling architecture with Google Cloud services.
author: codingphun
tags: DLP, serverless, schedule jobs, Cloud Function, Cloud Scheduler, BigQuery
date_published: 2020-11-05
---

Tristan Li and Wayne Davis | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows a simple yet effective and scalable event driven serverless scheduling architecture with Google Cloud services. Example included demonstrates how to work with Google Cloud Data Loss Prevention (Cloud DLP) API to inspect BigQuery data. Cloud Data Loss Prevention (Cloud DLP) can help you to discover, inspect, and classify sensitive elements in your data. The architecture is also extensible and can be easily replaced with any type of job/api with SDK support.

## Objectives

*   Enable Cloud Data Loss Prevention and BigQuery APIs
*   Create two Cloud Pub/Sub topics to handle events
*   Create two Cloud Functions to process events
*   Create a Cloud Scheduler job that triggers the job
*   Run the Cloud Scheduler job
*   Verify success of the job

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   BigQuery
*   Cloud Data Loss Prevention
*   Pub/Sub
*   Cloud Function
*   Cloud Scheduler

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Reference architecture

The following diagram shows the architecture of the solution:
![Example Architecture](https://storage.googleapis.com/gcp-community/tutorials/event-driven-serverless-scheduling-framework-dlp/arch.png)

## Before you begin

1.  Select or create a Google Cloud project
    - [Go to the Managed Resources page](https://console.cloud.google.com/cloud-resource-manager)
1.  Make sure that billing is enabled for your project 
    - [Learn how to enable billing](https://cloud.google.com/billing/docs/how-to/modify-project)
1.  Enable the BigQuery and Cloud Data Loss Prevention APIs
    - [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=bigquery.googleapis.com,dlp.googleapis.com)

## Setup instructions

1. Create two Pub/Sub topics by following instructions on [Pub/Sub quickstart guide](https://cloud.google.com/scheduler/docs/quickstart) 
    - First topic would be used by Cloud Scheduler to kick off a scheduled job
    - Second topic would be used by Cloud DLP API to notify a scanning job is complete 

1. Create two Cloud Functions with Trigger type of "Cloud Pub/Sub" by following instructons on [Cloud Functions quickstart guide](https://cloud.google.com/functions/docs/quickstart-python)
    - Make the first Cloud Function subscribes to the first Pub/Sub topic so it will be triggered when Cloud Scheduler kicks off a scheduled job. Add both [main.py](main-function/main.py) and [requirements.txt](main-function/requirements.txt) to the Cloud Function and make sure the **Entry Point** is pointing to **job_request** function.
    - Make the second Cloud Function subscribes to the second Pub/Sub topic so it will be triggered when Cloud DLP API finishes the scanning job. Add both [main.py](main-function/main.py) and [requirements.txt](main-function/requirements.txt) to the Cloud Function and make sure the **Entry Point** is pointing to **job_complete** function.

1. Follow instructions on [Cloud Scheduler quickstart guide](https://cloud.google.com/scheduler/docs/quickstart). When creating a Cloud Scheduler Job, note the following
    - Use the first Pub/Sub topic created in step ealier
    - In the payload section, use the [payload.json](payload.json) file. The payload.json is a convenient way to pass parameters to the Cloud Function for processing. Feel free to add/remove InfoTypes you want to detect in the dataset.  **In this example, be sure to replace the place holders values such as ProjectID, PubSubTopic and etc in payload.json with yours.** 
    
    ![Cloud Scheduler](https://storage.googleapis.com/gcp-community/tutorials/event-driven-serverless-scheduling-framework-dlp/cloud-scheduler.png)

1. Cloud Scheduler job can be kick off by click on the "Run now" button in the console, and it will publish a message to the first Cloud Pub/Sub topic which triggers the first Cloud Function to submit a Cloud DLP scanning job. After CloudDLP scanning job completes, it will publish a message to the second Cloud Pub/Sub topic which triggers the second Cloud Function for further processing. 

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [Cloud Data Loss Prevention](https://cloud.google.com/dlp).
- Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
