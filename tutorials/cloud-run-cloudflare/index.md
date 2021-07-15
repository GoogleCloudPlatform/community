---
title: Set up a load balancer for Cloud Run using Google Cloud and connect using Cloudflare
description: Learn how to set up a load balancer for Cloud Run applications and connect a custom domain.
author: eblaauw
tags: cloudflare, cloudrun
date_published: 2021-7-20
---

Edzo Blaauw | Cloud & Data Engineer | talabat 

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial will show you how you can create a Load Balancer connected to Cloud Run using a custom domain in Cloudflare. It will also show you how to setup Cloudflare. You need some experience on how to set up a Cloud Run application. In this tutorial I will not show you how to depkoy a Cloud Run application.

We will use the Google Cloud Platform UI. We will not use the command line in this tutorial.

## Objectives

*   Create a Load Balancer on Google Cloud
*   Connect the Load Balancer to Cloud Run
*   Connect a custom domain using Cloudflare to the Load Balancer
*   Verify success of the job.

## Costs

*   [Cloud Run](https://cloud.google.com/run)
*   [Cloud Load Balancing](https://cloud.google.com/load-balancing)

## Before you begin

1.  Connect a domain to Cloudflare
1.  Run a [Cloud Run application pn Google Cloud](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/python)

## Tutorial

### Set up a VPC and VPC connector

We want our custom domain to talk with the Load Balancer. We do not want the domain to talk with the Cloud Run app directly. For that, we create a new VPC connector. Create a new connector by going to [Serverless VPC access](https://console.cloud.google.com/networking/connectors/list) and click on 'Create Connector'.

In this tutorial, we will set the Region to europe-west1 and we will not create a new VPC network, so we will select the 'default' VPC network. You will need to create a custom subnet by clicking on Custom IP Range. Enter `10.8.0.0` in the IP Range field. After that, click Create.

![VPC Connector setup][state_machine_diagram]

[vpc_connector_setup]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/vpc_connector_setup.png

### Set up a Cloud Run container
Head to the [Google Cloud Console](https://console.cloud.google.com) and create a Cloud Run service. Enter the Service name and Region. You can use your own application name for this. After that, click next.

Click on "Deploy one revision from an existing container image" and enter your contaienr image URL. If you do not have an Docker image yet, you can use the default Docker image, provided by Google Cloud (`us-docker.pkg.dev/cloudrun/container/hello`).

Following that, click on Advanced Settings.

Go to the tab 'Container' and connect your newly created VPC Connector named `gcp-demo-connector` and click on Route all traffic through the VPC connector.

![Cloud Run Setup][cloud_run_setup1]

[cloud_run_setup1]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/cloud_run_setup1.png

In the third step of the service configuration, you want to change the ingress to `Allow internal traffic and traffic from Cloud Load Balancing`. This makes sure that _only requests will be accepted coming from the Load Balancer and VPC_. Click Allow unauthenticated invocations and click on create.

### Set up a Cloud Load Balancer

#### Set up the right load balancer type

Now that we have set up the Cloud Run application, we can go ahead and set up the Load Balancer. Open the [Load Balancing](https://console.cloud.google.com/net-services/loadbalancing/loadBalancers/list) page in the Google Cloud Platform, and create a new load Balancer. It will ask you for the type of load balancer, so select HTTP(S) Load Balancer. After that you want to choose the option "From Internet to my VMs" when it's asking for the load balance type traffic.

#### Create a backend

You will see 4 tabs on the side. It will start with an option to select the backend configuration. Click on the drop down and create a new backend service. You can name it as you like. For backend type, select Serverless network endpoint group. This is called a NEG. You want to use the HTTPS protocol and a timeout of 30 seconds. 
Below that you will see a card with New backend. Click on create a new servless network group. Name it as you like but select the same region as we created the VPC Connector in, so europe-west1. 

![Serverless NEG Setup][serverless_neg_setup]

[serverless_neg_setup]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/serverless_neg_setup.png

After we createad a serverless NEG, you can save the backend service.

![Backend service Setup][backend_service]

[backend_service]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/backend_service.png

#### Create a frontend

Create a new frontend IP and port by entering a name. The first frontend should be HTTP and can have Premium network tier. We want to use a fixed IP address for both HTTP and HTTPS, so create a new IP address by clicking on the IP address dropdown and create a new IP address. Name it as you like. Leave the port at port 80. 

Create one more frontend but use the protcol 'HTTPS'. Select the new IP address you just created and create a new certificate. This new certificate can be a Google managed certificate, but make sure to add the domain you want to use.

![Certificate][certificate]
[certificate]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/certificate.png

You have set up both HTTP and HTTPS now. It should look like the image below.

![Load balancer setup summary][summary]
[summary]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/summary.png


Wait a 10 to 20 minutes until the Load Balancer is set up.

#### Test the load balancer

Go to your new IP address and see if you will see a page that shows you the expected webpage, or the default message of the standard docker image "It's running".

![Website working][website_working]
[website_working]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/running.png

#### Set up Cloudflare

To connect Cloudflare to this load balancer, log in to your Cloudflare Dashboard and create a new DNS record. Create a new A record by specifying the name (subdomain) and enter the new IP address of the load balancer. *Make sure to select DNS only*. After 24 hours, you can change to this to Cloudflare. If you do not set it to DNS Only, Google Cloud cannot verify and validate the HTTPS certificate.


![Cloudflare setup][cloudflare_setup]
[cloudflare_setup]: https://storage.googleapis.com/gcp-community/tutorials/cloud-run-cloudflare/cloudflare_setup.png

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

