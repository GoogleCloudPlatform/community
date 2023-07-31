---
title: Deploy a Cloud Function with Cloud Build
description: Use Cloud Build to continuously deploy a Cloud Function.
author: montao
tags: Cloud Functions, GitHub, GoLang, continuous integration, continuous delivery, continuous deployment
date_published: 2020-07-29
---

Niklas Rosencrantz | DevOps/SRE

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial demonstrates how to create and deploy a Cloud Function with [Cloud Build](https://cloud.google.com/cloud-build).

## Objectives

* Use Cloud Build to deploy a Cloud Function.
* Use code written in the Go programming language to process incoming HTTP requests.

## Set up your environment

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Create a GitHub repository for your project.
1.  Enable the Cloud Functions API:

        gcloud services enable cloudfunctions.googleapis.com

1.  Add the [Cloud Build GitHub app](https://github.com/marketplace/google-cloud-build) to your GitHub account and repository. 
1.  Create the directory and file structure in the GitHub repository.

    You can use the file tree from the
    [source for this tutorial](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/cloud-functions-cloudbuild/) as a starting point. 
    
    Put a file named `cloudbuild.yaml` in the root directory and the code for the Cloud Function in a separate directory, as in the following file tree:

        │   .gitignore
        │   cloudbuild.yaml
        └───code
                function.go

## Connect the repository with Cloud Build

1.  In the Cloud Console, go to the [Cloud Build](https://console.cloud.google.com/cloud-build) page.
1.  Choose **Triggers**.
1.  Click **Connect repository**.
1.  Create a push trigger so that Cloud Build will run when you push to the master branch. 

After you have connected the repository with Cloud Build, Cloud Build will run, build, test, and deploy your Cloud Function each time you push to the repository.

You can view a list of your builds on the [Cloud Builds page of the Cloud Console](https://console.cloud.google.com/cloud-build/builds).
