---
title: Tutorial - Fresh and Accurate: Aggregating Streams in ELT
description: In this blog, we discuss a few of the most common challenges that data engineers face when solving for these use cases. We outline some design ideas and architectural patterns for efficient aggregation of streaming data using BigQuery.
author: slachterman, vincegonzalez
tags: BigQuery, ELT, dataform, workflow, streaming
date_published: 2020-04-01
---

# Fresh and Accurate: Aggregating Streams in ELT

- [Fresh and Accurate: Aggregating Streams in ELT](#fresh-and-accurate-aggregating-streams-in-elt)
- [Introduction](#introduction)
   - [Overview](#overview)
   - [Data freshness and accuracy ](#data-freshness-and-accuracy-)
   - [Scenario Description](#scenario-description)
- [Design](#design)
   - [Data Tiering](#data-tiering)
   - [Partitioning](#partitioning)
- [Architecture](#architecture)
   - [What you'll build](#what-you'll-build)
   - [Scheduling and Orchestration](#scheduling-and-orchestration)
   - [What you'll need](#what-you'll-need)
- [Getting set up](#getting-set-up)
   - [Create BigQuery Dataset and Table for Raw Tier](#create-bigquery-dataset-and-table-for-raw-tier)
   - [Create Pub/Sub Topic and Subscription](#create-pubsub-topic-and-subscription)
   - [Create Dataform Account and Project](#create-dataform-account-and-project)
- [Implementation](#implementation)
   - [Create Python Service for reading and publishing Events to Pub/Sub](#create-python-service-for-reading-and-publishing-events-to-pubsub)
- [Implementation, continued](#implementation-continued)
   - [Create Dataflow Job from Template to read from Pub/Sub and write to BigQuery](#create-dataflow-job-from-template-to-read-from-pubsub-and-write-to-bigquery)
- [Implementation, Dataform Steps](#implementation-dataform-steps)
   - [Model Tables in Dataform](#model-tables-in-dataform)
   - [Schedule Dataform Project](#schedule-dataform-project)
- [Congratulations](#congratulations)
   - [What's next?](#what's-next)
      - [Further reading](#further-reading)

---

# Introduction

## Overview

Frameworks for streaming analytics have become increasingly important in contemporary data warehousing, as business users' demand for real-time analytics continues unabated. Big strides have been made to improve data freshness inside warehouses and to support streaming analytics generally, but data engineers are still faced with challenges when adapting these streaming sources into their data warehouse architecture.

In this blog, we discuss a few of the most common challenges that data engineers face when solving for these use cases. We outline some design ideas and architectural patterns for efficient aggregation of streaming data using BigQuery.

## Data freshness and accuracy 

By _fresh_, we mean that the data latency of the aggregate is less than some threshold, e.g., "up to date as of the last hour". Freshness is determined by the subset of raw data that is included in the aggregates.

When dealing with streaming data, it is very common for events to arrive late within our data processing system, meaning that the time at which _our system_ processes an event is significantly later than the time at which the event occurs.

When we process the late-arriving facts, the values of our aggregated statistics will change, meaning that on an intra-day basis, the values that analysts see will change. By _accurate_, we mean that the aggregated statistics are as close as possible to the ultimate, reconciled values.

There is a third dimension to optimize, of course: cost--in the sense of both dollars and performance. To illustrate, we could make use of a logical view for the data objects in Staging and Reporting. The downside of using a logical view would be that every time the aggregated table is queried, the entire raw dataset is being scanned, which will be slow and expensive.

## Scenario Description

Let's set the stage for this use case. We are going to ingest Wikipedia Event Streams data that is published by Wikimedia. Our goal is to build a leaderboard that will show the authors with the most changes, and that will be up-to-date as new articles are published. Our leaderboard, which will be implemented as a BI Engine dashboard, will aggregate the raw events by username to compute the scores.

# Design

## Data Tiering

In the data pipeline, we will define multiple tiers of data. We will hold onto the raw event data, and build a pipeline of subsequent transformations, enrichment, and aggregation. We don't connect Reporting tables directly to the data held in Raw tables, because we want to unify and centralize the transformations that different teams care about for the staged data.

An important principle in this architecture is that higher tiers--Staging and Reporting--can be recalculated at any time using only the raw data.

## Partitioning

BigQuery supports two styles of partitioning; integer range partitioning and date partitioning. We'll consider only date partitioning in scope for this post.

For date partitioning, we can choose between ingestion time partitions or field based partitions. Ingestion time partitioning lands data in a partition based on when the data was acquired. Users can also select a partition at load time by specifying a partition decorator.

Field partitioning partitions data based on the date or timestamp value in a column. 

For ingestion of events, we'll land data into an ingestion time partitioned table. This is because ingestion time is relevant for processing or re-processing data received in the past. Backfills of historical data can be stored within ingestion time partitions as well, based on when they would have arrived.

In this Codelab, we will assume that we will not receive late-arriving facts from the Wikimedia event stream. This will simplify the incremental loading of the staging table, as discussed below.

For the staging table, we will partition by event time. This is because our analysts are interested in querying data based on the time of the event--the time the article was published on Wikipedia--and not the time at which the event was processed within the pipeline.

# Architecture

## What you'll build

In order to read the event stream from Wikimedia, we'll use the [SSE](https://en.wikipedia.org/wiki/Server-sent_events) protocol. We'll write a small middleware service that will read from [the event stream](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams) as an SSE client and will publish to a Pub/Sub topic within our GCP environment.

Once the events are available in Pub/Sub, we will create a Cloud Dataflow job, using a template, that will stream the records into our Raw data tier in our BigQuery data warehouse. The next step is to compute the aggregated statistics to support our live leaderboard. 

![image](https://drive.google.com/a/google.com/file/d/1p0NDblJakwKwEKGffT98CLGJE-pQ0JYy/view?usp=drivesdk)

## Scheduling and Orchestration

For orchestrating the ELT that populates the Staging and Reporting tiers of the warehouse, we will make use of [Dataform](https://dataform.co/). Dataform "brings tooling, best practices, and software engineering-inspired workflows" to data engineering teams. In addition to orchestration and scheduling, Dataform provides functionality like Assertions and Tests for ensuring quality, defining custom warehouse Operations for database management, and Documentation features to support data discovery.

The authors thank the Dataform team for their valuable feedback in reviewing this lab and blog.

Within Dataform, the Raw data streamed in from Dataflow will be declared as an external data set. The Staging and Reporting tables will be defined dynamically, using Dataform's SQLX syntax.

We will make use of Dataform's incremental loading feature to populate the staging table, scheduling the Dataform project to run every hour. Per the above, we'll assume that we will not receive late-arriving facts, so our logic will be to ingest records that have an event time that is later than the most recent event time among the existing staged records.

In later labs in this series, we will discuss the handling of late-arriving facts.

When we run the entire project, the upstream data tiers will have all the new records added, and our aggregations will be re-computed. In particular, each run will result in a full refresh of the aggregated table. Our physical design will include clustering the staging table by _username_, further increasing the performance of the aggregation query that will fully refresh this leaderboard.

## What you'll need

-  A recent version of Chrome
-  Basic knowledge of SQL and basic familiarity with BigQuery

---

# Getting set up

## Create BigQuery Dataset and Table for Raw Tier

Create a new dataset to contain our warehouse schema. We will also be using these variables later, so be sure to use the same shell session for the following steps, or set the variables as needed. Be sure to replace <PROJECT_ID> with your project's ID.

<table>
<thead>
<tr>
<th><p><pre>
export PROJECT=<PROJECT_ID>
export DATASET=fresh_streams
<br>
bq --project $PROJECT mk $DATASET
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Next, we'll create a table that will hold the raw events using the GCP Console. The schema will match the fields that we project from the event stream of published changes we are consuming from Wikimedia.

## Create Pub/Sub Topic and Subscription

<table>
<thead>
<tr>
<th><p><pre>
export TOPIC=<TOPIC_ID>
<br>
gcloud pubsub topics create $TOPIC
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## Create Dataform Account and Project

Navigate to [https://app.dataform.co](https://app.dataform.co) and create a new account. Once logged in, you'll create a new project.

Within your project, you'll need to configure the integration with BigQuery. Since Dataform will need to connect to the warehouse, we will need to [provision service account credentials](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating_a_service_account).

Please see [these steps](https://docs.dataform.co/dataform-web/guides/set-up-warehouse) within the Dataform docs. Be sure to select the same projectId that you've created above, then upload the credentials and test the connection.

![image](https://drive.google.com/a/google.com/file/d/1mBFIerceQNfLXQMzfBSIeZ2ec6hodeCj/view?usp=drivesdk)

Once you've configured the BigQuery integration, you'll see Datasets available within the Modeling tab. In particular, the Raw table we use to capture events from Dataflow will be present here. Let's come back to this shortly.

# Implementation

## Create Python Service for reading and publishing Events to Pub/Sub

Please see the Python code below, available within [this gist](https://gist.github.com/slachterman-g/7089b3c08b156f63ac836f22d63c6467) as well. We are following the [Pub/Sub API docs](https://googleapis.dev/python/pubsub/latest/publisher/index.html#publish-a-message) in this example.

Let's take note of the _keys_ list in the code, these are the fields which we are going to project from the full JSON event, persist in the published messages, and ultimately in the wiki_changes table within the Raw tier of our BigQuery dataset.

These match the _wiki_changes_ table schema we defined within our BigQuery dataset for wiki_changes

<table>
<thead>
<tr>
<th><p><pre>
#!/usr/bin/env python3
<br>
import json, time, sys, os
from sseclient import SSEClient as EventSource
<br>
from google.cloud import pubsub_v1
<br>
project_id = os.environ['PROJECT']
topic_name = os.environ['TOPIC']
<br>
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)
<br>
futures = dict()
<br>
url = 'https://stream.wikimedia.org/v2/stream/recentchange'
<br>
keys = ['id', 'timestamp', 'user', 'title']
<br>
for event in EventSource(url):
    if event.event == 'message':
        try:
            change = json.loads(event.data)
            changePub = {k: change.get(k, 0) for k in keys}
        except ValueError:
            pass
        else:
            payloadJson = json.dumps(changePub).encode('utf-8')
            future = publisher.publish(
                   topic_path, data=payloadJson)
            futures[payloadJson] = future
<br>
while futures:
    time.sleep(5)
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# Implementation, continued

## Create Dataflow Job from Template to read from Pub/Sub and write to BigQuery

Once the recent change events have been published to the Pub/Sub topic, we can make use of a Cloud Dataflow job to read these events and write them to BigQuery.

If we had sophisticated needs while processing the stream--think joining disparate streams, building windowed aggregations, using lookups to enrich data--then we could implement them in our Apache Beam code.

Since our needs are more straightforward for this use case, we can use the out-of-the-box Dataflow template and we won't have to make any customizations to it. We can do this directly from the GCP Console in Cloud Dataflow.

![image](https://drive.google.com/a/google.com/file/d/1-i5_3TsHkmHGMsQvZAAz4U-Va29hRhOy/view?usp=drivesdk)

We'll use the Pub/Sub Topic to BigQuery template, and then we just need to configure a few things: the 

![image](https://drive.google.com/a/google.com/file/d/118xfCsg3bw0ZH5FAqeXdPBGp9lbO1rqE/view?usp=drivesdk)

# Implementation, Dataform Steps

## Model Tables in Dataform

Our Dataform model is tied to the following GitHub [repository](https://github.com/slachterman-g/wikidev-dataform)--the definitions folder contains the SQLX files that define the data model.

As discussed in the [Scheduling and Orchestration section](#heading=h.yjpfrbzhqq3z), we'll define a staging table in Dataform that aggregates the raw records from _wiki_changes_. Let's take a look at the DDL for the staging table (also linked in the [GitHub repo](https://github.com/slachterman-g/wikidev-dataform/blob/master/definitions/wiki_staged.sqlx) tied to our Dataform project).

Let's note a few important features of this table:

-  It is configured as an incremental type, so when our scheduled ELT jobs run, only new records will be added
   -  As expressed by the when() code at the bottom, the logic for this is based on the timestamp field, which reflects the timestamp in the event stream, i.e., the event_time of the change

-  It is clustered using the _user_ field, which means that the records within each partition will be ordered by _user_, reducing the shuffle required by the query that builds the leaderboard

<table>
<thead>
<tr>
<th><p><pre>
config {
  type: "incremental",
  schema: "wiki_push",
  bigquery: {
    partitionBy: "date(event_time)",
    clusterBy: ["user"]
  }
}
<br>
select
  user,
  title,
  timestamp as event_time,
  current_timestamp() as processed_time
from
  wiki_push.wiki_changes
<br>
${ when(incremental(), `WHERE timestamp > (SELECT MAX(timestamp) FROM ${self()})`) }
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

The other table we need to define in our project is the Reporting tier table, which will support the leaderboard queries. Tables in the Reporting tier are aggregated, as our users are concerned with fresh and accurate counts of published Wikipedia changes.

The [table definition](https://github.com/slachterman-g/wikidev-dataform/blob/master/definitions/wiki_agg.sqlx) is straightforward, and makes use of Dataform [references](https://docs.dataform.co/guides/datasets#referencing-other-datasets). A big advantage of these references it that they make explicit the dependencies between objects, supporting pipeline correctness by assuring that dependencies are always executed _before_ dependent queries.

<table>
<thead>
<tr>
<th><p><pre>
config {
  type: "table",
  schema: "wiki_push"
}
<br>
select
  user,
  count(*) as changesCount
from
${ref("wiki_staged")}
group by user
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## Schedule Dataform Project

The final step is simply to create a schedule that will execute on an hourly basis. When our project is invoked, Dataform will execute the required SQL statements to refresh the incremental staging table, and to reload the aggregated table.

This Schedule can be invoked every hour--or even more frequently, up to roughly every 5-10 minutes--to keep the leaderboard updated with the recent events that have streamed into the system. 

![image](https://drive.google.com/a/google.com/file/d/1vVTcUHMqTpW7OkCrQMHd5k7R_qSGM5GO/view?usp=drivesdk)

# Congratulations

Congratulations, you've successfully built a tiered data architecture for your streamed data!

We started with a Wikimedia event stream and we've transformed this to a Reporting table in BigQuery which is consistently up-to-date.

![image](https://drive.google.com/a/google.com/file/d/1VAuef1LeX_v7bOwugRHft7gEekl2p5-k/view?usp=drivesdk)

## What's next?

### Further reading

-  [Introducing Dataform](https://dataform.co/blog/introducing-dataform)
-  [Functional Data Engineering — a modern paradigm for batch data processing](https://medium.com/@maximebeauchemin/functional-data-engineering-a-modern-paradigm-for-batch-data-processing-2327ec32c42a)
-  [How to aggregate data for BigQuery using Apache Airflow](https://cloud.google.com/blog/products/gcp/how-to-aggregate-data-for-bigquery-using-apache-airflow)
