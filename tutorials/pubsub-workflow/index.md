---
title: Building a distributed workflow with Pub/Sub and Cloud Storage
description: Learn how to use Pub/Sub, Memorystore, and Cloud Storage to implement a workflow that completes each unit of work one time.
author: dwatrous
tags: pubsub, gcp, gcs, workflow, memorystore
date_published: 2020-11-03
---

Daniel Watrous | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Queues provide an effective and robust mechanism for distributing work. This tutorial introduces Redis to prevent duplicate work and make the process as 
efficient as possible. 

This tutorial is for anyone building a distributed workflow using Pub/Sub. It covers the creation of topics, subscriptions, and a containerized Python 
application. The system described in this tutorial uses Cloud Storage to synthesize work and generate notifications.

This entire tutorial can be completed in the Cloud Shell in the Cloud Console, or locally using Docker.

The following diagram illustrates the components and interactions that are part of this tutorial:

![overview](https://storage.googleapis.com/gcp-community/tutorials/pubsub-workflow/pubsub-workflow.svg)

Some important design considerations when building a workflow include the following:

 * Design work outputs to be idempotent. That is, if a unit of work is unintentionally processed twice, the result is the same.
 * A queue is useful any time multiple workers need to respond to new *work available* events.
 * If a unit of work is delivered to multiple workers, there must be a way to decide which worker drops the unit of work and which one claims it.

## Objectives

 * Create new topics in Pub/Sub.
 * Create new subscriptions in Pub/Sub.
 * Generate units of work along with corresponding messages.
 * Start a new Python container and run an app to subscribe to and publish messages.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Pub/Sub](https://cloud.google.com/pubsub)
*   [Cloud Storage](https://cloud.google.com/storage/)
*   [Memorystore](https://cloud.google.com/memorystore/) (not used in the local development scenario)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

1.  Enable the APIs for the services:

        gcloud services enable redis.googleapis.com
        gcloud services enable pubsub.googleapis.com
        gcloud services enable storage-api.googleapis.com

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community
        
1.  Go to the directory for this tutorial:

        cd community/tutorials/pubsub-workflow/

1.  Set environment variables, replacing the values below with those that match your environment:

        export PROJECT_ID=project-name
        gcloud config set project $PROJECT_ID
        export WORKBUCKET=workbucket01_$PROJECT_ID
        export PROCESSEDBUCKET=processedbucket01_$PROJECT_ID
        export SERVICE_ACCOUNT=pubsub-access
        export KEYFILE=$SERVICE_ACCOUNT-key.json
        export GOOGLE_APPLICATION_CREDENTIALS=$KEYFILE
        export DEMOSOURCE=/path/to/community/tutorials/pubsub-workflow/

## Where to run this tutorial

This tutorial can be executed in any environment that provides `gcloud` and Docker. Some options include the following:

*   [Cloud Shell](https://cloud.google.com/shell) includes Docker and has `gcloud` built in and ready to go.
*   If you prefer to develop on your own host, install [Docker](https://www.docker.com/) and run the commands locally.
*   You can also create a small instance to follow this tutorial with the following command:

        gcloud compute instances create pubsub-tutorial \
           --project=$PROJECT_ID \
           --zone=us-central1-a \
           --machine-type=e2-micro \
           --image=cos-stable-85-13310-1041-9 \
           --image-project=cos-cloud \
           --boot-disk-size=15GB

Docker images used:

* Python 3: https://hub.docker.com/_/python
* `gcloud`: https://hub.docker.com/r/google/cloud-sdk (You can also install `gcloud` locally.)

## Set up Pub/Sub

1.  Create three Pub/Sub topics:

        gcloud pubsub topics create available processing complete --labels source=tgsdemo
        gcloud pubsub topics list

1.  Create worker and auditor subscriptions

        gcloud pubsub subscriptions create worker --topic=available
        gcloud pubsub subscriptions create auditor --topic=processing
        gcloud pubsub subscriptions list

## Establish a Redis instance

Depending on whether you are running the tutorial locally or in the cloud, use one of the following options.

### Local

    docker run --rm -p 6379:6379 --name some-redis -d redis

### Cloud

    gcloud redis instances create workavailability --size=1 --region=us-central1 --redis-version=redis_5_0

## Create a service account and add roles

The scripts that interact with Pub/Sub and Cloud Storage require a service account with specific permissions, which are granted by roles. 

1.  Create the service account:

        gcloud iam service-accounts create $SERVICE_ACCOUNT --display-name "PubSub Access Account" --description "access for pubsub workflow"
        
1.  Generate a credential file for this tutorial:

        gcloud iam service-accounts keys create $KEYFILE --iam-account=$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com

    Note the location where the `$SERVICE_ACCOUNT-key.json` key file is downloaded.

1.  Assign the roles that are required by the script for this tutorial:

        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/pubsub.publisher
            
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/pubsub.subscriber
            
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/storage.objectAdmin
            
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/serviceusage.serviceUsageConsumer


## Set up work files, buckets, and notifications

1.  Create a folder and fill it with 99 work files:

        mkdir workfiles
        for n in {1..9}; do touch workfiles/work00$n ; done
        for n in {10..99}; do touch workfiles/work0$n ; done

1.  Fill the work files with content:

        for f in workfiles/*; do base64 /dev/urandom | head -c 1024000 | grep -i svn | sed  's/svn/---SVN---/gI' | head -c 2048 > $f; done

    Each file contains up to 2048 bytes and includes tokens that you replace as part of your workflow.

1.  Create a bucket for work files and a bucket for processed files:

        gsutil mb -p $PROJECT_ID -l US-CENTRAL1 gs://$WORKBUCKET
        gsutil mb -p $PROJECT_ID -l US-CENTRAL1 gs://$PROCESSEDBUCKET

1.  Create a notification for objects placed in the work bucket:

        gsutil notification create -f json -t available gs://$WORKBUCKET
        gsutil notification list gs://$WORKBUCKET

    This command creates a notification on the work files bucket. When an object is added to the bucket, a new message is published to the `available` topic.

1.  Copy files to the bucket

        gsutil -m cp workfiles/* gs://$WORKBUCKET

At this point, there should be 99 files in `$WORKBUCKET`, no files in `$PROCESSEDBUCKET`, and 99 messages in the `available` topic that are ready to be pulled by
the `worker` subscription. Those messages continue to age until they are pulled and acknowledged.

## Update configuration file

Update the `config` file so that it looks like this:

    {
        "redis_host": "172.17.0.1",
        "redis_port": "6379",
        "processed_bucket": "PROCESSEDBUCKET",
        "processing_topic": "processing",
        "complete_topic": "complete"
    }

The `redis_` values depend on whether you used the local or cloud option when you established your Redis instance. When you run Redis as a container, you
need to be aware of the container networking to get the correct IP address to access Redis from the Python container created in the next step of the tutorial. 

Run `docker inspect 553c2826f9c6` with the ID for the Redis container to get details about the network bridge.

The `processed_bucket` was set in an environment variable at the beginning of this tutorial. Update that value in the `config` file.

## Start a Python container and install required libraries (local development)

1.  Start a Python container:

        docker run --rm -it --entrypoint /bin/bash -v $DEMOSOURCE:/pubsub -e PROJECT_ID -e GOOGLE_APPLICATION_CREDENTIALS=/pubsub/$KEYFILE -w /pubsub python:3

1.  Install required libraries and run the `worker.py` script:

        pip install -r /pubsub/requirements.txt

## Run the Python script

Run the `worker.py` script:

    python worker.py $PROJECT_ID worker
    exit
        
When the script is done, press `CTRL+C` to exit the script. The `temp` directory is cleaned up on exit.

## Cleaning up

1.  Clean up generated files:

        rm -fR workfiles

1.  Clean up Pub/Sub topics and subscriptions:

        gcloud pubsub subscriptions delete worker auditor
        gcloud pubsub topics delete available processing complete

1.  Remove roles:

        gcloud projects remove-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/pubsub.publisher
            
        gcloud projects remove-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/pubsub.subscriber
            
        gcloud projects remove-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/storage.objectAdmin
            
        gcloud projects remove-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
            --role=roles/serviceusage.serviceUsageConsumer

1.  Delete the service account:

        gcloud iam service-accounts delete $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com

1   Clean up Cloud Storage buckets:

        gsutil -m rm gs://$WORKBUCKET/*
        gsutil rb gs://$WORKBUCKET
        gsutil -m rm gs://$PROCESSEDBUCKET/*
        gsutil rb gs://$PROCESSEDBUCKET

1.  If you created a Memorystore instance, clean that up, too:

        gcloud redis instances delete workavailability --region=us-central1

## Alternatives

A simple alternative to this workflow management approach is to have a Cloud Function execute when an object in Cloud Storage experiences a specific event, as
described in [this tutorial](https://cloud.google.com/functions/docs/tutorials/storage). This may have some scale benefits, but it also introduces concurrency 
and assurance issues.

## What's next

* [Introduction to Pub/Sub](https://cloud.google.com/pubsub/docs/building-pubsub-messaging-system)
* [Python client for Pub/Sub](https://googleapis.dev/python/pubsub/latest/index.html)
* [Introduction to Redis](https://redis-py.readthedocs.io/en/stable/)
* [Redis Python client](https://redislabs.com/lp/python-redis/)
* [Automate Pub/Sub message when object is placed in Cloud Storage bucket](https://cloud.google.com/storage/docs/pubsub-notifications)
