---
title: Import a CSV file into a Cloud Bigtable table
description: Learn how to import a CSV file into a Cloud Bigtable table.
author: thebilly
tags: Cloud Bigtable, Dataflow, Java
date_published: 2018-06-26
---

This tutorial will walk you through importing data into a Cloud Bigtable table.
Using Cloud Dataflow, we will take a CSV file and map each row to a table row
and use the headers as column qualifiers all placed under the same column 
family for simplicity.

## Prerequisites

### Install software and download sample code


Make sure you have the following software installed:

- [Git](https://help.github.com/articles/set-up-git/)
- [Java SE 8](http://www.oracle.com/technetwork/java/javase/downloads/index.html)

  Note: that Java 9 will not work for this.

- [Apache Maven 3.3.x or later](https://maven.apache.org/install.html)

If you haven't used Maven before check out this
[5 minute quickstart](https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html).

### Set up your Google Cloud Platform project

1.  Create a project in the [GCP Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the **[Google Cloud SDK](https://cloud.google.com/sdk/)** if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK.

## Upload your CSV

You can use your own CSV file or the
[example provided](https://github.com/GoogleCloudPlatform/cloud-bigtable-examples/blob/master/java/dataflow-connector-examples/sample.csv). 

### Remove and store the headers

The method we are using to import data isn't able to automatically handle the
headers. Before uploading your file, make a copy of the comma-separated list of
headers and remove that row from the CSV if you don't want it imported into your
table. 

### Upload the CSV file

[Upload the headerless CSV file to a new or existing Cloud Storage bucket](https://cloud.google.com/storage/docs/uploading-objects).

## Prepare your Cloud Bigtable table for data import

Follow the steps in [cbt quickstart](https://cloud.google.com/bigtable/docs/quickstart-cbt)
to create a Cloud Bigtable instance and install the command line tool for Cloud
Bigtable. You can use an existing instance if you want.

Use an existing table or create a table:

    cbt createtable my-table

The Cloud Dataflow job inserts data into column family 'csv'. Create that column
family in your table:  

    cbt createfamily my-table csv

You can verify this worked by running:

    cbt ls my-table
    
Expect to see the following:

    Family Name GC Policy
    ----------- ---------
    csv   [default]

## Run the Cloud Dataflow job 

Cloud Dataflow is a fully-managed serverless service for transforming and
enriching data in stream (real time) and batch (historical) modes. We are using
it as an easy and quick way to process the CSV concurrently and easily perform
writes at a large scale to our table. You also only pay for what you use, so it
keeps costs down.

### Clone the repo

Clone the following repository and change to the directory for this tutorial's
code:

    git clone https://github.com/GoogleCloudPlatform/cloud-bigtable-examples.git
    cd cloud-bigtable-examples/java/dataflow-connector-examples/

### Start the Dataflow job 

    mvn package exec:exec -DCsvImport -Dbigtable.projectID=YOUR_PROJECT_ID -Dbigtable.instanceID=YOUR_INSTANCE_ID \
    -DinputFile="YOUR_FILE" -Dbigtable.table="YOUR_TABLE_ID" -Dheaders="YOUR_HEADERS"

replacing `YOUR_PROJECT_ID`, `YOUR_INSTANCE_ID`, `YOUR_FILE`, `YOUR_TABLE_ID`, and `YOUR_HEADERS`
with appropriate values.

Here is an example command:
    
    mvn package exec:exec -DCsvImport -Dbigtable.projectID=YOUR_PROJECT_ID -Dbigtable.instanceID=YOUR_INSTANCE_ID \
    -DinputFile="gs://YOUR_BUCKET/sample.csv" -Dbigtable.table="my-table" -Dheaders="rowkey,a,b"

Note: The first column will always be used as the row key. 

### Monitor your job

Monitor the newly created job's status and see if there are any errors running
it in the [Dataflow console](https://console.cloud.google.com/dataflow). 

## Verify your data was inserted

Run the following command to see the data for the first five rows (sorted
lexicographically by row key) of your Cloud Bigtable table and verify that the
output matches the data in the CSV file:

    cbt read my-table count=5
    
Expect an output similar to the following:
    
    1
      csv:a                                    @ 2018/07/09-13:42:39.364000
        "A5"
      csv:b                                    @ 2018/07/09-13:42:39.364000
        "B2"
    ----------------------------------------
    10
      csv:a                                    @ 2018/07/09-13:42:38.022000
        "A3"
      csv:b                                    @ 2018/07/09-13:42:38.022000
        "B4"
    ----------------------------------------
    2
      csv:a                                    @ 2018/07/09-13:42:39.365000
        "A4"
      csv:b                                    @ 2018/07/09-13:42:39.365000
        "B8"
    ----------------------------------------
    3
      csv:a                                    @ 2018/07/09-13:42:39.366000
        "A8"
      csv:b                                    @ 2018/07/09-13:42:39.366000
        "B0"
    ----------------------------------------
    4
      csv:a                                    @ 2018/07/09-13:42:39.367000
        "A4"
      csv:b                                    @ 2018/07/09-13:42:39.367000
        "B4"
    
## Next steps

* Explore the [Cloud Bigtable documentation](https://cloud.google.com/bigtable/docs/).
