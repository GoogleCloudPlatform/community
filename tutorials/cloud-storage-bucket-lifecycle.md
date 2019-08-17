---
title: Cloud Storage bucket lifecycle
description: Learn how to automatically change an objects storage class based on file age
author: Phuurl
tags: Cloud Storage
date_published: 2019-08-17
---

# Cloud Storage bucket lifecycle

Changing the storage class of older less frequently accessed data can significantly reduce storage costs.
In this tutorial, you'll configure a bucket lifecycle to do this automatically.

## Before you begin

Before starting this tutorial, ensure you have created a bucket and uploaded some data to it.
The [Cloud Storage quickstart tutorial](https://cloud.google.com/community/tutorials/storage-quickstart) can 
help with this if you are unsure.

## Costs

Storage costs vary by volume of data and storage class.
The [pricing calculator](https://cloud.google.com/products/calculator/) can be used to estimate the cost of 
using the various storage classes.

Note that Nearline and Coldline storage classes have cheaper storage costs, but both have data retrieval charges.
If your data is frequently accessed, it may be cheaper to keep it in the standard storage class.

## Configuring bucket lifecycle

1.  Navigate to the **Storage** > **Browser** page in the console.

2.  Click **None** in the **Lifecycle** column on the bucket you are setting the lifecycle rule for.

3.  Click the **Add rule** button.

4.  Choose **Age** as the condition, and enter a suitable number of days that the object should be in the bucket 
for before changing storage class.

5.  Choose either **Set to Nearline** or **Set to Coldline** as required.

    Note that if an object is already in Coldline, a *Set to Nearline* rule will have no effect on it.

6.  Click **Continue**, then **Save**.

Objects in the bucket will now have their storage class changed once they have been in the bucket for the number 
of days you specified in step 4.

Note that after you add or edit a lifecycle rule, it may take up to 24 hours to take effect.

## Clean up

To clean up the resources from this tutorial, you can either delete the bucket, or remove the lifecycle rule that you added.

To remove the rule:

1.  Navigate to the **Storage** > **Browser** page in the console.

2.  Click **Enabled** in the **Lifecycle** column on the bucket you set the lifecycle rule for.

3.  Click the **bin icon** next to the rule that you created.

## Conclusion

Now that you know how to configure bucket lifecycles in Cloud Storage, here are some things you may want to take a look at:

*   [A comparison between the storage classes](https://cloud.google.com/storage/docs/storage-classes) on the Cloud Storage docs.
*   Learn to set bucket lifecycles with [the gsutil command-line tool](https://cloud.google.com/storage/docs/gsutil/commands/lifecycle).
