---
title: DB Migration from MySQL to Cloud Spanner - Handling auto incrementing keys
description: Prevent hotspots in Cloud Spanner when migrating Auto Incrementing primary keys, using STRIIM
author: shashank-google
tags: mysql, spanner, cloud spanner, striim, migration, zero downtime, data migration
date_published: 2021-04-28
---

Shashank Agarwal | Database Migrations Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial you will learn about migrating databases consisting of auto incrementing primary keys. The primary key uniquely identifies each row in a table. If you insert records with a monotonically increasing integer as the key, you'll always insert at the end of your key space. This is undesirable because Cloud Spanner divides data among servers by key ranges, which means your inserts will be directed at a single server, creating a hotspot. This applies even when an existing database needs to be migrated. Unless mitigated, this can lead to slow data ingestion from MySQL to Cloud Spanner due to **hotspots**.   

This tutorial will implement [bit-reverse](https://cloud.google.com/spanner/docs/schema-design#bit_reverse_primary_key) technique to reliably convert incrementing keys such that it can prevent hotspot in Cloud Spanner. Core idea is to write a deterministic mathematical function f(x) which results in a non-incrementing value and is unique. Reversing the bits maintains unique values across the primary keys. You need to store only the reversed value, because you can recalculate the original value in your application code, if needed.   

In addition, we also got to solve for generating keys post migration. Cloud Spanner does not have auto generated keys (at time of writing this article), therefore post migration applications will need to generate primary keys. In this tutorial, we will assume that the applications will use [UUID](https://cloud.google.com/spanner/docs/schema-design#uuid_primary_key) for generating keys post migration on Cloud Spanner.  

We will use [Striim](https://www.striim.com/) for performing the zero downtime data migration from MySQL to Cloud Spanner.  

## Objectives

*   Create and setup CloudSQL MySQL instance with Auto Incrementing primary key.
*   Create and setup Cloud Spanner instance.
*   Deploy and configure Striim for performing data migration.
*   Plugin custom functions into striim for real time data transformation(s).
*   Create initial load striim pipeline.
*   Create couninous replication (CDC) striim pipeline.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   Compute Engine for Striim
*   Cloud SQL MySQL instance
*   Cloud Spanner
*   Striim License, which includes a trial period through the [Cloud Marketplace](https://console.cloud.google.com/marketplace/details/striim/striim)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.   
When you finish this tutorial, you can avoid continued billing by deleting the resources you created.

## Before you begin

Give a numbered sequence of procedural steps that the reader must take to set up their environment before getting into the main tutorial.

Don't assume anything about the reader's environment. You can include simple installation instructions of only a few steps, but provide links to installation
instructions for anything more complex.

### Example: Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1.  Create an account with the BigQuery free tier. See
    [this video from Google](https://www.youtube.com/watch?v=w4mzE--sprY&list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq&index=2) for detailed instructions.
1.  Create a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/).
1.  Install [DBeaver Community for Windows](https://dbeaver.io/download/).

## Tutorial body

Break the tutorial body into as many sections and subsections as needed, with concise headings.

### Use short numbered lists for procedures

Use numbered lists of steps for procedures. Each action that the reader must take should be its own step. Start each step with the action, such as *Click*, 
*Run*, or *Enter*.

Keep procedures to 7 steps or less, if possible. If a procedure is longer than 7 steps, consider how it might be separated into sub-procedures, each in its
own subsection.

### Provide context, but don't overdo the screenshots

Provide context and explain what's going on.

Use screenshots only when they help the reader. Don't provide a screenshot for every step.

Help the reader to recognize what success looks like along the way. For example, describing the result of a step helps the reader to feel like they're doing
it right and helps them know things are working so far.

## Cleaning up

Tell the reader how to shut down what they built to avoid incurring further costs.

### Example: Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

Tell the reader what they should read or watch next if they're interested in learning more.

### Example: What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
