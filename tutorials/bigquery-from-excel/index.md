---
title: Connect to BigQuery from Microsoft Excel using ODBC
description: Learn how to use the ODBC drivers for BigQuery to load query results into Microsoft Excel for analysis and visualization.
author: tswast
tags: BigQuery, Excel, ODBC
date_published: 2017-01-26
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[BigQuery](https://cloud.google.com/bigquery/) enables
[standard SQL queries](https://cloud.google.com/bigquery/docs/reference/standard-sql/) to
[petabytes of data](https://youtu.be/6Nv18xmJirs). But what if software that you depend on doesn't
use the BigQuery API? The [BigQuery ODBC drivers](https://cloud.google.com/bigquery/partners/simba-drivers/)
enable you to connect tools, such as Microsoft Excel, that use the
[Open Database Connectivity (ODBC)](https://wikipedia.org/wiki/Open_Database_Connectivity) API
to BigQuery.

## Objectives

* Installing the ODBC driver for BigQuery
* Configuring the ODBC driver
* Loading query results into Microsoft Excel

## Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).

1.  See the
    [blog post on getting started with the BigQuery free tier](https://cloud.google.com/blog/big-data/2017/01/how-to-run-a-terabyte-of-google-bigquery-queries-each-month-without-a-credit-card)
    or [video](https://youtu.be/w4mzE--sprY?list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq) for more detailed instructions.
1.  Install [Microsoft Excel 2016 for Windows](https://products.office.com/en-us/excel).

## Costs

This tutorial uses billable components of Google Cloud, including BigQuery.

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/#id=d343aa2d-457b-4778-b4cb-ef0ea35605ea)
to estimate the costs for your usage.

The first 1 TB per month of BigQuery queries are free. See
[the BigQuery pricing documentation](https://cloud.google.com/bigquery/pricing)
for details about on-demand and flat-rate pricing. BigQuery also offers
[controls to limit your costs](https://cloud.google.com/bigquery/cost-controls).

## Downloading the driver

1.  Check whether your version of Excel is
    [32-bit or 64-bit](https://www.digitalcitizen.life/3-ways-learn-whether-windows-program-64-bit-or-32-bit).
1.  Download the latest version  of the ODBC driver from the
    [Simba Drivers for BigQuery page](https://cloud.google.com/bigquery/partners/simba-drivers/) that
    matches your version of Excel.
1. Run the ODBC driver installer.

The installer writes a user guide to the installation directory (for example,
`C:/Program Files/Simba ODBC Driver for Google BigQuery`), which
contains more detailed instructions about how to configure the driver. These
instructions are also available in the
[Simba ODBC installation and configuration guide](https://www.simba.com/products/BigQuery/doc/v2/ODBC_InstallGuide/win/content/odbc/intro.htm).

## Configuring the driver

1.  Run the ODBC Data Sources Administrator program.

    ![Run ODBC data sources administrator program](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/odbc-data-source-admin.png)

1.  Select the **User DSN** tab.

1.  Click the **Add** button.

    ![Click add](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/add-odbc-source.png)

1.  Select the **Simba ODBC driver for Google BigQuery** from the data source
    dialog box and click the **Finish** button.

    ![Select driver](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/select-odbc-driver.png)

1.  Set a **Data source name (DSN)**, such as "BigQuery", "BigQuery64", or "BigQuery32".

    ![Set a data source name](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/set-dsn.png)

### Authenticating the driver

1.  Choose **User authentication** in the **OAuth mechanism** selection box.

    ![Choose User authentication](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/user-authentication.png)

1.  Click the **Sign in** button.

1.  Grant the ODBC driver permissions to run queries on your behalf by clicking the **Allow** button.

    ![Click allow](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/allow.png)

1.  Copy the authorization code to your clipboard.

    ![Copy the code](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/authorization-code.png)

1.  Paste the code into the **Confirmation code** text box.

    ![Paste the code](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/confirmation-code.png)

1.  Click the **Refresh token** text box. The ODBC driver will automatically
    fill in this text box by making an API request containing the confirmation
    code you provided.

    ![Get a refresh token](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/refresh-token.png)

### Configuring advanced options

1.  Click **Advanced options** to configure the ODBC driver further.

1.  If the [BigQuery Storage API](https://cloud.google.com/bigquery/docs/reference/storage)
    is enabled on the billing project used by the driver, check **High-throughput API**
    box for better performance when downloading query results.

1.  Add a comma-separated list of projects in the **Additional projects** text
    box to view datasets in projects outside of the billing account, such as the
    Google Cloud public datasets hosted in the `bigquery-public-data` project.

1.  Click **OK** to finish configuring advanced options.

![Advanced ODBC options](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/advanced-options.png)

### Finish configuring the driver

1.  Choose the [Google Cloud project ID](https://support.google.com/cloud/answer/6158840) to use as the
    billing project for queries by clicking the arrow on the **Catalog (project)** selection box.

    ![Choose a billing project](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/billing-project.png)

1. Click **OK** to finish configuring the driver.

## Running a query

After the ODBC driver is configured, open Excel.

### Opening the query dialog

1.  Go to the **Data** tab.
1.  Select **New Query > From Other Sources > From ODBC**.

    ![Query from ODBC in Excel screenshot](https://storage.googleapis.com/gcp-community/tutorials/bigquery-from-excel/query-from-odbc.png)

1.  Choose **Google BigQuery** as the data source.
1.  Don't supply a username or password. Instead, select the connection type tab
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

1.  Click **OK**. When the query completes, you will have a new sheet with about 7,400 rows.

## Next steps

With the driver you installed, you can connect any application which supports
the ODBC API to Google BigQuery.

* Follow the [BigQuery quickstart](https://cloud.google.com/bigquery/quickstart-web-ui) to explore
  the web UI and write your own queries.
* Explore more [BigQuery public datasets](https://cloud.google.com/bigquery/public-data/).
* Learn how to [load your own data into BigQuery](https://cloud.google.com/bigquery/loading-data).
* Reference the
  [Simba ODBC driver installation and configuration guide](https://www.simba.com/products/BigQuery/doc/v2/ODBC_InstallGuide/win/content/odbc/intro.htm).
