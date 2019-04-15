# Create a Guestbook with Redis and PHP

<walkthrough-tutorial-url url="https://cloud.google.com/kubernetes-engine/docs/tutorials/guestbook"></walkthrough-tutorial-url>
<!-- {% setvar repo_url "https://github.com/kubernetes/examples" %} -->
<!-- {% setvar repo_dir "examples/guestbook" %} -->

## Introduction

This tutorial demonstrates how to build a simple multi-tier web application
using Kubernetes Engine. The tutorial application is a guestbook that allows
visitors to enter text in a log and to see the last few logged entries.

The tutorial shows how to set up the guestbook web service on an external IP
with a load balancer and how to run a [Redis][redis] cluster with a single
master and multiple workers.

[Google Kubernetes Engine][gke-docs] is a powerful cluster manager and
orchestration system built on the power of open source Kubernetes.

To deploy and run the guestbook application on Kubernetes Engine, you must:

1. Set up a Redis master
1. Set up Redis workers
1. Set up the guestbook web frontend
1. Visit the guestbook website
1. Scale up the guestbook web frontend

## Project setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Create a Kubernetes Engine cluster

Open the [menu][spotlight-console-menu] on the left side of the console.

Then, select the **Kubernetes Engine** section.

<walkthrough-menu-navigation sectionId="KUBERNETES_SECTION"></walkthrough-menu-navigation>

## Create a Kubernetes cluster

A cluster consists of at least one cluster master machine and multiple worker
machines called nodes. You deploy applications to clusters, and the applications
run on the nodes.

Click the [Create cluster][spotlight-create-cluster] button.

*   Select the
    <walkthrough-spotlight-pointer cssSelector="button[aria-label='Standard cluster']">
    Standard cluster</walkthrough-spotlight-pointer> template.

*   Select a [name][spotlight-instance-name] and [zone][spotlight-instance-zone]
    for this cluster.

*   Click the [Create][spotlight-submit-create] button to create the cluster.

## Create the sample application

Cloud Shell is a built-in command line tool for the console. You're going to use
Cloud Shell to run the example app using the prebuilt container image at
[Google Kubernetes Registry][gke-registry].

### Open the Cloud Shell

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Clone the sample code

Use Cloud Shell to clone and navigate to the sample code to the Cloud Shell.

Note: If the directory already exists, remove the previous files before cloning.

```bash
git clone {{repo_url}}
```

```bash
cd {{repo_dir}}
```

## Set up a Redis master

You are now in the main directory for the sample code. First, look at the files
that configure your application.

### Setup gcloud and kubectl credentials

```bash
gcloud container clusters get-credentials <cluster-name> --zone <cluster-zone>
```

### Exploring the controller

Enter the following command to view your controller configuration:

```bash
cat redis-master-deployment.yaml
```

This file contains configuration to deploy a Redis master. The `spec` field
defines the Pod specification which the Replication Controller will
use to create the Redis pod. The `image` tag refers to a Docker
image to be pulled from a registry.

### Deploy the master controller

Run the following command to deploy the Redis master.

```bash
kubectl create -f redis-master-deployment.yaml
```

### View the running pod

Verify that the Redis master Pod is running.

```bash
kubectl get pods
```

## Create redis-master service

You need to create a Service to proxy the traffic to the Redis master Pod. Use
the following command
to create the service.

Enter the following command to view your service configuration:

```bash
cat redis-master-service.yaml
```

This manifest file creates a Service named `redis-master` with a set of label
selectors. These labels match the set of labels that are deployed in the
previous step.

```bash
kubectl create -f redis-master-service.yaml
```

Verify that the service is created.

```bash
kubectl get service
```

## Set up Redis workers

Although the Redis master is a single pod, you can make it highly available and meet traffic demands by adding a few Redis worker replicas.

```bash
cat redis-slave-deployment.yaml
```

This manifest file defines two replicas for the Redis workers.

Use the following command to start the two replicas on your container cluster.

```bash
kubectl create -f redis-slave-deployment.yaml
```

Verify that the two Redis worker replicas are running by querying the list of Pods.

```bash
kubectl get pods
```

## Create redis-slave service

The guestbook application needs to communicate to Redis workers to read data. To make the Redis workers discoverable, you need to set up a Service. A Service provides transparent load balancing to a set of Pods.

```bash
cat redis-slave-service.yaml
```

This file defines a Service named `redis-slave` running on port 6379. Note that the `selector` field of the Service matches the Redis worker Pods created in the previous step.

```bash
kubectl create -f redis-slave-service.yaml
```

Verify that the Service is created:

```bash
kubectl get service
```

## Set up the guestbook web frontend

Now that you have the Redis storage of your guestbook up and running, start the guestbook web servers. Like the Redis workers, this is a replicated application managed by a Deployment.

This tutorial uses a simple PHP frontend. It is configured to talk to either the Redis worker or master Services, depending on whether the request is a read or a write. It exposes a simple JSON interface, and serves a jQuery-Ajax-based UX.

```bash
kubectl create -f frontend-deployment.yaml
```

### Expose frontend on an external IP address

The Services you created in the previous steps are only accessible within the container cluster, because the default type for a Service is `ClusterIP`.
To make the guestbook web frontend Service to be externally visible, you need to specify type: `LoadBalancer` in the Service configuration.

To create the Service, first, uncomment the following line in the `frontend-service.yaml` file:

```bash
sed -i -e 's/NodePort/LoadBalancer/g' frontend-service.yaml
```

### Create the service

Use the following command the create the service.

```bash
kubectl create -f frontend-service.yaml
```

## Visit the guestbook website

Your website is now running!

### Find your external IP

List the services, and look for the frontend service. Wait until
you see an IP show up under the External IP column. This may take a minute. Afterwards you can stop monitoring by pressing Ctrl+C.

```bash
kubectl get services --watch
```

### Visit the application

Copy the IP address in EXTERNAL-IP column, and load the page in your browser.

## Cleanup

With a Kubernetes Engine cluster running, you can create and delete resources
with the `kubectl` command-line client.

To remove your cluster, select the [checkbox][spotlight-instance-checkbox] next
to your cluster name and click the [Delete button][spotlight-delete-button].

## Conclusion

Congratulations! You have deployed a multi-tier Guestbook application using
Google Kubernetes Engine.

Here's what to do next:

Learn how to store persistent data in your application through the [MySQL and WordPress][mysql-wordpress-tutorial] tutorial.

Explore other [Kubernetes Engine tutorials][kubernetes-tutorials].

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
