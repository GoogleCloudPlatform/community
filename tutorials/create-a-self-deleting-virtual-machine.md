---
title: Create a Self-Deleting Virtual Machine
description: Learn how to launch a Compute Engine VM that will delete itself after a set duration, insuring that costly resources are not left running.
author: engelke
tags: Compute Engine, self-deleting, education, cost control
date_published: 2019-03-15
---
# Create a Self-Deleting Virtual Machine on Google Compute Engine

Learning to use Google Cloud is best done hands-on, by actually creating, using,
and removing resources. But a common problem with doing this is learners may
forget to clean up their resources when finished trying something, resulting
in continuing running resources, often at a cost.

This tutorial shows how to create Compute Engine instances (virtual machines)
that will automatically delete themselves after a set time, insuring that
those resources will not remain, and incur charges, indefinitely even
if the learner forgets to clean them up. This will be particularly useful
in class settings.

## Objectives

Learn how to create Cloud Engine instances that will delete themselves after
a set period of time. You will see two ways to do this.

* Using the cloud console
* Using the `gcloud` CLI tool

## Before you begin

Create a Google Cloud Platform project in a web browser and note the
_Project ID_. You will use that in the steps below.

## Costs

This tutorial has you create a Compute Engine instance. That instance
will incur charges as long as it exists. Your account can use one free
micro instance (the kind created in this tutorial) as part of the
[Free Tier](https://cloud.google.com/free).

## Preparation

The way the self-deleting instance works is by automatically executing a
startup script that waits a set amount of time and then issues a `gcloud`
command to delete itself. This script needs to be provided in a file or
at an available URL when launching the instance.

Begin this tutorial by opening a text editor and creating a file named
`startup.sh` with the following contents:

    #!/bin/sh
    sleep 3600s
    export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
    gcloud --quiet compute instances delete $NAME --zone=$ZONE

When you start a new instance and specify that it should automatically run
this script, it will do nothing for one hour (the `3600s` value on the second
line), then look up information about the running instance and put it in shell
variables (the third and fourth lines), and finally run a `gcloud` command to
delete itself.


## Using the console

## Using the command line

## Cleaning up
