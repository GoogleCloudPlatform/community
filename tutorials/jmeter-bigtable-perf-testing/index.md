---
title: Measure Cloud Bigtable performance using JMeter
description: Evaluate Cloud BigTable for custom workloads using the JMeter.
author: shashank-google,shubhamgoogle,jhambleton
tags: bigtable, hbase, evaluation, migration, performance test, jmeter
date_published: 2022-06-15
---

Shashank Agarwal, Jordan Hambleton, Shubham Chawla | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>


[Cloud Bigtable](https://cloud.google.com/bigtable) is a fully managed, scalable NoSQL database as service for large analytical and operational workloads with up to 99.999% availability.

Before you adopt Cloud Bigtable, you might want to evaluate its cost and latency by performance testing. In this tutorial, you will do the performance testing with Cloud Bigtable using JMeter.

[Apache JMeter](https://jmeter.apache.org/) is a popular open source tool for load testing. It includes scriptable samplers in languages, such as Groovy and BeanShell. In this tutorial, you will use the JSR-233 Sampler to simulate load on Cloud Bigtable using the [bigtable-hbase-1.x](https://cloud.google.com/bigtable/docs/samples-hbase-java-hello) client library.


## Costs

This guide uses billable components of Google Cloud, including the following:

* Compute Engine (for running JMeter)
* Cloud Bigtable

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.


## Objectives

* Determine whether Cloud Bigtable is suitable for a workload, before application code changes.
* Write a performance test for your workload on Cloud Bigtable using JMeter.
* Estimate the number of Cloud Bigtable nodes needed (and therefore cost).
* Test the performance of frequent queries and mutations.
* Demonstrate the ability to scale horizontally.
* Explain optimizations needed for schema and SQL queries.
* Determine latency of read, write or scan operations with Cloud Bigtable.


## Use cases

Possible use cases for doing performance tests with JMeter:

* You want to migrate current Cassandra, HBase, or other NoSQL use cases to Cloud Bigtable.
* You want to evaluate performance of a data model and need to ensure that Bigtable scales linearly to meet demand.
* You want to standardize on Cloud Bigtable for multiple applications.
* Test Cloud Bigtable autoscaling response time and speed.


## Limitations

Below are a few limitations with JMeter and testing with Bigtable: 

* You cannot use JMeter to test non-Java Cloud Bigtable client side libraries. Although, you can bypass the client library using underlying [gRPC](https://cloud.google.com/bigtable/docs/reference/service-apis-overview#grpc) or [REST APIs](https://cloud.google.com/bigtable/docs/reference/service-apis-overview#rest), that is out of scope for this document.

Even if you use JMeter performance tests, you should also perform application-based testing before you go to production.


## Design considerations for Cloud Bigtable performance tests

You run performance tests to understand application behavior. Consider the following factors when deciding how to design and run tests that can answer your specific questions.


### Queries Per Second (QPS)

You should take into consideration the target QPS for read, write, update and scan operations on each of the tables. If you are migrating from an existing datastore such as HBase, then it might be worth looking into the performance numbers of the deployed service. 


### Query latency

You should establish expected response time for different operations as success criteria. This can be either based on your business SLAs or current datastore response time in the case of an existing application.


### Sizing / Number of nodes

Sizing of the Bigtable cluster depends on the data volume, QPS, and latency requirements of the application workload.

[CPU utilization](https://cloud.google.com/bigtable/docs/monitoring-instance#cpu) is another important factor when deciding the optimal number of nodes.

You can increase or decrease the initial cluster size to maintain the recommended CPU utilization. Alternatively you can choose to opt for [autoscaling](https://cloud.google.com/bigtable/docs/autoscaling) deployment.


## Preparing for tests

Before you begin writing performance tests, make the following preparations:

1. Identify top read and write operations. Determine the latency, frequency, and average number of rows returned for each of the operations. This information will also serve as a baseline for the current system.
2. Determine the Cloud [Bigtable zone](https://cloud.google.com/bigtable/docs/locations) before deployment. You cannot change the location after you create the instance. Ideally, load should be generated from the same region for minimum latency and best performance.
3. Estimate the range of Cloud Bigtable nodes required for the workload. 
4. [Request quota](https://cloud.google.com/bigtable/quotas#quota-increase) so that you have enough surplus quota for Cloud Bigtable nodes on a given region or multi-region. 


## Creating a Cloud Bigtable schema

For this document we will assume an example use case of real time App Install & Usage data platform for operating enterprise services. The service stores and serves in real time: app installs and app events for observability. The system monitoring apps is called the app health service. 


### High-level schema

enterprise_app_installs: This table records live app installations with a row key that includes the app identifier and UUID of the unique application install. The row key design serves millisecond response time for lookup and allows for identifying installations by app.

```text
	rowkey: 		appId#uuid
	cf1:owner		<owner_id>
	cf1:description		<user description>
	cf1:app_status		<status_id>
	cf1:app_category	<app_category>
	cf1:created_ts		<created_ts>
```

enterprise_app_event_history: This table stores app activity events for each user's session. Activity events are captured at key operations like login, logout, navigation, inventory analysis, etc. to collect information about important activities performed by the user (i.e. app install uuid). Along with that, the event date/time (yyyy-MM-dd'T'HH:mm:ss.SSS) is captured to provide row-level ordering of events based on when they occurred.

```text
	rowkey: 		uuid#eventId#timestamp
	cf1:event_details	<details_of_app_event>
	cf1:memory_usage	<memory_usage_metric>
	cf1:cpu_utilization	<cpu_utilization_metric>
	cf1:event_ts		<event_ts>
```

### DDL

[Install bigtable CLI tool](https://cloud.google.com/bigtable/docs/cbt-overview) (cbt) if you don’t have one already or create tables using UI.

```sh
cbt -instance bt-perf createtable enterprise_app_installs "families=cf1:maxversions=10"
cbt -instance bt-perf createtable enterprise_app_event_history "families=cf1:maxversions=1"
```


## Set up JMeter

JMeter provides a GUI for easy development of tests. After tests are developed, use the command line to run the JMeter tests. You can create a VM with the GUI enabled (or a windows VM), so that the same VM instance can be used for development and execution of tests.

You can use a local workstation for test development, too. Don't use a local workstation to run performance tests, because network latency will interfere with the tests results.


### Installation

1. Download and install [JMeter](https://jmeter.apache.org/download_jmeter.cgi) 5.3 or higher, which requires Java 8 or higher.
2. Install [Maven](https://maven.apache.org/install.html), which is used to download Cloud Bigtable HBase client libraries.
3. In a command shell, go to an empty directory, where you will keep JMeter dependencies.
4. Download the Cloud Bigtable HBase client library and dependencies:

```sh
mvn dependency:get -Dartifact=com.google.cloud.bigtable:bigtable-hbase-1.x-shaded:2.4.0 -Dmaven.repo.local=.
```

5. Move the downloaded JAR files into a folder for JMeter to load in its classpath (ie. `./jars/`): 

Linux

```sh
find . -name *.jar -exec mv '{}' . \;
```

Windows

```sh
for /r %x in (*.jar) do copy "%x" .
```

### Set up authentication for JMeter

JMeter uses Cloud Bigtable HBase client libraries to connect. It supports [various authentication mechanisms](https://github.com/googleapis/google-cloud-java#authentication), including service accounts. For simplicity, this example uses application default credentials. For detailed steps, see [quickstart documentation](https://cloud.google.com/bigtable/docs/creating-test-table).

In summary, you need to set up gcloud and run the following command to store credentials locally:

```sh
gcloud auth application-default login
```

## JMeter basics

JMeter is a highly configurable tool and has various components from which you can choose. This section provides a basic overview of how to create a JMeter test along with some minimal configurations that you can use as a base for your tests.


### JMeter test plan

JMeter has a hierarchical structure to the tests, with a top node called the test plan. It consists of one or more thread groups, logic controllers, sample generating controllers, listeners, timers, assertions, and configuration elements. Because a test plan is the top-level configuration element, saving a test plan to disk also saves all nested objects, and the resulting file is saved with a `.jmx` filename extension.

For simplicity, it's sufficient to have the top-level test plan contain a single thread group, which in turn contains one or more samplers. There can be multiple samplers (and other components) within a thread group; each is executed serially per thread.

Test plans and thread groups can also have configuration elements such as a CSV data reader. Configurations can be shared with child nodes.


### Configuring connection parameters

As shown in the following screenshot within each JMeter test, you need to provide instance parameters, which are used by the bigtable-hbase library to connect to Cloud Bigtable.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/0-instance-config.jpeg)


### Thread groups

[Thread group](https://jmeter.apache.org/usermanual/test_plan.html#thread_group) represents a test case containing a collection of samplers, each sampler is executed sequentially. It can be configured with a number of parallel threads (aka users) for that test.

Within the thread group samplers are added which will call bigtable.


### JSR223 request sampler

JMeter does not have a built-in Bigtable compatible sampler. Therefore you need to write custom code in Groovy / Java using JSR223 sampler, to interact with Bigtable.


### Connection configuration

Creating a connection is a resource heavy operation, hence you need to create a connection pool one time and cache the connection object in-memory. To do this you should use a special component called “setUp Thread Group” as shown in the screenshot below. 

This thread group gets executed before any other thread groups.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/1-connection.jpeg)


Within this thread group create a JSR233 Sampler which creates the connection object one-time and stores it in memory (as btConn property). Later the same object is fetched by the tests to connect to Bigtable.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/2-set-up.jpeg)


Sample code as below:


	import com.google.cloud.bigtable.hbase.BigtableConfiguration;
	import org.apache.hadoop.hbase.client.Connection;

	Connection conn = BigtableConfiguration.connect("${project-id}", "${bigtable-instance-id}");
	OUT.println("Opened Connection:" + conn);
	props.put("btConn", conn);


Similarly, you should also create a tearDown thread group with a sampler to close the connection as shown in screenshot below.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/3-teardown.jpeg)


## Loading initial data into Cloud Bigtable

Before you start doing performance tests, you need to initialize the database with seed data. We recommend that you load the volume of rows in each table, representative of current production data size.

There are [multiple ways](https://cloud.google.com/bigtable/docs/import-export) to import data to Bigtable. However, for testing purposes we can mock data using Jmeter.


### How much data to load

The Bigtable cluster configurations including [storage types](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#storage-types), [application profiles](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#app-profiles), number of [nodes](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#nodes)  and the size of the data set can alter the performance of workload and the test results on the same cluster. Data set size should be picked similar in volume to production data keeping in mind what we are trying to understand about the bigtable cluster’s performance.


### How to reset tests

Ideally, you should reset your database to the same seed data for comparison between multiple test executions. You can use backup/restore (or export/import) to initialize each run to the same initial dataset.


### Using JMeter to mock seed data

Sometimes it is not simple to import existing or mocked up data into Cloud Bigtable. Mock data can be generated by writing insert queries in JMeter.

Below is an example Bigtable-Initial-Load.jmx used to load sample schema. You will need to update connection parameters as described previously.


### **[Bigtable-Initial-Load.jmx](./Bigtable-Initial-Load.jmx)**

The  [Bigtable-Initial-Load.jmx](./Bigtable-Initial-Load.jmx) test generates random data in enterprise_app_installs and enterprise_app_event_history tables as described below. 

table: enterprise_app_installs
<table>
  <tr>
   <td><strong>Column Name</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>rowkey
   </td>
   <td>random string consisting of 5 characters [0-9|a-f] + a random <a href="https://en.wikipedia.org/wiki/Universally_unique_identifier">UUID</a>
   </td>
  </tr>
  <tr>
   <td>cf1:owner
   </td>
   <td>random string consisting of 10 alphabetic and numeric characters as owner id
   </td>
  </tr>
  <tr>
   <td>cf1:description
   </td>
   <td>random string consisting of 40 alphabetic and numeric characters as user description
   </td>
  </tr>
  <tr>
   <td>cf1:app_status
   </td>
   <td>constant string value for all the rows
   </td>
  </tr>
  <tr>
   <td>cf1:app_category
   </td>
   <td>constant string value for all the rows
   </td>
  </tr>
  <tr>
   <td>cf1:created_ts
   </td>
   <td>random date value
   </td>
  </tr>
</table>

table: enterprise_app_event_history
<table>
  <tr>
   <td><strong>Column Name</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>rowkey
   </td>
   <td>random <a href="https://en.wikipedia.org/wiki/Universally_unique_identifier">UUID</a> + a random numeric event id + a random date/time between 2021-2022 (format yyyy-MM-dd'T'HH:mm:ss.SSS) 
   </td>
  </tr>
  <tr>
   <td>cf1:event_details
   </td>
   <td>random string consisting of 40 alphabetic and numeric characters as event details
   </td>
  </tr>
  <tr>
   <td>cf1:memory_usage
   </td>
   <td>random numeric value between 10_000 and 10_000_000
   </td>
  </tr>
  <tr>
   <td>cf1:cpu_usage
   </td>
   <td>random numeric value between 10 and 70
   </td>
  </tr>
  <tr>
   <td>cf1:event_ts
   </td>
   <td>random date/time between 2021-2022 (format yyyy-MM-dd'T'HH:mm:ss.SSS)
   </td>
  </tr>
</table>

You can run this JMeter test with the following command:

```sh
jmeter -n -t Bigtable-Initial-Load.jmx -l load-out-c.csv -Jthreads=100 -Jloops=1000
```

You can use the  [Key Visualizer tool for Bigtable](https://cloud.google.com/bigtable/docs/keyvis-overview) to generate visual reports for your table. This tool will help you analyze your Bigtable usage patterns. Key Visualizer makes it possible to check whether your usage patterns are causing undesirable results, such as hotspots on specific rows or excessive CPU utilization. 

Initial load should be done with randomly generated rowkeys. Using monotonically increasing keys will lead to write hotspots and cause a lengthy delay in populating the table.


## Developing performance tests

* Target to configure performance tests such that they generate transactions per second (TPS) similar to the current database (baseline). Later in the execution phase, increase the number of users (load) to simulate scaling.
* Test with enough data: \
Try to test your instance with roughly the same amount of data as present in your production environment.

* Stay below the recommended storage utilization per node. For details, see [Storage utilization per node](https://cloud.google.com/bigtable/quotas#storage-per-node).

* Run your test for at least 10 minutes. This step lets Bigtable further optimize your data, and it helps ensure that you will test reads from disk and cached reads from memory.

* Use the right type of write requests for your data. Choosing the optimal way to [write your data](https://cloud.google.com/bigtable/docs/writes) helps maintain high performance.

* Use an[ SSD cluster](https://cloud.google.com/bigtable/docs/choosing-ssd-hdd) for read heavy operations. SSD nodes are significantly faster with more predictable performance.
* Plan your Bigtable instance based on your specific need. You can take a look at this [article](https://cloud.google.com/bigtable/docs/performance#throughput-vs-latency) to know more about various trade-offs between high throughput and low latency offered by Bigtable.


### Sample JMeter test for Bigtable

Assume that the following baseline needs to be performance-tested:


<table>
  <tr>
   <td><strong>S. No.</strong>
   </td>
   <td><strong>Transactions</strong>
   </td>
   <td><strong>Baseline</strong>
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td>Bigtable Insert
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>2
   </td>
   <td>Bigtable Update
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>3
   </td>
   <td>Bigtable Read
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>4
   </td>
   <td>Bigtable Scan
   </td>
   <td>
   </td>
  </tr>
</table>


Below is the sample JMeter test to simulate the above scenarios.


#### **[Bigtable-Runner.jmx](./Bigtable-Runner.jmx)**


[Bigtable-Runner.jmx](./Bigtable-Runner.jmx) uses a CSV configuration to get appId and install UUIDs rowkey elements for apps installed in enterprise_app_installs. These elements are used for tests in the subsequent steps.  

The following are the first few lines, for example:

```text
cfb2a,053f47ec-07ab-4281-81d8-ee57a48f517d
395b9,130794a3-e3d7-4ce9-a149-33a451b184f5
88078,5ca4c6d2-5963-42a2-ab17-0730966319e4
f6955,ba01b91c-6714-48fd-b498-6b7a4de87ce2
14c22,5e5f7332-ae37-481f-ac8f-2b86b589aadb
1bbc8,c11961f3-2b41-4f02-84f4-bc8cc317e2a9
```

The above CSV file will be created using JMeter Bigtable Loader.

There are four thread groups with different transactions, as shown in the following screenshot.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/4-csv-config.jpeg)

The CSV Read configuration reads data from a CSV file that is being used in all four thread groups. CSV Data Set Config is used to read and split lines from a file into variables. It's more user-friendly than `__CSVRead()` and `__StringFromFile()`. It's great for dealing with a lot of variables, and it's also great for testing with "random" and unique values.


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/5-csv-confg-detials.jpeg)


All the thread groups are configured to use below parameters which can be passed by command line as well (ie. `-Jthreads=10`).



* **Number of Threads (users)**: Configures the number of simultaneous connections to Bigtable cluster. If you want a thread group to run for a given duration, then you can change this property.
* **Ramp-Up Period (in seconds)**: Time taken by JMeter to ramp-up each thread. In this case, each thread will start 1 second after the previous thread.
* **Loop Count:** It is the number of times the test needs to be executed.  


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/6-thread-group.jpeg)

The Bigtable Insert group as shown below uses Groovy script in order to connect to Bigtable and insert randomly generated values to **enterprise_app_event_history** table.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/7-add-event.jpeg)


**Randomly generated values**:

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/jmeter-bigtable-perf-testing/8-random-values.jpeg)


## Executing performance test


### Guidelines for executing the tests, for best results:

* Run JMeter tests from the command line, not GUI mode.
* Run each test at least 3 times to even out random differences.
* Warm up Bigtable before running tests (as in production).
* Run tests for long enough such that TPS is stable. It depends on the workload, for example having at least a 15 minute test can ensure that enough ramp-up time is available.
* Ensure that the client machine running JMeter has enough resources. JMeter is a CPU-intensive process.
* Increase JMeter’s [jvm heap size](https://www.blazemeter.com/blog/9-easy-solutions-jmeter-load-test-%E2%80%9Cout-memory%E2%80%9D-failure), if needed.
* Run multiple JMeter instances in parallel, or use [remote testing](https://jmeter.apache.org/usermanual/remote-test.html) for horizontal scaling of JMeter. Often, a single instance of JMeter is not able to produce enough load on a Bigtable cluster.
* Ensure that Bigtable CPU load for a cluster is under 70%. For latency-sensitive applications, it is recommended to plan at least 2x capacity for application's max Bigtable queries per second (QPS).
* Ensure that the cluster has enough nodes to satisfy the recommended limits for both compute and storage.


### Sample test execution


### Run the test:

```sh
jmeter -n -t bigtable-performance-test.jmx -l load-out-c.csv -Jthreads=10 -Jloops=100
```

You can modify the number of users and duration as needed.

The test generates a test-out.csv file with raw statistics. You can use the following command to [create a JMeter report from it](https://jmeter.apache.org/usermanual/generating-dashboard.html#report_only):

```sh
jmeter -g test-out.csv -o [PATH_TO_OUTPUT_FOLDER]
```

### Collecting performance test results

You gather performance metrics after the test execution.

1. Validate that the test ran according to the requirements defined earlier.
2. Compare results with your success criteria.

We recommend capturing these performance metrics from Bigtable monitoring rather than the JMeter report. 

Based on the success criteria, following metrics can be collected from Bigtable Monitoring:
* **CPU Load** : <70% is preferred for latency sensitive apps.
* **Storage** : <60% of storage utilization is optimal to keep latencies low. Also SSDs is recommended for latency sensitive applications. 
* **Latency at 50th and 95th percentile** 

Refer [here](https://cloud.google.com/bigtable/docs/performance) for more details on optimizing performance of BigTable.
Cloud Bigtable instances can be monitored using [Cloud monitoring](https://cloud.google.com/bigtable/docs/monitoring-instance), various types of metrics can be visualized including CPU utilization, Disk Usage, Latency, etc.

To troubleshoot performance issues, use [Key Visualiser ](https://cloud.google.com/bigtable/docs/keyvis-overview)to analyze Bigtable usage patterns.


## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project that you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next
* [BigTable Schema design best practices](https://cloud.google.com/bigtable/docs/schema-design)
* [Eliminate hotspots in Cloud Bigtable](https://cloud.google.com/blog/products/databases/hotspots-and-performance-debugging-in-cloud-bigtable)
* [Live Migrate from Apache HBase to Cloud Bigtable](https://cloud.google.com/blog/products/databases/migrate-from-apache-hbase-to-cloud-bigtable-with-live-migrations)
* [How BIG is Cloud Bigtable?](https://cloud.google.com/blog/topics/developers-practitioners/how-big-cloud-bigtable)
* [Measure Cloud Spanner performance using JMeter](https://cloud.google.com/community/tutorials/jmeter-spanner-performance-test)


