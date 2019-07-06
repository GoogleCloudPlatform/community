---
title: Deploy HA VPN with Terraform
description: Deploy full GCP envrionment used in HA VPN interop guides with Terraform.
author: ashishverm
tags: terraform, ha vpn,
date_published: 2019-07-06
---

This tutorial demonstrates how to deploy High Availability VPN resources on Google Cloud Platform
used in [interop guides](https://cloud.google.com/vpn/docs/how-to/interop-guides) with Terraform.

## Objectives

Create HA VPN with [1-peer-2-address](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) topology
on Google Cloud Platform.

## Before you begin

This guide assumes you are familiar with Terraform. Instructions provided in this guide
are based on the GCP envrionment depicted in HA VPN interop guides and only for testing
purposes.

See [getting-started-on-gcp-with-terraform](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/getting-started-on-gcp-with-terraform/index.md)
to setup your Terraform envrionment for Google Cloud Platform.

Ensure you have service account with sufficient permissions to deploy resources
used in this tutorial.

## Quick Start

*   Activate Google Cloud Shell. Use Cloud Shell because the Google Cloud SDK
    (gcloud) and other tools are included.
*   `git clone https://github.com/GoogleCloudPlatform/deploy-ha-vpn-with-terraform.git`
*   `cd deploy-ha-vpn-with-terraform`
*   [optional]Change variable values in `gcp_variables.tf` per your envrionment.
*   Run Terraform.
    *   Examine configuration files.
        *   `terraform init`
        *   `terraform validate`
        *   `terraform plan`
    *   Apply configurations.
        *   `terraform apply`
    *   Confirm configurations.
        *   `terraform output`
        *   `terraform show`
*   Clean up
    *   `terraform plan -destroy`
    *   `terraform destroy`
    *   `terraform show`

## References

*   [Automated multi cloud classic VPN](https://github.com/GoogleCloudPlatform/autonetdeploy-multicloudvpn)
*   [HA VPN Topologies](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses)
*   [Creating HA VPN](https://cloud.google.com/vpn/docs/how-to/creating-ha-vpn)
*   [VPN interop guides](https://cloud.google.com/vpn/docs/how-to/interop-guides)
