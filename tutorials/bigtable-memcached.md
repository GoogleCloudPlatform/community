---
title: Adding a cache layer to Google Cloud databases (Cloud Bigtable with Memcached)
description: Improve your application's performance by using Memcached for frequently queried data.
author: billyjacobson
tags: bigtable, memcached, database, memorystore, firestore, datastore, spanner, cache, caching, big table
date_published: 2020-11-03
---

Billy Jacobson | Developer Relations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how to improve your application's performance by using Memcached for frequently queried data like this:

```java
MemcachedClient mcc = new MemcachedClient(new InetSocketAddress(memcachedIP, 11211));      
Object value = mcc.get(rowId);
if (value != null) {
    System.out.println("Value fetched from cache: " + value);
} else {
    // Read row from database (Pseudocode)
    Row row = dataClient.readRow(rowId); 
    mcc.set(rowId, 30 * 60, row.toString()); // Cache for 30 minutes.
    System.out.println("Value fetched from db and cached: " + row);
}
```

Databases are designed for specific schemas, queries, and throughput, but if you have data that gets queried more frequently for a period of time, you may want 
to reduce the load on your database by introducing a cache layer. 

This tutorial looks at the horizontally scalable Cloud Bigtable, which is great for high-throughput reads and writes. You can optimize performance by ensuring
that rows are queried somewhat uniformly across the database. If you introduce a cache for more frequently queried rows, you speed up your application in two 
ways: reducing the load on frequently accessed rows and speeding up responses by colocating the cache and computing. 

Memcached is an in-memory key-value store for small chunks of arbitrary data. This tutorial uses the scalable, fully managed
[Memorystore for Memcached](https://cloud.google.com/memorystore/docs/memcached), because it is well integrated with the Google Cloud ecosystem.

The examples in this tutorial use [Cloud Bigtable](https://cloud.google.com/bigtable/docs), but Spanner or Firestore would be good options too.

This tutorial uses [`gcloud` commands](https://cloud.google.com/sdk/gcloud) for most of the steps, but you can accomplish the same tasks in the
[Cloud Console](https://console.cloud.google.com/).

## Before you begin

1.  [Create a new Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) or select an existing project.

1.  Create a Cloud Bigtable instance and a table with one row:

        cbt createinstance bt-cache "Bigtable with cache" bt-cache-c1 us-central1-b 1 SSD && \ 
        cbt -instance=bt-cache createtable mobile-time-series "families=stats_summary" && \ 
        cbt -instance=bt-cache set mobile-time-series phone#4c410523#20190501 stats_summary:os_build=PQ2A.190405.003 stats_summary:os_name=android && \ 
        cbt -instance=bt-cache read mobile-time-series

## The code

The general logic for a cache can be described as follows:

1.  Pick a row key to query.
1.  If the row key is in cache
    1.  Return the value.
1.  Otherwise
    1.  Look up the row in Cloud Bigtable.
    1.  Add the value to the cache with an expiration.
    1.  Return the value.

For Cloud Bigtable, your code might look like this
([full code on GitHub](https://github.com/GoogleCloudPlatform/java-docs-samples/tree/master/bigtable/memorystore)):

[embedmd]:# (https://raw.githubusercontent.com/GoogleCloudPlatform/java-docs-samples/master/bigtable/memorystore/src/main/java/Memcached.java /try {/ /get cache value.*\n.*\n.*}/)
```java
try {
  MemcachedClient mcc = new MemcachedClient(new InetSocketAddress(discoveryEndpoint, 11211));
  System.out.println("Connected to Memcached successfully");

  // Get value from cache
  String rowkey = "phone#4c410523#20190501";
  String columnFamily = "stats_summary";
  String column = "os_build";
  String cacheKey = String.format("%s:%s:%s", rowkey, columnFamily, column);

  Object value = mcc.get(cacheKey);

  if (value != null) {
    System.out.println("Value fetched from cache: " + value);
  } else {
    System.out.println("didn't get value from cache");
    // Get data from Bigtable source and add to cache for 30 minutes.
    try (BigtableDataClient dataClient = BigtableDataClient.create(projectId, instanceId)) {
      Row row = dataClient.readRow(tableId, rowkey);
      String cellValue = row.getCells(columnFamily, column).get(0).getValue().toStringUtf8();
      System.out.println("got data from bt " + cellValue);
      // Set data into memcached server.
      mcc.set(cacheKey, 30 * 60, cellValue);
      System.out.println("Value fetched from Bigtable: " + cellValue);
    } catch (Exception e) {
      System.out.println("Could not set cache value.");
      e.printStackTrace();
    }
  }
  mcc.shutdown();
} catch (Exception e) {
  System.out.println("Could not get cache value.");
  e.printStackTrace();
}
```


In this case, the cache key is `row_key:column_family:column_qualifier` to make it easy to access column values.

Here are some potential cache key-value pairs you could use:

- `rowkey: encoded row`
- `start_row_key-end_row_key: array of encoded rows`
- `SQL queries: results`
- `row prefix: array of encoded rows`

When creating your cache, determine the setup based on your use case. Note that Bigtable rowkeys have a size limit of 4KB, whereas Memcached keys have a size 
limit of 250 bytes, so your rowkey could potentially be too large.

## Create a Memcached instance

This tutorial creates a Memorystore for Memcached instance, but you can install and run a
[local Memcached instance](https://github.com/memcached/memcached/wiki/Install) to try this out or for testing. 

1.  Enable the Memorystore for Memcached API:

        gcloud services enable memcache.googleapis.com

1.  Create a Memcached instance with the smallest size on the default network, in a region that is appropriate for your application:

        gcloud beta memcache instances create bigtable-cache --node-count=1 --node-cpu=1 --node-memory=1GB --region=us-central1 
        
    You may have to wait a few minutes for the instance to finish creation.

1.  Get the Memcached instance details and get the 
    [discoveryEndpoint IP address](https://cloud.google.com/memorystore/docs/memcached/using-auto-discovery):

        gcloud beta memcache instances describe bigtable-cache --region=us-central1

## Set up a machine within the network

You need to create a place to run code on the [same network](https://cloud.google.com/vpc/docs/vpc) as your Memcached instance. You can use a 
[serverless option](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) such as Cloud Functions, but a Compute Engine VM requires less 
configuration.

1.  Create a Compute Engine instance on the default network with enabled API scopes for Cloud Bigtable data:

        gcloud beta compute instances create bigtable-memcached-vm \
            --zone=us-central1-a \
            --machine-type=e2-micro \
            --image=debian-10-buster-v20200910 \
            --image-project=debian-cloud \
            --boot-disk-size=10GB \
            --boot-disk-type=pd-standard \
            --boot-disk-device-name=bigtable-memcached-vm \
            --scopes=https://www.googleapis.com/auth/bigtable.data,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/trace.append,https://www.googleapis.com/auth/devstorage.read_only

     The zone must be in the same region as your Memcached instance.
     
1.  Connect to your new VM with SSH:

        gcloud beta compute ssh --zone "us-central1-a" bigtable-memcached-vm

## Optionally connect to Memcached via Telnet

The [Memorystore for Memcached documentation](https://cloud.google.com/memorystore/docs/memcached/connecting-memcached-instance) contains more information about
this process, but you can just run the commands below to set and get a value in the cache:

    sudo apt-get install telnet
    telnet $DISCOVERY_ENDPOINT_ID 11211
    set greeting 1 0 11
    hello world
    get greeting

## Run the code

Now you're ready to put your code on the machine.

The instructions in this section explain how to clone the repository directly onto the VM and run it from there. If you want to customize the code, check out the
article on 
[rsyncing code to Compute Engine](https://medium.com/google-cloud/rsync-on-gcp-compute-engine-when-you-cant-run-your-code-locally-network-issues-cb2ff2c9c176) or
use the [gcloud scp command](https://cloud.google.com/sdk/gcloud/reference/compute/scp) to copy your code from your local machine to your VM.

1.  Install Git on the VM:

        sudo apt-get install git

1.  Clone the repository containing the code:

        git clone https://github.com/GoogleCloudPlatform/java-docs-samples.git
        
1.  Go to the directory containing the code:

        cd java-docs-samples/bigtable/memorystore

1.  Install Maven:

        sudo apt-get install maven

1.  Set environment variables for your configuration:

        PROJECT_ID=your-project-id
        MEMCACHED_DISCOVERY_ENDPOINT="0.0.0.0"
        
    You get the `MEMCACHED_DISCOVERY_ENDPOINT` value from the `gcloud beta memcache instances describe` command that you ran in a previous step. Exclude the
    `:11211` suffix

1.  Run the program once to get the value from the database, and then run it again to see that the value is fetched from the cache:

        mvn compile exec:java -Dexec.mainClass=Memcached \
            -DbigtableProjectId=$PROJECT_ID \
            -DbigtableInstanceId=bt-cache \
            -DbigtableTableId=mobile-time-series \
            -DmemcachedDiscoveryEndpoint=$MEMCACHED_DISCOVERY_ENDPOINT

Now you have used the core concepts for putting a cache layer in front of your database, and you can integrate these concepts into your existing application.

## Cleaning up

If you followed along with this tutorial, delete your VM, Cloud Bigtable instance, and Memcached instance with these commands to avoid being billed for 
the continued use of these resources:

    cbt deleteinstance bt-cache
    gcloud beta memcache instances delete bigtable-cache --region=us-central1 
    gcloud compute instances delete bigtable-memcached-vm --zone=us-central1-a

## What's next

- Learn more about [Cloud Bigtable](https://cloud.google.com/bigtable/docs/).
- Learn more about [Memorystore for Memcached](https://cloud.google.com/memorystore/docs/memcached).
