---
title: Building a Slack Reminder App with Google Cloud Functions and Google Cloud Scheduler
description: Build a Slack App that sends messages to a channel at an interval of 3 hours.
author: timtech4u
tags: Cloud Function, Cloud Scheduler, Slack
date_published: 2019-07-11
---

In this tutorial we will build and deploy a serverless application that sends messages to Slack by leveraging on Google Cloud Function.
We will also use Google Cloud Scheduler to periodically run our application at an interval of 3hours.

## Objectives

- Create a [Slack App](https://api.slack.com/apps?new_app=1).
- Create a HTTP Serverless Function that sends messages to Slack with [Cloud Function](https://cloud.google.com/functions)
- Create a Scheduled Job that calls our Cloud Function every 3hours with [Cloud Scheduler](https://cloud.google.com/scheduler)

## Before you begin

1.  [Create a new Google Cloud Platform project, or use an existing one](https://console.cloud.google.com/project).
2.  [Enable billing for your project](https://support.google.com/cloud/answer/6293499#enable-billing).
3.  Create a [new Slack team](https://slack.com/create), or use an team where you have permissions to add integrations.

## Costs

This tutorial uses billable components of Cloud Platform including Google
Compute Engine. Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=6d866c0e-b928-4786-b2ab-bed5c380a2fd)
to estimate the costs for your usage.

Slack is free for up to 10 apps and integrations. Check the [Slack pricing
page](https://slack.com/pricing) for details.

## Getting the sample code

Get the sample code from GitHub Gist.
([here](https://gist.github.com/Timtech4u/2f59976a183eefe57bb65be247de49b5))

## Setting up Slack

To create a new Slack app, go to the [app management
page](https://api.slack.com/apps?new_app=1) and click **Create new app**.

1.  Give the app a name, such as "RestReminder".
2.  Choose the Slack team for development and where you will eventually install it.
3.  Click Incoming Webhooks.
4.  Enable incoming webhooks.
5.  Click Add New Webhook to Team. An authorization page opens.
6.  From the drop-down menu, select the channel to which you would like notifications sent. We'll be using the #random channel
7.  Click Authorize.
8.  A webhook for your Slack application has been created. Copy the webhook and save it for later use. 

## Setting up Cloud Function

Visit [Cloud Function Console](https://console.cloud.google.com/functions) and click **Create Function**

1.  Enter your function's name
2.  Set Memory Allocated : 256MB
3.  Set Trigger : HTTP
4.  Authentication : Check - Allow unauthenticated invocations
5.  Source code : Select - Inline editor
6.  Runtime : Node.js 8 (Feel free to change this to suit your choice in future)
7.  Function to execute : sendToSlack 
8.  Paste the sample code snippet into the Inline editor both index.js and package.json
9. Deploy

Once done, you can visit the URL on your Cloud Function URL to test.

## Setting up Cloud Scheduler

Visit [Cloud Scheduler Console](https://console.cloud.google.com/cloudscheduler) and click **Create Job**

1.  Enter job name
2.  Set Frequency : every 3 hours
3.  Target : Select HTTP
4.  Set URL : (Use your deployed Cloud Function URL)
5.  HTTP Method : Select GET

Great! You just scheduled a Slack Bot that sends a message to your Slack Channel every 3 hours. 

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this tutorial.

1. Delete the project used (if you create a new project).
2. Delete the Cloud Scheduler Job and Cloud Function.
2. OR Pause the Cloud Scheduler Job.

## Next steps

If you want to learn more about Google Cloud Functions and Google Cloud Scheduler, check out the following resources.

-  [Google Cloud Function](https://cloud.google.com/functions)
-  [Google Cloud Scheduler](https://cloud.google.com/scheduler)
-  [Cloud Functions for Firebase](https://firebase.google.com/docs/functions)
-  [Scheduled Cloud Functions for Firebase](https://firebase.google.com/docs/functions/schedule-functions)
-  [Awesome List for Google Cloud Platform](https://github.com/GoogleCloudPlatform/awesome-google-cloud)
