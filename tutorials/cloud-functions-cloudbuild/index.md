---
title: Cloud function with cloudbuild and continuous delivery
description: Use cloudbuild to deploy to cloud functions.
author: montao
tags: Cloud Functions, Cloud Build, GoLang, CI/CD
date_published: 2020-07-25
---

Niklas Rosencrantz | DevOps/SRE

## Introduction

This tutorial demonstrates how to create a cloud function from cloudbuild

## Objectives

* Use [GCP Cloud Build](https://cloud.google.com/cloud-build) to deploy a cloud function.
* Use GoLang to process incoming HTTP request

## Set up your environment

1.  Create a project in the [GCP Console][console].
    
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Create a GitHub repository for your project
1.  Enable APIs:

        gcloud services enable \
        cloudfunctions.googleapis.com \

    
1.  Add [Cloud Build GitHub App](https://github.com/marketplace/google-cloud-build) to your GitHub account and repository. 
1.  Create the directory and file structure in the GitHub repository.
1.  Connect the repository with Cloud Build from the GCP project console.

### Cloud Build 

Now the cloud build will run, build, test and deploy your cloud function every time you push to the repository.

[console]: https://console.cloud.google.com/
