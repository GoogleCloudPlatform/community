---
title: Automated static website publishing with Cloud Build
description: Learn how to automate publishing your static website to Cloud Storage with Cloud Build.
author: ahmetb
tags: Cloud Build, Hosting, Cloud Storage
date_published: 2017-03-13
---

This tutorial shows how to automate publishing a static HTML website using a
custom domain name to Cloud Storage using [Cloud Build][gcb].

## Objectives

- Automatically publish changes to your static website from the source control
  repository.

## Before you begin

1. Make sure you have a custom domain name (e.g., example.com).
1. Make sure the source code for your static website is hosted in a GitHub or
   BitBucket repository.
1. Make sure you verified ownership of your domain on
   [Google Webmaster Central][gwc]. Do not include `http://` or `https://` in the URL for the
   purposes of this tutorial.
1. Make sure you have a project in the Cloud Console to
   host your website.

## Set up a storage bucket

By uploading your website contents as files to Cloud Storage, you can
[host your static website][gcs-hosting] on buckets. First, you need to create a
bucket. Head to the [Storage][p6n-storage] section of the Cloud Console and type
in your domain name (e.g., `www.example.com`) and create the bucket:

![Create a bucket named as your domain
name](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/create-bucket.png)

After the bucket is created, you need to make it readable by everyone. Go to the
[Storage Browser][p6n-storage] on the Cloud Console, click the menu icon
to the right of the bucket, and select **Edit Object Default Permissions**:

![Change object default permissions of the
bucket](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/change-defacl.png)

Then add the user `allUsers` with the Reader role and click **Save**:

![Add allUsers as
HeReader](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/add-allUsers.png)

Now, you need to configure the storage bucket to serve a static website. Click
the **Edit Website Configuration** button on the list of buckets:

![Edit Website
Configuration](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/configure-website-button.png)

Specify the main page as `index.html` and click **Save**:

![Specify main
page](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/configure-website.png)

Now, configure your domain name’s DNS records to
[create a CNAME record][gcs-hosting] that points to Cloud Storage. This makes clients
requesting your website point to Cloud Storage APIs.

## Set up automated builds with a build trigger

You use [Cloud Build][gcb] and its
[build triggers](https://cloud.google.com/cloud-build/docs/running-builds/create-manage-triggers) 
to upload your website automatically every time you push a new git commit to the source repository.

If you do not have a repository on GitHub, you can fork [this sample repository][sample-repo] for 
this tutorial.

1. Go to the Cloud Build &rarr; [**Triggers**][p6n-triggers] page.

2. Click **Create trigger**.

3. Enter a name for your trigger (for example, `publish-website`).

4. If you forked the [sample repository][sample-repo] for this tutorial,
   select **Push to a branch** as your repository event.

5. Select the repository that contains your source code and build
   configuration file.

6. Specify the regular expression for the branch that will start your trigger (e.g., `^master$`).

7. Choose **Cloud build configuration (yaml or json)** as your build configuration
   file type.

8. Set the file location to `cloudbuild.yaml`.

9. Click **Create** to save your build trigger.

Now, create a `cloudbuild.yaml` file with the following contents in your
repository. Note that you can add files to your repository on thr GitHub website or
by cloning the repository on your development machine:

```yaml
steps:
  - name: gcr.io/cloud-builders/gsutil
    args: ["-m", "rsync", "-r", "-c", "-d", "./vision/explore-api", "gs://hello.alp.im"]
```

This YAML file declares a build step with the `gsutil -m rsync` command and
makes sure that the website is uploaded to the storage bucket. The `-m` flag
accelerates upload by processing multiple files in parallel, and the `-c` flag
avoids re-uploading unchanged files.

If you are using the sample repository, you should upload the
`./vision/explore-api/` directory. If you would like to upload your entire
repository to the storage bucket, make sure to change this value to `.` in the
YAML file.

The last command in the `args` is the name of your storage bucket prefixed with
`gs://`. Be sure to change this argument to the correct value.

After saving the file, commit and push the changes:

    git add cloudbuild.yaml
    git commit -m 'Add build configuration'
    git push

### Start the first build

After you push the `cloudbuild.yaml` file to your repository and create the build
trigger, you can start the first build manually. Go to the Cloud Console
[**Triggers**][p6n-triggers] section, click **Run Trigger**, and choose the branch
(for example, master) to build.

![Trigger the first build
manually](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/trigger-build.png)

Now click the **Build history** on the left and watch the build job execute and
succeed.

Remember that after now, every commit pushed to any branch of your GitHub
repository will trigger a new build and publish contents to your website. If you
need to change which git branches or tags you use for publishing, you can update
the Build Trigger configuration.

## Try it out

Point your browser to your website URL and see if it works:

![See if your website
works](https://storage.googleapis.com/gcp-community/tutorials/automated-publishing-cloud-build/browser.png)

## Clean up

After you no longer need the artifacts of this tutorial, you can clean up the
following resources in the Cloud Console to prevent incurring
additional charges:

- Storage: delete bucket named as your website
- Cloud Build &rarr; Triggers: delete build trigger
- Development &rarr; Repositories: delete mirrored repository

[gcb]: https://cloud.google.com/cloud-build/
[gwc]: https://www.google.com/webmasters/verification/
[gcs-hosting]: https://cloud.google.com/storage/docs/hosting-static-website
[p6n-storage]: https://console.cloud.google.com/storage/browser
[p6n-triggers]: https://console.cloud.google.com/gcr/triggers
[bt]: https://cloud.google.com/cloud-build/docs/creating-build-triggers
[sample-repo]: https://github.com/GoogleCloudPlatform/web-docs-samples
