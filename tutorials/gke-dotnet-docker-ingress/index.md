---
title: dotnet core application in GKE with docker and ingress
description: Learn how to deploy a dotnet core application to gke using docker, cloud build and expose using ingress
author: livesankp
tags: GKE, docker, dotnet, ingress
date_published: 2022-04-05
---

Sandeep Parmar

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows you how to deploy a dotnet core application to gke using the `gcloud` command-line tool.

After following this tutorial, you will be able to deploy a dotnet core application in GKE using cloud build and Docker.

This tutorial assumes that you know the basics of the following products and services:

  - [GKE](https://cloud.google.com/kubernetes-engine/docs)
  - [Cloud Build](https://cloud.google.com/build/docs)
  - [`gcloud`](https://cloud.google.com/sdk/docs)
  - [Docker](https://docs.docker.com/engine/reference/commandline/run)
  - [dotnetcore](https://docs.microsoft.com/en-us/aspnet/core/introduction-to-aspnet-core)

## Objectives

*   Create and set up dotnet core application using [Visual Studio](https://visualstudio.microsoft.com/).
*   Build and containerize your app using the [Cloud SDK](https://cloud.google.com/sdk).
*   Deploy your app to the web using the [`gcloud` command-line tool](https://cloud.google.com/sdk/gcloud).

## Before you begin

1.  Select or create a Google Cloud project.

    [Go to the **Manage resources** page.](https://console.cloud.google.com/cloud-resource-manager)

1.  Enable the GKE, Cloud Build, and Container Registry APIs. For details, see
    [Enabling APIs](https://cloud.google.com/apis/docs/getting-started#enabling_apis).

## dotnet core application creation and setup

In this section, you will create a sample dotnet core application using visual studio. .NET 6.0 and visual studio 2022 community version is used in this tutorial.

1. Follow [dotnet core](https://docs.microsoft.com/en-us/aspnet/core/?view=aspnetcore-6.0) documentation on how to create a new project. While creating a project make sure to add docker support for windows. This tutorial is using SampleApplication name.
1. Once project is created, verify if visual studio build is working and you are able to run the application. For this tutorial purpose sample application is provided.
1. You can see the sample code in this tutorial's [GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/gke-dotnet-docker-ingress/SampleApplication).
1. For this application to work in GKE few changes are added like health check and reading PORT enviroment variable. Check the `//GKE` comments in program.cs

## gcloud console setup

1.  Using gcloud console do the login `gcloud auth login`.
1.  Once login is succeeded set the project using `gcloud config set project yourprojectid`.

## cloud build and gke deployment
1.  `Dockerfile` and `cloudbuid.yaml` files are added at the root of the application.
1.  Run `gcloud builds submit` at root of the application where `Dockerfile` is located. If this runs successfully then verify container registry of the project with image name as per cloudbuild.yaml and your projectid.
	![container-registry](https://storage.googleapis.com/gcp-community/tutorials/gke-dotnet-docker-ingress/images/container-registry-image.png)
1.  Copy the image path and update `deployment.yaml` file under GKE folder.
1.  Navigate to GKE folder.
1.  If you don't have Kubernetes command-line tool installed then Run `gcloud components install kubectl`.
1.  Get the credentials of your gke cluster using `gcloud container clusters get-credentials "yourclustername" --zone "zoneofyourcluster" --project yourprojectid`
1.  Create the kubernetes namespace using `kubectl create namespace sample-application-ns`.
1.  Execute the backend config for healthcheck first using `kubectl apply -f backend-config.yaml`.
1.  Run the deployment using `kubectl apply -f deployment.yaml`. Verify this.
        ![gke-deployment](https://storage.googleapis.com/gcp-community/tutorials/gke-dotnet-docker-ingress/images/gke-deployment.png)
1.  Run the service using `kubectl apply -f service.yaml`. Verify this.
        ![gke-service](https://storage.googleapis.com/gcp-community/tutorials/gke-dotnet-docker-ingress/images/gke-service.png)
1.  Run the ingress using `kubectl apply -f ingress.yaml`. Verify this. Open ip address of FrontEnds in ingress. You should be able to see your application running.
        ![gke-ingress](https://storage.googleapis.com/gcp-community/tutorials/gke-dotnet-docker-ingress/images/gke-ingress.png)
	![running application](https://storage.googleapis.com/gcp-community/tutorials/gke-dotnet-docker-ingress/images/running-application.png)
