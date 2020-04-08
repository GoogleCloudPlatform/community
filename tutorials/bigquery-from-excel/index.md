---
title: Connecting to BigQuery from Microsoft Excel using ODBC
description: Learn how to use the ODBC drivers for BigQuery to load query results into Microsoft Excel for analysis and visualization.
author: tswast
tags: BigQuery, Excel, ODBC
date_published: 2017-01-26
---

[BigQuery](https://cloud.google.com/bigquery/) enables [standard SQL
queries](https://cloud.google.com/bigquery/docs/reference/standard-sql/) to
[petabytes of data](https://youtu.be/6Nv18xmJirs). But what if software you
depend on doesn't support the BigQuery API? The [BigQuery ODBC
drivers](https://cloud.google.com/bigquery/partners/simba-drivers/) enable you
to connect tools that support the [Open Database Connectivity
(ODBC)](https://wikipedia.org/wiki/Open_Database_Connectivity) API to
BigQuery, such as Microsoft Excel.

## Objectives

* Installing the ODBC driver for BigQuery.
* Configuring the ODBC driver
* Loading query results into Microsoft Excel®

## Before you begin

This tutorial assumes you are using the Microsoft Windows operating system.

1. Create a project in the [Google Cloud Platform
   Console](https://console.cloud.google.com/).

1. See the [blog post on getting started with the BigQuery free
   tier](https://cloud.google.com/blog/big-data/2017/01/how-to-run-a-terabyte-of-google-bigquery-queries-each-month-without-a-credit-card)
   or [video for more detailed
   instructions](https://youtu.be/w4mzE--sprY?list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq).
1. Install [Microsoft Excel 2016 for
   Windows](https://products.office.com/en-us/excel).

## Costs

This tutorial uses billable components of Cloud Platform including
BigQuery. Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=d343aa2d-457b-4778-b4cb-ef0ea35605ea)
to estimate the costs for your usage.

The first 1 TB per month of BigQuery queries are free. See [the BigQuery
pricing documentation](https://cloud.google.com/bigquery/pricing) for more
details about on-demand and flat-rate pricing. BigQuery also offers [controls
to limit your costs](https://cloud.google.com/bigquery/cost-controls).

## Downloading the driver

1. Check whether your version of Excel is [32-bit or
  64-bit](https://liberty.service-now.com/kb_view.do?sys_kb_id=7e56d58e358829405af1cb6de5727f5a).
1. Download the latest version  of the
  ODBC driver from the [Simba Drivers for BigQuery
  page](https://cloud.google.com/bigquery/partners/simba-drivers/) which
  matches your version of Excel.
1. Run the ODBC driver installer.

## Configuring the driver

1. Run the ODBC Data Sources Administrator program as the
  Windows administrator.
1. Select the System DSN tab.
1. Configure the BigQuery driver.
1. Provide credentials with user authentication. Follow the prompts to log in
  and authorize the driver to access the BigQuery API.
1. Set the Project (Catalog) to your [Google Cloud project
  ID](https://support.google.com/cloud/answer/6158840?hl=en).

Note that the installer writes a user guide to the installation directory (in
my case: `C:/Program Files/Simba ODBC Driver for Google BigQuery`) which
contains more detailed instructions about how to configure the driver.

## Running a query

Once the ODBC driver is configured, open Excel.

### Opening the query dialog

1. Go to the **Data** tab.
1. Select **New Query -> From Other Sources -> From ODBC**.
  ![Query from ODBC in Excel screenshot](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/query-from-odbc.png)
1. Choose **Google BigQuery** as the data source.
1. Don't supply a username or password. Instead, select the connection type tab
  for **Default or Custom**.

### Entering a query

1.  Select **Advanced Options**.
1.  Enter your query in the **SQL statement** text box.

    ![Enter SQL statement screenshot](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/sql-statement.png)

    As an example, query the [USA names public dataset](https://cloud.google.com/bigquery/public-data/usa-names)
    for the most popular names during the [baby boomer generation](https://wikipedia.org/wiki/Baby_boomers).

        #standardSQL
        SELECT
          name, SUM(number) as total_number
        FROM
          `bigquery-public-data.usa_names.usa_1910_2013`
        WHERE
          year >= 1946
          AND year <= 1964
        GROUP BY
          name
        ORDER BY
          total_number
        DESC

1. Click **OK**. When the query completes, you will have a new sheet with about 7,400 rows.

## Next Steps

With the driver you installed, you can connect any application which supports
the ODBC API to Google BigQuery.

* Follow the [BigQuery
  quickstart](https://cloud.google.com/bigquery/quickstart-web-ui) to explore
  the Web UI and write your own queries.
* Explore more [BigQuery public
  datasets](https://cloud.google.com/bigquery/public-data/).
* Learn how to [load your own data into
  BigQuery](https://cloud.google.com/bigquery/loading-data).

