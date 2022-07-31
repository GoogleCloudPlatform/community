---
title: Using external Apache Hive metastore with Cloud Dataproc
description: Learn how to deploy an external Hive metastore service in High Availability mode for Cloud Dataproc.
author: anantdamle
tags: Dataproc, Hive, Apache Hadoop, CloudSQL, high availability, data analytics
date_published: 2022-08-01
---
Anant Damle | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Google Cloud [Dataproc](https://cloud.google.com/dataproc) provides managed Hadoop clusters, which—along with
[Dataproc Metastore](https://cloud.google.com/dataproc-metastore/docs) for managed Hive Metastore—allows developers and enterprises to use ephemeral 
clusters without losing the flexibility of using Hive and the related ecosystem.

Hive is a popular open source data warehouse system built on [Apache Hadoop](https://hadoop.apache.org/). Hive offers a SQL-like query language,
[HiveQL](https://wikipedia.org/wiki/Apache_Hive#HiveQL), which is used to analyze large, structured datasets. The Hive metastore holds metadata about 
Hive tables, such as their schema and location. MySQL is commonly used as a backend for the Hive metastore. Cloud SQL makes it easy to set up, maintain,
manage, and administer your relational databases on Google Cloud.

Dataproc is a fast, easy-to-use, fully managed service on Google Cloud for running [Apache Spark](https://spark.apache.org/) and
[Apache Hadoop](https://hadoop.apache.org/) workloads in a simple, cost-efficient way. Even though Dataproc clusters can remain stateless, we recommend
making the Hive table data persistent in Cloud Storage and the Hive metastore in MySQL on Cloud SQL.

This document builds on the multi-regional architecture concept described in the companion document on
[using Apache Hive on Dataproc](https://cloud.google.com/architecture/using-apache-hive-on-cloud-dataproc#considerations_for_multi-regional_architectures)
when the [Dataproc Metastore](https://cloud.google.com/dataproc-metastore/docs) service is unavailble.

This document is intended for a technical audience whose responsibilities include data processing or data analytics. This document assumes that you're 
familiar with data processing without the need to be an expert. This document assumes some familiarity with shell scripts and basic knowledge of Google
Cloud, Hadoop, and Hive.

## Objectives

 * Create MySQL instance on Cloud SQL for the Hive metastore
 * Deploy two single-node Dataproc clusters for Hive metastore service
 * Install [Cloud SQL Proxy]() on the Hive metastore Dataproc clusters
 * Upload Hive table data files to Cloud Storage
 * Create ephemeral worker Dataproc clusters in two separate regions 
 * Run Hive queries on compute clusters

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Dataproc](https://cloud.google.com/dataproc/pricing)
* [Cloud Storage](https://cloud.google.com/storage/pricing)
* [Cloud SQL](https://cloud.google.com/cloudsql/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your
projected usage.

## Architecture

![multi-regional hive metastore usage](https://cloud.google.com/architecture/images/using-apache-hive-on-cloud-dataproc-2.svg)

As the Hive metastore service can only run on the Dataproc cluster master nodes, the metastore service cluster is provisioned as a single node cluster to optimize costs. The Hive metastore is a stateless service and allows for multiple independent metastore services to be started in parallel to provide High Availability

The metastore service sends a high volume of requests to the database; to minimize latency, the metastore service clusters are deployed in the same region as the Cloud SQL instance. 

The solutions uses the [high availability configuration for Cloud SQL](https://cloud.google.com/sql/docs/mysql/high-availability) instances, to protect against rare cases of infrastructure failure. This solution also demonstrates the use of [private IP](https://cloud.google.com/vpc/docs/ip-addresses#:~:text=Private%20IP%20addresses%20are%20addresses,connected%20to%20a%20VPC%20network.&text=Public%20IP%20addresses%20are%20internet%20routable.)s to secure the perimeter of the data analytics system including the MySQL database.


With this architecture, the lifecycle of a Hive query follows these steps:

  1. The Hive client submits a query to the Hive server that runs in an ephemeral cluster.
  1. The server processes the query and requests the metadata from the metastore service running in a seperate cluster.
  1. The metastore service fetches the Hive metadata from Cloud SQL through a secure tunnel created by the Cloud SQL Proxy.
  1. The worker processes the data by loading data from the Hive warehouse located in a [multi-regional bucket](https://cloud.google.com/storage/docs/locations#location-mr) in Cloud Storage.
  1. The server returns the result to the client.

You can also consider using a regional bucket if the Hive data needs to be accessed only from Hive servers that are located in a single location. The choice between regional and multi-regional buckets depends on your use case. You must balance latency, availability, and bandwidth costs. Refer to the documentation on [location considerations](https://cloud.google.com/storage/docs/bucket-locations#considerations) for more details.


## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make
cleanup easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google
    Cloud project.
1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

    At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session opens and
    displays a command-line prompt. Cloud Shell is a shell environment with the Cloud SDK already installed, including
    the [gcloud](https://cloud.google.com/sdk/gcloud/) command-line tool, and with values already set for your current
    project. It can take a few seconds for the session to initialize.

1.  Enable APIs for Compute Engine, Cloud Storage, Dataproc, and Cloud SQL services:

        gcloud services enable \
        compute.googleapis.com \
        dataproc.googleapis.com \
        servicenetworking.googleapis.com \
        storage.googleapis.com \
        sqladmin.googleapis.com

## Setting up your environment

In Cloud Shell, set the default Compute Engine zone and region where you are going to create your Dataproc clusters:

    export PROJECT="$(gcloud info --format='value(config.project)')"
    export REGION="us-central1"
    export ZONE="us-central1-a"
    export ZONE2="us-central1-b"
    export WORKER_REGION2="us-east1"    
    export WORKER_ZONE2="us-east1-b"
    export WAREHOUSE_MULTI_REGION="us"
    export VPC_NETWORK_NAME="hive-network"

## Creating resources

### Create the warehouse Cloud Storage bucket

Create a Cloud Storage bucket for storing test data, run the following command on Cloud Shell:

    gsutil mb -p ${PROJECT} \
    -l ${WAREHOUSE_MULTI_REGION} \
    "gs://${PROJECT}-warehouse" 


### Create private VPC network

Create user defined cloud networking and peer it with Google services

1.  In Cloud Shell, run the following command to create the VPC network:

        gcloud compute networks create ${VPC_NETWORK_NAME} \
        --subnet-mode=auto \
        --bgp-routing-mode=global

1.  In Cloud Shell, run the follwing command to reserve the IPs required for the network:

        gcloud compute addresses create \
        google-managed-services-${VPC_NETWORK_NAME} \
        --global \
        --purpose=VPC_PEERING \
        --prefix-length=16 \
        --network=projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}

1.  In Cloud Shell, run the command to setup VPC peering for Google service on the private VPC network:

        gcloud services vpc-peerings connect \
        --ranges=google-managed-services-${VPC_NETWORK_NAME} \
        --network=${VPC_NETWORK_NAME} \
        --project=${PROJECT}

1.  In Cloud Shell, run the following command to enable VM-to-VM communication for Dataproc clusters and CloudSQL.

        gcloud compute firewall-rules create allow-all-internal \
        --network projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME} \
        --allow=tcp,udp,icmp \
        --source-ranges=10.128.0.0/9

1.  In Cloud Shell, run the command to enable Private Google access to the two regions that you will use for this tutorial:

        gcloud compute networks subnets update "${VPC_NETWORK_NAME}" \
        --region=${REGION} \
        --enable-private-ip-google-access
        
        gcloud compute networks subnets update "${VPC_NETWORK_NAME}" \
        --region=${WORKER_REGION2} \
        --enable-private-ip-google-access

### Create Cloud SQL instance

Create a [high availability](https://cloud.google.com/sql/docs/mysql/high-availability) MySQL on Cloud SQL instance to be used later to host the Hive metastore database. The CloudSQL instance uses private IPs for added protection.

In Cloud Shell, execute the following command to create a new Cloud SQL instance:
        
    gcloud beta sql instances create hive-metastore-db \
    --database-version="MYSQL_5_7" \
    --activation-policy=ALWAYS \
    --enable-bin-log \
    --no-assign-ip \
    --network="projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}" \
    --availability-type=regional \
    --zone="${ZONE}" \
    --secondary-zone="${ZONE2}"

**Note:** This tutorial uses an empty `root` user password for simplicity. To follow the best practice for production systems add `--root-password=<your-password>` in the command above to set a root user password, and follow the [initialization guide](https://github.com/GoogleCloudDataproc/initialization-actions/tree/master/cloud-sql-proxy#protecting-passwords-with-kms) for CloudSQL proxy on using passwords with Hive.


This command might take a few minutes to complete.

### Create Dataproc clusters for Hive metastore

Create the first single-node Dataproc cluster that will be the Hive metastore service provider for worker clusters.

In Cloud Shell, execute the following command:

    gcloud dataproc clusters create hive-metastore1 \
    --no-address \
    --enable-component-gateway \
    --scopes sql-admin \
    --region ${REGION} \
    --zone ${ZONE} \
    --single-node \
    --network="projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}" \
    --master-machine-type n1-standard-8 \
    --master-boot-disk-type pd-ssd \
    --master-boot-disk-size 500 \
    --image-version 2.0-debian10 \
    --properties hive:hive.metastore.warehouse.dir=gs://${PROJECT}-warehouse/datasets \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/cloud-sql-proxy/cloud-sql-proxy.sh \
    --metadata hive-metastore-instance=${PROJECT}:${REGION}:hive-metastore-db

This command will take a few minutes to create and initialize the cluster.

Since the Hive metastore is stateless, multiple instances can be deployed to achieve High Availability. Create a failover metastore service cluster using the following command in Cloud Shell:

    gcloud dataproc clusters create hive-metastore2 \
    --no-address \
    --enable-component-gateway \
    --scopes sql-admin \
    --region ${REGION} \
    --zone ${ZONE2} \
    --single-node \
    --network="projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}" \
    --master-machine-type n1-standard-8 \
    --master-boot-disk-type pd-ssd \
    --master-boot-disk-size 500 \
    --image-version 2.0-debian10 \
    --properties hive:hive.metastore.warehouse.dir=gs://${PROJECT}-warehouse/datasets \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/cloud-sql-proxy/cloud-sql-proxy.sh \
    --metadata hive-metastore-instance=${PROJECT}:${REGION}:hive-metastore-db \
    --async        

### Create a Hive table

In this section, you upload a sample dataset to your warehouse bucket, create a new external Hive table.

In Cloud Shell run the following commands:

1.  Copy the sample dataset to warehouse bucket:

        gsutil cp gs://hive-solution/part-00000.parquet \
        gs://${PROJECT}-warehouse/datasets/transactions/part-00000.parquet

    The sample dataset is compressed in the [Parquet](https://parquet.apache.org/) format and contains thousands of fictitious bank transaction records with three columns: date, amount, and transaction type.

1.  Create an external Hive table for the dataset:

        gcloud dataproc jobs submit hive \
        --cluster hive-metastore1 \
        --region ${REGION} \
        --execute " 
        CREATE EXTERNAL TABLE transactions (SubmissionDate DATE, TransactionAmount DOUBLE, TransactionType STRING) STORED AS PARQUET 
        LOCATION 'gs://${PROJECT}-warehouse/datasets/transactions';"

### Create Worker clusters

In this section, you create two Dataproc clusters in different regions preferrably in the same multi-region covered by the warehouse bucket.

In Cloud Shell, run the following command to create first worker cluster in the same region:

    gcloud dataproc clusters create hive-worker1 \
    --image-version 2.0-debian10 \
    --region ${REGION} \
    --zone ${ZONE} \
    --network="projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}" \
    --properties=^#^hive:hive.metastore.warehouse.dir=gs://${PROJECT}-warehouse/datasets \
    --properties=^#^hive:hive.metastore.uris=thrift://hive-metastore1-m.${ZONE}.c.${PROJECT}.internal:9083,thrift://hive-metastore2-m.${ZONE2}.c.${PROJECT}.internal:9083

Note: The `hive.metastore.uris` property points the metastore service to the external Hive metastore service clusters. It is possible to indicate multiple, comma-separated metastore instances.

## Running Hive Query on workers

You can use different tools inside Dataproc to run Hive queries like Hive jobs API, [Beeline](https://cwiki.apache.org/confluence/display/Hive/HiveServer2+Clients#HiveServer2Clients-Beeline%E2%80%93CommandLineShell) CLI client and [SparkSQL](https://spark.apache.org/sql/). In this section, you learn how to perform queries using the Hive jobs API:

    gcloud dataproc jobs submit hive \
    --cluster hive-worker1 \
    --region ${REGION} \
    --execute "SELECT * FROM transactions LIMIT 10;"

The output includes the following:

    +-----------------+--------------------+------------------+
    | submissiondate  | transactionamount  | transactiontype  |
    +-----------------+--------------------+------------------+
    | 2017-12-03      | 1167.39            | debit            |
    | 2017-09-23      | 2567.87            | debit            |
    | 2017-12-22      | 1074.73            | credit           |
    | 2018-01-21      | 5718.58            | debit            |
    | 2017-10-21      | 333.26             | debit            |
    | 2017-09-12      | 2439.62            | debit            |
    | 2017-08-06      | 5885.08            | debit            |
    | 2017-12-05      | 7353.92            | authorization    |
    | 2017-09-12      | 4710.29            | authorization    |
    | 2018-01-05      | 9115.27            | debit            |
    +-----------------+--------------------+------------------+

## Creating another Dataproc cluster

In this section, you create another Dataproc cluster to verify that the Hive data and Hive metastore can be shared across multiple clusters in separate regions.

1.  Create the second worker cluster in a different region:

        gcloud dataproc clusters create hive-worker2 \
        --image-version 2.0-debian10 \
        --region ${WORKER_REGION2} \
        --zone ${WORKER_ZONE2} \
        --network="projects/${PROJECT}/global/networks/${VPC_NETWORK_NAME}" \
        --properties=^#^hive:hive.metastore.warehouse.dir=gs://${PROJECT}-warehouse/datasets \
        --properties=^#^hive:hive.metastore.uris=thrift://hive-metastore1-m.${ZONE}.c.${PROJECT}.internal:9083,thrift://hive-metastore2-m.${ZONE2}.c.${PROJECT}.internal:9083

1.  Verify that the new cluster can access the data:

        gcloud dataproc jobs submit hive \
        --cluster hive-worker2 \
        --region ${WORKER_REGION2} \
        --execute "
        SELECT TransactionType, COUNT(TransactionType) as Count 
        FROM transactions 
        WHERE SubmissionDate = '2017-08-22' 
        GROUP BY TransactionType;"

    The output includes the following:

        +------------------+--------+
        | transactiontype  | count  |
        +------------------+--------+
        | authorization    | 696    |
        | credit           | 1722   |
        | debit            | 2599   |
        +------------------+--------+

Congratulations, you've completed the tutorial!

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

* Read the companion document on 
[Using Apache Hive on Dataproc](https://cloud.google.com/architecture/using-apache-hive-on-cloud-dataproc).
* Learn about [Dataproc Metastore](https://cloud.google.com/dlp/docs/inspecting-storage).
* Learn more about [Using BigQuery connector with Spark](https://cloud.google.com/dataproc/docs/tutorials/bigquery-connector-spark-example).
* Explore reference architectures, diagrams, tutorials, and best practices about Google Cloud. Take a look at our [Cloud Architecture Center](https://cloud.google.com/architecture).
