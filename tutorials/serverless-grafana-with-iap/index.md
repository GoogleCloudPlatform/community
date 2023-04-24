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

  * Run the Terraform script to deploy Grafana on Cloud Run with Cloud SQL as the database and Identity-Aware Proxy (IAP).
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
The password for the database user is placed in Secret Manager for secured access. This tutorial uses a MySQL micro instance because only a small amount of data 
is stored in MySQL.

The Cloud Run container is deployed using the Google Container Registry mirror of the Grafana container image and started. For details, see the
[`main.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L56).
The script also
[passes required environment variables to the container](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L151),
such as information about the database connection and auth proxy. 

To make sure that your Grafana dashboard is useful, a datasource for Cloud Monitoring is provisioned. This tutorial uses the
[Grafana provisioning mechanism](https://grafana.com/docs/grafana/latest/administration/provisioning/), which discovers data sources and dashboards 
from the disk. Because Cloud Run instances don't have persistent volumes, you can't just place the data source and dashboard file into the file system. As a 
workaround, the file is added as a secret to Secret Manager and then mounted to the required location so Grafana can pick up the data source correctly. For 
details, see the
[`main.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/main.tf#L187).
With this, you have mock data in your dashboard. An alternative is to use
[Cloud Storage FUSE](https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse), which allows you to mount a Cloud Storage bucket into the file 
system, but this requires modifying the Docker image.

To access your Grafana dashboard, Cloud Load Balancer is configured to service HTTPS traffic from Cloud Run using a serverless network endpoint group (NEG) as  a 
backend service. Identity-Aware Proxy (IAP) is integrated with the Load Balancer backend service, as shown in the
[`lb.tf` Terraform script](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-grafana-with-iap/code/lb.tf#L50). The client ID and
secret are passed to the Load Balancer configuration. IAP provides headers containing the authorization information to applications secured with it.
For more information, see [Securing your app with signed headers](https://cloud.google.com/iap/docs/signed-headers-howto). Grafana provides the
[functionality](https://grafana.com/docs/grafana/latest/auth/auth-proxy/) to receive such header information for authentication. 

## Before you begin

To complete this tutorial, you need a Google Cloud account, a Google Cloud project with billing enabled, and Terraform installed and enabled.

1.  [Create or select a Google Cloud project.](https://console.cloud.google.com/project)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  Choose a region to host your project in, ideally one that’s close to you. For information about available regions, see
    [Regions and zones](https://cloud.google.com/compute/docs/regions-zones).
1.  Make sure that you know the domain name where you will host your Grafana dashboard, and make sure that you are able to edit the A record for this domain.

## Configure the OAuth consent screen

In this section, you configure an OAuth [consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent) for Identity-Aware Proxy. 

1.  Go to the [Identity-Aware Proxy page](https://console.cloud.google.com/security/iap) in the Cloud Console.

    If you are prompted to enable the IAP API, then do so.

    If you haven't already configured a consent screen, then you are prompted to do so:
 
    ![Consent missing error message](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/iap-consent-not-configured.png)
    
1.  Click the **Configure Consent Screen** button, choose **Internal** under **User type**, and click **Create**.

    You select **Internal** to allow only users that are part of your Cloud Identity organization to use Grafana. This option requires you to have a Cloud 
    Identity organization. If you want to enable IAP with external identities, you need to use
    [Google Cloud Identity Platform](https://cloud.google.com/identity-platform), which is not covered in this tutorial.
 
1.  Click **Save and continue** within the **Scopes** step

1.  Enter the app name and user support email address, and then click **Save and continue** until the process is complete.

### Troubleshooting

If you see the following error message while deploying, this means you have not configured the consent screen for your Google Cloud project:

    Error: Error creating Client: googleapi: Error 404: Requested entity was not found.
    │ 
    │   with google_iap_client.project_client,
    │   on lb.tf line 79, in resource "google_iap_client" "project_client":
    │   79: resource "google_iap_client" "project_client" {
    │ 

## Set up your environment

In this section, you set up the environment in order for the project to deploy.

1.  [Open a new Cloud Shell session.](https://console.cloud.google.com/?cloudshell=true)
1.  Download the source code for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/community.git
        
1.  Go to the `code` folder:

        cd ./community/tutorials/serverless-grafana-with-iap/code

1.  Set the required environment variables:

        export TF_VAR_project_id=$GOOGLE_CLOUD_PROJECT
        export TF_VAR_domain=[YOUR_DOMAIN]

     Replace `[YOUR_DOMAIN]` with the domain on which to host your Grafana dashboard.
     
1.  Initialize Terraform:

        terraform init

## Run the Terraform script to create your Grafana dashboard

1.  Create an execution plan and verify all of the steps:

        terraform plan

1.  Apply the changes:

        terraform apply
        
    The deployment may take up to 15 minutes.

1.  Confirm that the deployment has been executed successfully.

    You should see the IP address of your load balancer printed in the console as in this example:
    
        module.lb-http.google_compute_global_forwarding_rule.https[0]: Creation complete after 11s [id=projects/[YOUR_PROJECT_ID]/global/forwardingRules/tf-cr-lb-https]

        Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

        Outputs:

        external_ip = "[YOUR_EXTERNAL_IP]"
  
1.  Copy the value of `external_ip`.

1.  Add an A record from your domain to this IP address.

    If you are managing your domain through Google Cloud, then you can do this step in Cloud DNS. If not, an A record can be set through your domain registrar.
    
1.  Wait 10 minutes for Google Cloud Load Balancer to perform certificate checks.

## Access your Grafana Dashboard

To grant users access to your Grafana instance, you need to grant them the role **IAP-Secured Web App User** for the resource.

Grant your user account the necessary role with the following command:

    gcloud iap web add-iam-policy-binding \
      --resource-type=backend-services \
      --member='user:[YOUR_USER_ACCOUNT_EMAIL_ADDRESS]' \
      --service='tf-cr-lb-backend-default' \
      --role='roles/iap.httpsResourceAccessor'

You can open Grafana by visiting `[YOUR_DOMAIN]` from the browser. Because the database is automatically provisioned, your user will only have **Viewer**
permissions in Grafana. If you want to elevate your user to an Admin, you need to access the MySQL instance and modify the user table entry for your user.

## Test access your Grafana dashboard

Open a new [Incognito browser window](https://support.google.com/chrome/answer/95464) and visit `[YOUR_DOMAIN]`. You will be forwarded to your configured OAuth
consent screen. After you log in, you should also have access to Grafana.

## Conclusion

You now have a serverless deployment of Grafana up and running, connected with Google Cloud Monitoring and secured using Identity-Aware Proxy. You can now access
and log in to Grafana using your browser and accessing your domain. There should already be a dashboard available monitoring Google Cloud Load Balancing for you.
This provides you with reduced worries around properly hosting your Grafana dashboards, while also providing a very low cost solution to hosting Grafana. If you
want to use the alerts feature from Grafana, consider keeping some [CPU allocated](https://cloud.google.com/run/docs/configuring/cpu-allocation); otherwise 
alerts might not be triggered. 

![Grafana dashboard screenshot](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-dashboard-screenshot.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can use Terraform to delete most of the resources. If you 
created a new project for deploying the resources, you can also delete the entire project.

To delete resources using Terraform, run the following command:

    terraform destroy

To delete the project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## Update regarding changes due to Grafana 9.2

There have been configuration behavior changes in Grafana 9.2 that affect this tutorial. For details, see
[the discussion in this GitHub issue](https://github.com/GoogleCloudPlatform/community/pull/2288#issuecomment-1469728639).
Because we recommend that you verify the proper signing of the token, we removed the proxy config option.
This could mean that if you are updating from the previous configuration to the updated configuration in
this tutorial, the provider of the users in your `user_auth` will change, and permissions and roles might
not be carried over.
