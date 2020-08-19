---
title: Cloud Data Loss Prevention (DLP) Hybrid Inspect demonstration for SQL databases using JDBC
description: Demonstrates how to inspect SQL table data using Cloud Data Loss Prevention with Hybrid Inspect.
author: scellis,crwilson
tags: Cloud DLP, Java, PII
date_published: 2020-08-21
---

Cloud Data Loss Prevention (Cloud DLP) can help you to discover, inspect, and classify sensitive elements in your data. This tutorial shows how to use Cloud DLP's [_hybrid inspection method_](https://cloud.google.com/dlp/docs/reference/rest/v2/HybridInspectDlpJobRequest) along with a JDBC driver to inspect samples of table in a SQL databas like MySQL, SQL Server, or PostgreSQL. You can configure several parameters including the database host, username, password, desired number of rows to sample, as well as what Cloud DLP hybrid job id to use. Note: passwords are sent using Cloud Secret Manager to avoid exposing them via the command line. 

## Configuration and Build
To run this script you will need to configure [authenticated access](https://cloud.google.com/dlp/docs/auth#using_a_service_account) with permission to call Cloud DLP and Secret Manager. You can use it to inspect a database running virtually anywhere. It does not need to be located in the same place as where you run the script but the script must have network access to the database host.  Depend in on the database you are connecting to, you may need to update the ```pom.xml``` file to include the proper JDBC client.

When configuring your [Hybrid Job](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#HybridOptions), it is recommended that you turn on the action for [SaveFindings to BigQuery](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#savefindings) if you want to see detailed finidngs or run analysis on findings. 

__Compile everything__
```
mvn clean package -DskipTests
```

## Command line parameters

| parameter                   | desc                                                                                                                                                                                                                  | 
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| sql                         | database type "mysql" "postgres" "cloudsql" (there must be a JDBC driver for these configured in ```your pom.xml```)                                                                                                  |
| threadPoolSize              | number of worker threads. _Note: This code uses 1 thread per table regardless of this setting. If you are scanning multiple tables, increasing this number means more than one table can be processed in parallel.    |
| sampleRowLimit              | max number of rows to scan per table                                                                                                                                                                                  |
| hybridJobName               | Cloud DLP Hybrid job resource ID/name                                                                                                                                                                                 |
| databaseInstanceDescription | Give this run an instance name for tracking - this gets written to Hybrid and must follow label contraints.                                                                                                           |
| databaseInstanceServer      | The hostname where your database is running (e.g. localhost or 127.0.0.1 for local).                                                                                                                                  |
| databaseName                | The name of the database or dataset name that you want to scan.                                                                                                                                                       |
| tableName                   | (Optional) The name of the table you want to scan. If blank, then all tables will be scanned.                                                                                                                         |
| databaseUser                | The username for your database instance.                                                                                                                                                                              |
| secretManagerResourceName   | The Secret Manager resrouce ID/name that has your database password. Currently this is just the _name_ and the secret must be in the same project.                                                                    |

## Example command lines

### MySQL

```
java -cp target/dlp-hybrid-inspect-sql-0.5-jar-with-dependencies.jar com.example.dlp.HybridInspectSql \
-sql "mysql" \
-threadPoolSize 1 \
-sampleRowLimit 1000 \
-hybridJobName "projects/[PROJECT-ID]/dlpJobs/[HYBRID-JOB-NAME]" \
-databaseInstanceDescription "Hybrid Inspect Test" \
-databaseInstanceServer "127.0.0.1" \
-databaseName "[DATABSE-NAME]" \
-databaseUser "[DATABASE-USER]" \
-secretManagerResourceName "[SECRET-MANAGER]"
```
