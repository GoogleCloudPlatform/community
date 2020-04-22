---
title: Modular Load Balancing with Terraform
description: Learn how to use Terraform Modules to create modular architectures with load balancing.
author: danisla
tags: Terraform
date_published: 2017-09-12
---

Dan Isla | Google Cloud Solution Architect | Google

Load balancing on Google Cloud Platform (GCP) is different from other cloud providers. The primary difference is that Google uses forwarding rules instead of routing instances. These forwarding rules are combined with backend services, target pools, URL maps and target proxies to construct a functional load balancer across multiple regions and instance groups.

[Terraform](https://www.terraform.io) is an open source infrastructure management tool that can greatly simplify the provisioning of load balancers on GCP by using modules.

This tutorial will demonstrate how to use the GCP Terraform modules for load balancing in a variety of scenarios that you can  build into your own projects.

## Objectives

- Learn about the load balancing modules for Terraform.
- Create a regional TCP load balancer.
- Create a regional internal TCP load balancer.
- Create a global HTTP load balancer with Kubernetes Engine.
- Create a global HTTPS content-based load balancer.

## Before you begin

This tutorial assumes you already have a GCP account and are familiar with the high level concepts of [Terraform](https://terraform.io) and [Load Balancing](https://cloud.google.com/compute/docs/load-balancing/) on GCP.

## Costs

This tutorial uses billable components of GCP, including:

- [Google Compute Engine](https://cloud.google.com/compute/pricing)
- [Cloud Storage](https://cloud.google.com/storage/pricing)
- [Forwarding Rules](https://cloud.google.com/compute/pricing#lb)

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to estimate your total costs.

## Terraform modules overview

### `terraform-google-lb` (regional forwarding rule)

This module creates a [TCP Network Load Balancer](https://cloud.google.com/compute/docs/load-balancing/network/example) for regional load balancing across a managed instance group. You provide a reference to a managed instance group and the module adds it to a target pool. A regional forwarding rule is created to forward traffic to healthy instances in the target pool.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/terraform-google-lb-diagram.png)

**Figure 1.** `terraform-google-lb` module Terraform resources diagram.

Example usage snippet:

    module "gce-lb-fr" {
      source       = "github.com/GoogleCloudPlatform/terraform-google-lb"
      region       = var.region
      name         = "group1-lb"
      service_port = module.mig1.service_port
      target_tags  = [module.mig1.target_tags]
    }

### `terraform-google-lb-internal` (regional internal forwarding rule)

This module creates an [internal load balancer](https://cloud.google.com/compute/docs/load-balancing/internal/) for regional load balancing of internal resources. You provide a reference to the managed instance group and the module adds it to a regional [backend service](https://cloud.google.com/compute/docs/load-balancing/internal/#backend-service). An internal forwarding rule is created to forward traffic to healthy instances.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/terraform-google-lb-internal-diagram.png)

**Figure 2.** `terraform-google-lb-internal` module Terraform resources diagram.

Example usage snippet:

    module "gce-ilb" {
      source         = "github.com/GoogleCloudPlatform/terraform-google-lb-internal"
      region         = var.region
      name           = "group2-ilb"
      ports          = [module.mig2.service_port]
      health_port    = module.mig2.service_port
      source_tags    = [module.mig1.target_tags]
      target_tags    = [module.mig2.target_tags,module.mig3.target_tags]
      backends       = [
        { group = module.mig2.instance_group },
        { group = module.mig3.instance_group },
      ]
    }

### `terraform-google-lb-http` (global HTTP(S) forwarding rule)

This module creates a [global HTTP load balancer](https://cloud.google.com/compute/docs/load-balancing/http/) for multi-regional content-based load balancing. You provide a reference to the managed instance group, optional certificates for SSL termination, and the module creates the [http backend service](https://cloud.google.com/compute/docs/load-balancing/http/backend-service), [URL map](https://cloud.google.com/compute/docs/load-balancing/http/url-map), [HTTP(S) target proxy](https://cloud.google.com/compute/docs/load-balancing/http/target-proxies), and the [global http forwarding rule](https://cloud.google.com/compute/docs/load-balancing/http/global-forwarding-rules) to route traffic based on HTTP paths to healthy instances.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/terraform-google-lb-http-diagram.png)

**Figure 3.** `terraform-google-lb-http` module Terraform resources diagram.

Example usage snippet:

    module "gce-lb-http" {
      source            = "github.com/GoogleCloudPlatform/terraform-google-lb-http"
      name              = "group-http-lb"
      target_tags       = [module.mig1.target_tags, module.mig2.target_tags]
      backends          = {
        "0" = [
          { group = module.mig1.instance_group },
          { group = module.mig2.instance_group }
        ],
      }
      backend_params    = [
        # health check path, port name, port number, timeout seconds.
        "/,http,80,10"
      ]
    }

## Clone the examples repository

All of the examples in this tutorial have sample code available in the [terraform-google-examples](https://github.com/GoogleCloudPlatform/terraform-google-examples) GitHub repository.

In this tutorial, you run all commands by using the [Google Cloud Shell](https://cloud.google.com/shell/). You can also run the commands from your local environment.

1. Open [Cloud Shell](https://console.cloud.google.com/cloudshell)
2. Clone the `terraform-google-examples` repository:

        git clone https://github.com/GoogleCloudPlatform/terraform-google-examples --recursive

        cd terraform-google-examples

## Download and configure Terraform

1. Configure your Cloud Shell environment to use Terraform through the Docker image.

        curl -L https://git.io/v51VZ -o ${HOME}/.tfdocker
        source ${HOME}/.tfdocker

This script creates a bash function for the `terraform` command that runs the latest version of Terraform using a Docker container. You can also [install it locally](https://www.terraform.io/downloads.html) if don't want to use Docker.

2. If you aren't using Cloud Shell, this tutorial uses the [default application credentials](https://developers.google.com/identity/protocols/application-default-credentials) for Terraform authentication to GCP. Run the following command first to obtain the default credentials for your project.

        gcloud auth application-default login

## TCP load balancer with regional forwarding rule

This example creates a managed instance group with two instances in the same region and a network TCP load balancer.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/example-lb-diagram.png)

**Figure 4.** `example-lb` architecture diagram

1. Change to the example directory:

        cd example-lb

2. Run Terraform to deploy architecture:

        export GOOGLE_PROJECT=$(gcloud config get-value project)
        terraform init
        terraform plan
        terraform apply


      The instances and load balancer are ready after a few minutes.

3. Open the URL of the load balancer in a browser:

        EXTERNAL_IP=$(terraform output -module gce-lb-fr | grep external_ip | cut -d = -f2 | xargs echo -n)

        echo "open http://${EXTERNAL_IP}"

4. In a new browser tab, open the link displayed in the terminal.
5. Refresh a few times to observe traffic being balanced across the two instances in the `us-central1` region.
6. When finished, clean up the example by running `terraform destroy` and change back to the parent directory:

        terraform destroy
        cd ..

## Internal TCP load balancer with regional forwarding rule

This example creates three instance groups. The first group is in `us-central1-b` and uses the internal load balancer to proxy access to services running in instance groups two and three which exist in `us-central1-c` and `us-central1-f` respectively. A regional TCP load balancer is also used to forward external traffic to the instances in group one.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/example-lb-internal-diagram.png)

**Figure 5.** `example-lb-internal` architecture diagram.

1. Change to the example directory:

        cd example-lb-internal

2. Run Terraform to deploy architecture:

        export GOOGLE_PROJECT=$(gcloud config get-value project)
        terraform init
        terraform plan
        terraform apply

      The instances and load balancer are ready after a few minutes.

3. Open the URL of the load balancer in a browser:

        EXTERNAL_IP=$(terraform output -module gce-lb-fr | grep external_ip | cut -d = -f2 | xargs echo -n)

        echo "open http://${EXTERNAL_IP}"

4. In a new browser tab, open the link displayed in the terminal.
5. Refresh a few times to observe traffic being balanced across the four instances in the `us-central1-c` and `us-central1-f` zones.
6. When finished, clean up the example by running `terraform destroy` and change back to the parent directory:

        terraform destroy
        cd ..

## Global HTTP load balancer

This example creates a global HTTP forwarding rule to forward traffic to instance groups in the `us-west1` and `us-east1` regions.

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/example-lb-http-diagram.png)

**Figure 6.** `example-lb-http architecture` diagram.

1. Change to the example directory:

        cd example-lb-http

2. Run Terraform to deploy architecture:

        export GOOGLE_PROJECT=$(gcloud config get-value project)
        terraform init
        terraform plan
        terraform apply

      The instances and load balancer are ready after a few minutes.

3. Open the URL of the load balancer in a browser:

        EXTERNAL_IP=$(terraform output -module gce-lb-http | grep external_ip | cut -d = -f2 | xargs echo -n)

        echo "open http://${EXTERNAL_IP}"

4. In a new browser tab, open the link displayed in the terminal.

      It can take several minutes for the forwarding rule to be provisioned. While it's being created, you might see 404 and 500 errors in the browser.

5. Refresh a few times to observe traffic being balanced across the 2 instances in the region closest to you.
6. Verify traffic can flow to the other region by scaling the region closest to you to zero instances.

        # If you are getting traffic from us-west1, scale group 1 to 0 instances:
        TF_VAR_group1_size=0 terraform apply

        # Otherwise scale group 2 (us-east1) to 0 instances:
        TF_VAR_group2_size=0 terraform apply


7. Open the external IP again and verify you see traffic from the other group:

        echo "open http://${EXTERNAL_IP}"

8. In a new browser tab, open the link displayed in the terminal.
9. When finished, clean up the example by running `terraform destroy` and change back to the parent directory:

        terraform destroy
        cd ..

## Global content-based HTTP(S) load balancer

This example creates an HTTPS load balancer to forward traffic to a custom URL map. The URL map sends traffic to the region closest to you with static assets being served from a Cloud Storage bucket. The TLS key and certificate is generated by Terraform using the [TLS provider](https://www.terraform.io/docs/providers/tls/index.html).

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/modular-load-balancing-with-terraform/example-lb-https-content-diagram.png)

**Figure 7.** `example-lb-https-content architecture` diagram.

1. Change to the example directory:

        cd example-lb-https-content

2. Run Terraform to deploy architecture:

        export GOOGLE_PROJECT=$(gcloud config get-value project)
        terraform init
        terraform plan
        terraform apply

      The instances and load balancer are ready after a few minutes.

3. Open the URL of the load balancer in a browser:

        EXTERNAL_IP=$(terraform output -module gce-lb-http | grep external_ip | cut -d = -f2 | xargs echo -n)

        echo "open https://${EXTERNAL_IP}/"

4. In a new browser tab, open the link displayed in the terminal.

      It can take several minutes for the forwarding rule to be provisioned. While it's being created, you might see 404 and 500 errors in the browser.

5. You should see the GCP logo and instance details from the group closest to your geographical region.
6. You can access the per-region routes directly through the URLs below:

        # us-west1
        echo "open https://${EXTERNAL_IP}/group1/"

        # us-central1
        echo "open https://${EXTERNAL_IP}/group2/"

        # us-east1
        echo "open https://${EXTERNAL_IP}/group3/"

7. When finished, clean up the example by running `terraform destroy` and change back to the parent directory:

        terraform destroy
        cd ..

## Cleanup

Each example includes its own cleanup and can be explicitly cleaned from within each directory by using this command:

        terraform destroy

## Next Steps

- [Additional examples in the terraform-google-examples repository](https://github.com/GoogleCloudPlatform/terraform-google-examples).
- [Learn more about load balancing on GCP](https://cloud.google.com/compute/docs/load-balancing/).
