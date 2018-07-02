---
title: Import a CSV file into a Cloud Bigtable table
description: Learn how to import a CSV file into a Cloud Bigtable table.
author: thebilly
tags: Cloud Bigtable, Dataflow, Java
date_published: 2018-06-26
---
## Cloud Bigtable

## Before you begin

### Install software and download sample code

Make sure you have the following software installed:

- [Git](https://help.github.com/articles/set-up-git/)
- [Java SE 8](http://www.oracle.com/technetwork/java/javase/downloads/index.html)
- [Apache Maven 3.3.x or later](https://maven.apache.org/install.html)
       
    > If you haven't used Maven before check out this [5 minute quickstart](https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html)


## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/).
1. Enable billing for your project.
1.  Install the **[Google Cloud SDK](https://cloud.google.com/sdk/)** if you do
    not already have it. Make sure you
    [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK. Use
    your project's ID to set the default project for the `gcloud` command-line tool. 

## Upload your CSV

### Create a Google Cloud Storage bucket

You use Cloud Storage to store your application's dependencies. Feel free to use an existing bucket if you have one.

1. Navigate to the [Cloud Storage browser](https://console.cloud.google.com/storage/browser). 
1. Click 'create bucket' and complete the provided form.

### Remove and store the headers

The method we are using to import data isn't able to automatically handle the headers. Before uploading your file
save the comma-separated list of headers and remove that row from the CSV if you don't want it imported into your table. 

### Upload the CSV file

1. Navigate into your bucket
2. Click upload file and select your CSV. (You can also drag and drop the file to upload.)

## Create your table with the Cloud Bigtable Tool (CBT)

Follow the steps in [CBT quickstart](https://cloud.google.com/bigtable/docs/quickstart-cbt) to create a Cloud Bigtable 
instance and install the tool.

Once cbt is set up, run these commands to create a table and column family

    cbt createtable my-table
    cbt createfamily my-table cf1

You can verify this worked by running 

    cbt ls
    cbt ls my-table

## Run the Cloud Dataflow job 
https://github.com/GoogleCloudPlatform/cloud-bigtable-examples.git

### Clone the repo

Clone the following repository and change to into the directory for this tutorial's
code:

    git clone https://github.com/GoogleCloudPlatform/cloud-bigtable-examples.git
    cd java/dataflow-connector-examples/
    

### Start the Dataflow job 

    mvn package exec:exec -DCsvImport -Dbigtable.projectID=<projectID> -Dbigtable.instanceID=<instanceID> 
    -Dgs=<Your bucket>  -DinputFile="<Your file>" -Dheaders="<Your headers>"

### Monitor your job

In the [Dataflow console](https://pantheon.corp.google.com/dataflow), you can monitor the newly created job's status and 
see if there are any errors running it. 

## Verify your data was inserted

Run cbt read (10 rows)

    cbt read my-table count=5