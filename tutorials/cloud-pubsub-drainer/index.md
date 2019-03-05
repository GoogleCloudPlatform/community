---
title: Alert based Event Archiver
description: Use Strackdriver Alerting to trigger a serverless event archive task in Cloud Pub/Sub.
author: ptone
tags: IoT, Cloud Pubsub, Stackdriver, Cloud Functions, Serverless
date_published: 2018-03-05
---
<!-- private diagram sources: https://docs.google.com/presentation/d/1U0QYoR-CW9NWPV7-ZRqK8lLaOoEoSxkQdBc_L-Tj27A/edit#slide=id.g506f2f687f_0_0 -->

Preston Holmes | Solution Architect | Google Cloud

Cloud Pub/Sub is often used for large data flows and is capable of handling large throughput. But it is also often used for lower-volume event streams that are still of high value, or are more irregular in their arrival rates.

[Cloud Dataflow Templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates#cloudpubsubtogcstext) allow you to easily deploy a Cloud Dataflow job to move events from Cloud Pub/Sub to Cloud Storage. This will run a streaming Dataflow job continuously and may be expensive to run when the event volume is low, or if you have multiple medium volume topics to archive.

Cloud Pub/Sub will retain messages for 7 days in a subscription resource before they are deleted. This means that lower volume topics can be periodically archived as batches into Cloud Storage objects without running a continuous streaming job. Cloud Function PubSub triggers can not be used for this directly - as they are invoked for each Cloud Pub/Sub message individually and you generally want to archive in batches.

This solution uses the built-in metrics for subscription resources in Cloud Pub/Sub subscriptions to trigger an archiving task based on a combination of backlog size and age.

## Objectives

* Create a Stackdriver notification webhook.
* Create a Stackdriver Alerting policy with Cloud Pub/Sub conditions.
* Create a pair of Cloud Functions that respond to the Stackdriver alert
* Verify that data gets archived from Cloud Pub/Sub to Cloud Storage

## Architecture

![](image/architecture.png)

There are several components to the architecture.

* A data ingest Cloud Pub/Sub topic - this is where events of interest are received.
* A Stackdriver Alert which consists of:
	* Alerting Policy watching metrics related to a subscription associated with the data ingest topic
	* A webhook notification channel which points to a Cloud Function
* A Cloud Pub/Sub topic which durably records the alert incident relaying it to the Archiver function
* The archiver function, which uses streaming pull with Cloud Pub/Sub and streaming write to Cloud Storage to efficiently batch and move event data from Cloud Pub/Sub to Cloud Storage.

## Before you begin

1. Create a Google Cloud Project for this tutorial to allow for easier cleanup
2. Create a [Stackdriver workspace](https://cloud.google.com/monitoring/workspaces/guide) 
3. enable cloud functions

## Setting up the automation

Commands in this tutorial assume you are running from the tutorial folder:

	git clone https://github.com/GoogleCloudPlatform/community.git
	cd community/tutorials/cloud-pubsub-drainer/

### Install gcloud alpha components

You will use the new support for CLI access to Stackdriver resources which currently is supported in the gcloud alpha component.

	gcloud components install alpha

### Set environment variables

These will be used throughout the project.

	export FULL_PROJECT=$(gcloud config list project --format "value(core.project)")
	export PROJECT_ID="$(echo $FULL_PROJECT | cut -f2 -d ':')"

### Create a data archive bucket

This is the bucket into which we will archive data from Cloud Pub/Sub into.

	gsutil mb gs://$PROJECT_ID-data-archive

### Create Cloud Pub/Sub resources

	gcloud pubsub topics create demo-data
	gcloud pubsub subscriptions create bulk-drainer --topic demo-data
	gcloud pubsub topics create drain-tasks

The "demo-data" topic is the main topic where data is sent that we want to archive. It may have several subscriptions to it which react to events, or process streaming data. In Cloud Pub/Sub each subscription gets its own durable copy of the data.

The "bulk-drainer" subscription is created to act as the storage buffer dedicated to the archiver task.

The "drain-tasks" topic, serves as a durable relay of the Stackdriver alert occurrence.

### Deploy the Archiving Function

The "Archiver" function is woken up by a Stackdriver condition based alert and drains any outstanding events in the "bulk-drainer" subscription into chunked objects in the data-archive bucket.

    cd drainer-func
    gcloud functions deploy Archiver \
        --runtime go111 \
        --trigger-topic drain-tasks \
        --update-env-vars BUCKET_NAME=$PROJECT_ID-data-archive,SUBSCRIPTION_NAME=bulk-drainer,AUTH_TOKEN=abcd

How much is consolidated per object is configured in the code, but can be set to a number of messages or a certain number of bytes.

### Deploy webhook relay

Stackdriver does not currently have a native Cloud Pub/Sub alert notification channel. We use a small HTTP Cloud Function to act as a simple relay. The `AUTH_TOKEN` environment variable sets an expected shared secret between the Stackdriver Notification Channel and the webhook.

	gcloud functions deploy StackDriverRelay --runtime go111 --trigger-http --update-env-vars AUTH_TOKEN=abcd

### Allow Stackdriver to call the webhook

*Cloud Function Alpha Users Only* 

Stackdriver can only reach publicly accesible webhooks, and if you are using a project with function authorization enabled, you will need to make it reachable.

	gcloud alpha functions add-iam-policy-binding StackDriverRelay --member "allUsers" --role "roles/cloudfunctions.invoker"

### Create Stackdriver Notification Channel

In Stackdriver, a Notification Channel is a resource that can be used with one or more Alert Policies. These can be created in the console or via API.  Using the URL from our deployed function, you create a new channel, and then get the Stackdriver-assigned channel identifier as an environment variable.

	export URL=$(gcloud functions describe StackDriverRelay --format='value(httpsTrigger.url)')

	gcloud alpha monitoring channels create --channel-content-from-file channel.json --channel-labels url=$URL?token=abcd

	export CHANNEL=$(gcloud alpha monitoring channels list --filter='displayName="Archiver"' --format='value("name")')

### Create a Stackdriver Alerting Policy

Alerting Policies describe conditions that result in the alert firing as true. This is where we want to create an alert condition if messages in our "bulk-drainer" Cloud Pub/Sub subscription get either too numerous, or too old.  See the contents of `policy.json` in the tutorial repo for details. The duration and size thresholds are set low so that the solution can be tested and demonstrated quickly.

After the policy is created, the ID is retrieved and then it is updated with to use the Notification Channel created earlier.

	gcloud alpha monitoring policies create --policy-from-file=policy.json

	export POLICY=$(gcloud alpha monitoring policies list --filter='displayName="archive-pubsub"' --format='value("name")')

	gcloud alpha monitoring policies update $POLICY --add-notification-channels=$CHANNEL

	At this point, the solution is fully deployed. You can see and review the policy in the alerting section of Stackdriver Console. You can see notification channels in the workspace settings area of the Stackdriver console.

## Testing the solution

### Create test data

The loader script creates some synthetic test data

	cd ../loader
	go run main.go

To test the age based condition in the policy, let the loader run just for a moment, cancel with CTRL-C, then wait a few minutes till the condition is triggered.

For backlog-size based condition trigger, let the loader tool run for several minutes before cancelling.  Note, do not let this script run indefinitely - as it will continue to generate billable volumes of data.

Note that Stackdriver metrics do not appear instantaneously, it takes some time for them to show in the alert policy charts. Also note that for the condition to fire, it has to be true for 1 minute (this is a configurable part of policy).

While you wait for a alert to fire, you may wish to check out the [Stackdriver alerting policy overview](https://cloud.google.com/monitoring/alerts/).

### Check the function logs

The Archiver function logs should show the archiving activity, including how many messages were archived.

### Check the archive bucket

If you look in the data archive bucket in the Cloud Console [storage browser](https://console.cloud.google.com/storage) you will see a set of nested folders by year/month/day and then named for the time the archive event occurred.

The size archive size is set to 1MB in this tutorial, though that is adjustable in the function code.

## Limits of the pattern

This pattern is not appropriate for all cases. Notably function invocations are limited to 10 minutes. This means that the alert policy should trigger often enough that the archive task completely well within this timeframe as Alerts to not retry.

If the data-volume into Cloud Pub/Sub is too much to be archived by such a periodic task, it is better handled by a proper [streaming Dataflow job](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates#cloudpubsubtogcstext).

## Cleaning up and next steps


	gcloud functions delete Archiver
	gcloud functions delete StackDriverRelay
	gcloud pubsub subscriptions delete bulk-drainer --topic demo-data
	gcloud pubsub topics delete drain-tasks
	gcloud pubsub topics delete demo-data

You can choose to delete the Stackdriver notifications and alert policy in the Stackdriver console.

### Next steps

There are several ways to extend this pattern

* Add scheduled run of the archiver using [Cloud Scheduler](https://cloud.google.com/scheduler/) as an extra backstop
* Add conversion and compression (eg avro) to the data as you write it to Cloud Storage
* Add nightly [load of all archived files into BigQuery](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage)
