---
title: Use Spark with Cloud Bigtable 
description: Learn how to use Apache Spark for distributed and parallelized data processing with Cloud Bigtable.
author: billyjacobson
tags: bigtable, spark, database, big table, apache spark, hbase, dataproc
date_published: 2021-04-07
---

Billy Jacobson | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to use Apache Spark for distributed and parallelized data processing with Cloud Bigtable.

## Prerequisites

This tutorial assumes that you have basic familiarity with [Apache Spark](https://spark.apache.org/) and [Scala](https://www.scala-lang.org/).

Install and create the resources that are used in this tutorial:

1.  Create or select a [Google Cloud project](https://console.cloud.google.com/cloud-resource-manager).
1.  Install the [Cloud SDK](https://cloud.google.com/sdk/).
1.  Install the [sbt](https://www.scala-sbt.org/) build tool.
1.  Install [Apache Spark](https://spark.apache.org/). Download Spark built for Scala 2.11. This example uses Spark 2.4.7 and Scala 2.11.2.

## Get the example code and assemble the example

1.  Clone the repository that contains the example code:

        git clone https://github.com/GoogleCloudPlatform/java-docs-samples.git
        
1.  Go to the directory for the example:

        cd java-docs-samples/bigtable/spark

1.  Assemble the sample applications as a single uber JAR file (a JAR file with all of its dependencies and configurations):

        sbt clean assembly

## Set up Bigtable

1.  Set the following environment variables, so you can copy and paste the commands in this tutorial:

        SPARK_HOME=/PATH/TO/spark-2.4.7-bin-hadoop2.7
        BIGTABLE_SPARK_PROJECT_ID=your-project-id
        BIGTABLE_SPARK_INSTANCE_ID=your-instance-id

        BIGTABLE_SPARK_WORDCOUNT_TABLE=wordcount
        BIGTABLE_SPARK_WORDCOUNT_FILE=src/test/resources/Romeo-and-Juliet-prologue.txt
        BIGTABLE_SPARK_ASSEMBLY_JAR=target/scala-2.11/bigtable-spark-samples-assembly-0.1.jar

1.  Choose a [zone](https://cloud.google.com/bigtable/docs/locations) to use for your Bigtable instance, and set the zone as an environment variable:

        BIGTABLE_SPARK_INSTANCE_ZONE=your-zone

1.  Create the instance:

        cbt -project=$BIGTABLE_SPARK_PROJECT_ID createinstance \
         $BIGTABLE_SPARK_INSTANCE_ID "Spark wordcount instance" \
         $BIGTABLE_SPARK_INSTANCE_ID $BIGTABLE_SPARK_INSTANCE_ZONE 1 SSD

    **Note:** You can use an existing instance rather than creating a new instance in this step.

1.  Create a table called `wordcount`:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          -instance=$BIGTABLE_SPARK_INSTANCE_ID \
          createtable $BIGTABLE_SPARK_WORDCOUNT_TABLE \
          "families=cf"

1.  To ensure that the table was created, run this command and look for `wordcount`:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          -instance=$BIGTABLE_SPARK_INSTANCE_ID \
          ls

## Run the Wordcount job

This section contains the Spark Wordcount job that you'll be running. After the job has counted the words, it writes a row with the word as
the key with a column count containing the number of occurrences. You can view the
[full code on GitHub](https://github.com/GoogleCloudPlatform/java-docs-samples/blob/master/bigtable/spark/src/main/scala/example/Wordcount.scala). 

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

1.  Run the Spark job locally:

        $SPARK_HOME/bin/spark-submit \
          --packages org.apache.hbase.connectors.spark:hbase-spark:1.0.0 \
          --class example.Wordcount \
          $BIGTABLE_SPARK_ASSEMBLY_JAR \
          $BIGTABLE_SPARK_PROJECT_ID $BIGTABLE_SPARK_INSTANCE_ID \
          $BIGTABLE_SPARK_WORDCOUNT_TABLE $BIGTABLE_SPARK_WORDCOUNT_FILE

1.  Count the number of rows in the `BIGTABLE_SPARK_WORDCOUNT_TABLE` table:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          -instance=$BIGTABLE_SPARK_INSTANCE_ID \
          count $BIGTABLE_SPARK_WORDCOUNT_TABLE

    There should be 88 rows.

## Running on Dataproc

If you'd like to run the Wordcount example on Dataproc, Google Cloud's fully managed and highly scalable service for running
Apache Spark, see part 2 of this tutorial:
[Run a Cloud Bigtable Spark job on Dataproc](https://cloud.google.com/community/tutorials/bigtable-spark-dataproc).

Part 2 continues with the same table and instance, so don't delete these resources if you intend to continue on to part 2.

## Cleaning up

If you're not continuing to part 2 of this tutorial,
[Run a Cloud Bigtable Spark job on Dataproc](https://cloud.google.com/community/tutorials/bigtable-spark-dataproc),
then we recommend that you clean up the resources that you created in this tutorial. 

-  If you created a new instance to try this out, delete the instance: 

        cbt -project=$BIGTABLE_SPARK_PROJECT_ID deleteinstance $BIGTABLE_SPARK_INSTANCE_ID

-  If you created a table on an existing instance, delete the table:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          -instance=$BIGTABLE_SPARK_INSTANCE_ID \
          deletetable $BIGTABLE_SPARK_WORDCOUNT_TABLE

## What's next

- Learn more about [Cloud Bigtable](https://cloud.google.com/bigtable/).
- Learn more about [Dataproc](https://cloud.google.com/dataproc).
