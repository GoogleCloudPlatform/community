---
title: Measure Cloud Spanner performance using JMeter
description: Evaluate Cloud Spanner for custom workloads using the JMeter JDBC Sampler.
author: shashank-google,chbussler,rlota
tags: spanner, cloud spanner, evaluation, migration, performance test, jdbc
date_published: 2021-06-30
---

Shashank Agarwal, Ravinder Lota, Christoph Bussler | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Spanner](https://cloud.google.com/spanner) is a fully managed, horizontally scalable, transactional, SQL-compliant
database service. 

Before you migrate to Cloud Spanner, you might want to run performance tests to evaluate its cost and latency. In this tutorial,
you do performance testing with Cloud Spanner before making application code changes and migrating data.

[Apache JMeter](https://jmeter.apache.org/) is a popular open source tool for load testing. It includes scriptable
samplers in JSR 223-compatible languages, such as Groovy and BeanShell. In this tutorial, you use the JDBC Sampler,
which can trigger queries and simulate transactions on databases.

This document demonstrates JMeter performance tests using an example Cloud Spanner schema. You use JMeter to send
DML (data manipulation language) commands to the database to test its performance. 

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

You can't use JMeter to test non-JDBC Cloud Spanner client-side libraries like Python and R2DBC. You can bypass the
client library using underlying [gRPC](https://cloud.google.com/spanner/docs/reference/rpc)
or [REST](https://cloud.google.com/spanner/docs/reference/rest) APIs, but that is out of scope for this document.

You can't test non-DML features like [mutations](https://cloud.google.com/spanner/docs/modify-mutation-api) and
[parallel reads (partitioned selects)](https://cloud.google.com/spanner/docs/reads#read_data_in_parallel)
using JDBC Sampler. In such cases, you can
[embed custom Java code](https://stackoverflow.com/questions/21266923/using-a-jmeter-jdbc-connection-in-java-code)
using JSR223 Sampler, but that is out of scope for this document.

Even if you use JMeter performance tests, you should also do application-based performance tests later.

## Design considerations for Cloud Spanner performance tests

You run performance tests to understand application behavior. Consider the following factors when deciding
how to design and run tests that can answer your specific questions.

### Transactions per second (TPS)

TPS metrics should be based on your application workload requirements, mostly to support the peak load.

For example, 7,000 read operations per second, 4,000 insert operations per second, and 2,000 update operations per
second comes to an overall rate of 13,000 transactions per second (TPS).

### Query latency

You should establish expected response time for different DMLs as success criteria. This can be either based on
your business SLAs or current database response time in the case of an existing application.

### Sizing: Number of nodes

Sizing of the Spanner cluster depends on the data volume, TPS, and latency requirements of the application workload.

[CPU utilization](https://cloud.google.com/spanner/docs/cpu-utilization)
is another important factor when deciding the optimal number of nodes.

You can increase or decrease the initial cluster size to maintain the recommended 45% CPU utilization for multi-region
deployment and 65% for regional deployment.

### Test Cloud Spanner Autoscaler

[Cloud Spanner Autoscaler](https://github.com/cloudspannerecosystem/autoscaler) is a solution to elastically scale
Cloud Spanner. Use JMeter to simulate workloads that vary with spikes of activity to tune autoscaling scaling parameters.

## Preparing for tests

Before you begin writing performance tests, make the following preparations:

1. Identify top SQL queries. Determine the latency, frequency, and average number of rows returned or updated for each
   of the top queries. This information will also serve as a baseline for the current system.
1. Determine the Cloud Spanner region or multi-region deployment. Ideally, load should be generated from Cloud Spanner’s
   leader region for minimum latency and best performance. For more information, see
   [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations).
1. Estimate the range of Cloud Spanner nodes required for the workload. We recommend that you have at
   least 2 nodes for linear scaling.
4. [Request quota](https://cloud.google.com/spanner/quotas#increasing_your_quotas) so that you have enough surplus quota for
   Cloud Spanner nodes on a given region or multi-region. Changes in quota can take up to 1 business day. Although it depends on
   workload, asking for a quota of 100 nodes for a performance test can be reasonable.

## Creating a Cloud Spanner schema

This section assumes that you are migrating an existing application from a common RDBMS database such as MySQL, Postgresql, SQL Server, or
Oracle.

For information about modeling your schema, see the [schema design best practices](https://cloud.google.com/spanner/docs/schema-design).

Keep the following in mind:

-  Cloud Spanner needs primary keys to be generated from the application layer. Also, monotonically increasing primary keys will
   introduce [hotspots](https://cloud.google.com/spanner/docs/schema-design#primary-key-prevent-hotspots).
   [Using a UUID](https://cloud.google.com/spanner/docs/schema-design#uuid_primary_key) can be a good alternative.
-  Use an interleaved table to improve performance where most (more than 90%) of the access is using join to the parent
   table. Interleaving must be created from the start; you can't change table interleaving after the tables have been
   created.
-  Secondary indexes on monotonically increasing values (such as indexes on a timestamp) may introduce hotspots.
-  Secondary indexes can use [storing clauses](https://cloud.google.com/spanner/docs/secondary-indexes#storing-clause)
   to improve performance of certain queries.
-  Use the `STRING` data type if you need to have
   [greater precision than `NUMERIC`](https://cloud.google.com/spanner/docs/storing-numeric-data#recommendation_store_arbitrary_precision_numbers_as_strings).

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

        mvn dependency:get -Dartifact=com.google.cloud:google-cloud-spanner-jdbc:RELEASE -Dmaven.repo.local=.

1.  Move the downloaded JAR files into a folder for JMeter to load in its classpath:

    Linux:
    
        find . -name *.jar -exec mv '{}' . \;

    Windows:

        for /r /Y %x in (*.jar) do copy "%x" .\

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

### JMeter test plan

JMeter has a hierarchical structure to the tests, with a top node
called the [*test plan*](https://jmeter.apache.org/usermanual/test_plan.html). It consists of one or more thread groups, logic
controllers, sample generating controllers, listeners, timers, assertions, and configuration elements. Because a test plan
is the top-level configuration element, saving a test plan to disk also saves all nested objects, and the resulting
file is saved with a `.jmx` filename extension.

For simplicity, it's sufficient to have the top-level test plan contain a single thread group, which in turn contains
one or more samplers. There can be multiple samplers (and other components) within a thread group; each is
executed serially per thread.

Test plans and thread groups can also have configuration elements such as a JDBC connection or CSV data reader. Configurations can
be shared with child nodes.

### Configuring connection parameters

As shown in the following screenshot, within each JMeter test, you need to provide connection parameters, which are used by the JDBC
library to connect to Cloud Spanner.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/01_Connection_Params.png)

* `project_id`: Google Cloud project ID
* `instance`: Cloud Spanner instance ID
* `db`: Cloud Spanner database name
* `connections`: Cloud Spanner [sessions](https://cloud.google.com/spanner/docs/sessions). You should have 1 session per thread.
* `grpc_channel`: There can be a maximum of 100 sessions per gRPC channel.

The following parameters may not need to be changed; they will be passed from the command line, and default values are used when
testing from JMeter graphical user interface.

* `users`: Number of parallel threads per thread group, increasing stress on target.
* `iterations`: Number of times each thread should loop, extending duration of tests.

### JDBC connection configuration

The parameters listed above are used for the JDBC connection configuration.

For a complete list of JDBC properties, see the 
[JdbcDriver documentation](https://javadoc.io/doc/com.google.cloud/google-cloud-spanner-jdbc/latest/com/google/cloud/spanner/jdbc/JdbcDriver.html).

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/02_JDBC_Connection_Params.png)

The connection pool variable (`conn_pool`) is used by JDBC samplers to obtain a connection. The JDBC connection URL is as follows:

    jdbc:cloudspanner:/projects/${project_id}/instances/${instance}/databases/${db}?minSessions=${connections};maxSessions=${connections};numChannels=${grpc_channel}

You can use [additional configurations](https://cloud.google.com/spanner/docs/use-oss-jdbc#session_management_statements) such as
`READ_ONLY_STALENESS` as needed.

### Thread groups

A Thread group represents a group of users, and the number of threads you assign a thread group is equivalent to the
number of users that you want querying Cloud Spanner.

The following screnshot shows an example thread group configuration:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/03_thread_groups.png)

If you want a thread group to run for a given duration, then you can change the beahvior as shown in the following screenshot:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/04_thread_groups_2.png)

### JDBC request sampler

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/05_jdbc_sampler.png)

Using JDBC Sampler you can fire SQL Queries. Using Prepared Select or Prepared Update is recommended as it
is [more performant](https://cloud.google.com/spanner/docs/sql-best-practices#query-parameters) on Cloud Spanner.

### Listeners

You can add an aggregate report (or other types of reports) after all the thread groups. This will show stats from the
JMeter graphical user interface (GUI) in real time for all the samplers. However, we don't recommend running performance
tests in GUI mode, because the JMeter GUI can be slow. You can use it for test development purposes, though.

We recommend running tests in command-line mode, which generates HTML reports with the different JMeter reports.

## Loading initial data into Cloud Spanner

Before you start doing performance tests, you will need to initialize the database with seed data. It is recommended to
load the volume of rows in each table, representative of current production data size.

Typically you can use dataflow jobs
for [Importing data from non-Cloud Spanner databases](https://cloud.google.com/spanner/docs/import-non-spanner)

However, sometimes you cannot do that because of schema changes with Cloud Spanner. Therefore an alternative could be to
mock seed data using JMeter.

**How much data should I load?**

Data loading prepares Cloud Spanner to create splits (shards) and distribute different nodes as leaders for each split.
More details about database splits
is [here](https://cloud.google.com/spanner/docs/schema-and-data-model#database-splits).

Volume of data depends on the SQL queries you want to do performance tests. Main focus is to load those tables which
will be used by read or write queries. Ideally it should be similar in volume as production data. In addition data might
need to be massaged to fit into potentially modified Cloud Spanner schema.

**How to reset my tests ?**

Ideally you should reset your database to the same seed data for comparison between multiple test executions. You can
use backup/restore (or export/import)  to initialize each run to the same initial dataset. The latter is better if
different configurations are tested.

### Using JMeter to mock seed data

Sometimes it is non trivial to import existing data into Cloud Spanner due to various reasons like data massaging,
operations difficulties. Hence, mock data can be generated by writing insert queries in JMeter.

Below is an example Spanner-Initial-Load.jmx used to load sample schema. You will need to update 
[connection parameters](#connection) as discussed previously.

#### [Spanner-Initial-Load.jmx](Spanner-Initial-Load.jmx)

The above test will generate random data hierarchically into Singer, Album and Song tables. Each Singer will get a
random number of Albums between 0-20. Similarly, 0-15 Songs per Album will get generated. Parallel threads (aka users)
will be used to insert data concurrently.

You can run this JMeter test with the following command:

    jmeter -n -t Spanner-Initial-Load.jmx -l load-out.csv -Jusers=1000 -Jiterations=1000

Watch out for [cpu utilization](https://cloud.google.com/spanner/docs/cpu-utilization#recommended-max) of Cloud
Spanner. Increase the number of nodes and JMeter’s parallel threads (users) to increase data generation rate. Increase
iterations count to longer execution time.  

Initial load should be done with randomly generated keys. Using monotonically increasing keys will lead to write 
hotspotting and cause a lengthy delay in populating the database.

## Developing performance tests

Guidelines to develop performance tests:

1. Target to configure performance tests such that it generates transactions per second (TPS) similar to current
   database (baseline). Later in the execution phase, increase the number of users (load) to simulate scaling.
2. Prefer to have only one transaction per thread group. This will allow you to throttle load for that transaction
   independent of other transactions. A transaction could be composed of single or multiple sql queries. \
   For example, it is fine to have just a single select/insert/update query in a thread group. if that compares evenly
   with a transaction in your current database (baseline).
3. Determine the transactions per second (TPS) in the current database (baseline) for each DML operation and throttle
   load accordingly. In other words, sometimes even with one user in the thread group, there is far higher TPS than
   baseline. If so, then use [timers](https://jmeter.apache.org/usermanual/component_reference.html#timers) to introduce
   delay, as needed to tone down the TPS close to baseline.
4. Use [parameterized queries](https://cloud.google.com/spanner/docs/sql-best-practices#query-parameters) for better
   performance.
5. [Tune SQL Queries](https://cloud.google.com/spanner/docs/query-syntax) by adding relevant hints as needed.
    1. Cloud Spanner’s GCP Console UI can lead to longer query execution time, especially when result size is large.
       Therefore you can use [gcloud](https://cloud.google.com/sdk/gcloud/reference/spanner/databases/execute-sql)
       or [Spanner CLI](https://github.com/cloudspannerecosystem/spanner-cli) as alternatives to time sql queries
       accurately.
    2. Use [query execution plans](https://cloud.google.com/spanner/docs/query-execution-plans) to identify query
       bottlenecks and tune them accordingly.
    3. [Add indexes](https://cloud.google.com/spanner/docs/secondary-indexes) as needed to improve performance of select
       queries.
    4. Use [FORCE_INDEX hint](https://cloud.google.com/spanner/docs/query-syntax#table-hints) for all queries as it can
       take upto a few days before the query optimizer starts to automatically utilize the new index.
    5. Use GROUPBY_SCAN_OPTIMIZATION to make queries with GROUP BY faster.
    6. Use [join hints](https://cloud.google.com/spanner/docs/query-syntax#join-hints) to optimize join performance, as
       needed.
6. If needed, export query parameter values into a csv. Then
   use [csv config](https://jmeter.apache.org/usermanual/component_reference.html#CSV_Data_Set_Config) in JMeter to
   supply parameters from the csv file.

### Sample JMeter test for Singers schema

Let us assume the following baseline needs to be performance tested.

| Sno | Transactions | Baseline TPS |
| --- | ------------ | ------------ |
| 1. | select AlbumTitle from Albums where SingerId = ? and AlbumTitle like ? | 7000 |
| 2. | select SingerId, AlbumId, TrackId, SongName from Songs where SingerId = ? and AlbumId = ? order by SongName | 5000 |
| 3. | update Singers set SingerInfo = ? where SingerId = ? | 1000 |

Below is the Sample JMeter test to simulate the above load. You will need to update 
[connection parameters](#connection) as discussed previously.

#### [Spanner-Perf-Test.jmx](Spanner-Perf-Test.jmx)

Note: It uses a csv config to get SingerId and AlbumId parameters, example top few lines as below.

    "singerid","albumid"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","328e1b6f-a449-42d1-bc8b-3d6ba2615d2f"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","43b1011e-d40d-480b-96a2-247636fc7c96"
    "0002aad0-30e9-4eae-b1a0-952ebec9de76","5c64c8f2-0fad-4fe7-9c3a-6e5925e3cbcd"

Above csv can be created using a sql query such as below. This is to randomly select data from the album table.

    SELECT SingerId,AlbumId FROM Albums TABLESAMPLE BERNOULLI (0.1 PERCENT) limit 10000;

There are three thread groups with the transaction as defined previously, as shown in the following screenshot:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/06_test-ss-1.png)

The CSV Read config reads data from a csv file which is being used in all the three thread groups. All the three
thread groups are very similar. The following screenshot shows the Search Albums thread group.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/07_test-ss-2.png)

It is configured to use users and duration parameters which can be passed by command line (if not then defaults will be
used). It contains one JDBC Sampler Search Album which depends on User Parameters and Timer.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/08_test-ss-3.png)

Search Album jdbc sampler as above triggers sql query as screenshot above. It populates query parameters using 
variable(s) as below:

`${singerid} -- obtained from CSV Read`  
`${title} -- obtained from User Parameters`

Finally a timer is configured to throttle load to meet the requirement. It need to be supplied with transactions 
**per minute**, therefore 7K (TPS) * 60 = 420,000 (TPM)

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/09_test-ss-4.png)

## Executing performance test

Guidelines for executing the tests, for best results:

1. Execute tests from the same Cloud Spanner region for a regional spanner and “leader” region for multi-region Cloud
   Spanner instances.
2. It is recommended to execute JMeter tests from command line / non-gui mode.
3. Run each test at least 3 times to even out random differences.
4. Warm up Cloud Spanner before running tests (as in production).
5. It is recommended to execute tests for long enough such that TPS is stable. It depends on the workload, for example
   having at least a 15 min test can ensure that enough ramp up time is available.
6. Scaling Cloud Spanner can take some time to stabilize. It is recommended to generate load on Cloud Spanner for faster
   stabilization.
7. Ensure that client machine running JMeter has enough resources. JMeter is a CPU-intensive process.
8. Increase
   JMeter’s [jvm heap size](https://www.blazemeter.com/blog/9-easy-solutions-jmeter-load-test-%E2%80%9Cout-memory%E2%80%9D-failure)
   , if needed.
9. It is recommended to run multiple jmeter instances in parallel and/or
   use [remote testing](https://jmeter.apache.org/usermanual/remote-test.html) for horizontal scaling of JMeter. Often a
   single instance of JMeter is not able to produce enough load on a multi-node Cloud Spanner instance.
10. Ensure Cloud Spanner is not more
    than [recommended CPU threshold](https://cloud.google.com/spanner/docs/cpu-utilization#recommended-max), i.e.
    &lt;65% for regional and &lt;45% for multi regional.
11. Plan for long running tests (2 hours or more) to verify sustained performance. This is because Cloud Spanner can
    start [system tasks](https://cloud.google.com/spanner/docs/cpu-utilization#task-priority) which may have performance
    impact.

### Sample test execution

For executing the test developed in the previous section, the following command needs to be executed. Number of users
and duration can be passed using the command line as needed.

    jmeter -n -t Spanner-Perf-Test.jmx -l test-out.csv -Jusers=100 -Jduration=900

[Optional] Once execution is complete it will generate a test-out.csv file with raw stats. If you want, you can execute
the below command
to [create a JMeter report from it](https://jmeter.apache.org/usermanual/generating-dashboard.html#report_only).

    jmeter -g test-out.csv -o <Path to output folder>

### Collecting performance test results

You will need to gather performance metrics after the test execution.

1. Validate that the test ran as per the requirements defined earlier in section 1.1 TPS and latency metrics will help
   identify optimization opportunities for query tuning and cluster sizing.
2. Compare results with the success criteria defined in section 1.1.

We suggest capturing these performance metrics from Spanner monitoring rather than JMeter report. JMeter provides this
information with added latency for each query execution depending on how busy the VM has been. Therefore it will not be
the true measure of Spanner response time.

Based on the success criteria, the most important metrics are the following:

1. Operations/sec (read/write).
2. Latency at 50th and 99th percentile for different types of operations.
3. CPU utilization

Spanner monitoring dashboard provides this information at minute level aggregate.  
For custom dashboards or metrics that are not available in standard dashboards you can
use [metrics explorer](https://cloud.google.com/spanner/docs/monitoring-cloud#create-charts).

**Operations/sec:**

Spanner dashboard provides information about the read & write operations executing on the spanner instance.
For example, the following chart shows a total TPS of 43744 per second for the selected duration.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/10_results-ss-1.png)

**Latency**

An example of read and write operations latency at 50th and 99th percentile is captured in the following chart.  
**Note:** You can also get **95th percentile** latency from [Cloud Monitoring](https://cloud.google.com/spanner/docs/monitoring-cloud)

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/11_results-ss-2.png)

*Latency metrics have been redacted in above screen shot.*

In addition you can use [introspection tools](https://cloud.google.com/spanner/docs/introspection) to investigate issues
with your database. Use query statistics to know which queries are expensive, run frequently or scan a lot of data. Read
statistics and Transaction statistics to investigate the most common and most resource-consuming read and writes.

Sometimes writes can be competing and can result in higher latency. You can check
the [lock statistics](https://cloud.google.com/spanner/docs/introspection/lock-statistics) to get clarity on wait time
and higher latency and
apply [best practice](https://cloud.google.com/spanner/docs/introspection/lock-statistics#applying_best_practices_to_reduce_lock_contention)
to reduce the lock time.

**CPU utilization**

This metric is important for understanding whether the cluster is under-utilized or over-utilized.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-spanner-performance-test/12_results-ss-3.png)

This information can be used to further optimize the cluster size. For details, see
[Investigating high CPU utilization](https://cloud.google.com/spanner/docs/introspection/investigate-cpu-utilization).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project that you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- [Cloud Spanner schema and data model](https://cloud.google.com/spanner/docs/schema-and-data-model)
- [Schema design best practices](https://cloud.google.com/spanner/docs/schema-design)
- [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations)
- [Introspection tools](https://cloud.google.com/spanner/docs/introspection)
- [Handling auto-incrementing keys data migration](https://cloud.google.com/community/tutorials/db-migration-spanner-handle-increasing-pks)
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
