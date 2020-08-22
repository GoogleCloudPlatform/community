---
title: Cloud Data Loss Prevention (DLP) hybrid inspection for SQL databases using JDBC
description: Demonstrates how to inspect SQL table data using Cloud Data Loss Prevention with hybrid inspection.
author: scellis, crwilson
tags: Cloud DLP, Java, PII
date_published: 2020-08-24
---

Cloud Data Loss Prevention (Cloud DLP) can help you to discover, inspect, and classify sensitive elements in your data. This document shows how to use the Cloud 
DLP [_hybrid inspection method_](https://cloud.google.com/dlp/docs/reference/rest/v2/HybridInspectDlpJobRequest) with a JDBC driver to inspect samples of 
tables in a SQL database like MySQL, SQL Server, or PostgreSQL.

For a video demonstration, see
[Managing sensitive data in hybrid environments](https://www.youtube.com/watch?v=ApUEuhqeEno&feature=youtu.be&t=688).

## Objectives

* Enable Cloud Data Loss Prevention
* Create a Cloud DLP hybrid job
* Create a secret in Secret Manger
* Create an automated process that uses Cloud DLP to inspect data in a database using JDBC

## Costs

This tutorial uses billable components of Google Cloud, including the following:
* Cloud Data Loss Prevention
* BigQuery (if you choose to write findings to BigQuery)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

1.  Select or create a Google Cloud project.

    [Go to the Managed Resources page.](https://console.cloud.google.com/cloud-resource-manager)
  
1.  Make sure that billing is enabled for your project.

    [Learn how to enable billing.](https://cloud.google.com/billing/docs/how-to/modify-project)

1.  Enable the Cloud Data Loss Prevention API.

    [Enable the API.](https://console.cloud.google.com/flows/enableapi?apiid=dlp.googleapis.com)

## Create a database

For this demonstration, you need to have data running in a database that has a JDBC driver available. You can use this script to inspect a database running 
virtually anywhere. The database does not need to be located in the same place as where you run the script, but the script must have network access to the 
database host. You may need to update the
[`pom.xml` file](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/dlp-hybrid-inspect/pom.xml)
to include the appropriate JDBC client.

If you do not have a database created, [here is a tutorial on how to install MySQL on Google Compute Engine](https://cloud.google.com/solutions/setup-mysql).

## Create a secret with your database user password

To securely pass your database password to the demonstration script, this demonstration uses [Secret Manager](https://cloud.google.com/secret-manager). For
details about creating a secret, see 
[Creating secrets and versions](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets). You need to create a secret that contains your 
database password and then pass the secret resource ID as a parameter into the script.

## Create a hybrid job using Cloud Console

1.  To create the inspection template in Cloud DLP, go to the Cloud [DLP Create job page](https://console.cloud.google.com/security/dlp/create/job).
1.  Select **Hybrid** as the location type.
1.  Configure detection to determine what you want to inspect for. 
1.  Select the actions that you want. If you want to analyze detailed findings, turn on **Save to BigQuery**. 
1.  Finish creating the DLP job.

The resource name that is created is used as a parameter for the script below and will be in a format similar to the following:

    projects/[YOUR_PROJECT_ID]/locations/global/dlpJobs/i-[YOUR_JOB_NAME]

## Configuration

To run the
[demonstration script](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/dlp-hybrid-inspect/src/main/java/com/example/dlp/HybridInspectSql.java),
you need to configure [authenticated access](https://cloud.google.com/dlp/docs/auth#using_a_service_account) with permission to 
call Cloud DLP and Secret Manager. 

Configure service account credentials:

    export GOOGLE_APPLICATION_CREDENTIALS="[PATH_TO_YOUR_CREDENTIALS].json"

If you run this on Compute Engine, you can also use the virtual machine's default service account, but you need to assign the permissions for Cloud DLP
and Secret Manger

Reminder: If you want to see detailed findings or run analysis on findings, we recommend that you turn on the
[`SaveFindings` action](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#savefindings) to BigQuery when configuring your
[hybrid job](https://cloud.google.com/dlp/docs/reference/rest/v2/InspectJobConfig#HybridOptions). 


## Build

Run the following command to compile the script:

    mvn clean package -DskipTests

## Command line parameters

You can configure several parameters, including the database host, username, password, number of rows to sample, and what Cloud DLP hybrid job ID to use. 
Passwords are sent using Cloud Secret Manager to avoid exposing them through the command line. 

| parameter            | description                                         | 
|----------------------|-----------------------------------------------------|
| `sql`                | Database type: `"mysql"`, `"postgres"`, or `"cloudsql"`. There must be an appropriate JDBC driver configured in your `pom.xml` file. |
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

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project you created.

To delete the project, do the following:

1.  In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and click Delete project.
1.  In the dialog, type the project ID, and then click Shut down to delete the project.

## What's next

* Learn about [Cloud Data Loss Prevention](https://cloud.google.com/dlp).
* For a video demonstration of this script, see
  [Managing sensitive data in hybrid environments](https://www.youtube.com/watch?v=ApUEuhqeEno&feature=youtu.be&t=688).
* Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
