---
title: Google Cloud HA VPN Interop Guide for [PRODUCT]
description: Describes how to build site-to-site IPsec VPNs between HA VPN on Google Cloud Platform (GCP) and  [VENDOR] [PRODUCT]
author: [AUTHOR]
tags: VPN, interop, [VENDOR], [PRODUCT]
date_published: YYYY-mm-dd
---

**BEGIN: HOW TO USE THIS TEMPLATE**

1. Make a copy of this template.
1. On your local computer, update and add information as indicated. Note:
    + Fill in the meta information (title, description, author, date_published at the top
      of this file.
    + There are notes in the template for you, the author, that explain where you need to
      make changes. These notes are enclosed in brackets (&lt; &gt;).
    + The template contains placeholders for things like the vendor and 
      product name. These are also enclosed in brackets—for example, 
      every place you see `<vendor-name>` and `<product-name>`, 
      substitute approriate names.
    + After you've made appropriate updates, _remove_ bracketed content.
    + Remove these instructions.
    + Because this is a template for a variety of setups, it might contain
      content that isn't releavent to your scenario. Remove (or update)
      any sections that don't apply to you.
1. Fork the [GoogleCloudPlatform/community/](https://github.com/GoogleCloudPlatform/community/) repo.
4. In your fork, add a new folder named `/tutorials/[YOUR_TUTORIAL]`. For the
   folder name, use hyphens to separate words. We recommend that you 
   include a product name in the folder name, such as `https-load-balancing-ingix`.
5. Copy the updated file to the `index.md` file of the new folder.
6. Create a branch.
7. Issue a PR to get your new content into the community site.
   
<**END: HOW TO USE THIS TEMPLATE**>

# Using HA VPN with <vendor-name><product-name>

Learn how to build site-to-site IPsec VPNs between
[HA VPN](https://cloud.google.com/vpn/docs/)on Google Cloud Platform (GCP) and
<vendor-name><product-name>.

<To see a finished version of this guide, see the
[Using Cloud VPN with Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page).>

<NOTE: Options or instructions are shown in angle brackets throughout this
template. Change or remove these items as needed.>

#####add TOC here####

<Put trademark statements here>: <vendor terminology> and the <vendor> logo are
trademarks of <vendor company name> or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

Author: <author name and email address>

## Introduction

This guide walks you through the process of configuring
<vendor-name><product-name> for integration with the
[HA VPN service](https://cloud.google.com/vpn/docs) on GCP.

For more information about Cloud VPN, see the
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

<This is some sample terminology. Add any terminology to this section that needs
explanation.>

-  **GCP VPC network**—A single virtual network within a single GCP project.
-  **On-premises gateway**—The VPN device on the non-GCP side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. GCP instructions are written from the
point of view of the GCP VPC network, so "on-premises gateway" refers to the
gateway that's connecting _to_ GCP.
-  **External IP address** or **GCP peer address**—a single static IP address
within a GCP project that exists at the edge of the GCP network.
-  **Static routing**—Manually specifying the route to subnets on the GCP
side and to the on-premises side of the VPN gateway.
-  **Dynamic routing**—GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
-  <<vendor-name><product-name> term>
-  <<vendor-name><product-name> term>

## Topology

Cloud VPN supports the following topologies:

-  A site-to-site IPsec VPN tunnel configuration using 
[Cloud Router](https://cloud.google.com/router/docs/)
and providing dynamic routing with the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).

For detailed topology information, see the following resources:

-  For basic VPN topologies, see 
[Cloud VPN Overview](https://cloud.google.com/vpn/docs/concepts/overview).
-  For redundant topologies,  the
[Cloud VPN documentation on redundant and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns).

## Product environment

The <vendor-name><product-name> equipment used in this guide is as follows:

-  Vendor—<vendor-name>
-  Model—<model name>
-  Software release—<full software release name>

<Fill in the following if the vendor supports more than one platform. However,
the following section is optional, because some vendors might only have one
platform.>

Although the steps in this guide use <model name>, this guide also applies to
the following <product-name> platforms:

-  <vendor model 1>
-  <vendor model 2>
-  <vendor model 3>


## Before you begin

Follow the steps in this section to prepare for VPN configuration.

**Note**: This guide assumes that you have basic knowledge of the
[IPsec](https://wikipedia.org/wiki/IPsec) protocol.

### GCP account and project

Make sure you have a GCP account. When you begin, you must select or create a
GCP project where you will build the VPN. For details, see
[Creating and Managing Projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

### Permissions

To create a GCP network, a subnetwork, and other entities described in this
guide, you must be able to sign in to GCP as a user who has
[Network Admin](https://cloud.google.com/compute/docs/access/iam#network_admin_role)
permissions. For details, see
[Required Permissions](https://cloud.google.com/vpn/docs/how-to/creating-vpn-dynamic-routes#required_permissions)
in the article
[Creating a VPN Tunnel using Dynamic Routing](https://cloud.google.com/vpn/docs/how-to/creating-vpn-dynamic-routes).

### Licenses and modules

<This section is optional, because some VPN vendors can be open source or cloud
providers that don't require licensing>

Before you configure your <vendor-name><product-name> for use with Cloud VPN,
make sure that the following licenses are available:

<Below are some examples. Replace with information that applies to the
product>

-  Advanced Enterprise Services (SLASR1-AES) or Advanced IP Services
Technology Package License (SLASR1-AIS).
-  IPsec RTU license (FLASR1-IPsec-RTU).
-  Encryption HW module (ASR1002HX-IPsecHW(=) and ASR1001HX-IPsecW(=)) and
Tiered Crypto throughput license, which applies to ASR1002-HX and ASR1001-HX
chassis only.

<For detailed <vendor-name><product-name> license information, see the
<Vendor-Guide-link> documentation.>

## Configure the GCP side

This section covers how to configure HA VPN.

There are two ways to create HA VPN gateways on GCP: using the Google Cloud
Platform Console and using the
[gcloud command-line tool](https://cloud.google.com/sdk/).
This section describes how to perform the tasks using the GCP Console. To see
the `gcloud` commands for performing these tasks, see the
[appendix](#appendix-using-gcloud-commands).

### Initial tasks

Complete the following procedures before configuring a GCP HA VPN gateway and tunnel.

#### Select a GCP project name

1. [Open the GCP Console](https://console.google.com).
1. At the top of the page, select the GCP project you want to use.

    **Note**: Make sure that you use the same GCP project for all of the GCP
    procedures in this guide.

#### Create a custom VPC network and subnet

1. In the GCP Console,
[go to the VPC Networks page](https://console.cloud.google.com/networking/networks/list).
1. Click **Create VPC network**.
1. For **Name**, enter a name such as `vpn-vendor-test-network`. Remember
this name for later.
1. Under **Subnets, Subnet creation mode**, select the **Custom** tab and
then populate the following fields:

+ **Name**—The name for the subnet, such as `vpn-subnet-1`.
+ **Region**—The region that is geographically closest to the
    on-premises gateway, such as  `us-east1`.
+ **IP address range**—A range such as `172.16.100.0/24`.

1. In the **New subnet** window, click **Done**.
1. Click **Create**. You're returned to the **VPC networks** page, where it
takes about a minute for this network and its subnet to appear.
