---
title: Freshness and accuracy - Aggregating data streams in ELT
description: Describes common challenges that data engineers face when solving for freshness and accuracy. Outlines design ideas and architectural patterns for efficient aggregation of streaming data using BigQuery.
author: slachterman-g,vicenteg
tags: BigQuery, ELT, Dataform, workflow, streaming
date_published: 2020-05-14
---

Sam Lachterman and Vince Gonzalez | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Frameworks for streaming analytics have become increasingly important in contemporary data warehousing, as business users' 
demand for real-time analytics continues unabated. Big strides have been made to improve data freshness inside warehouses 
and to support streaming analytics generally, but data engineers are still faced with challenges when adapting these 
streaming sources into their data warehouse architecture.

This article discusses a few of the most common challenges that data engineers face when solving for these use cases and 
outlines some design ideas and architectural patterns for efficient aggregation of streaming data using BigQuery.

To complete the tutorial portion of this article, you need a recent version of Chrome, a basic knowledge of SQL, and 
basic familiarity with BigQuery.

### Data freshness and accuracy 

By _fresh_, we mean that the data latency of the aggregate is less than some threshold, such as "up to date as of the last
hour". Freshness is determined by the subset of raw data that is included in the aggregates.

When dealing with streaming data, it is very common for events to arrive late to the data processing system, meaning
that the time at which the system processes an event is significantly later than the time at which the event occurs. When 
the system processes the late-arriving facts, the values of the aggregated statistics will change, meaning that on an
intra-day basis, the values that analysts see will change.

By _accurate_, we mean that the aggregated statistics are as close as possible to the ultimate, reconciled values.

A third dimension to optimize is, of course, cost⁠—in both dollars and performance. Consider a logical view for the
data objects in staging and reporting: The downside of using a logical view would be that every time the aggregated table is
queried, the entire raw dataset is scanned, which would be slow and expensive.

### Scenario description

In this tutorial, you ingest Wikipedia event stream data published by Wikimedia. The goal is to build a leaderboard that 
shows the authors with the most changes, which is kept up to date as new articles are published. The leaderboard, which is 
implemented as a BI Engine dashboard, aggregates the raw events by username to compute the scores.

## Design

### Data tiering

The data pipeline defines multiple tiers of data. The system holds onto the raw event data and uses a pipeline of subsequent 
transformations, enrichment, and aggregation. We don't connect reporting tables directly to the data held in raw tables, 
because we want to unify and centralize the transformations that different teams care about for the staged data.

An important principle in this architecture is that higher tiers (staging and reporting) can be recalculated at any time 
using only the raw data.

### Partitioning

BigQuery supports two styles of partitioning: integer range partitioning and date partitioning. This article only considers 
date partitioning.

For date partitioning, you can choose between ingestion-time partitions and field-based partitions. Ingestion-time 
partitioning puts data in a partition based on when the data was acquired. Users can also select a partition at load time by
specifying a partition decorator.

Field partitioning partitions data based on the date or timestamp value in a column. 

For ingestion of events, you'll put data into an ingestion-time partitioned table. This is because ingestion time is 
relevant for processing or re-processing of data received in the past. Backfills of historical data can be stored in
ingestion-time partitions, as well, based on when they would have arrived.

This tutorial assumes that the system will not receive late-arriving facts from the Wikimedia event stream. This 
simplifies the incremental loading of the staging table, as discussed below.

For the staging table, this tutorial partitions by event time because the analysts in this scenario are interested in 
querying data based on the time of the event—the time the article was published on Wikipedia—and not the time at which the
event was processed within the pipeline.

## Architecture

### What you'll build

To read the event stream from Wikimedia, this tutorial uses the [SSE](https://en.wikipedia.org/wiki/Server-sent_events) 
protocol. You use a small middleware service that reads from the
[event stream](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams) as an SSE client and publishes to a 
Pub/Sub topic in your Google Cloud environment.

After the events are available in Pub/Sub, you use a template to create a Cloud Dataflow job that streams the records into
the raw data tier in your BigQuery data warehouse. The next step is to compute the aggregated statistics to support the live
leaderboard. 

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--9g096jwjmg.png)

### Scheduling and orchestration

For orchestrating the ELT that populates the staging and reporting tiers of the warehouse, you use
[Dataform](https://dataform.co/). In addition to orchestration and scheduling, Dataform provides functionality like 
assertions and tests for ensuring quality, defining custom warehouse operations for database management, and documentation 
features to support data discovery.

Within Dataform, the raw data streamed in from Dataflow is declared as an external data set. The staging and reporting 
tables are defined dynamically, using Dataform's SQLX syntax.

This tutorial uses Dataform's incremental loading feature to populate the staging table, scheduling the Dataform project to 
run every hour. Assume that the system will not receive late-arriving facts, so the logic is to ingest records that have 
an event time that is later than the most recent event time among the existing staged records.

When you run the entire project, the upstream data tiers have all of the new records added, and the aggregations is 
re-computed. Each run causes a full refresh of the aggregated table. The design includes clustering the staging table by 
username, further increasing the performance of the aggregation query that fully refreshes this leaderboard.

## Getting set up

### Create a BigQuery dataset and table for the raw tier

Create a new dataset to contain your warehouse schema. You will also be using these variables later, so be sure to use the 
same shell session for the following steps, or set the variables as needed. Replace [YOUR_PROJECT_ID] with your project ID.

    export PROJECT=[YOUR_PROJECT_ID]
    export DATASET=fresh_streams

    bq --project $PROJECT mk $DATASET

Next, you'll create a table that will hold the raw events using the Cloud Console. The schema will match the fields that are 
projected from the event stream of published changes consumed from Wikimedia.

### Create a Pub/Sub topic and subscription

    export TOPIC=[TOPIC_ID]

    gcloud pubsub topics create $TOPIC

### Create a Dataform account and project

Navigate to [https://app.dataform.co](https://app.dataform.co) and create a new account. After you are logged in,
create a new project.

In your project, you need to configure the integration with BigQuery. Because Dataform needs to connect to the 
warehouse, you need to 
[provision service account credentials](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating_a_service_account).

See [these steps](https://docs.dataform.co/dataform-web/guides/set-up-warehouse) in the Dataform documentation. Select the 
same project ID that you created above, and then upload the credentials and test the connection.

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--apnmkrdirlp.png)

After you've configured the BigQuery integration, you'll see datasets in the **Modeling** tab, including 
the raw table that you use to capture events from Dataflow.

## Implementation

### Create a Python service for reading and publishing Events to Pub/Sub

See the Python code below, which is available in
[this gist](https://gist.github.com/slachterman-g/7089b3c08b156f63ac836f22d63c6467). This example follows the
[Pub/Sub API documentation](https://googleapis.dev/python/pubsub/latest/publisher/index.html#publish-a-message).

Note the `keys` list. These are the fields into which values are projected from the full JSON event. These fields are
then made persistent through the published messages and ultimately in the `wiki_changes` table in the raw tier of your
BigQuery dataset. These match the `wiki_changes` table schema defined in the BigQuery dataset for `wiki_changes`.

    #!/usr/bin/env python3

    import json, time, sys, os
    from sseclient import SSEClient as EventSource

    from google.cloud import pubsub_v1

    project_id = os.environ['PROJECT']
    topic_name = os.environ['TOPIC']

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)

    futures = dict()

    url = 'https://stream.wikimedia.org/v2/stream/recentchange'

    keys = ['id', 'timestamp', 'user', 'title']

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

    while futures:
        time.sleep(5)


### Create a Dataflow job from a template to read from Pub/Sub and write to BigQuery

After the recent change events have been published to the Pub/Sub topic, you use a Cloud Dataflow job to read these events 
and write them to BigQuery.

If you have sophisticated needs while processing the stream—for example, joining disparate streams, building windowed 
aggregations, and using lookups to enrich data—then you can implement them in your Apache Beam code. Because the needs for
the current use case are more straightforward, you can use the standard the **Cloud Pub/Sub Topic to BigQuery** Dataflow 
template without any customizations, directly from the Cloud Console in Cloud Dataflow.

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--d34ofwu913f.png)

You just need to configure a few things, as shown below:

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--qemj5i9wrcj.png)

### Model tables in Dataform

The Dataform model for this tutorial is tied to [this GitHubrepository](https://github.com/slachterman-g/wikidev-dataform). 
The definitions folder contains the SQLX files that define the data model.

As discussed in the "Scheduling and orchestration section", you define a staging table in Dataform that aggregates the raw
records from `wiki_changes`. Let's take a look at the DDL for the staging table, which is also linked in the
[GitHub repository](https://github.com/slachterman-g/wikidev-dataform/blob/master/definitions/wiki_staged.sqlx) tied to the 
Dataform project.

    config {
      type: "incremental",
      schema: "wiki_push",
      bigquery: {
        partitionBy: "date(event_time)",
        clusterBy: ["user"]
      }
    }

    select
      user,
      title,
      timestamp as event_time,
      current_timestamp() as processed_time
    from
      wiki_push.wiki_changes

    ${ when(incremental(), `WHERE timestamp > (SELECT MAX(timestamp) FROM ${self()})`) }

Some important features of the staging table:

- It is configured as an incremental type, so that when the scheduled ELT jobs run, only new records are added. As expressed
  by the `when()` code at the bottom, the logic for this is based on the timestamp field, which reflects the timestamp in 
  the event stream (the `event_time` of the change).
- It is clustered using the `user` field, which means that the records within each partition are ordered by `user`, 
  reducing the shuffle required by the query that builds the leaderboard.

The other table that you need to define in your project is the reporting tier table, which supports the leaderboard queries.
Tables in the reporting tier are aggregated, because users are concerned with fresh and accurate counts of published 
Wikipedia changes.

The [table definition](https://github.com/slachterman-g/wikidev-dataform/blob/master/definitions/wiki_agg.sqlx) is
straightforward and makes use of [Dataform references](https://docs.dataform.co/guides/datasets#referencing-other-datasets). 
A big advantage of these references is that they make explicit the dependencies between objects, supporting pipeline 
correctness by assuring that dependencies are always executed _before_ dependent queries.


    config {
      type: "table",
      schema: "wiki_push"
    }

    select
      user,
      count(*) as changesCount
    from
    ${ref("wiki_staged")}
    group by user

### Schedule Dataform project

The final step is to create a schedule that executes hourly. When the project is invoked, Dataform 
executes the required SQL statements to refresh the incremental staging table and reload the aggregated table.

This schedule can be invoked every hour—or even more frequently, up to roughly every 10 minutes—to keep the leaderboard 
updated with the recent events that have streamed into the system. 

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--jh2a3728hgo.png)

## Conclusion

Congratulations! You've successfully built a tiered data architecture for your streamed data.

You started with a Wikimedia event stream and transformed this to a reporting table in BigQuery that is consistently 
up to date.

![image](https://storage.googleapis.com/gcp-community/tutorials/elt-orchestration-dataform/streamingaggre--y154sp1nsco.png)

The authors thank the Dataform team for their valuable feedback in reviewing this article.

## What's next?

### Further reading

-  [Introducing Dataform](https://dataform.co/blog/introducing-dataform)
-  [Functional Data Engineering — a modern paradigm for batch data processing](https://medium.com/@maximebeauchemin/functional-data-engineering-a-modern-paradigm-for-batch-data-processing-2327ec32c42a)
-  [How to aggregate data for BigQuery using Apache Airflow](https://cloud.google.com/blog/products/gcp/how-to-aggregate-data-for-bigquery-using-apache-airflow)
