---
title: Allow third-party services to access specific backend resources in a Shared VPC network
description: Learn how to provision a serverless function to access a backend resource in a Shared VPC network using Terraform scripts.
author: skalolazka,gasparch,nplanner
tags: shared VPC, Cloud Run, Serverless VPC Access connector
date_published: 2021-10-04
---

Natalia Strelkova | Infrastructure Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document describes how to use Terraform to configure Cloud Run and a Serverless VPC Access connector to allow third-party services access to specific 
backend resources in a Shared VPC network. This approach allows you to give third-party services outside of your network access to specific backend resources 
instead of allowing them to access the whole VPC network. This solution shows an example use case in which a Cloud Run service is serving as a proxy to allow 
access to some private backend. The Cloud Run service can be used to add context-specific information to the third-party services. 

Typical uses cases for this solution: 

* Webhooks 
* Infrequent access from third-party services 

This example uses Cloud Run, but you can take similar steps to configure other serverless services, such as App Engine or Cloud Functions.

This document is for network administrators, security architects, app developers, and cloud operations professionals. This document assumes that you are
familiar with setting up networking on Google Cloud and are familiar with using the Cloud Console, [Terraform](https://cloud.google.com/docs/terraform), and 
Cloud Run.

## Architecture 

The following diagram summarizes the architecture that you create in this tutorial:

![Architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-backend-access-in-shared-vpc/image1.png)

This tutorial uses a second Google Cloud project to simulate your private (or on-premises) network with which the shared VPC network is shared. 

## Objectives

* Create a Serverless VPC Access connector in the shared VPC host project
* Provision an example Cloud Run service
* Create and configure a security policy for Cloud Armor
* Provision an HTTP load balancer

## Costs

This tutorial uses the following billable components of Google Cloud:

* [Compute Engine](https://cloud.google.com/compute/pricing)
* [Cloud Run](https://cloud.google.com/run/pricing)
* [HTTP(S) Load Balancer with Serverless NEGs](https://cloud.google.com/vpc/network-pricing)
* [Serverless VPC Access connector](https://cloud.google.com/vpc/pricing)

To generate a cost estimate based on your projected usage, use the [pricing calculator](https://cloud.google.com/products/calculator).

## Before you begin

Because this tutorial requires two Google Cloud projects, complete these steps to create and enable billing and APIs for _two_ projects. The tutorial refers to 
these projects as `your-gcp-host-project` and `your-gcp-service-project`.

1.  In the [Cloud Console](https://console.cloud.google.com/), on the project selector page, select or create a Google Cloud project.

    If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting an existing project. After you finish these
    steps, you can delete the project, removing all resources associated with the project.

1.  [Go to project selector](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  In the Cloud Console, [activate Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

    At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session starts and displays a command-line prompt. Cloud 
    Shell is a shell environment with the Cloud SDK already installed, including the [gcloud](https://cloud.google.com/sdk/gcloud) command-line tool, and with 
    values already set for your current project. It can take a few seconds for the session to initialize.

1.  Set up your Terraform environment for Google Cloud. For details, see
    [Getting started with Terraform on Google Cloud](https://cloud.google.com/community/tutorials/getting-started-on-gcp-with-terraform).
    
    The code that accompanies this tutorial has been tested using Terraform version 1.0.2.

1.  Ensure that you have a [service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) with sufficient permissions to deploy the 
    resources used in this tutorial.

1.  Enable the following APIs in the `your-gcp-service-project` project:

    * Compute Engine API
    * Serverless VPC Access API
    * Cloud Build API
    * API Gateway API
    * Service Control API
    * Service Management API
    * Cloud Deployment Manager V2 API
    * Cloud Run API

            gcloud services enable \
              compute.googleapis.com  \
              vpcaccess.googleapis.com \
              cloudbuild.googleapis.com \
              apigateway.googleapis.com  \
              servicecontrol.googleapis.com \
              servicemanagement.googleapis.com \
              deploymentmanager.googleapis.com \
              run.googleapis.com

1.  Enable the following APIs in the `your-gcp-host-project` project:

    * Compute Engine API

            gcloud services enable compute.googleapis.com 

1.  Clone the repository that contains the tutorial's code:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial code directory:

        cd community/tutorials/serverless-backend-access-in-shared-vpc/code

## Summary of the tutorial code

This section gives an overview of
[the code that accompanies the tutorial](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/serverless-backend-access-in-shared-vpc/code).

* The main module for the solution components is in the `code/modules/serverless_endpoint/` folder. It creates the necessary serverless components and organizes
  access between them.
* Variables and data are defined in the `code/variables.tf` and `code/main.tf` files.
* The `code/networking.tf` file sets up a Shared VPC network.
* The `example_server.tf` file sets up an example webserver.
* The IP address of the webserver is hardcoded in `server/index.js` and is used in Terraform variables.

## Set up, deploy, and test the architecture

1.  Run the following command to obtain the default credentials for your project:

        gcloud auth application-default login

    _If you aren't using Cloud Shell_, this tutorial uses the default application credentials for Terraform authentication to Google Cloud. 

1.  (optional) Create a `terraform.tfvars` file with the variable values for your environment.

    Example content:

        cloud_run_project = "your-gcp-host-project"
        shared_vpc_host_project = "your-gcp-service-project"
        source_ip_range_for_security_policy = ["0.0.0.0/0"]

    Main variables used:

    - `cloud_run_project`: the project where the load balancer and Cloud Run are deployed.
    - `shared_vpc_host_project`: the project to host the shared VPC network and to deploy the Serverless VPC Access connector and an example server.
    - `source_ip_range_for_security_policy`: array of Cloud Armor security policy allowed IP address ranges. Put your IP address as an array here, such as
      `["10.0.0.0"]`.
      
    See the `variables.tf` and `modules/serverless_endpoint/variables.tf` files for other variables that have default values.

1.  Run Terraform to deploy the architecture:

        terraform init
        terraform plan
        terraform apply

    The resources are ready after a few minutes.

1.  Check the output of `terraform apply` and get the IP address of the web server.

1.  Test the web server by going to the IP address, `http://[IP_ADDRESS]/` or `https://[IP_ADDRESS]/ping`.

1.  If you supplied the variable `cloud_run_invoker` in the `modules/serverless_endpoint/variables.tf` file with your user, then you can try to access
    the IP address with authentication:

        curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" http://[IP_ADDRESS]/ping

## Clean up by destroying the resources that you created

To destroy all of the resources that you created, run the following command:

    terraform destroy

Destroying all of the resources might require two steps, because the `destroy` process because of the order of the dependencies. Specifically, destroying the
`google_compute_shared_vpc_host_project` resource might require a second run of the `destroy` command. If you get an error when running the command the first 
time, run `terraform destroy` again. If you get the error again, you might need to detach the shared VPC host project manually.

## What's next

* [Additional Google Cloud Terraform examples](https://github.com/GoogleCloudPlatform/terraform-google-examples)
* [Google Cloud load balancer documentation](https://cloud.google.com/compute/docs/load-balancing)
* [SSL certificates for Google Cloud load balancers](https://cloud.google.com/load-balancing/docs/ssl-certificates)
