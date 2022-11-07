---
title: Create Data Catalog tags by inspecting BigQuery data with Cloud Data Loss Prevention
description: Learn how to inspect BigQuery data using Cloud Data Loss Prevention and automatically create Data Catalog tags for sensitive elements with results from inspection scans.
author: imadethis,mesmacosta
tags: database, Cloud DLP, Java, PII
date_published: 2020-04-27
---

Marcelo Costa and Scott Ellis | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Cloud Data Loss Prevention (Cloud DLP) can help you to discover, inspect, and classify sensitive elements in your data. The 
results of these inspections can be valuable as *tags* in Data Catalog. This tutorial shows how to inspect BigQuery data 
using the Cloud Data Loss Prevention API and then use the Data Catalog API to create tags at the column level with the 
sensitive elements found.

This tutorial includes instructions to create a Cloud DLP inspection template to define what data elements to inspect for, 
the JDBC driver used to connect to BigQuery, and the number of worker threads used to parallelize the work. Such an 
implementation, connecting to the data source with JDBC, allows for changing the data source to alternatives like MySQL, SQL 
Server, or PostgreSQL. You can also customize or adjust this script to change the tag fields to better fit your use case.

For a related solution that uses Dataflow to inspect data on a larger scale, see
[Create Data Catalog tags on a large scale by inspecting BigQuery data with Cloud DLP using Dataflow](https://cloud.google.com/community/tutorials/dataflow-dlp-to-datacatalog-tags).

## Objectives

- Enable Cloud Data Loss Prevention, BigQuery, and Cloud Data Catalog APIs.
- Create a Cloud DLP inspection template.
- Create an automated process that uses Cloud DLP findings to label and tag BigQuery table columns.
- Use these labels and tags in your code. 
- Use Cloud Data Catalog to quickly understand where sensitive data exists in your BigQuery table columns.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- BigQuery
- Cloud Data Loss Prevention
- Data Catalog

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.

## Reference architecture

The following diagram shows the architecture of the solution:

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/dlp-to-datacatalog-tags/flow.png)

## Tutorial video

You can also watch a video demonstration of running the script:

[![Tutorial video](https://img.youtube.com/vi/jWAaen5-t7U/0.jpg)](http://www.youtube.com/watch?v=jWAaen5-t7U)

## Before you begin

1.  Select or create a Google Cloud project.

    [Go to the **Manage resources** page.](https://console.cloud.google.com/cloud-resource-manager)

1.  Make sure that billing is enabled for your project.

    [Learn how to enable billing.](https://cloud.google.com/billing/docs/how-to/modify-project)

1.  Enable the Data Catalog, BigQuery, and Cloud Data Loss Prevention APIs.

    [Enable the APIs.](https://console.cloud.google.com/flows/enableapi?apiid=datacatalog.googleapis.com,bigquery.googleapis.com,dlp.googleapis.com)

## Create BigQuery tables

You can use the open source script [BigQuery Fake PII Creator](https://github.com/mesmacosta/bq-fake-pii-table-creator) to 
create BigQuery tables with example personally identifiable information (PII). 

## Create the inspection template

Create the inspection template in Cloud DLP:

1.  Go to the Cloud DLP [**Create template** page](https://console.cloud.google.com/security/dlp/create/template).

1.  Set up the infoTypes. This is an example. You may choose any from the list available:
    
    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/dlp-to-datacatalog-tags/infoTypes.png)

1.  Finish creating the inspection template:
    
    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/dlp-to-datacatalog-tags/inspectTemplateCreated.png)

## Get the script code

The script code is available from
[this GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/dlp-to-datacatalog-tags).

## Install the BigQuery JDBC driver

Run the following commands to download the latest Simba BigQuery driver, extract it, install it with Maven, and delete the 
temporary `lib` files:

    curl -o SimbaJDBCDriverforGoogleBigQuery.zip https://storage.googleapis.com/simba-bq-release/jdbc/SimbaJDBCDriverforGoogleBigQuery42_1.2.2.1004.zip && \
    unzip -qu SimbaJDBCDriverforGoogleBigQuery.zip -d lib && \
    mvn install:install-file  \
    -Dfile=lib/GoogleBigQueryJDBC42.jar \
    -DgroupId=com.simba \
    -DartifactId=simba-jdbc \
    -Dversion=1.0 \
    -Dpackaging=jar \
    -DgeneratePom=true && \
    rm -rf lib

If you want to connect to other databases, you may adapt the script to use different JDBC drivers.

## Configure service account credentials

Create a service account with the following:
* BigQuery Admin
* Data Catalog Admin
* DLP Administrator

```
export GOOGLE_APPLICATION_CREDENTIALS="[PATH_TO_YOUR_CREDENTIALS].json"
```

If you run this on Compute Engine, you can also use the virtual machine's default service account, but you need to assign
the permissions listed above. 

## Running the script

### Command line parameters

| Parameter                  | Description                                                           | 
|----------------------------|-----------------------------------------------------------------------|
| `dbType`                   | The database type. `"bigquery"` is currently the only type supported. |
| `dbName`                   | The name of the dataset that you want to scan. This parameter is optional for BigQuery; if you don't use it, or if you leave it blank, then all datasets in the project are scanned. |
| `tableName`                | The name of the table that you want to scan. This parameter is optional for BigQuery; if you don't use it, or if you leave it blank, then all tables are scanned. |
| `threadPoolSize`           | Number of worker threads. This code uses 1 thread per table, regardless of this setting. If you are scanning multiple tables, increasing this number means that more than one table can be processed in parallel. |
| `limitMax`                 | Maximum number of rows to scan per table.  |
| `minThreshold`             | Minimum number of findings per infoType in a given column before it will be tagged. For example, if this is set at 10 and only 9 items are found, the column won't be tagged. |
| `inspectTemplate`          | Cloud DLP inspection template to use. |
| `projectId`                | Your Cloud project ID. |

### Compile the script

```
mvn clean package -DskipTests
```

### Execute the script

```
java -cp target/dlp-to-datacatalog-tags-0.1-jar-with-dependencies.jar com.example.dlp.DlpDataCatalogTagsTutorial \
-dbType "bigquery" \
-limitMax 1000 \
-dbName research2 \
-projectId my-project \
-threadPoolSize 5 \
-inspectTemplate "projects/my-project/inspectTemplates/inspect_template_dlp_demo" \
-minThreshold 100
```

## Check the results of the script

After the script finishes, you can go to [Data Catalog](https://cloud.google.com/data-catalog) and search for sensitive
data:

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/dlp-to-datacatalog-tags/searchUI.png)

By clicking each table, you can see which columns were marked as sensitive:

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/dlp-to-datacatalog-tags/taggedTable.png)

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete 
the project you created.

To delete the project, follow the steps below:

1.  In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1.  In the project list, select the project that you want to delete and click **Delete project**.

    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/partial-redaction-with-dlp-and-gcf/img_delete_project.png)
    
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn about [Cloud Data Loss Prevention](https://cloud.google.com/dlp).
- Learn about [Data Catalog](https://cloud.google.com/data-catalog).
- For a related solution that uses Dataflow to inspect data on a larger scale, see
[Create Data Catalog tags on a large scale by inspecting BigQuery data with Cloud DLP using Dataflow](https://cloud.google.com/community/tutorials/dataflow-dlp-to-datacatalog-tags).
- Try out other Google Cloud features. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
