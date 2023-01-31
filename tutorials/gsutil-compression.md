---
title: Compression using gsutil & Compute Engine
description: This tutorial is intented to provide an alternate way to compress the data already exisitng in a bucket.
author: RahulDubey391
tags: #gsutil, #compression, #gzip
date_published: 2023-01-31
---


Rahul Dubey | Community Editor | Software Engineer | Capgemini

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial is to provide a brief workflow to allow the users who are facing the issue of non-compressed data in the Google Cloud Storage bucket and wants to compress it within the same bucket. But the very first question comes up is Why? Because the Google Cloud Storage buckets are blob storages and doesn't follow the same rules as with the local File System and hence the file manipulation applied to the stored blobs only creates new blobs inplace of the existing one. One such case is compression on upload.

According to the Google Cloud Platform standard documentation, it is suggested that compression can only be applied while using gsutil when uploading the data to the bucket, but same gsutil command cannot be use to compress the data which is already there in the bucket.

## Use-Case
Suppose you have just dumped alot of data from Snowflake datawarehouse to GCS bucket using "COPY INTO <LOCATION-TO-GCS>" statement without any compression applied since you want to process this data further without decompressing, but once the processing is done you want to compress it again and send to an API endpoint which applies an upload limit of 200MB with gzip compression. How to approach it without burning much compute on custom applications built by developers having inefficient code. Instead of reinventing the wheel, you just have to use "gsutil" commands in multithread setting to efficiently compress the data. 

Before proceeding ahead, you have to make sure to have following services enabled:

  * GCP Account
  * Compute Engine
  * Google Cloud Storage

## Setup a Compute Engine VM instance

We will use Compute Engine VM instance to pull the existing data in GCS bucket. We assume that you have some uncompressed data residing in one of the GCS buckets.

## Pulling data from GCS Bucket

In this step, we will use gsutil to pull the data in the bucket. While pulling the data, we have to use multithreading parameter "-m" for faster download. Usually the data transafer between the services in the GCP is much faster when compared to pulling data from on-premise machines.

## Store the data back to GCS bucket with Compression enabled

Once the data is downloaded to VM isntance, we will again use gsutil command to send the data back to the bucket with the compression parameter "-z" enabled with value "csv" file format. By default if you use "-Z" instead of "-z" the "gzip" encoding is applied.

## Deleting the Compute Engine VM instance

After completing the compression step, you can stop and delete the VM instance to stop any cost from incurring. Since for this exercise, the configuration used for VM instance is heavy, be careful to not leave the instance running.

## Costs

Tell the reader which technologies the tutorial uses and what it costs to use them.

For Google Cloud services, link to the preconfigured [pricing calculator](https://cloud.google.com/products/calculator/) if possible.

If there are no costs to be incurred, state that.

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
