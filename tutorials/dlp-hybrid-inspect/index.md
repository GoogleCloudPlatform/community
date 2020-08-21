---
title: Cloud Data Loss Prevention (DLP) hybrid inspection demonstration for SQL databases using JDBC
description: Demonstrates how to inspect SQL table data using Cloud Data Loss Prevention with hybrid inspection.
author: scellis,crwilson
tags: Cloud DLP, Java, PII
date_published: 2020-08-24
---

Cloud Data Loss Prevention (Cloud DLP) can help you to discover, inspect, and classify sensitive elements in your data. This document shows how to use the Cloud 
DLP [_hybrid inspection method_](https://cloud.google.com/dlp/docs/reference/rest/v2/HybridInspectDlpJobRequest) with a JDBC driver to inspect samples of 
tables in a SQL database like MySQL, SQL Server, or PostgreSQL. 

## Configuration and build

To run the
[demonstration script](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/dlp-hybrid-inspect/src/main/java/com/example/dlp/HybridInspectSql.java),
you need to configure [authenticated access](https://cloud.google.com/dlp/docs/auth#using_a_service_account) with permission to 
call Cloud DLP and Secret Manager. 

You can use this script to inspect a database running virtually anywhere. The database does not need to be located in the same place as where you run the script,
but the script must have network access to the database host. You may need to update the
[`pom.xml` file](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/dlp-hybrid-inspect/pom.xml)
to include the appropriate JDBC client.

If you want to see detailed findings or run analysis on findings, we recommend that you turn on the
[`SaveFindings` action](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#savefindings) to BigQuery when configuring your
[hybrid job](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#HybridOptions). 

Run the following command to compile the script:

```
mvn clean package -DskipTests
```


## Command line parameters

You can configure several parameters, including the database host, username, password, number of rows to sample, and what Cloud DLP hybrid job ID to use. 
Passwords are sent using Cloud Secret Manager to avoid exposing them through the command line. 


| parameter            | description                                         | 
|----------------------|-----------------------------------------------------|
| `sql`                | Database type: `"mysql"`, `"postgres"`, or `"cloudsql"`. There must be an appropriate JDBC driver configured in your `pom.xml` file.|
| `threadPoolSize`     | Number of worker threads. This code uses 1 thread per table regardless of this setting. If you are scanning multiple tables, increasing this number means that more than one table can be processed in parallel. |
| `sampleRowLimit`     | Maximum number of rows to scan per table.   |
| `hybridJobName`      | Cloud DLP Hybrid job resource ID/name.      |
| `databaseInstanceDescription` | An instance name for tracking. This name gets written to Hybrid and must follow label contraints. |
| `databaseInstanceServer`    | The hostname where your database is running (for example, `localhost` or `127.0.0.1` for local). |
| `databaseName`              | The name of the database or dataset name that you want to scan. |
| `tableName`                 | (Optional) The name of the table you want to scan. If blank, then all tables will be scanned. |
| `databaseUser`              | The username for your database instance.  |
| `secretManagerResourceName` | The Secret Manager resource ID/name that has your database password. Currently this is just the _name_ and the secret must be in the same project. |

## Example command line for MySQL

```
java -cp target/dlp-hybrid-inspect-sql-0.5-jar-with-dependencies.jar com.example.dlp.HybridInspectSql \
-sql "mysql" \
-threadPoolSize 1 \
-sampleRowLimit 1000 \
-hybridJobName "projects/[PROJECT_ID]/dlpJobs/[HYBRID_JOB_NAME]" \
-databaseInstanceDescription "Hybrid Inspect Test" \
-databaseInstanceServer "127.0.0.1" \
-databaseName "[DATABSE_NAME]" \
-databaseUser "[DATABASE_USER]" \
-secretManagerResourceName "[SECRET_MANAGER]"
```
