---
title: Routing Cloud Run and Cloud Functions egress traffic through a static external IP address
description: Route all egress traffic from Cloud Run and Cloud Functions through a static IP address.
author: jphalip
tags: serverless, cloud-run, cloud-functions, networking
date_published: 2022-01-10
---

Julien Phalip | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

It is common for third-party services to allow access over the internet only from known IP addresses or IP address ranges. If your application runs on
Google Cloud serverless computing solutions like [Cloud Run](https://cloud.google.com/run) or [Cloud Functions](https://cloud.google.com/functions), by default 
the application gets a dynamic IP address when accessing the internet, which prevents it from consistently accessing such third-party services. To guarantee the 
use of a static external IP address, you must use a [Serverless VPC Access connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) combined
with a [Cloud NAT](https://cloud.google.com/nat/) instance. This tutorial shows you how to deploy this solution for Cloud Run and Cloud Functions.

![Architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/serverless-static-ip/serverless-static-ip.png)

## Objectives

+   Deploy sample Cloud Run and Cloud Functions applications.
+   Create and configure a Serverless VPC Access connector.
+   Create a public IP address.
+   Deploy a Cloud NAT instance to channel internet traffic through the public IP address.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

+   [Cloud Run](https://cloud.google.com/run)
+   [Cloud Functions](https://cloud.google.com/functions)
+   [Serverless VPC Access connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)
+   [Cloud NAT](https://cloud.google.com/nat)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your
projected usage.

## Before you begin

### Create a new project

1.  In the Google Cloud Console, go to the [project selector page](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Select or create a Google Cloud project. If you don't plan to keep the resources that you create in this procedure,
    create a project instead of selecting an existing project. After you finish this tutorial, you can delete the
    project, removing all resources associated with the project.

### Enable billing

Make sure that billing is enabled for your Google Cloud project.
[Learn how to confirm that billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

### Set up the environment

1.  Start a [Cloud Shell instance](https://console.cloud.google.com/home/dashboard?cloudshell=true).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community

1.  Go to the directory for this tutorial:

        cd community/tutorials/serverless-static-ip

1.  Enable the Google Cloud APIs that this tutorial uses:

        gcloud services enable \
          compute.googleapis.com \
          cloudfunctions.googleapis.com \
          run.googleapis.com \
          cloudbuild.googleapis.com \
          vpcaccess.googleapis.com

1.  Set environment variables:

        export PROJECT=$(gcloud info --format='value(config.project)')
        export REGION=us-central1
        export NETWORK_NAME="my-network"
        export STATIC_IP_NAME="my-static-ip"
        export CLOUD_RUN_APP="my-app"
        export VPC_CONNECTOR="my-connector"
        export CONNECTOR_IP_RANGE="10.8.0.0/28"
        export NAT_ROUTER="nat-router"  
        export NAT_CONFIG="nat-config"
    
    This tutorial uses the `us-central1` region. You can use a different region, but make sure that it's one of the available locations for
    [Cloud Run](https://cloud.google.com/run/docs/locations) and [Cloud Functions](https://cloud.google.com/functions/docs/locations).
    
    The value for `CONNECTOR_IP_RANGE` corresponds to the CIDR range of internal addresses that are reserved for the Serverless VPC Access connector.
    You can change this value; the range must be unique and it must not overlap with existing ranges in your VPC network.

## Configure the network

In this section, you configure the network components of the solution.

1.  Create a new network:

        gcloud compute networks create ${NETWORK_NAME} \
          --subnet-mode custom

1.  Create a new external static IP address:

        gcloud compute addresses create ${STATIC_IP_NAME} \
          --region ${REGION}

1.  Display the value of the IP address:

        gcloud compute addresses describe ${STATIC_IP_NAME} \
          --region ${REGION} \
          --format "value(address)"

    Take note of the returned value. You will compare it to the value returned in later steps of this tutorial.

1.  Create a new router:

        gcloud compute routers create ${NAT_ROUTER} \
          --network ${NETWORK_NAME} \
          --region ${REGION}

1.  Add a NAT (network address translation) configuration to the router:

        gcloud compute routers nats create ${NAT_CONFIG} \
          --router-region ${REGION} \
          --router ${NAT_ROUTER} \
          --nat-all-subnet-ip-ranges \
          --nat-external-ip-pool ${STATIC_IP_NAME}

1.  Create a Serverless VPC Access connector:

        gcloud compute networks vpc-access connectors create ${VPC_CONNECTOR} \
          --network ${NETWORK_NAME} \
          --region ${REGION} \
          --range ${CONNECTOR_IP_RANGE}

## Deploy a Cloud Run app

In this section, you deploy a sample Cloud Run app to demonstrate how the external egress routing works.

1.  Build the container image as defined by the `Dockerfile` located in the `cloud-run` directory:

        gcloud builds submit cloud-run \
          --tag gcr.io/${PROJECT}/${CLOUD_RUN_APP}

1.  Deploy the Cloud Run app:
 
        gcloud run deploy ${CLOUD_RUN_APP} \
          --image gcr.io/${PROJECT}/${CLOUD_RUN_APP} \
          --platform managed \
          --allow-unauthenticated \
          --region ${REGION} \
          --vpc-connector ${VPC_CONNECTOR} \
          --vpc-egress all-traffic

    The `--vpc-egress all-traffic` option is what causes all outbound traffic from the Cloud Run app to be routed
    through the VPC connector.

1.  Retrieve the Cloud Run app's URL:

        SERVICE_URL=$(gcloud run services describe ${CLOUD_RUN_APP} \
          --platform managed \
          --region ${REGION} \
          --format "value(status.url)")

1.  Open the Cloud Run app's URL:

        curl ${SERVICE_URL}/run-ip

    The output looks like the following:

        The Cloud Run app's external IP address is: [X.X.X.X]

    The app makes a call to [http://checkip.dyndns.org](http://checkip.dyndns.org) to check the origin IP address,
    as you can see in the app's code. The value of `[X.X.X.X]` should match the value of the external static IP
    address that you created in the "Configure the network" section.

## Deploy a Cloud Function

In this section, you deploy a sample Cloud Function to demonstrate how the external egress routing works.

1.  Deploy the Cloud Function located in the `cloud-functions` directory:

        gcloud functions deploy function_ip \
          --source cloud-functions \
          --trigger-http \
          --runtime nodejs14 \
          --allow-unauthenticated \
          --region=${REGION} \
          --egress-settings all \
          --vpc-connector ${VPC_CONNECTOR}

    The `--egress-settings all` option is what causes all outbound traffic from the Cloud Function to be routed through the
    VPC connector.

1.  Call the Cloud Function:

        gcloud functions call function_ip --region ${REGION}

    The output looks like the following:

        The Cloud Function's external IP address is: [X.X.X.X]

    The function makes a call to [http://checkip.dyndns.org](http://checkip.dyndns.org) to check the origin IP address, as you can see in the function's code. 
    The value of `[X.X.X.X]` should match the value of the external static IP address that you created in the "Configure the network" section.

## Cleaning up

After you've finished the tutorial, clean up the Google Cloud resources so that you won't continue to be billed for them.

The easiest way to eliminate billing is to delete the project that you created for the tutorial:

1.  In the Cloud Console, go to the
    [Projects](https://console.cloud.google.com/iam-admin/projects) page.
1.  Click the trash can icon to the right of the project name.

**Warning:** If you used an existing project, deleting the project also deletes any other work that you've done in the project.

## What's next

+   Learn more about using a Serverless VPC Access connector:

    +   [Cloud Run](https://cloud.google.com/run/docs/configuring/connecting-vpc)
    +   [Cloud Functions](https://cloud.google.com/functions/docs/networking/connecting-vpc)
    +   [App Engine](https://cloud.google.com/appengine/docs/standard/python3/connecting-vpc)

+   See a
    [similar deployment of this solution using Terraform](https://medium.com/google-cloud/provisioning-cloud-run-with-cloud-nat-using-terraform-e6b8d678eb85).
+   Check out the documentation on
    [setting up a static outbound IP address for Cloud Run](https://cloud.google.com/run/docs/configuring/static-outbound-ip).
