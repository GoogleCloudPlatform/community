---
title: Allowing third party services to access specific backend resources in a Shared VPC
description: Replace with a description of your tutorial, focusing on what the reader will learn.
author: skalolazka,github-username-for-other-author
tags: replace, with, tags, not, in, title, or, description
date_published: 2021-09-01
---

Norman Planner | Community Editor | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>


<p style="color: red; font-weight: bold">>>>>>  gd2md-html alert:  ERRORs: 0; WARNINGs: 0; ALERTS: 1.</p>
<ul style="color: red; font-weight: bold"><li>See top comment block for details on ERRORs and WARNINGs. <li>In the converted Markdown or HTML, search for inline alerts that start with >>>>>  gd2md-html alert:  for specific instances that need correction.</ul>

<p style="color: red; font-weight: bold">Links to alert messages:</p><a href="#gdcalert1">alert1</a>

<p style="color: red; font-weight: bold">>>>>> PLEASE check and correct alert issues and delete this message and the inline alerts.<hr></p>


This tutorial describes how to configure Cloud Run and a Serverless Connector to allow third party services access to specific backend resources in a Shared VPC via Terraform. This approach allows you to give third party services outside of your network access to specific backend resources instead of allowing them to access the whole VPC. This solution shows an example use case where the cloud run service is proxying access to some private backend. The Cloud Run Service can be used to add context specific information to the third party services e.g. TBC

This document is for network administrators, security architects, app developers and cloud operations professionals.

Typical uses cases are: 



* Webhooks 
* Seldom access from third party services 

In this example we are using Cloud Run, but you can take similar steps to configure other serverless services like App Engine or Cloud Functions.

This tutorial assumes that you have basic familiarity using Google Cloud Console, Terraform, Cloud Run and setting up networking on Google Cloud. 

<h3>Architecture using Cloud Run </h3>


The following diagram summarizes the architecture that you create in this tutorial.



<p id="gdcalert1" ><span style="color: red; font-weight: bold">>>>>>  gd2md-html alert: inline image link here (to images/image1.png). Store image on your image server and adjust path/filename/extension if necessary. </span><br>(<a href="#">Back to top</a>)(<a href="#gdcalert2">Next alert</a>)<br><span style="color: red; font-weight: bold">>>>>> </span></p>


![alt_text](images/image1.png "image_tooltip")


<h3>Notes:</h3>


This tutorial uses a second Google Cloud project to simulate your private (or on-premises) network with which the shared VPC will be shared. 

<h3>Objectives:</h3>




* Create a Serverless Connector in the shared VPC host project
* Provision an example Cloud Run service
* Create and configure a security policy for Cloud Armor
* Provision an HTTP load balancer

<h3>Costs:</h3>


This tutorial uses the following billable components of Google Cloud:



* [Compute Engine](https://cloud.google.com/compute/pricing)
* <span style="text-decoration:underline;">Cloud Run</span>
* [HTTP(S) Load Balancer with Serverless NEGs](https://cloud.google.com/vpc/network-pricing)
* [Serverless VPC Access Connector](https://cloud.google.com/vpc/pricing)

To generate a cost estimate based on your projected usage, use the [pricing calculator](https://cloud.google.com/products/calculator).



<h3>Before you begin:</h3>


Because this tutorial requires two Google Cloud projects, complete these steps to create and enable billing and APIs for _two_ projects. The tutorial refers to these projects as **<code><em>your-gcp-host-project </em></code></strong> and <strong><code><em>your-gcp-service-project</em></code></strong>.



1. In the Google Cloud Console, on the project selector page, select or create a Google Cloud project. \
**Note**: If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting an existing project. After you finish these steps, you can delete the project, removing all resources associated with the project.
2. [Go to project selector](https://console.cloud.google.com/projectselector2/home/dashboard)
3. Make sure that billing is enabled for your Cloud project. [Learn how to confirm that billing is enabled for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
4. In the Cloud Console, activate Cloud Shell. \
[Activate Cloud Shell \
](https://console.cloud.google.com/?cloudshell=true)At the bottom of the Cloud Console, a [Cloud Shell](https://cloud.google.com/shell/docs/features) session starts and displays a command-line prompt. Cloud Shell is a shell environment with the Cloud SDK already installed, including the [gcloud](https://cloud.google.com/sdk/gcloud) command-line tool, and with values already set for your current project. It can take a few seconds for the session to initialize.

This guide assumes that you are familiar with [Terraform](https://cloud.google.com/docs/terraform). 



* See [Getting started with Terraform on Google Cloud](https://cloud.google.com/community/tutorials/getting-started-on-gcp-with-terraform) to set up your Terraform environment for Google Cloud.
* Ensure that you have a [service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) with sufficient permissions to deploy the resources used in this tutorial.

<h3>Authentication - calls from the unauthenticated 3rd party server (allUsers)</h3>


<h3>Preparing your environment:</h3>


1. Enable the following APIs on **<code><em>your-gcp-service-project</em></code></strong>



* Compute Engine API
* Serverless VPC Access API
* Cloud Build API
* API Gateway API
* Service Control API
* Service Management API
* Cloud Deployment Manager V2 API
* Cloud Run API

        ```
gcloud services enable \
compute.googleapis.com  \
vpcaccess.googleapis.com \
cloudbuild.googleapis.com \
apigateway.googleapis.com  \
servicecontrol.googleapis.com \
servicemanagement.googleapis.com \
deploymentmanager.googleapis.com \
run.googleapis.com
```



2. Enable the following APIs on **_your-gcp-host-project_**



* Compute Engine API

        ```
gcloud services enable compute.googleapis.com 
```



<h3>**Folder structure**</h3>




* The main module for the solution components is in the** <code>modules/serverless_endpoint/</code></strong> folder. It creates the necessary serverless components and organizes access between them.
* In<strong> <code>variables.tf</code> </strong>and<strong> <code>main.tf</code> </strong>the<strong> </strong>variables, locals and data are defined.
* Other files are to create an example to be able to test the setup - the file <strong><code>networking.tf</code></strong> sets up a Shared VPC,<strong> <code>example_server.tf</code> </strong>runs an example webserver.

<h3>Note: The IP of the webserver is hardcoded in server/index.js and is used in Terraform variables.</h3>


<h3>**Quickstart: **</h3>




1. Open [Cloud Shell](https://console.cloud.google.com/cloudshell)
2. Clone the `terraform-google-examples` repository:

    ```
git clone https://github.com/GoogleCloudPlatform/community.git

```



3. Go to the `terraform-google-examples` directory:


```
cd community/tutorials/serverless-backend-access-in-shared-vpc/
```



    4. If you aren't using Cloud Shell, this tutorial uses the default application credentials for Terraform authentication to Google Cloud. Run the following command first to obtain the default credentials for your project.


```
gcloud auth application-default login
```



    5. (optional) Change variable values in variables.tf for your environment.


    6. Run Terraform to deploy architecture:


```
terraform init
terraform plan
terraform apply
```


The resources are ready after a few minutes.

Before the terraform code will be applied you need to plug in variables specific to your environment. 


```
variable "cloud_run_project"
#your-gcp-service-project where GCLB + Cloud Run are deployed
```



```
variable "shared_vpc_host_project"
# your-gcp-host-project to host the shared VPC and to deploy the serverless connector and an example server
```



```
variable "source_ip_range_for_security_policy"
#Array of Cloud Armor security policy allowed IP ranges (put your IP as an array here e.g. ["10.0.0.0"])
```


7. Check the output of terraform apply to test if the web server is responding 

Note: it will need some time that the IP address will be propagated and you can access the web server


    8. Delete the Cloud resources provisioned by Terraform:


```
terraform destroy
```


<h3>What's next</h3>




* _[Additional examples in the terraform-google-examples repository](https://github.com/GoogleCloudPlatform/terraform-google-examples)._
* _[Learn more about load balancing on Google Cloud](https://cloud.google.com/compute/docs/load-balancing)._
* _[How to setup SSL certificates on GCLB](https://cloud.google.com/load-balancing/docs/ssl-certificates)  _
* Try out other Google Cloud Platform features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).