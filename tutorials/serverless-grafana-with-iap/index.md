---
title: How to deploy Grafana on Cloud Run with IAP using Terraform
description: In this tutorial, we'll be demonstrating how to deploy Grafana serverless and restrict access to the dashboard.
author: cgrotz,annamuscarella
tags: serverless, identity, proxy, sql
date_published: 2021-11-28
---

Christoph Grotz | Strategic Cloud Engineer | Google

Anna Muscarella | Strategic Cloud Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, we'll be demonstrating how to deploy Grafana serverless and restrict access to the dashboard. If you're a developer, DevOps engineer, or simply interested in deploying applications serverless or restricting access to it, read on.

You should have basic knowledge of Google Cloud Platform, Grafana and Terraform, own a domain, and can modify its A record.

![Serverless Grafana architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-iap-architecture.png)


## Objectives

By the end of this tutorial, you'll have information to:

  * Run the Terraform script to deploy Grafana on Cloud Run with CloudSQL as database. and Identity Aware Proxy setup.
  * Create a new user for accessing the dashboard.
  * Explore and test the capabilities of Identity Aware Proxy (IAP) to restrict access to your Grafana dashboard.

## Costs

We'll be using billable components of Google Cloud, including the following:
  * [Cloud Run](https://cloud.google.com/run)
  * [CloudSQL](https://cloud.google.com/sql)
  * [Cloud Load Balancer](https://cloud.google.com/load-balancing)
  * [Identity-Aware Proxy](https://cloud.google.com/iap)
  * [Secret Manager](https://cloud.google.com/secret-manager)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## What happens behind the scenes

You can easily deploy the setup with minimal effort; most of it is done through a Terraform script. Here is what happens in the background:

First, all required APIs are enabled, e.g., IAM, Cloud Run, Compute, IAP, SQL by the Terraform script. Hence you don't need to worry about this step.

Grafana requires a database for storing data. Therefore, a CloudSQL instance is created. The password for the database user is placed in Secret Manager, for secured access.

Then, the Cloud Run container is deployed using the GCR mirror of the Grafana container image and started. The script also passes required environment variables to the container, such as information about the database connection, and auth proxy. 

To make sure your Grafana dashboard is useful, a datasource for Google Cloud Monitoring is mounted. We use [Grafanas provisioning mechanism](https://grafana.com/docs/grafana/latest/administration/provisioning/) for that, which discovers data sources and dashboards from the disk. Since Cloud Run instances don't have persistent volumes at the moment, we can't just place the datasource and dashboard file into the filesystem. As a workaround, the file is added as a secret to Secret Manager and then copied to the required location so Grafana can pick up the data source correctly. Et voila, you now have mock data in your dashboard! An alternative could be to use [GCS Fuse](https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse), which allows mounting a GCS bucket into the filesystem, but this requires modifying the Docker image.

To access your Grafana dashboard, Cloud Load Balancer is configured to service HTTPS traffic from CloudRun using a Serverless Network Endpoint Group (NEG) as backend service. Identity-Aware Proxy (IAP) is integrated with the Load Balancer backend service. Client ID and secret are passed to the Load Balancer configuration. IAP provides headers containing the authorization information to applications secured with it ([link to documentation](https://cloud.google.com/iap/docs/signed-headers-howto)). Grafana provides the [functionality](https://grafana.com/docs/grafana/latest/auth/auth-proxy/) to receive exactly such header information for authentication. 

With other words: IAP and Grafana? A match made in heaven.


### Before you begin

You should have a Google Cloud Platform account and project setup, billing configured for your project, and Terraform installed and enabled.
  1. [Download the code](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code) from the tutorial resources.
  2. Open the working directory with your preferred terminal. The working directory is: Examples > Serverless > Grafana.
  3. Know your GCP project ID. If you don’t know how to find the project ID, you can learn about it [here](https://support.google.com/googleapi/answer/7014113?hl=en).
  4. Choose a region to host your project in, ideally one that’s close to you. You can find an overview of available regions [here](https://cloud.google.com/compute/docs/regions-zones).
  5. Make sure you know the domain name where you want to host your Grafana dashboard and are able to edit the A record for this domain.
  6. *Run* `gcloud auth login` to authenticate against Google Cloud Platform. Ideally, you should be using a service account for this, as described [here](https://cloud.google.com/sdk/gcloud/reference/auth/activate-service-account).


## Configure the OAuth consent screen

Configure an OAuth consent screen for Identity-Aware Proxy. 
  1. Go to GCP Console > Security > Identity-Aware Proxy. 
  2. If you didn’t configure a consent screen before, there will be a red warning message prompting you to configure one. 
  ![Consent missing error message](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-consent-not-confgured.png)
  1. Click Configure Consent Screen, choose User Type Internal and click Create. Internal allows only users that are part of your organization to access your application. You can add additional users by logging into admin.google.com.
  ![Configure consent](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-configure-oauth.png)
  4. Enter the app name and user support email, then click Save and continue until the process is complete.


### Set up Terraform and Docker

Next, you’re going to set up the typical configuration for Terraform in order for the project to deploy.

  1. *Open* the Working Directory Examples > Serverless > Grafana in your favorite shell.
  2. *Run* `terraform init`
  3. *Set* required terraform variables, e.g., Linux:
  `export TF_VAR_project_id=[YOUR_GCP_PROJECT_ID]`
  `export TF_VAR_domain=[YOUR_DOMAIN] This is the domain to host your Grafana dashboard.`


### Execute the Terraform script to create your Grafana Dashboard

  1. *Run* `terraform plan` and confirm that all steps are correct.
  2. *Run* `terraform apply`.
  3. Confirm the command has been executed successfully.
  4. *Copy* the external_ip from the console Outputs. *Add* an A record redirect from your domain to this IP address.
  5. Wait around 5 - 10 minutes for GCP Load Balancer to perform certificate checks.


### Access your Grafana Dashboard
  1. Open an Incognito browser window. Go to admin.google.com and sign in with your GCP account owner. Create a new user (only users who are part of your domain can access the dashboard).
  2. Open the GCP Console and go to IAM > Add > enter your user’s email (e.g., user@your-domain.com) and select role IAP-secured Web App User.
  3. Open an incognito window, go to your-domain.com (the domain you used in step 6) and sign in using the newly created user (you will be prompted to change your password the first time you login).


## Conclusion
Congratulations, you now have a serverless deployment of Grafana up and running, connected with Google Cloud Monitoring and secured using Google's Identity-Aware Proxy. You can now access and login to Grafana using your browser and accessing your domain. There should already be a dashboard available monitoring GCLB for you. This provides you with reduced worries around properly hosting your Grafana dashboards, while also providing a very low cost solution to hosting Grafana. Please keep in mind that should you want to use the alerts feature from Grafana you should consider keeping some [CPU allocated](https://cloud.google.com/run/docs/configuring/cpu-allocation), otherwise alerts might not be triggered. 

![Grafana dashboard screenshot](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-dashboard-screenshot.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete most resources used with Terraform.

Alternatively, if you created a new peoject for deploying the resources, you may also delete the whole project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.


To delete resources only, do the following:

1. *Manually delete* your CloudSQL instance, as deletion protection is activated. Go to Google Cloud console, then open the [SQL page](https://console.cloud.google.com/sql/instances), click on the [**grafana** instance](https://console.cloud.google.com/sql/instances/grafana/overview) and click **Delete**
2. *Execute* `terraform destroy` to delete the remaining resources. 



## Troubleshooting

If you see the following error message while deploying, this means you have not configured the Consent Screen for your GCP project.

```
Error: Error creating Client: googleapi: Error 404: Requested entity was not found.
│ 
│   with google_iap_client.project_client,
│   on lb.tf line 62, in resource "google_iap_client" "project_client":
│   62: resource "google_iap_client" "project_client" {
│ 
```