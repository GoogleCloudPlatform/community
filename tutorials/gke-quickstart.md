---
title: Google Kubernetes Engine quickstart - Deploy a prebuilt Docker container image
description: Deploy a prebuilt Docker container image using GKE.
author: jscud
tags: Kubernetes
date_published: 2019-07-31
---

# Google Kubernetes Engine quickstart: Deploy a prebuilt Docker container image

<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=gke_quickstart)

</walkthrough-alt>

This quickstart shows you how to start a cluster of virtual machines and deploy a prebuilt
Docker container image with a simple Node.js example app.

## Project setup

Google Cloud organizes resources into projects. This allows you to
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
git clone https://github.com/GoogleCloudPlatform/kubernetes-engine-samples
```

Navigate to the directory containing the sample code:

```bash
cd kubernetes-engine-samples/hello-app
```

## Exploring the deployment

You are now in the main directory for the sample code.

### Exploring the application

View the application code:

```bash
cat main.go
```

`main.go` is a web server implementation written in the Go programming language.
The server responds to any HTTP request with a `"Hello, world!"` message.

### Exploring the image configuration

View the image configuration:

```bash
cat Dockerfile
```

`Dockerfile` describes the image that you want Docker to build, including all of
its resources and dependencies, and specifies which network port the app should
expose.

To learn more about how this file works, refer to the Dockerfile reference in the
[Docker documentation][docker-docs].

## Deploy the application

### Wait for the cluster creation to finish

The cluster creation needs to finish before the tutorial can proceed. To track the
progress of this activity and others, click the [**Notifications**][spotlight-notification-menu]
button in the navigation bar in the upper-right corner of the console.

### Set up gcloud and kubectl credentials

Get the `gcloud` credentials for the cluster that you created:

```bash
gcloud container clusters get-credentials [cluster-name] --zone [cluster-zone]
```

Replace `[cluster-name]` and `[cluster-zone]` with the name and zone of the instance that you created.

### Build and push the container

Build the image:

```bash
docker build -t gcr.io/{{project_id}}/hello-app:v1 $PWD
```

Push the image:

```bash
gcloud docker -- push gcr.io/{{project_id}}/hello-app:v1
```

### Run the application

Run the application on your Kubernetes cluster:

```bash
kubectl run hello-app --image=gcr.io/{{project_id}}/hello-app:v1 --port=8080
```

## View the application

### Expose the cluster

Make the cluster available to the public:

```bash
kubectl expose deployment hello-app --type="LoadBalancer"
```

### Find your external IP address

List the services, and look for the `hello-app` service:

```bash
kubectl get service hello-app --watch
```

Wait until you see an IP address in the `External IP` column. This may take a
minute. To stop monitoring the services, press `Ctrl+C`.

### Visit your running app

Copy the IP address from the `External IP` column.

Open a new web browser tab, and visit your app by connecting to the IP address on port 8080:

`http://[external-IP]:8080`

Replace `[external-IP]` with the external IP address copied in the previous step.

## Modifying your cluster

Kubernetes allows you to easily scale or upgrade your application.

### Scale your application

Use the following command to scale your application up to four replicas:

```bash
kubectl scale deployment hello-app --replicas=4
```

Each replica runs independently on the cluster, with the load balancer serving traffic to
all of them.

### View your application settings

Look at the deployment settings of your cluster with the following commands:

```bash
kubectl get deployment
```

```bash
kubectl get pods
```

## Update the application

In this section, you modify your local copy of `main.go`, rebuild the
application, and push the new version.

### Modify the application

Use this command to make a text substitution in your local copy of `main.go`
to make it return a different version number in its output:

```bash
sed -i -e 's/1.0.0/2.0.0/g' main.go
```

You can also modify the file with a text editor instead of using this `sed` command.

### Rebuild the application

```bash
docker build -t gcr.io/{{project_id}}/hello-app:v2 $PWD
```

### Publish the application

```bash
gcloud docker -- push gcr.io/{{project_id}}/hello-app:v2
```

```bash
kubectl set image deployment/hello-app hello-app=gcr.io/{{project_id}}/hello-app:v2 && echo 'image updated'
```

### View the modified application

Wait a minute to give the application image time to update, and
then view the modified application at the same address as before:

`http://[external-IP]:8080`

## Inspect your cluster

You can inspect properties of your cluster through the GCP Console.

### View cluster details

Click the [name of the cluster][spotlight-cluster-row] that you created. This
opens the cluster details page.

### Delete the cluster

You can continue to use your app, or you can shut down the entire cluster to
avoid subsequent charges.

To remove your cluster, select the [checkbox][spotlight-instance-checkbox] next
to the cluster name and click the [**Delete**][spotlight-delete-button] button.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You have deployed a simple "Hello, world" application using Google
Kubernetes Engine.

Here are some suggestions for what you can do next:

*   Find Google Cloud
    [samples on GitHub](http://googlecloudplatform.github.io/).

*   Learn how to set up [HTTP load balancing][http-balancer].

*   Explore other [Kubernetes Engine tutorials][kubernetes-tutorials].

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
[kubernetes-tutorials]: https://cloud.google.com/kubernetes-engine/docs/tutorials/
