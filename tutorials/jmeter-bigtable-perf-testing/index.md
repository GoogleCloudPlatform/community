
# Measure Cloud Bigtable performance using JMeter

[Cloud Bigtable](https://cloud.google.com/bigtable) is a fully managed, scalable NoSQL database as service for large analytical and operational workloads with up to 99.999% availability.

Before you adopt Cloud Bigtable, you might want to evaluate its cost and latency by performance testing. In this tutorial, you will do the performance testing with Cloud Bigtable using JMeter.

[Apache JMeter](https://jmeter.apache.org/) is a popular open source tool for load testing. It includes scriptable samplers in languages, such as Groovy and BeanShell. In this tutorial, you will use the JSR-233 Sampler to simulate load on Cloud Bigtable using the [bigtable-hbase-1.x](https://cloud.google.com/bigtable/docs/hbase-bigtable) client library.


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



* You want to migrate current Cassandra, HBase, or other NoSQL use cases  to Cloud Bigtable.
* You want to evaluate performance of a data model and need to ensure that Bigtable scales linearly to meet demand.
* You want to standardize on Cloud Bigtable for multiple applications.
* Test Cloud Bigtable autoscaling response time and speed.


## Limitations

Below are a few limitations with JMeter and testing with Bigtable: 



* You cannot use JMeter to test non-Java Cloud Bigtable client side libraries. Although, you can bypass the client library using underlying [gRPC](https://cloud.google.com/bigtable/docs/reference/service-apis-overview#grpc) or [REST APIs](https://cloud.google.com/bigtable/docs/reference/service-apis-overview#rest), that is out of scope for this document.
* JMeter does not allow you to create a shared connection pool used by all the threads with JSR 233 Sampler. Therefore you will be creating one connection per thread in a Thread Group.

Even if you use JMeter performance tests, you should also do application-based performance tests before you go to production.


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

enterprise_app_installs:  store record of apps ever available with UUID as app identifier. Lookup by key. 

rowkey: 			uuid

cf1:owner			&lt;owner_id>

cf1:description		&lt;user description>

cf1:app_status			&lt;status_id>

cf1:app_category		&lt;app_category>

cf1:created_ts			&lt;created_ts>

enterprise_app_event_history:  store app session and activity events. Activity events are captured at least at launch and closure of the app to collect stateful information by UUID as app identifier, timestamp of event, and unique eventId.

rowkey: 			uuid#eventId#timestamp

cf1:event_details		&lt;details_of_app_event>

cf1:memory_usage		&lt;memory_usage_metric>

cf1:cpu_utilization		&lt;cpu_utilization_metric>

cf1:event_ts			&lt;event_ts>


### DDL

[Install bigtable CLI tool](https://cloud.google.com/bigtable/docs/cbt-overview) (cbt) if you don’t have one already or create tables using UI.


```
cbt -instance bt-perf createtable enterprise_app_installs "families=cf1:maxversions=10"
cbt -instance bt-perf createtable enterprise_app_event_history "families=cf1:maxversions=1"
```



## Set up JMeter

JMeter provides a GUI for easy development of tests. After tests are developed, use the command line to run the JMeter tests. You can create a VM with the GUI enabled (or a windows VM), so that the same VM instance can be used for development and execution of tests.

You can use a local workstation for test development, too. Don't use a local workstation to run performance tests, because network latency will interfere with the tests results.


### Installation



1. Download and install [JMeter](https://jmeter.apache.org/download_jmeter.cgi) 5.3 or higher, which requires Java 8 or higher.
2. Install [Maven](https://maven.apache.org/install.html), which is used to download Cloud Spanner client libraries.
3. In a command shell, go to an empty directory, where you will keep JMeter dependencies.
4. Download the Cloud Bigtable HBase client library and dependencies:

mvn dependency:get -Dartifact=com.google.cloud.bigtable:bigtable-hbase-1.x-shaded:2.0.0 -Dmaven.repo.local=.



5. Move the downloaded JAR files into a folder for JMeter to load in its classpath: \
Linux

		find . -name *.jar -exec mv '{}' . \; \


	Windows

	

		for /r %x in (*.jar) do copy "%x" .


### Set up authentication for JMeter

JMeter uses Cloud Bigtable client libraries to connect. It supports [various authentication mechanisms](https://github.com/googleapis/google-cloud-java#authentication), including service accounts. For simplicity, this example uses application default credentials. For detailed steps, see [quickstart documentation](https://cloud.google.com/bigtable/docs/creating-test-table).

In summary, you need to set up gcloud and run the following command to store credentials locally:

	   gcloud auth application-default login


## JMeter basics

JMeter is a highly configurable tool and has various components from which you can choose. This section provides a basic overview of how to create a JMeter test along with some minimal configurations that you can use as a base for your tests.


### JMeter test plan

JMeter has a hierarchical structure to the tests, with a top node called the [test plan](https://jmeter.apache.org/usermanual/test_plan.html). It consists of one or more thread groups, logic controllers, sample generating controllers, listeners, timers, assertions, and configuration elements. Because a test plan is the top-level configuration element, saving a test plan to disk also saves all nested objects, and the resulting file is saved with a `.jmx` filename extension.

For simplicity, it's sufficient to have the top-level test plan contain a single thread group, which in turn contains one or more samplers. There can be multiple samplers (and other components) within a thread group; each is executed serially per thread.

Test plans and thread groups can also have configuration elements such as a CSV data reader. Configurations can be shared with child nodes.


### Configuring connection parameters

As shown in the following screenshot, within each JMeter test, you need to provide connection parameters, which are used by the bigtable-hbase library to connect to Cloud Bigtable.

JMeter Bigtable Data Generator sample code

[https://paste.googleplex.com/5115278657585152](https://paste.googleplex.com/5115278657585152)



* Is cluster “bigtable-cluster-id” required in jmx?

Error when running tool

JMeter Bigtable Performance Test sample code

[https://paste.googleplex.com/5634432653328384](https://paste.googleplex.com/5634432653328384)


### Thread groups

[Thread group](https://jmeter.apache.org/usermanual/test_plan.html#thread_group) represents a test case containing a collection of samplers, each sampler is executed sequentially. It can be configured with a number of parallel threads (aka users) for that test.

Within the thread group samplers are added which will call the bigtable.


### JSR223 request sampler

JMeter does not have a built-in Bigtable compatible sampler. Therefore you need to write custom code in Groovy / Java using JSR223 sampler, to interact with Bigtable.


### Connection configuration

Creating a connection is a resource heavy operation, hence you need to create a connection pool one time and cache the connection object in-memory. To do this you should use a special component called “setUp Thread Group” as shown in the screenshot below. 

This thread group gets executed before any other thread groups.



<p id="gdcalert1" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image1.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert2">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image1.png "image_tooltip")


Within this thread group create a JSR233 Sampler which creates the connection object one-time and stores it in memory (as btConn property). Later the same object is fetched by the tests to connect to Bigtable.



<p id="gdcalert2" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image2.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert3">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image2.png "image_tooltip")


Sample code as below:


```
import com.google.cloud.bigtable.hbase.BigtableConfiguration;
import org.apache.hadoop.hbase.client.Connection;

Connection conn = BigtableConfiguration.connect("${project-id}", "${bigtable-instance-id}");
OUT.println("Opened Connection:" + conn);
props.put("btConn", conn);
```


Similarly, you should also create a tearDown thread group with a sampler to close the connection as shown in screenshot below.



<p id="gdcalert3" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image3.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert4">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image3.png "image_tooltip")



## Loading initial data into Cloud Bigtable

Before you start doing performance tests, you need to initialize the database with seed data. We recommend that you load the volume of rows in each table, representative of current production data size.

There are [multiple ways](https://cloud.google.com/bigtable/docs/import-export) to import data to Bigtable. However, for testing purposes we can mock data using Jmeter.


### How much data to load

The Bigtable cluster configurations including [storage types](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#storage-types), [application profiles](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#app-profiles), number of [nodes](https://cloud.google.com/bigtable/docs/instances-clusters-nodes#nodes)  and the size of the data set can alter the performance of workload and the test results on the same cluster. Data set size should be picked similar in volume to production data keeping in mind what we are trying to understand about the cluster’s performance.


### How to reset tests


### Ideally, you should reset your database to the same seed data for comparison between multiple test executions. You can use backup/restore (or export/import) to initialize each run to the same initial dataset. The latter is better if different configurations are tested.


### Using JMeter to mock seed data

Sometimes it is not simple to import existing or mocked up data into Cloud Bigtable. Mock data can be generated by writing insert queries in JMeter.

Below is an example Bigtable-Initial-Load.jmx used to load sample schema. You will need to update connection parameters as described previously.


### **Bigtable-Initial-Load.jmx**


### The  Bigtable-Initial-Load.jmx test generates random data in enterprise_app_installs table with the below  given column family.


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
   <td><a href="https://en.wikipedia.org/wiki/Universally_unique_identifier">uuid</a>
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


You can run this JMeter test with the following command:


```
jmeter -n -t Bigtable-Initial-Load.jmx -l load-out-c.csv -Jusers=10 -Jiterations=100
```


You can use the  [Key Visualizer tool for Bigtable](https://cloud.google.com/bigtable/docs/keyvis-overview) to generate visual reports for your table. This tool will help you analyze your Bigtable usage patterns. Key Visualizer makes it possible to check whether your usage patterns are causing undesirable results, such as hotspots on specific rows or excessive CPU utilization. 

Initial load should be done with randomly generated rowkeys. Using monotonically increasing keys will lead to write hotspots and cause a lengthy delay in populating the table.


## Developing performance tests



* Target to configure performance tests such that they generate transactions per second (TPS) similar to the current database (baseline). Later in the execution phase, increase the number of users (load) to simulate scaling.
* Test with enough data: \
Try to test your instance with roughly the same amount of data as present in your production environment. \

* Stay below the recommended storage utilization per node. For details, see [Storage utilization per node](https://cloud.google.com/bigtable/quotas#storage-per-node). \

* Run your test for at least 10 minutes. This step lets Bigtable further optimize your data, and it helps ensure that you will test reads from disk and cached reads from memory. \

* Use the right type of write requests for your data. Choosing the optimal way to [write your data](https://cloud.google.com/bigtable/docs/writes) helps maintain high performance. \

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


#### **Bigtable-Perf-Test.jmx**


#### <span style="text-decoration:underline;">Bigtable-Perf-Test.jmx</span> uses a CSV configuration to get UUID rowkey.

The following are the first few lines, for example:


```
bfee72e3-0a6f-4b63-afbd-ce97bd1df68a
b5c00c8d-33b6-4c7b-add1-0eade16d7d7d
019bb7ce-9b19-41b7-9c5b-ec3f901069f5
6ed25e50-d0b2-4d57-9398-7db78d25370c
f918d20f-049f-4b33-994b-5b22e2927d5f
81e64859-810a-403f-a690-ee31022a9c88
414ffce9-341c-49ba-8eaf-5343e64a3976
e50c4b91-eb49-476f-8c9b-8d800b24a66d
02e9e364-5b9a-4be7-b39f-fde92e524cfa
cd21919a-79b6-4c9e-b24c-a3f48dbb732d
```


The above CSV file will be created using <span style="text-decoration:underline;">JMeter Bigtable Loader code</span>

There are four thread groups with different transactions, as shown in the following screenshot.



<p id="gdcalert4" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image4.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert5">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image4.png "image_tooltip")


The** <span style="text-decoration:underline;">CSV Read configuration</span> **reads data from a CSV file that is being used in all four thread groups. CSV Data Set Config is used to read and split lines from a file into variables. It's more user-friendly than __CSVRead() and __StringFromFile(). It's great for dealing with a lot of variables, and it's also great for testing with "random" and unique values.



<p id="gdcalert5" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image5.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert6">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image5.png "image_tooltip")


<p id="gdcalert6" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image6.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert7">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image6.png "image_tooltip")


All the thread groups are configured to use below parameters which can be passed by command line as well.



* **Number of Threads (users)**: Configures the number of simultaneous connections to Bigtable cluster. If you want a thread group to run for a given duration, then you can change this property.
* **Ramp-Up Period (in seconds)**: Time taken by JMeter to ramp-up each thread. In this case, each thread will start 1 second after the previous thread.
* **Loop Count:** It is the number of times the test needs to be executed.  \


   

<p id="gdcalert7" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image7.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert8">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image7.png "image_tooltip")


The Bigtable Insert group as shown below uses Groovy script in order to connect to Bigtable and insert randomly generated values to **enterprise_app_event_history** table



<p id="gdcalert8" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image8.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert9">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image8.png "image_tooltip")


**Randomly generated values**:



<p id="gdcalert9" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image9.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert10">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image9.png "image_tooltip")



## Executing performance test


### Guidelines for executing the tests, for best results:



* Run JMeter tests from the command line, not GUI mode.
* Run each test at least 3 times to even out random differences.
* Warm up Bigtable before running tests (as in production).
* Run tests for long enough such that TPS is stable. It depends on the workload, for example having at least a 15 minute test can ensure that enough ramp-up time is available.
* Ensure that the client machine running JMeter has enough resources. JMeter is a CPU-intensive process.
* Increase JMeter’s [jvm heap size](https://www.blazemeter.com/blog/9-easy-solutions-jmeter-load-test-%E2%80%9Cout-memory%E2%80%9D-failure), if needed.
* Run multiple JMeter instances in parallel, or use [remote testing](https://jmeter.apache.org/usermanual/remote-test.html) for horizontal scaling of JMeter. Often, a single instance of JMeter is not able to produce enough load on a Bigtable node.
* Ensure that Bigtable CPU load for a cluster is under 70%. For latency-sensitive applications, it is recommended to plan at least 2x capacity for application's max Bigtable queries per second (QPS). 
* It is recommended to have max 1 KB of data in each row of a Bigtable table. Increasing the amount of data per row will also reduce the number of rows per second.
* Ensure that the cluster has enough nodes to satisfy the recommended limits for both compute and storage.


### Sample test execution


### Run the test:


```
jmeter -n -t bigtable-performance-test.jmx -l load-out-c.csv -Jusers=10 -Jiterations=100
```


You can modify the number of users and duration as needed.

The test generates a test-out.csv file with raw statistics. You can use the following command to [create a JMeter report from it](https://jmeter.apache.org/usermanual/generating-dashboard.html#report_only):


```
jmeter -g test-out.csv -o [PATH_TO_OUTPUT_FOLDER]
```



### Collecting performance test results

You gather performance metrics after the test execution.



1. Validate that the test ran according to the requirements defined earlier.
2. Compare results with your success criteria.

We recommend capturing these performance metrics from Bigtable monitoring rather than the JMeter report. 

Based on the success criteria, following most important metrics are collected using Cloud Monitoring:

CPU Load



<p id="gdcalert10" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image10.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert11">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image10.png "image_tooltip")


Latency at 50th and 99th percentile for different types of operations:



<p id="gdcalert11" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image11.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert12">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image11.png "image_tooltip")




<p id="gdcalert12" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image12.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert13">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image12.png "image_tooltip")


Cloud Bigtable instances can be monitored using [Cloud monitoring](https://cloud.google.com/bigtable/docs/monitoring-instance), various types of metrics can be visualized including CPU utilization, Disk Usage, Latency, etc.

To troubleshoot performance issues, use [Key Visualiser ](https://cloud.google.com/bigtable/docs/keyvis-overview)to analyze Bigtable usage patterns.


## Cleaning up


## What's next
