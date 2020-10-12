---
title: Cleaning up Compute Engine instances at scale
description: Use a simple and scalable serverless mechanism to automatically delete Compute Engine instances after a specified amount of time.
author: hbougdal,jpatokal
tags: garbage collection
date_published: 2020-10-14
---

This tutorial offers a simple and scalable serverless mechanism to automatically delete
([*garbage-collect*](https://en.wikipedia.org/wiki/Garbage_collection_(computer_science))) Compute Engine vitual machine (VM) instances after a specified amount
of time.

Some use cases where this may be be useful:

* Developers or testers create one-off VM instances for testing a feature, but they might not always remember to manually delete the instances.
* Workflows can require dynamically starting a large number of Compute Engine worker instances to perform a certain task. A best practice is to have instances 
  delete themselves after the task is complete, but ensuring that this always happens can be difficult if the task is distributed or some workers stop because
  of errors.

This tutorial uses the following Google Cloud components: 

*   Compute Engine
*   Cloud Scheduler
*   Pub/Sub
*   Cloud Functions

The following diagram shows a high-level overview of the solution:

![High-level overview of the solution](https://storage.googleapis.com/gcp-community/tutorials/cleaning-up-at-scale/overview.svg)

## How it works 

Each Compute Engine instance in scope is assigned two labels:

*   **TTL** (time to live): Indicates (in minutes) after how much time this VM will not be needed and can be deleted.
*   **ENV**: Indicates that the instance is part of the pool of VMs that can be checked regularly and can be deleted if the TTL is reached. 

The overall flow is the following:

1.  A Cloud Scheduler cron job is triggered regularly (for example, every 5 minutes). The Cloud Scheduler configuration specifies the label of the 
    pool of VMs to target, using the following format: `'{"label":"env=test"}'`
1.  When the cron job is triggered, Cloud Scheduler pushes a message with the payload above to a Pub/Sub topic.
1.  A Cloud Function is subscribed to the Pub/Sub topic. Each time the function is triggered, it does the following: 
    1.  Reads the payload of the Pub/Sub message and extracts the label.
    1.  Filters all of the Compute Engine instances that have the label.
    1.  Iterates through the instances and does the following: 
        1.  Reads the value of the TTL label for each instance.
        1.  Calculates the difference between the current time and the creation time of each instance. 
        1.  If the difference is greater than the TTL, then the instance is deleted. If not, nothing is done.

## Prerequisites

1.  If you don’t already have one, create a [Google Account](https://accounts.google.com/SignUp).

1.  Create and configure a Google Cloud project:
    1.  In the [Cloud Console](https://console.cloud.google.com/project), select **Create Project**.
    1.  [Enable billing for the project](https://support.google.com/cloud/answer/6293499#enable-billing).
    1.  Open [Cloud Shell][https://cloud.google.com/shell/docs/using-cloud-shell] and create an App Engine app:

            gcloud app create --region=us-central
	    
	The App Engine app is required by Cloud Scheduler.
    
    1.  Enable the APIs used by this tutorial:

            gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com \
              cloudfunctions.googleapis.com cloudscheduler.googleapis.com compute.googleapis.com \
              pubsub.googleapis.com
    
This tutorial uses several billable components of Google Cloud. To estimate the cost of running this sample, assume that you run a single `f1-micro` 
Compute Engine instance for a total of 15 minutes on one day while you test the sample, after which you delete the project, releasing all resources. 

Use the [Google Cloud Platform Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on this projected usage. 

Cloud Scheduler is free for up to 3 jobs per month.

New Google Cloud users may be eligible for a [free trial](http://cloud.google.com/free-trial).

## Set up the sample

1.  To clone the GitHub repository, run the following command in Cloud Shell:

        git clone https://github.com/GoogleCloudPlatform/community

1.  Change directories to the `cleaning-up-at-scale` directory:

        cd community/tutorials/cleaning-up-at-scale
	
    The exact path depends on where you placed the directory when you cloned the sample files from GitHub.

1.  Create the Pub/Sub topic that you will push messages to:

        gcloud pubsub topics create unused-instances

    The topic is now listed under `gcloud pubsub topics list`.  You can also see the topic
    in the console: Big Data > Pub/Sub

1.  Deploy the Cloud Function that will monitor the Pub/Sub topic and clean up instances:

        gcloud functions deploy clean-unused-instances --trigger-topic=unused-instances --runtime=nodejs12 --entry-point=cleanUnusedInstances

1.  Configure Cloud Scheduler to push a message containing the target label every minute to the Pub/Sub topic `unused-instances`:

        gcloud scheduler jobs create pubsub clean-unused-instances-job --schedule="* * * * *" \
          --topic=unused-instances --message-body='{"label":"env=test"}'

    The `schedule` is specified in [unix-cron format](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules).
    A `*` in every field means the job runs every minute, every hour, every day of the month, every month, every day of the week.
    More simply put, it runs once per minute.

    If scanning large numbers of VMs, running less often (such as once an hour) is likely sufficient.

The job is now visible in `gcloud scheduler jobs list`.  You can also see the jobs 
in the console: Tools > Cloud Scheduler 

Scheduler execution logs for the job are visible via the Logs link for each job.

## Test the automated clean-up

1.  Create a test instance labeled `env=test` with a two-minute TTL:

        gcloud compute instances create cleanup-test --zone=us-central1-a --machine-type=f1-micro \
          --labels=env=test,ttl=2

1.  Check that the new instance has started successfully.

        gcloud compute instances list

1.  Wait two minutes and run the same command again:

        gcloud compute instances list

    The instance should have been automatically deleted.

You can also see the Cloud Function execution results, including the name of the deleted instance, under Cloud Function Logs in the console.

### Clean up

Now that you have tested the sample, delete the resources that you created to prevent further billing for them on your account.

1.  Delete the Cloud Scheduler job.

    You can delete the job from the Cloud Scheduler section of the [Cloud Console](https://console.cloud.google.com).

1.  Delete the Cloud Pub/Sub topic.

    You can delete the topic and associated subscriptions from the Cloud Pub/Sub section of the [Cloud Console](https://console.cloud.google.com).
