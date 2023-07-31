---
title: Building a Slack reminder app with Cloud Functions and Cloud Scheduler
description: Build a Slack app that sends messages to a channel at an interval of 3 hours.
author: timtech4u
tags: Cloud Function, Cloud Scheduler, Slack
date_published: 2019-07-13
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you build and deploy a serverless application that sends messages to Slack using a Cloud Function.
You also use Cloud Scheduler to periodically run your application at an interval of 3 hours.

## Objectives

- Create a [Slack app](https://api.slack.com/apps?new_app=1).
- Create an HTTP serverless function that sends messages to Slack with a
  [Cloud Function](https://cloud.google.com/functions).
- Create a scheduled job that calls your Cloud Function every 3 hours with
  [Cloud Scheduler](https://cloud.google.com/scheduler).

## Before you begin

1.  [Create a new Google Cloud project](https://console.cloud.google.com/project), or use an existing one.
2.  [Enable billing for your project](https://support.google.com/cloud/answer/6293499#enable-billing).
3.  Create a [new Slack team](https://slack.com/create), or use a team for which you have permissions to add integrations.

## Costs

This tutorial uses billable components of Google Cloud including Compute Engine. Use the
[Pricing Calculator](https://cloud.google.com/products/calculator/#id=6d866c0e-b928-4786-b2ab-bed5c380a2fd)
to estimate the costs for your usage.

Slack is free for up to 10 apps and integrations. Check the [Slack pricing page](https://slack.com/pricing) for details.

## Get the sample code

Get the sample code from GitHub Gist, [here](https://gist.github.com/Timtech4u/2f59976a183eefe57bb65be247de49b5).

## Create a new Slack app and set up Slack

1.  Go to the [Slack app management page](https://api.slack.com/apps?new_app=1).
1.  Click **Create new app**.
1.  Give the app a name, such as "RestReminder".
1.  Choose the Slack team for development and where you will eventually install it.
1.  Click **Incoming Webhooks**.
1.  Enable incoming webhooks.
1.  Click **Add New Webhook to Team**. An authorization page opens.
1.  From the drop-down menu, select the channel to which you would like notifications sent. We'll be using
    the #random channel.
1.  Click **Authorize**.
1.  A webhook for your Slack application has been created. Copy the webhook and save it for later use. 

## Set up the Cloud Function

1.  Go to the [**Cloud Functions** page of the Cloud Console](https://console.cloud.google.com/functions).
1.  Click **Create Function**.
1.  Enter your function's name in the **Name** field.
1.  Set **Memory allocated** to **256MB**.
1.  Set **Trigger** to **HTTP**.
1.  For **Authentication**, check **Allow unauthenticated invocations**.
1.  For **Source code**, select **Inline editor**.
1.  For **Runtime**, choose **Node.js 8**. (Feel free to change this to suit your choice in future.)
1.  Paste the sample code into the inline editor, both `index.js` and `package.json`.
1.  For **Function to execute**, enter `sendToSlack`.
1.  Click the **Create** button to deploy the new Cloud Function.

After these steps are done, you can visit the URL on your Cloud Function URL to test.

## Set up Cloud Scheduler

1.  Go to the [**Cloud Scheduler** page of the Cloud Console](https://console.cloud.google.com/cloudscheduler).
1.  Click **Create Job**.
1.  Enter a job name in the **Name** field.
2.  In the **Frequency** field, enter `0 */3 * * *`, which indicates every 3 hours in unix-cron format.
3.  For **Target**, select **HTTP**.
4.  In the **URL** field, enter your deployed Cloud Function URL.
5.  For **HTTP method**, select GET.

Great! You just scheduled a Slack Bot that sends a message to your Slack channel every 3 hours. 

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this tutorial.

1. Delete the project used (if you created a new project).
2. Delete the Cloud Scheduler job and Cloud Function.

You might also choose to pause the Cloud Scheduler job.

## Next steps

If you want to learn more about Cloud Functions and Cloud Scheduler, check out the following resources:

-  [Cloud Function](https://cloud.google.com/functions)
-  [Cloud Scheduler](https://cloud.google.com/scheduler)
-  [Cloud Functions for Firebase](https://firebase.google.com/docs/functions)
-  [Scheduled Cloud Functions for Firebase](https://firebase.google.com/docs/functions/schedule-functions)
-  [Awesome List for Google Cloud Platform](https://github.com/GoogleCloudPlatform/awesome-google-cloud)
