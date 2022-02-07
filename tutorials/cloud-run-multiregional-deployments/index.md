---
title: How to deploy Multiregional application on Cloud Run with Terraform
description: Learn how to deploy a highly available, regionally resiliant serverless application with Cloud Run and Terraform.
author: timhiatt
tags: serverless, cloud run, containers, app, high availability
date_published: 2022-02-07
---

Tim Hiatt | Cloud Consultant | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>
This tutorial demonstrates how you can easily utilize Terraform to deploy a multiregional containerized serverless application on Google Cloud with Cloud Run.

The target audience for this tutorial is Developers of all levels as well as DevOps engineers and serverless enthusiasts with a basic understanding of cloud principles.

To complete this tutorial, you require a basic working knowledge of Google Cloud, Containers, and Terraform. You will also require own a domain name for which you can modify the DNS records and a VPN that allows you to emulate your browsers country of origin.

![Multiregional Serverless Cloud Run Architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-iap-architecture.png)

## Objectives

- Examine and understand the core components of the Terraform scripts.
- Run the Terraform script to deploy a single containerized application across a group of Cloud Run services in multiple Cloud Regions behind a External Global L7 Cloud Load Balancer.
- Modify the deployment scripts to add additional regions to your multiregional deployment.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- [Cloud Run](https://cloud.google.com/run)
- [Cloud Load Balancer](https://cloud.google.com/load-balancing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## How the code for this tutorial works

The entirety of this deployment is executed through terraform scripts.

Initially the required Google Cloud APIs (Cloud Run & Compute Engine) are iteratively enabled within your specified Google Cloud project via the [`google_project_service`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_service) Terraform provider [(`main.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/main.tf#L25). The enabling of these APIs is a dependancy to the the Terraform execution steps that follow.

A new Service Account is created [(`main.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/main.tf#L32) as part of the deployment. This service account is assigned the role `roles/monitoring.viewer` as read only monitoring access within the Google Cloud Console and API [(`main.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/main.tf#L38).

In this tutorial we are deploying a containerized application. For example purposes we are using the
[`GoogleCloudPlatform/cloud-run-hello`](https://github.com/GoogleCloudPlatform/cloud-run-hello) sample application. It is a publically available container image mirrored in the Google Container Registry [`gcr.io/cloudrun/hello`](https://gcr.io/cloudrun/hello). This sample container is perfect for our purposes as when up and running it visually reports back the following information:

1. The Cloud Run container deployment revision.
1. The Cloud Run service name.
1. The Cloud Run deployment region.
1. The Google Cloud project name in which the container is deployed.

We can therefore use this container image to easily test the concept of deploying multiregional deploymnets behind a global L7 load balancer.

This container image is deployed as a service within Google Cloud Run using the [`google_cloud_run_service`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_service) terraform provider. In order to achieve the goal of this tutorial and make this service multiregional a new Cloud Run Service is deployed via the terraform scripts [(`cloud-run.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/cloud-run.tf#L17) in each region in which we wish to make it available. This operation is completed using the Terraform [`for_each`](https://www.terraform.io/language/meta-arguments/for_each) syntax to loop over an array of Cloud Regions provided to the terrafrom scripts via way of the `regions` variable [`variables.tf`(defaults here)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/variables.tf#L20).

By default our Cloud Run services are configured to only be accessible by authorized users. However for this tutorial we would like to make the services publically available. Therefore our Terraform scripts [(`cloud-run.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/cloud-run.tf#L64) bind the Cloud Run IAM role [`roles/run.invoker`](https://cloud.google.com/run/docs/reference/iam/roles#standard-roles) to the membership [`allUsers`](https://cloud.google.com/iam/docs/overview#all-users) and then apply this policy to each of our Cloud Run services [(`cloud-run.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/cloud-run.tf#L73)

Each of the above Cloud Run services is also configured to only accept incomming network traffic from sources that are internal to our Google Cloud project VPC or from an associated Cloud Load Balancer. This is configured via the Cloud Run metadata & YAML annotation: [`run.googleapis.com/ingress`](https://cloud.google.com/run/docs/securing/ingress#setting_ingress) [(`cloud-run.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/cloud-run.tf#L27). Therefore in order to make our application accessible our terraform script deploys a Cloud Load Balancer.

The Cloud Load Balancer is finally configured with a default backend and a collection of network endpoint groups (NEG). Each NEG represents one of our previously deployed Cloud Run Services, again one for each deployment region [(`lb.tf` code reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/lb.tf#L18).

When fully deployed a user can use a web enabled device to hit your external Global Load Balancer and you they will recieve a response from our example application. The application will display the Cloud Regions in which the container they have been routed too is running. If the deployment is configured correctly, with multiple regions the Global Load Balancer will route your users web request automatically to the [closest, healthy](https://cloud.google.com/load-balancing/docs/https) Cloud Run Service that is running your application.

You should be able to easily add additional regions to your deployment variables to increase your global coverage and high availability.

## Before you begin

To complete this tutorial, you need a Google Cloud account, a Google Cloud project with billing enabled, and Terraform installed and enabled.

1.  [Create or select a Google Cloud project.](https://console.cloud.google.com/project)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  Choose a region to host your project in, ideally one that’s close to you. For information about available regions, see
    [Regions and zones](https://cloud.google.com/compute/docs/regions-zones).
1.  Make sure that you know the domain name where you will host your sample application, and make sure that you are able to edit the DNS A records for this domain.

## Set up your environment

In this section, you set up the environment in order for the project to deploy.

1.  [Open a new Cloud Shell session.](https://console.cloud.google.com/?cloudshell=true)
1.  Download the source code for this tutorial:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the `code` folder:

        cd ./community/tutorials/cloud-run-multiregional-deployments/code

1.  Set the required environment variables:

        export TF_VAR_project_id=$GOOGLE_CLOUD_PROJECT
        export TF_VAR_domain=[YOUR_DOMAIN]

    Replace `[YOUR_DOMAIN]` with the domain on which to host our sample application.

1.  Initialize Terraform:

        terraform init

## Run the Terraform script to create your multiregional application deployment

1.  Create an execution plan and verify all of the steps:

        terraform plan

1.  Apply the changes:

        terraform apply

    The deployment may take up to 15 minutes.

1.  Confirm that the deployment has been executed successfully.

    You should see the IP address of your load balancer printed in the console as in this example:

        module.lb-http.google_compute_global_forwarding_rule.https[0]: Creation complete after 11s [id=projects/[YOUR_PROJECT_ID]/global/forwardingRules/tf-cr-lb-https]

        Apply complete! Resources: 20 added, 0 changed, 0 destroyed.

        Outputs:

        external_ip = "[YOUR_EXTERNAL_IP]"

1.  Copy the value of `external_ip`.

1.  Add an A record from your domain to this IP address.

    If you are managing your domain through Google Cloud, then you can do this step in Cloud DNS. If not, an A record can be set through your domain registrar.

1.  Wait 10 to 15 minutes for Google Cloud Load Balancer to perform certificate checks.

## Access our sample application

You can open our sample aplpication by visiting `[YOUR_DOMAIN]` from a web browser. When the application loads you should be greated with a wealth of information about our applications deployment including the [Cloud Region](https://cloud.google.com/compute/docs/regions-zones) in our sample application is responding to your request from.

## Test the multiregional deployment (With VPN)

In the previous step you viewed our sample application. The site showed the Cloud Region in which your application was responding from.

The Global External Load Balancer automatically routes your browsers request to the nearest Cloud Region in which your application is hosted. To test thi visit your `[YOUR_DOMAIN]` again and make note of the deployment region; for example (`europe-west1` or `us-central1` or `australia-southeast1`).

Then, if you have the ability, use your VPN on your machine to set your network location to a completely different region of the world far away from the deployment region you noted previously.

Sample Ideas:

- If you noted down a `europe-west1` based deployment set your VPN to somewhere located in the US.
- If you noted down a `us-central1` based deployment set your VPN to somewhere located in Europe.
- If you noted down a `australia-southeast1` based deployment set your VPN to somewhere located in Europe.

When the VPN has updated your network location. Open up a new browser tab and revisit `[YOUR_DOMAIN]`. Your application will respond again, however this time the Cloud Region in which your application is hosted should have changed to show your broswers request is being routed to the New nearest Cloud Region.

## Expand your multiregional deployment

To show the ease of deploying to additional Cloud Regions with this IaC Terraform setup lets add several more cloud reigons to the application architecture with a very simple modification.

1.  From within your existing Cloud Shell session select the "Open Editor" button to open the `Cloud Shell Editior` and wait for the Editior UI to be provisioned (1-3 minutes).

1.  From within the Cloud Shell Editor UI navigate to the `community/tutorials/cloud-run-multiregional-deployments/code` directory.

1.  Open the `variables.tf` file [(Reference)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/variables.tf#L20).

1.  Locate the variable `regions` [(Line 20)](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/variables.tf#L20). Then comment out the defaults on [line 23](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/variables.tf#L23) by adding a `#` before the work `default`. Finally remove the `#` before the word `default` on [line 25](https://github.com/timbohiatt/community/blob/master/tutorials/cloud-run-multiregional-deployments/code/variables.tf#L25) to uncomment the extended defaults. This will expand the deployment regions from 3 Global Cloud Regions to 7 Global Cloud Regions. Save the `variables.tf` file.

1.  Select the `Open Terminal` button to return to the shell and confirm you are still currently in the `community/tutorials/cloud-run-multiregional-deployments/code` directory.

1.  To update your architecture re-create an execution plan and verify all of the steps, which should include deployment plans for your additional 4 Cloud Regions:

        terraform plan

1.  Apply the new changes changes:

        terraform apply

    The deployment again, may take up to 15 minutes.

1.  Confirm that the deployment has been executed & updated successfully.

    You should see the IP address of your load balancer printed in the console as in this example:

        module.lb-http.google_compute_backend_service.default["default"]: Modifications complete after 11s [id=projects/YOUR_PROJECT_ID]/global/backendServices/tf-cr-lb-backend-default]

        Apply complete! Resources: 12 added, 1 changed, 0 destroyed.

        Outputs:

        external_ip = "[YOUR_EXTERNAL_IP]"

1.  Revisit the above section `Expand your multiregional deployment` however this time try setting your VPN to additional locations including Canada, Asia, The Nordics and South America and see the results. See if you can hit all of the deployed Cloud Regions listed in your variables files. Additionally try for yourself add and deploy to additional Cloud Regions where [Cloud Run is available](https://cloud.google.com/run/docs/locations).

## Conclusion

You now have a serverless deployment of a containerized application running in Google Cloud Run.

Thanks to the use of the Global External Load Balancer a strong user experience is generated by ensuring the automatic routing of user requests to the nearest enabled Cloud Region resulting in timely low latency network responses.

Your application is scalable and highly available as it is deployed in multiple Cloud Regions and is therefore protected from regional outages and network disruptions.

In addition, Google Cloud Run only charges you for the resources you actually use. Therefore deployment to multiple Regions comes at no cost when your services are not responding to user requests. Allowing you to provide High Availability at no additional cost.

Finally we covered how you can easily modify the included example code to update your Infrastructure through code to scale your multiregional services to even more Cloud Regions in only a few minutes.

![Cloud Load Balancer Request Flow screenshot](https://storage.googleapis.com/gcp-community/tutorials/serverless-grafana-with-iap/grafana-dashboard-screenshot.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can use Terraform to delete most of the resources. If you
created a new project for deploying the resources, you can also delete the entire project.

To delete resources using Terraform, run the following command:

    terraform destroy

To delete the project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
