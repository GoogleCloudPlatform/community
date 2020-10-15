---
title: Running partial redaction of credit card images with Cloud Functions and Cloud Data Loss Prevention API
description: Learn how to partially redact images with credit card numbers using Cloud Data Loss Prevention API, Cloud Functions, and Cloud Storage.
author: arieljassan
tags: Cloud Functions, Cloud Data Loss Prevention, Cloud Storage
date_published: 2019-02-04
---

Ariel Jassan | Data Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to partially redact images containing credit card numbers using a Cloud Function written in Python 3.7 and Cloud Data Loss Prevention (Cloud DLP) API. The Cloud Function will be triggered in the event of an image object uploaded to a Cloud Storage bucket.

In many cases, companies need to store images of the credit cards provided by their customers as proof of their purchase, and to comply with certifications such as PCI, they are required to redact part of the image to avoid visualizing the full number.

The Cloud Data Loss Prevention API provides scalable classification and redaction for sensitive data elements like credit card numbers, and as of today, the API redacts credit card numbers fully. This is useful in most cases, but in others, for the image of the credit card to be useful it is necessary to have part of its number redacted while another part is not redacted.

There might be cases in which the uploaded images do not contain credit card numbers or they are not clear enough. This solution includes instructions to set up Google Cloud Storage buckets for both, redacted and not redacted images, where the images will be stored after having been processed by the Cloud DLP API. Such implementation allows for setting different permissions levels and having more granular access control to each bucket.

## Objectives

- Enable Cloud Data Loss Prevention API, Cloud Functions, Cloud Storage
- Create relevant Cloud Storage buckets
- Deploy the Cloud Function
- Test the Cloud Function

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- Cloud Storage
- Cloud Data Loss Prevention API
- Cloud Functions

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Reference architecture

The following diagram shows the architecture of the solution:

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/partial-redaction-with-dlp-and-gcf/partial-dlp1.png)

1. An image of credit card is uploaded into a Cloud Storage bucket.
1. The upload event triggers a Cloud Function for partial redaction.
1. The Google Cloud Function calls the Cloud Data Loss Prevention API to identify the areas in the image with partial credit card numbers.
1. If a credit card number was identified, the Cloud Function stores the partially redacted image into a bucket with redacted images.
1. On the contrary, if no credit card number was identified, the Cloud Function stores the partially redacted image into a different bucket with the original image. 

## Before you begin

1.  Select or create a Google Cloud project.
    [Go to the Managed Resources page.](https://console.cloud.google.com/cloud-resource-manager)

1.  Make sure that billing is enabled for your project.
    [Learn how to enable billing.](https://cloud.google.com/billing/docs/how-to/modify-project)

1.  Enable Cloud Functions, Cloud Storage, and Cloud Data Loss Prevention API.
    [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=cloudfunctions,storage_api,dlp.googleapis.com):

        gcloud components update &&
        gcloud components install beta

## Preparing the application

1.  Create a Cloud Storage bucket to upload the original images, where *`YOUR_ORIGINAL_BUCKET`* is a globally unique bucket name:

        gsutil mb gs://YOUR_ORIGINAL_BUCKET

1.  Create a Cloud Storage bucket to upload the original images, where *`YOUR_REDACTED_BUCKET`* is a globally unique bucket name:

        gsutil mb gs://YOUR_REDACTED_BUCKET

1.  Create a Cloud Storage bucket to upload the original images, where *`YOUR_NOT_REDACTED_BUCKET`* is a globally unique bucket name:

        gsutil mb gs://YOUR_NOT_REDACTED_BUCKET

1.  Update the configuration file with the bucket names as you have created them. With the text editor of your choice, open the `config.json` file and change the variables according to the bucket names:

        {
          "REDACTED_BUCKET": "YOUR_REDACTED_BUCKET",
          "NOT_REDACTED_BUCKET": "YOUR_NOT_REDACTED_BUCKET"
        }

## Configuring the sets of credit card digits to redact

The present function redacts the second and third set of credit card digits. If you’d like to configure this in a different way, you can update the following lines in the `main.py` file:

    # Redact second and third set of credit card digits
    for box in [boxes[1], boxes[2]]:

## Deploying the function

To deploy the Cloud Function to your project, execute the command below. It creates a Python 3.7 Google Cloud Function in your project that is triggered when an object is uploaded into the bucket *`YOUR_ORIGIN_BUCKET`*.

    gcloud functions deploy partial_dlp --runtime python37 \
    --trigger-resource YOUR_ORIGIN_BUCKET \
    --trigger-event google.storage.object.finalize

## Testing the function

1.  You can use the command below to upload a sample image that contains a valid credit card number for testing into the *`YOUR_ORIGIN_BUCKET`* that you have created previously: 

        gsutil cp images/credit-card2.png gs://YOUR_ORIGIN_BUCKET

    After a few seconds, you should see the redacted image in the bucket *`YOUR_REDACTED_BUCKET`*

1.  Check the logs to be sure the executions have completed:

        gcloud functions logs read --limit 100 

## Extending this lab

Cloud Storage supports common use cases like setting a Time to Live (TTL), for example when you need to comply with retention policies. This can be achieved with [Object Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle#actions). 

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project you created.

To delete the project, follow the steps below:
1.  In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1.  In the project list, select the project you want to delete and click **Delete project**.

    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/partial-redaction-with-dlp-and-gcf/img_delete_project.png)
    
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn about [Cloud Data Loss Prevention API](https://cloud.google.com/dlp/)
- Learn about [Cloud Functions](https://cloud.google.com/functions/) and other [tutorials](https://cloud.google.com/functions/docs/tutorials/)
- Learn about [Cloud Storage Object Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle#actions)
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).


