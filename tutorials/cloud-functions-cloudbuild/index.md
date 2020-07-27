---
title: Deploy a Cloud Function with Cloud Build
description: Use Cloud Build to continuously deploy a Cloud Function.
author: montao
tags: Cloud Functions, GitHub, GoLang, continuous integration, continuous delivery, continuous deployment
date_published: 2020-07-31
---

Niklas Rosencrantz | DevOps/SRE

## Introduction

This tutorial demonstrates how to create a Cloud Function with [Cloud Build](https://cloud.google.com/cloud-build).

## Objectives

* Use Cloud Build to deploy a Cloud Function.
* Use GoLang to process incoming HTTP requests.

## Set up your environment

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Create a GitHub repository for your project.
1.  Enable the Cloud Functions API:

        gcloud services enable cloudfunctions.googleapis.com

1.  Add the [Cloud Build GitHub app](https://github.com/marketplace/google-cloud-build) to your GitHub account and repository. 
1.  Create the directory and file structure in the GitHub repository.
1.  Connect the repository with Cloud Build from the Cloud Console.

### Cloud Build 

Now Cloud Build will run, build, test, and deploy your Cloud Function every time you push to the repository.
