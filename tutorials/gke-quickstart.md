---
title: Kubernetes Engine Quickstart
description: Deploy a prebuilt Docker container image using GKE.
author: jscud
tags: Kubernetes
date_published: 2019-04-12
---

# Google Kubernetes Engine Quickstart

<walkthrough-tutorial-url url="https://cloud.google.com/kubernetes-engine/docs/quickstart"></walkthrough-tutorial-url>
<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/kubernetes-engine-samples" %} -->
<!-- {% setvar repo_dir "kubernetes-engine-samples/hello-app" %} -->
<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=gke_quickstart)

</walkthrough-alt>

## Introduction

This quickstart shows you how to deploy a prebuilt Docker container image with a
simple Node.js example app.

Here are the steps you will be taking.

*   **Start a cluster**
    *   Using the Google Cloud Console, start a cluster of virtual machines with
        the click of a button.
*   **Deploy the app**
    *   You will be guided through the Kubernetes configuration and commands
        required to deploy the application using Google Cloud Shell, right in
        your browser.
*   **After the app...**
    *   Your app and cluster will be live and you'll be able to experiment with
        it after you deploy, or you can remove them and start fresh.

## Project setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Navigate to Kubernetes Engine

Open the [menu][spotlight-console-menu] on the left side of the console.

Then, select the **Kubernetes Engine** section.

<walkthrough-menu-navigation sectionId="KUBERNETES_SECTION"></walkthrough-menu-navigation>

## Create a Kubernetes cluster

A cluster consists of at least one cluster master machine and multiple worker
machines called nodes. You deploy applications to clusters, and the applications
run on the nodes.

Click the [Create cluster][spotlight-create-cluster] button.

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
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar
in the upper-right corner of the console.

### Clone the sample code

Use Cloud Shell to clone and navigate to the sample code to the Cloud Shell.

Note: If the directory already exists, remove the previous files before cloning.

```bash
git clone {{repo_url}}
```

```bash
cd {{repo_dir}}
```

## Configuring your deployment

You are now in the main directory for the sample code.

### Exploring the application

Enter the following command to view your application code:

```bash
cat main.go
```

`main.go` is a web server implementation written in the Go programming language.
The server responds to any HTTP request with a "Hello, world!" message.

### Exploring your configuration

`Dockerfile` describes the image you want Docker to build, including all of its
resources and dependencies, and specifies which network port the app should
expose.

```bash
cat Dockerfile
```

To learn more about how this file work, refer to Dockerfile reference in the
[Docker documentation][docker-docs].

## Deploy the application

### Wait for the cluster creation to finish

The cluster creation needs to finish before the tutorial can proceed. The
activity can be tracked by clicking the
[notification menu][spotlight-notification-menu] from the navigation bar at the
top.

### Setup gcloud and kubectl credentials

Get the gcloud credentials for the cluster that you created. Enter the zone and
name of the cluster you created.

```bash
gcloud container clusters get-credentials <cluster-name> --zone <cluster-zone>
```

### Build the container

Use the following command to build and push the application image.

```bash
docker build -t gcr.io/{{project_id}}/hello-app:v1 $PWD
```

```bash
gcloud docker -- push gcr.io/{{project_id}}/hello-app:v1
```

### Run the container

Now, run the application on your Kubernetes cluster.

```bash
kubectl run hello-app --image=gcr.io/{{project_id}}/hello-app:v1 --port=8080
```

## View the application

### Expose the cluster

Then, make the cluster available to the public.

```bash
kubectl expose deployment hello-app --type="LoadBalancer"
```

### Find your external IP

List the services, and look for the hello-app service. Wait until you see an IP
show up under the External IP column. This may take a minute. Afterwards you can
stop monitoring by pressing Ctrl+C.

```bash
kubectl get service hello-app --watch
```

### Visit your running app

Copy the IP in the External IP column.

Open a new tab and visit your app, by connecting to the IP address on port 8080:

http://EXTERNAL-IP:8080 (replace EXTERNAL-IP with the external IP address)

## Modifying your cluster

Kubernetes allows you to easily scale or upgrade your application.

### Scale your application

Use the following command to scale up your application to four replicas. Each
runs independently on the cluster with the load balanced serving traffic to all
of them.

```bash
kubectl scale deployment hello-app --replicas=4
```

### View your application settings

Look at the deployment settings of your cluster with the following commands:

```bash
kubectl get deployment
```

```bash
kubectl get pods
```

## Update your application

You can modify your local copy of `main.go` to return a different message using
an editor or the first command, then build the docker image.

### Modify your application

```bash
sed -i -e 's/1.0.0/2.0.0/g' main.go
```

```bash
docker build -t gcr.io/{{project_id}}/hello-app:v2 $PWD
```

### Publish your application

```bash
gcloud docker -- push gcr.io/{{project_id}}/hello-app:v2
```

```bash
kubectl set image deployment/hello-app hello-app=gcr.io/{{project_id}}/hello-app:v2 && echo 'image updated'
```

### View your modified application

View the new version of the application at the same address. It make take a
minute for the application image to update:

```bash
kubectl get service hello-app
```

http://EXTERNAL-IP:8080

## Inspect your cluster

You can inspect properties of your cluster through the cloud console.

### View cluster details

Click on the [name of the cluster][spotlight-cluster-row] that you created. This
will bring up the cluster details page.

### Delete the cluster

You can continue to use your app, or you can shut down the entire cluster to
avoid subsequent charges.

To remove your cluster, select the [checkbox][spotlight-instance-checkbox] next
to your cluster name and click the [Delete button][spotlight-delete-button].

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You have deployed a simple Hello World application using Google
Kubernetes Engine.

Here's what you can do next:

Find Google Cloud Platform [samples on GitHub][gcp-github]

Learn how to set up [HTTP Load Balancing][http-balancer]

[gke-registry]: https://cloud.google.com/container-registry
[gcp-github]: http://googlecloudplatform.github.io/
[http-balancer]: https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer
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
[docker-docs]: https://docs.docker.com/engine/reference/builder/
