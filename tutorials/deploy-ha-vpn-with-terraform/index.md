---
title: Deploy HA VPN with Terraform
description: Deploy Google Cloud environment used in HA VPN interop guides with Terraform.
author: ashishverm
tags: terraform, ha vpn,
date_published: 2019-07-12
---

Ashish Verma | Technical Program Manager | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to use Terraform to deploy the High Availability VPN resources on Google Cloud that are used in the
[VPN interoperability guides](https://cloud.google.com/vpn/docs/how-to/interop-guides).

## Objectives

Deploy HA VPN with a [1-peer-2-addresses](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) 
configuration on Google Cloud.

## Before you begin

*   This guide assumes that you are familiar with [Terraform](https://cloud.google.com/docs/terraform). Instructions provided in this guide
    are based on the Google Cloud environment depicted in the
    [HA VPN interop guides](https://cloud.google.com/vpn/docs/how-to/interop-guides) and are only for testing purposes.

*   See [Getting started with Terraform on Google Cloud](https://cloud.google.com/community/tutorials/getting-started-on-gcp-with-terraform) to set up your Terraform environment for Google Cloud.

*   Ensure the you have a [service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) with 
    [sufficient permissions](https://cloud.google.com/vpn/docs/how-to/creating-ha-vpn2#permissions) to deploy the resources
    used in this tutorial.

## Quickstart

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git
        
1.  Go to the `deploy-ha-vpn-with-terraform/terraform` directory:

        cd community/tutorials/deploy-ha-vpn-with-terraform/terraform

1.  (optional) Change variable values in `gcp_variables.tf` for your environment.

1.  Run the following Terraform commands:

    1.  Examine configuration files:

            terraform init
            terraform validate
            terraform plan
            
    1.  Apply the configurations: 

            terraform apply
            
    1.  Confirm configurations:
    
            terraform output
            terraform show

    1.  Clean up:
    
            terraform plan -destroy
            terraform destroy
            terraform show

## References

*   [Automated multi-cloud classic VPN](https://github.com/GoogleCloudPlatform/autonetdeploy-multicloudvpn)
*   [HA VPN topologies](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses)
*   [Creating HA VPN](https://cloud.google.com/vpn/docs/how-to/creating-ha-vpn)
*   [VPN interop guides](https://cloud.google.com/vpn/docs/how-to/interop-guides)
