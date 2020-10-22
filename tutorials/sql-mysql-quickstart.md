---
title: Set up a MySQL database with Cloud SQL
description: Set up a MySQL database with Cloud SQL on Google Cloud.
author: jscud
tags: Cloud SQL
date_published: 2019-07-31
---

# Set up a MySQL database with Cloud SQL

<walkthrough-tutorial-duration duration="10"></walkthrough-tutorial-duration>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=sql_mysql_quickstart)

</walkthrough-alt>

## Overview

In this tutorial, you will do the following:

1.  Create a new MySQL instance.
2.  Set up and query a database.
3.  Clean up the resources used in the tutorial.

## Project setup

Google Cloud organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Create a MySQL instance

1.  Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
    then select **SQL**.
    <walkthrough-menu-navigation sectionId="SQL_SECTION"></walkthrough-menu-navigation>

1.  Click <walkthrough-spotlight-pointer spotlightId="sql-zero-state-create-button">**Create instance**</walkthrough-spotlight-pointer>.

1.  Click **Choose MySQL**.

1.  Configure the instance.

    The default configuration should be sufficient.
    
    Make note of these values; you'll use them later:

    *   <walkthrough-spotlight-pointer spotlightId="sql-instance-id-input">**Instance ID**</walkthrough-spotlight-pointer>
    *   <walkthrough-spotlight-pointer spotlightId="sql-root-password-input">**Root password**</walkthrough-spotlight-pointer> 
        (or choose
        <walkthrough-spotlight-pointer spotlightId="sql-root-password-input-nopassword">**No password**</walkthrough-spotlight-pointer>)

1.  Click <walkthrough-spotlight-pointer spotlightId="sql-create-save">**Create**</walkthrough-spotlight-pointer>.

## Connect to the SQL instance

In this tutorial, you do much of your work in Cloud Shell, which is a built-in command-line tool for the Cloud Console.

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

Use this command to connect to the instance, replacing `[INSTANCE_ID]` with the instance ID that you noted
in the previous step:

```bash
gcloud sql connect [INSTANCE_ID] --user=root
```

You should see a prompt similar to the following:

```terminal
MySQL [(none)]
```

## Using the SQL instance

At the `MySQL` prompt, run the following commands:

1.  Create the database and table:

        CREATE DATABASE geography;
        USE geography;
        CREATE TABLE cities (city VARCHAR(255), country VARCHAR(255));

1.  Insert data:

        INSERT INTO cities (city, country) values ("San Francisco", "USA");
        INSERT INTO cities (city, country) values ("Beijing", "China");

1.  Query:

        SELECT * FROM cities;

## Cleanup

The last step is to clean up the newly created resources.

1.  Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
    then select **SQL**.
    <walkthrough-menu-navigation sectionId="SQL_SECTION"></walkthrough-menu-navigation>

1.  Click the <walkthrough-spotlight-pointer spotlightId="sql-instance-detail-link">
    Instance ID</walkthrough-spotlight-pointer> link to go to **Instance details** page.

1.  Click the **Delete** button at the top of the page.

## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've successfully set up a MySQL database! 

Here are some next steps that you can take:

*   Download the [Cloud SDK](https://cloud.google.com/sdk/downloads#interactive) on your local machine so that
    you can connect to SQL locally.
*   Explore Cloud SQL features in the [Cloud SQL documentation](https://cloud.google.com/sql/docs/features)

[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
