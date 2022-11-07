---
title: Automate building Android APK files with Cloud Build CI/CD and a Gradle Docker image
description: Set up a Cloud Build trigger that builds your Android app and uploads it to a Cloud Storage bucket.
author: timtech4u
tags: Android, automation, Gradle, Cloud Build
date_published: 2019-07-30
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you set up a Cloud Build trigger that builds your Android application and uploads it to a Cloud Storage
bucket. The builds of new APK bundles are automatically triggered after code is pushed to your repository.

## Objectives

- Create a [Cloud Build trigger](https://cloud.google.com/cloud-build).
- Add a `cloudbuild.yaml` build configuration file to your code repository.
- Create a [Cloud Storage](https://cloud.google.com/storage/) bucket for your built APKs.

## Before you begin

1.  [Create a new Google Cloud project](https://console.cloud.google.com/project), or use an existing one.
2.  [Enable billing for your project](https://support.google.com/cloud/answer/6293499#enable-billing).
3.  [Enable the Cloud Build API](https://console.cloud.google.com/cloud-build/builds).

## Costs

Cloud Build is free for up to the first 120 build minutes per day. Check the
[Cloud Build pricing page](https://cloud.google.com/pricing/) for details.

## Get the sample code

Get the sample code from [GitHub Gist](https://github.com/Timtech4u/gcb-android-tutorial).

## Set up Cloud Storage

In this section, you create a Cloud Storage bucket, where your project APK files will be stored.

1.  Go to the [**Browser** page](https://console.cloud.google.com/storage/browser) for Cloud Storage.
1.  Click **Create bucket**.
1.  On the **Create a bucket** page, provide a unique bucket name.
1.  Click the **Create** button.
1.  (Optional) [Make the bucket public](https://cloud.google.com/storage/docs/access-control/making-data-public#buckets).
    1. On the **Bucket details** page, on the **Permissions** tab, enable bucket-level permissions.
    1. Click **Add members**.
    1. In the **New members** field, enter `allUsers`.
    1. In the **Role** field, choose **Storage Object Viewer**, and then click **Save**.
       (*Note: Your bucket is public and can be accessed by anyone on the internet.*)
1.  Grant Cloud Build access to Cloud Storage (optional, if bucket is public):
    1. Open the [IAM page](https://console.cloud.google.com/project/_/iam-admin/iam?_ga=2.2968627.-2014380672.1551979429)
       in the GCP Console.
    1. Select your project and click **Continue**.
    1. In the list of members, look for your Cloud Build service account named
       [PROJECT_ID]@cloudbuild.gserviceaccount.com, where [PROJECT_ID] is your GCP project ID.
    1. Click the pencil icon in that row.
    1. Click **Add another role**, select **Storage Object Admin** under **Storage**, and click Save.


## Set up Cloud Build

You need to ensure that your application code and all necessary files needed for building an APK are available in a code 
repository. Cloud Build currently supports Cloud Source Repositories, GitHub, and Bitbucket. You can also make use of the 
sample code for this tutorial, [here](https://github.com/Timtech4u/gcb-android-tutorial).

In your repository, create a build configuration file, `cloudbuild.yaml`, which contains instructions for Cloud Build. The 
configuration file for this tutorial is as follows:

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
    
In a nutshell, Cloud Build helps you run the following Docker command:

    docker run -v $(pwd):/home/app --rm gcr.io/fullstackgcp/gradle /bin/bash -c 'cd /home/app && ./gradlew clean assembleDebug'`
   
In the command, we specify `-v`, which mounts our current directory as the volume, and `--rm`, which removes the container 
on exit.
   
You can change the  `-c` command on your `cloudbuild.yaml` file if you would like to use other Gradle commands.
   
Cloud Build also copies the output `app-debug.apk` into your Cloud Storage bucket as `app-debug-$SHORT_SHA.apk`, where
`$SHORT_SHA` is the first seven characters of `COMMIT_SHA` of the commit that triggered Cloud Build; it is meant to tag the
APK builds in your GCS bucket.

### Set up a Cloud Build trigger

A Cloud Build trigger listens to changes in your code repository. Follow the steps below to create a Cloud Build trigger:

1.  Visit the [Cloud Build **Triggers** page](https://console.cloud.google.com/cloud-build/triggers) and
    click **Create Trigger**.
1.  Enter a name for your trigger.
1.  Select the repository event to start your trigger.
1.  Select the repository that contains your source code and build
    configuration file.
1.  Specify the regular expression for the branch or tag name that will start your
    trigger.
1.  Choose **Cloud Build configuration (yaml or json)** as your build
    configuration.
1. In the **Cloud Build configuration file location** field, type `cloudbuild.yaml` after the `/`.
1.  Click **Create** to save your build trigger.
1.  (Optional) To manually test a build trigger, click **Run trigger** on your trigger's entry in the triggers list.

Great! You have just configured Cloud Build for your code repository. On code push, it builds your Android APK and uploads
to your Cloud Storage bucket. 

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this tutorial.

1.  Delete the project used (if you created a new project).
2.  Delete the Cloud Build trigger and Cloud Storage bucket.

You might choose to disable the Cloud Build trigger, rather than deleting it.

You might also choose to pause the Cloud Scheduler job.

## Next steps

If you want to learn more about Cloud Build, check out the following resources:

-  [Cloud Build documentation](https://cloud.google.com/cloud-build/docs/) 
-  [Official Cloud Builder](https://github.com/GoogleCloudPlatform/cloud-builders)
-  [Community Cloud Builders](https://github.com/GoogleCloudPlatform/cloud-builders-community)
-  [Google Cloud Platform Awesome List](https://github.com/GoogleCloudPlatform/awesome-google-cloud)
