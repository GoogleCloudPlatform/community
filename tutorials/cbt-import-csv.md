---
title: Import a CSV file into a Cloud Bigtable table with Dataflow
description: Learn how to import a CSV file into a Cloud Bigtable table.
author: billyjacobson
tags: Cloud Bigtable, Dataflow, Java
date_published: 2018-06-26
---

Billy Jacobson | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>


<p style="background-color:#F3A8BC;"><b>Important:</b> You can now use the Cloud Bigtable CLI to import CSV files, using the <code>cbt import</code> command.
For details, see
<a href="https://medium.com/google-cloud/easy-csv-importing-into-cloud-bigtable-ed3f62139b89">Easy CSV importing into Cloud Bigtable</a>.
You can still follow the tutorial on this page to use Dataflow to import a CSV file if you need to have a customized CSV import.</p>

This tutorial walks you through importing data into a Cloud Bigtable table.
Using Dataflow, you take a CSV file and map each row to a table row
and use the headers as column qualifiers all placed under the same column 
family for simplicity.

## Prerequisites

### Install software and download sample code

Make sure that you have the following software installed:

- [Git](https://help.github.com/articles/set-up-git/)
- [Java SE 11](https://openjdk.java.net/install/)
- [Apache Maven 3.6.x or later](https://maven.apache.org/install.html)

These software packages are already installed for Cloud Shell.

If you haven't used Maven before, check out this
[5 minute quickstart](https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html).

### Set up your Google Cloud project

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  Enable billing for your project.
1.  Install the [Cloud SDK](https://cloud.google.com/sdk/) if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK.

## Upload your CSV

You can use your own CSV file or the
[example provided](https://github.com/GoogleCloudPlatform/cloud-bigtable-examples/blob/master/java/dataflow-connector-examples/sample.csv). 

### Remove and store the headers

The method used in this tutorial to import data isn't able to automatically handle the
headers. Before uploading your file, make a copy of the comma-separated list of
headers and remove the header row from the CSV if you don't want it imported into your
table. 

### Upload the CSV file

[Upload the headerless CSV file to a new or existing Cloud Storage bucket](https://cloud.google.com/storage/docs/uploading-objects).

## Prepare your Cloud Bigtable table for data import

Follow the steps in the [cbt quickstart](https://cloud.google.com/bigtable/docs/quickstart-cbt)
to create a Cloud Bigtable instance and install the command-line tool for Cloud
Bigtable. You can use an existing instance if you want.

1.  Create a table:

        cbt createtable my-table

1.  Create the `csv` column family in your table:  

        cbt createfamily my-table csv
   
    The Dataflow job inserts data into the column family `csv`.

1.  Verify that the creation worked:

        cbt ls my-table

    The output should be the following:

        Family Name GC Policy
        ----------- ---------
        csv   [default]

## Run the Dataflow job 

Dataflow is a fully-managed serverless service for transforming and
enriching data in stream (real-time) and batch (historical) modes. This tutorial uses Dataflow
as quick way to process the CSV concurrently and perform
writes at a large scale to the table. You also only pay for what you use, so it
keeps costs down.

### Clone the repository

Clone the following repository and change to the directory for this tutorial's
code:

    git clone https://github.com/GoogleCloudPlatform/cloud-bigtable-examples.git
    cd cloud-bigtable-examples/java/dataflow-connector-examples/

### Start the Dataflow job 

    mvn package exec:exec -DCsvImport -Dbigtable.projectID=YOUR_PROJECT_ID -Dbigtable.instanceID=YOUR_INSTANCE_ID \
    -DinputFile="YOUR_FILE" -Dbigtable.table="YOUR_TABLE_ID" -Dheaders="YOUR_HEADERS"

Replace `YOUR_PROJECT_ID`, `YOUR_INSTANCE_ID`, `YOUR_FILE`, `YOUR_TABLE_ID`, and `YOUR_HEADERS`
with appropriate values.

Here is an example command:
    
    mvn package exec:exec -DCsvImport -Dbigtable.projectID=YOUR_PROJECT_ID -Dbigtable.instanceID=YOUR_INSTANCE_ID \
    -DinputFile="gs://YOUR_BUCKET/sample.csv" -Dbigtable.table="my-table" -Dheaders="rowkey,a,b"

The first column is always used as the row key. 

If you see an error saying `"Unable to get application default credentials."`, this means that you likely need to
set up application credentials as outlined [here](https://cloud.google.com/docs/authentication/production). If you are
setting up a custom service account, be sure to assign the necessary roles for this job. For testing purposes, you can use
Bigtable Administrator, Dataflow Admin, and Storage Admin. 

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
