---
title: Label images with the Cloud Vision API
description: Learn the basics of image labeling with a simple Cloud Vision API application.
author: jscud
tags: Cloud Vision
date_published: 2019-07-31
---

# Label images with the Cloud Vision API

<!-- {% setvar repo_url "https://github.com/GoogleCloudPlatform/python-docs-samples.git" %} -->
<!-- {% setvar repo_name "python-docs-samples" %} -->
<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=python_vision_quickstart)

</walkthrough-alt>

## Introduction

This tutorial walks you through a basic application that uses the Vision API.
In this application, a `LABEL_DETECTION` request annotates an image with a
label (tag) that is selected based on the image content. For example, a
picture of a barn may produce a label of `barn`, `farm`, or some other similar
annotation.

["Python" and the Python logos are trademarks or registered trademarks of the
Python Software Foundation.](walkthrough://footnote)

## Project setup

Google Cloud organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Enable the Vision API

Before your project can use a service like the Vision API, you must enable the
API for the project.

Use the following to enable the API:

<walkthrough-enable-apis apis="vision.googleapis.com"></walkthrough-enable-apis>

<walkthrough-alt>
https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com
</walkthrough-alt>

## Open Cloud Shell

In this tutorial, you do much of your work in Cloud Shell, which is a built-in command-line tool for the Cloud Console.

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the Cloud Console.

## Clone the sample code

Use Cloud Shell to clone and navigate to the sample code. The sample code
is cloned from your project repository to the Cloud Shell.

If the directory already exists, remove the previous files before cloning:

```bash
rm -rf python-docs-samples
```

Clone the sample repository:

```bash
git clone https://github.com/googleapis/python-vision.git
```

Change directory to the tutorial directory:

```bash
cd python-vision/samples/snippets/quickstart
```

You are now in the main directory for the sample code.

## Explore the application

Enter the following command to view the application code:

```bash
cat quickstart.py
```

The `quickstart.py` file formats your request information, like the request type
and content. Expand each section below to learn about the details.

Requests to the Vision API are provided as JSON objects. See the
[Vision API reference][vision-request-doc] for complete information on the specific
structure of such a request. Your JSON request is only sent when you call
`execute`. This pattern allows you to pass around such requests and call
`execute` as needed.

## Set up up a service account and credentials

To use a Cloud API, you need to set up the proper [credentials][auth-doc] for 
your application. This enables your application to authenticate its identity to
the service and obtain authorization to perform tasks.

### Create a service account

You need to create a service account to authenticate your API requests. If you
already have the service account created, it will be reused.

```bash
gcloud iam service-accounts create vision-quickstart --project {{project_id}}
```

`{{project_id}}` is your Google Cloud project ID.

### Create credentials

Next, create a service account key and set it as your default credentials.

```bash
gcloud iam service-accounts keys create key.json --iam-account \
  vision-quickstart@{{project_id}}.iam.gserviceaccount.com
```

```bash
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

<walkthrough-test-code-output text="created key"></walkthrough-test-code-output>

## Test your app

To test your app with a sample image, enter the following command:

```bash
python quickstart.py
```

The image resource, `resources/wakeupcat.jpg`, is specified in the source.
([View image][cat-picture])

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You are ready to use the Cloud Vision API.

Here's what you can do next:

*   Work through the [face detection][face-tutorial] tutorial.
*   Try the [document text][document-text-tutorial] tutorial.
*   See the [sample applications][vision-samples].
*   Download the [Cloud SDK][get-cloud-sdk] to run on your local machine.

[auth-doc]: https://cloud.google.com/vision/docs/auth
[cat-picture]: https://raw.githubusercontent.com/GoogleCloudPlatform/python-docs-samples/master/vision/cloud-client/quickstart/resources/wakeupcat.jpg
[document-text-tutorial]: https://cloud.google.com/vision/docs/fulltext-annotations
[face-tutorial]: https://cloud.google.com/vision/docs/face-tutorial
[get-cloud-sdk]: https://cloud.google.com/sdk/
[vision-request-doc]: https://cloud.google.com/vision/reference/rest
[vision-samples]: https://cloud.google.com/vision/docs/samples
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
