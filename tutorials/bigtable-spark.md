---
title: Using Spark with Cloud Bigtable 
description: Learn how to use Apache Spark for distributed and parallelized data processing with Cloud Bigtable.
author: billyjacobson
tags: bigtable, spark, database, big table, apache spark, hbase, dataproc
date_published: 2021-03-19
---

Billy Jacobson | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

## Prerequisites

1. [Google Cloud project](https://console.cloud.google.com/)
1. [Google Cloud SDK](https://cloud.google.com/sdk/) installed.
1. [sbt](https://www.scala-sbt.org/) installed.
1. [Apache Spark](https://spark.apache.org/) installed. Download Spark built for Scala 2.11. This sample uses Spark 2.4.7 and Scala 2.11.2.
1. A basic familiarity with [Apache Spark](https://spark.apache.org/) and [Scala](https://www.scala-lang.org/).

## Get the code and assemble the example

```bash
git clone https://github.com/GoogleCloudPlatform/java-docs-samples.git
cd java-docs-samples/bigtable/spark
```
Execute the following `sbt` command to assemble the sample applications as a single uber/fat jar (with all of its dependencies and configuration).

```bash
sbt clean assembly
```

## Setup

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

### Set up Bigtable

#### Instance
You can use an existing instance for this tutorial or create a new one.

Select a [zone](https://cloud.google.com/bigtable/docs/locations) to use and set it as an environment variable.

    BIGTABLE_SPARK_INSTANCE_ZONE=your-zone

Create the instance.

    cbt -project=$BIGTABLE_SPARK_PROJECT_ID createinstance \
     $BIGTABLE_SPARK_INSTANCE_ID "Spark wordcount instance" \
     $BIGTABLE_SPARK_INSTANCE_ID $BIGTABLE_SPARK_INSTANCE_ZONE 1 SSD

#### Table

Create a table called wordcount.

```bash
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  -instance=$BIGTABLE_SPARK_INSTANCE_ID \
  createtable $BIGTABLE_SPARK_WORDCOUNT_TABLE \
  "families=cf"
```

Ensure it was created by running this command and looking for `wordcount`
```bash
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  -instance=$BIGTABLE_SPARK_INSTANCE_ID \
  ls
```

## Run the Wordcount example

Below is the Spark Wordcount job you will be running. Once it has counted the words, it writes a row with the word as
the key with a column count containing the number of occurrences. You can view the [full code on Github](https://github.com/GoogleCloudPlatform/java-docs-samples/blob/master/bigtable/spark/src/main/scala/example/Wordcount.scala). 

[embedmd]:# (https://raw.githubusercontent.com/GoogleCloudPlatform/java-docs-samples/master/bigtable/spark/src/main/scala/example/Wordcount.scala /.*var hConf/ /saveAsNewAPIHadoopDataset\(hConf\)/)
```scala
  var hConf = BigtableConfiguration.configure(projectId, instanceId)
  hConf.set(TableOutputFormat.OUTPUT_TABLE, table)

  import org.apache.hadoop.mapreduce.Job

  val job = Job.getInstance(hConf)
  job.setOutputFormatClass(classOf[TableOutputFormat[ImmutableBytesWritable]])
  hConf = job.getConfiguration

  import org.apache.spark.SparkConf

  val config = new SparkConf()

  // Workaround for a bug in TableOutputFormat
  // See https://stackoverflow.com/a/51959451/1305344
  config.set("spark.hadoop.validateOutputSpecs", "false")

  val sc = SparkContext.getOrCreate(config)
  val wordCounts = sc
    .textFile(file)
    .flatMap(_.split("\\W+"))
    .filter(!_.isEmpty)
    .map { word => (word, 1) }
    .reduceByKey(_ + _)
    .map { case (word, count) =>
      val ColumnFamilyBytes = Bytes.toBytes("cf")
      val ColumnNameBytes = Bytes.toBytes("Count")
      val put = new Put(Bytes.toBytes(word))
        .addColumn(ColumnFamilyBytes, ColumnNameBytes, Bytes.toBytes(count))
      // The KEY is ignored while the output value must be either a Put or a Delete instance
      // The underlying writer ignores keys, only the value matters here.
      (null, put)
    }
  wordCounts.saveAsNewAPIHadoopDataset(hConf)
```

Run the Spark job locally.

```bash
$SPARK_HOME/bin/spark-submit \
  --packages org.apache.hbase.connectors.spark:hbase-spark:1.0.0 \
  --class example.Wordcount \
  $BIGTABLE_SPARK_ASSEMBLY_JAR \
  $BIGTABLE_SPARK_PROJECT_ID $BIGTABLE_SPARK_INSTANCE_ID \
  $BIGTABLE_SPARK_WORDCOUNT_TABLE $BIGTABLE_SPARK_WORDCOUNT_FILE
```

Count the number of rows in the `BIGTABLE_SPARK_WORDCOUNT_TABLE` table. There should be 88 rows.

```bash
cbt \
  -project=$BIGTABLE_SPARK_PROJECT_ID \
  -instance=$BIGTABLE_SPARK_INSTANCE_ID \
  count $BIGTABLE_SPARK_WORDCOUNT_TABLE
```


## Running on Dataproc

If you'd like to run the Wordcount example on Dataproc, GCP's fully managed and highly scalable service for running
Apache Spark, see part two of this tutorial: [Running a Cloud Bigtable Spark job on Dataproc](https://cloud.google.com/community/tutorials/bigtable-spark-dataproc). It continues with the
same table and instance, so don't clean them up if you want to continue.

## Cleaning up

If you're not continuing to [run on Dataproc](https://cloud.google.com/community/tutorials/bigtable-spark-dataproc),
clean up your resources. 

If you created a new instance to try this out, delete it. 

    cbt -project=$BIGTABLE_SPARK_PROJECT_ID deleteinstance $BIGTABLE_SPARK_INSTANCE_ID

If you created a table on an existing instance, only delete that.

    cbt \
      -project=$BIGTABLE_SPARK_PROJECT_ID \
      -instance=$BIGTABLE_SPARK_INSTANCE_ID \
      deletetable $BIGTABLE_SPARK_WORDCOUNT_TABLE


## What's next

- Learn more about [Cloud Bigtable](https://cloud.google.com/bigtable/).
- Learn more about [Dataproc](https://cloud.google.com/dataproc).
