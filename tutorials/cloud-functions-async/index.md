---
title: Asynchronous patterns for Cloud Functions
description: Build a simple HTTP function API for long running job or tasks.
author: ptone
tags: Cloud Functions, Cloud Firestore, serverless
date_published: 2019-03-08
---

Preston Holmes | Solution Architect | Google

<!-- diagram sources: https://docs.google.com/presentation/d/1s01eqo3YUKiskJwSESW-T17IeUQf3DLCT_lvuAV7CwM/edit#slide=id.g4fb0d7b3af_0_0 -->

## Introduction

This tutorial demonstrates how to use [Cloud Functions](https://cloud.google.com/functions/) to extend the synchronous
web-hook-style request/response to longer-running jobs, with a focus on trackable and stateful long-running operations.

When a caller makes a request of a service, the caller is asking the service to perform some work. There are three 
integration patterns that can be applied, depending on the use-case:

### Synchronous request/response
![sync](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-async/sync-request.png)

The caller will wait until the work is done, expecting a result. This pattern can be directly and simply handled
by [Cloud Functions](https://cloud.google.com/functions/) with
an [HTTP trigger](https://cloud.google.com/functions/docs/calling/http).

### Asynchronous work queue
![work-queue](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-async/work-queue.png)

The caller does not need to wait for the work to be done, and does not need to follow up on the completion status.

There are a couple ways this can be solved on Google Cloud Platform in a serverless way. You can use Cloud Pub/Sub
patterns for [long-running tasks](https://cloud.google.com/solutions/using-cloud-pub-sub-long-running-tasks) or you
can use a dedicated service with [Cloud Tasks](https://cloud.google.com/tasks/).

### Asynchronous stateful jobs
![](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-async/stateful-job.png)

The caller does not need to wait for the work to be done, but it does need the ability to inquire about the completion
of the request.

This pattern is common enough that Google has defined a standard of a [long-running-operation API contract](https://github.com/googleapis/googleapis/tree/master/google/longrunning) used in multiple APIs.

This is a high-level pattern. What about a job state is tracked and how work is performed will vary by use-case.
This tutorial goes deeper into this pattern.

## Serverless stateful jobs

This tutorial uses several managed services to implement the asynchronous stateful jobs pattern,
including [Cloud Pub/Sub](https://cloud.google.com/pubsub/) and [Cloud Firestore](https://cloud.google.com/firestore/).

![](https://storage.googleapis.com/gcp-community/tutorials/cloud-functions-async/arch.png)

You can implement this pattern with alternative components. You can use Cloud SQL for job state storage or Cloud
Tasks for the work queue. This tutorial uses the support of [Go](https://golang.org/) in Cloud Functions, but any
supported language can be used to fulfill the pattern.

### Job resource definition

A simple custom job definition is defined as follows:

    type JobState int

    const (
        Created JobState = iota
        Running
        Completed
        Failed
    )

    type Job struct {
        ID         string    `json:"id"`
        CreateTime time.Time `json:"created-time"`
        DoneTime   time.Time `json:"done-time" firestore:"DoneTime,omitempty"`
        Done       bool
        Result     string
        State      JobState
        Task       map[string]interface{} `json:"-"`
        // can add a requester, source IP etc if needed
    }


When a job request is received, it is given an ID, and the details of the work are included in a task field.
This task is sent into the work queue as a Cloud Pub/Sub payload, with the job ID as a
[Cloud Pub/Sub attribute](https://cloud.google.com/pubsub/docs/publisher#custom-attributes). When a worker picks up
the task, it moves the job from `Created` to `Running`. When the task is complete, it moves from `Running` to `Completed`
(success) or `Failed` and writes any result back into the Cloud Firestore document.

## Setup

1.  Create a project in the [GCP Console][console].
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Use [Cloud Shell][shell] or install the [Google Cloud SDK][sdk].
1.  Enable Cloud Functions, Firestore, and Pub/Sub APIs:

        gcloud services enable cloudfunctions.googleapis.com firestore.googleapis.com pubsub.googleapis.com
	    
1.  Install [`jq`][jq], [`curl`][curl], and [`watch`][watch]. These tools are already in Cloud Shell,
    but install them if you are running this tutoral from your local machine.

[console]: https://console.cloud.google.com/
[shell]: https://cloud.google.com/shell/
[sdk]: https://cloud.google.com/sdk/

Commands in this tutorial assume that you are running from the tutorial folder:

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community/tutorials/cloud-functions-async

### Create Cloud Pub/Sub resources

    gcloud pubsub topics create jobs
    gcloud pubsub subscriptions create worker-tasks --topic jobs

### Create the Cloud Firestore database

Cloud Firestore is used to store the state of jobs. Follow the
[server quickstart](https://cloud.google.com/firestore/docs/quickstart-servers) documentation to create a
Cloud Firestore database.

### Deploy Cloud Functions

    gcloud functions deploy Jobs --runtime go111 --trigger-http

## Create jobs and check their state

After the function is deployed, we can use `POST` and `GET` methods to interact with long-running jobs.

### Copy the URL

Put the URL of the deployed Cloud Function into an environment variable:

    export URL=$(gcloud functions describe Jobs --format='value(httpsTrigger.url)')

### Create a job

Call the function-based API to create a job with a simple task. Our task has one field, `worktime`, which
determines how many seconds the task takes to complete:

    JOBID=$(curl -s --header "Content-Type: application/json" --request POST --data '{"worktime":40}' $URL | jq -r '.id')

When the job is created, the function returns the ID of the job, which is put into an environment variable for
reference later.

### Check on job status

This command polls the state of the job every 2 seconds with the `watch` command.

	watch -t "curl -s $URL/$JOBID | jq"

### Perform the work

Start a worker in another tab in either your local terminal or in Cloud Shell, and then run a basic worker that will 
complete after waiting the `worktime` value in the original.

    cd worker
    go run main.go

You'll see output that looks like this:

    2019/02/22 08:19:20 Starting on task 4d43b618-9696-4398-aad4-f0e4f7bfc0d7

If you switch back to the shell that is watching the state of the job, in about 40 seconds you will see it transition
from this:

    {
      "Done": false,
      "Result": "",
      "State": 1,
      "created-time": "2019-02-22T16:21:43.055Z",
      "done-time": "0001-01-01T00:00:00Z",
      "id": "ec82ea86-66d6-46c0-8e9f-ed0b073356ab"
    }

to this:

    {
      "Done": true,
      "Result": "OK completed",
      "State": 2,
      "created-time": "2019-02-22T16:21:43.055Z",
      "done-time": "2019-02-22T16:22:23.794021Z",
      "id": "ec82ea86-66d6-46c0-8e9f-ed0b073356ab"
    }


At that point you can press CTRL-C to exit the `watch` command. Switch to the shell with the worker process
and press CTRL-C to exit the worker.

## Cleanup and next steps

Optionally, delete the deployed function and Cloud Pub/Sub resources:

	gcloud functions delete Jobs
	gcloud pubsub subscriptions delete worker-tasks
	gcloud pubsub topics delete jobs

In production, you would want to add authorization to the API function, for example
with [Firebase Auth tokens](https://github.com/firebase/functions-samples/tree/master/authorized-https-endpoint).

[curl]: https://linux.die.net/man/1/curl
[jq]: https://stedolan.github.io/jq/
[watch]: https://linux.die.net/man/1/watch
