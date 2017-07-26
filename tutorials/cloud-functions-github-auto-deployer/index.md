---
title: HTTP Auto-deployer Tutorial
description: Learn how to deploy automatically HTTP Cloud Function stored on GItHub when a commit is pushed.
author: ancavulpe
tags: Cloud Functions, Node.js
date_published: 2017-07-26
---
## Introduction

This simple tutorial demonstrate using an [HTTP Cloud Function][function] for re-deploying automatically another [HTTP Cloud Function][function] stored on [GitHub][git] when a commit is pushed.

[function]: https://cloud.google.com/functions/docs/writing/http
[git]: https://github.com

## Objectives

* Prepare an HTTP Cloud Function in your GitHub repository
* Deploy an auto-deployer HTTP Cloud Function that watches changes in that repository
* Make a new commit to your GitHub repository and watch your HTTP Cloud Function being automatically updated.

## Costs

This tutorial uses billable components of [Cloud Platform][platform], including:
* [Google Cloud Functions][functions]
* [Google Cloud Storage][storage]

Use the [Pricing Calculator][price] to generate a cost estimate based on your projected usage.
[functions]:https://cloud.google.com/functions
[storage]:https://cloud.google.com/storage/
[price]:https://cloud.google.com/products/calculator

## Before you begin:

1. Fork an existing github repo with hello world function.
1. Clone the repository which contain the [auto-deployer function][repo].
[repo]:https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-functions-github-auto-deployer/auto-deployer

## Preparing the application

Go to the directory with the auto-deployer function and update the `config.js` file.

	{
  	  "secretToken" : "[YOUR_SECRET_TOKEN]", 
  	  "stageBucket" : "[YOUR_STAGING_BUCKET_NAME]",
  	  "location" : "[YOUR_REGION]",
  	  "deployments": "[
     	    {
       	      "functionName":"[YOUR_FUNCTION_NAME_1]",
       	      "path":"[YOUR_FUNCTION_PATH_1]" 
     	    },
    	    ...
      	    {
       	      "functionName":"[YOUR_FUNCTION_NAME_N]",
              "path":"[YOUR_FUNCTION_PATH_N]" 
            }
          ]"
	}


where
* `[YOUR_SECRET_TOKEN]` is the secret key configured for the GitHub webhook in order to validate the request.
* `[YOUR_STAGING_BUCKET_NAME]` is the name of your staging Cloud Storage bucket.
* `[YOUR_REGION]` is the region where your function is deployed.
* `[YOUR_FUNCTION_NAME]` is the name of the function that you want to be automatically deployed.
* `[YOUR_FUNCTION_PATH]` is the path of the HTTP Cloud Function in your GitHub repository.

## Deploying the auto-deployer function
To deploy the `deployHttp` function with an HTTP trigger, run the following command in the `auto-deployer` directory:

	gcloud beta functions deploy gitHubAutoDeployer --stage-bucket [YOUR_STAGING_BUCKET_NAME] --trigger-http

where `[YOUR_STAGING_BUCKET_NAME]` is the name of your staging Cloud Storage bucket.

## Making the function from your repository auto-deployable
1. To deploy an HTTP Cloud Function whenever a **commit** is pushed, set the auto-deployer as a **webhook** in your repository:

	1. Go to your forked GitHub repository on the **Settings** tab.
	1. Click on **Webhooks** option in the left panel.
	1. Click on **Add webhook** button and confirm by reintroducing your credentials.
	1. Put the **HTTP trigger URL** of the auto-deployer in **Payload URL** field. E.g. `https://[YOUR_REGION]-[YOUR_PROJECT_ID].cloudfunctions.net/gitHubAutoDeployer` , where `[YOUR_REGION]` is the region where your function is deployed and `[YOUR_PROJECT_ID]` is your Cloud project ID.
	1. For **Content type** select **application/json**.
	1. In the **Secret** textbox fill in the secret token for validating the request.
	1. Make sure that **Just the push event** is selected for triggering the webhook.
	1. Click an **Add webhook** button.

1. Update your repository and watch your function being redeployed.
	1. Modify the function in your repository.
	1. Push commit to your repository.
	1. Observe that the auto-deployer re-deploys your function.


