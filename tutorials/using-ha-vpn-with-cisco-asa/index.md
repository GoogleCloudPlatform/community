---
title: Google Cloud HA VPN Interop Guide for Cisco ASA 5506H
description: Describes how to build site-to-site IPsec VPNs between HA VPN on Google Cloud Platform (GCP) and Cisco ASA 5506H
author: ashishverm
tags: HA VPN, Cloud VPN, interop, Cisco, ASA
date_published: 2019-07-06
---

# Using HA VPN with Cisco ASA 5506H

Learn how to build site-to-site IPsec VPNs between [HA VPN](https://cloud.google.com/vpn/docs/)
on Google Cloud Platform (GCP) and Cisco ASA 5506H.

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
- [Configure the Cisco ASA 5506H side](#configure-the-cisco-asa-5506h-side)
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
- [Troubleshooting IPsec on Cisco ASA 5506H](#troubleshooting-ipsec-on-cisco-asa-5506h)
- [Reference documentation](#reference-documentation)
    - [GCP documentation](#gcp-documentation)
    - [Cisco ASA 5506H documentation](#cisco-asa-5506h-documentation)

Cisco terminology and the Cisco logo are
trademarks of Cisco or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

Author: ashishverm

## Introduction

This guide walks you through the process of configuring
Cisco ASA 5506H for integration with the
[HA VPN service](https://cloud.google.com/vpn/docs) on GCP.

For more information about HA or Classic VPN, see the
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

-  **GCP VPC network**—A single virtual network within a single GCP project.
-  **On-premises gateway**—The VPN device on the non-GCP side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. GCP instructions are written from the
point of view of the GCP VPC network, so "on-premises gateway" refers to the
gateway that's connecting _to_ GCP.
-  **External IP address** or **GCP peer address**—external IP addresses used 
by peer VPN devices to establish HA VPN with Google Cloud. External IP addresses
are allocated automatically, one for each gateway interface within a GCP project.
-  **Dynamic routing**—GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
Note that HA VPN only supports dynamic routing.

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/vpn/docs/concepts/topologies):

This interop guide is based on [1-peer-2-address](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) topology.

## Product environment

The Cisco equipment used in this guide is as follows:

-  Vendor — Cisco
-  Model — ASA 5506H
-  Software release — 9.9(2)

## Before you begin

1. Review information about how [dynamic routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#dynamic-routing) works in Google Cloud Platform.

1. Make sure your peer VPN gateway supports BGP.

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

There are no additional licenses required for site-to-site VPN on Cisco
ASA 5506H.

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
<td>Cisco</td>
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
<td>VPN BGP routing mode</td>
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
<td>External static IP address for the first internet interface of Cisco ASA 5506H</td>
<td><code>[ON_PREM_GW_IP_0]</code> </td>
<td>209.119.81.225</code></td>
</tr>

<tr>
<td>External static IP address for the second internet interface of Cisco ASA 5506H</td>
<td><code>[ON_PREM_GW_IP_1]</code> </td>
<td>209.119.81.225</td>
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

The command should look similar to the following example:

    gcloud compute networks create network-a \
    --subnet-mode custom  \
    --bgp-routing-mode global
    
#### Create subnets

Create two subnets in as follows:

    gcloud compute networks subnets create [SUBNET_NAME_1]  \
    --network [NETWORK] \
    --region [REGION_1] \
    --range [RANGE_1]
    
    gcloud compute networks subnets create [SUBNET_NAME_2] \
    --network [NETWORK] \
    --region [REGION_2] \
    --range [RANGE_2]

The command should look similar to the following example:

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

    gcloud beta compute vpn-gateways create [GW_NAME] \
    --network [NETWORK] \
    --region [REGION]
    
The command should look similar to the following example:
    
    gcloud beta compute vpn-gateways create ha-vpn-gw-a \
    --network network-a \
    --region us-central1

### Create Cloud Router

Complete the following command sequence to create a Cloud Router. In the following 
commands, replace the options as noted below:

Replace [ROUTER_NAME] with the name of the new Cloud Router, which you must create 
in the same GCP region as the Cloud HA VPN gateway.
Replace [GOOGLE_ASN] with any private ASN (64512 - 65534, 4200000000 - 4294967294) 
that you are not already using in the peer network. The Google ASN is used for all 
BGP sessions on the same Cloud Router and it cannot be changed later.

    gcloud compute routers create [ROUTER_NAME] \
    --region [REGION] \
    --network [NETWORK] \
    --asn [GOOGLE_ASN]

The command should look similar to the following example:

    gcloud compute routers create router-a \
    --region us-central1 \
    --network network-a \
    --asn 65001
    
### Create an External VPN Gateway resource

Create an external VPN gateway resource that provides information to GCP about your peer VPN gateway or gateways. Depending on the HA recommendations for your peer VPN gateway, you can create external VPN gateway resource for the following different types of on-premises VPN gateways:

- Two separate peer VPN gateway devices where the two devices are redundant with each other and each device has its own public IP address.
- A single peer VPN gateway that uses two separate interfaces, each with its own public IP address. For this kind of peer gateway, you can create a single external VPN gateway with two interfaces.
- A single peer VPN gateway with a single public IP address.

This interop guide covers option 2 only. 

#### Create an External VPN Gateway resource for a single peer VPN gateway with two separate interfaces

    gcloud beta compute external-vpn-gateways create [PEER_GW_NAME] \
    --interfaces 0=[ON_PREM_GW_IP_0],1=[ON_PREM_GW_IP_1] \

The command should look similar to the following example:
 
    gcloud beta compute external-vpn-gateways create peer-gw   \
     --interfaces 0=209.119.81.225,1=209.119.81.225 \

### Create two VPN tunnels, one for each interface on the HA VPN gateway

    gcloud beta compute vpn-tunnels create [TUNNEL_NAME_IF0] \
    --peer-external-gateway [PEER_GW_NAME] \
    --peer-external-gateway-interface [PEER_EXT_GW_IF0]  \
    --region [REGION] \
    --ike-version [IKE_VERS] \
    --shared-secret [SHARED_SECRET] \
    --router [ROUTER_NAME] \
    --vpn-gateway [GW_NAME] \
    --interface [INT_NUM_0]
    
    gcloud beta compute vpn-tunnels create [TUNNEL_NAME_IF1] \
    --peer-external-gateway [PEER_GW_NAME] \
    --peer-external-gateway-interface [PEER_EXT_GW_IF1] \
    --region [REGION] \
    --ike-version [IKE_VERS] \
    --shared-secret [SHARED_SECRET] \
    --router [ROUTER_NAME] \
    --vpn-gateway [GW_NAME] \
    --interface [INT_NUM_1]
    
The command should look similar to the following example:
 
    gcloud beta compute vpn-tunnels create tunnel-a-to-on-prem-if-0 \
    --peer-external-gateway peer-gw \
    --peer-external-gateway-interface 0  \
    --region us-central1 \
    --ike-version 2 \
    --shared-secret mysharedsecret \
    --router router-a \
    --vpn-gateway ha-vpn-gw-a \
    --interface 0
    
    gcloud beta compute vpn-tunnels create tunnel-a-to-on-prem-if-1 \
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
interfaces and BGP peers, this example uses the automatic method.

For the first VPN tunnel

1.Add a new BGP interface to the Cloud Router.

    gcloud compute routers add-interface [ROUTER_NAME] \
    --interface-name [ROUTER_INTERFACE_NAME_0] \
    --mask-length [MASK_LENGTH] \
    --vpn-tunnel [TUNNEL_NAME_0] \
    --region [REGION]
    
The command should look similar to the following example:
    
    gcloud compute routers add-interface router-a \
    --interface-name if-tunnel-a-to-on-prem-if-0 \
    --mask-length 30 \
    --vpn-tunnel tunnel-a-to-on-prem-if-0 \
    --region us-central1  

2.Add a BGP peer to the interface for the first tunnel.

    gcloud compute routers add-bgp-peer [ROUTER_NAME] \
    --peer-name [PEER_NAME] \
    --peer-asn [PEER_ASN] \
    --interface [ROUTER_INTERFACE_NAME_0] \
    --region [REGION] \
    
 The command should look similar to the following example:   
 
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

The command should look similar to the following example:

    gcloud compute routers add-interface router-a \
    --interface-name if-tunnel-a-to-on-prem-if-1 \
    --mask-length 30 \
    --vpn-tunnel tunnel-a-to-on-prem-if-1 \
    --region us-central1
    
    
2.Add a BGP peer to the interface for the second tunnel.

    gcloud compute routers add-bgp-peer [ROUTER_NAME] \
    --peer-name [PEER_NAME] \
    --peer-asn [PEER_ASN] \
    --interface [ROUTER_INTERFACE_NAME_1] \
    --region [REGION] \

The command should look similar to the following example:

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
    
    gcloud compute routers describe router-a \
    --region us-central1

### Configure firewall rules

Configure firewall rules to allow inbound traffic from the on-premises
network subnets. You must also configure the on-premises network firewall to
allow inbound traffic from your VPC subnet prefixes.

    gcloud compute firewall-rules create [VPN_RULE_NAME] \
    --network [NETWORK] \
    --allow tcp,udp,icmp \
    --source-ranges [IP_ON_PREM_SUBNET]
    
The command should look similar to the following example:    
    
     gcloud compute firewall-rules create network-a-to-on-prem \
    --network network-a \
    --allow tcp,udp,icmp \
    --source-ranges 192.168.1.0/24
    
## Configure the Cisco ASA 5506H side

### Creating the base network configuration

Follow the procedure listed in the configuration code snippet below to create
the base Layer 3 network configuration of Cisco. Note the following:

-  At least one internal-facing network interface is required in order to
connect to your on-premises network, and one external-facing interface is
required in order to connect to GCP.

```
<insert configuration code snippet here>
```

### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

### GCP-compatible settings for IPSec and IKE

 [Ciphers supported by GCP](https://cloud.google.com/vpn/docs/how-to/configuring-peer-gateway#configuring_ike).

#### Configure the IKE proposal and policy

-  **Encryption algorithm** - aes-gcm-256
-  **Integrity algorithm** - sha-512
-  **Diffie-Hellman group** - group14

```
crypto ikev2 policy 10
 encryption aes-gcm-256
 integrity null
 group 14     
 prf sha512 sha384 sha256 sha
 lifetime seconds 36000
```

#### Configure the IKEv2 keyring

```
<Insert configuration code snippet here>
```

#### Configure the IKEv2 profile

```
crypto ipsec ikev2 ipsec-proposal GCP
 protocol esp encryption aes-gcm-256
 protocol esp integrity sha-512

crypto ipsec profile GCP
 set ikev2 ipsec-proposal GCP
 set pfs group14
 set security-association lifetime seconds 10800
```

#### Configure the IPsec security association (SA)

```
crypto ipsec profile GCP
 set ikev2 ipsec-proposal GCP
 set pfs group14
 set security-association lifetime seconds 10800
```

#### Configure the IPsec transform set

< insert the instructions for creating the IPsec transform set here.>

```
<Insert configuration code snippet here>
```

#### Configure the IPsec static virtual tunnel interface (SVTI)

-  Adjust the maximum segment size (MSS) value of TCP packets going through a
router as discussed in
[MTU Considerations](https://cloud.google.com/vpn/docs/concepts/mtu-considerations)
for Cloud VPN.

```
interface Tunnel10
 nameif tunnel-a
 ip address 169.254.0.2 255.255.255.252 
 tunnel source interface outside
 tunnel destination 35.242.111.74
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile GCP
!
interface Tunnel20
 nameif tunnel-b
 ip address 169.254.0.6 255.255.255.252 
 tunnel source interface outside
 tunnel destination 35.220.72.68
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile GCP
!
```

### Configuring the dynamic routing protocol

Follow the procedure in this section to configure dynamic routing for traffic
through the VPN tunnel or tunnels using the BGP routing protocol.

```
prefix-list GCP-IN seq 5 permit 192.168.10.0/24 le 32
prefix-list GCP-OUT seq 5 permit 192.168.1.0/24 le 32

router bgp 65002
 bgp log-neighbor-changes
 bgp graceful-restart
 bgp router-id 192.168.1.1
 address-family ipv4 unicast
  neighbor 169.254.0.1 remote-as 65001
  neighbor 169.254.0.1 ebgp-multihop 2
  neighbor 169.254.0.1 activate
  neighbor 169.254.0.1 prefix-list GCP-IN in
  neighbor 169.254.0.1 prefix-list GCP-OUT out
  neighbor 169.254.0.1 maximum-prefix 100 70
  neighbor 169.254.0.5 remote-as 65001
  neighbor 169.254.0.5 ebgp-multihop 2
  neighbor 169.254.0.5 activate
  neighbor 169.254.0.5 prefix-list GCP-IN in
  neighbor 169.254.0.5 prefix-list GCP-OUT out
  neighbor 169.254.0.5 maximum-prefix 100 70
  network 192.168.1.0
  ! Enables ECMP Over both peers
  maximum-paths 2
  no auto-summary
  no synchronization
 exit-address-family
!
```

### Configure firewall rules

```
access-list GCP-IN extended permit ip any any 
access-group GCP-IN in interface tunnel-a
access-group GCP-IN in interface tunnel-a control-plane
access-group GCP-IN in interface tunnel-b
access-group GCP-IN in interface tunnel-b control-plane
```

### Saving the configuration

Follow the procedure in this section to save the on-premises configuration.

```
<Insert configuration code snippet here>
```

### Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. For either side, 
make sure that the subnet that a machine or virtual machine is located in is being forwarded 
through the VPN tunnel.

1. Create VMs on both sides of the tunnel. Make sure that you configure the
VMs on a subnet that will pass traffic through the VPN tunnel.

-  Instructions for creating virtual machines in Compute Engine are located
in the 
[Getting Started Guide](https://cloud.google.com/compute/docs/quickstart).
- Instructions for creating machines machines on-premises are located
\<here>.

2. After you have deployed VMs on both the GCP and on-premises, you can use 
an ICMP echo (ping) test to test network connectivity through the VPN tunnel.

On the GCP side, use the following instructions to test the connection to a
machine that's behind the on-premises gateway:

1. In the GCP Console,
[go to the VM Instances page](https://console.cloud.google.com/compute?).
1. Find the GCP virtual machine you created.
1. In the **Connect** column, click **SSH**. A browser window opens at the VM
command line.
1. Ping a machine that's behind the on-premises gateway.

<Insert any additional instructions for testing the VPN tunnels from the \<vendor
name>\<product-name> here. For example, below is an example of a successful ping
from a Cisco ASR router to GCP.>

    cisco-asr#ping 172.16.100.2 source 10.0.200.1
    Type escape sequence to abort.
    Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:
    Packet sent with a source address of 10.0.200.1
    !!!!!
    Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms


## Troubleshooting IPsec on Cisco ASA 5506H

For troubleshooting information, see the Cisco ASA 5506H
[troubleshooting guide](#https://www.cisco.com/c/en/us/support/docs/security/asa-5500-x-series-next-generation-firewalls/113574-tg-asa-ipsec-ike-debugs-main-00.html?referring_site=RE&pos=1&page=https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/5409-ipsec-debug-00.html).

## Reference documentation

You can refer to the following \<vendor-name>\<product-name> documentation and
Cloud VPN documentation for additional information about both products.

### GCP documentation

To learn more about GCP networking, see the following documents:

-  [VPC Networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Advanced Cloud VPN Configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Check VPN status](#https://cloud.google.com/vpn/docs/how-to/checking-vpn-status)
-  [Terraform template for HA VPN](https://www.terraform.io/docs/providers/google/r/compute_ha_vpn_gateway.html)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### Cisco ASA 5506H documentation

For more product information on Cisco ASA 5506H, refer to the following
ASA series feature configuration guides and datasheets:

- [Cisco ASA 5500 Datasheet](#https://www.cisco.com/c/en/us/products/collateral/security/asa-5500-series-next-generation-firewalls/datasheet-c78-733916.html)
- [Cisco ASA Series VPN CLI Configuration Guide](#https://www.cisco.com/c/en/us/td/docs/security/asa/asa99/configuration/vpn/asa-99-vpn-config/vpn-ike.html)

For common Cisco ASA 5506H error messages and debug commands, see
the following guides:

- [ASA IPSEC debug](#https://www.cisco.com/c/en/us/support/docs/security/asa-5500-x-series-next-generation-firewalls/113574-tg-asa-ipsec-ike-debugs-main-00.html?referring_site=RE&pos=1&page=https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/5409-ipsec-debug-00.html)
