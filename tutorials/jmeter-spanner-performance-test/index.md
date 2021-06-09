---
title: Cloud Spanner performance test using JMeter
description: Evaluate Cloud Spanner for custom workload using JMeter's JDBC Sampler
author: shashank-google, chbussler, ravinderl
tags: spanner, cloud spanner, evaluation, migration, perforamnce test, jdbc
date_published: 2021-06-20
---

Shashank Agarwal, Ravinder Lota, Chritoph Bussler | Google Cloud Engineer(s) | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>


Cloud Spanner is a fully managed, horizontally scalable, transactional and SQL compliant database as service. 
For more key features read [here](https://cloud.google.com/spanner#section-2). 
However in order to evaluate Cloud Spanner’s cost and latency, you might want to run performance tests before you start migration.

In this tutorial we do performance testing Cloud Spanner **before making application code changes and executing data migration**.  
[Apache JMeter(TM)](https://jmeter.apache.org/) is a popular open source tool for load testing. 
It includes scriptable Samplers in JSR223-compatible languages like Groovy and BeanShell. 
Using JDBC Sampler which can trigger queries and/or simulate transactions on database(s). 
The core idea is to use JMeter as an application which is sending DML to the database, thus performance testing it.

## Costs
This guide uses billable components of Google Cloud, including the following:

*   Compute Engine (for running JMeter)
*   Cloud Spanner

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.  

## Objectives
*   Determine if Cloud Spanner is suitable for **an existing workload, before application code changes.** 
*   Enable you to write a performance test on Cloud Spanner using JMeter, for your workload. 
    No generic performance benchmarks are discussed in this guide.
*   Estimate the number of Cloud Spanner nodes needed (and therefore cost).
*   Performance test the most frequent set of queries and transactions.
*   Demonstrate the ability to scale horizontally.
*   Better understand the optimizations needed for schema and sql queries.
*   Determine latency of select, insert, update and delete with Cloud Spanner.


### Use Cases

Below are some possible use cases for doing JMeter based performance tests:
*   You want to consolidate current multi-sharded RDBMS into Cloud Spanner.
*   You have a spikey workload and you need an elastic database.
*   You want to standardize on Cloud Spanner for different applications.


### Limitations

*   You cannot test non-jdbc Cloud Spanner client side libraries (like python, r2dbc etc). 
Although you can bypass the client library using underlying [gRPC](https://cloud.google.com/spanner/docs/reference/rpc) 
or [REST](https://cloud.google.com/spanner/docs/reference/rest) apis, that is out of scope for this guide.
*   You should not bypass application based performance tests later.
*   You cannot test non-dml features like [mutations](https://cloud.google.com/spanner/docs/modify-mutation-api), [parallel reads](https://cloud.google.com/spanner/docs/reads#read_data_in_parallel) (aka partitioned selects) etc using JDBC Sampler. In such a case you can [embed custom java code](https://stackoverflow.com/questions/21266923/using-a-jmeter-jdbc-connection-in-java-code) using JSR223 Sampler, that is out of scope for this guide.

This guide will demonstrate JMeter performance tests using an example Cloud Spanner schema.


## 1.1. What do you want to understand about Cloud Spanner performance?

Performance tests are executed to understand application behaviour with Spanner for speed, scalability and stability. 
Following factors need to be considered to design and execute a test that can answer your specific questions.


### 1.1.1. Transactions per second (TPS)

TPS metrics should be based on your application workload requirements, mostly to support the peak load.
example - 7K reads/sec, 4K inserts/sec, 2K updates/sec, etc.  (overall TPS 13K/sec) 


### 1.1.2. Query latency

Expected response time for different DMLs needs to be established as a success criteria. 
This can be either based on your business SLAs or current DB response time in case of an existing application. 


### 1.1.3. Sizing - Number of nodes

Sizing of the Spanner cluster depends on the data volume, TPS and latency requirements of application workload. 
In addition, [CPU utilization](https://cloud.google.com/spanner/docs/cpu-utilization) 
is another important factor to decide the optimal number of nodes. 
You can increase or decrease the initial cluster size in order to maintain the recommended 
45% CPU utilization for multi-region and 65% for regional deployment.


### 1.1.4. Test Cloud Spanner Autoscaler
[Cloud Spanner Autoscaler](https://github.com/cloudspannerecosystem/autoscaler) is a solution to elastically scalable Cloud Spanner. 
Simulate spikey workload via JMeter tests in order to tune autoscaling scaling parameters. 



# 2. Preparing for tests

Developing performance tests takes time and effort, hence planning ahead of time is important. 
Before you begin writing tests following preparation needs to be made:

1. Identify top SQL queries, latency, frequency / hour and avg number of rows returned or updated for each. 
This information will also serve as a BASELINE for the current system.
3. Determine Cloud Spanner region / multi-region deployment. Ideally, load should be generated from Cloud Spanner’s leader region 
for minimum latency and best performance. 
Read [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations) 
for more details on various configurations of Cloud Spanner.
4. Guestimate range of Cloud Spanner nodes required for a given workload based on (step 1). 
It is recommended to have a minimum of 2 nodes for linear scaling. 
**Note**: Peak performance numbers of [regional performance](https://cloud.google.com/spanner/docs/instances#regional-performance) 
and [multi regional performance](https://cloud.google.com/spanner/docs/instances#multi-region-performance) are published. 
However it is based on a 1KB single row transaction with no secondary indexes. 
4. [Request quota](https://cloud.google.com/spanner/quotas#increasing_your_quotas) - Request enough surplus quota for Cloud Spanner nodes on a given 
region / multi-region. It can take up to 1 business day. Although it depends on workload, asking for 100 nodes quota for a performance test can be reasonable.


# 3. Creating Cloud Spanner schema

Assuming you are migrating an existing application from a common RDBMS database(s) like MySQL, Postgresql, SQL Server or Oracle etc. 
You will need to keep in mind [schema design best practices](https://cloud.google.com/spanner/docs/schema-design) when modeling your schema. 

Below is list of common items which you should keep in mind, but it not an exhaustive list:

1. Cloud Spanner needs primary keys to be generated from the application layer. 
Also, monotonically increasing PKs will introduce [hotspots](https://cloud.google.com/spanner/docs/schema-design#primary-key-prevent-hotspots). 
Hence, [using a UUID](https://cloud.google.com/spanner/docs/schema-design#uuid_primary_key) could be a fair alternative.
2. Use an interleaved table to improve performance where most (ex 90%+) of the access is using join to the parent table.   
*Note: Interleaving must be created from the start. You cannot change table interleaving once the tables have been created*  
3. Secondary indexes on monotonically increasing values may introduce hotspots. (ex: index on timestamp).
4. Secondary indexes can utilize [storing clauses](https://cloud.google.com/spanner/docs/secondary-indexes#storing-clause) 
to improve performance of certain queries.
5. Use STRING datatype if you need to have a 
[precision higher than NUMERIC](https://cloud.google.com/spanner/docs/storing-numeric-data#recommendation_store_arbitrary_precision_numbers_as_strings) 
data type.

 

For this guide I'm going to create database Singers with the schema as below.

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


# 4. Setup JMeter
JMeter provides a GUI for easy development of tests. Once tests are developed you should use the command line to execute JMeter tests. 
You may create a VM (in the same region as Cloud Spanner’s Leader) with GUI enabled. 
Therefore the same VM instance can be used for development and execution of tests.

**NOTE: You can use a local workstation for test development too. But, DO NOT use a local workstation for execution of performance tests, 
due to potential network latency.**


## 4.1. Installation

1. Download and install [JMeter](https://jmeter.apache.org/download_jmeter.cgi) 5.3+ (and Java8+).
2. Install [maven](https://maven.apache.org/install.html) used to download Cloud Spanner client libraries.
3. Open terminal / command prompt and change directory (cd) to an empty directory, where you will keep JMeter dependencies.
4. Download Cloud Spanner JDBC library and dependencies using maven command as below.

    mvn dependency:get -Dartifact=com.google.cloud:google-cloud-spanner-jdbc:RELEASE -Dmaven.repo.local=.

5. Move (or Copy) all the downloaded jars into one single folder for JMeter to load in its classpath.

Sample linux command:

    find . -name *.jar -exec mv '{}' . \;

Sample windows command:

    for /r /Y %x in (*.jar) do copy "%x" .\

## 4.2. Setup authentication for JMeter

JMeter uses Cloud Spanner JDBC Client libraries to connect. 
It supports [various authentication mechanisms](https://github.com/googleapis/google-cloud-java#authentication) including service accounts etc. 
In this example we are going to use application default credentials to keep it simple. 
Detailed steps are described [here](https://cloud.google.com/spanner/docs/getting-started/set-up).

In summary, you need to set up gcloud and execute the below command to store credentials locally.

    gcloud auth application-default login

# 5. JMeter basics

JMeter is a highly configurable tool and has various components to pick and choose. 
So in this section we try to provide a basic overview of how to create a Jmeter test along with some minimal configurations you can 
use as a base for your own tests.


## 5.1 JMeter test plan

JMeter has a hierarchical structure to the tests with a top node called [test plan](https://jmeter.apache.org/usermanual/test_plan.html). 
It consists of one or more thread groups, logic controllers, sample generating controllers, listeners, timers, assertions, 
and configuration elements. Since a Test Plan is the top level configuration element, saving a Test Plan to disk will also save all 
nested objects and the resulting file is saved with a .jmx file extension.

For simplicity, it's sufficient to have the top level Test Plan contain a single Thread Group, which in turn contains one or more Samplers. 
There can be multiple Samplers (and other components) within a thread group, each will get executed serially per thread.

Test plan (and/or Thread group) can also have config elements such as JDBC Connection, CSV Data Reader etc. 
Configs can then be shared with child nodes.

<p id="gdcalert1" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: undefined internal link (link text: "Sample test plan link"). Did you generate a TOC? </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert2">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>

[Sample test plan link](#heading=h.v1r2n2peezpu)


## 5.2. Configuring connection parameters

Within each JMeter test (screenshot below) you will need to provide connection parameters which will be used by the JDBC library to connect to Cloud Spanner, complete list [here](https://javadoc.io/doc/com.google.cloud/google-cloud-spanner-jdbc/latest/com/google/cloud/spanner/jdbc/JdbcDriver.html).

 

<p id="gdcalert2" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert3">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

Following properties should be updated:



*   project_id: GCP Project ID
*   instance: Cloud Spanner Instance ID
*   db: Cloud Spanner database Name
*   connections: Cloud Spanner [sessions](https://cloud.google.com/spanner/docs/sessions). Ensure you should have 1 session per thread (users * thread groups).
*   grpc_channel: There can be a maximum of 100 sessions per grpc channel.

Following may not need to be changed. It will be passed from the command line. While default values shall be used when tested from jmeter gui.



*   users: Number of parallel threads per thread group, increasing stress on target.
*   iterations: Number of times each thread should loop, extending duration of tests.


## 5.3. JDBC Connection Configuration

Above parameters will be utilized in JDBC Connection Configuration.



<p id="gdcalert3" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert4">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

JDBC Connection URL as below:


```
jdbc:cloudspanner:/projects/${project_id}/instances/${instance}/databases/${db}?minSessions=${connections};maxSessions=${connections};numChannels=${grpc_channel}
```


Connection pool variable name (conn_pool) will be used by JDBC Samplers to obtain connection.

Also there can be [additional configurations](https://cloud.google.com/spanner/docs/use-oss-jdbc#session_management_statements) such as Read Only or Staleness etc which can be configured as needed.


## 5.4. Thread Groups

A Thread group represents a group of users, and the number of threads you assign a thread group is equivalent to the number of users that you want querying Cloud Spanner. Example thread group configuration as below.



<p id="gdcalert4" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert5">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

In case you want a thread group to execute for a given time duration, then you can change it as shown in screenshot below. Where duration can be supplied as command line value with default of 5 mins.



<p id="gdcalert5" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert6">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)


## 5.5. JDBC Request Sampler



<p id="gdcalert6" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert7">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

Using JDBC Sampler you can fire SQL Queries. Using Prepared Select or Prepared Update is recommended as it is [more performant](https://cloud.google.com/spanner/docs/sql-best-practices#query-parameters) on Cloud Spanner. 


## 5.6 Listeners 

You can add an aggregate report (or other types of reports) after all the thread groups. This will show stats from JMeter gui in real time for all the samplers. However, running performance tests in gui mode  is not recommended as JMeter gui can be slow. Hence, use it for test development purposes.

It is recommended to execute tests command line mode which generates html reports with the different JMeter reports. More on this later.


# 6. Loading initial data into Cloud Spanner

Before you start doing performance tests, you will need to initialize the database with seed data. It is recommended to load the volume of rows in each table, representative of current production data size. 

Typically you can use dataflow jobs for [Importing data from non-Cloud Spanner databases](https://cloud.google.com/spanner/docs/import-non-spanner)

However, sometimes you cannot do that because of schema changes with Cloud Spanner. Therefore an alternative could be to mock seed data using JMeter. 

**How much data should I load?**

Data loading prepares Cloud Spanner to create splits (shards) and distribute different nodes as leaders for each split. More details about database splits is [here](https://cloud.google.com/spanner/docs/schema-and-data-model#database-splits).

Volume of data depends on the SQL queries you want to do performance tests. Main focus is to load those tables which will be used by read or write queries. Ideally it should be similar in volume as production data. In addition data might need to be massaged to fit into potentially modified Cloud Spanner schema. 

**How to reset my tests ?**

Ideally you should reset your database to the same seed data for comparison between multiple test executions. You can use backup/restore (or export/import)  to initialize each run to the same initial dataset. The latter is better if different configurations are tested.


## 6.1. Using JMeter to mock seed data

Sometimes it is non trivial to import existing data into Cloud Spanner due to various reasons like data massaging, operations difficulties. Hence, mock data can be generated by writing insert queries in JMeter.

Below is an example Spanner-Initial-Load.jmx used to load sample schema. You will need to update 

<p id="gdcalert7" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: undefined internal link (link text: "connection parameters"). Did you generate a TOC? </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert8">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>

[connection parameters](#heading=h.t5nr8mnava3y) as discussed previously.


```
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Spanner Initial Load" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="project_id" elementType="Argument">
            <stringProp name="Argument.name">project_id</stringProp>
            <stringProp name="Argument.value">XXXXXXXXXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="instance" elementType="Argument">
            <stringProp name="Argument.name">instance</stringProp>
            <stringProp name="Argument.value">XXXXXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="db" elementType="Argument">
            <stringProp name="Argument.name">db</stringProp>
            <stringProp name="Argument.value">XXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="connections" elementType="Argument">
            <stringProp name="Argument.name">connections</stringProp>
            <stringProp name="Argument.value">1000</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="grpc_channel" elementType="Argument">
            <stringProp name="Argument.name">grpc_channel</stringProp>
            <stringProp name="Argument.value">10</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="users" elementType="Argument">
            <stringProp name="Argument.name">users</stringProp>
            <stringProp name="Argument.value">${__P(users, 10)}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="iterations" elementType="Argument">
            <stringProp name="Argument.name">iterations</stringProp>
            <stringProp name="Argument.value">${__P(iterations, 100)}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath">/location/to/my/jars</stringProp>
    </TestPlan>
    <hashTree>
      <JDBCDataSource guiclass="TestBeanGUI" testclass="JDBCDataSource" testname="JDBC Connection" enabled="true">
        <boolProp name="autocommit">true</boolProp>
        <stringProp name="checkQuery"></stringProp>
        <stringProp name="connectionAge">5000</stringProp>
        <stringProp name="connectionProperties"></stringProp>
        <stringProp name="dataSource">conn_pool</stringProp>
        <stringProp name="dbUrl">jdbc:cloudspanner:/projects/${project_id}/instances/${instance}/databases/${db}?minSessions=${connections};maxSessions=${connections};numChannels=${grpc_channel}</stringProp>
        <stringProp name="driver">com.google.cloud.spanner.jdbc.JdbcDriver</stringProp>
        <stringProp name="initQuery"></stringProp>
        <boolProp name="keepAlive">true</boolProp>
        <stringProp name="password"></stringProp>
        <stringProp name="poolMax">${connections}</stringProp>
        <boolProp name="preinit">false</boolProp>
        <stringProp name="timeout">10000</stringProp>
        <stringProp name="transactionIsolation">DEFAULT</stringProp>
        <stringProp name="trimInterval">60000</stringProp>
        <stringProp name="username"></stringProp>
      </JDBCDataSource>
      <hashTree/>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Insert Data" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">${iterations}</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${users}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="Singer insert" enabled="true">
          <stringProp name="dataSource">conn_pool</stringProp>
          <stringProp name="query">insert into singers (singerid, firstname, lastname) values (?,?,?)</stringProp>
          <stringProp name="queryArguments">${singerid},${firstname},${lastname}</stringProp>
          <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR,VARCHAR</stringProp>
          <stringProp name="queryTimeout"></stringProp>
          <stringProp name="queryType">Prepared Update Statement</stringProp>
          <stringProp name="resultSetHandler">Store as String</stringProp>
          <stringProp name="resultSetMaxRows"></stringProp>
          <stringProp name="resultVariable"></stringProp>
          <stringProp name="variableNames"></stringProp>
        </JDBCSampler>
        <hashTree>
          <UserParameters guiclass="UserParametersGui" testclass="UserParameters" testname="User Parameters" enabled="true">
            <collectionProp name="UserParameters.names">
              <stringProp name="505782679">singerid</stringProp>
              <stringProp name="133788987">firstname</stringProp>
              <stringProp name="-1458646495">lastname</stringProp>
              <stringProp name="-477469889">album_count</stringProp>
            </collectionProp>
            <collectionProp name="UserParameters.thread_values">
              <collectionProp name="-1096124671">
                <stringProp name="118040362">${__UUID()}</stringProp>
                <stringProp name="-1194545551">${__RandomString(10,abcdefghijklmnopqrstuvwxyz)}</stringProp>
                <stringProp name="-1194545551">${__RandomString(10,abcdefghijklmnopqrstuvwxyz)}</stringProp>
                <stringProp name="-1226741124">${__Random(0,20)}</stringProp>
              </collectionProp>
            </collectionProp>
            <boolProp name="UserParameters.per_iteration">false</boolProp>
            <stringProp name="TestPlan.comments">Random generated values to populate database</stringProp>
          </UserParameters>
          <hashTree/>
        </hashTree>
        <LoopController guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">true</boolProp>
          <stringProp name="LoopController.loops">${album_count}</stringProp>
        </LoopController>
        <hashTree>
          <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="Album insert" enabled="true">
            <stringProp name="dataSource">conn_pool</stringProp>
            <stringProp name="query">insert into albums (SingerId, AlbumId, AlbumTitle) values (?,?,?)</stringProp>
            <stringProp name="queryArguments">${singerid},${albumid},${title}</stringProp>
            <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR,VARCHAR</stringProp>
            <stringProp name="queryTimeout"></stringProp>
            <stringProp name="queryType">Prepared Update Statement</stringProp>
            <stringProp name="resultSetHandler">Store as String</stringProp>
            <stringProp name="resultSetMaxRows"></stringProp>
            <stringProp name="resultVariable"></stringProp>
            <stringProp name="variableNames"></stringProp>
          </JDBCSampler>
          <hashTree>
            <UserParameters guiclass="UserParametersGui" testclass="UserParameters" testname="User Parameters" enabled="true">
              <collectionProp name="UserParameters.names">
                <stringProp name="-920409142">albumid</stringProp>
                <stringProp name="110371416">title</stringProp>
                <stringProp name="-1161466994">songs_count</stringProp>
              </collectionProp>
              <collectionProp name="UserParameters.thread_values">
                <collectionProp name="-281684151">
                  <stringProp name="118040362">${__UUID()}</stringProp>
                  <stringProp name="-843745614">${__RandomString(20,abcdefghijklmnopqrstuvwxyz)}</stringProp>
                  <stringProp name="-1226766110">${__Random(0,15)}</stringProp>
                </collectionProp>
              </collectionProp>
              <boolProp name="UserParameters.per_iteration">false</boolProp>
            </UserParameters>
            <hashTree/>
          </hashTree>
          <LoopController guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
            <boolProp name="LoopController.continue_forever">true</boolProp>
            <stringProp name="LoopController.loops">${songs_count}</stringProp>
          </LoopController>
          <hashTree>
            <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="Song insert" enabled="true">
              <stringProp name="dataSource">conn_pool</stringProp>
              <stringProp name="query">insert into Songs (SingerId, AlbumId, TrackId, SongName) values (?,?,?,?)</stringProp>
              <stringProp name="queryArguments">${singerid},${albumid},${track_id},${song_name}</stringProp>
              <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR,VARCHAR,VARCHAR</stringProp>
              <stringProp name="queryTimeout"></stringProp>
              <stringProp name="queryType">Prepared Update Statement</stringProp>
              <stringProp name="resultSetHandler">Store as String</stringProp>
              <stringProp name="resultSetMaxRows"></stringProp>
              <stringProp name="resultVariable"></stringProp>
              <stringProp name="variableNames"></stringProp>
            </JDBCSampler>
            <hashTree>
              <UserParameters guiclass="UserParametersGui" testclass="UserParameters" testname="User Parameters" enabled="true">
                <collectionProp name="UserParameters.names">
                  <stringProp name="360653685">song_name</stringProp>
                  <stringProp name="1270478991">track_id</stringProp>
                </collectionProp>
                <collectionProp name="UserParameters.thread_values">
                  <collectionProp name="767221779">
                    <stringProp name="-492945677">${__RandomString(30,abcdefghijklmnopqrstuvwxyz)}</stringProp>
                    <stringProp name="118040362">${__UUID()}</stringProp>
                  </collectionProp>
                </collectionProp>
                <boolProp name="UserParameters.per_iteration">false</boolProp>
              </UserParameters>
              <hashTree/>
            </hashTree>
          </hashTree>
        </hashTree>
      </hashTree>
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="false">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="TestPlan.comments">Used for debugging</stringProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="Aggregate Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```


The above test will generate random data hierarchically into Singer, Album and Song tables. Each Singer will get a random number of Albums between 0-20. Similarly, 0-15 Songs per Album will get generated. Parallel threads (aka users) will be used to insert data concurrently. 

Executing the above jmeter test can be done using the command as below. Please make sure to update the connection parameters and jdbc library path.


```
jmeter -n -t Spanner-Initial-Load.jmx -l load-out.csv -Jusers=1000 -Jiterations=1000
```


**Note**: Watchout for [cpu utilization](https://cloud.google.com/spanner/docs/cpu-utilization#recommended-max) of Cloud Spanner. Increase the number of nodes and jmeter’s parallel threads (users) to increase data generation rate. Increase iterations count to longer execution time. It is important to note that the initial load must be done with randomly generated keys. Using monotonically increasing keys will lead to write hotspotting and cause a lengthy delay in populating the database.


# 7. Developing performance tests 

Guidelines to develop performance tests:



1. Target to configure performance tests such that it generates transactions per second (TPS) similar to current database (baseline). Later in the execution phase, increase the number of users (load) to simulate scaling.
2. Prefer to have only one transaction per thread group. This will allow you to throttle load for that transaction independent of other transactions. A transaction could be composed of single or multiple sql queries. \
For example, it is fine to have just a single select/insert/update query in a thread group. if that compares evenly with a transaction in your current database (baseline).
3. Determine the transactions per second (TPS) in the current database (baseline) for each DML operation and throttle load accordingly. In other words, sometimes even with one user in the thread group, there is far higher TPS than baseline. If so, then use [timers](https://jmeter.apache.org/usermanual/component_reference.html#timers) to introduce delay, as needed to tone down the TPS close to baseline. 
4. Use [parameterized queries](https://cloud.google.com/spanner/docs/sql-best-practices#query-parameters) for better performance. 
5. [Tune SQL Queries](https://cloud.google.com/spanner/docs/query-syntax) by adding relevant hints as needed.
    1. Cloud Spanner’s GCP Console UI can lead to longer query execution time, especially when result size is large. Therefore you can use [gcloud](https://cloud.google.com/sdk/gcloud/reference/spanner/databases/execute-sql) or [Spanner CLI](https://github.com/cloudspannerecosystem/spanner-cli) as alternatives to time sql queries accurately.  
    2. Use [query execution plans](https://cloud.google.com/spanner/docs/query-execution-plans) to identify query bottlenecks and tune them accordingly.
    3. [Add indexes](https://cloud.google.com/spanner/docs/secondary-indexes) as needed to improve performance of select queries. 
    4. Use [FORCE_INDEX hint](https://cloud.google.com/spanner/docs/query-syntax#table-hints) for all queries as it can take upto a few days before the query optimizer starts to automatically utilize the new index.
    5. Use GROUPBY_SCAN_OPTIMIZATION to make queries with GROUP BY faster.
    6. Use [join hints](https://cloud.google.com/spanner/docs/query-syntax#join-hints) to optimize join performance, as needed.
6. If needed, export query parameter values into a csv. Then use [csv config](https://jmeter.apache.org/usermanual/component_reference.html#CSV_Data_Set_Config) in JMeter to supply parameters from the csv file. 


## 7.1. Sample JMeter Test for Singers schema

Let us assume the following baseline needs to be performance tested.


<table>
  <tr>
   <td>Sno.
   </td>
   <td>Transactions
   </td>
   <td>Baseline TPS
   </td>
  </tr>
  <tr>
   <td>1.
   </td>
   <td>select AlbumTitle from Albums where SingerId = ? and AlbumTitle like ?
   </td>
   <td>7K
   </td>
  </tr>
  <tr>
   <td>2.
   </td>
   <td>select  SingerId, AlbumId, TrackId, SongName from Songs where SingerId = ? and AlbumId = ? order by SongName
   </td>
   <td>5K
   </td>
  </tr>
  <tr>
   <td>3.
   </td>
   <td>update Singers set SingerInfo = ? where SingerId = ?
   </td>
   <td>1K
   </td>
  </tr>
</table>


Below is the Sample JMeter test to simulate the above load. You will need to update 

<p id="gdcalert8" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: undefined internal link (link text: "connection parameters"). Did you generate a TOC? </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert9">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>

[connection parameters](#heading=h.t5nr8mnava3y) as discussed previously.


```
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Spanner Performance Test" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="project_id" elementType="Argument">
            <stringProp name="Argument.name">project_id</stringProp>
            <stringProp name="Argument.value">XXXXXXXXXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="instance" elementType="Argument">
            <stringProp name="Argument.name">instance</stringProp>
            <stringProp name="Argument.value">XXXXXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="db" elementType="Argument">
            <stringProp name="Argument.name">db</stringProp>
            <stringProp name="Argument.value">XXXXX</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="connections" elementType="Argument">
            <stringProp name="Argument.name">connections</stringProp>
            <stringProp name="Argument.value">1000</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="grpc_channel" elementType="Argument">
            <stringProp name="Argument.name">grpc_channel</stringProp>
            <stringProp name="Argument.value">10</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="users" elementType="Argument">
            <stringProp name="Argument.name">users</stringProp>
            <stringProp name="Argument.value">${__P(users, 15)}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="duration" elementType="Argument">
            <stringProp name="Argument.name">duration</stringProp>
            <stringProp name="Argument.value">${__P(duration, 120)}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath">/location/to/my/jars</stringProp>
    </TestPlan>
    <hashTree>
      <JDBCDataSource guiclass="TestBeanGUI" testclass="JDBCDataSource" testname="JDBC Connection" enabled="true">
        <boolProp name="autocommit">true</boolProp>
        <stringProp name="checkQuery"></stringProp>
        <stringProp name="connectionAge">5000</stringProp>
        <stringProp name="connectionProperties"></stringProp>
        <stringProp name="dataSource">conn_pool</stringProp>
        <stringProp name="dbUrl">jdbc:cloudspanner:/projects/${project_id}/instances/${instance}/databases/${db}?minSessions=${connections};maxSessions=${connections};numChannels=${grpc_channel}</stringProp>
        <stringProp name="driver">com.google.cloud.spanner.jdbc.JdbcDriver</stringProp>
        <stringProp name="initQuery"></stringProp>
        <boolProp name="keepAlive">true</boolProp>
        <stringProp name="password"></stringProp>
        <stringProp name="poolMax">${connections}</stringProp>
        <boolProp name="preinit">false</boolProp>
        <stringProp name="timeout">10000</stringProp>
        <stringProp name="transactionIsolation">DEFAULT</stringProp>
        <stringProp name="trimInterval">60000</stringProp>
        <stringProp name="username"></stringProp>
      </JDBCDataSource>
      <hashTree/>
      <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="CSV Read" enabled="true">
        <stringProp name="delimiter">,</stringProp>
        <stringProp name="fileEncoding">UTF-8</stringProp>
        <stringProp name="filename">/Users/agarwalsh/Pictures/singer_and_album_ids.csv</stringProp>
        <boolProp name="ignoreFirstLine">true</boolProp>
        <boolProp name="quotedData">false</boolProp>
        <boolProp name="recycle">true</boolProp>
        <stringProp name="shareMode">shareMode.all</stringProp>
        <boolProp name="stopThread">false</boolProp>
        <stringProp name="variableNames">singerid,albumid</stringProp>
      </CSVDataSet>
      <hashTree/>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Search Albums" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <intProp name="LoopController.loops">-1</intProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${users}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${duration}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="Search Album" enabled="true">
          <stringProp name="dataSource">conn_pool</stringProp>
          <stringProp name="query">select AlbumTitle from Albums where SingerId = ? and AlbumTitle like ?</stringProp>
          <stringProp name="queryArguments">${singerid},${title}</stringProp>
          <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR</stringProp>
          <stringProp name="queryTimeout"></stringProp>
          <stringProp name="queryType">Prepared Select Statement</stringProp>
          <stringProp name="resultSetHandler">Store as String</stringProp>
          <stringProp name="resultSetMaxRows"></stringProp>
          <stringProp name="resultVariable"></stringProp>
          <stringProp name="variableNames"></stringProp>
        </JDBCSampler>
        <hashTree>
          <UserParameters guiclass="UserParametersGui" testclass="UserParameters" testname="User Parameters" enabled="true">
            <collectionProp name="UserParameters.names">
              <stringProp name="110371416">title</stringProp>
            </collectionProp>
            <collectionProp name="UserParameters.thread_values">
              <collectionProp name="1052563230">
                <stringProp name="1730530892">${__RandomString(1,abcdefghijklmnopqrstuvwxyz)}%</stringProp>
              </collectionProp>
            </collectionProp>
            <boolProp name="UserParameters.per_iteration">false</boolProp>
            <stringProp name="TestPlan.comments">Random generated values to populate database</stringProp>
          </UserParameters>
          <hashTree/>
          <ConstantThroughputTimer guiclass="TestBeanGUI" testclass="ConstantThroughputTimer" testname="Constant Throughput Timer" enabled="true">
            <intProp name="calcMode">2</intProp>
            <doubleProp>
              <name>throughput</name>
              <value>420000.0</value>
              <savedValue>0.0</savedValue>
            </doubleProp>
          </ConstantThroughputTimer>
          <hashTree/>
        </hashTree>
      </hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="List songs" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <intProp name="LoopController.loops">-1</intProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${users}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${duration}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="List songs" enabled="true">
          <stringProp name="dataSource">conn_pool</stringProp>
          <stringProp name="query">select  SingerId, AlbumId, TrackId, SongName from Songs where SingerId = ? and AlbumId = ? 
order by SongName</stringProp>
          <stringProp name="queryArguments">${singerid},${albumid}</stringProp>
          <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR</stringProp>
          <stringProp name="queryTimeout"></stringProp>
          <stringProp name="queryType">Prepared Select Statement</stringProp>
          <stringProp name="resultSetHandler">Store as String</stringProp>
          <stringProp name="resultSetMaxRows"></stringProp>
          <stringProp name="resultVariable"></stringProp>
          <stringProp name="variableNames"></stringProp>
        </JDBCSampler>
        <hashTree>
          <ConstantThroughputTimer guiclass="TestBeanGUI" testclass="ConstantThroughputTimer" testname="Constant Throughput Timer" enabled="true">
            <intProp name="calcMode">2</intProp>
            <doubleProp>
              <name>throughput</name>
              <value>300000.0</value>
              <savedValue>0.0</savedValue>
            </doubleProp>
          </ConstantThroughputTimer>
          <hashTree/>
        </hashTree>
      </hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Update singer" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <intProp name="LoopController.loops">-1</intProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${users}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${duration}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <JDBCSampler guiclass="TestBeanGUI" testclass="JDBCSampler" testname="Update singer" enabled="true">
          <stringProp name="dataSource">conn_pool</stringProp>
          <stringProp name="query">update Singers set SingerInfo = FROM_HEX(?) where SingerId = ?</stringProp>
          <stringProp name="queryArguments">${infohex},${singerid}</stringProp>
          <stringProp name="queryArgumentsTypes">VARCHAR,VARCHAR</stringProp>
          <stringProp name="queryTimeout"></stringProp>
          <stringProp name="queryType">Prepared Update Statement</stringProp>
          <stringProp name="resultSetHandler">Store as String</stringProp>
          <stringProp name="resultSetMaxRows"></stringProp>
          <stringProp name="resultVariable"></stringProp>
          <stringProp name="variableNames"></stringProp>
        </JDBCSampler>
        <hashTree>
          <UserParameters guiclass="UserParametersGui" testclass="UserParameters" testname="User Parameters" enabled="true">
            <collectionProp name="UserParameters.names">
              <stringProp name="1945421741">infohex</stringProp>
            </collectionProp>
            <collectionProp name="UserParameters.thread_values">
              <collectionProp name="292808673">
                <stringProp name="-1034328907">${__RandomString(200,123456789abcdef)}</stringProp>
              </collectionProp>
            </collectionProp>
            <boolProp name="UserParameters.per_iteration">false</boolProp>
            <stringProp name="TestPlan.comments">Random generated values to populate database</stringProp>
          </UserParameters>
          <hashTree/>
          <ConstantThroughputTimer guiclass="TestBeanGUI" testclass="ConstantThroughputTimer" testname="Constant Throughput Timer" enabled="true">
            <intProp name="calcMode">2</intProp>
            <doubleProp>
              <name>throughput</name>
              <value>60000.0</value>
              <savedValue>0.0</savedValue>
            </doubleProp>
          </ConstantThroughputTimer>
          <hashTree/>
        </hashTree>
      </hashTree>
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="false">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="TestPlan.comments">Used for debugging</stringProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="Aggregate Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```


Note: It uses a csv config to get SingerId and AlbumId parameters, example top few lines as below. 


```
"singerid","albumid"
"0002aad0-30e9-4eae-b1a0-952ebec9de76","328e1b6f-a449-42d1-bc8b-3d6ba2615d2f"
"0002aad0-30e9-4eae-b1a0-952ebec9de76","43b1011e-d40d-480b-96a2-247636fc7c96"
"0002aad0-30e9-4eae-b1a0-952ebec9de76","5c64c8f2-0fad-4fe7-9c3a-6e5925e3cbcd"
```


Above csv can be created using a sql query such as below. This is to randomly select data from the album table.


```
SELECT SingerId,AlbumId FROM Albums TABLESAMPLE BERNOULLI (0.1 PERCENT) limit 10000;
```


Let's take a brief walkthrough of the test. As the below screenshot shows, there are three thread groups with the transaction as defined previously. 



<p id="gdcalert9" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert10">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

The CSV Read' config reads data from a csv file which is being used in all the three thread groups. Since all the three thread groups are very similar we will take a look at Search Albums.



<p id="gdcalert10" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert11">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

It is configured to use users and duration parameters which can be passed by command line (if not then defaults will be used). It contains one JDBC Sampler Search Album which depends on User Parameters and Timer.



<p id="gdcalert11" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert12">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)

Search Album jdbc sampler as above triggers sql query as screenshot above. It populates query parameters using variable(s) 

${singerid} -- obtained from CSV Read

${title} -- obtained from User Parameters

Finally a timer is configured to throttle load to meet the requirement. It need to be supplied with transactions per **minute**, therefore 7K (TPS) * 60 = 420,000 (TPM)



<p id="gdcalert12" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline drawings not supported directly from Docs. You may want to copy the inline drawing to a standalone drawing and export by reference. See <a href="https://github.com/evbacher/gd2md-html/wiki/Google-Drawings-by-reference">Google Drawings by reference</a> for details. The img URL below is a placeholder. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert13">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![drawing](https://docs.google.com/drawings/d/12345/export/png)


# 


# 8. Executing performance test

Guidelines for executing the tests, for best results:



1. Execute tests from the same Cloud Spanner region for a regional spanner and “leader” region for multi-region Cloud Spanner instances.
2. It is recommended to execute JMeter tests from command line / non-gui mode.
3. Run each test at least 3 times to even out random differences.
4. Warm up Cloud Spanner before running tests (as in production).
5. It is recommended to execute tests for long enough such that TPS is stable. It depends on the workload, for example having at least a 15 min test can ensure that enough ramp up time is available.
6. Scaling Cloud Spanner can take some time to stabilize. It is recommended to generate load on Cloud Spanner for faster stabilization.
7. Ensure that client machine running jmeter should have enough resources and is not maxing out. JMeter is a CPU intensive process.
8. Increase JMeter’s [jvm heap size](https://www.blazemeter.com/blog/9-easy-solutions-jmeter-load-test-%E2%80%9Cout-memory%E2%80%9D-failure), if needed.
9. It is recommended to run multiple jmeter instances in parallel and/or use [remote testing](https://jmeter.apache.org/usermanual/remote-test.html) for horizontal scaling of JMeter. Often a single instance of JMeter is not able to produce enough load on a multi-node Cloud Spanner instance. 
10. Ensure Cloud Spanner is not more than [recommended CPU threshold](https://cloud.google.com/spanner/docs/cpu-utilization#recommended-max), i.e. &lt;65% for regional and &lt;45% for multi regional. 
11. Plan for long running tests (2 hours or more) to verify sustained performance. This is because Cloud Spanner can start [system tasks](https://cloud.google.com/spanner/docs/cpu-utilization#task-priority) which may have performance impact. 


## 8.1. Sample test execution

For executing the test developed in the previous section, the following command needs to be executed. Number of users and duration can be passed using the command line as needed.


```
jmeter -n -t spanner-test.jmx -l test-out.csv -Jusers=100 -Jduration=900
```


[Optional] Once execution is complete it will generate a test-out.csv file with raw stats. If you want, you can execute the below command to [create a JMeter report from it](https://jmeter.apache.org/usermanual/generating-dashboard.html#report_only).


```
jmeter -g test-out.csv -o <Path to output folder>
```



# 


# 9. Collecting the performance test results

You will need to gather performance metrics after the test execution.



1. Validate that the test ran as per the requirements defined earlier in section 1.1 TPS and latency metrics will help identify optimization opportunities for query tuning and cluster sizing.
2. Compare results with the success criteria defined in section 1.1. 

We suggest capturing these performance metrics from Spanner monitoring rather than JMeter report. JMeter provides this information with added latency for each query execution depending on how busy the VM has been. Therefore it will not be the true measure of Spanner response time.

Based on the success criteria we will be mostly interested in



1. Operations/sec (read/write).
2. Latency at 50th and 99th percentile for different types of operations. 
3. CPU utilization 

Spanner monitoring dashboard provides this information at minute level aggregate.

For custom dashboards or  metrics that are not available in standard dashboards you can use [metrics explorer](https://cloud.google.com/spanner/docs/monitoring-cloud#create-charts).

**Operations/sec:**

Spanner dashboard provides information about the read & write operations executing on the spanner instance.

For example, the following chart shows a total TPS of 43744 per second for the selected minute.



<p id="gdcalert13" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image1.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert14">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image1.png "image_tooltip")


**Latency:**

An example of read and write operations latency at 50th and 99th percentile  is captured in the following chart. 

_Note: You can also get 95th percentile latency from Cloud Monitoring dashboard._



<p id="gdcalert14" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image2.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert15">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image2.png "image_tooltip")


* latency metrics have been redacted 

In addition you can use [introspection tools](https://cloud.google.com/spanner/docs/introspection) to investigate issues with your database. Use query statistics to know which queries are expensive, run frequently or scan a lot of data. Read statistics and Transaction statistics to investigate the most common and most resource-consuming read and writes. 

Sometimes writes can be competing and can result in higher latency. You can check the [lock statistics](https://cloud.google.com/spanner/docs/introspection/lock-statistics) to get clarity on wait time and higher latency and apply [best practice](https://cloud.google.com/spanner/docs/introspection/lock-statistics#applying_best_practices_to_reduce_lock_contention) to reduce the lock time.

**CPU utilization:**

This metric is important to understand the CPU utilization throughout the test duration and provides information whether the cluster is under-utilized or over-utilized.



<p id="gdcalert15" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image3.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert16">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image3.png "image_tooltip")


This information can be used to further optimize the cluster size. More details on how to investigate high CPU utilization can be found [here](https://cloud.google.com/spanner/docs/introspection/investigate-cpu-utilization).


# 10. References



1. Cloud Spanner [Schema and data model](https://cloud.google.com/spanner/docs/schema-and-data-model)
2. [Schema design best practices](https://cloud.google.com/spanner/docs/schema-design)
3. [Demystifying Cloud Spanner multi-region configurations](https://cloud.google.com/blog/topics/developers-practitioners/demystifying-cloud-spanner-multi-region-configurations)
4. 
