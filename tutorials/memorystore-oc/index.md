---
title: Client-side tracing of Memorystore for Redis workloads with OpenCensus
description: Implement client-side tracing in Memorystore for Redis workloads with OpenCensus and Cloud Trace.
author: karthitect
tags: Cloud Memorystore, OpenCensus, tracing
date_published: 2018-12-19
---

Karthi Thyagarajan | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to implement client-side tracing in your Memorystore for Redis workloads using OpenCensus and Cloud Trace. While Memorystore for Redis surfaces a number of helpful server-side metrics via Stackdriver, applications can realize added benefits from implementing client-side tracing. For example, server-side metrics do not give you a window into the round-trip latency of calls made to your Redis endpoint and can only be surfaced using client-side tracing.

[Cloud Memorystore](https://cloud.google.com/memorystore/) for Redis provides a fully managed and Google-hosted Redis deployment for your caching needs.

[OpenCensus](https://opencensus.io) is an open source library that can be used to provide observability in your applications. It is vendor-agnostic and integrates with a number of backends such as Prometheus and Zipkin. In this tutorial, we use Cloud Trace as the tracing backend.

## Objectives

*   Deploy a Cloud Memorystore for Redis instance.
*   Deploy a Compute Engine VM for running an OpenCensus instrumented Java client.
*   Download, deploy, and run an instrumented Java client.
*   View OpenCensus traces in the Cloud Trace tool.

## Costs

This tutorial uses the following billable components of Google Cloud:

*   Compute Engine
*   Memorystore for Redis
*   Cloud Trace
*   Cloud Storage

You can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage.

New Google Cloud users might be eligible for a [free trial](https://cloud.google.com/free/).

We recommend that you deploy this tutorial into an ephemeral project, which can then be deleted once you’re done.

## Before you begin

### Create a new project

1.  In the Cloud Console, go to the [Manage resources page](https://console.cloud.google.com/cloud-resource-manager).
2.  Select a project, or click **Create Project** to create a new project.
3.  In the dialog, name your project. Make a note of your generated project ID.
4.  Click **Create** to create a new project.

### Enable billing

*   Make sure that [billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

### Initialize the environment

1.  Start a [Cloud Shell instance](https://console.cloud.google.com/home/dashboard?cloudshell%3Dtrue).

2.  In Cloud Shell, set the default Compute Engine zone to the zone where you are going to create your Dataproc clusters. This tutorial uses the `us-central1-a` zone in the `us-central1` region.

        $ export REGION=us-central1
        $ export ZONE=us-central1-a
        $ gcloud config set compute/zone $ZONE

3.  Enable the Compute Engine and Memorystore for Redis Admin APIs by running this command in Cloud Shell:

        $ gcloud services enable compute.googleapis.com redis.googleapis.com

## Reference architecture

For simplicity, in this tutorial we’ll implement all of our client-side logic in a Java console application. For the caching tier, we’ll use Memorystore for Redis; for the database tier, we’ll use Cloud Storage. This will allow us to focus on the key aspects of client-side tracing without getting hung up on things like database deployments and related configuration.

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image4.png)

## Application flow

The Java application running on the Compute Engine VM will retrieve the simple JSON file (person.json) shown below from Cloud Storage and cache it in Cloud Memorystore for Redis:

    {
     "FirstName": "John",
     "LastName": "Doe"
    }

The application will then turn around and fetch it again from Cloud Memorystore for Redis.

Both the initial retrieval from Cloud Storage and the second retrieval from Cloud Memorystore for Redis will be instrumented with OpenCensus so we can inspect the latencies involved in those calls within Cloud Trace.

## Creating a Memorystore for Redis instance

In this section, you will create a new Memorystore for Redis instance that will be used later by our Java application.

In Cloud Shell, create a 1 GB Memorystore for Redis instance:

    $ gcloud redis instances create cm-redis --size=1 --region=$REGION --zone=$ZONE

This command might take a few minutes to complete.

## Upload JSON object to Cloud Storage bucket

In this section, you will first create a Cloud Storage bucket and then upload the JSON file (`person.json`) for subsequent retrieval in the Java application 
below.

Run the following commands in Cloud Shell to create a bucket. Keep in mind that Cloud Storage bucket names have to be globally unique, so be sure to substitute `[your-unique-bucket-name]` below with a unique name of your own.

    $ export MYBUCKET=[your-unique-bucket-name]
    $ gsutil mb gs://$MYBUCKET

Now upload a JSON file to the bucket you just created by running the following commands:

    $ echo "{\"FirstName\": \"John\",\"LastName\": \"Doe\"}" >> person.json

    $ gsutil cp person.json gs://$MYBUCKET/

The Java application you’ll deploy below will need this file.

## Creating and configuring a Compute Engine VM

Create a Compute Engine VM by running the following command from Cloud Shell:

    gcloud compute instances create trace-client

In the **Navigation** menu on the left side of the Cloud Console, choose **Compute Engine > VM Instances**.

Use SSH to connect to the VM by clicking the SSH button (highlighted in yellow in the screenshot below):

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image7.png)

Once logged into the VM, run the following command to install the redis-cli, git, the Java 8 JDK, and maven:

    $ sudo apt-get install redis-tools git openjdk-8-jdk maven -y

Run the following command within the trace-client VM to ensure that you can reach the Cloud Memorystore for Redis instance you created earlier:

    $ redis-cli -h [ip-address-of-redis-instance] PING

You should get a response from the Redis server:

    $ PONG

**Note:** To get the IP address of your Memorystore for Redis instance, run the following commands from Cloud Shell and use the value listed next to the label titled ‘host’ (see screenshot below).

    $ export $REGION=us-central1
    $ gcloud redis instances describe cm-redis --region=$REGION

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image8.png)

Make a note of the IP address as you’ll need it below when updating the Java code.

## Deploying the Java application

In this section, you’ll download the Java application containing the instrumented code, make the necessary modifications to reflect your environment and then run it.

If you’re not already logged into the trace-client VM you created in the previous section, do so by following the steps described in the previous section.

Once you’ve logged in, clone the source repository for this tutorial

    $ git clone https://github.com/GoogleCloudPlatform/community.git

You will now update the Java application with some configuration specific to your project. First, navigate to the folder containing the Java source

    $ cd community/tutorials/memorystore-oc/java/

Then open the Java source using your favorite terminal editor, such as nano or vi

    $ nano src/main/java/com/example/memorystore/App.java

Near the top of the file, you’ll need to edit 3 of the following 4 Java String constants to reflect your environment

    ...

    public class App {

        private static final String PROJECT_ID = "[YOUR PROJECT ID]";
        private static final String GCS_BUCKET_NAME = "[YOUR BUCKET NAME]";
        private static final String GCS_OBJECT_NAME = "person.json";
        private static final String REDIS_HOST = "[YOUR REDIS HOST]";

    ...

*   `PROJECT_ID`: Your Google Cloud project ID. See [here](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects) for information on locating your project ID.
*   `GCS_BUCKET_NAME`: This is the Cloud Storage bucket you created in the section above titled: Upload JSON object to Cloud Storage bucket.
*   `REDIS_HOST`: The IP address of the MemoryStore for Redis instance you created above. See the section above for details on how to get the IP address of the
    Memorystore for Redis instance.

Now save the file and exit (using Ctrl+O and then Ctrl+X, if you’re using nano). Before we run the program, let’s explore the key parts of the code to see how it’s instrumented.

Here’s the relevant part of the main function:

```java
public static void main(String[] args) throws IOException, InterruptedException {
    configureOpenCensusExporters();

    // initialize jedis pool
    jedisPool = new JedisPool(REDIS_HOST);

    try (Scope ss = tracer.spanBuilder("In main").startScopedSpan()) {

        // do initial read from Cloud Storage
        String jsonPayloadFromGCS = readFromGCS();

        // now write to Redis
        writeToCache(jsonPayloadFromGCS);

        // read from Redis
        String jsonPayloadFromCache = readFromCache();

        if (jsonPayloadFromCache.equals(jsonPayloadFromGCS)) {
            System.out.println("SUCCESS: Value from cache = value from Cloud Storage");
        } else {
            System.out.println("ERROR: Value from cache != value from Cloud Storage");
        }
    }
```

Notice the `try` block with the call to `spanBuilder`. This illustrates how the program uses OpenCensus to perform tracing. The entire call chain starting with the `main` function is instrumented in this way.

The program also configures Cloud Trace as the tracing backend:

```java
private static void configureOpenCensusExporters() throws IOException {
    TraceConfig traceConfig = Tracing.getTraceConfig();

    // For demo purposes, let's always sample.
    traceConfig.updateActiveTraceParams(
        traceConfig.getActiveTraceParams().toBuilder().setSampler(Samplers.alwaysSample()).build());

    // Create the Cloud Trace exporter
    StackdriverTraceExporter.createAndRegister(
        StackdriverTraceConfiguration.builder()
            .setProjectId(PROJECT_ID)
            .build());
}
```

**Note:** For more information on OpenCensus, visit [https://opencensus.io/](https://opencensus.io/).

Now run the following commands to build and run the program:

    $ mvn package -DskipTests

    $ mvn exec:java -Dexec.mainClass=com.example.memorystore.App

You should see output similar to the following:

    SUCCESS: Value from cache = value from Cloud Storage
    Exiting in 15s...
    14s...
    13s...
    12s...
    11s...
    10s...
    ...

## Viewing traces in Cloud Trace UI

After running the program, navigate to the Cloud Trace console:

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image5.png)

Click **Trace List**, and you should see a table similar to the following:

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image6.png)

Recognize the “In main” string? This is from the code you just edited. If you click the “In main” string, you’ll be taken to a drill-down view that shows more information about the call chain, along with other useful information such as call latencies.

![](https://storage.googleapis.com/gcp-community/tutorials/memorystore-oc/image2.png)

As you would expect, the latency for calls to Cloud Memorystore for Redis is much lower than that for calls to Cloud Storage.

## Cleaning up

Since this tutorial uses multiple Google Cloud components, be sure to delete the associated resources once you are done.

## Next steps

What you saw in this tutorial is just the tip of the iceberg when it comes to the instrumentation possibilities with OpenCensus. For more details on how to implement observability in your applications, visit [https://opencensus.io](https://opencensus.io).
