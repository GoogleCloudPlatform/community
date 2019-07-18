---
title: Automate building Android APK files with Cloud Build CI/CD and a Gradle Docker image
description: Set up a Cloud Build trigger that builds your Android app and uploads it to a Cloud Storage bucket.
author: timtech4u
tags: Android, automation, Gradle, Cloud Build
date_published: 2019-07-19
---

In this tutorial, you set up a Cloud Build trigger that builds your Android application and uploads it to a Cloud Storage
bucket. The builds of new APK bundles are automatically triggered after code is pushed code to your code repository.

## Objectives

- Create a [Cloud Build trigger](https://cloud.google.com/cloud-build).
- Add a `cloudbuild.yaml` build configuration file to your code repository.
- Create a [Cloud Storage](https://cloud.google.com/storage/) bucket for your built APKs.

## Before you begin

1.  [Create a new Google Cloud Platform (GCP) project](https://console.cloud.google.com/project), or use an existing one.
2.  [Enable billing for your project](https://support.google.com/cloud/answer/6293499#enable-billing).
3.  [Enable the Cloud Build API](https://console.cloud.google.com/cloud-build/builds).

## Costs

Cloud Build is free for up to the first 120 build minutes per day. Check the
[Cloud Build pricing page](https://cloud.google.com/pricing/) for details.

## Get the sample code

Get the sample code from [GitHub Gist](https://github.com/Timtech4u/gcb-android-tutorial).

## Set up the Cloud Storage

This is where your project APKs will be stored.

1.  Go to the [**Browser** page](https://console.cloud.google.com/storage/browser) for Cloud Storage.
1.  Click **Create bucket**.
1.  Provide a unique bucket name.
1.  Make Bucket Public (Optional)
  - Enable **Bucket-level** permissions.
  - Click **Add Members** on the **Permissions** tab of your Bucket.
  - Enter **New Members** value to be **allUsers**
  - Select **Storage Object Viewer** Role under **Storage** and click **Save**
  Note that: **Your bucket is public and can be accessed by anyone on the internet**
1. Granting Cloud Build access to Cloud Storage (Optional - If your bucket is public)
  - [Open the IAM page in GCP Console.](https://console.cloud.google.com/project/_/iam-admin/iam?_ga=2.2968627.-2014380672.1551979429)
  - Select your project and click **Continue**.
  - In the list of members look for your Cloud Build service account named  *[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com*, where  *[PROJECT_NUMBER]* is your GCP project number.
  - Click the pencil icon in that row.
  - Click **Add another role**, select **Storage Object Admin** under **Storage** and click Save.


## Set up Cloud Build

-  You need to ensure your application codes and all necessary files needed for building an APK are available on a code repository. Cloud Build currently supports Cloud Source Repositories, GitHub, or Bitbucket. You can also make use of the sample codes for this tutorial, [here](https://github.com/Timtech4u/gcb-android-tutorial) 
-  In your repository, create a build configuration file: cloudbuild.yaml, which contains instructions for Cloud Build. The configuration file for this tutorial is as follows:
    ```yaml
    # cloudbuild.yaml
    steps:
    # Set a persistent volume according to https://cloud.google.com/cloud-build/docs/build-config (search for volumes)
    - name: 'ubuntu'
      volumes:
      - name: 'vol1'
        path: '/persistent_volume'
      args: ['cp', '-a', '.', '/persistent_volume']

    # Build APK with Gradle Image from mounted /persistent_volume using name: vol1
    - name: 'gcr.io/cloud-builders/docker'
      volumes:
      - name: 'vol1'
        path: '/persistent_volume'
      args: ['run', '-v', 'vol1:/home/app', '--rm', 'gcr.io/fullstackgcp/gradle', '/bin/sh', '-c', 'cd /home/app && ./gradlew clean assembleDebug']

    # Push the APK Output from vol1 to your GCS Bucket with Short Commit SHA.
    - name: 'gcr.io/cloud-builders/gsutil'
      volumes:
      - name: 'vol1'
        path: '/persistent_volume'
      args: ['cp', '/persistent_volume/app/build/outputs/apk/debug/app-debug.apk', 'gs://fullstackgcp-apk-builds/app-debug-$SHORT_SHA.apk']

    timeout: 1200s
    ```
-  In a nutshell, Cloud Build helps you run the following docker command:
   `docker run -v $(pwd):/home/app --rm gcr.io/fullstackgcp/gradle /bin/bash -c 'cd /home/app && ./gradlew clean assembleDebug'`
   
   In the command, we specify: **-v** which mounts our current directory as the volume, **--rm** which removes the container on exit.
   
   You can change the  **-c** command on your **cloudbuild.yaml** file if you would like to use other Gradle commands.
   
   Cloud Build also copies the output: **app-debug.apk** into your  GCS Bucket as **app-debug-$SHORT_SHA.apk** , where *$SHORT_SHA* is the first seven characters of *COMMIT_SHA* of the commit which triggered Cloud Build, it is meant to tag the APK builds on your GCS Bucket.


### Set up Cloud Build Trigger

Cloud Build trigger listens to changes in your code repository, follow the steps below to create a GCB trigger.

-  Visit the  [Cloud Build Triggers Page](https://console.cloud.google.com/cloud-build/triggers) and Click **Create Trigger**
-  Select *Code Repository Source*
-  Select **Repository** (Filter your search by entering the repository name)
-  Enter **Description** and **Set Build Configuration** : **cloudbuild.yaml** (Set a **Branch Regex** if you would like to limit the trigger to certain branches)
-  Click **Create Trigger**, you can optionally also **Run Trigger*

Great! You have just configured Cloud Build for your code repository, on code push, it builds your Android APK and uploads to your GCS Bucket. 

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this tutorial.

1.  Delete the project used (if you created a new project).
2.  Delete the Cloud Build Trigger and Cloud Storage Bucket.

You might also choose to disable the Cloud Build Trigger.


You might also choose to pause the Cloud Scheduler job.

## Next steps

If you want to learn more about Cloud Build check out the following resources:

-  [Cloud Build Documentation](https://cloud.google.com/cloud-build/docs/) 
-  [Official Cloud Builder](https://github.com/GoogleCloudPlatform/cloud-builders)
-  [Community Cloud Builders](https://github.com/GoogleCloudPlatform/cloud-builders-community)
-  [Google Cloud Platform Awesome List](https://github.com/GoogleCloudPlatform/awesome-google-cloud)
