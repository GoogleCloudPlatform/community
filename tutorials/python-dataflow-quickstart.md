---
title: Count words with Cloud Dataflow and Python
description: Learn the Cloud Dataflow service by running a word count example in Python.
author: jscud
tags: Dataflow
date_published: 2019-07-31
---

# Count words with Cloud Dataflow and Python

<!-- {% setvar job_name "dataflow-intro" %} -->
<!-- {% setvar project_id_no_domain "<your-project>" %} -->
<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=python_dataflow_quickstart)

</walkthrough-alt>

## Introduction

In this tutorial, you'll learn the basics of the Cloud Dataflow service by
running a simple example pipeline using Python.

Cloud Dataflow pipelines are either *batch* (processing bounded input like a file or
database table) or *streaming* (processing unbounded input from a source like
Cloud Pub/Sub). The example in this tutorial is a batch pipeline that counts
words in a collection of Shakespeare's works.

Before you start, you'll need to check for prerequisites in your GCP
project and perform initial setup.

## Project setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Set up Cloud Dataflow

To use Cloud Dataflow, enable the Cloud Dataflow APIs and open Cloud Shell.

### Enable Cloud APIs

Cloud Dataflow processes data in many GCP data stores and messaging services,
including BigQuery, Cloud Storage, and Cloud Pub/Sub. To use these services,
you must first enable their APIs.

Use the following to enable the APIs:

<walkthrough-enable-apis apis=
"compute.googleapis.com,dataflow,cloudresourcemanager.googleapis.com,logging,storage_component,storage_api,bigquery,pubsub">
</walkthrough-enable-apis>

<walkthrough-alt>
https://console.cloud.google.com/flows/enableapi?apiid=compute.googleapis.com,dataflow,cloudresourcemanager.googleapis.com,logging,storage_component,storage_api,bigquery,pubsub
</walkthrough-alt>

### Open Cloud Shell

In this tutorial, you do much of your work in Cloud Shell, which is a built-in command-line tool for the GCP Console.

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

## Install Cloud Dataflow samples

Cloud Dataflow runs jobs written using the Apache Beam SDK. To submit jobs to the
Cloud Dataflow service using Python, your development environment requires Python,
the Google Cloud SDK, and the Apache Beam SDK for Python. Additionally, Cloud
Dataflow uses pip, Python's package manager, to manage SDK dependencies.

This tutorial uses a Cloud Shell environment that has Python and pip installed. If
you prefer, you can do this tutorial [on your local machine][dataflow-python-tutorial].

### Download the samples and the Apache Beam SDK for Python

To write a Cloud Dataflow job with Python, you first need to download the SDK
from the repository.

When you run this command in Cloud Shell, pip will download and install the appropriate version
of the Apache Beam SDK:

```bash
pip install --user --quiet apache-beam[gcp]
```

## Set up a Cloud Storage bucket

Cloud Dataflow uses Cloud Storage buckets to store output data and cache your
pipeline code.

### Run gsutil mb

In Cloud Shell, use the command `gsutil mb` to create a Cloud Storage bucket:

```bash
gsutil mb gs://{{project_id_no_domain}}
```

`{{project_id_no_domain}}` is your GCP project ID.

For more information about the `gsutil` tool, see the [documentation][gsutil-docs].

## Create and launch a pipeline

In Cloud Dataflow, data processing work is represented by a *pipeline*. A
pipeline reads input data, performs transformations on that data, and then
produces output data. A pipeline's transformations might include filtering,
grouping, comparing, or joining data.

### Launch your pipeline on the Cloud Dataflow service

Use Python to launch your pipeline on the Cloud Dataflow service. The running
pipeline is referred to as a *job*.

```bash
python -m apache_beam.examples.wordcount \
  --project {{project_id}} \
  --runner DataflowRunner \
  --temp_location gs://{{project_id_no_domain}}/temp \
  --output gs://{{project_id_no_domain}}/results/output \
  --job_name dataflow-intro
```

*   `{{project_id}}` is your GCP project ID.
*   `output` is the bucket used by the WordCount example to store the job results.

### Your job is running

Congratulations! Your binary is now staged to the storage bucket that you
created earlier, and Compute Engine instances are being created. Cloud Dataflow
will split up your input file such that your data can be processed by multiple
machines in parallel.

## Monitor your job

In this section, you check the progress of your pipeline on the **Dataflow** page
in the GCP Console.

### Go to the Dataflow page

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
then select **Dataflow**.

<walkthrough-menu-navigation sectionId="DATAFLOW_SECTION"></walkthrough-menu-navigation>

### Select your job

Click the job name to view the job details.

### Explore pipeline details and metrics

Explore the pipeline on the left and the job information on the right. To see
detailed job status, click [**Logs**][spotlight-job-logs] at the top of the page.

Click a step in the pipeline to view its metrics.

As your job finishes, you'll see the job status change, and the Compute Engine
instances used by the job will stop automatically.

Note: When you see the message in Cloud Shell that the job is finished, you can close Cloud Shell.

## View your output

Now that your job has run, you can explore the output files in Cloud Storage.

### Go to the Cloud Storage page

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console,
select **Storage**, and then click **Browser**.

<walkthrough-menu-navigation sectionId=STORAGE_SECTION></walkthrough-menu-navigation>

### Go to the storage bucket

In the list of buckets, select the bucket that you created earlier.

The bucket contains output and temp folders. Dataflow saves the
output in shards, so your bucket will contain several output files.

The temp folder is for staging binaries needed by the workers and for
temporary files needed by the job execution.

## Clean up

To prevent being charged for Cloud Storage usage, delete the bucket you
created.

1.  Click the [**Buckets**][spotlight-buckets-link] link to go back to the bucket browser.

1.  Check the box next to the bucket that you created.

1.  Click the [**Delete**][spotlight-delete-bucket] button at the top of the GCP Console, and
    confirm the deletion.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Here's what you can do next:

*   [Read more about the WordCount example][wordcount]
*   [Learn about the Cloud Dataflow programming model][df-pipelines]
*   [Explore the Apache Beam SDK on GitHub][beam-sdk]

Set up your local environment:

*   [Use Java and Eclipse to run Cloud Dataflow][df-eclipse]
*   [Use Java and Maven to run Cloud Dataflow][df-maven]

[df-eclipse]: https://cloud.google.com/dataflow/docs/quickstarts/quickstart-java-eclipse
[df-maven]: https://cloud.google.com/dataflow/docs/quickstarts/quickstart-java-maven
[df-pipelines]: https://cloud.google.com/dataflow/model/programming-model-beam
[beam-sdk]: https://github.com/apache/beam/tree/master/sdks/python
[wordcount]: https://beam.apache.org/get-started/wordcount-example/
[gsutil-docs]: https://cloud.google.com/storage/docs/gsutil
[dataflow-python-tutorial]: https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python
[spotlight-job-logs]: walkthrough://spotlight-pointer?cssSelector=#p6n-dax-job-logs-toggle
[spotlight-buckets-link]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-path-link
[spotlight-delete-bucket]: walkthrough://spotlight-pointer?cssSelector=#p6n-cloudstorage-delete-buckets
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
