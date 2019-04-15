---
title: Cloud SQL Hello World
description: Set up a MySQL database in GCP.
author: jscud
tags: Cloud SQL
date_published: 2019-04-15
---

# Cloud SQL 'Hello World' Tutorial

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=sql_mysql_quickstart)

</walkthrough-alt>

## Overview

In this tutorial, you will:

1.  Instantiate a new MySQL instance
2.  Setup and query a database
3.  Cleanup instance

<walkthrough-tutorial-duration duration="10"></walkthrough-tutorial-duration>

## Project setup

Google Cloud Platform resources are organized into projects. Cloud SQL needs a
project to get started.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Create SQL instance

You can create a MySQL instance using the UI.

1.  Navigate to SQL Instances page
    <walkthrough-menu-navigation sectionId="SQL_SECTION"></walkthrough-menu-navigation>

1.  Click
    <walkthrough-spotlight-pointer spotlightId="sql-zero-state-create-button">
    Create Instance </walkthrough-spotlight-pointer>

1.  Choose a database engine:

    Verify
    <walkthrough-spotlight-pointer spotlightId="sql-mysql-radio-button">MySQL</walkthrough-spotlight-pointer>
    is selected and click
    <walkthrough-spotlight-pointer spotlightId="sql-choose-engine-next">next</walkthrough-spotlight-pointer>
    button.

1.  Choose a MySQL instance type:

    Click <walkthrough-spotlight-pointer spotlightId="sql-second-generation">
    Choose Second Generation </walkthrough-spotlight-pointer>

1.  Configure Instance:

    The default configuration should be sufficient. Remember these values, you'll
    reference them later:

    *   <walkthrough-spotlight-pointer spotlightId="sql-instance-id-input">Instance ID</walkthrough-spotlight-pointer>
    *   <walkthrough-spotlight-pointer spotlightId="sql-root-password-input">Root password</walkthrough-spotlight-pointer> or choose
        <walkthrough-spotlight-pointer spotlightId="sql-root-password-input-nopassword">no password</walkthrough-spotlight-pointer>

1.  Click <walkthrough-spotlight-pointer spotlightId="sql-create-save">Create</walkthrough-spotlight-pointer>

## Connect to the SQL instance

The **gcloud** CLI is used to interface with the instance. This tool comes
pre-installed in the web console shell.

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

Use this command to connect to the instance:

```bash
gcloud sql connect InstanceIdHere --user=root
```

You should see a prompt similar to the following:

```terminal
MySQL [(none)]
```

## Using the SQL instance

Within the `MySQL` prompt, run the following:

1.  Create database and table

    ```sql
    CREATE DATABASE geography;
    USE geography;
    CREATE TABLE cities (city VARCHAR(255), country VARCHAR(255));
    ```

1.  Insert data

    ```sql
    INSERT INTO cities (city, country) values ("San Francisco", "USA");
    INSERT INTO cities (city, country) values ("Beijing", "China");
    ```

1.  Query

    ```sql
    SELECT * FROM cities;
    ```

    You should see the following query results:

    ```terminal
    SELECT * FROM cities;
    +---------------+---------+

    +---------------+---------+

    +---------------+---------+
    ```

## Cleanup

You'll need to cleanup the newly created resources.

1.  Navigate to SQL instances page the SQL instances page.

    <walkthrough-menu-navigation sectionId="SQL_SECTION"></walkthrough-menu-navigation>

1.  Click the <walkthrough-spotlight-pointer spotlightId="sql-instance-detail-link">
    Instance ID</walkthrough-spotlight-pointer> link to go to details page.

1.  Click <walkthrough-spotlight-pointer spotlightId="sql-instance-delete">
    Delete</walkthrough-spotlight-pointer>

## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've successfully setup a MySQL database! Here are some next steps:

**Download the Google Cloud SDK and connect to SQL locally** install the Google
Cloud SDK and connect to SQL locally.

Install the [Google Cloud SDK][cloud-sdk-installer] on your local machine.

[cloud-sdk-installer]: https://cloud.google.com/sdk/downloads#interactive

**Cloud SQL features**

Explore in [documentation][cloud-sql-features-doc]

[cloud-sql-features-doc]: https://cloud.google.com/sql/docs/features
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
