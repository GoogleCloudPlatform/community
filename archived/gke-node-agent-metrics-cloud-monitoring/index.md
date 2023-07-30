---
title: Collect additional GKE node metrics using collectd with Cloud Monitoring
description: Learn how to deploy the Cloud Monitoring agent on GKE nodes to expose additional VM metrics on GKE nodes.
author: aaronsutton,echiugoog
tags: host metrics
date_published: 2020-08-07
---

Aaron Sutton and Edwin Chiu | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Only a few metrics are available by default on GKE nodes. You can deploy a Cloud Monitoring agent to expose additional metrics for added visibility into the 
health of your GKE nodes.

## Objectives

Expose additional host metrics using the Cloud Monitoring agent on GKE nodes.

Host metrics available by default:

* CPU usage
* Disk I/O
* Network traffic

Metrics added with the Cloud Monitoring agent:

* CPU load
* CPU steal
* Memory usage
* Swap usage
* Disk usage
* Open TCP connections
* Processes

For details about the metrics exposed by the Cloud Monitoring agent, see [Agent metrics](https://cloud.google.com/monitoring/api/metrics_agent).

Even more metrics can be added by customizing
[`collectd.conf`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/gke-node-agent-metrics-cloud-monitoring/collectd.conf) to meet your
needs.

## Before you begin

1. Create a Google Cloud project and GKE cluster, as shown in [this quickstart tutorial](https://cloud.google.com/kubernetes-engine/docs/quickstart).
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).
1. Clone this repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

    The files for this tutorial are in the
    [`/tutorials/gke-node-agent-metrics-cloud-monitoring`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/gke-node-agent-metrics-cloud-monitoring) directory.

## Build the container image

1. Update `cloudbuild.yaml` by replacing the following values:

    * `[PROJECT_ID]` is your Google Cloud project ID.
    * `[IMAGE_NAME]` is the name of the container image.

1. Build the container image with Cloud Build:

        gcloud builds submit --config cloudbuild.yaml .

    When the build finishes, the image will be published to Container Registry.

## Deploy the daemonset

1. Update `agent.yaml` by replacing the following values:

    * `[PROJECT_ID]` is your Google Cloud project ID
    * `[IMAGE_NAME]` is the name of the container image that you used when building the container image.

1. Deploy:

        kubectl apply -f agent.yaml

1. Check that the daemonset deployed and is ready:

        kubectl get ds

    The output should be similar to the following, where [IMAGE_NAME] is the name of your container image:

        NAME           DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
        [IMAGE_NAME]   1         1         1       1            1           <none>          29s

## (optional) Customize the Cloud Monitoring agent

1.  Edit `collectd.conf` to expose additional metrics.
1.  Add any new dependencies required for metric collection.
1.  Rebuild the container image and redeploy the daemonset. 

## Viewing the metrics

After deploying the daemonset, the additional metrics should begin to flow to Cloud Monitoring automatically. To view the metrics, go to the
[**Monitoring**](https://console.cloud.google.com/monitoring) page in the Cloud Console.

One way of examining metrics is using the [Metrics Explorer](https://console.cloud.google.com/monitoring/metrics-explorer). Because the new metrics being
collected are GKE node metrics, they are visible for the Compute Engine VM instance resource type with the metric names beginning with `agent.googleapis.com`:

![Metrics explorer](https://storage.googleapis.com/gcp-community/tutorials/gke-node-agent-metrics-cloud-monitoring/sd-explorer.png)

If you take a detailed look at the node itself within Cloud Monitoring, you can see the additional metrics graphed within the VM instance dashboard agent tab. 
Go to the [**Dashboards**](https://console.cloud.google.com/monitoring/dashboards) page, and then click **VM Instances** and the instance you're interested in
viewing metrics for.

![Monitoring agent metrics](https://storage.googleapis.com/gcp-community/tutorials/gke-node-agent-metrics-cloud-monitoring/sd-agent-metrics.png)

## Cleanup

1. Delete the daemonset:

        kubectl delete ds [IMAGE_NAME]

1. Delete the cluster you created in the **Before you begin** section:

        gcloud container clusters delete [CLUSTER_NAME]
