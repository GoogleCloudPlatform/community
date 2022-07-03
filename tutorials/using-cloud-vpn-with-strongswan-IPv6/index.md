---
title: How to set up a VPN between strongSwan and Cloud VPN with IPv6
description: Learn how to build a site-to-site IPsec VPN between strongSwan and Cloud VPN.
author: yinghli
tags: Compute Engine, Cloud VPN, strongSwan, bird
date_published: 2022-07-03
---


IPv6 is being developed across multiple tracks for GCP. This doc will provides an step-by-step of how IPv6 hybrid connectivity will be enabled for IPSec VPN. This guide walks you through how to configure [strongSwan](https://www.strongswan.org/) and [BIRD](https://bird.network.cz/) for integration with [Google Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview). 

# Environment overview

The equipment used in the creation of this guide is as follows:

* Vendor: strongSwan
* Software release: 5.7.2 on Debian 10

* Vendor: BIRD
* Software release: 2.0.7 on Debian 10

# Topology

The topology outlined by this guide is a basic site-to-site IPsec VPN tunnel
configuration using the referenced device:

# Configuring a dynamic (BGP) IPsec VPN tunnel with strongSwan and BIRD

In this example, a dynamic BGP-based VPN uses a VTI interface. This guide is based
on the official [strongSwan wiki](https://wiki.strongswan.org/projects/strongswan/wiki/RouteBasedVPN#VTI-Devices-on-Linux).

The following sample environment walks you through set up of a route-based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

This guide assumes that you have [BIRD](https://bird.network.cz/) 2.0.7 installed on your strongSwan server.

**Cloud VPN**

|Name | Value|
-----|------
|Cloud VPN(external IP)|`35.242.38.248`|
|VPC IPv4 CIDR|`172.17.0.0/16`|
|VPC IPv6 CIDR|`2600:2d00:4031:29c6::/64`|
|BGP IPv4 GCP|`169.254.52.201`|
|BGP IPv4 GCP|`2600:2d00:0:3:0:0:0:74b9`|
|GCP-ASN|`65001`|

**strongSwan**

|Name | Value|
-----|------
|External IP|`13.213.47.43`|
|IPv4 CIDR Behind strongSwan|`172.31.16.0/20`|
|IPv6 CIDR Behind strongSwan|`3000::/64`|
|IPv4 TUN-INSIDE- SW|`169.254.52.202`|
|IPv6 TUN-INSIDE- SW|`2600:2d00:0:3:0:0:0:74ba`|
|strongSwan ASN|`65002`|

## Configuration of Google Cloud

With a IPv6 enabled route-based VPN, you need to IKEv2 and dynamic routing. This example uses
dynamic (BGP) routing. [Cloud Router](https://cloud.google.com/network-connectivity/docs/router/) is used to establish
IPv4 BGP sessions between the two peers and exchange both IPv4 and IPv6 unicast address family route.

### Configuring a cloud router

**Step 1**: In the Cloud Console, select **Networking** > [**Cloud Routers**](https://console.cloud.google.com/hybrid/routers/list) > **Create Router**.

**Step 2**: Enter the following parameters, and click **Create**.

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`ipv6cr`|Name of the cloud router.|
|Description| IPv4/IPv6 Dual stack|Description of the cloud router.|
|Network|`ipv6internal`|The Google Cloud network the cloud router attaches to. This is the network that manages route information.|
|Region|`asia-east1`|The home region of the cloud router. Make sure the cloud router is in the same region as the subnetworks it is connecting to.|
|Google ASN|`65001`|The Autonomous System Number assigned to the cloud router. Use any unused private ASN (64512 - 65534, 4200000000 – 4294967294).|

### Configuring Cloud VPN

**Step 1**: In the Cloud Console, select **Networking** > **Interconnect** > [**VPN**](https://console.cloud.google.com/hybrid/vpn/list) > **CREATE VPN CONNECTION**.

**Step 2**: Enter the following parameters for the Compute Engine VPN gateway:

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`ipv6vpngw`|Name of the VPN gateway.|
|Description|`VPN tunnel connection between GCP and strongSwan`|Description of the VPN connection.|
|Network|`ipv6internal`| The Google Cloud network the VPN gateway attaches to. This network will get VPN connectivity.|
|Region|`asia-east1`|The home region of the VPN gateway. Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`Cloud VPN IPv4 public IP`|The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|
|VPN tunnel inner IP stack type|`IPv4 and IPv6 (dual-stack)`|The IP stack type will apply to all the tunnels associated with this VPN gateway.|

**Step 3**: Enter the following parameters for the tunnel:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`tunnel1`|Name of the VPN gateway|
|Description|`VPN tunnel connection between GCP and strongSwan`|Description of the VPN gateway|
|Remote peer IP address| `13.213.47.43`|Public IP address of the on-premises strongSwan.|
|IKE version|`IKEv2`|The IKE protocol version. IPv6 only support with IKEv2.|
|Shared secret|`secret`|A shared secret used for authentication by the VPN gateways. Configure the on-premises VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Dynamic(BGP)`|Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Cloud Router|`ipv6cr`|Select the cloud router you created previously.|
|BGP session| |BGP sessions enable your cloud network and on-premises networks to dynamically exchange routes|

**Step 4**: Enter the parameters as shown in the following table for the BGP peering:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`mpbgp`|Name of the BGP session.|
|Peer ASN|`65002`|Unique BGP ASN of the on-premises router.|
|Multiprotocol BGP|`Enable IPv6 traffic`|BGP sessions are set up over IPv4, exchanging IPv4 and IPv6 addresses|
|Google BGP IPv4 address|`Automatically`|In this case, IPv4 is 169.254.52.201 |
|Peer BGP IPv4 address|`Automatically`|In this case, IPv4 is 169.254.52.202 |
|Google BGP IPv6 address|`Automatically`| In this case, IPv6 is 2600:2d00:0:3:0:0:0:74b9 |
|Peer BGP IPv6 address|`Automatically`|In this case, IPv6 is 2600:2d00:0:3:0:0:0:74ba |

Click **Save and Continue** to complete.

**Note**: Add ingress firewall rules to allow inbound network traffic as per your security policy.

## Configuration of strongSwan

This guide assumes that you have strongSwan already installed. It also assumes a default layout of Debian 10.
