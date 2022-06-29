---
title: Tutorial template
description: Replace with a description of your tutorial, focusing on what the reader will learn.
author: github-username-for-author,github-username-for-other-author
tags: replace, with, tags, not, in, title, or, description
date_published: 2020-04-28
---

Todd Kopriva | Community Editor | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

To begin creating a tutorial, copy the Markdown source for this tutorial template into your blank Markdown file. Replace the explanatory text and examples with 
your own tutorial content. Not all documents will use all of the sections described in this template. For example, a conceptual document or code walkthrough
might not include the "Costs" or "Cleaning up" sections. For more information, see the 
[style guide](https://cloud.google.com/community/tutorials/styleguide) and [contribution guide](https://cloud.google.com/community/tutorials/write).

Replace the placeholders in the metadata at the top of the Markdown file with your own values. Follow the guidance provided by the placeholder values for spacing
and punctuation.

The first line after the metadata should be your name and an optional job description and organization affiliation.

After that is one of two banners that indicates whether the document was contributed by a Google employee. Just leave one banner and delete the other one.

The first paragraph or two of the tutorial should tell the reader the following:

  * Who the tutorial is for
  * What they will learn from the tutorial
  * What prerequisite knowledge they need for the tutorial

Don't use a heading like **Overview** or **Introduction**. Just get right to it.

## Objectives

Give the reader a high-level summary of what steps they take during the tutorial. This information is often most effective as a short bulleted list.

### Example: Objectives

*   Create a service account with limited access.
*   Create a Cloud Function that triggers on HTTP.
*   Create a Cloud Scheduler job that targets an HTTP endpoint.
*   Run the Cloud Scheduler job. 
*   Verify success of the job.

## Costs

Tell the reader which technologies the tutorial uses and what it costs to use them.

For Google Cloud services, link to the preconfigured [pricing calculator](https://cloud.google.com/products/calculator/) if possible.

If there are no costs to be incurred, state that.

### Example: Costs 

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Scheduler](https://cloud.google.com/scheduler)
*   [App Engine](https://cloud.google.com/appengine/docs/flexible/python)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

Give a numbered sequence of procedural steps that the reader must take to set up their environment before getting into the main tutorial.

Don't assume anything about the reader's environment. You can include simple installation instructions of only a few steps, but provide links to installation
instructions for anything more complex.

### Example: Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1.  Create an account with the BigQuery free tier. See
    [this video from Google](https://www.youtube.com/watch?v=w4mzE--sprY&list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq&index=2) for detailed instructions.
1.  Create a Google Cloud project in the [Cloud console](https://console.cloud.google.com/).
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

1.  In the Cloud console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

Tell the reader what they should read or watch next if they're interested in learning more.

### Example: What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
