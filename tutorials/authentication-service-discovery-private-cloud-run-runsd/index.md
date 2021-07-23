---
title: Easier authentication and service discovery for private Cloud Run services with runsd
description: Learn how to authenticate and call private Cloud Run services using standard URLs with no code changes
author: tth
tags:
date_published:
---
Tan Tze Hon | Solutions Architect | Google
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial is for developers who create services that run on Cloud Run.

You will learn how to use [`runsd`](https://github.com/ahmetb/runsd) to authenticate and call a private Cloud Run service without adding additional authentication code, using a predictable URL that’s known beforehand.

Basic knowledge of containers and Cloud Run is required for this tutorial.

## Objectives
*   Create a Memorystore for Redis instance
*   Deploy a receiving Cloud Run service that requires authentication and queries the Memorystore instance
*   Deploy a calling Cloud Run service that authenticates and calls the receiving Cloud Run service using `runsd`

## Costs
This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Run](https://cloud.google.com/run/pricing)
*   [Cloud Memorystore](https://cloud.google.com/memorystore/docs/redis/pricing)
*   [Serverless VPC Access](https://cloud.google.com/vpc/docs/serverless-vpc-access#pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin
For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the  "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://cloud.google.com/billing/docs/how-to/modify-project#enable-billing)

1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient
    permissions to use the services listed above.

## Using Cloud Shell

This tutorial uses the following tool packages:

* [`gcloud`](https://cloud.google.com/sdk/gcloud)

## Preparing your environment

### Open Cloud Shell

Open Cloud Shell by clicking the **Activate Cloud Shell** button in the upper-right corner of the Cloud Console.

### Get the sample code

The sample code for this tutorial is in the
[Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/authentication-service-discovery-private-cloud-run-runsd

## Implementation steps

### Set the environment variables

1.  Use a text editor to modify the `set_variables.sh` file to set the required environment variables:

        PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
        PROJECT_NUMBER="$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format='get(projectNumber)')"
        REGION=${REGION}
        REDIS_INSTANCE_ID=${REDIS_INSTANCE_ID}
        NETWORK=${NETWORK}
        CONNECTOR_ID=${CONNECTOR_ID}
        REDIS_CLIENT=${REDIS_CLIENT}
        CALLER=${CALLER}
        CALLER_SA =${CALLER_SA}

1. Run the script to set the environment variables:

        source set_variables.sh

### Enable the required APIs

1.  Enable the required APIs:

        gcloud services enable \
          compute.googleapis.com \
          redis.googleapis.com \
          cloudbuild.googleapis.com \
          run.googleapis.com \
          vpcaccess.googleapis.com

### Create a Memorystore instance

1. Create a Memorystore instance. It can take up to 5 minutes for instance creation:

        gcloud redis instances create ${REDIS_INSTANCE_ID} --size=2 --region=${REGION} \
          --network=${NETWORK} --redis-version=redis_5_0

1. After the instance is created, save the IP address and port of the instance in environment variables:

        REDIS_IP="$(gcloud redis instances describe ${REDIS_INSTANCE_ID} --region=${REGION} | awk '/host:/ {print $2}')"
        REDIS_PORT="$(gcloud redis instances describe ${REDIS_INSTANCE_ID} --region=${REGION} | awk '/port:/ {print $2}')"

### Create a Serverless VPC connector

1. Create a Serverless VPC connector for your Cloud Run instance to connect to the Memorystore instance.

        gcloud compute networks vpc-access connectors create ${CONNECTOR_ID} \
          --network ${NETWORK} \
          --region ${REGION} \
          --range 10.8.0.0/28 \
          --async

### Build the Memorystore client

1. Build a Memorystore client using Cloud Build:

        gcloud builds submit memorystore-client --tag gcr.io/${PROJECT_ID}/${REDIS_CLIENT}

### Deploy the Memorystore client to Cloud Run

1. Deploy a Memorystore client to Cloud Run. This initial deployment will allow external, unauthenticated requests to the Memorystore client:

        gcloud run deploy ${REDIS_CLIENT} \
          --image gcr.io/${PROJECT_ID}/${REDIS_CLIENT} \
          --platform managed \
          --allow-unauthenticated \
          --region ${REGION} \
          --vpc-connector ${CONNECTOR_ID} \
          --set-env-vars REDISHOST=${REDIS_IP},REDISPORT=${REDIS_PORT}

1. Visit your service and see the count on your Redis instance increase each time the service is visited:

        REDIS_CLIENT_URL="$(gcloud run services describe $REDIS_CLIENT --region ${REGION} | awk '/URL:/ {print $2}')"
        curl "${REDIS_CLIENT_URL}"

### Update the Memorystore client to accept only internal, authenticated requests

1. Deploy a new revision of the Memorystore client that accepts only authenticated requests from within the same project or VPC Service Controls perimeter:

        gcloud run deploy ${REDIS_CLIENT} \
          --image gcr.io/${PROJECT_ID}/${REDIS_CLIENT} \
          --platform managed \
          --ingress internal \
          --region ${REGION} \
          --no-allow-unauthenticated \
          --vpc-connector ${CONNECTOR_ID} \
          --set-env-vars REDISHOST=${REDIS_IP},REDISPORT=${REDIS_PORT}


### Verify Memorystore client is no longer reachable

1. After the deployment successfully completes, you are no longer be able to access the service:

        curl "${REDIS_CLIENT_URL}"

### Get project hash

1. Out of the box, Cloud Run service URLs on Cloud Run look like:

        {name}-{project_hash}-{region}.a.run.app

    We configure `runsd` using the project hash so that Cloud Run services can call the target service by simply using the service name in the form of http://name instead of http://{name}-{project_hash}-{region}.a.run.app.

    Save your project hash in an environment variable:

        PROJECT_HASH="$(echo $REDIS_CLIENT_URL | awk -F"-" '{print $2}')"

### Build the calling service

1. Build the calling service that will call the Memorystore client:

        gcloud builds submit caller --tag gcr.io/${PROJECT_ID}/${CALLER}

### Create a service identity

1. Create a service account for your calling service:

        gcloud iam service-accounts create $CALLER_SA

        gcloud iam service-accounts add-iam-policy-binding ${CALLER_SA}@${PROJECT_ID}.iam.gserviceaccount.com \
          --member "serviceAccount:${CALLER_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role roles/iam.serviceAccountUser

### Deploying the calling service

1. Deploy the calling service with the newly created service account as the service identity, using `runsd` to call other Cloud Run services with a stable URL and obtain authentication tokens without additional code changes:

        gcloud run deploy ${CALLER} \
          --image gcr.io/${PROJECT_ID}/${CALLER} \
          --platform managed \
          --region ${REGION} \
          --service-account ${CALLER_SA} \
          --allow-unauthenticated \
          --vpc-connector ${CONNECTOR_ID} \
          --vpc-egress all-traffic \
          --set-env-vars CLOUD_RUN_PROJECT_HASH=${PROJECT_HASH} \
          --set-env-vars REDIS_CLIENT=${REDIS_CLIENT}

    The calling service now sends internal requests to the Memorystore client as the requests are routed through the internal VPC connector. However, even though the calling service now obtains authentication tokens, the calling service itself is not authenticated to call the Memorystore client.

### Verify that you can't call the Memorystore client

1. Visit your calling service. It can't call the Memorystore client as it has not been authenticated to invoke the Memorystore client:

        CALLER_URL="$(gcloud run services describe $CALLER --region ${REGION} | awk '/URL:/ {print $2}')"
        curl "${CALLER_URL}"

### Authorize the calling service

1. Authorize the calling service:

        gcloud run services add-iam-policy-binding ${REDIS_CLIENT} \
          --member=serviceAccount:${CALLER_SA}@${PROJECT_ID}.iam.gserviceaccount.com \
          --role=roles/run.invoker \
          --region=${REGION}

    After the calling service has been authorized, the Memorystore client now recognizes the calling service's authentication token.

### Verify that you can call the service

1. Visit your calling service. You can now invoke the Memorystore client. IAM bindings can take a few minutes to take effect. If the calling service can't invoke the Memorystore client immediately, wait a minute and try again:

        curl "${CALLER_URL}"

    Using `runsd`, you've enabled service to service authentication without additional code changes, and called another Cloud Run service using a predictable URL known beforehand.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following effects:

* Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, delete selected resources inside the project instead of deleting the whole project.

If you plan to explore multiple tutorials, reusing projects can help you to avoid exceeding project quota limits.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

1.  In the Cloud Console, go to the [**Manage resources page**](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

-  Learn how to [build and deploy a Flask CRUD API with Firestore and Cloud Run](https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run)
-  Learn how to [control access for a Cloud Run application with conditional IAM roles](https://cloud.google.com/community/tutorials/cloud-run-conditional-iam).