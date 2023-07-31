---
title: Add a lifecycle rule for a Cloud Storage bucket
description: Learn how to automatically change an object's storage class based on file age.
author: Phuurl
tags: Cloud Storage
date_published: 2019-09-03
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Changing the storage class of older, less frequently accessed data can significantly reduce storage costs.
In this tutorial, you configure a bucket lifecycle to do this automatically.

## Before you begin

Before starting this tutorial, ensure that you have created a bucket and uploaded some data to it.
The [Cloud Storage quickstart tutorial](https://cloud.google.com/community/tutorials/storage-quickstart) can 
help with this if you are unsure.

## Costs

Storage costs vary by volume of data and storage class.
You can use the [pricing calculator](https://cloud.google.com/products/calculator/) to estimate the cost of 
using various storage classes.

Note that Nearline Storage and Coldline Storage classes have cheaper storage costs, but both have data retrieval charges.
If your data is frequently accessed, it may be cheaper to keep it in the Standard Storage class.

## Add a lifecycle rule to automatically change the storage class

1.  Navigate to the [**Storage > Browser** page](https://console.cloud.google.com/storage/browser) in the Cloud Console.

2.  Click **None** in the **Lifecycle** column for the bucket that you are setting the lifecycle rule for.

3.  Click the **Add rule** button.

4.  Choose **Age** as the condition, and enter a number of days that the object should be in the bucket 
    for before changing storage class.

5.  Choose **Set to Nearline** or **Set to Coldline**.

    Note that if an object is already in the Coldline Storage class, **Set to Nearline** will have no effect on it.

6.  Click **Continue**, and then click **Save**.

With this rule, objects in the bucket will have their storage class changed after they have been in the bucket for the number 
of days that you specified in step 4.

Changes to a lifecycle rule take up to 24 hours to take effect.

## Clean up

To clean up the resources for this tutorial, you can either delete the bucket or remove the lifecycle rule that
you added.

To remove the rule, do the following:

1.  Navigate to the [**Storage > Browser** page](https://console.cloud.google.com/storage/browser) in the Cloud Console.

2.  Click **Enabled** in the **Lifecycle** column on the bucket that you set the lifecycle rule for.

3.  Click the delete button (trash-can icon) for the rule that you created.

## What's next

Now that you know how to configure bucket lifecycles in Cloud Storage, here are some things you may want to look at:

*   [A comparison between the storage classes](https://cloud.google.com/storage/docs/storage-classes) in the Cloud
    Storage documentation.
*   Learn to set bucket lifecycles with
    [the `gsutil` command-line tool](https://cloud.google.com/storage/docs/gsutil/commands/lifecycle).
