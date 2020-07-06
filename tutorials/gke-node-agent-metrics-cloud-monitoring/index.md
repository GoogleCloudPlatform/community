---
title: Collecting additional GKE Node metrics using collectd to Cloud Monitoring
description: Learn how to deploy the Cloud Monitoring agent on GKE nodes to expose additional VM metrics on GKE nodes.
author: aaronsutton,echiugoog
tags: Google Container Engine, host metrics
date_published: 2020-07-06
---

Today only a few metrics are available by default on GKE Nodes. You can deploy a Cloud Monitoring agent to expose additional metrics for added visibility into 
the health of your GKE nodes.

## Objectives

Expose additional host metrics using the Cloud Monitoring agent on GKE Nodes.

Host metrics available today:
 * CPU usage
 * Disk I/O
 * Network traffic

Additional metrics added with Cloud Monitoring agent:
 * CPU load
 * CPU steal
 * Memory usage
 * Swap usage
 * Disk usage
 * Open TCP connections
 * Processes

For details about the metrics exposed by the Cloud Monitoring agent, see [Agent metrics](https://cloud.google.com/monitoring/api/metrics_agent).

Even more metrics can be added by customizing `collectd.conf` to meet your needs.

## Before you begin

 * You have an existing project and GKE cluster created - [quickstart tutorial](https://cloud.google.com/kubernetes-engine/docs/quickstart)
 
 * Install the [Google Cloud SDK](https://cloud.google.com/sdk/)

## Getting started

 * Clone this repository -

## Build the container iamge

1.  Update `cloudbuild.yaml` by replacing the following values:

    * `[PROJECT_ID]` is your Google Cloud project ID.
    * `[IMAGE_NAME]` is the name of the container image.
   
1.  Build the container image with Cloud Build:

        gcloud builds submit --config cloudbuild-ec.yaml .

    When the build finishes, the image will be published to Container Registry.

## Deploy the daemonset

1.  Update `agent.yaml` by replacing the following values:

    * `[PROJECT_ID]` is your Google Cloud project ID
    * `[IMAGE_NAME]` is the name of the container image that you used when building the container image.
    
1.  Deploy:

        kubectl apply -f agent.yaml

## (optional) Customize the Cloud Monitoring agent

 * Edit `collectd.conf` to add in additional desired metrics.
 * Rebuild the container image and redeploy the daemonset. Add in any new dependencies that may be required for metric collection.
