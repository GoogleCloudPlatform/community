---
title: Measure Cloud Spanner performance using JMeter
description: Evaluate Cloud Spanner for custom workloads using the JMeter JSR-223 Sampler.
author: shashank-google,somanishivam
tags: spanner, cloud spanner, evaluation, migration, performance test, mutation, client library, java
date_published: 2022-11-08
---

Shashank Agarwal, Shivam Somani | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Spanner](https://cloud.google.com/spanner) is a fully managed, horizontally scalable, transactional, SQL-compliant
database service. 

Before you migrate to Cloud Spanner, you might want to run performance tests to evaluate its cost and latency. In this tutorial,
you do performance testing with Cloud Spanner before making application code changes and migrating data.

[Apache JMeter](https://jmeter.apache.org/) is a popular open source tool for load testing. It includes scriptable
samplers in JSR 223-compatible languages, such as Groovy and BeanShell. In this tutorial, you use the JSR 223 Sampler,
which can execute operations or query on spanner database using [Java client API and Mutation](https://cloud.google.com/spanner/docs/modify-mutation-api#java).

This document demonstrates JMeter performance tests using an example Cloud Spanner schema. You use features like [mutations](https://cloud.google.com/spanner/docs/modify-mutation-api) and
[parallel reads (partitioned selects)](https://cloud.google.com/spanner/docs/reads#read_data_in_parallel)
using JDBC Sampler. 

**Note:** This is continuation of [previous article](https://cloud.google.com/community/tutorials/jmeter-spanner-performance-test) regarding Spanner Performance tests using JMeter via JDBC and DMLs.

## Costs

This guide uses billable components of Google Cloud, including the following:

* Compute Engine (for running JMeter)
* Cloud Spanner

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your
projected usage.

## Objectives

* Determine whether Cloud Spanner is suitable for an existing workload, before application code changes.
* Write a performance test for your workload on Cloud Spanner using JMeter.
* Estimate the number of Cloud Spanner nodes needed (and therefore cost).
* Test the performance of frequent queries and transactions.
* Demonstrate the ability to scale horizontally.
* Explain optimizations needed for schema and SQL queries.
* Determine latency of select, insert, update, and delete operations with Cloud Spanner.

## Use cases

Possible use cases for doing performance tests with JMeter:

* You want to consolidate current multi-sharded relational database management systems into Cloud Spanner.
* You have a workload that varies with spikes of activity, and you need a database that scales to meet the demand.
* You want to standardize on Cloud Spanner for different applications.

## Limitations

This document is limited to Java Client Library and does not include other languages like Python.

Even if you use JMeter performance tests, you should also do application-based performance tests later.

## Design considerations for Cloud Spanner performance tests

You run performance tests to understand application behavior. Consider the factors mentioned [here](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/jmeter-spanner-performance-test/index.md#design-considerations-for-cloud-spanner-performance-tests) when deciding
how to design and run tests that can answer your specific questions.

## Preparing for tests

Before you begin writing performance tests, make the following preparations

1. Identify top SQL queries. Determine the latency, frequency, and average number of rows returned or updated for each
   of the top queries. This information will also serve as a baseline for the current system.
2. Determine the Cloud Spanner region or multi-region deployment. Ideally, load should be generated from Cloud Spanner’s
   leader region for minimum latency and best performance. For more information, see
   [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations).
3. Estimate the range of Cloud Spanner nodes required for the workload. We recommend that you have at
   least 2 nodes for linear scaling.
4. [Request quota](https://cloud.google.com/spanner/quotas#increasing_your_quotas) so that you have enough surplus quota for
   Cloud Spanner nodes on a given region or multi-region. Changes in quota can take up to 1 business day. Although it depends on
   workload, asking for a quota of 100 nodes for a performance test can be reasonable.
5. Creating [schema](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/jmeter-spanner-performance-test/index.md#creating-a-cloud-spanner-schema) for Cloud Spanner. 

## Creating a Cloud Spanner schema
This example uses the database `Singers`, which is created with the following schema:

    CREATE TABLE Singers (
      SingerId   STRING(36) NOT NULL,
      FirstName  STRING(1024),
      LastName   STRING(1024),
      SingerInfo BYTES(MAX),
    ) PRIMARY KEY (SingerId);
    
    CREATE TABLE Albums (
      SingerId     STRING(36) NOT NULL,
      AlbumId      STRING(36) NOT NULL,
      AlbumTitle   STRING(MAX),
    ) PRIMARY KEY (SingerId, AlbumId),
      INTERLEAVE IN PARENT Singers ON DELETE CASCADE;
    
    CREATE TABLE Songs (
      SingerId     STRING(36) NOT NULL,
      AlbumId      STRING(36) NOT NULL,
      TrackId      STRING(36) NOT NULL,
      SongName     STRING(MAX),
    ) PRIMARY KEY (SingerId, AlbumId, TrackId),
      INTERLEAVE IN PARENT Albums ON DELETE CASCADE;

Refer [previous article](https://cloud.google.com/community/tutorials/jmeter-spanner-performance-test) for more details on schema designing. 

## Set up JMeter

JMeter provides a GUI for easy development of tests. After tests are developed, use the command line to run the
JMeter tests. You can create a VM (in the same region as Cloud Spanner’s Leader) with the GUI enabled, so the same VM
instance can be used for development and execution of tests.

You can use a local workstation for test development, too. Don't use a local workstation to run
performance tests, because network latency can interfere with the tests.

### Installation

1.  Download and install [JMeter](https://jmeter.apache.org/download_jmeter.cgi) 5.3 or higher, which requires Java 8 or higher.
1.  Install [Maven](https://maven.apache.org/install.html), which is used to download Cloud Spanner client libraries.
1.  In a command shell, go to an empty directory, where you will keep JMeter dependencies.
1.  Download the Cloud Spanner JDBC library and dependencies:

        mvn dependency:get -Dartifact=com.google.cloud:google-cloud-spanner:RELEASE -Dmaven.repo.local=.

1.  Move the downloaded JAR files into a folder for JMeter to load in its classpath:

    Linux:
    
        find . -name *.jar -exec mv '{}' . \;

    Windows:

        for /r %x in (*.jar) do copy "%x" .

### Set up authentication for JMeter

JMeter uses Cloud Spanner JDBC client libraries to connect. It
supports [various authentication mechanisms](https://github.com/googleapis/google-cloud-java#authentication), including
service accounts. For simplicity, this example uses application default credentials. For detailed
steps, see [the Cloud Spanner setup documentation](https://cloud.google.com/spanner/docs/getting-started/set-up).

In summary, you need to set up `gcloud` and run the following command to store credentials locally:

    gcloud auth application-default login

## JMeter basics

JMeter is a highly configurable tool and has various components from which you can choose. This section provides
a basic overview of how to create a JMeter test along with some minimal configurations that you can use as a base for your tests. 
Also, it shows how to configure sample jmeter test linked below.

### Configuring connection parameters

As shown in the following screenshot, within each JMeter test, you need to provide connection parameters, which are used by the Java Client
library to connect to Cloud Spanner.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/01_Connection_Params.png)

* `project-id`: Google Cloud project ID
* `instance-id`: Cloud Spanner instance ID
* `db`: Cloud Spanner database name

The following parameters may not need to be changed; they will be passed from the command line, and default values are used when
testing from JMeter graphical user interface.

* `threads`: Number of parallel threads per thread group, increasing stress on target.
* `loops`: Number of times each thread should loop, extending duration of tests.

### Thread groups

[Thread group](https://jmeter.apache.org/usermanual/test_plan.html#thread_group) represents a test case containing a collection of samplers, each sampler is executed sequentially. It can be configured with a number of parallel threads (aka users) for that test.

Within the thread group samplers are added which will call spanner.


### JSR223 request sampler

JMeter does not have a built-in Spanner compatible sampler. Therefore you need to write custom code in Groovy / Java using JSR223 sampler, to interact with Spanner.


### Connection configuration

Creating a connection is a resource heavy operation, hence you need to create a connection pool one time and cache the connection object in-memory. To do this you should use a special component called “setUp Thread Group” as shown in the screenshot below. 

This thread group gets executed before any other thread groups.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/02_SetUp_Thread.png)


Within this thread group create a JSR233 Sampler which creates the connection object one-time and stores it in memory (as dbClient property). Later the same object is fetched by the tests to connect to Spanner.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/03_Connection_setUp_thread.png)


Sample code as below:


	 // Instantiates a client
    	SpannerOptions options = SpannerOptions.newBuilder().build();
    	Spanner spanner = options.getService();

	DatabaseClient dbClient = spanner.getDatabaseClient(DatabaseId.of(projectId, instanceId, databaseId));
	props.put("spanner",spanner);
    	props.put("dbClient",dbClient);


Similarly, you should also create a tearDown thread group with a sampler to close the connection as shown in screenshot below.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/04_Teardown_Thread.png)

### Listeners

You can add an aggregate report (or other types of reports) after all the thread groups. This will show staistics from the
JMeter graphical user interface (GUI) in real time for all of the samplers. However, we don't recommend running performance
tests in GUI mode, because the JMeter GUI can be slow. You can use it for test development purposes, though.

We recommend running tests in command-line mode, which generates HTML reports with the different JMeter reports.

## Loading initial data into Cloud Spanner

Before you start doing performance tests, you need to initialize the database with seed data. We recommend that you
load the volume of rows in each table, representative of current production data size.

Refer [previous article](https://cloud.google.com/community/tutorials/jmeter-spanner-performance-test) for more details on this topic. 
For simplicity we will mock seed data using JMeter itself.

### Using JMeter to mock seed data

Sometimes it is not simple to import existing data into Cloud Spanner. Mock data can be generated by writing insert queries in JMeter.

Below is an example `Spanner-Init-Load.jmx` used to load sample schema. You will need to update 
connection parameters as described previously.

#### Spanner-Init-Load.jmx

Download [Spanner-Init-Load.jmx here](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/jmeter-spanner-performance-test-using-mutation/Spanner-Init-Load.jmx) 
test generates random data hierarchically into `Singer`, `Album`, and `Song` tables. Each singer gets a
random number of albums between 0 and 20. Similarly, 0-15 songs per album are generated. Parallel threads (users)
are used to insert data concurrently.

You can run this JMeter test with the following command:

    jmeter -n -t Spanner-Init-Load.jmx -l load-out.csv -Jusers=1000 -Jiterations=1000

Watch the [CPU utilization](https://cloud.google.com/spanner/docs/cpu-utilization#recommended-max) of Cloud
Spanner. Increase the number of nodes and JMeter’s parallel threads (users) to increase the data generation rate. Increase the
iterations count to increase execution time.  

Initial load should be done with randomly generated keys. Using monotonically increasing keys will lead to write 
hotspots and cause a lengthy delay in populating the database.

## Developing performance tests


### Example JMeter test-bed for the target database

Assume that the following baseline needs to be performance-tested:

| Sno | Transactions | Baseline TPS |
| --- | ------------ | ------------ |
| 1. | Spanner Insert using Mutation |  |
| 2. | Spanner Insert using DML |  |
| 3. | Spanner Update using Mutation |  |
| 4. | Spanner Update using DML |  |
| 5. | Spanner Read using Parallel Read |  |
| 6. | Spanner Scan using Read API |  |

Below is the sample JMeter test to simulate the above load. 
You will need to update connection parameters as discussed previously.

#### Spanner-Perf-Test.jmx

Download [Spanner-Performance-Test-Plan.jmx here](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/jmeter-spanner-performance-test-using-mutation/Spanner-Performance-Test-Plan.jmx) 
uses a CSV configuration to get `SingerId`, `AlbumId` and `TrackId` parameters.

The following are the first few lines, for example:

    "singerid","albumid","trackid"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","328e1b6f-a449-42d1-bc8b-3d6ba2615d2f","0002aad0-30e9-4eae-43b1011e"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","43b1011e-d40d-480b-96a2-247636fc7c96","0002aad0-30e9-4eae-5c64c8f2"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","5c64c8f2-0fad-4fe7-9c3a-6e5925e3cbcd","0002aad0-30e9-4eae-328e1b6f"

This CSV can be created using a SQL query such as the following, which randomly selects data from the album table:

    SELECT SingerId,AlbumId,TrackId FROM Songs TABLESAMPLE BERNOULLI (0.1 PERCENT) limit 10000;

There are three thread groups with the transaction as defined previously, as shown in the following screenshot:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/05_Perf_Test_tg.png)

The CSV Read configuration reads data from a CSV file that is being used in all three thread groups.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/06_CSV_Config.png) 

All other thread groups are very similar uses Java Client Library for Spanner Interaction. The following screenshot shows the Insert thread group.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/07_Insert_TG.png)

It is configured to use threads and loops parameters, which can be passed by command line. It contains JSR-223 Sampler, 
which depends on User Parameters and [writes data to tables using Mutation](https://cloud.google.com/spanner/docs/modify-mutation-api#insert-new-roles).

Random User Parameters:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test-using-mutation/08_Insert_Random_Parameters.png)

## Executing performance test

### Sample test execution

Run the test:

    jmeter -n -t Spanner-Performance-Test-Plan.jmx -l test-out.csv -Jthreads=10 -Jloops=100

You can modify the number of users and duration as needed.

The test generates a `test-out.csv` file with raw statistics. You can use the following command to
[create a JMeter report from it](https://jmeter.apache.org/usermanual/generating-dashboard.html#report_only):

    jmeter -g test-out.csv -o [PATH_TO_OUTPUT_FOLDER]

### Collecting performance test results

You gather performance metrics after the test execution.

1. Validate that the test ran according to the requirements defined earlier.
2. Compare results with your success criteria.

We recommend capturing these performance metrics from Spanner monitoring rather than the JMeter report. 

Based on the success criteria, the most important metrics are the following:

1. Operations per second (read and write)
2. Latency at 50th and 99th percentile for different types of operations
3. CPU utilization

The Spanner monitoring dashboard provides this information aggregated at the minute level.  
For custom dashboards or metrics that are not available in standard dashboards, you can
use the [Metrics Explorer](https://cloud.google.com/spanner/docs/monitoring-cloud#create-charts).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project that you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- [Measure Cloud Spanner performance using JMeter via JDBC](https://cloud.google.com/community/tutorials/jmeter-spanner-performance-test)
- [Cloud Spanner schema and data model](https://cloud.google.com/spanner/docs/schema-and-data-model)
- [Schema design best practices](https://cloud.google.com/spanner/docs/schema-design)
- [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations)
- [Introspection tools](https://cloud.google.com/spanner/docs/introspection)
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
