---
title: Real time Data Processing With Cloud IoT Core
description: Demonstrate how to build data processing backend for Google Cloud IoT.
author: teppeiy
tags: Cloud IoT Core, Cloud Dataflow, Cloud Functions, Java, Node.js, internet of things
date_published: 2018-04-10
---
## Application Background
The setup described in this tutorial addresses following scenario: At industrial facilities, sensors are installed to monitor the equipment on site. Sensor data is continuously streamed to the cloud. There it is handled by different components for various purposes, such as real-time monitoring and alerts, long-term data storage for analysis, performance improvement, and model training.

Feasible scenarios are:

- Geographically dispersed facilities with centralized monitoring system.
- Monitoring of remote unmanned sites—power transformer stations, mobile base stations, etc.

In this tutorial, the sensors are simulated by a Java application script that continuously generates random measurement points and sends them to the cloud.

This tutorial focuses on two aspect of the monitoring application setup:

- Using [Cloud IoT Core](https://cloud.google.com/iot-core/docs/), a cloud managed service for IoT, to enforce structured handling of sensor devices' security keys and metadata, and secured delivery of measurement data between sensors and cloud.
- In-stream data handling in the cloud, where two parallel processing pipelines separate real-time monitoring and alerting from the less critical need for data storage and analysis.

## Technical Overview

This tutorial demonstrates how to push updates from Message Queueing Telemetry
Transport (MQTT) devices to Google Cloud Platform (GCP) and process them in real
time.

The tutorial includes sample code to show two kinds of data processing
approaches that use GCP products:

1.  A function deployed in [Cloud Functions](https://cloud.google.com/functions/docs/) transforms data and logs it to
    [Stackdriver Logging](https://cloud.google.com/logging/).
1.  A streaming application deployed in [Cloud Dataflow](https://cloud.google.com/dataflow/docs) transforms data and
    inserts it into [BigQuery](https://cloud.google.com/bigquery/docs/).

In both cases, sample temperature data is collected that is generated from
simulated devices. This data is transformed into other data formats, and is passed to
another GCP product for further data processing and analysis. Cloud Functions is
suitable for simple Extract/Transform/Load (ETL) processing, while Cloud
Dataflow can handle more sophisticated data pipelines that involve multiple
transformations, joins, windowing, and so on.

Cloud IoT Core can not only receive data from MQTT clients, but also can send
configuration data to clients. It can be used to control behavior of devices or
the surrounding environment.

## Data structure

The sample MQTT client simulates devices and generates sample data with the
following attributes:

- `DeviceId`: A unique identifier for individual devices.
- `Timestamp`: A timestamp for when a temperature is measured.
- `Temperature`: The measured temperature from the device.
- `Coordinates`: The longitude and latitude of the device.

## Architecture

The sample MQTT client simulates a device and sends sample data to Cloud IoT
Core, which transforms and redirects requests to a [Cloud Pub/Sub](https://cloud.google.com/pubsub/docs) topic. After
the data is stored in Cloud Pub/Sub, it is retrieved by two subscribers: a function
in Cloud Functions and a streaming job running in Cloud Dataflow.

This tutorial shows how data is transformed and processed in Cloud Functions and
Cloud Dataflow.

![Architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/arch.png)

## Objectives

This tutorial demonstrates how to:

- Deploy a function to Cloud Functions that transforms temperature data into
  JSON format and logs it to Stackdriver Logging.
- Deploy a streaming application to Cloud Dataflow that transforms temperature
  data into BigQuery row format and inserts it into BigQuery.
- Run an MQTT client that generates simulated temperature and coordinates, and
  then submits the data to Cloud IoT Core.

## Cost

This tutorial uses billable components of GCP, including:

- BigQuery
- Cloud Dataflow
- Cloud Functions
- Cloud IoT Core
- Cloud Pub/Sub
- [Cloud Storage](https://cloud.google.com/storage/docs/)
- [Compute Engine](https://cloud.google.com/compute/docs/)
- [Cloud Datastore](https://cloud.google.com/datastore/docs/)

You can use the [Pricing Calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate that is based on your projected usage.

## Before you begin

### Install software and download sample code

Make sure you have the following software installed:

- [Git](https://help.github.com/articles/set-up-git/)
- [Java SE 8](http://www.oracle.com/technetwork/java/javase/downloads/index.html)
- [Apache Maven 3.3.x or later](https://maven.apache.org/install.html)

Clone the following repository and change to into the directory for this tutorial's
code:

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd tutorials/cloud-iot-rtdp

`tutorials/cloud-iot-rtdp` contains the following directory structure:

- `bin/`: script files
- `function/`: JavaScript file
- `streaming/`: Java streaming application

### Configure a GCP project and enable APIs

1.  Create or select a GCP project.
1.  Enable billing for your project.
1.  Enable the following APIs:

    1. Cloud IoT Core
    1. Cloud Functions
    1. Cloud Dataflow

### Create a Cloud Storage bucket

1.  Open the [Cloud Storage console](https://console.developers.google.com/storage).
1.  Create a Cloud Storage bucket.

    ![Storage](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_storage.png)

    The bucket name must be unique across Cloud Storage.

1.  Click **Create folder**, enter a temporary folder name, and then click
    **Create**.

    ![folder](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_folder.png)

### Set environment variables

To make it easier to run commands, you can set environment variables so that you
don't have to supply options for some values that you’ll use repeatedly. You
will create the corresponding resources in later steps.

1.  Open [Cloud Shell](https://cloud.google.com/shell/docs/quickstart)
1.  Set the following  environment variables:

    ```sh
    export PROJECT=[PROJECT_ID]
    export REGION=[REGION_NAME]
    export ZONE=[ZONE_NAME]
    export BUCKET=[BUCKET_NAME]
    export REGISTRY=[CLOUD_IOT_CORE_REGISTRY_ID]
    export TOPIC=[CLOUD_PUBSUB_TOPIC_NAME]
    ```

## Configure Cloud IoT Core

In this section, you create a topic in Cloud Pub/Sub and configure Cloud IoT
Core to receive data from MQTT clients.

1.  Open the [Cloud Pub/Sub console](https://console.developers.google.com/cloudpubsub)
1.  In the left navigation menu, click the **Topics** menu.
1.  Click **Create a topic**. In the **Name** box, enter the topic name that you
    assigned earlier to the environment variable, and then click **Create**.

    ![topic](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_topic.png)

1.  Open the [Cloud IoT Core console](https://console.developers.google.com/iot).
1.  Click **Create device registry**.
1.  In the **Registry ID** box, type **myregistry**. Select a GCP region close
    to you, and select the Pub/Sub topic that you just created.

    ![registry](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_registry.png)

1.  When you're done, click **Create**.
1.  In the **Grant permission to service account** dialog box, click **Continue**.
1.  In Cloud Shell, generate a new public/private key pair, which will override
    the checked in pair:

    ```sh
    cd bin
    ./create_cert.sh
    ```

10. In Cloud Shell, register devices in the device registry:

    ```sh
    bin/register.sh
    ```

    Warning: This tutorial includes a public/private key pair for testing
    purposes. Do not use this pair in a production environment.

## Create threshold values in Cloud Datastore
In this section, you insert threshold values for each of the devices, registered in the IoT Core Device Manager, in Cloud Datastore.

1. In Cloud Shell, run a Python script to insert the device objects into Cloud Datastore:

    ```sh
    export GCLOUD_PROJECT=$PROJECT
    virtualenv env && source env/bin/activate
    pip install google-cloud-datastore
    cd bin
    python create_temp_alert_store.py
    deactivate
    ```

1. Open the [Cloud Datastore console](https://console.developers.google.com/datastore).
1. Confirm that the device entities have been created with the corresponding threshold temperature value:

    ![data_store_confirm](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/view_ds.png)

## Deploy a Cloud Function

In this section, you set up a function that logs data that is sent to Cloud IoT
Core and is retrieved through Cloud Pub/Sub. It also compares the temperature
received against the threshold value in Cloud Datastore. If the threshold is
exceeded, an error is logged.

1.  In Cloud Shell, deploy a function to Cloud Functions:

    ```sh
    cd function
    gcloud beta functions deploy iot --stage-bucket $BUCKET --trigger-topic $TOPIC
    ```

    You see results similar to the following:

        / [1 files][  292.0 B/  292.0 B]
        Operation completed over 1 objects/292.0 B.
        Deploying function (may take a while - up to 2 minutes)...done.
        availableMemoryMb: 256
        entryPoint: iot
        eventTrigger:
        ...

1.  Open the [Cloud Functions console](https://console.developers.google.com/functions).
1.  Confirm that you created a function:

    ![function_confirm](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_cf.png)

## Deploy a streaming application to Cloud Dataflow

In this section, you deploy a Java-based streaming application that transforms
data that is retrieved from Cloud Pub/Sub and loads it into a BigQuery table.

1.  In Cloud Shell, build and submit a streaming job:

    ```sh
    cd bin
    ./job.sh
    ```

    The results look similar to the following:

        [INFO] Scanning for projects...
        [INFO]
        [INFO] ------------------------------------------------------------------------
        [INFO] Building cloud-iot-rtdp 0.0.1-SNAPSHOT
        [INFO] ------------------------------------------------------------------------
        [INFO]
        [INFO] --- maven-resources-plugin:2.6:resources (default-resources) @ cloud-iot-rtdp ---
        ...

1.  Open the [Cloud Dataflow console](https://console.developer.google.com/dataflow).
1.  Confirm that a streaming job is running:

    ![stream_confirm](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/create_df.png)

## Generate simulated temperature and coordinates data

Now you can run an MQTT client that generates simulated data on temperature and
coordinates and then submits it to Cloud IoT Core.

1.  In Cloud Shell, run an MQTT client to generate simulated data:

    ```sh
    cd bin
    ./run.sh
    ```

    You see results similar to the following:

        [INFO] Scanning for projects...
        [INFO]
        [INFO] ------------------------------------------------------------------------
        [INFO] Building cloud-iot-rtdp 0.0.1-SNAPSHOT
        [INFO] ------------------------------------------------------------------------
        [INFO]
        [INFO] --- maven-resources-plugin:2.6:resources (default-resources) @ cloud-iot-rtdp ---
        ...

1.  Open the [Cloud Functions console](https://console.developers.google.com/functions).
1.  To confirm that a function is processing data, click the **More options** icon
    on the right side of your function, and then click **View logs**:

    ![view_logs](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/cf_console.png)

    You see results similar to the following:

    ![logs](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/view_logs.png)

1.  Open the [Cloud Dataflow console](https://console.developers.google.com/dataflow).
1.  To confirm that a streaming Cloud Dataflow job is processing data, click the
    job ID:

    ![view_df](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/view_df.png)

1.  Open [BigQuery](https://bigquery.cloud.google.com/).
1.  Click the **Compose Query** button to open the query editor.
1.  To confirm that the temperature data is stored in a BigQuery table, run the
    following query in the editor:

    ```sql
    SELECT count(*) from [[PROJECT_ID]:iotds.temp_sensor]
    ```

    ![bq_editor](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/bq_console.png)

    If everything is working, you should see a single row in the results that
    displays a count of all the records that have been processed.

## Handling alerts

Temperature measurements that are above the configured threshold for each device
are logged as errors by Cloud Functions. You can view and analyse these in the
[Error console](https://console.developers.google.com/errors).

To active the error notifications, follow the documentation on [Error reporting notifications](https://cloud.google.com/error-reporting/docs/notifications).

![error_console](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-rtdp/view_error_report.png)

## Next steps

You can learn more about IoT, data processing, and visualization from
the following links:

- [Overview of IoT Solutions](https://cloud.google.com/solutions/iot/)
- [BigQuery for Data Warehouse Practitioners](https://cloud.google.com/solutions/bigquery-data-warehouse)
- [Visualizing BigQuery Data Using Google Data Studio](https://cloud.google.com/bigquery/docs/visualize-data-studio)
- [Visualizing BigQuery Data Using Google Cloud Datalab](https://cloud.google.com/bigquery/docs/visualize-datalab)
