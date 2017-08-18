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

## Set Up

1. 
