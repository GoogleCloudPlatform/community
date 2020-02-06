---
title: Alert-based event archiver with Stackdriver and Cloud Pub/Sub
description: Use Stackdriver alerting to trigger a serverless event archive task in Cloud Pub/Sub.
author: ptone
tags: IoT, Cloud Pubsub, Stackdriver, Cloud Functions, Serverless
date_published: 2019-03-15
---

Preston Holmes | Solution Architect | Google Cloud

Cloud Pub/Sub is often used for large data flows and is capable of handling large throughput, but it is also often used
for high-value event streams that have lower volumes or are more irregular in their arrival rates.

[Cloud Dataflow templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates#cloudpubsubtogcstext)
allow you to easily deploy a Cloud Dataflow job to move events from Cloud Pub/Sub to Cloud Storage. This will run a 
streaming Dataflow job continuously and may be expensive to run when the event volume is low, or if you have multiple
medium-volume topics to archive.

Cloud Pub/Sub retains messages for 7 days in a subscription resource before they are deleted. This means that
lower-volume topics can be periodically archived as batches into Cloud Storage objects without running a continuous 
streaming job. Cloud Function Pub/Sub triggers can't be used for this directly, since they are invoked for each Cloud
Pub/Sub message individually and you generally want to archive in batches.

This solution uses the built-in metrics for subscription resources in Cloud Pub/Sub subscriptions to trigger an archiving 
task based on a combination of backlog size and age.

## Objectives

* Create a Stackdriver notification webhook.
* Create a Stackdriver alerting policy with Cloud Pub/Sub conditions.
* Create a pair of Cloud Functions that respond to the Stackdriver alert.
* Verify that data gets archived from Cloud Pub/Sub to Cloud Storage.

## Architecture

![architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/architecture.png)

There are several components to the architecture:

* Data ingest Cloud Pub/Sub topic: This is where events of interest are received.
* Stackdriver alert, which consists of the following:
    * Alerting policy watching metrics related to a subscription associated with the data ingest topic
    * Webhook notification channel that points to a Cloud Function
* Cloud Pub/Sub topic, which durably records the alert incident relaying it to the Archiver function
* Archiver function, which uses streaming pull with Cloud Pub/Sub and streaming write to Cloud Storage to
  efficiently batch and move event data from Cloud Pub/Sub to Cloud Storage.

## Before you begin

1.  Create a GCP project for this tutorial to allow for easier cleanup.
1.  Create a new [Stackdriver workspace](https://cloud.google.com/monitoring/workspaces/guide) in the
    GCP project that you created above.
1.  Enable Cloud Functions:

        gcloud services enable cloudfunctions.googleapis.com

## Setting up the automation

Commands in this tutorial assume that you are running from the tutorial folder:

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community/tutorials/cloud-pubsub-drainer/

### Install components

You will use the new command-line interface for Stackdriver resources, which is provided by the `gcloud` `alpha` component:

    gcloud components install alpha

### Set environment variables

These environment variables are used throughout the project:

    export FULL_PROJECT=$(gcloud config list project --format "value(core.project)")
    export PROJECT_ID="$(echo $FULL_PROJECT | cut -f2 -d ':')"

### Create a data archive bucket

This is the bucket into which we archive data from Cloud Pub/Sub:

    gsutil mb gs://$PROJECT_ID-data-archive

### Create Cloud Pub/Sub resources

    gcloud pubsub topics create demo-data
    gcloud pubsub subscriptions create bulk-drainer --topic demo-data
    gcloud pubsub topics create drain-tasks

The `demo-data` topic is the main topic where data is sent that we want to archive. It may have several subscriptions to
it that react to events or process streaming data. In Cloud Pub/Sub, each subscription gets its own durable copy of the 
data.

The `bulk-drainer` subscription is created to act as the storage buffer dedicated to the archiver task.

The `drain-tasks` topic serves as a durable relay of the Stackdriver alert occurrence.

### Deploy the archiving function

The `Archiver` function is awakened by a Stackdriver condition-based alert and drains any outstanding events in
the `bulk-drainer` subscription into chunked objects in the `data-archive` bucket.

    cd drainer-func
    gcloud functions deploy Archiver \
        --runtime go111 \
        --trigger-topic drain-tasks \
        --update-env-vars BUCKET_NAME=$PROJECT_ID-data-archive,SUBSCRIPTION_NAME=bulk-drainer,AUTH_TOKEN=abcd

How much is consolidated per object is configured in the code; it can be set to a number of messages or a number of bytes.

### Deploy webhook relay

Stackdriver does not currently have a native Cloud Pub/Sub alert notification channel. We use a small HTTP Cloud Function
to act as a simple relay. The `AUTH_TOKEN` environment variable sets an expected shared secret between the Stackdriver 
Notification Channel and the webhook.

    gcloud functions deploy StackDriverRelay --runtime go111 --trigger-http --update-env-vars AUTH_TOKEN=abcd

### Allow Stackdriver to call the webhook

*[Cloud Function IAM Alpha](http://bit.ly/gcf-iam-alpha) Users Only* 

Stackdriver can only reach publicly accesible webhooks. If you are using a project with function authorization enabled,
you need to make it reachable:

    gcloud alpha functions add-iam-policy-binding StackDriverRelay --member "allUsers" --role "roles/cloudfunctions.invoker"

### Create Stackdriver notification channel

In Stackdriver, a notification channel is a resource that can be used with one or more alerting policies. These can be 
created in the GCP Console or through an API. Using the URL from our deployed function, you create a new channel and then
get the Stackdriver-assigned channel identifier as an environment variable:

    cd ..
    export URL=$(gcloud functions describe StackDriverRelay --format='value(httpsTrigger.url)')

    gcloud alpha monitoring channels create --channel-content-from-file channel.json --channel-labels url=$URL?token=abcd

    export CHANNEL=$(gcloud alpha monitoring channels list --filter='displayName="Archiver"' --format='value("name")')

### Create a Stackdriver alerting policy

Alerting policies describe conditions that result in the alert firing as true. This is where we want to create an alert 
condition if messages in our `bulk-drainer` Cloud Pub/Sub subscription get either too numerous or too old. See the 
contents of `policy.json` in the tutorial repository for details. The duration and size thresholds are set low so that the 
solution can be tested and demonstrated quickly.

After the policy is created, the ID is retrieved and then it is updated with to use the Notification Channel created 
earlier.

    gcloud alpha monitoring policies create --policy-from-file=policy.json

    export POLICY=$(gcloud alpha monitoring policies list --filter='displayName="archive-pubsub"' --format='value("name")')

    gcloud alpha monitoring policies update $POLICY --add-notification-channels=$CHANNEL

At this point, the solution is fully deployed. You can see and review the policy in the alerting section of Stackdriver 
Console. You can see notification channels in the workspace settings area of the Stackdriver console.

## Testing the solution

### Create test data

The loader script creates some synthetic test data

    cd ../loader
    go get
    # note you may see a warning about gopath if you are in Cloud Shell
    go run main.go
    
You should see output that looks like:

    bulking out
    done bulking out
    2019/03/05 16:55:33 Published Batch
    2019/03/05 16:55:34 Published Batch
    2019/03/05 16:55:35 Published Batch
    2019/03/05 16:55:36 Published Batch
    2019/03/05 16:55:37 Published Batch
    2019/03/05 16:55:38 Published Batch
    2019/03/05 16:55:39 Published Batch
    2019/03/05 16:55:40 Published Batch
    2019/03/05 16:55:41 Published Batch
    2019/03/05 16:55:42 Published Batch

To test the age-based condition in the policy, let the loader run just for a moment, cancel by pressing Ctrl-C, and then
wait a few minutes until the condition is triggered.

![Stackdriver alerting policy](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/stackdriver_alerting_policy.png)

For a trigger based on backlog size, let the loader tool run for several minutes before canceling. (Note: Do not let this
script run indefinitely, since it will continue to generate billable volumes of data.)

Note that Stackdriver metrics do not appear instantaneously; it takes some time for them to show in the alert policy charts. 
Also note that for the condition to fire, it has to be true for 1 minute (this is a configurable part of policy).

While you wait for an alert to fire, you can to check out
the [Stackdriver alerting policy overview](https://cloud.google.com/monitoring/alerts/).

### Check the function logs

The `Relay` function logs should show that the function was called.

![Stackdriver relay function logs](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/stackdriver_relay_function_logs.png)

The `Archiver` function logs should show the archiving activity, including how many messages were archived.

![Stackdriver archiver function logs](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/stackdriver_archiver_function_logs.png)

### Check the archive bucket

If you look in the data archive bucket in the Cloud Console [storage browser](https://console.cloud.google.com/storage)
you will see a set of nested folders by year/month/day and then named for the time the archive event occurred.

The size archive size is set to 1MB in this tutorial, though that is adjustable in the function code.

![storage export](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/cloud_storage_export.png)

## Limits of the pattern

This pattern is not appropriate for all cases. Notably, function invocations are limited to 10 minutes. This means that the
alert policy should trigger often enough that the archive task completes within this timeframe.

If the data volume into Cloud Pub/Sub is too much to be archived by such a periodic task, it is better handled by a proper [streaming Dataflow job](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates#cloudpubsubtogcstext).

## Cleaning up and next steps

    gcloud functions delete Archiver
    gcloud functions delete StackDriverRelay
    gcloud pubsub subscriptions delete bulk-drainer --topic demo-data
    gcloud pubsub topics delete drain-tasks
    gcloud pubsub topics delete demo-data

You can choose to delete the Stackdriver notifications and alert policy in the Stackdriver console.

### Next steps

There are several ways to extend this pattern:

* Add scheduled run of the archiver using [Cloud Scheduler](https://cloud.google.com/scheduler/) as an extra backstop.
* Add conversion and compression (e.g., using Avro) to the data as you write it to Cloud Storage.
* Add nightly [load of all archived files into BigQuery](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage).
