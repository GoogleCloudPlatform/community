---
title: Google Cloud HA VPN Interop Guide for [PRODUCT]
description: Describes how to build site-to-site IPsec VPNs between HA VPN on Google Cloud Platform (GCP) and [VENDOR] [PRODUCT]
author: [AUTHOR]
tags: HA VPN, Cloud VPN, interop, [VENDOR], [PRODUCT]
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

# Using HA VPN with \<vendor-name>\<product-name>

Learn how to build site-to-site IPsec VPNs between [HA VPN](https://cloud.google.com/vpn/docs/)
on Google Cloud Platform (GCP) and \<vendor-name>\<product-name>.

To see a finished version of this guide, see the
[Using Cloud VPN with Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page).

**NOTE**: Options or instructions are shown in angle brackets throughout this
template. Change or remove these items as needed.

- [Introduction](#introduction)
- [Terminology](#terminology)
- [Topology](#topology)
- [Product environment](#product-environment)
- [Before you begin](#before-you-begin)
    - [Licenses and modules](#licenses-and-modules)
    - [Configuration parameters and values](#configuration-parameters-and-values)
- [Configure the GCP side](#configure-the-gcp-side)
    - [Initial tasks](#initial-tasks)
        - [Create a custom VPC network](#create-a-custom-vpc-network)
        - [Create subnets](#create-subnets)
    - [Create the HA VPN gateway](#create-the-ha-vpn-gateway)
    - [Create Cloud Router](#create-cloud-router)
    - [Create an External VPN Gateway resource](#create-an-external-vpn-gateway-resource)
        - [Create an External VPN Gateway resource for a single peer VPN gateway with two separate interfaces](#create-an-external-vpn-gateway-resource-for-a-single-peer-vpn-gateway-with-two-separate-interfaces)
    - [Create two VPN tunnels, one for each interface on the HA VPN gateway](#create-two-vpn-tunnels-one-for-each-interface-on-the-ha-vpn-gateway)
    - [Create Cloud Router interfaces and BGP peers](#create-cloud-router-interfaces-and-bgp-peers)
- [Configure the \<vendor-name>\<vendor product> side](#configure-the-vendor-namevendor-product-side)
    - [Creating the base network configuration](#creating-the-base-network-configuration)
    - [Creating the base VPN gateway configuration](#creating-the-base-vpn-gateway-configuration)
    - [GCP-compatible settings for IPSec and IKE](#gcp-compatible-settings-for-ipsec-and-ike)
        - [Configure the IKE proposal and policy](#configure-the-ike-proposal-and-policy)
        - [Configure the IKEv2 keyring](#configure-the-ikev2-keyring)
        - [Configure the IKEv2 profile](#configure-the-ikev2-profile)
        - [Configure the IPsec security association (SA)](#configure-the-ipsec-security-association-sa)
        - [Configure the IPsec transform set](#configure-the-ipsec-transform-set)
        - [Configure the IPsec static virtual tunnel interface (SVTI)](#configure-the-ipsec-static-virtual-tunnel-interface-svti)
    - [Configuring the dynamic routing protocol](#configuring-the-dynamic-routing-protocol)
    - [Saving the configuration](#saving-the-configuration)
    - [Testing the configuration](#testing-the-configuration)
- [Troubleshooting IPsec on \<vendor-name>\<product-name>](#troubleshooting-ipsec-on-vendor-nameproduct-name)
- [Reference documentation](#reference-documentation)
    - [GCP documentation](#gcp-documentation)
    - [\<vendor-name>\<product-name> documentation](#vendor-nameproduct-name-documentation)

<Put trademark statements here>: <vendor terminology> and the <vendor> logo are
trademarks of <vendor company name> or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

Author: <author name and email address>

## Introduction

This guide walks you through the process of configuring
\<vendor-name>\<product-name> for integration with the
[HA VPN service](https://cloud.google.com/vpn/docs) on GCP.

For more information about HA or Classic VPN, see the
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
-  **Dynamic routing**—GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
-  \<vendor-name>\<product-name> term
-  \<vendor-name>\<product-name> term

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/vpn/docs/concepts/topologies):

This interop guide is based on [1-peer-2-address](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) topology.

## Product environment

The \<vendor-name>\<product-name> equipment used in this guide is as follows:

-  Vendor — <vendor-name>
-  Model — <model name>
-  Software release — <full software release name>

## Before you begin

1. Review information about how [dynamic routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#dynamic-routing) works in GCP.

1. Make sure your peer VPN gateway supports BGP.

Setting up the following items in GCP makes it easier to configure HA VPN:

1. Select or [create](https://console.cloud.google.com/cloud-resource-manager) 
a Google Cloud Platform project.

1. Make sure that [billing](https://cloud.google.com/billing/docs/how-to/modify-project) 
is enabled for your Google Cloud Platform project.

1. [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1. If you are using gcloud commands, set your project ID with the following command. 
The gcloud instructions on this page assume that you have set your project ID before 
issuing commands.

   `gcloud config set project [PROJECT_ID]`
    
1. You can also view a project ID that has already been set:

    `gcloud config list --format='text(core.project)'`

### Licenses and modules

<This section is optional, because some VPN vendors can be open source or cloud
providers that don't require licensing>

Before you configure your <vendor-name><product-name> for use with HA VPN,
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

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a GCP project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values. The section that follows
the table describes how to set Linux environment variables to hold the values
you need for these parameters.

<table>
<thead>
<tr>
<th><strong>Parameter description</strong></th>
<th><strong>Placeholder</strong></th>
<th><strong>Example value</strong></th>
</tr>
</thead>
<tbody>

<tr>
<td>Vendor name</td>
<td><code>[VENDOR_NAME]<code></td>
<td>(Your product's vendor name. This value should have no spaces or
punctuation in it other than underscores or hyphens, because it will be
used as part of the names for GCP entities.)</td>
</tr>

<tr>
<td>GCP project name </td>
<td><code>[PROJECT_NAME]<code></td>
<td><code>vpn-guide<code></td>
</tr>

<tr>
<td>Shared secret</td>
<td><code>[SHARED_SECRET]<code></td>
<td>See <a
href="https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key">Generating
a Strong Pre-shared Key</a>.</td>
</tr>

<tr>
<td>VPC network name</td>
<td><code>[NETWORK]<code></td>
<td><code>network-a<code></td>
</tr>

<tr>
<td>Subnet mode</td>
<td><code>[SUBNET_MODE]<code></td>
<td><code>custom<code></td>
</tr>

<tr>
<td>BGP routing mode</td>
<td><code>[BGP_ROUTING_MODE]<code></td>
<td><code>global</td>
</tr>

<tr>
<td>Subnet on the GCP VPC network (for example, <code>vpn-vendor-test-network</code>)</td>
<td><code>[SUBNET_NAME_1]<code></td>
<td><code>subnet-a-central<code></td>
</tr>
    
<tr>
<td>Subnet on the GCP VPC network (for example, <code>vpn-vendor-test-network</code>)</td>
<td><code>[SUBNET_NAME_2]<code></td>
<td><code>subnet-a-west<code></td>
</tr>
    
<tr>
<td>GCP region. Can be any region, but it should be geographically close to the
on-premises gateway.</td>
<td><code>[REGION1]<code></td>
<td><code>us-central1<code></td>
</tr>
    
<tr>
<td>GCP region. Can be any region, but it should be geographically close to the
on-premises gateway.</td>
<td><code>[REGION2]<code></td>
<td><code>us-west1<code></td>
</tr>

<tr>
<td>IP address range for the GCP VPC subnet (<code>vpn-subnet-1</code>)</td>
<td><code>[RANGE_1]<code></td>
<td><code>10.0.1.0/24<code></td>
</tr>
    
<tr>
<td>IP address range for the GCP VPC subnet (<code>vpn-subnet-2</code>)</td>
<td><code>[RANGE_2]<code></td>
<td><code>10.0.2.0/24<code></td>
</tr>

<tr>
<td>IP address range for the on-premises subnet. You will use this range when
creating rules for inbound traffic to GCP.</td>
<td><code>[IP_ON_PREM_SUBNET]<code></td>
<td><code>192.168.1.0/24<code></td>
</tr>

<tr>
<td>External static IP address for the first internet interface of <vendor
name><product-name></td>
<td><code>[ON_PREM_GW_IP_0]</code> </td>
<td>For example, <code>199.203.248.181</code></td>
</tr>

<tr>
<td>External static IP address for the second internet interface of <vendor
name><product-name></td>
<td><code>[ON_PREM_GW_IP_1]</code> </td>
<td>For example, <code>199.203.248.182</code></td>
</tr>

<tr>
<td>HA VPN Gateway</td>
<td><code>[GW_NAME]<code></td>
<td><code>ha-vpn-gw-a<code></td>
</tr>
    
<tr>
<td>Cloud Router name (for dynamic routing)</td>
<td><code>[ROUTER_NAME]<code></td>
<td><code>router-a<code></td>
</tr>

<tr>
<td>Google ASN</td>
<td><code>[GOOGLE_ASN]<code></td>
<td><code>65001<code></td>
</tr>

<tr>
<td>Peer ASN</td>
<td><code>[PEER_ASN]<code></td>
<td><code>65002<code></td>
</tr>

<tr>
<td>External VPN Gateway resource</td>
<td><code>[PEER_GW_NAME]<code></td>
<td><code>peer-gw<code></td>
</tr>

<tr>
<td>First VPN Tunnel</td>
<td><code>[TUNNEL_NAME_IF0]<code></td>
<td><code>tunnel-a-to-on-prem-if-0<code></td>
</tr>

<tr>
<td>Second VPN Tunnel</td>
<td><code>[TUNNEL_NAME_IF1]<code></td>
<td><code>tunnel-a-to-on-prem-if-1<code></td>
</tr>

<tr>
<td>First BGP peer interface</td>
<td><code>[ROUTER_INTERFACE_NAME_0]<code></td>
<td><code>bgp-peer-tunnel-a-to-on-prem-if-0<code></td>
</tr>

<tr>
<td>Second BGP peer interface</td>
<td><code>[ROUTER_INTERFACE_NAME_1]<code></td>
<td><code>bgp-peer-tunnel-a-to-on-prem-if-1<code></td>
</tr>
    
<tr>
<td>BGP interface netmask length</td>
<td><code>[MASK_LENGTH]<code></td>
<td><code>/30<code></td>
</tr>

</tbody>
</table>

## Configure the GCP side

This section covers how to configure HA VPN.

There are two ways to create HA VPN gateways on GCP: using the Google Cloud
Platform Console and using the
[gcloud command-line tool](https://cloud.google.com/sdk/).
This section describes how to perform the tasks using `gcloud`. 

### Initial tasks

Complete the following procedures before configuring a GCP HA VPN gateway and tunnel.

#### Create a custom VPC network

If you haven't already, create a VPC network. These example instructions 
create a [custom mode](https://cloud.google.com/vpc/docs/vpc#subnet-ranges) 
VPC network with one subnet in one region and another subnet in another region.

In the following commands, replace the options as noted below:

[NETWORK] assign a network name.
[SUBNET_MODE] set as custom.
[BGP_ROUTING_MODE] set as global.

    gcloud compute networks create [NETWORK] \
    --subnet-mode [SUBNET_MODE]  \
    --bgp-routing-mode [BGP_ROUTING_MODE]

The command output should look similar to the following example:

    gcloud compute networks create network-a \
    --subnet-mode custom  \
    --bgp-routing-mode global
    
#### Create subnets

Create two subnets in as follows:

    gcloud compute networks subnets create [SUBNET_NAME_1]  \
    --network NETWORK] \
    --region [REGION_1] \
    --range [RANGE_1]
    
    gcloud compute networks subnets create [SUBNET_NAME_2] \
    --network [NETWORK] \
    --region [REGION_2] \
    --range [RANGE_2]

The command output should look similar to the following example:

    gcloud compute networks subnets create subnet-a-central  \
    --network network-a \
    --region us-central1 \
    --range 10.0.1.0/24
    
    gcloud compute networks subnets create subnet-a-west \
    --network network-a \
    --region us-west1 \
    --range 10.0.2.0/24
    
### Create the HA VPN gateway

Complete the following command sequence to create the HA VPN gateway:

Create an HA VPN gateway. When the gateway is created, two external IP 
addresses are automatically allocated, one for each gateway interface.

    gcloud compute vpn-gateways create [GW_NAME] \
    --network [NETWORK] \
    --region [REGION]
    
The command output should look similar to the following example:
    
    gcloud compute vpn-gateways create ha-vpn-gw-a \
    --network network-a \
    --region us-central1
    
### Create Cloud Router

Complete the following command sequence to create a Cloud Router. In the following commands, replace the options as noted below:

Replace [ROUTER_NAME] with the name of the Cloud Router in the same region as the Cloud VPN gateway.
Replace [GOOGLE_ASN] with any private ASN (64512 - 65534, 4200000000 - 4294967294) that you are not already using in the peer network. The Google ASN is used for all BGP sessions on the same Cloud Router and it cannot be changed later.

    gcloud compute routers create [ROUTER_NAME] \
    --region [REGION] \
    --network [NETWORK] \
    --asn [GOOGLE_ASN]

The command output should look similar to the following example:

    gcloud compute routers create router-a \
    --region us-central1 \
    --network network-a \
    --asn 65001
    
### Create an External VPN Gateway resource

Create an external VPN gateway resource that provides information to GCP about your peer VPN gateway or gateways. Depending on the HA recommendations for your peer VPN gateway, you can create external VPN gateway resource for the following different types of on-premises VPN gateways:

1. Two separate peer VPN gateway devices where the two devices are redundant with each other and each device has its own public IP address.
1. A single peer VPN gateway that uses two separate interfaces, each with its own public IP address. For this kind of peer gateway, you can create a single external VPN gateway with two interfaces.
1. A single peer VPN gateway with a single public IP address.

This interop guide covers option 2 only. 

#### Create an External VPN Gateway resource for a single peer VPN gateway with two separate interfaces

    gcloud compute external-vpn-gateways create [PEER_GW_NAME] \
    --interfaces 0=[ON_PREM_GW_IP_0],1=[ON_PREM_GW_IP_1] \

The command output should look similar to the following example:
 
    gcloud compute external-vpn-gateways create peer-gw   \
     --interfaces 0=204.237.220.4,1=204.237.220.35 \

### Create two VPN tunnels, one for each interface on the HA VPN gateway

    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF0] \
    --peer-external-gateway [PEER_GW_NAME] \
    --peer-external-gateway-interface [PEER_EXT_GW_IF0]  \
    --region [REGION] \
    --ike-version [IKE_VERS] \
    --shared-secret [SHARED_SECRET] \
    --router [ROUTER_NAME] \
    --vpn-gateway [GW_NAME] \
    --interface [INT_NUM_0]
    
    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF1] \
    --peer-external-gateway [PEER_GW_NAME] \
    --peer-external-gateway-interface [PEER_EXT_GW_IF1] \
    --region [REGION] \
    --ike-version [IKE_VERS] \
    --shared-secret [SHARED_SECRET] \
    --router [ROUTER_NAME] \
    --vpn-gateway [GW_NAME] \
    --interface [INT_NUM_1]
    
The command output should look similar to the following example:
 
    gcloud compute vpn-tunnels create tunnel-a-to-on-prem-if-0 \
    --peer-external-gateway peer-gw \
    --peer-external-gateway-interface 0  \
    --region us-central1 \
    --ike-version 2 \
    --shared-secret mysharedsecret \
    --router router-a \
    --vpn-gateway ha-vpn-gw-a \
    --interface 0
    
    gcloud compute vpn-tunnels create tunnel-a-to-on-prem-if-1 \
    --peer-external-gateway peer-gw \
    --peer-external-gateway-interface 1  \
    --region us-central1 \
    --ike-version 2 \
    --shared-secret mysharedsecret \
    --router router-a \
    --vpn-gateway ha-vpn-gw-a \
    --interface 1
    
### Create Cloud Router interfaces and BGP peers
 
Create a Cloud Router BGP interface and BGP peer for each tunnel you previously
configured on the HA VPN gateway interfaces.

You can choose the automatic or manual configuration method of configuring BGP 
interfaces and BGP peers, this example is using automatic method.

For the first VPN tunnel

1.Add a new BGP interface to the Cloud Router.

    gcloud compute routers add-interface [ROUTER_NAME] \
    --interface-name [ROUTER_INTERFACE_NAME_0] \
    --mask-length [MASK_LENGTH] \
    --vpn-tunnel [TUNNEL_NAME_0] \
    --region [REGION]
    
The command output should look similar to the following example:
    
    gcloud compute routers add-interface router-a \
    --interface-name if-tunnel-a-to-on-prem-if-0 \
    --mask-length 30 \
    --vpn-tunnel tunnel-a-to-on-prem-if-0 \
    --region us-central1  

1.Add a BGP peer to the interface for the first tunnel.

    gcloud compute routers add-bgp-peer [ROUTER_NAME] \
    --peer-name [PEER_NAME] \
    --peer-asn [PEER_ASN] \
    --interface [ROUTER_INTERFACE_NAME_0] \
    --region [REGION] \
    
 The command output should look similar to the following example:   
 
    gcloud compute routers add-bgp-peer router-a \
    --peer-name peer-b \
    --peer-asn 65002 \
    --interface if-tunnel-a-to-on-prem-if-0 \
    --region us-central1 \

For the second VPN tunnel

1.Add a new BGP interface to the Cloud Router.

    gcloud compute routers add-interface [ROUTER_NAME] \
    --interface-name [ROUTER_INTERFACE_NAME_1] \
    --mask-length [MASK_LENGTH] \
    --vpn-tunnel [TUNNEL_NAME_1] \
    --region [REGION]

The command output should look similar to the following example:

    gcloud compute routers add-interface router-a \
    --interface-name if-tunnel-a-to-on-prem-if-1 \
    --mask-length 30 \
    --vpn-tunnel tunnel-a-to-on-prem-if-1 \
    --region us-central1
    
    
1.Add a BGP peer to the interface for the second tunnel.

    gcloud compute routers add-bgp-peer [ROUTER_NAME] \
    --peer-name [PEER_NAME] \
    --peer-asn [PEER_ASN] \
    --interface [ROUTER_INTERFACE_NAME_1] \
    --region [REGION] \

The command output should look similar to the following example:

    gcloud compute routers add-bgp-peer router-a \
    --peer-name peer-a \
    --peer-asn 65002 \
    --interface if-tunnel-a-to-on-prem-if-1 \
    --region us-central1 \
 
Verify the Cloud Router configuration
 
    gcloud compute routers get-status router-a \
     --region us-central1 \
     --format='flattened(result.bgpPeerStatus[].name,
       result.bgpPeerStatus[].ipAddress, result.bgpPeerStatus[].peerIpAddress)'
    
    result.bgpPeerStatus[0].ipAddress:     169.254.174.249
    result.bgpPeerStatus[0].name:          peer-a
    result.bgpPeerStatus[0].peerIpAddress: 169.254.174.250
    result.bgpPeerStatus[1].ipAddress:     169.254.36.85
    result.bgpPeerStatus[1].name:          peer-b
    result.bgpPeerStatus[1].peerIpAddress: 169.254.36.86

    gcloud compute routers describe [ROUTER_NAME] \
    --region [REGION]

## Configure the \<vendor-name>\<vendor product> side

<This section includes sample tasks that describe how to configure the
on-premises side of the VPN gateway configuration using <vendor-name>
equipment.>

### Creating the base network configuration

<The sample wording below assumes that you are showing the configuration steps
in the configuration code snippet below. If not, list the steps needed.>

Follow the procedure listed in the configuration code snippet below to create
the base Layer 3 network configuration of <vendor-name>. Note the following:

-  At least one internal-facing network interface is required in order to
connect to your on-premises network, and one external-facing interface is
required in order to connect to GCP.

```
<insert configuration code snippet here>
```

### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

<This section contains outlines of subsections for different aspects of
configuring IPsec and IKE on the vendor side. Fill in the sections that are
relevant to the current configuration, and remove any sections that don't
apply.>

### GCP-compatible settings for IPSec and IKE

#### Configure the IKE proposal and policy

<Insert the instructions for creating the IKE proposal and policy here. Below
are some examples of IKE algorithms to specify as part of the instructions.>

-  **Encryption algorithm**—< list required algorithms here>
-  **Integrity algorithm**—< list required algorithms here>
-  **Diffie-Hellman group—**< list required group here>

```
<insert configuration code snippet here>
```

#### Configure the IKEv2 keyring

< insert the instructions for creating the IKEv2 keyring here.>

```
<insert configuration code snippet here>
```

#### Configure the IKEv2 profile

< insert the instructions for creating the IKEv2 profile here.>

```
<insert configuration code snippet here>
```

#### Configure the IPsec security association (SA)

< insert the instructions for creating the IPsec SA here. Below is an example of
parameters to set.>

-  **IPsec SA replay window-size**—Set this to 1024, which is the
recommended value for <vendor-name><product-name>.

```
<insert configuration code snippet here>
```

#### Configure the IPsec transform set

< insert the instructions for creating the IPsec transform set here.>

```
<insert configuration code snippet here>
```

#### Configure the IPsec static virtual tunnel interface (SVTI)

< insert the instructions for creating the IPsec SVTI here. Below are some
examples of parameters to set.>

-  Adjust the maximum segment size (MSS) value of TCP packets going through a
router as discussed in
[MTU Considerations](https://cloud.google.com/vpn/docs/concepts/mtu-considerations)
for Cloud VPN.

```
<insert configuration code snippet here>
```

### Configuring the dynamic routing protocol

Follow the procedure in this section to configure dynamic routing for traffic
through the VPN tunnel or tunnels using the BGP routing protocol.

< insert the instructions for configuring dynamic routing here. Below are some
examples of parameters to set.>

BGP timers are adjusted to provide more rapid detection of outages.

To advertise additional prefixes to GCP, < insert instructions here>.

```
<insert configuration code snippet here>
```

### Saving the configuration

Follow the procedure in this section to save the on-premises configuration.

< insert the instructions for saving the configuration here.>

```
<insert configuration code snippet here>
```

### Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. For either side, make sure that the subnet that a machine or virtual machine is located in is being forwarded through the VPN tunnel.

First, create VMs on both sides of the tunnel. Make sure that you configure the
VMs on a subnet that will pass traffic through the VPN tunnel.

-  Instructions for creating virtual machines in Compute Engine are located
in the 
[Getting Started Guide](https://cloud.google.com/compute/docs/quickstart).
-  Instructions for creating virtual machine for <vendor-name><product-name>
platforms are located at <link here>.

After VMs have been deployed on both the GCP and <vendor-name><product-name>
platforms, you can use an ICMP echo (ping) test to test network connectivity
through the VPN tunnel.

On the GCP side, use the following instructions to test the connection to a
machine that's behind the on-premises gateway:

1. In the GCP Console,
[go to the VM Instances page](https://console.cloud.google.com/compute?).
1. Find the GCP virtual machine you created.
1. In the **Connect** column, click **SSH**. A browser window opens at the VM
command line.
1. Ping a machine that's behind the on-premises gateway.

<Insert any additional instructions for testing the VPN tunnels from the <vendor
name><product-name> here. For example, below is an example of a successful ping
from a Cisco ASR router to GCP.>

    cisco-asr#ping 172.16.100.2 source 10.0.200.1
    Type escape sequence to abort.
    Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:
    Packet sent with a source address of 10.0.200.1
    !!!!!
    Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms


## Troubleshooting IPsec on \<vendor-name>\<product-name>

For troubleshooting information, see the <vendor-name><product-name>
troubleshooting guide <add link>.

<Add details here about what kind of troubleshooting information can be found in
the <vendor-name><product-name> guide.>


## Reference documentation

You can refer to the following <vendor-name><product-name> documentation and
Cloud VPN documentation for additional information about both products.

### GCP documentation

To learn more about GCP networking, see the following documents:

-  [VPC Networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Creating Route-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-route-based-vpns)
-  [Creating Policy-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-policy-based-vpns)
-  [Advanced Cloud VPN Configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Terraform template for HA VPN](https://www.terraform.io/docs/providers/google/r/compute_ha_vpn_gateway.html)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### \<vendor-name>\<product-name> documentation

For more product information on <vendor-name><product-name>, see the following
<product-name> feature configuration guides and datasheets:

-  <guide name>
-  <guide name>

For common <vendor-name><product-name> error messages and debug commands, see
the following guides:

-  <guide name>
-  <guide name>
