---
title: Deduplicate Pub/Sub Messages Using Dataflow in A Spring Application
description: Use Dataflow's PubsubIO to deduplicate Pub/Sub messages in a Spring application
author: anguillanneuf
tags: Cloud Pub/Sub, Spring, Spring Cloud GCP, Cloud Dataflow, Java
date_published: 2020-02-29
---


Tianzi Cai | Developer Programs Engineer | Google Cloud


## Architecture

## Objectives
- Configure a Spring application to use [Cloud Pub/Sub] as the messaging middleware.
- Use [Cloud Dataflow] to deduplicate messages

## Before You Begin

## Bind Cloud Pub/Sub to Your Spring Application

## Start a Dataflow Job to Deduplicate Pub/Sub Messages

```shell script
 mvn compile exec:java \
   -Dexec.mainClass=com.example.DedupPubSub \
   -Dexec.cleanupDaemonThreads=false \
   -Dexec.args="\
     --project=$PROJECT_NAME \
     --inputTopic=projects/$PROJECT_NAME/topics/topicFirst \
     --outputTopic=projects/$PROJECT_NAME/topics/topicSecond \
     --idAttribute=key \
     --runner=DataflowRunner"
```

## Cleanup

## Next Steps

[Cloud Pub/Sub]: https://cloud.google.com/pubsub/docs/
[Cloud Dataflow]: https://cloud.google.com/dataflow/docs/