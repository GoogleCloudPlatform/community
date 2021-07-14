---
title: Measuring query performance in BigQuery
description: Measure and compare query performance in BigQuery with Colab and Python libraries.
author: arieljassan
tags: BigQuery, Python, Colab, performance
date_published: 2021-07-07
---

This tutorial describes how to test the performance of queries in BigQuery using a Colab with Python libraries. Performance metrics included in this Colab are query execution time, slots consumed, and gigabytes processed.

Measuring performance of queries can be instrumental for making decisions about system configuration, e.g. whether to use materialized views, partitioning, clustering, etcetera, that may have implications on overall system performance and cost.

You can use the Colab to test your own setup and queries, but for the purposes of the tutorial, we will set up a lab consisting of a public dataset and a dataset in your own project. Note that you may incur costs for creating the dataset and running the queries.

## Objectives
- Create a BigQuery dataset for testing in your own project
- Create a Materialized View based on the data from a table in one of BigQuery public datesets.
- Create a Materialized View with partition alignment based on the data from a table in one of BigQuery public datesets.
- Run the Colab to compare the performance of running queries against the configurations above.

## Costs

This tutorial uses billable components of Google Cloud Platform, including BigQuery. Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

1.  Select or create a GCP project.
    [Go to the Managed Resources page.](https://console.cloud.google.com/cloud-resource-manager)

## Create a BigQuery dataset

Create a BigQuery dataset in your project by running the following SQL instruction in BigQuery SQL:

        CREATE SCHEMA wikipedia_test

## Create a Materialized View

Create a Materialized View from the table *`pageviews_2017`* from the public dataset *`bigquery-public-data.wikipedia`*.

        -- Create materialized view.
        CREATE MATERIALIZED VIEW `wikipedia_test.MV_pageviews_2017`
        AS
        SELECT datehour, wiki, sum(views) as views
        FROM `bigquery-public-data.wikipedia.pageviews_2017`
        WHERE DATE(datehour) >= '2017-01-01'
        GROUP BY 1, 2

## Create a Materialized View with partition and cluster alignment

Create a materialized view with partition and clustering alignment from the table *`pageviews_2017`* in the dataset *`bigquery-public-data.wikipedia`*.

        -- Create materialized view with partition and cluster alignment
        CREATE MATERIALIZED VIEW `wikipedia_test.MV_pageviews_2017_aligned`
        PARTITION BY DATE(datehour)
        CLUSTER BY wiki
        AS
        SELECT datehour, wiki, sum(views) as views
        FROM `bigquery-public-data.wikipedia.pageviews_2017`
        WHERE DATE(datehour) >= '2017-01-01'
        GROUP BY 1, 2

## Compare query performance using Colab

In this part of the tutorial we will compare the performance of queries running against the setups that we have created in previous steps.

Open the [Colab](https://colab.research.google.com/) and follow the instructions there. Once the Colab completes running, you should see at the bottom of it a chart and performance indicators for the queries that you've run.


## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud Platform account for the resources used in this tutorial is to delete the project you created.

To delete the project, follow the steps below:
1.  In the Cloud Platform Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1.  In the project list, select the project you want to delete and click **Delete project**.

    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/partial-redaction-with-dlp-and-gcf/img_delete_project.png)

1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
