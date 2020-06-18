---
title: Connecting DBeaver to BigQuery through ODBC
description: Learn how to leverage ODBC drivers to access and modify BigQuery data from DBeaver.
author: julzsam
tags: BigQuery, DBeaver, ODBC
date_published: 2020-06-18
---

[BigQuery](https://cloud.google.com/bigquery/) is a managed, serverless data warehouse for storing and querying massive datasets. To access these datasets, you need some kind of a tool that understands BigQuery API or you can use an ODBC driver that can work with a wide range of ODBC-compliant tools, as a data access layer.

Open Database Connectivity (ODBC) is an API that allows external applications to access data in various database management systems. The ODBC driver acts as an interface between an external database and an ODBC data source.

This tutorial shows you how to leverage the [ ODBC Driver for BigQuery](https://www.devart.com/odbc/bigquery/) to connect and access data in BigQuery data warehouse from DBeaver Community, a free database administration tool.  


## Objectives
* Installing the ODBC Driver for BigQuery
* Configuring a DSN for the driver
* Accessing BigQuery data from DBeaver Community

## Before you begin
This tutorial assumes you are using the Microsoft Windows operating system. 
* Create an account with the BigQuery free tier. See this [video](https://www.youtube.com/watch?v=w4mzE--sprY&list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq&index=2) by Google for detailed instructions.
* Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com/)
* Install [DBeaver Community for Windows](https://dbeaver.io/download/)


## Costs
Google BigQuery is a billable web service. The first 1TB of query data processed per month and  the first 10GB of storage per month are free. 
See BigQuery’s [pricing page](https://cloud.google.com/bigquery/pricing) for more details.   



## Downloading the driver
1. Download the latest version of [Devart ODBC Driver for BigQuery](https://www.devart.com/odbc/bigquery/download.html) for the Windows platform
2. Run the ODBC driver installer. The installation wizard offers you to install the 32-bit and 64-bit versions of the driver. Confirm both versions if you are planning to use the driver with older external applications. The driver offers a 30-day trial period, no credit card required.  


## Configuring a DSN for the driver

1. Run the ODBC data source administrator (64-bit) application.
2. Select the **User DSN** or **System DSN** tab, depending on whether you want to create a DSN for the current user or for all user accounts that exist in your Windows system
3. Click **Add** and select **Devart ODBC Driver for Google BigQuery.** 
4. Specify the name for your data source, your **Project ID**, and **Dataset ID**.
5. Click **Request Refresh Token**. Follow the prompts to authorize the driver to view and manage your data in Google BigQuery.
6. Check the **Save Token** box.
7. Open the **Advanced** settings tab and select **Ansi strings** in **String Types**. 
8. Click OK to save the DSN.

## Connecting and accessing BigQuery data

Once the DSN is configured, run DBeaver Community. 

### Creating a new database connection
1. Click **New Database Connection**.
2. Select **ODBC** in the list of data sources and click **Next**.
3. Specify your DSN in the **Database** field and click  **Finish**

You can now expand the created ODBC data source in the **Database Navigator** pane to see existing objects in your BigQuery project.


### Entering a query

1. Right-click the data source and select **SQL Editor**.
2. In the SQL Editor that opens in a new tab, enter your SQL statement.
3. Press **CTRL** + **Enter** on your keyboard to execute the statement.

Image below shows the results of executing a select statement against my sample **head_office** table that contains employee information.

![Running query in DBeaver Community](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-dbeaver-odbc/select_statement.png)

Similarly, you can run insert, update or delete statements against your dataset. The choice of data access tools is not limited to ODBC-compliant applications, you can run queries directly from code in programming languages like Python, PHP, etc.
