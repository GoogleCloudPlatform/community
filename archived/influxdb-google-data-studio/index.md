---
title: Access time series data in InfluxDB Cloud with Google Data Studio
description: Quickly deploy a comprehensive dashboard using Data Studio and your time series data.
author: gunnaraasen
tags: time series, data, visualization, monitoring, Google Cloud, Data Studio
date_published: 2020-12-08
---

Gunnar Aasen | Product Manager | InfluxData

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Google Data Studio is an interactive dashboard tool that turns any internet-accessible data source into informative dashboards that are easy to build and share, 
which help you to derive powerful insights from your data.

The easy-to-use user interface makes it possible for anyone with the curiosity to drill down into their live datasets and build dashboard and
reports with interactive controls such as data selectors, column sorts, and page-level filters. It also has support for calculated metrics and calculated fields.
The [InfluxData platform](https://docs.influxdata.com/influxdb/v2.0/) comes with a Data Studio connector that allows users to query time series data from their 
InfluxDB instance to build these Data Studio dashboards. In this tutorial, you use Data Studio to visualize monitoring metrics stored in InfluxDB Cloud.

The same general steps in this tutorial can be used for other InfluxDB measurement data being collected. Simply replace the references to `diskio-usage` and 
`diskio` with the bucket name and measurement name to connect to Data Studio.

![Data Studio dashboard showing COVID-19 data](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-data-studio/COVID-19-Data-Studio-Dashboard-powered-by-InfluxDB.png)

## Objectives

* Connect Data Studio to your InfluxDB Cloud instance.
* Configure a downsampling task to aggregate metric data.
* Create comprehensive dashboards using Data Studio and your time series data.

## Costs

This tutorial does not incur any costs on InfluxDB Cloud if you use a Free-tier account.

This tutorial explains how to monitor existing Google Cloud resources but does not require any new resources on Google Cloud.

## Before you begin

This tutorial assumes that you have Data Studio, an existing InfluxDB Cloud account, and Telegraf enabled to collect disk usage data.

* Get free access to [Data Studio](https://datastudio.google.com/overview).
* Create a [new InfluxDB Cloud account for free](https://cloud2.influxdata.com/signup).
* Install and configure the [Telegraf metrics collection agent](https://docs.influxdata.com/influxdb/v2.0/write-data/no-code/use-telegraf/) to collect monitoring
  metrics from a local system.

We recommend following the tutorial on
[Monitoring Google Cloud with InfluxDB templates](https://cloud.google.com/community/tutorials/influxdb-google-cloud-monitoring-templates) to set up an InfluxDB 
Cloud account and configure it to monitor your Google Cloud resources.

## Configure InfluxDB Cloud

1.  [Log in to your InfluxDB Cloud account](https://cloud2.influxdata.com/signup).
1.  Create two buckets, named `diskio-usage` and `diskio-usage-1h`.

    You can also rename an existing bucket or, if you would like to use different bucket names, substitute the `diskio-usage` and `diskio-usage-1h` bucket names
    throughout this tutorial.

1.  Generate a new security token to be used in your Data Studio setup: In your InfluxDB Cloud instance, select
    **Load Data > Tokens > Generate Read/Write Token**.
    
    The new token only requires read permissions on the bucket where your disk usage data is stored.

## Configure an InfluxDB task to downsample source data

We recommend using aggregated source data to avoid performance issues in the Data Studio UI.

The steps in this section show how to define a new task to downsample the disk usage metrics into a new bucket.

InfluxDB uses the [Flux functional data scripting language](https://docs.influxdata.com/influxdb/v2.0/process-data/common-tasks/downsample-data/) to create data
aggregation tasks.

1.  In your InfluxDB Cloud instance, select **Task > Create Task**.

1.  Copy the example Flux script below to create a new task for downsampling disk I/O metrics into 1-hour windows:

        // option task = {name: "diskio-usage-1h", every: 1h}
        data = from(bucket: "diskio-usage")
          |> range(start: -duration(v: int(v: task.every) * 24))
          |> filter(fn: (r) => (r["_measurement"] == "diskio"))
          |> filter(fn: (r) => (r["_field"] == "write_bytes" or r._field == "read_bytes" or r._field == "io_time" or r._field == "iops_in_progress"))

        data
          |> aggregateWindow(fn: sum, every: 1h)
          |> to(bucket: "diskio-usage-1h")

1.  Add the following settings to the task definition:

    * `Name = diskio-usage-1h`
    * `Schedule Task {Every} = 1h`
    
1. Save the task, and wait for the task status to update to verify that it's running and aggregating data.

When the aggregated time series data is available, you can use it in your Data Studio project.

## Connect InfluxDB Cloud to Data Studio

1.  [Authorize the Data Studio InfluxDB Community Connector](https://datastudio.google.com/u/0/datasources/create?connectorId=AKfycbwhJChhmMypQvNlihgRJMAhCb8gaM3ii9oUNWlW_Cp2PbJSfqeHfPyjNVp15iy9ltCs) data source to enable a direct connection from Data Studio to InfluxDB 
    Cloud.

1.  After authorizing the connector, enter the following connection details in the Data Studio data source wizard to connect with InfluxDB Cloud:

    * InfluxDB Cloud URL for your region, such as `https://us-central1-1.gcp.cloud2.influxdata.com`
    * Token created in the "Configure InfluxDB Cloud" section
    * [Organization name](https://docs.influxdata.com/influxdb/v2.0/organizations/view-orgs/)
    * Bucket name: `diskio-usage` or `diskio-usage-1h` depending on whether downsampling was configured
    * Measurement name: `diskio`

1.  Click **Connect** to continue.

    After you complete the authorization, you see a list of fields available from your measurement, including all tags, fields, and timestamps.

    ![InfluxDB field list](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-data-studio/Google-Data-Studio_InfluxDB-Field-List.png)

1.  Click **Create report** in Data Studio to start building your charts.

## Results

The Data Studio project can use InfluxDB Cloud as a data source for charts. Time series data stored in InfluxDB Cloud can be efficiently queried and combined 
with other data.

The task created in InfluxDB aggregates data every hour. Querying the aggregated hourly data creates even faster Data Studio reports, especially for longer time
ranges.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the Data Studio InfluxDB Community Connector and 
remove the task from InfluxDB Cloud.

### Delete the Data Studio InfluxDB Community Connector

1.  Navigate to the [Data Studio data sources page](https://datastudio.google.com/#/navigation/datasources).
1.  In the upper right corner of the the Data Studio InfluxDB Community Connector's card, click **More**.
1.  Click **Revoke access**.

### Delete the InfluxDB Cloud task

1. Follow the instructions to [delete the task](https://docs.influxdata.com/influxdb/cloud/process-data/manage-tasks/delete-task/) named `diskio-usage-1h`.

## What's next  

* View the [InfluxDB template gallery](https://www.influxdata.com/products/influxdb-templates/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)  
* Learn more about [Google and InfluxDB](https://www.influxdata.com/partners/google/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
* Learn more about integrating [InfluxDB with Data Studio](https://www.influxdata.com/integration/data-studio/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
