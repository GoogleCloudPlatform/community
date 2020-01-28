---
title: Google Kubernetes Engine quickstart - Create a guestbook with Redis and PHP
description: Use Google Kubernetes Engine to deploy a guestbook application with Redis and PHP.
author: jscud
tags: Kubernetes
date_published: 2019-07-31
---

# Google Kubernetes Engine quickstart: Create a guestbook with Redis and PHP

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=gke_guestbook)

</walkthrough-alt>

This tutorial demonstrates how to build a multi-tier web app
using [Google Kubernetes Engine (GKE)][gke-docs]. The tutorial app is a guestbook that allows
visitors to enter text in a log and to see the last few logged entries.

The tutorial shows how to set up the guestbook web service on an external IP address with a load
balancer and how to run a [Redis][redis] cluster with a single master and multiple workers.

## Project setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Navigate to the Kubernetes Engine page

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
then select **Kubernetes Engine**.

<walkthrough-menu-navigation sectionId="KUBERNETES_SECTION"></walkthrough-menu-navigation>

## Create a Kubernetes cluster

A cluster consists of at least one cluster master machine and multiple worker
machines called *nodes*. You deploy applications to clusters, and the applications
run on the nodes.

1.  Click the [**Create cluster**][spotlight-create-cluster] button.

1.  On the **Create a Kubernetes cluster** page, select the
    <walkthrough-spotlight-pointer cssSelector="button[aria-label='Standard cluster']">Standard cluster</walkthrough-spotlight-pointer> template.

1.   Enter a [name][spotlight-instance-name] for this cluster.

1.   Choose a [zone][spotlight-instance-zone] for this cluster.

1.  Click [**Create**][spotlight-submit-create] to create the cluster.

## Get the sample application code

Cloud Shell is a built-in command-line tool for the console. In this section,
you start Cloud Shell and use it to get the sample application code. Later,
you use Cloud Shell to run the example app using a prebuilt container image.

### Open Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Get the sample code

Clone the sample code:

```bash
git clone https://github.com/kubernetes/examples
```

Navigate to the directory containing the sample code:

```bash
cd examples/guestbook
```

## Set up a Redis master

In this section, you deploy a Redis master and verify that it is running.

### Set up gcloud and kubectl credentials

```bash
gcloud container clusters get-credentials [cluster-name] --zone [cluster-zone]
```

Replace `[cluster-name]` and `[cluster-zone]` with the name and zone of the instance that you created.

### Exploring the controller

View the configuration file for the controller:

```bash
cat redis-master-deployment.yaml
```

This file contains configuration to deploy a Redis master. The `spec` field defines the pod
specification that the replication controller uses to create the Redis pod. The `image` tag
refers to a Docker image to be pulled from a registry.

### Deploy the master controller

Deploy the Redis master:

```bash
kubectl create -f redis-master-deployment.yaml
```

### View the running pod

Verify that the Redis master pod is running:

```bash
kubectl get pods
```

## Create the redis-master service

In this section, you create a service to proxy the traffic to the Redis master pod.

View your service configuration:

```bash
cat redis-master-service.yaml
```

This manifest file defines a service named `redis-master` with a set of label
selectors. These labels match the set of labels that are deployed in the
previous step.

Create the service:

```bash
kubectl create -f redis-master-service.yaml
```

Verify that the service has been created:

```bash
kubectl get service
```

## Set up Redis workers

Although the Redis master is a single pod, you can make it more highly available to meet traffic
demands by adding a few Redis worker replicas.

View the manifest file, which defines two replicas for the Redis workers:

```bash
cat redis-slave-deployment.yaml
```

Start the two replicas on your container cluster:

```bash
kubectl create -f redis-slave-deployment.yaml
```

Verify that the two Redis worker replicas are running by querying the list of pods:

```bash
kubectl get pods
```

## Create the Redis worker service

The guestbook application needs to communicate to Redis workers to read data. To make the
Redis workers discoverable, you need to set up a service. A service provides transparent
load balancing to a set of pods.

View the configuration file that defines the worker service:

```bash
cat redis-slave-service.yaml
```

This file defines a service named `redis-slave` running on port 6379. Note that
the `selector` field of the service matches the Redis worker pods created in the previous
step.

Create the service:

```bash
kubectl create -f redis-slave-service.yaml
```

Verify that the service has been created:

```bash
kubectl get service
```

## Set up the guestbook web frontend

Now that you have the Redis storage of your guestbook up and running, start the guestbook web
servers. Like the Redis workers, this is a replicated application managed by a deployment.

This tutorial uses a simple PHP frontend. It is configured to talk to either the Redis worker
or master services, depending on whether the request is a read or a write. It exposes a simple
JSON interface and serves a user experience based on jQuery and Ajax.

### Create the frontend deployment

```bash
kubectl create -f frontend-deployment.yaml
```

### Expose the frontend on an external IP address

The services that you created in the previous steps are only accessible within the container cluster,
because the default type for a service does not expose it to the internet.

To make the guestbook web frontend service externally visible, you need to specify the type
`LoadBalancer` in the service configuration.

Use the following command to replace `NodePort` with `LoadBalancer` in the `type` specification
in the `frontend-service.yaml` configuration file:

```bash
sed -i -e 's/NodePort/LoadBalancer/g' frontend-service.yaml
```

### Create the service

Create the service:

```bash
kubectl create -f frontend-service.yaml
```

## Visit the guestbook website

Your website is now running!

### Find your external IP address

List the services:

```bash
kubectl get services --watch
```

Wait until you see an IP address in the `External IP` column for the `frontend` service.
This may take a minute. To stop monitoring the services, press Ctrl+C.

### Visit the application

Copy the IP address from the `External IP` column, and load the page in your browser.

## Cleanup

With a GKE cluster running, you can create and delete resources with the `kubectl`
command-line client.

To remove your cluster, select the [checkbox][spotlight-instance-checkbox] next
to the cluster name and click the [**Delete**][spotlight-delete-button] button.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You have deployed a multi-tier guestbook application using
Google Kubernetes Engine.

Here are some suggestions for what you can do next:

*   Find Google Cloud Platform
    [samples on GitHub](http://googlecloudplatform.github.io/).

*   Learn how to store persistent data in your application through the
    [MySQL and WordPress][mysql-wordpress-tutorial] tutorial.

*   Explore other [Google Kubernetes Engine tutorials][kubernetes-tutorials].

[gke-docs]: https://cloud.google.com/kubernetes-engine/
[gke-registry]: https://cloud.google.com/container-registry
[redis]: http://redis.io/
[mysql-wordpress-tutorial]: https://cloud.google.com/kubernetes-engine/docs/tutorials/persistent-disk
[kubernetes-tutorials]: https://cloud.google.com/kubernetes-engine/docs/tutorials/
[spotlight-create-cluster]: walkthrough://spotlight-pointer?cssSelector=.p6n-zero-state-link-test.jfk-button-primary,gce-create-button
[spotlight-submit-create]: walkthrough://spotlight-pointer?spotlightId=gke-cluster-create-button
[spotlight-instance-name]: walkthrough://spotlight-pointer?spotlightId=gke-cluster-add-name
[spotlight-instance-zone]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-zone-select
[spotlight-notification-menu]: walkthrough://spotlight-pointer?cssSelector=.p6n-notification-dropdown,.cfc-icon-notifications
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-instance-checkbox]: walkthrough://spotlight-pointer?cssSelector=.p6n-checkbox-form-label
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
[spotlight-cluster-row]: walkthrough://spotlight-pointer?cssSelector=.p6n-kubernetes-cluster-row
