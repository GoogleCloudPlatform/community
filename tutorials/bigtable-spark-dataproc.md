---
title: Running a Cloud Bigtable Spark job on Dataproc 
description: Run a Spark job on Dataproc that reads from and writes to Cloud Bigtable. 
author: billyjacobson
tags: bigtable, spark, database, big table, apache spark, hbase, dataproc
date_published: 2021-03-19
---

Billy Jacobson | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

## Prerequisites

This is a follow up to [Using Spark with Cloud Bigtable](), so follow the steps in that tutorial before beginning this
one. It walks you through setting up the environment variables, Bigtable instance and table, and running the Spark job
locally.


## Setup

### Create Dataproc Cluster

Set the below environment variables:
```
BIGTABLE_SPARK_DATAPROC_CLUSTER=your-dataproc-cluster
BIGTABLE_SPARK_DATAPROC_REGION=your-dataproc-region
BIGTABLE_SPARK_CLUSTER_ZONE=your-bigtable-cluster-zone
BIGTABLE_SPARK_PROJECT_ID=your-project-id //This can be the same as your Bigtable project 
```
**NOTE**: Read [Available regions and zones](https://cloud.google.com/compute/docs/regions-zones#available) for more information about regions and zones.

Use the `gcloud` command line tool to create a cluster:
```
gcloud dataproc clusters create $BIGTABLE_SPARK_DATAPROC_CLUSTER \
  --region=$BIGTABLE_SPARK_DATAPROC_REGION \
  --zone=$BIGTABLE_SPARK_CLUSTER_ZONE \
  --project=$BIGTABLE_SPARK_PROJECT_ID \
  --image-version=1.4
```

Please note that the examples use Dataproc 1.4.

For the list of available Dataproc image versions visit [Dataproc Image version list](https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-versions).

List the clusters and make sure that `BIGTABLE_SPARK_DATAPROC_CLUSTER` is among them.

```
gcloud dataproc clusters list \
  --region=$BIGTABLE_SPARK_DATAPROC_REGION
```

### Upload File to Cloud Storage

Since you're running the Spark job in the Cloud, you'll need to upload your the file to [Cloud Storage](https://cloud.google.com/storage).

**TIP**: Read [Quickstart: Using the gsutil tool](https://cloud.google.com/storage/docs/quickstart-gsutil) in the official documentation.

1. Create a bucket.

```
gsutil mb \
  -b on \
  -l $BIGTABLE_SPARK_DATAPROC_REGION \
  -p $BIGTABLE_SPARK_PROJECT_ID \
  $BIGTABLE_SPARK_BUCKET_NAME
```

1. Upload an input file into the bucket.

```
gsutil cp src/test/resources/Romeo-and-Juliet-prologue.txt $BIGTABLE_SPARK_BUCKET_NAME
```

1. List contents of the bucket.

```
gsutil ls $BIGTABLE_SPARK_BUCKET_NAME
```
   
Output should be:
```
gs://[your-bucket-name]/Romeo-and-Juliet-prologue.txt


### Configure Environment

Set the additional environment variables:
```
BIGTABLE_SPARK_PROJECT_ID=your-project-id
BIGTABLE_SPARK_INSTANCE_ID=your-instance-id

BIGTABLE_SPARK_WORDCOUNT_TABLE=wordcount
BIGTABLE_SPARK_BUCKET_NAME=gs://[your-bucket-name]
BIGTABLE_SPARK_ASSEMBLY_JAR=target/scala-2.11/bigtable-spark-samples-assembly-0.1.jar
```


### Environment variables
Set the following environment variables, so you can copy/paste the commands in this tutorial:

```bash
SPARK_HOME=/PATH/TO/spark-2.4.7-bin-hadoop2.7
BIGTABLE_SPARK_PROJECT_ID=your-project-id
BIGTABLE_SPARK_INSTANCE_ID=your-instance-id

BIGTABLE_SPARK_WORDCOUNT_TABLE=wordcount
BIGTABLE_SPARK_WORDCOUNT_FILE=src/test/resources/Romeo-and-Juliet-prologue.txt
BIGTABLE_SPARK_ASSEMBLY_JAR=target/scala-2.11/bigtable-spark-samples-assembly-0.1.jar
```

### Submit Wordcount

Submit Wordcount to the Dataproc instance.

```
gcloud dataproc jobs submit spark \
  --cluster=$BIGTABLE_SPARK_DATAPROC_CLUSTER \
  --region=$BIGTABLE_SPARK_DATAPROC_REGION \
  --class=example.Wordcount \
  --jars=$BIGTABLE_SPARK_ASSEMBLY_JAR \
  --properties=spark.jars.packages='org.apache.hbase.connectors.spark:hbase-spark:1.0.0' \
  -- \
  $BIGTABLE_SPARK_PROJECT_ID $BIGTABLE_SPARK_INSTANCE_ID \
  $BIGTABLE_SPARK_WORDCOUNT_TABLE $BIGTABLE_SPARK_BUCKET_NAME/Romeo-and-Juliet-prologue.txt
```

It may take some time to see any progress and may seem to be idle. You may want to use `--verbosity` global option with `debug` to be told about progress earlier.

Eventually, you should see the following messages:

```text
Job [joibId] submitted.
Waiting for job output...
```

### Verify

```
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  -instance=$BIGTABLE_SPARK_INSTANCE_ID \
  read $BIGTABLE_SPARK_WORDCOUNT_TABLE
```

## Cleaning up


Delete the Bigtable instance.

```
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  deleteinstance $BIGTABLE_SPARK_INSTANCE_ID
```

```
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  listinstances
```

Delete the Dataproc cluster.

```
gcloud dataproc clusters delete $BIGTABLE_SPARK_DATAPROC_CLUSTER \
  --region=$BIGTABLE_SPARK_DATAPROC_REGION \
  --project=$BIGTABLE_SPARK_PROJECT_ID
```

```
gcloud dataproc clusters list \
  --region=$BIGTABLE_SPARK_DATAPROC_REGION
```

Remove the input file in the bucket and the bucket itself.

```
gsutil rm $BIGTABLE_SPARK_BUCKET_NAME/Romeo-and-Juliet-prologue.txt
gsutil rb $BIGTABLE_SPARK_BUCKET_NAME
```


## What's next

- Learn more about [Cloud Bigtable](https://cloud.google.com/bigtable/).
- Learn more about [Dataproc](https://cloud.google.com/dataproc).
