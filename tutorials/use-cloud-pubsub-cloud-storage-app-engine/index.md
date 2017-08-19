---
title: How to Use Cloud Pub/Sub Notifications and Cloud Storage with App Engine
description: Create a shared photo album using Cloud Pub/Sub, Cloud Storage, Datastore, and App Engine.
author: ggchien, cmwoods
tags: App Engine, Cloud Pub/Sub, Cloud Storage, GCS, Datastore, photo album
date published: 2017-08-17
---
Some sort of intro here.

## Objectives

* Store photos in Google Cloud Storage buckets.
* Store entities in Datastore.
* Configure Cloud Pub/Sub notifications.
* Use Google Cloud Vision to implement a photos search.
* Create and deploy a shared photo album as an App Engine project to display actions performed through the Cloud Platform Console.

## Costs

This tutorial uses billable components of Cloud Platform, including:

* Google App Engine
* Google Cloud Storage
* Google Cloud Datastore
* Google Cloud Pub/Sub
* Google Cloud Vision

Use the [pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538) to generate a cost estimate based on your projected usage. New Cloud Platform users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Overview

This tutorial teaches you how to integrate several Google products to simulate a shared photo album, hosted on App Engine and managed through the Cloud Platform Console. The diagram below shows the overall flow of the application:

![alt text](link to image here "Shared Photo App Workflow")

Two buckets exist in [Cloud Storage](https://cloud.google.com/storage/) (GCS): one to store the uploaded photos themselves, and the other to store the thumbnails of the uploaded photos. [Cloud Datastore](https://cloud.google.com/datastore/) stores all non-image entities needed for the web application, which is hosted on [App Engine](https://cloud.google.com/appengine/). Notifications of changes to the GCS photo bucket are sent to the application via [Cloud Pub/Sub](https://cloud.google.com/pubsub/). The [Google Cloud Vision API Client Library](https://developers.google.com/api-client-library/python/apis/vision/v1) is used to label photos for search. Further detail is revealed in later portions of this tutorial.

Note: Basic coding knowledge is necessary to complete this tutorial.

## Set Up

The following instructions assume no prior set up has been done. Skip steps appropriately if you have already completed them.
1. [Install the Google Cloud SDK](https://cloud.google.com/sdk/downloads) for necessary commands such as `gcloud` and `gsutil`.
2. [Create a Pantheon account](https://console.cloud.google.com/) for use of the Cloud Platform Console.
3. In Pantheon, navigate to the upper header bar and create a new project for use as your App Engine project. (Billing?) Your project has a unique ID that is part of your web application url.
4. In the command line, [set the default project](https://cloud.google.com/sdk/docs/managing-configurations) to your newly created project by running the following command:
  ```sh
  gcloud config set project [PROJECT ID]
  ```
5. In Pantheon, click on the ![alt text](insert three bar icon link "Products & Services") icon in the upper left hand corner to open the `Products & Services` menu. Click on `Storage`. In the browser, create a bucket with `Multi-Regional` or `Regional` storage. This bucket is for storing the photos of your shared photo album.
6. If you want collaborators on your photo album, click on the three-dots icon for your photo bucket on the right side of the screen. Click `Edit bucket permissions` and add the email addresses of the collaborators as `Storage Admins`.
7. Change the photos bucket permissions to make it publicly readable so that the photos may be viewed on your website. in the command line, run:
  ```sh
  gsutil defacl ch -g allUsers:R gs://[PHOTO BUCKET NAME]
  ```
8. Create another bucket with `Multi-Regional` or `Regional` storage. This bucket is for storing the thumbnails of the photos in your shared photo album.
9. Open the `Products & Services` menu and click on `Pub/Sub`. Create a new topic with the same name as your photos bucket.
10. Click on the three-dots icon for your photo album topic and click on `New subscription`. Change the `Delivery Type` to `Push into an endpoint url`. Your url should be something of the format
  ```sh
  https://[YOUR PROJECT ID].appspot.com/_ah/push-handlers/receive_message
  ```
This is the url that receives your Cloud Pub/Sub messages.

11. Configure Cloud Pub/Sub notifications for your photos bucket by running
  ```sh
  gsutil notification create -f json gs://[PHOTO BUCKET NAME]
  ```
  
## Basic Application Layout

1.
