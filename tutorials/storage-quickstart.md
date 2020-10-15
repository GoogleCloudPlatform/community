---
title: Cloud Storage quickstart - Create a bucket and upload files
description: Learn how to store objects in Cloud Storage.
author: jscud
tags: Cloud Storage
date_published: 2019-07-31
---

# Cloud Storage quickstart: Create a bucket and upload files

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=storage_quickstart)

</walkthrough-alt>

## Overview

Cloud Storage is a powerful and cost-effective storage solution for unstructured objects. In this tutorial,
you'll see how easy it is to store objects in Cloud Storage.

Here's what you'll do:

*   **Create a bucket**: Buckets hold the objects (any type of file) that you store in Cloud Storage.
*   **Upload and share objects**: Start using your bucket by uploading an object and making it publicly
    available.
*   **Clean up**: As a final step, you'll delete the bucket and object you created for this tutorial.
    It's important that you follow the cleanup steps at the end of the tutorial so that you don't incur
    unexpected charges.

## Project setup

Google Cloud organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Create a bucket

1.  Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
    then select **Storage**.
    
    <walkthrough-menu-navigation sectionId="STORAGE_SECTION"></walkthrough-menu-navigation>

1.  Click [**Create bucket**][spotlight-create-bucket].

1.  On the **Create a bucket** page, specify the bucket's properties.

    For this tutorial, you can use the default values for everything but **Name**.

    Here are some things to keep in mind:

     *  **Name**: Names must be globally unique. You'll see an error if you enter a
    name that's the same as another bucket's name in Cloud Storage.
     *  **Default storage class**: This is the storage class assigned to your
    bucket's objects by default. Your choice depends mainly on how
    frequently you expect the objects to be accessed and whether you're
    serving the data worldwide. The storage class affects your cost.
     *  **Location**: You'll want to keep your data close to the applications
    and users accessing it. The available choices depend on your storage
    class selection.

1.  Click the **Create** button.

## Upload an object

Now that you have a bucket, you can start uploading objects. You can upload any type of file.

* At the top of the **Bucket details** page, click [**Upload files**][spotlight-upload-file]
  and select a file to upload.
* Drag and drop a file onto the space below the bucket name.
* If you're using the interactive version of this tutorial in the Cloud Console, you can
  [click this link to create a sample text file][create-sample-file], and then click
  [**Refresh Bucket**][spotlight-refresh-bucket] at the top of the page to see it in your bucket.
  
## Clean up

To clean up the resources used in this tutorial, delete the bucket that you just created. Deleting
a bucket also deletes its contents.

1.  At the top of the table that lists the contents of your bucket, click [**Buckets**][spotlight-buckets-link]
    to go back to the **Browser** page.

1.  Check the box next to your bucket.

1.  At the top of the page, click [**Delete**][spotlight-delete-buckets] and confirm the deletion.

## Conclusion

<walkthrough-conclusion-trophy/>

Congratulations!

Now that you know how to store objects in Cloud Storage, here are some things
that you can do next:

*   Put Cloud Storage to real-world use by
    [hosting a static website](https://cloud.google.com/storage/docs/hosting-static-website).
*   Learn to use Cloud Storage with [the gsutil command-line tool](https://cloud.google.com/storage/docs/quickstart-gsutil).
*   Learn how you can start using Cloud Storage and other Google Cloud services for [free](https://cloud.google.com/free).

[create-sample-file]: walkthrough://create-sample-storage-file
[spotlight-buckets-link]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-path-link
[spotlight-create-bucket]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-cloudstorage-create-first-bucket-button,#p6n-cloudstorage-create-bucket
[spotlight-create-button]: walkthrough://spotlight-pointer?cssSelector=#p6ntest-gcs-create-bucket-button
[spotlight-delete-buckets]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-delete-bucket
[spotlight-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-public-link]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-browser-public-label
[spotlight-refresh-bucket]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-refresh-objects
[spotlight-share-public]: walkthrough://spotlight-pointer?cssSelector=.p6n-cloudstorage-browser-public-checkbox
[spotlight-upload-file]: walkthrough://spotlight-pointer?spotlightId=gcs-action-bar-upload-file
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
