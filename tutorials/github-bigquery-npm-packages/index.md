---
title: Querying the Most Popular NPM Packages on GitHub with Google BigQuery
description: Learn how to find the most popular NPM packages on GitHub by querying BigQuery's public GitHub datasets.
author: JustinBeckwith
tags: BigQuery, GitHub, NPM
date_published: 2017-02-08
---

Justin Beckwith | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to query the public GitHub dataset on BigQuery
in order to determine the most popular NPM packages among public projects on
GitHub.

## Objectives

* Run a simple query to determine how many `package.json` files exist on GitHub
* Run a complex query to determine the most popular top-level NPM imports on
  GitHub

## Costs

This tutorial uses billable components of Google Cloud, including BigQuery.

## Before you begin

1.  Select or create a [Google Cloud][console] project.
    [Go to the projects page][projects].
1.  Enable billing for your project. [Enable billing][billing].

[console]: https://console.cloud.google.com/
[projects]: https://console.cloud.google.com/project
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing

## The BigQuery console

Navigate to [bigquery.cloud.google.com/welcome/YOUR_PROJECT_ID][bigquery_console]
to start running queries.

[bigquery_console]: https://bigquery.cloud.google.com/welcome/YOUR_PROJECT_ID

When querying data BigQuery charges $5 (USD) per terabyte of data processed,
where the first terabyte (1 TB) per month is free.

The queries in this tutorial will process more than 1 TB, which is why billing
must be enabled.

## How many package.json files are on GitHub?

1.  In the BigQuery console click **Compose Query** and paste in the following SQL
    query:

    ```sql
    SELECT
      COUNT(*) AS num_files
    FROM [bigquery-public-data:github_repos.files]
      WHERE
        RIGHT(path, 12) = "package.json"
    ```

1.  Click **Run Query** to execute the query, which should only take a few
    seconds.
1.  You should see a result like the following:

    ![query-1](https://storage.googleapis.com/gcp-community/tutorials/github-bigquery-npm-packages/query-1.png)

## Which NPM packages are imported the most on GitHub?

1.  In the BigQuery console click **Compose Query** and paste in the following SQL
    query:

    ```sql
    SELECT
      COUNT(*) as times_imported, package
    FROM
      JS(
        (SELECT content FROM [bigquery-public-data:github_repos.contents] WHERE id IN (
          SELECT id FROM [bigquery-public-data:github_repos.files] WHERE RIGHT(path, 12) = "package.json"
        )),
        content,
        "[{ name: 'package', type: 'string'}]",
        "function(row, emit) {
          try {
            x = JSON.parse(row.content);
            if (x.dependencies) {
              Object.keys(x.dependencies).forEach(function(dep) {
                emit({ package: dep });
              });
            }
          } catch (e) {}
        }"
      )
    GROUP BY package
    ORDER BY times_imported DESC
    LIMIT 1000
    ```

1.  Click **Run Query** to execute the query, which should take 2-3 minutes and
    process several terabytes of data.
1.  You should see a result like the following:

    ![query-2](https://storage.googleapis.com/gcp-community/tutorials/github-bigquery-npm-packages/query-2.png)

There you have it, the most imported NPM packages on GitHub!

## Next steps

- Learn more about [BigQuery](https://cloud.google.com/bigquery/docs).
- Explore [other BigQuery queries](https://medium.com/google-cloud/github-on-bigquery-analyze-all-the-code-b3576fd2b150)
