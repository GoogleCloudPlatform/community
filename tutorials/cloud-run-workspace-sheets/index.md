---
title: Access data in Sheets from Cloud Run
description: Access data securely from sheets from a Cloud Run Service
author: ptone
tags: Serverless, Workspace, Cloud Run, Golang, Go, Sheets
date_published: 2021-07-16
---

Preston Holmes | Product Manager | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document shows you how to use [Cloud Run](https://cloud.google.com/run/) to read data stored in a Google Sheet.

## Setup

### Clone this tutorial and change to its directory:

```
git clone https://github.com/GoogleCloudPlatform/community.git
cd community/tutorials/cloud-run-workspace-sheets
```

### Set Project ID Environment variable

```
export PROJECTID=$(gcloud config get-value project)
```

## Create an identity

There are several ways to authenticate a backend service to Workspace APIs. 

While you can create end-user based delegated OAuth credentials to use in a backend service, it is far simpler to use a service account identity directly.

For more on end-user auth Workspace API options, consult this [best practices document](https://static.googleusercontent.com/media/www.google.com/en//support/enterprise/static/gapps/docs/admin/en/gapps_workspace/Google%20Workspace%20APIs%20-%20Authentication%20Best%20Practices.pdf).

Create a Service account to run the service as:

```
gcloud iam service-accounts create sheets-reader
```

In this tutorial we are using a public sheet, but if you want to access a private sheet you would grant the this service account access to the the sheet by adding it's email address as a viewer in the Sheet's sharing dialog.

## Build the Service image

```
docker build -t gcr.io/${PROJECTID}/sheets-demo .
docker push gcr.io/${PROJECTID}/sheets-demo
```

## Deploy the service

gcloud run deploy sheets-demo --region us-central1 --allow-unauthenticated \
   --service-account=sheets-reader@${PROJECTID}.iam.gserviceaccount.com \
   --image=gcr.io/${PROJECTID}/sheets-demo:latest 


Once the service is deployed - you can visit the published URL and see the data read from a sheet rendered in the HTML returned.

Try changing the sheet ID to a private sheet you give explicit access to the sheets-reader service account.