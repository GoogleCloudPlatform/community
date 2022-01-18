---
title: Ingest data from Google Earth Engine to BigQuery
description: Use Cloud Dataflow and GeoBeam to ingest raster image data(TIFF files) from Google Earth Engine to BigQuery. 
author: kannappans
tags: Dataflow, Google Earth Engine, GeoBeam, BigQuery
date_published: 2019-03-15
---

Kannappan Sirchabesan | Cloud Data Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Google Earth Engine is a geospatial processing platform powered by Google Cloud that combines a multi-petabyte catalog of satellite imagery and geospatial datasets with planetary-scale analysis capabilities. Earth Engine is used for analyzing forest and water coverage, land use change, assessing the health of agricultural fields, etc.

[GeoBeam](https://github.com/GoogleCloudPlatform/dataflow-geobeam) is a framework that provides a set of Apache Beam classes and utilities that make it easier to process and transform massive amounts of Geospatial data using Google Cloud Dataflow. 

This solution uses GeoBeam to ingest Raster TIFF images generated in Google Earth Engine into BigQuery. 

## Objectives

* Import a Google Earth Engine TIFF image to a GCS bucket.
* Install the python library GeoBeam.
* Run a GeoBeam job to ingest the TIFF file from GCS bucket to BigQuery.
* Use BigQuery GeoViz to verify that the TIFF image has been ingested correctly.

## Architecture

![architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/architecture.png)

There are several components to the architecture:

* Data ingest Pub/Sub topic: This is where events of interest are received.
* Cloud Monitoring alert, which consists of the following:
    * Alerting policy watching metrics related to a subscription associated with the data ingest topic
    * Webhook notification channel that points to a Cloud Function
* Pub/Sub topic, which durably records the alert incident relaying it to the Archiver function
* Archiver function, which uses streaming pull with Pub/Sub and streaming write to Cloud Storage to
  efficiently batch and move event data from Pub/Sub to Cloud Storage.

## Before you begin

1.  Create a Google Cloud project for this tutorial to allow for easier cleanup.
1.  Create a new [workspace](https://cloud.google.com/monitoring/workspaces/guide) in the
    Google Cloud project that you created above.
1.  Enable Cloud Functions:

        gcloud services enable cloudfunctions.googleapis.com

## Setting up the automation

Commands in this tutorial assume that you are running from the tutorial folder:

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community/tutorials/cloud-pubsub-drainer/

### Install components

You will use the command-line interface for Cloud Monitoring resources, which is provided by the `gcloud` `alpha` component:

    gcloud components install alpha

### Set environment variables

These environment variables are used throughout the project:

    export FULL_PROJECT=$(gcloud config list project --format "value(core.project)")
    export PROJECT_ID="$(echo $FULL_PROJECT | cut -f2 -d ':')"

### Create a data archive bucket

This is the bucket into which we archive data from Pub/Sub:

    gsutil mb gs://$PROJECT_ID-data-archive

### Create Pub/Sub resources

    gcloud pubsub topics create demo-data
    gcloud pubsub subscriptions create bulk-drainer --topic demo-data
    gcloud pubsub topics create drain-tasks

The `demo-data` topic is the main topic where data is sent that we want to archive. It may have several subscriptions to
it that react to events or process streaming data. In Pub/Sub, each subscription gets its own durable copy of the 
data.

The `bulk-drainer` subscription is created to act as the storage buffer dedicated to the archiver task.

The `drain-tasks` topic serves as a durable relay of the alert occurrence.

### Deploy the archiving function

The `Archiver` function is awakened by a condition-based alert and drains any outstanding events in
the `bulk-drainer` subscription into chunked objects in the `data-archive` bucket.

    cd drainer-func
    gcloud functions deploy Archiver \
        --runtime go111 \
        --trigger-topic drain-tasks \
        --update-env-vars BUCKET_NAME=$PROJECT_ID-data-archive,SUBSCRIPTION_NAME=bulk-drainer,AUTH_TOKEN=abcd

How much is consolidated per object is configured in the code; it can be set to a number of messages or a number of bytes.

### Deploy webhook relay

Cloud Monitoring does not currently have a native Pub/Sub alert notification channel. We use a small HTTP Cloud Function
to act as a simple relay. The `AUTH_TOKEN` environment variable sets an expected shared secret between the Cloud Monitoring 
notification channel and the webhook.

    gcloud functions deploy StackDriverRelay --runtime go111 --trigger-http --update-env-vars AUTH_TOKEN=abcd

### Allow Cloud Monitoring to call the webhook

*[Cloud Function IAM Alpha](http://bit.ly/gcf-iam-alpha) Users Only* 

Cloud Monitoring can only reach publicly accesible webhooks. If you are using a project with function authorization enabled,
you need to make it reachable:

    gcloud alpha functions add-iam-policy-binding StackDriverRelay --member "allUsers" --role "roles/cloudfunctions.invoker"

### Create a Cloud Monitoring notification channel

In Cloud Monitoring, a notification channel is a resource that can be used with one or more alerting policies. These can be 
created in the Cloud Console or through an API. Using the URL from our deployed function, you create a new channel and then
get the channel identifier as an environment variable:

    cd ..
    export URL=$(gcloud functions describe StackDriverRelay --format='value(httpsTrigger.url)')

    gcloud alpha monitoring channels create --channel-content-from-file channel.json --channel-labels url=$URL?token=abcd

    export CHANNEL=$(gcloud alpha monitoring channels list --filter='displayName="Archiver"' --format='value("name")')

### Download Earth Engine Image

Export the Earth Engine Image as a TIF file to the bucket created in GCS.  

Wait for a couple of minutes for the export to complete.  

    image = ee.ImageCollection("COPERNICUS/S2").first().select(['B4', 'B3', 'B2']);

    task_config = {
      'description': 'copernicus-3',    
      'scale': 30,
      'bucket': 'ee-geobeam-2',
      'fileNamePrefix': 'copernicusExport'
    }

    task = ee.batch.Export.image.toCloudStorage(image, **task_config)
    task.start()


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

![alerting policy](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/stackdriver_alerting_policy.png)

For a trigger based on backlog size, let the loader tool run for several minutes before canceling. (Do not let this
script run indefinitely, since it will continue to generate billable volumes of data.)

Note that Cloud Monitoring metrics do not appear instantaneously; it takes some time for them to show in the alert policy charts. 
Also note that for the condition to fire, it has to be true for 1 minute (this is a configurable part of policy).

While you wait for an alert to fire, you can to check out
the [alerting policy overview](https://cloud.google.com/monitoring/alerts/).

### Check BigQuery Viz

Check BigQuery Viz to see if the images match roughly

![BQ Viz](../image/bqgeoviz.png)

The `Archiver` function logs should show the archiving activity, including how many messages were archived.

![archiver function logs](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/stackdriver_archiver_function_logs.png)

### Check the archive bucket

If you look in the data archive bucket in the Cloud Console [storage browser](https://console.cloud.google.com/storage)
you will see a set of nested folders by year/month/day and then named for the time the archive event occurred.

The size archive size is set to 1MB in this tutorial, though that is adjustable in the function code.

![storage export](https://storage.googleapis.com/gcp-community/tutorials/cloud-pubsub-drainer/cloud_storage_export.png)

## Limits of the pattern

This pattern is not appropriate for all cases. Notably, function invocations are limited to 10 minutes. This means that the
alert policy should trigger often enough that the archive task completes within this timeframe.

If the data volume into Pub/Sub is too much to be archived by such a periodic task, it is better handled by a proper [streaming Dataflow job](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates#cloudpubsubtogcstext).

## Cleaning up and next steps

    gcloud functions delete Archiver
    gcloud functions delete StackDriverRelay
    gcloud pubsub subscriptions delete bulk-drainer --topic demo-data
    gcloud pubsub topics delete drain-tasks
    gcloud pubsub topics delete demo-data

You can choose to delete the notifications and alert policy in the console.

### Next steps

There are several ways to extend this pattern:

* Add scheduled run of the archiver using [Cloud Scheduler](https://cloud.google.com/scheduler/) as an extra backstop.
* Add conversion and compression (e.g., using Avro) to the data as you write it to Cloud Storage.
* Add nightly [load of all archived files into BigQuery](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage).
