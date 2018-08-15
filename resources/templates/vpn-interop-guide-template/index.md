---
title: Google Cloud VPN Interop Guide for [PRODUCT]
description: Describes how to build site-to-site IPsec VPNs between Cloud VPN on Google Cloud Platform (GCP) and  [VENDOR] [PRODUCT]
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

# Using Cloud VPN with <vendor-name><product-name>

Learn how to build site-to-site IPsec VPNs between
[Cloud VPN](https://cloud.google.com/vpn/docs/)on Google Cloud Platform (GCP) and
<vendor-name><product-name>.

<To see a finished version of this guide, see the
[Using Cloud VPN with Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page).>

<NOTE: Options or instructions are shown in angle brackets throughout this
template. Change or remove these items as needed.>

- [Google Cloud VPN Interop Guide](#google-cloud-vpn-interop-guide)
- [Introduction](#introduction)
- [Topology](#topology)
- [Product environment](#product-environment)
- [Before you begin](#before-you-begin)
    - [GCP account and project](#gcp-account-and-project)
    - [Permissions](#permissions)
    - [Licenses and modules](#licenses-and-modules)
- [Configure the GCP side](#configure-the-gcp-side)
    - [Initial tasks](#initial-tasks)
        - [Select a GCP project name](#select-a-gcp-project-name)
        - [Create a custom VPC network and subnet](#create-a-custom-vpc-network-and-subnet)
        - [Create the GCP external IP address](#create-the-gcp-external-ip-address)
    - [Configuring an IPsec VPN using dynamic routing](#configuring-an-ipsec-vpn-using-dynamic-routing)
        - [Configure the VPN gateway](#configure-the-vpn-gateway)
        - [Configure firewall rules](#configure-firewall-rules)
    - [Configuring route-based IPsec VPN using static routing](#configuring-route-based-ipsec-vpn-using-static-routing)
- [Configure the <vendor-name><vendor product> side](#configure-the-vendor-namevendor-product-side)
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
    - [Configuring static routing](#configuring-static-routing)
    - [Saving the configuration](#saving-the-configuration)
    - [Testing the configuration](#testing-the-configuration)
- [Advanced VPN configurations](#advanced-vpn-configurations)
    - [Configuring VPN redundancy](#configuring-vpn-redundancy)
        - [Configuring <product-name> dynamic route priority settings](#configuring-product-name-dynamic-route-priority-settings)
        - [Configuring <product-name> static route metrics](#configuring-product-name-static-route-metrics)
        - [Configuring GCP BGP route priority](#configuring-gcp-bgp-route-priority)
        - [Configuring GCP static route priority](#configuring-gcp-static-route-priority)
        - [Testing VPN redundancy on <vendor-name><device name>](#testing-vpn-redundancy-on-vendor-namedevice-name)
    - [Getting higher throughput](#getting-higher-throughput)
        - [Configuring GCP for higher throughput](#configuring-gcp-for-higher-throughput)
        - [Configuring <vendor-name><product-name> for higher throughput](#configuring-vendor-nameproduct-name-for-higher-throughput)
        - [Testing the higher-throughput configuration](#testing-the-higher-throughput-configuration)
- [Troubleshooting IPsec on <vendor-name><product-name>](#troubleshooting-ipsec-on-vendor-nameproduct-name)
- [Reference documentation](#reference-documentation)
    - [GCP documentation](#gcp-documentation)
    - [<vendor-name><product-name> documentation](#vendor-nameproduct-name-documentation)
- [Appendix: Using gcloud commands](#appendix-using-gcloud-commands)
    - [Running gcloud commands](#running-gcloud-commands)
    - [Configuration parameters and values](#configuration-parameters-and-values)
    - [Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters)
    - [Configuring an IPsec VPN using dynamic routing](#configuring-an-ipsec-vpn-using-dynamic-routing)
    - [Configuring route-based IPsec VPN using static routing](#configuring-route-based-ipsec-vpn-using-static-routing)

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
[Cloud VPN service](https://cloud.google.com/vpn/docs) on GCP.

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
-  A site-to-site IPsec VPN tunnel configuration using static routing.

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

This section covers how to configure Cloud VPN. The preferred approach is to use
dynamic routing with the BGP protocol, but this section also includes
instructions for configuring static routing.

There are two ways to create VPN gateways on GCP: using the Google Cloud
Platform Console and using the
[gcloud command-line tool](https://cloud.google.com/sdk/).
This section describes how to perform the tasks using the GCP Console. To see
the `gcloud` commands for performing these tasks, see the
[appendix](#appendix-using-gcloud-commands).

### Initial tasks

Complete the following procedures before configuring either a dynamic or static
GCP VPN gateway and tunnel.

#### Select a GCP project name

1. [Open the GCP Console](https://console.google.com).
1. At the top of the page, select the GCP project you want to use.

    **Note**: Make sure that you use the same GCP project for all of the GCP
    procedures in this guide.

#### Create a custom VPC network and subnet

1. In the GCP Console,
[go to the VPC Networks page](https://pantheon.corp.google.com/networking/networks/list).
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

#### Create the GCP external IP address

1.  In the GCP Console,
[go to the External IP addresses page](https://pantheon.corp.google.com/networking/addresses/list).

1. Click **Reserve Static Address**.
1. Populate the following fields for the Cloud VPN address:

-  **Name**—The name of the address, such as `vpn-test-static-ip`.
    Remember the name for later.
-  **Region**—The region where you want to locate the VPN gateway.
    Normally, this is the region that contains the instances you want to
    reach.

1. Click **Reserve**. You are returned to the **External IP addresses** page.
After a moment, the page displays the static external IP address that you
have created.

1. Make a note of the IP address that is created so that you can use it to
configure the VPN gateway later.

### Configuring an IPsec VPN using dynamic routing

For dynamic routing, you use
[Cloud Router](https://cloud.google.com/router/docs/concepts/overview)
to establish BGP sessions between GCP and the on-premises
<vendor-name><vendor product> equipment. We recommend dynamic routing over
static routing where possible, as discussed in the
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview) and
[Cloud VPN Network and Tunnel Routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing).

**Important:** Throughout these procedures, you assign names to entities like
the VPC network and subnet, IP address, and so on. Each time you assign a name,
make a note of it, because you often need to use those names in later
procedures.

#### Configure the VPN gateway

1. In the GCP Console, 
[go to the VPN page](https://console.cloud.google.com/networking/vpn/list).
1. Click **Create VPN connection**.
1. Populate the following fields for the gateway:

-  **Name**—The name of the VPN gateway. This name is displayed in the
    console and used in by the gcloud tool to reference the gateway. Use a
    name like `vpn-test-[VENDOR_NAME]-gw-1`, where `[VENDOR_NAME]` is a
    string that identifies the vendor.
-  **Network**—The VPC network that you created previously (for
    example,  `vpn-vendor-test-network`) that contains the instances that the
    VPN gateway will serve.
-  **Region**—The region where you want to locate the VPN gateway.
    Normally, this is the region that contains the instances you want to reach.
-  **IP address**—Select the 
    [static external IP address](#create-the-gcp-external-ip-address)
    (for example, `vpn-test-static-ip`) that you created for this gateway
    in the previous section.

1. Populate the fields for at least one tunnel:

-  **Name**—The name of the VPN tunnel, such as `vpn-test-tunnel1`.
-  **Remote peer IP address**—The public external IP address of the
    on-premises VPN gateway.
-  **IKE version**—`IKEv2` or `IKEv1`. IKEv2 is preferred, but IKEv1 is
    supported if it is the only supported IKE version that the on-premises
    gateway can use.
-  **Shared secret**—A character string used in establishing encryption
    for the tunnel. You must enter the same shared secret into both VPN
    gateways. For more information, see
    [Generating a Strong Pre-shared Key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).

1. Under **Routing options**, select the **Dynamic (BGP)** tab.
1. Under **Cloud router, **select** Create cloud router** and then populate
the following fields:

-  **Name**—The name of the Cloud Router. This name is displayed in
    the console. If you use `gcloud` command-line tool to perform VPN tasks,
    you use this name to reference the router. Example: `vpn-test-vendor-rtr.`
-  **Google ASN**—The 
    [private ASN](https://tools.ietf.org/html/rfc6996) (`64512–65534`,
    `4200000000–4294967294`) for the router you are configuring. It can be
    any private ASN that you are not already using. Example: `65002`.

1. Click **Save and continue**.
1. Next to **BGP session**, click the pencil icon and then populate the
following fields:

- **Name**—A name for the session, such as `bgp-peer1`.
-  **Peer ASN**—The [private ASN](https://tools.ietf.org/html/rfc6996)
    (`64512–65534`, `4200000000–4294967294`) for the on-premises VPN device
    you are configuring. It can be any private ASN that you are not already using.
    Example: `65001`.
- **Google BGP IP address**—A
    [link-local](https://wikipedia.org/wiki/Link-local_address) IP address
    that belongs to the same `/30` subnet in `169.254.0.0/16`. Example:
    `169.254.1.1`.
-  **Peer BGP IP address**—A link-local IP address for the on-premises
    peer. Example: `169.254.1.2`. For details, see
    [this explanation of dynamic routing for VPN tunnels in VPC networks](https://cloud.google.com/router/docs/concepts/overview#dynamic_routing_for_vpn_tunnels_in_vpc_networks).
-  **Remote network IP range**—The IP address range of the on-premises
    subnet on the other side of the tunnel from this gateway.
-  **Advertised route priority**–Configure this option if you want to
    configure redundant or high-throughput VPNs as described in 
    [advanced VPN configurations](#advanced-vpn-configurations). Note that if you
    don't need advanced VPN now, you will need to configure a new VPN tunnel
    later to support it. The advertised route priority is the base priority
    that Cloud Router uses when advertising the "to GCP" routes. For more
    information, see
    [Route metrics](https://cloud.google.com/router/docs/concepts/overview#route_metrics).
    Your on-premises VPN gateway imports these as MED values.

1. Click **Save and continue**.
1. Click **Create**. The GCP VPN gateway and the Cloud Router are initiated,
and the tunnel is initiated.

This procedure automatically creates a static route to the on-premises subnet as
well as forwarding rules for UDP ports 500 and 4500 and for ESP traffic. The VPN
gateways will not connect until you've configured the on-premises gateway and
created firewall rules in GCP to allow traffic through the tunnel between the
Cloud VPN  gateway and the on-premises gateway.

#### Configure firewall rules

Next, you configure GCP firewall rules to allow inbound traffic from the
on-premises network subnets. You must also configure the on-premises network
firewall to allow inbound traffic from your VPC subnet prefixes.

1. In the GCP Console,
[go to the GCP Firewall rules page](https://console.cloud.google.com/networking/firewalls).
1. Click **Create firewall rule**.
1. Populate the following fields:

1. **Name**—A name such as `vpnrule1`.
1. **VPC network**—The name of the VPC network that you created
    previously (for example,  `vpn-vendor-test-network`).
1. **Source filter**—A filter to apply your rule to specific sources of
    traffic. In this case, choose source IP ranges.
1. **Source IP ranges**—The on-premises IP ranges to accept from the
    on-premises VPN gateway.
1. **Allowed protocols and ports**—The string `tcp;udp;icmp`.

1. Click **Create**.

### Configuring route-based IPsec VPN using static routing

This section covers the steps for creating a GCP IPsec VPN using static routing.
Both route-based Cloud VPN and policy-based Cloud VPN use static routing.  For
information on how this works, see the 
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).

**Note**: Some steps in the procedure for using static routing are the same as
steps for using dynamic routing. Rather than repeat those steps in the following
procedure, the procedure links to earlier sections of this guide.

1. Complete the
[initial tasks](#initial-tasks)
for creating a VPN as described earlier in this guide.
1. Follow the steps for 
[setting up a GCP gateway for dynamic routing](#configuring-an-ipsec-vpn-using-dynamic-routing)
with these changes:

1. In the configuration for a tunnel, under **Routing options**,
    choose **route based**.
1. For **Remote network IP ranges**, set the IP address range or ranges
    of the on-premises network, which is the network on the other side of the
    tunnel from the Cloud VPN gateway you are currently configuring.

1. Click **Create** to create the gateway and initiate all tunnels. This step
automatically creates a network-wide route and the necessary forwarding
rules for the tunnel. The tunnels will not pass traffic until you've
configured the firewall rules.

1. Configure firewall rules to allow inbound traffic from the on-premises
network subnets. You must also configure the on-premises network firewall to
allow inbound traffic from your VPC subnet prefixes.

1. [Go to the Firewall rules page](https://console.cloud.google.com/networking/firewalls).
1. Click **Create firewall rule**.
1. Populate the following fields:
    -  **Name**—A name such as `vpnrule1`.
    -  **VPC network**—The name you used earlier for the VPC network,
        such as `vpn-vendor-test-network`.
    -  **Source filter**—A filter to apply your rule to specific
        sources of traffic. In this case, choose source IP ranges.
    -  **Source IP ranges**—The peer ranges to accept from the peer
        VPN gateway.
    -  **Allowed protocols and ports**—The string `tcp;udp;icmp`.

1. Click **Create**.

## Configure the <vendor-name><vendor product> side

<This section includes sample tasks that describe how to configure the
on-premises side of the VPN gateway configuration using <vendor-name>
equipment.>

<For an example of how to fill in the instructions and parameters, see the
[Cisco ASR1000 section](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#configuration--cisco-asr-1000)
of
[the VPN Interop guide for Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page).
For each set of instructions, explain what purpose the configuration setting
serves.>

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

Configuring the vendor side of the VPN network requires you to use IPsec and IKE
settings that are compatible with the GCP side of the network. The following
table lists settings and information about values compatible with GCP VPN.
Use these settings for the procedures in the subsections that follow.

<Not all of the settings in the following table are applicable to all vendor
setups; use the settings that apply to your configuration. Remove the settings
in the table that do not apply to current configuration.>

**Note**: The <vendor-name><product-name> solution might have its own
specifications for replay window size.

<table>
<thead>
<tr>
<th><strong>Setting</strong></th>
<th><strong>Description or value</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>IPsec Mode</td>
<td>ESP+Auth Tunnel mode (Site-to-Site)</td>
</tr>
<tr>
<td>Auth Protocol</td>
<td><code>psk</code></td>
</tr>
<tr>
<td>Shared Secret</td>
<td>Also known as an IKE pre-shared key. Choose a strong password by following
<a
href="https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key">these
guidelines</a>. The shared secret is very sensitive as it allows access
into your network.</td>
</tr>
<tr>
<td>Start</td>
<td><code>auto</code> (on-premises device should automatically restart the
connection if it drops)</td>
</tr>
<tr>
<td>PFS (Perfect Forward Secrecy)</td>
<td>on</td>
</tr>
<tr>
<td>DPD (Dead Peer Detection)</td>
<td>Recommended: <code>Aggressive</code>. DPD detects when the Cloud VPN
restarts and routes traffic using alternate tunnels.</td>
</tr>
<tr>
<td>INITIAL_CONTACT (sometimes called <i>uniqueids</i>)</td>
<td>Recommended: <code>on</code> (sometimes called <code>restart</code>). The
purpose is to detect restarts faster so that perceived downtime is
reduced.</td>
</tr>
<tr>
<td>TSi (Traffic Selector - Initiator)</td>
<td>Subnet networks: the ranges specified by the GCP local traffic selector. If
no local traffic selector range was specified because the VPN is in an auto-mode
VPC network and is announcing only the gateway's subnet, that subnet range is
used. <br>
<br>
Legacy networks: the range of the network.</td>
</tr>
<tr>
<td>TSr (Traffic Selector - Responder)</td>
<td>IKEv2: The destination ranges of all of the routes that have the next hop
VPN tunnel set to this tunnel on the GCP side.<br>
<br>
IKEv1: Arbitrarily, the destination range of one of the routes that has the
next hop VPN tunnel set to this tunnel on the GCP side.</td>
</tr>
<tr>
<td>MTU</td>
<td>The MTU of the on-premises VPN device must be set to 1460 or lower. ESP
packets leaving the device must not exceed 1460 bytes. You must enable
prefragmentation on your device, which means that packets must be
fragmented first, then encapsulated. For more information, see <a
href="https://cloud.google.com/vpn/docs/concepts/mtu-considerations">Maximum
Transmission Unit (MTU) considerations</a>.</td>
</tr>
<tr>
<td>IKE ciphers</td>
<td>For details about IKE ciphers for IKEv1 or IKEv2 supported by GCP,
including the additional ciphers for PFS, see <a
href="https://cloud.google.com/vpn/docs/concepts/supported-ike-ciphers">Supported
IKE Ciphers</a>.</td>
</tr>
</tbody>
</table>

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

### Configuring static routing

Follow the procedure in this section to configure static routing of traffic to
the GCP network through the VPN tunnel interface.

```
<insert configuration code snippet here>
```

For more recommendations about on-premises routing configurations, see
[GCP Best Practices](https://cloud.google.com/router/docs/resources/best-practices).

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

## Advanced VPN configurations

This section covers how to configure redundant on-premises VPN gateways and how
to get higher throughput through VPN tunnels.

### Configuring VPN redundancy

Using redundant on-premises VPN gateways ensures continuous availability when a
tunnel fails. The article
[Redundancy and High-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns)
in the Cloud VPN documentation provides configuration guidelines for both GCP
and on-premises VPN gateways, including guidance on setting route priorities for
redundant gateways. <link to the <vendor-name><product-name> reference guide for
configuring redundancy on the vendor product.>

This section contains procedures for configuring route priority settings on
<vendor-name><product-name> and GCP. The GCP instructions assume you have built
each GCP gateway in a set of redundant gateways as described in the
[dynamic routing section](#configuring-an-ipsec-vpn-using-dynamic-routing)
and configured the **Advertised route priority** field when you
configured the VPN gateway. If you didn't do this, you will need to
[create a new tunnel and BGP session for the gateways involved and configure
the Advertised route priority field](#configure-the-vpn-gateway)
as described in the following sections.

**Note**: Some of the procedures in this section use `gcloud` commands. For
information about using `gcloud` commands, and about setting environment
variables for parameter values such as the GCP network name, see the
[appendix](#appendix-using-gcloud-commands).

#### Configuring <product-name> dynamic route priority settings

< insert the instructions for configuring BGP route priority settings on the
<vendor-name><product-name> device here. Indicate whether the preferred route is
a higher or lower priority number.>

```
<insert configuration code snippet showing the existing BGP route configuration here>
```

< insert the instructions for configuring BGP multi-exit discriminator (MED)
values on the <vendor-name><product-name> device or service here.>

```
<insert configuration code snippet showing BGP MED values here>
```

#### Configuring <product-name> static route metrics

< insert the instructions for configuring a static route on the
<vendor-name><product-name> device or service here. State whether the metric for
the preferred route is a higher or lower number.>

```
<insert configuration code snippet here>
```

#### Configuring GCP BGP route priority

With GCP dynamic routing, you can configure advertised route priority. For
details, see the
[Cloud Router overview](https://cloud.google.com/router/docs/concepts/overview)
and the
[Cloud Router API documentation](https://cloud.google.com/sdk/gcloud/reference/compute/routers/update-bgp-peer).
If you have a preferred route announced to the on-premises side of the network,
BGP will prefer the higher priority on-premises route.

You can set BGP route priority using [the console](#configure-the-vpn-gateway)
or the following `gcloud` command. Note the following:

-  Make sure you've set environment variables as described in the
[appendix](#appendix-using-gcloud-commands).
-  For `[PEER_ASN]`, use a [private ASN](https://tools.ietf.org/html/rfc6996)
value (`64512–65534`, `4200000000–4294967294`) that's not already in use,
such as `65001`.
-  For `[PRIORITY]`, use an appropriate value, such as `2000`.
-  For `[PEER-IP-ADDRESS]`, use an address in the range `169.254.n.n`.

```
gcloud compute --project $PROJECT_NAME routers add-bgp-peer \
    $CLOUD_ROUTER_NAME \
    --peer-name $BGP_SESSION_NAME \
    --interface $BGP_IF \
    --peer-ip-address [PEER-IP-ADDRESS] \
    --peer-asn [PEER_ASN] \
    --region $REGION \
    --advertised-route-priority=[PRIORITY]
```

#### Configuring GCP static route priority

When you use static routing, GCP gives you an option to customize route priority
if there are multiple routes with the same prefix length. To enable symmetric
traffic flow, make sure that you set the priority of your secondary GCP tunnel
to a higher value than the primary tunnel. (The default priority is 1000.) To
define the route priority, run the following command. Note the following:

-  Make sure you've set environment variables as described in the
[appendix](#appendix-using-gcloud-commands).
-  For `[PRIORITY]` use an appropriate priority value, such as `2000`.


```
gcloud compute routes create $ROUTE_NAME \
    --project $PROJECT_NAME \
    --network $VPC_NETWORK_NAME \
    --next-hop-vpn-tunnel $VPN_TUNNEL_1 \
    --next-hop-vpn-tunnel-region $REGION \
    --destination-range $IP_ON_PREM_SUBNET \
    --priority=[PRIORITY]
```

#### Testing VPN redundancy on <vendor-name><device name>

< insert the instructions for testing VPN redundancy on the <vendor-name><product
name>  device here. Below is example testing output. Replace it with the output
for the <vendor-name><product-name> device.>

```
cisco-asr#sh ip bgp 172.16.100.0
    BGP routing table entry for 172.16.100.0/24, version 690
    Paths: (3 available, best #1, table default)
    Multipath: eBGP
    Flag: 0x404200
    Advertised to update-groups:
        18
    Refresh Epoch 1
    65002
        169.254.0.1 from 169.254.0.1 (169.254.0.1)
        Origin incomplete, metric 100, localpref 2000, valid, external, best
        rx pathid: 0, tx pathid: 0x0
    Refresh Epoch 1
    65002, (received-only)
        169.254.0.1 from 169.254.0.1 (169.254.0.1)
        Origin incomplete, metric 100, localpref 100, valid, external
        rx pathid: 0, tx pathid: 0
    Refresh Epoch 1
    65002
        169.254.0.57 from 169.254.0.57 (169.254.0.1)
        Origin incomplete, metric 100, localpref 100, valid, external
        rx pathid: 0, tx pathid: 0

    cisco-asr#sh ip cef 172.16.100.0
    172.16.100.0/24
    nexthop 169.254.0.1 Tunnel1
```

### Getting higher throughput

Each Cloud VPN tunnel can support up to 3 Gbps when the tunnel traffic traverses
a direct peering link, or 1.5 Gbps when the tunnel traffic traverses the public
internet. For more information, see
[Redundant and High Throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns).

#### Configuring GCP for higher throughput

To increase throughput, add multiple Cloud VPN gateways in the same region to
load balance the traffic across the tunnels. For more information, see the 
[Topology](#topology) section in this guide.

GCP performs ECMP routing by default, so no additional configuration is required
apart from creating the number of tunnels that meet your throughput
requirements. You can either use a single VPN gateway to create multiple
tunnels, or you can create a separate VPN gateway for each tunnel.

Actual tunnel throughput can vary depending on the following factors:

-  **Network capacity** between the GCP and on-premises VPN gateways.
-  **Capabilities of the on-premises VPN device**. See your device's
documentation for more information.
-  **Packet size.** Because processing happens on a per-packet basis, traffic
with a significant percentage of smaller packets can reduce overall throughput.
-  **[High Round Trip Time (RTT)](https://en.wikipedia.org/wiki/Round-trip_delay_time)
and packet loss rates.** This can greatly reduce throughput for TCP.

#### Configuring <vendor-name><product-name> for higher throughput

<Describe how <vendor-name><product-name> does ECMP. Also describe how many
equal cost paths the device can handle.>

```
<insert configuration code snippet for existing code here>
```

#### Testing the higher-throughput configuration

You can test the IPsec tunnel from GCP with the instructions in the
[Building High-throughput VPNs](https://cloud-dot-devsite.googleplex.com/solutions/building-high-throughput-vpns)
guide.

You can test the IPsec tunnel from the on-premises VPN device by using ICMP to
ping a VM host on GCP

<Add details here about how to initiate a ping from <vendor-name><product-name>
similar to those mentioned previously.>

```
<insert ping output from on-premises device here>
```

## Troubleshooting IPsec on <vendor-name><product-name>

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
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### <vendor-name><product-name> documentation

For more product information on <vendor-name><product-name>, see the following
<product-name> feature configuration guides and datasheets:

-  <guide name>
-  <guide name>

For common <vendor-name><product-name> error messages and debug commands, see
the following guides:

-  <guide name>
-  <guide name>

## Appendix: Using gcloud commands

The instructions in this guide focus on using the GCP Console. However, you can
perform many of the tasks for the GPC side of the VPN configuration by using the
[gcloud command-line tool](https://cloud.google.com/sdk/gcloud/). Using `gcloud`
commands can be faster and more convenient if you're comfortable with using a
command-line interface.

### Running gcloud commands

You can run `gcloud` commands on your local computer by installing the [Cloud
SDK](https://cloud.google.com/sdk/). Alternatively, you can run `gcloud`
commands in [Cloud Shell](https://cloud.google.com/shell/), a browser-based
command line. If you use Cloud Shell, you don't need to install the SDK on your
own computer, and you don't need to set up authentication.

**Note**: The `gcloud` commands presented in this guide assume you are working
in a Linux environment. (Cloud Shell is a Linux environment.)

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
<td><code>[VPC_NETWORK_NAME]<code></td>
<td><code>vpn-vendor-test-network<code></td>
</tr>

<tr>
<td>Subnet on the GCP VPC network (for example, <code>vpn-vendor-test-network</code>)</td>
<td><code>[VPC_SUBNET_NAME]<code></td>
<td><code>vpn-subnet-1<code></td>
</tr>

<tr>
<td>GCP region. Can be any region, but it should be geographically close to the
on-premises gateway.</td>
<td><code>[REGION]<code></td>
<td><code>us-east1<code></td>
</tr>

<tr>
<td>Pre-existing external static IP address that you configure for the internet
side of the Cloud VPN gateway.</td>
<td><code>[STATIC_EXTERNAL_IP]<code></td>
<td><code>vpn-test-static-ip<code></td>
</tr>

<tr>
<td>IP address range for the GCP VPC subnet (<code>vpn-subnet-1</code>)</td>
<td><code>[SUBNET_IP]<code></td>
<td><code>172.16.100.0/24<code></td>
</tr>

<tr>
<td>IP address range for the on-premises subnet. You will use this range when
creating rules for inbound traffic to GCP.</td>
<td><code>[IP_ON_PREM_SUBNET]<code></td>
<td><code>10.0.0.0/8<code></td>
</tr>

<tr>
<td>External static IP address for the internet interface of <vendor
name><product-name></td>
<td><code>[CUST_GW_EXT_IP]</code> </td>
<td>For example, <code>199.203.248.181</code></td>
</tr>

<tr>
<td>Cloud Router name (for dynamic routing)</td>
<td><code>[CLOUD_ROUTER_NAME]<code></td>
<td><code>vpn-test-vendor-rtr<code></td>
</tr>

<tr>
<td>BGP interface name</td>
<td><code>[BGP_IF]<code></td>
<td><code>if-1<code></td>
</tr>

<tr>
<td>BGP session name (for dynamic routing)</td>
<td><code>[BGP_SESSION_NAME]<code></td>
<td><code>bgp-peer1<code></td>
</tr>

<tr>
<td>The name for the first GCP VPN gateway.</td>
<td><code>[VPN_GATEWAY_1]<code></td>
<td><code>vpn-test-[VENDOR_NAME]-gw-1</code>, where <code>[VENDOR_ NAME]</code>
is the <code>[VENDOR_NAME]</code> string</td>
</tr>

<tr>
<td>The name for the first VPN tunnel for
<code>vpn-test-[VENDOR_NAME]-gw-1</code></td>
<td><code>[VPN_TUNNEL_1]<code></td>
<td><code>vpn-test-tunnel1<code></td>
</tr>

<tr>
<td>The name of a firewall rule that allows traffic between the on-premises
network and GCP VPC networks</td>
<td><code>[VPN_RULE]<code></td>
<td><code>vpnrule1<code></td>
</tr>

<tr>
<td>The name for the <a
href="https://cloud.google.com/sdk/gcloud/reference/compute/routes/create">static
route</a> used to forward traffic to the on-premises network.<br>
<br>
<strong>Note</strong>: You need this value only if you are creating a VPN
using a static route.</td>
<td><code>[ROUTE_NAME]<code>

</td>
<td><code>vpn-static-route<code>

</td>
</tr>
<tr>
<td>The name for the forwarding rule for the <a
href="https://wikipedia.org/wiki/IPsec#Encapsulating_Security_Payload">ESP
protocol</a></td>
<td><code>[FWD_RULE_ESP]<code></td>
<td><code>fr-esp<code></td>
</tr>

<tr>
<td>The name for the forwarding rule for the <a
href="https://wikipedia.org/wiki/User_Datagram_Protocol">UDP
protocol</a>, port 500</td>
<td><code>[FWD_RULE_UDP_500]<code></td>
<td><code>fr-udp500<code></td>
</tr>

<tr>
<td>The name for the forwarding rule for the UDP protocol, port 4500</td>
<td><code>[FWD_RULE_UDP_4500]<code></td>
<td><code>fr-udp4500<code></td>
</tr>

</tbody>
</table>

### Setting environment variables for gcloud command parameters

To make it easier to run `gcloud` commands that contain parameters, you can
create environment variables to hold the values you need, such as your project
name, the names of subnets and forwarding rules, and so on. The `gcloud`
commands presented in this section reference variables that contain your
values.

To set the environment variables, run the following commands at the command line
_before_ you run `gcloud` commands, substituting your own values for all the
placeholders in square brackets, such as `[PROJECT_NAME]`, `[VPC_NETWORK_NAME]`,
and `[SUBNET_IP]`. If you don't know what values to use for the placeholders,
use the example values from the parameters table in the preceding section.

```
export PROJECT_NAME=[PROJECT_NAME]
export REGION=[REGION]
export VPC_SUBNET_NAME=[VPC_SUBNET_NAME]
export VPC_NETWORK_NAME=[VPC_NETWORK_NAME]
export FWD_RULE_ESP=[FWD_RULE_ESP]
export FWD_RULE_UDP_500=[FWD_RULE_UDP_500]
export FWD_RULE_UDP_4500=[FWD_RULE_UDP_4500]
export SUBNET_IP=[SUBNET_IP]
export VPN_GATEWAY_1=[VPN_GATEWAY_1]
export STATIC_EXTERNAL_IP=[STATIC_EXTERNAL_IP]
export VPN_RULE=[VPN_RULE]
export IP_ON_PREM_SUBNET=[IP_ON_PREM_SUBNET]
export CLOUD_ROUTER_NAME=[CLOUD_ROUTER_NAME]
export BGP_IF=[BGP_IF]
export BGP_SESSION_NAME=[BGP_SESSION_NAME]
export VPN_TUNNEL_1=[VPN_TUNNEL_1]
export CUST_GW_EXT_IP=[CUST_GW_EXT_IP]
export ROUTE_NAME=[ROUTE_NAME]
```

### Configuring an IPsec VPN using dynamic routing

This section describes how to use the `gcloud` command-line tool to configure
IPsec VPN with dynamic routing. To perform the same task using the GCP Console,
see
[Configuring IPsec VPN using dynamic routing](##configuring-an-ipsec-vpn-using-dynamic-routing)
earlier in this guide.

**Note**: Before you run the `gcloud` commands in this section, make sure that
you've set the variables as described earlier under
[Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters).

1. Create a custom VPC network.

    ```
    gcloud compute networks create $VPC_NETWORK_NAME \
        --project $PROJECT_NAME \
        --subnet-mode custom
    ```

1. Create a subnet on that network. Make sure there is no conflict with your
local network IP address range or any other configured subnets.

    ```
    gcloud compute networks subnets create $VPC_SUBNET_NAME \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --region $REGION \
        --range $SUBNET_IP
    ``` 

1. Create a GCP VPN gateway in the region you are using.

    ```
    gcloud compute target-vpn-gateways create $VPN_GATEWAY_1 \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --region $REGION
    ```

    This step creates an unconfigured VPN gateway in your VPC network.

1. Reserve a static IP address in the VPC network and region where you
created the VPN gateway. Make a note of the created address for use in
future steps.

    ```
    gcloud compute addresses create $STATIC_EXTERNAL_IP \
        --project $PROJECT_NAME \
        --region $REGION
    ```

1. Create three forwarding rules, one each to forward ESP, IKE, and NAT-T
traffic to the Cloud VPN gateway. Note the following:

    -  For the `[STATIC_IP_ADDRESS]` in the following commands, use the static
    IP address that you reserved in the previous step.

    ```
    gcloud compute forwarding-rules create $FWD_RULE_ESP \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol ESP \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --address [STATIC_IP_ADDRESS]

    gcloud compute forwarding-rules create $FWD_RULE_UDP_500 \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol UDP \
        --ports 500 \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --address [STATIC_IP_ADDRESS]

    gcloud compute forwarding-rules create $FWD_RULE_UDP_4500 \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol UDP \
        --ports 4500 \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --address [STATIC_IP_ADDRESS]
    ```

1. Create a [Cloud Router](https://cloud.google.com/compute/docs/cloudrouter).
Note the following:

    -  For `[PRIVATE_ASN]`, use the
    [private ASN](https://tools.ietf.org/html/rfc6996) (`64512–65534`,
    `4200000000–4294967294`) for the router you are configuring. It can be any
    private ASN you are not already using, such as `65001`.

    ```
    gcloud compute routers create $CLOUD_ROUTER_NAME \
        --project $PROJECT_NAME \
        --region $REGION \
        --network $VPC_NETWORK_NAME \
        --asn [PRIVATE_ASN]
    ```

1. Create a VPN tunnel on the Cloud VPN Gateway that points to the external
IP address of your on-premises VPN gateway. Note the following:

    - Set the IKE version. The following command sets the IKE version to 2,
    which is the default, preferred IKE version. If you need to set it to 1,
    use `--ike-version 1`.
    - For `[SHARED_SECRET]`, supply the shared secret. For details, see
    [Generating a Strong Pre-shared Key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).


    ```
    gcloud compute vpn-tunnels create $VPN_TUNNEL_1 \
        --project $PROJECT_NAME \
        --region $REGION \
        --ike-version 2 \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --router $CLOUD_ROUTER_NAME \
        --peer-address $CUST_GW_EXT_IP \
        --shared-secret [SHARED_SECRET]
    ```

    After you run this command, resources are allocated for this VPN tunnel, but the
    tunnel is not yet passing traffic.

1. Update the Cloud Router configuration to add a virtual interface
(`--interface-name`) for the BGP peer. Note the following:

    -  The recommended netmask length is `30`.
    -  Make sure each tunnel has a unique pair of IP addresses. Alternatively,
    you can leave out `--ip-address` and `--mask-length`. In that case, the
    addresses will be automatically generated.
    -  For `[BGP_IF_IP_ADDRESS]`, use a
    [link-local](https://wikipedia.org/wiki/Link-local_address) IP address
    belonging to the IP address range `169.254.0.0/16`. The address must belong
    to the same subnet as the interface address of the peer router.

    ```
    gcloud compute routers add-interface $CLOUD_ROUTER_NAME \
        --project $PROJECT_NAME \
        --interface-name $BGP_IF \
        --mask-length 30 \
        --vpn-tunnel $VPN_TUNNEL_1 \
        --region $REGION \
        --ip-address [BGP_IF_IP_ADDRESS]
    ```

1. Update the Cloud Router config to add the BGP peer to the interface. Note
the following:

    -  For `[PEER_ASN]`, use your public ASN or any
    [private ASN](https://tools.ietf.org/html/rfc6996) (`64512–65534`,
    `4200000000–4294967294`) that you are not already using in the peer network.
        For example, you can use `65001`.
    -  For `[PEER_IP_ADDRESS]`, use a
    [link-local](https://wikipedia.org/wiki/Link-local_address) IP address
    belonging to the IP address range `169.254.0.0/16`. It must belong to the
    same subnet as the GCP-side interface.
    -  If you left out the IP address and mask length in the previous step, leave
    out the peer IP address in this command.
    -  Make sure each tunnel has a unique pair of IPs.

    ```
    gcloud compute routers add-bgp-peer $CLOUD_ROUTER_NAME \
        --project $PROJECT_NAME \
        --region $REGION \
        --peer-name $BGP_SESSION_NAME \
        --interface $BGP_IF \
        --peer-asn [PEER_ASN] \
        --peer-ip-address [PEER_IP_ADDRESS]
    ```

1. View details of the configured Cloud Router in order to confirm your
settings.

    ```
    gcloud compute routers describe $CLOUD_ROUTER_NAME \
        --project $PROJECT_NAME \
        --region $REGION
    ```

    The output for a configured Cloud Router will look like the following example.
    (This output shows sample values—your output will include an ID unique to you,
    your project name, the region you've selected, and so on.)

    ```
    Output:
    bgp:
    advertiseMode: DEFAULT
    asn: 65001
    creationTimestamp: '2018-04-23T09:54:46.633-07:00'
    description: ''
    id: '2327390853769965881'
    kind: compute#router
    name: vpn-test-[VENDOR_NAME]
    network: https://www.googleapis.com/compute/v1/projects/vpn-guide/global/networks/default
    region: https://www.googleapis.com/compute/v1/projects/vpn-guide/regions/us-east1
    selfLink: https://www.googleapis.com/compute/v1/projects/vpn-guide/regions/us-east1/routers/vpn-test-[VENDOR_NAME]
    ```

1. Create GCP firewall rules to allow inbound traffic from the on-premises
network subnets and from your VPC subnet prefixes.

    ```
    gcloud compute firewall-rules create $VPN_RULE \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --allow tcp,udp,icmp \
        --source-ranges $IP_ON_PREM_SUBNET
    ```

### Configuring route-based IPsec VPN using static routing

This section describes how to use the `gcloud` command-line tool to configure
IPsec VPN with static routing. To perform the same task using the GPC Console,
see
[Configuring IPsec VPN using static routing](#configuring-route-based-ipsec-vpn-using-static-routing)
earlier in this guide.

The procedure suggests creating a custom VPC network. This is preferred over
using an auto-created network. For more information, see
[Networks and Tunnel Routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#network-types)
in the Cloud VPN documentation.

**Note**: Before you run the `gcloud` commands in this section, make sure that
you've set the variables as described earlier under
[Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters).

1. Create a custom VPC network. Make sure there is no conflict with your
local network IP address range. Note the following:

    -  For `[RANGE]`, substitute an appropriate CIDR range, such as
    `172.16.100.0/24`.

    ```
    gcloud compute networks create $VPC_NETWORK_NAME \
        --project $PROJECT_NAME \
        --subnet-mode custom

    gcloud compute networks subnets create $VPC_SUBNET_NAME \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --region $REGION \
        --range [RANGE]
    ```

1. Create a VPN gateway in the region you are using. Normally, this is the
region that contains the instances you want to reach.

    ```
    gcloud compute target-vpn-gateways create $VPN_GATEWAY_1 \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --region $REGION
    ```

This step creates an unconfigured VPN gateway in your GCP VPC network.

1. Reserve a static IP address in the VPC network and region where you
created the VPN gateway. Make a note of the address that is created for use
in future steps.

    ```
    gcloud compute addresses create $STATIC_EXTERNAL_IP \
        --project $PROJECT_NAME \
        --region $REGION
    ```

1. Create three forwarding rules, one each to forward ESP, IKE, and NAT-T
traffic to the Cloud VPN gateway. Note the following:

    -  For `[STATIC_IP_ADDRESS]`, use the static IP address that you reserved in
    the previous step.

    ```
    gcloud compute forwarding-rules create $FWD_RULE_ESP \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol ESP \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --address [STATIC_IP_ADDRESS]

    gcloud compute forwarding-rules create $FWD_RULE_UDP_500 \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol UDP \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --ports 500 \
        --address [STATIC_IP_ADDRESS]

    gcloud compute forwarding-rules create $FWD_RULE_UDP_4500 \
        --project $PROJECT_NAME \
        --region $REGION \
        --ip-protocol UDP \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --ports 4500 \
        --address [STATIC_IP_ADDRESS]
    ``` 

1. Create a VPN tunnel on the Cloud VPN Gateway that points to the external
IP address of your on-premises VPN gateway. Note the following:

-  Set the IKE version. The following command sets the IKE version to
    2, which is the default, preferred IKE version. If you need to set it to
    1, use `--ike-version 1`.
-  For `[SHARED_SECRET]`, supply the shared secret.  For details, see
    [Generating a Strong Pre-shared Key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).
-  For `[LOCAL_TRAFFIC_SELECTOR_IP]`, supply an IP address range, like
    `172.16.100.0/24`,  that will be accessed on the GCP side of the  tunnel,
    as described in
    [Traffic selectors](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#static-routing-networks)
    in the GCP VPN networking documentation.

    ```
    gcloud compute vpn-tunnels create $VPN_TUNNEL_1 \
        --project $PROJECT_NAME \
        --peer-address $CUST_GW_EXT_IP \
        --region $REGION \
        --ike-version 2 \
        --shared-secret [SHARED_SECRET] \
        --target-vpn-gateway $VPN_GATEWAY_1 \
        --local-traffic-selector [LOCAL_TRAFFIC_SELECTOR_IP]
    ``` 

    After you run this command, resources are allocated for this VPN tunnel, but it
    is not yet passing traffic.

1. Use a
[static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create)
to forward traffic to the destination range of IP addresses in your
    on-premises network. The region must be the
    same region as for the VPN tunnel.

    ```
    gcloud compute routes create $ROUTE_NAME \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --next-hop-vpn-tunnel $VPN_TUNNEL_1 \
        --next-hop-vpn-tunnel-region $REGION \
        --destination-range $IP_ON_PREM_SUBNET
    ```

1. If you want to pass traffic from multiple subnets through the VPN tunnel,
repeat the previous step to forward the IP address of each of the subnets.

1. Create firewall rules to allow traffic between the on-premises network and
GCP VPC networks.

    ```
    gcloud compute firewall-rules create $VPN_RULE \
        --project $PROJECT_NAME \
        --network $VPC_NETWORK_NAME \
        --allow tcp,udp,icmp \
        --source-ranges $IP_ON_PREM_SUBNET
    ```
