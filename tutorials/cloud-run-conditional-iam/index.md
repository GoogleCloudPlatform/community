---
title: Conditional IAM Roles with Cloud Run
description: Tutorial on setting up conditional IAM Roles for Cloud Run applications
author: mike-ensor
tags: cloud-run, iam, GCP, conditional iam
date_published: 2020-09-06
---

This tutorial takes a deeper look at running a managed Google Cloud Run application with a Google Service Account using Conditional IAM Roles.

## Objectives

1.  Create a simple application that lists contents of a [Google Cloud Storage][gcs] bucket.
1.  Create a [Google Service Account (GSA)][gsa] to manage the application's Google Service interaction
1.  Bind the Google Service Account with a [Conditional IAM Role][conditional-iam] `storage.objectViewer`

## Before you begin ___(optional)

* Costs
* Project w/ billing account
* `gcloud` initialized with project
* `gsutil` in PATH

## Overview

Applications that use Google Cloud services such as Google PubSub, Cloud Storage and CloudSQL require authentication.

## A closer look

### Overview of the workflow

1. Create a protected Cloud Storage bucket
1. Create an application container to access Cloud Storage bucket
1. Create a Google Service Account (GSA)
1. Create managed Cloud Run instance using the GSA
1. Setup conditional IAM permissions

## Creating Cloud Storage Bucket

```bash
# Generate random lower-case alphanumeric suffix
SUFFIX=$(head -3 /dev/urandom | tr -cd '[:alnum:]' | cut -c -5 | awk '{print tolower($0)}')
# Create bucket
gsutil mb gs://cloud-run-tutorial-bucket-${SUFFIX}
# Add item to bucket
wget https://cloud.google.com/images/run/google-cloud-run.png
gsutil cp google-cloud-run.png gs://cloud-run-tutorial-bucket-${SUFFIX}
# Verify contents
gsutil ls gs://cloud-run-tutorial-bucket-${SUFFIX}
```
### Sample Output
```
~: gsutil ls gs://cloud-run-tutorial-bucket-${SUFFIX}

gs://cloud-run-tutorial-bucket-xxxxx/google-cloud-run.png
```

## Create Application Container







...

[gsa]: https://cloud.google.com/iam/docs/service-accounts
[gcs]: https://cloud.google.com/storage
[conditional-iam]: https://cloud.google.com/iam/docs/managing-conditional-role-bindings

