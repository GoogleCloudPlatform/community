---
title: How to deploy Grafana on Cloud Run with Identity-Aware Proxy using Terraform
description: Learn how to deploy Grafana serverless and restrict access to the dashboard.
author: cgrotz,annamuscarella
tags: serverless, identity, proxy, sql
date_published: 2022-01-19
---

Christoph Grotz | Strategic Cloud Engineer | Google

Anna Muscarella | Strategic Cloud Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to deploy Grafana serverless and restrict access to the dashboard. This tutorial is for developers, DevOps engineers, and anyone
interested in deploying serverless applications or restricting access to them.

To use this tutorial, you need basic knowledge of Google Cloud, Grafana, and Terraform, and you need to own a domain and be able to modify its A record.

![Serverless Grafana architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-iap-architecture.png)

## Objectives

  * Run the Terraform script to deploy Grafana on Cloud Run with Cloud SQL as database and Identity-Aware Proxy (IAP) setup.
  * Create a new user for accessing the dashboard.
  * Explore and test the capabilities of Identity-Aware Proxy to restrict access to your Grafana dashboard.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

  * [Cloud Run](https://cloud.google.com/run)
  * [Cloud SQL](https://cloud.google.com/sql)
  * [Cloud Load Balancer](https://cloud.google.com/load-balancing)
  * [Identity-Aware Proxy](https://cloud.google.com/iap)
  * [Secret Manager](https://cloud.google.com/secret-manager)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## How the code for this tutorial works

First, required APIs (including IAM, Cloud Run, Compute Engine, Identity-Aware Proxy, and Cloud SQL) are enabled by the Terraform script. For
details, see the
[`main.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L18).
Enabling the APIs is necessary to allow the usage of the APIs during the deployment in your project.

Grafana requires a database for storing users, roles, data sources, and dashboards. Therefore, a Terraform script creates a Cloud SQL instance. 
For details, see the
[`cloudsql.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/cloudsql.tf#L48).
The password for the database user is placed in Secret Manager for secured access. This tutorial usse a MySQL micro instance because only a small amount of data 
is stored in MySQL.

The Cloud Run container is deployed using the Google Container Registry mirror of the Grafana container image and started. For details, see the
[`main.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L56).
The script also
[passes required environment variables to the container](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L151),
such as information about the database connection and auth proxy. 

To make sure that your Grafana dashboard is useful, a datasource for Cloud Monitoring is provisioned. This tutorial uses the
[Grafanas provisioning mechanism](https://grafana.com/docs/grafana/latest/administration/provisioning/) for that, which discovers data sources and dashboards 
from the disk. Because Cloud Run instances don't have persistent volumes, you can't just place the data source and dashboard file into the filesystem. As a 
workaround, the file is added as a secret to Secret Manager and then mounted to the required location so Grafana can pick up the data source correctly. For 
details, see the
[`main.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L187).
With this, you have mock data in your dashboard. An alternative could be to use
[Cloud Storage FUSE](https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse), which allows you to mount a Cloud Storage bucket into the filesystem,
but this requires modifying the Docker image.

To access your Grafana dashboard, Cloud Load Balancer is configured to service HTTPS traffic from Cloud Run using a serverless network endpoint group (NEG) as  a 
backend service. Identity-Aware Proxy (IAP) is integrated with the Load Balancer backend service, as shown in the
[`lb.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/lb.tf#L50). The client ID and
secret are passed to the Load Balancer configuration. IAP provides headers containing the authorization information to applications secured with it
For more information, see [Securing your app with signed headers](https://cloud.google.com/iap/docs/signed-headers-howto). Grafana provides the
[functionality](https://grafana.com/docs/grafana/latest/auth/auth-proxy/) to receive such header information for authentication. 

### Before you begin

To complete this tutorial, you need a Google Cloud account, a Google Cloud project with billing enabled, and Terraform installed and enabled.

  1. [Create or select a Google Cloud project.](https://console.cloud.google.com/project)
  1. [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
  1. Choose a region to host your project in, ideally one that’s close to you. For information about available regions, see
     [Regions and zones](https://cloud.google.com/compute/docs/regions-zones).
  1. Make sure that you know the domain name where you will host your Grafana dashboard and are able to edit the A record for this domain.

### Configure the OAuth consent screen

Configure an OAuth consent screen for Identity-Aware Proxy. 
  1. Go to GCP Console > Security > Identity-Aware Proxy. If necessary, enable the Identity-Aware proxy when the console requests it.
  2. If you didn’t configure a consent screen before, there will be a red warning message prompting you to configure one. 
  ![Consent missing error message](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-consent-not-configured.png)
  Select internal users, this allows only users that are part of your Cloud Identity organisation to use Grafana, but requires you to have a Cloud Identity organisation. If you want to enable IAP with external identities, you will have to use [GCP Identity Platform](https://cloud.google.com/identity-platform) which we don't cover in this tutorial. 
  3. Click Configure Consent Screen, choose User Type Internal. Add a name and support email addresses and click Create.
  ![Configure consent](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-configure-oauth.png)
  4. Click Save and Continue within the Scopes step
  5. Enter the app name and user support email, then click **Save** and continue until the process is complete.


### Set up your Environment

Next, you’re going to set up the environment in order for the project to deploy.
  1. [Open a new Cloud Shell session.](https://console.cloud.google.com/?cloudshell=true)
  1. *Run* `git clone https://github.com/GoogleCloudPlatform/community.git` to download the sources to your cloud shell.
  1. `cd ./community/tutorials/serverless-grafana-with-iap/code` change directory to the *code* folder.
  1. *Set* required environment variables. Replace [YOUR_DOMAIN] with the domain on which you want to host your Grafana dashboard.
  ```
  export TF_VAR_project_id=$GOOGLE_CLOUD_PROJECT
  export TF_VAR_domain=[YOUR_DOMAIN]
  ```
  1. *Run* `terraform init`


### Execute the Terraform script to create your Grafana Dashboard

  1. *Run* `terraform plan` and confirm that all steps are correct.
  2. *Run* `terraform apply`.
  3. Confirm the command has been executed successfully. You should see the IP address of your Load Balancer printed in the console as in the example output below. This may take up to 15 min. 
  ```
  module.lb-http.google_compute_global_forwarding_rule.https[0]: Creation complete after 11s [id=projects/[YOUR_PROJECT_ID]/global/forwardingRules/tf-cr-lb-https]

  Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

  Outputs:

  external_ip = "[YOUR_EXTERNAL_IP]"
  ```
  4. *Copy* the external_ip from the console outputs. 
  5. *Add* an A record from your domain to this IP address. If you are managing your domain through GCP, you can do this step in Cloud DNS. If not, an A record can be set through your domain registrar.
  6. Wait around 5 - 10 minutes for GCP Load Balancer to perform certificate checks.

### Access your Grafana Dashboard
In order to grant users access to your Grafana instance, you need to grant them the role "IAP-Secured Web App User" for the resource. You can do this with the following gcloud command. You should do this for your user account.
```
gcloud iap web add-iam-policy-binding \
            --resource-type=backend-services \
            --member='user:<your_user_email>' \
            --service='tf-cr-lb-backend-default' \
            --role='roles/iap.httpsResourceAccessor'
```
Afterwards you can open Grafana by visiting [YOUR_DOMAIN] from the browser. Since the database is automatically provisioned your user will only have Viewer permissions in Grafana. If you want to elevate your user to an Admin, you will need to access the MySQL instance and modify the user table entry for your user.

### Test Access your Grafana Dashboard
Open a new [incognito browser window](https://support.google.com/chrome/answer/95464?hl=en&co=GENIE.Platform%3DDesktop) and visit [YOUR_DOMAIN]. You will be forwarded to your configured OAuth consent screen. After login in, you should also have access to Grafana.

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
- If you want to avoid further cost, it's a good idea to delete the resources in the project before deleting the project

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
2.  In the project list, select the project you want to delete and click **Delete**.
3.  In the dialog, type the project ID, and then click **Shut down** to delete the project.


To delete resources only, do the following:

1. *Execute* `terraform destroy` to delete the remaining resources. 



## Troubleshooting

If you see the following error message while deploying, this means you have not configured the Consent Screen for your GCP project.

```
Error: Error creating Client: googleapi: Error 404: Requested entity was not found.
│ 
│   with google_iap_client.project_client,
│   on lb.tf line 79, in resource "google_iap_client" "project_client":
│   79: resource "google_iap_client" "project_client" {
│ 
```
