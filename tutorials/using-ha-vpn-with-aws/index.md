---
title: Google Cloud HA VPN Interop Guide for AWS
description: Describes how to build site-to-site IPsec VPNs between HA VPN on Google Cloud Platform (GCP) and AWS.
author: ashishverm
tags: HA VPN, Cloud VPN, interop, AWS
date_published: 2019-07-06
---

# Using HA VPN with AWS

Author: ashishverm

Learn how to build site-to-site IPSec VPNs between [HA VPN](https://cloud.google.com/vpn/docs/)
on Google Cloud Platform (GCP) and AWS.

AWS terminology and the AWS logo are
trademarks of Amazon Web Services or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

## Introduction

This guide walks you through the process of configuring route based VPN
tunnel between AWS and the [HA VPN service](https://cloud.google.com/vpn/docs)
on GCP.

For more information about HA or Classic VPN, see the
[Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

-  **GCP VPC network**: A single virtual network within a single GCP project.
-  **On-premises gateway**: The VPN device on the non-GCP side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. GCP instructions are written from the
point of view of the GCP VPC network, so *on-premises gateway* refers to the
gateway that's connecting _to_ GCP.
-  **External IP address** or **GCP peer address**: External IP
addresses used by peer VPN devices to establish HA VPN with GCP.
External IP addresses are allocated automatically, one for each gateway interface within a
GCP project.
-  **Dynamic routing**: GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
Note that HA VPN only supports dynamic routing.

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/vpn/docs/concepts/topologies).

This interop guide is based on the [AWS-peer-gateways](https://cloud.google.com/vpn/docs/concepts/topologies#aws_peer_gateways) 
using `FOUR_IPS_REDUNDANCY` REDUNDANCY_TYPE.

There are three major gateway components to set up for this configuration, as shown in the following topology diagram:

-  An HA VPN gateway in Google Cloud Platform with two interfaces.
-  Two AWS Virtual Private Gateways, which connect to your HA VPN gateway.
-  An external VPN gateway resource in GCP that represents your AWS Virtual Private Gateway. 
   This resource provides information to GCP about your AWS gateway.
   
   <insert-diagram>

The supported AWS configuration uses 4 tunnels total:

-  Two tunnels from one AWS Virtual Private Gateway to one interface of the HA VPN gateway.
-  Two tunnels from the other AWS Virtual Private Gateway to the other interface of the HA VPN gateway.

## Before you begin

1.  Review information about how
    [dynamic routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#dynamic-routing)
    works in Google Cloud Platform.

1.  Select or [create](https://console.cloud.google.com/cloud-resource-manager) a GCP project.

1.  Make sure that [billing](https://cloud.google.com/billing/docs/how-to/modify-project) is
    enabled for your GCP project.

1.  [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1.  If you are using `gcloud` commands, set your project ID with the following command:

        gcloud config set project [PROJECT_ID]

    The `gcloud` instructions on this page assume that you have set your project ID before
    issuing commands.

1.  You can also view a project ID that has already been set:

        gcloud config list --format='text(core.project)'

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a GCP project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values used in this guide.

| Parameter description | Placeholder          | Example value                                          |
|-----------------------|----------------------|--------------------------------------------------------|
| Vendor name           | `[VENDOR_NAME]`      | AWS                                                    |
| GCP project name      | `[PROJECT_NAME]`     | `vpn-guide`                                            |
| Shared secret         | `[SHARED_SECRET]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| VPC network name      | `[NETWORK]`          | `network-a`                                            |
| Subnet mode           | `[SUBNET_MODE]`      | `custom`                                               |
| VPN BGP routing mode  | `[BGP_ROUTING_MODE]` | `global`                                               |
| Subnet on the GCP VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_1]` | `subnet-a-central` |
| Subnet on the GCP VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_2]` | `subnet-a-west` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION1]` | `us-central1` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION2]` | `us-west1` |
| IP address range for the GCP VPC subnet (`vpn-subnet-1`) | `[RANGE_1]` | `10.0.1.0/24` |
| IP address range for the GCP VPC subnet (`vpn-subnet-2`) | `[RANGE_2]` | `10.0.2.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to GCP. | `[IP_ON_PREM_SUBNET]` | `192.168.1.0/24` |
| External static IP address for the first internet interface of Foritgate  | `[ON_PREM_GW_IP_0]` | `` |
| External static IP address for the second internet interface of Foritgate | `[ON_PREM_GW_IP_1]` | `` |
| External static IP address for the first internet interface of Foritgate  | `[ON_PREM_GW_IP_2]` | `` |
| External static IP address for the second internet interface of Foritgate | `[ON_PREM_GW_IP_3]` | `` |
| HA VPN gateway                          | `[GW_NAME]`                 | `ha-vpn-gw-a`                       |
| Cloud Router name (for dynamic routing) | `[ROUTER_NAME]`             | `router-a`                          |
| Google ASN                              | `[GOOGLE_ASN]`              | `65001`                             |
| Peer ASN                                | `[PEER_ASN]`                | `65002`                             |
| External VPN gateway resource           | `[PEER_GW_NAME]`            | `peer-gw`                           |
| First VPN tunnel                        | `[TUNNEL_NAME_IF0]`         | `tunnel-a-to-on-prem-if-0`          |
| Second VPN tunnel                       | `[TUNNEL_NAME_IF1]`         | `tunnel-a-to-on-prem-if-1`          |
| First BGP peer interface                | `[ROUTER_INTERFACE_NAME_0]` | `bgp-peer-tunnel-a-to-on-prem-if-0` |
| Second BGP peer interface               | `[ROUTER_INTERFACE_NAME_1]` | `bgp-peer-tunnel-a-to-on-prem-if-1` |
| BGP interface netmask length            | `[MASK_LENGTH]`             | `/30`                               |

## High-level configuration steps
Because HA VPN is dependent on BGP IP settings generated by AWS, you must configure Cloud VPN and AWS components in the following sequence:

1.  Create the HA VPN gateway and create a Cloud Router.
1.  Create two AWS Virtual Private Gateways.
1.  Create two AWS Site-to-Site VPN connections and customer gateways; one for each AWS Virtual Private Gateway.
1.  Download the AWS configuration files..
1.  Create four VPN tunnels on the HA VPN gateway.
1.  Configure BGP sessions on the Cloud Router using the BGP IP addresses from the downloaded AWS configuration files.

## Configure the GCP side

This section covers how to configure HA VPN. See [deply-ha-vpn-with-terraform](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/deploy-ha-vpn-with-terraform/index.md)
for a quick depploment.

There are two ways to create HA VPN gateways on GCP: using the GCP Console and using
[`gcloud` commands](https://cloud.google.com/sdk/).

This section describes how to perform the tasks using `gcloud` commands.

### Initial tasks

Complete the following procedures before configuring a GCP HA VPN gateway and tunnel.

These instructions create a [custom mode](https://cloud.google.com/vpc/docs/vpc#subnet-ranges)
VPC network with one subnet in one region and another subnet in another region.

#### Create a custom VPC network

If you haven't already, create a VPC network with this command:

    gcloud compute networks create [NETWORK] \
    --subnet-mode [SUBNET_MODE]  \
    --bgp-routing-mode [BGP_ROUTING_MODE]

Replace the placeholders as follows:

- `[NETWORK]`: Assign a network name.
- `[SUBNET_MODE]`: Set as `custom`.
- `[BGP_ROUTING_MODE]`: Set as `global`.

The command should look similar to the following example:

    gcloud compute networks create network-a \
    --subnet-mode custom  \
    --bgp-routing-mode global

#### Create subnets

Create two subnets:

    gcloud compute networks subnets create [SUBNET_NAME_1]  \
    --network [NETWORK] \
    --region [REGION_1] \
    --range [RANGE_1]

    gcloud compute networks subnets create [SUBNET_NAME_2] \
    --network [NETWORK] \
    --region [REGION_2] \
    --range [RANGE_2]

The commands should look similar to the following example:

    gcloud compute networks subnets create subnet-a-central  \
    --network network-a \
    --region us-central1 \
    --range 10.0.1.0/24

    gcloud compute networks subnets create subnet-a-west \
    --network network-a \
    --region us-west1 \
    --range 10.0.2.0/24

### Create the HA VPN gateway

Create the HA VPN gateway:

    gcloud beta compute vpn-gateways create [GW_NAME] \
    --network [NETWORK] \
    --region [REGION]

The command should look similar to the following example:

    gcloud beta compute vpn-gateways create ha-vpn-gw-a \
    --network network-a \
    --region us-central1

When the gateway is created, two external IP addresses are automatically allocated,
one for each gateway interface.

### Create Cloud Router

Create a Cloud Router:

    gcloud compute routers create [ROUTER_NAME] \
    --region [REGION] \
    --network [NETWORK] \
    --asn [GOOGLE_ASN]

Replace the placeholders as follows:

- `[ROUTER_NAME]`: The name of the new Cloud Router, which you must create in the same GCP
  region as the Cloud HA VPN gateway.
- `[GOOGLE_ASN]`: Any private ASN (64512-65534, 4200000000-4294967294) that you are not
  already using in the peer network. The Google ASN is used for all BGP sessions on the
  same Cloud Router, and it cannot be changed later.

The command should look similar to the following example:

    gcloud compute routers create router-a \
    --region us-central1 \
    --network network-a \
    --asn 65001
    
## Configure AWS VPN gateways

Create two AWS virtual private gateways, each associated with an AWS site-to-site 
VPN connection and a customer gateway.The first AWS gateway has one site-to-site 
connection and two customer gateways. The first AWS configuration connects to 
interface 0 on the HA VPN gateway. The second AWS gateway has the same configuration
and connects to interface 1 on the HA VPN gateway.

Create all AWS components in the AWS VPC console dashboard by selecting each top-level 
component in the dashboard's navigation bar.

**Note:** These instructions assume you have created an AWS VPC for this gateway.

### Create the AWS gateway and attach it to a VPC

1. In the AWS dashboard, under **Virtual Private Network**, select **Virtual Private Gateways**.
1. Click **Create Virtual Private Gateway**.
1. Enter a **Name** for the gateway.
1. Select **Custom ASN** and give the gateway an AWS ASN that doesn't conflict with the [GOOGLE_ASN].
1. Click **Create Virtual Private Gateway**. Click **Close**.
1. Attach the gateway to the AWS VPC by selecting the gateway you just created, clicking **Actions, Attach to VPC**.
   1. Pull down the menu and select a VPC for this gateway and click **Yes, Attach**.
   1. Note the ID of the gateway for the steps that follow.

### Create a site-to-site connection and customer gateway

1. In the AWS dashboard, under **Virtual Private Network** select **Site-to-site VPN connections**.
1. Click **Create VPN connection**.
1. Enter a **Name** for the connection.
1. Pull down the **Virtual Private Gateway** menu and select the ID of the Virtual private gateway you just created.
1. Under **Customer gateway** select `New`.
     1. For **IP address**, use the public IP address that was automatically generated for interface 0 of the HA VPN gateway you created earlier.
     1. For **BGP ASN**, use the value for `[GOOGLE_ASN]`.
     1. Under **Routing options** make sure `dynamic` is selected.
     1. For **Tunnel 1** and **Tunnel 2**, specify the **Inside IP CIDR** for your AWS VPC network, 
        which is a BGP IP address from a /30 CIDR in the `169.254.0.0/16` range. 
        For example, `169.254.1.4/30`. This address must not overlap with the BGP IP address 
        for the GCP side. When you specify the Pre-shared key, you must use the same pre-shared
        key for the tunnel from the HA VPN gateway side. If you specify a key, AWS doesn't autogenerate it.
     1. Click **Create VPN connection**.
     
**Create the second AWS gateway**

Repeat the above steps to create a second AWS gateway, site-to-site connection, and customer gateway, 
but use the IP address generated for HA VPN gateway interface 1 instead. Use the same [GOOGLE_ASN].

**Download the AWS configuration settings for each site-to-site connection**

1. As of this writing, you can download the configuration settings from your AWS virtual private gateway 
into a text file that you can reference when configuring HA VPN. You do this after you've configured 
the HA VPN gateway and Cloud Router:
1. On the AWS **VPC Dashboard** screen, in the left navigation bar, select **Site-to-Site VPN Connections**.
1. Check the checkbox for the first VPN connection to download.
1. At the top of the screen, click the middle button that reads **Download Configuration**. The **Download 
Configuration** button provides only one configuration file, the one for the selected connection.
1. In the pop-up dialog box, choose `vendor: generic`. There is no need to change the rest of the fields, 
Click the **Download** button.
1. Repeat the above steps, but choose the second VPN connection to download the file.

## Create an External VPN Gateway resource

When you create a GCP external VPN gateway resource for an AWS virtual private gateway, 
you must create it with four interfaces, as as shown in the AWS topology diagram.

**Note:** For successful configuration, you must use the public IP addresses for the AWS 
interfaces as referenced in the two AWS configuration files you downloaded earlier.
You must also match each AWS public IP address exactly with a specific HA VPN interface. 
The instructions below describe this task in detail.

1. Complete the following command to create the External VPN gateway resource. Replace the options as noted below:

   1. For [AWS_GW_IP_0], in the configuration file you downloaded for AWS Connection 0, 
under IPSec tunnel #1, #3 Tunnel Interface Configuration, use the IP address 
under Outside IP address, Virtual private gateway.
   1. For [AWS_GW_IP_1], in the configuration file you downloaded for AWS Connection 0, 
under IPSec tunnel #2, #3 Tunnel Interface Configuration, use the IP address under 
Outside IP address, Virtual private gateway.
   1. For [AWS_GW_IP_2], in the configuration file you downloaded for AWS Connection 1, 
under IPSec tunnel #1, #3 Tunnel Interface Configuration, use the IP address under 
Outside IP address, Virtual private gateway.
   1. For [AWS_GW_IP_3], in the configuration file you downloaded for AWS Connection 1, 
under IPSec tunnel #2, #3 Tunnel Interface Configuration, use the IP address under Outside IP address, Virtual private gateway.

              gcloud compute external-vpn-gateways create peer-gw \
              --interfaces 0=[AWS_GW_IP_0],  \
                          1=[AWS_GW_IP_1],  \
                          2=[AWS_GW_IP_2],  \
                          3=[AWS_GW_IP_3]
