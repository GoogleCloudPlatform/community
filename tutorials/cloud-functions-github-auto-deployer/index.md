---
title: Cloud Functions GitHub Auto-deployer
description: Learn how to automatically deploy HTTP Cloud Functions stored on GitHub when a commit is pushed.
author: ancavulpe
tags: Cloud Functions, Node.js
date_published: 2017-07-26
---
## Introduction

This simple tutorial demonstrates using an [HTTP Cloud Function][function] to
automatically re-deploy another [HTTP Cloud Function][function] stored on
[GitHub][github] when a commit is pushed.

[function]: https://cloud.google.com/functions/docs/writing/http
[github]: https://github.com

## Objectives

* Prepare an HTTP Cloud Function in your GitHub repository.
* Deploy an auto-deployer HTTP Cloud Function that watches changes in that
  repository.
* Make a new commit to your GitHub repository and watch your HTTP Cloud Function
  be automatically re-deployed.

## Costs

This tutorial uses billable components of [Cloud Platform][platform], including:

* [Google Cloud Functions][functions]
* [Google Cloud Storage][storage]

Use the [Pricing Calculator][price] to generate a cost estimate based on your
projected usage.

[functions]:https://cloud.google.com/functions
[storage]:https://cloud.google.com/storage
[price]:https://cloud.google.com/products/calculator

## Prerequisites

1.  Create a project in the [Google Cloud Platform Console][console].
1.  Enable billing for your project.
1.  Install the [Google Cloud SDK][sdk].

[console]: https://console.cloud.google.com/
[sdk]: https://cloud.google.com/sdk/

## Deploying the auto-deployer function

1.	Fork an existing github repo with hello world function.
1.	Clone the repository which contains the [auto-deployer function][repo].

        git clone https://github.com/GoogleCloudPlatform/community

[repo]:https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-functions-github-auto-deployer/auto-deployer

1.  Change into the cloned directory:

        cd community/tutorials/cloud-functions-github-auto-deployer/auto-deployer

1.	Update the `config.js` file with your own values:

    ```json
    {
      "secretToken" : "[YOUR_SECRET_TOKEN]",
      "stageBucket" : "[YOUR_STAGING_BUCKET_NAME]",
      "location" : "[YOUR_REGION]",
      "deployments": [
        {
          "repository":"[YOUR_REPOSITORY_1]",
          "path":"[YOUR_FUNCTION_PATH_1]",
          "functionName":"[YOUR_FUNCTION_NAME_1]"
        },
        {
          "repository":"[YOUR_REPOSITORY_2]",
          "path":"[YOUR_FUNCTION_PATH_N]",
          "functionName":"[YOUR_FUNCTION_NAME_N]"
        }
      ]
    }
    ```

    where

    * `[YOUR_SECRET_TOKEN]` is the secret key you will configure in your GitHub
      webhook	in order to validate the request.
    * `[YOUR_STAGING_BUCKET_NAME]` is the name of your staging Cloud Storage
      bucket.
    * `[YOUR_REGION]` is the region where your function is deployed.
    * `[YOUR_REPOSITORY]` is the owner/repo of the repository where the function
      to be deployed resides, e.g. `GoogleCloudPlatform/nodejs-docs-samples`.
    * `[YOUR_FUNCTION_PATH]` is the path of the HTTP Cloud Function in your
      GitHub repository, e.g. `functions/helloworld`
    * `[YOUR_FUNCTION_NAME]` is the name of the function that you want to be
      automatically deployed, e.g. `helloGET`.

1.  Run the following command to deploy the auto-deployer function:

        gcloud beta functions deploy githubAutoDeployer --stage-bucket [YOUR_STAGING_BUCKET_NAME] --trigger-http

    where `[YOUR_STAGING_BUCKET_NAME]` is the name of your staging Cloud Storage
    bucket.

## Making a function in your repository auto-deployable

1. 	To deploy an HTTP Cloud Function whenever a **commit** is pushed, create a
    **webhook** in your repository:

    Note: If you don't have an HTTP Cloud Function in a GitHub repository of
    your own, you can fork https://github.com/GoogleCloudPlatform/community and
    setup auto-deployment for the HTTP function found in the
    `tutorials/cloud-functions-github-auto-deployer/sample-function` directory.

  1.  Go to your GitHub repository.
  1.  Clink on the **Settings** tab.
  1.  Click on **Webhooks** option in the left panel.
  1.  Click on **Add webhook** button and confirm by reintroducing your
      credentials.
  1.  Enter the **HTTP trigger URL** of the auto-deployer function you just
      deployed into the **Payload URL** field, i.e. `https://[YOUR_REGION]-[YOUR_PROJECT_ID].cloudfunctions.net/gitHubAutoDeployer`,
      where `[YOUR_REGION]` is the region where your function is deployed and
      `[YOUR_PROJECT_ID]` is your Google Cloud project ID.
  1.  For **Content type** select **application/json**.
  1.  In the **Secret** textbox fill in the secret token you used in the
      `config.json` file (see `[YOUR_SECRET_TOKEN]` above) for validating the
      request.
  1.  Make sure that **Just the push event** is selected for triggering the
      webhook.
  1.  Click an **Add webhook** button.

1.  Update your repository and watch your function being re-deployed by the
    auto-deployer function:

  1. 	Modify the function in your repository.
  1. 	Push commit to your repository.
  1. 	Observe that the auto-deployer re-deploys your function.
