---
title: Run a Cloud Bigtable Spark job on Dataproc 
description: Run a Spark job on Dataproc that reads from and writes to Cloud Bigtable.
author: billyjacobson
tags: bigtable, spark, database, big table, apache spark, hbase, dataproc
date_published: 2021-04-07
---

Billy Jacobson | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you run a Spark job on Dataproc that reads from and writes to Cloud Bigtable.

## Prerequisites

This is a followup to [Using Spark with Cloud Bigtable](https://cloud.google.com/community/tutorials/bigtable-spark),
so follow the steps in that tutorial before beginning this one. The previous tutorial walks you through setting up the environment
variables, creating the Bigtable instance and table, and running the Spark job locally.

The examples in this tutorial use Dataproc 1.4. For the list of available Dataproc image versions see the
[Dataproc image version list](https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-versions).

## Create the Dataproc cluster

1.  Set the environment variables for configuring your Dataproc cluster:

        BIGTABLE_SPARK_DATAPROC_CLUSTER=your-dataproc-cluster
        BIGTABLE_SPARK_DATAPROC_REGION=your-dataproc-region
        BIGTABLE_SPARK_CLUSTER_ZONE=your-bigtable-cluster-zone
        BIGTABLE_SPARK_PROJECT_ID=your-project-id //This can be the same as your Bigtable project 

    For information about regions and zones, read [Available regions and zones](https://cloud.google.com/compute/docs/regions-zones#available).

1.  Use the `gcloud` command-line tool to create a cluster:

        gcloud dataproc clusters create $BIGTABLE_SPARK_DATAPROC_CLUSTER \
          --region=$BIGTABLE_SPARK_DATAPROC_REGION \
          --zone=$BIGTABLE_SPARK_CLUSTER_ZONE \
          --project=$BIGTABLE_SPARK_PROJECT_ID \
          --image-version=1.4

1.  List the clusters:

        gcloud dataproc clusters list \
        --region=$BIGTABLE_SPARK_DATAPROC_REGION

     Make sure that `BIGTABLE_SPARK_DATAPROC_CLUSTER` is among the clusters.

## Upload the file to Cloud Storage

Because you're running the Spark job in the cloud, you need to upload your the file to [Cloud Storage](https://cloud.google.com/storage).

For information about `gsutil`, see [Quickstart: Using the gsutil tool](https://cloud.google.com/storage/docs/quickstart-gsutil).

1.  Choose a bucket name and set it as an environment variable:
    
        BIGTABLE_SPARK_BUCKET_NAME=gs://your-bucket-name-12345
    
    Bucket names must be unique across all Google Cloud projects, so you may want to append a few digits, so you don't run into name conflicts during 
    creation.

1.  Create the bucket:

        gsutil mb \
          -b on \
          -l $BIGTABLE_SPARK_DATAPROC_REGION \
          -p $BIGTABLE_SPARK_PROJECT_ID \
          $BIGTABLE_SPARK_BUCKET_NAME

1.  Upload an input file into the bucket:

        gsutil cp src/test/resources/Romeo-and-Juliet-prologue.txt $BIGTABLE_SPARK_BUCKET_NAME

1.  List the contents of the bucket:

        gsutil ls $BIGTABLE_SPARK_BUCKET_NAME

    The output should be the following:

        gs://[your-bucket-name]/Romeo-and-Juliet-prologue.txt

## Submit the Wordcount job

Submit the Wordcount job to the Dataproc instance:

    gcloud dataproc jobs submit spark \
      --cluster=$BIGTABLE_SPARK_DATAPROC_CLUSTER \
      --region=$BIGTABLE_SPARK_DATAPROC_REGION \
      --class=example.Wordcount \
      --jars=$BIGTABLE_SPARK_ASSEMBLY_JAR \
      --properties=spark.jars.packages='org.apache.hbase.connectors.spark:hbase-spark:1.0.0' \
      -- \
      $BIGTABLE_SPARK_PROJECT_ID $BIGTABLE_SPARK_INSTANCE_ID \
      $BIGTABLE_SPARK_WORDCOUNT_TABLE $BIGTABLE_SPARK_BUCKET_NAME/Romeo-and-Juliet-prologue.txt

It may take some time to see any progress. You can use the `--verbosity` global option with `debug` to be told about progress earlier.

Eventually, you should see the following messages:

    Job [joibId] submitted.
    Waiting for job output...

## Verify

Read the database:

    cbt \
      -project=$BIGTABLE_SPARK_PROJECT_ID \
      -instance=$BIGTABLE_SPARK_INSTANCE_ID \
      read $BIGTABLE_SPARK_WORDCOUNT_TABLE

If you ran the Wordcount job locally, you will see duplicate entries for words, since Bigtable supports data versioning.

## Cleaning up

1.  If you created a new instance to try this out, delete the instance:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          deleteinstance $BIGTABLE_SPARK_INSTANCE_ID

1.  If you created a table on an existing instance, only delete the table:

        cbt \
          -project=$BIGTABLE_SPARK_PROJECT_ID \
          -instance=$BIGTABLE_SPARK_INSTANCE_ID \
          deletetable $BIGTABLE_SPARK_WORDCOUNT_TABLE

1.  Delete the Dataproc cluster:

        gcloud dataproc clusters delete $BIGTABLE_SPARK_DATAPROC_CLUSTER \
          --region=$BIGTABLE_SPARK_DATAPROC_REGION \
          --project=$BIGTABLE_SPARK_PROJECT_ID

1.  Verify that the cluster is deleted:

        gcloud dataproc clusters list \
          --region=$BIGTABLE_SPARK_DATAPROC_REGION

1.  Delete the input file and your bucket:

        gsutil rm $BIGTABLE_SPARK_BUCKET_NAME/Romeo-and-Juliet-prologue.txt
        gsutil rb $BIGTABLE_SPARK_BUCKET_NAME

## What's next

- Learn more about [Cloud Bigtable](https://cloud.google.com/bigtable/).
- Learn more about [Dataproc](https://cloud.google.com/dataproc).
