---
title: Collecting additional GKE Node metrics using collectd to Cloud Monitoring
description: Learn how to deploy the Cloud Monitoring agent on GKE nodes to expose additional VM metrics on GKE nodes.
author: aaronsutton,echiugoog
tags: Google Container Engine, GKE, Cloud Monitoring, collectd, host metrics, VM metrics
date_published: 2020-06-19
---
Today only a few metrics are avaialble by default on GKE Nodes.

You can deploy a Cloud Monitoring agent to expose additional metrics for added visbiility into the health of your GKE nodes

## Objectives
Expose additional host metrics using the Cloud Monitoring agent on GKE Nodes. e.g. [Cloud Monitoring Agent Metrics](https://cloud.google.com/monitoring/api/metrics_agent)

Host metrics available today:
 * CPU Usage
 * Disk I/O
 * Network traffic

Additional metrics added with Cloud Monitoring agent:
 * CPU Load
 * CPU Steal
 * Memory Usage
 * Swap Usage
 * Disk Usage
 * Open TCP Connections
 * Processes

Even more metrics can be added by customizing `collectd.conf` to meet your needs.

## Before you begin
 * You have an existing project and GKE cluster created - [quickstart tutorial](https://cloud.google.com/kubernetes-engine/docs/quickstart)
 * Install the [Google Cloud SDK](https://cloud.google.com/sdk/)

## Getting started
 * Clone this repository -

## Build the container iamge
 * Update `cloudbuild.yaml`
   * Where:
     * `[PROJECT_ID]` is your Google Cloud project ID
     * `[IMAGE_NAME]` is the desired name of the container image
 * submit cloud build, this will publish to Container Registry (GCR) on
   completion: `gcloud builds submit --config cloudbuild-ec.yaml .`

## Deploy the daemonset
 * Update `agent.yaml` 
   * Where:
     * `[PROJECT_ID]` is your Google Cloud project ID
     * `[IMAGE_NAME]` is the name of the container image used above when building
       the container image
 * Deploy `kubectl apply -f agent.yaml`


## (optional) Customize the Cloud Monitoring agent
 * Edit `collectd.conf` to add in additional desired metrics
 * Rebuild container image and redeploy daemonset
   * NB: Add in any new dependencies that may be required for metric collection


