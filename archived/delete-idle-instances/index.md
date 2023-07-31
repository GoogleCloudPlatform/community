---
title: Delete idle Compute Engine instances automatically
description: Use a simple and scalable serverless mechanism to automatically delete Compute Engine instances that are not in active use.
author: jpatokal
tags: garbage collection, Cloud Scheduler, Cloud Functions
date_published: 2021-03-19
---

Jani Patokallio | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial offers a simple and scalable serverless mechanism to automatically delete
([*garbage-collect*](https://en.wikipedia.org/wiki/Garbage_collection_(computer_science))) Compute Engine virtual machine (VM) instances that are marked as idle.

Some cases in which this may be useful:

* Developers or testers create one-off VM instances for testing a feature, but they might not always remember to manually delete the instances.
* Workflows can require dynamically starting a large number of Compute Engine worker instances to perform a certain task. A best practice is to have instances 
  delete themselves after the task is complete, but ensuring that this always happens can be difficult if the task is distributed or some workers stop because
  of errors.

Idle VM recommendations are generated automatically based on system utilization over the past 14 days. They are not available for some types of instances, 
including VMs belonging to managed instance groups, managed services like Dataflow or Google Kubernetes Engine, or instances with local resources like local 
SSDs, GPUs, or TPUS. For the full list of limitations, see
[Viewing and applying idle VM recommendations](https://cloud.google.com/compute/docs/instances/viewing-and-applying-idle-vm-recommendations#limitations).

## How it works 

The following diagram shows a high-level overview of the solution:

![High-level overview of the solution](https://storage.googleapis.com/gcp-community/tutorials/delete-idle-instances/overview.svg)

The overall flow is the following:

1.  A Cloud Scheduler cron job is triggered regularly (for example, once a day). The Cloud Scheduler configuration specifies the label of the 
    pool of VM instances to target and whether or not they should be deleted, using the following format:
    
        '{"label":"env=test,action=mark"}'

    If the configuration is empty (`{}`), all VM instances are considered targets.
	
1.  When the cron job is triggered, Cloud Scheduler calls a Cloud Function with the payload.
1.  Each time the function is triggered, it does the following: 
    1.  Queries the Idle VM Recommender for a list of idle Compute Engine instances.
    1.  Filters the list for instances that have the target label.
    1.  Iterates through the instances and does the following: 
        *   If the Cloud Scheduler configuration includes the label `action=stop`, then the target is immediately stopped and the recommendation status is set to
            `SUCCEEDED`.
        *   If the Cloud Scheduler configuration includes the label `action=delete`, then the target is immediately deleted and the recommendation status is set 
            to `SUCCEEDED`.
        *   Otherwise, the label `delete=true` is applied to the instance and the recommendation status is set to `CLAIMED`.

By default, potential idle instances are only labeled. You can obtain the list of labeled instances by checking recommendation status or searching for instances
with the label.

## Costs

This tutorial uses the following Google Cloud components: 

*   Compute Engine
*   Cloud Scheduler
*   Cloud Functions
*   Recommender API

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on this projected usage. 

Cloud Scheduler is free for up to 3 jobs per month.

New Google Cloud users may be eligible for a [free trial](http://cloud.google.com/free-trial).

## Before you begin

The following steps create a new project and new VM instances, so idle VM instance recommendations may not be generated until 14 days of system metrics are 
available. For immediate results, you can deploy this in an existing project with idle instances instead.

1.  If you don’t already have one, create a [Google Account](https://accounts.google.com/SignUp).
1.  Create a Google Cloud project: In the [Cloud Console](https://console.cloud.google.com/project), click **Create project**.
1.  [Enable billing for the project](https://support.google.com/cloud/answer/6293499#enable-billing).
1.  Open [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell).
1.  Create an App Engine app, which is required by Cloud Scheduler:

        gcloud app create --region=us-central
    
1.  Enable the APIs used by this tutorial:

        gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com \
          cloudfunctions.googleapis.com cloudscheduler.googleapis.com compute.googleapis.com \
          recommender.googleapis.com
    
## Set up the automated cleanup code

Run the commands in this section in Cloud Shell.

1.  Clone the GitHub repository:

        git clone https://github.com/GoogleCloudPlatform/community

1.  Go to the `delete-idle-instances` directory:

        cd community/tutorials/delete-idle-instances
	
1.  Create a service account for Cloud Scheduler to use:

        gcloud iam service-accounts create scheduler-sa --display-name "Cloud Scheduler service account"
        export SCHEDULER_SA=scheduler-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com

1.  Assign the IAM roles needed to allow this service account to invoke Cloud Functions and
    administer Compute Engine recommendations and instances:

        gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
          --member serviceAccount:${SCHEDULER_SA} \
          --role roles/cloudfunctions.invoker
        gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
          --member serviceAccount:${SCHEDULER_SA} \
          --role roles/compute.instanceAdmin
        gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
          --member serviceAccount:${SCHEDULER_SA} \
          --role roles/recommender.computeAdmin

1.  Deploy the Cloud Function that marks idle instances:

        gcloud functions deploy mark_idle_instances --trigger-http --region us-central1 --runtime=nodejs12 \
          --service-account ${SCHEDULER_SA} --entry-point=deleteIdleInstances --no-allow-unauthenticated

    **Note**: The Cloud Function runs with the default App Engine service account, which has project `editor` rights.

1.  Configure Cloud Scheduler to invoke the Cloud Function once per day:

        gcloud scheduler jobs create http mark-idle-instances-job --schedule="0 0 * * *" \
          --uri "https://us-central1-${GOOGLE_CLOUD_PROJECT}.cloudfunctions.net/mark_idle_instances" \
          --http-method POST --oidc-service-account-email ${SCHEDULER_SA} \
          --message-body='{"label":"env=test"}'

    The schedule is specified in [unix-cron format](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules).
    `0 0 * * *` means that the jobs runs at 0:00 (midnight) UTC every day of the month, every month, and every day of the week. More simply put, the job runs 
    once per day.

1.  Verify that the job has been created:

        gcloud scheduler jobs list

    Jobs also appear on the [**Cloud Scheduler** page](https://console.cloud.google.com/cloudscheduler) in the Cloud Console. On that page, you can view
    execution logs for each job by clicking **View** in the **Logs** column.

## Test the automated tagging

1.  Create a test instance labeled `env=test`:

        gcloud compute instances create idle-test --zone=us-central1-a \
          --machine-type=n1-standard-1 --labels=env=test

1.  Check that the new instance has started successfully:

        gcloud compute instances list --format='table(name,status,labels.list())'

1.  Wait 14 days and run the same command again:

        gcloud compute instances list --format='table(name,status,labels.list())'

    The `idle-test` instance should be shown as `RUNNING` with the label `delete=true` now applied.

1.  List and review instances marked for deletion:

        gcloud compute instances list --filter='labels.delete=true' --format='value(name)'

1.  (Optional) Delete the instances that are marked for deletion:

        gcloud compute instances delete |\
        $(gcloud compute instances list --filter='labels.delete=true' --format='value(name)')

You can also see the Cloud Function execution results, including the names of the marked instances, by viewing the Cloud Function logs from the
[**Cloud Functions** page](https://console.colud.google.com/functions/list) in the Cloud Console.

## Shut down resources used in the tutorial

After you have tested the automated cleanup of VM instances, you can either
[delete the entire project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects) or delete the individual resources
that you created to prevent further billing for them on your account.

- You can delete the Cloud Scheduler job on the [**Cloud Scheduler** page](https://console.cloud.google.com/cloudscheduler) in the Cloud Console.

- You can delete the Cloud Function on the [**Cloud Functions** page](https://console.cloud.google.com/functions) in the Cloud Console.
