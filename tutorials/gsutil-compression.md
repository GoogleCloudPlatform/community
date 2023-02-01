---
title: Bulk Compression using gsutil & Compute Engine for same bucket
description: This tutorial is intented to provide a simpler way to compress the data already exisitng in a bucket.
author: RahulDubey391
tags: gsutil, Google Cloud Storage, Google Compute Engine, Compression, gzip
date_published: 2023-02-01
---


Rahul Dubey | Community Editor | Software Engineer | Capgemini

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial gives you a simpler and brief idea about dealing with non-compressed data existing in the bucket which you want to compress in bulk manner. There are already other exisitng methods mentioned below under **Alternative Suggestion** section but those require some developer's effort. This one only require few commands to execute to enable bulk compression over an exisiting bucket.

## Use-Case
Suppose you have dumped large number of files from Snowflake datawarehouse to GCS bucket using "COPY INTO <LOCATION-TO-GCS>" statement without any compression and chunking enabled. You want to process this data further without decompressing, but once the processing is done you want to compress it again and send to an API endpoint which applies an upload limit of 200MB with gzip compression. How to approach it without burning much compute on custom applications built by developers having not-close-to-perfect performance? Instead of reinventing the wheel, you just have to use "gsutil" commands. 


## Alternative Suggestion
According to the documentations provided by officially by Google, there are several ways you can approach this problem, but these ways require you to have some handy experience with programming and some development efforts.
  * Using Bulk Compression Dataflow template.
  * Writing a custom App Engine or Cloud Run application to handle compression logic.


## Drawbacks with Alternative Suggestions
  * For the Dataflow template, you have to understant the unified programming model provided by Apache Beam. This can be a bit challenging if you have never used it before.
  * For writing custom application, you have to be familiar Multithreading, Multiprocessing, Task Queues etc. Apart from the programming jargon, you have to understand that there are limitations with GCS API if you are using HDD type. Even if you use SSD type, your program will always be IO-Bounded and hence an efficient implementation is out of question.


## Gsutil to the rescue
Often the simpler solutions are better and highly performant when compared to the complex solution with not-so-good performance and this can escalate quickly if you are dealing with heavy amout of data in production setting. Gsutil is an elegant and simpler tool provided for GCS related worklods.

Before proceeding ahead, you have to make sure to have following services enabled:

  * GCP Account
  * Compute Engine
  * Google Cloud Storage


## Costs
For this tutorial, you will be charged for Compute Engine Instance, Google Cloud Storage.

For Google Cloud services, check this [pricing calculator](https://cloud.google.com/products/calculator/) to get a rough estimate of the charge incurred.


## Setup a Compute Engine VM instance
We will use Compute Engine VM instance to pull the existing data in GCS bucket. We assume that you have some uncompressed data residing in one of the GCS buckets.

Follow these steps to create VM instance:
  1. Go to Google Cloud Console and click on **Side Drawer**.
  2. Hover mouse pointer over **Compute Engine**. Then click on **Virtual Machines**.
  3. After the above step, a new page will open. At the top you will see **CREATE INSTANCE**. Click on it and start configuring the VM.
  4. Provide a **Name** for the instance.
  5. Set **Region** and **Zone** accordingly.
  6. Under **Machine Configuration**, set **Series** as **N2** and **Machine type** as **n2-standard-8**.
  7. Under **Boot disk** section, click on **CHANGE** and select the size of disk under **Size(GB)** as more than **100**. Since this exercise assumes you have to process large number of files and data.
  8. Also under **Access scopes**, set **Allow full acces to all Cloud APIs** as active radio button. This will ensure that VM instance is allowed to access **GCS Bucket**.
  9. Finally, click on **Create** to assign a VM instance.

After setting up the VM instance, click on **SSH** to open a terminal window. After this in the terminal type **sudo -i** to become root user. Once this is done you can follow the below steps to execute `gsutil` commands.
 
## Pulling data from GCS Bucket
In this step, we will use gsutil to pull the data in the bucket. While pulling the data, we have to use multithreading parameter "-m" for faster download. Usually the data transafer between the services in the GCP is much faster when compared to pulling data from on-premise machines.

`gsutil -m cp -r gs://<SOURCE-BUCKET>/<BLOB-PREFIX> <LOCAL-DESTINATION>`

Here the parameters are as follow:
  * `cp` - Copy command to copy the files from one location to another.
  * `-m` - Enables multithreading/multi-processing for `cp` command.
  * `-r` - Enables recursive copy execution for whole directory tree.
  * `<SOURCE-BUCKET>` - Source bucket name followed by `<BLOB-PREFIX>` for any particular folder
  * `<LOCAL-DESTINATION>` - Local path in the Compute Engine attached storage  


## Store the data back to GCS bucket with Compression enabled
Once the data is downloaded to VM isntance, we will again use gsutil command to send the data back to the bucket with the compression parameter "-z" enabled with value "csv" file format. By default if you use "-Z" instead of "-z" the "gzip" encoding is applied.

`gsutil -m cp -r -z csv <LOCAL-SOURCE>/*.csv gs://<DESTINATION-BUCKET>/<BLOB-PREFIX>/`

Here the parameters are as follow:
  * `cp` - Copy command to copy the files from one location to another.
  * `-m` - Enables multithreading/multi-processing for `cp` command.
  * `-r` - Enables recursive copy execution for whole directory tree.
  * `-z` - Enables **gzip** compression over the source files. The target file format is provided as `csv`.
  * `<LOCAL-SOURCE>` - Source path in the VM instance's local storage.
  * `<DESTINATION-BUCKET>` - Destination path of the GCS bucket. Keep the Source and Destination bucket same to avoid creating multiple files.


## Cleaning up
To avoid any charge incurred for the services used, follow these steps to clean up the service instances:
  1. Go to **Compute Engine** and select **VM Instances**. This will provide a list of instances already created.
  2. Click on checkbox next to the VM instance you created at the beginning of this tutorial.
  3. Click on **Three dot menu button** at the top right corner and click on **Delete**. This will delete the VM instance along with the data stored in the attached storage.
  4. Now go to **Google Cloud Storage** and select the bucket you have created. 
  5. After selecting the bucket, click **Delete**. This will popup a box asking to type **DELETE** in the textbox. Type it and click delete.

## What's next
As explained before, there are alternative ways for developers to follow for the compression of data.

- Learn more about [Bulk Compression using Cloud Dataflow Templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-utilities).
- Learn more about [Object Transcoding](https://cloud.google.com/storage/docs/transcoding).