---
title: Scheduling periodic jobs with Cloud Scheduler
description: Schedule virtually any job, including batch, big data jobs, cloud infrastructure operations, and more with Cloud Scheduler.
author: timtech4u
tags: Cloud Scheduler, Cron, Automation
date_published: 2019-11-21
---

Automating tasks that re-occur is definitely at the heart of every software developer. Google Cloud Platform has a tool that allows users to schedule jobs while maintaining the usual unix-cron format.  

Cloud Scheduler can be referred to as *Cronjob as a Service* tool, it is fully managed by Google Cloud Platform so you don't need to manage the scheduler's underlying infrastructure.

Cloud Scheduler can be used for multiple use cases such as making requests to an HTTP/S Endpoint, invoking a Pub/Sub topic, making database updates and push notifications, triggering CI/CD pipelines, scheduling tasks such as image uploads and sending an email, or even invoking Cloud Functions.

## Objective

In this article, we would simply use Cloud Scheduler to make simple requests to an HTTP Endpoint.  

## Before you begin

1. Set up a [Google Cloud account and project](https://cloud.google.com/gcp/getting-started/).

2. Enable [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler).

3. Copy the URL of the HTTP Endpoint you would like to make requests to.

## Get the sample code

I built a tool that periodically makes request to Cloud Run services to prevent them from having Cold Starts.

Get the code from [GitHub](https://github.com/Timtech4u/cloudrun_warmer).

## Setting up Cloud Scheduler 

Visit [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler) and click on * ➕ Create Job*

- Enter job name

- Set *Frequency* : every 24 hours

- *Target* : Select HTTP

- Set *URL* :  (Use your Application or Functions URL)

- *HTTP Method* : Select GET

*You can change values above to fit your use case.*

![Cloud-Scheduler.PNG](https://cdn.hashnode.com/res/hashnode/image/upload/v1574150947725/wE9sLzr_F.png)

## Next steps

If you face problems with HTTP headers or other issues while using Cloud Scheduler, feel free to check out  [John Hanley's](https://twitter.com/NeoPrimeAws)  answers on  [Stack Overflow.](https://stackoverflow.com/search?q=user:8016720+[google-cloud-scheduler) 

Cloud Scheduler can also be used with Firebase Cloud Functions which automatically configures Cloud Scheduler, along with a Pub/Sub topic, that invokes the function that you define using the Cloud Functions for Firebase SDK.  [Read more
](https://firebase.google.com/docs/functions/schedule-functions)

In addition, Stackdriver integrates with  Cloud Scheduler providing *powerful logging* for greater transparency into job execution and performance.

## Pricing

Cloud Scheduler is simple and pay-for-use; where you pay for the number of jobs you consume per month.  Google Cloud generously also allows you create 3 free jobs per month while you only per for others at $0.10/job/month

## Resources

If you want to learn more about Cloud Scheduler, check out the following resources:

- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs/quickstart) 

- [Scheduled Cloud Functions from Fireship ](https://fireship.io/lessons/cloud-functions-scheduled-time-trigger/)

- [Awesome List for Google Cloud Platform](https://github.com/GoogleCloudPlatform/awesome-google-cloud)

Thanks for reading through! Let [me](https://twitter.com/timtech4u) know if I missed anything, if something didn’t work out quite right for you, or if this
guide was helpful.
