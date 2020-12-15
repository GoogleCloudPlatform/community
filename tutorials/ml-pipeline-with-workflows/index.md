---
title: Creating a custom ML pipeline with Cloud Workflows and serverless services on GCP
description: Learn about using Cloud Workflows to create a custom ML pipeline.
author: enakai00
tags: Cloud Workflows, Cloud Run, Dataflow, AI Platform
date_published: 2021-xx-xx
---

Etsuji Nakai | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how you can use [Cloud Workflows](https://cloud.google.com/workflows) and other serverless services, such as [Cloud Run](https://cloud.google.com/run), to create a custom ML pipeline. The ML usecase is based on the [babyweight model example](https://github.com/GoogleCloudPlatform/training-data-analyst/blob/master/blogs/babyweight_keras/babyweight.ipynb). The following diagram shows the overall architecture of what you build in this tutorial.

<img src="https://github.com/enakai00/workflows-ml-pipeline-example/blob/main/docs/img/architecture.png" width="640px">

* You deploy two microservices on Cloud Run. One is to launch a Dataflow pipeline to preprocess the training data. The orignal data stored in BigQuery are coverted to CSV files and stored in Cloud Storage bucket. The other is to launch a ML training job on Cloud AI Platform, and deploy the trained model for predctions. The ML model files are cloned from the GitHub repository.

* You deploy a Cloud Workflows template to automate the whole process.


The first paragraph or two of the tutorial should tell the reader the following:

  * Who the tutorial is for
  * What they will learn from the tutorial
  * What prerequisite knowledge they need for the tutorial

Don't use a heading like **Overview** or **Introduction**. Just get right to it.

## Objectives

*   Deploy a microservice that launchs a Dataflow pipeline.
*   Deploy a microservice that launchs a ML training job on Cloud AI Platform and deploy the trained model for predictions.
*   Deploy a Cloud Workflow template to automate the whole process.
*   Execute a Cloud Workflow job.

## Costs

This tutorial uses billable components of Google Cloud, including:

* [Cloud Workflows](https://cloud.google.com/workflows)
* [Cloud Run](https://cloud.google.com/run)
* [Dataflow](https://cloud.google.com/dataflow)
* [AI Platform](https://cloud.google.com/ai-platform)
* [Cloud Build](https://cloud.google.com/cloud-build)
* [Cloud Storage](https://cloud.google.com/storage)

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage.

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
