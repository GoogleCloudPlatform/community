---
title: How to Set Up VPN between Checkpoint and Cloud VPN
description: Learn how to build site-to-site IPSEC VPN between Checkpoint and Cloud VPN.
author: ashishverm
tags: Compute Engine, Cloud VPN, Cisco ASR
date_published: 2018-01-02
---

# Introduction

Use this guide to configure a Check Point Security Gateway for integration with the
Google Cloud VPN service. This guide describes a sample environment only. This
overview assumes familiarity with the IPsec protocol. Any IP addresses, device IDs,
shared secrets or keys, and account information or project names, should be replaced
with values for your environment.

## Getting Started

To use a Check Point Security Gateway with the Google Cloud Platform (GCP) VPN
service, make sure the following prerequisites have been met:
* The Check Point Security Gateway is online and functioning with no faults detected
* There is root access to the Check Point Security Gateway
* There is at least one configured and verified functional internal interface
* There is one configured and verified functional external interface

## IPsec Parameters
Use these parameters and values in the Gateway’s IPSec configuration.

|Parameter | Value|
--------- |  -----
|IPsec Mode | `Tunnel mode` |
|Auth protocol | `Pre-shared-key` |
|Key Exchange | `IKEv2 or IKEv1` |
|Start | `Auto` |
|Perfect Forward Secrecy (PFS) | `on` |

These are the Cipher configuration settings for IKE phase 1 and phase 2 that are used
in this guide.

|Phase | Cipher Role | Cipher|
-------|-------------|-------
|Phase-1|Encryption|aes-128 (IKEv1)|
|       |            |aes-256(IKEv2)|
|       |Integrity|sha-1|
|       |Diffie-Helman|Group2
|       |Phase1 lifetime| 36,600 seconds (10 hours and 10 Minutes ) – IKEv1|
|       |                | 36,000 seconds (10 hours) – IKEv2 |
|Phase-2|Encryption|aes-128(IKEv1)or aes-256(IKEv2)|
|       |Integrity|sha-1|

#Policy Based IPsec VPN Setup
Below is a sample environment to walk you through set up of the GCP VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

**Google Cloud Platform**

|Name | Value|                             
-----|------                                  
|GCP(external IP)|35.195.227.26|
|VPC CIDR|10.132.0.0/20|
                        
**Checkpoint**

|Name | Value|
-----|------
|Checkpoint Security Gateway(external IP)|199.203.248.181|
|Addresses behind Check Point Security Gateway|10.0.0.10/24|

#Google Cloud Platform

To configure the Google Cloud Platform VPN:
1. Log on to the GCP Developers Console > **Networking** > **Create VPN connection**.
1. Select the VPN node and click Create VPN.

Add image 1
Add image 2

|Parameter|Description|
|---------|-----------|
|Name|Name of the VPN gateway|
|Description|Description of the VPN connection|
|Network| The GCP network the VPN gateway attaches to|
|       |Note: This network will get VPN connectivity|
|Region|The home region of the VPN gateway Note: Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address| The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|
|Remote peer IP address| Public IP address of the on-premise VPN appliance used to connect to the Cloud VPN.|
|IKE version| The IKE protocol version. You can select IKEv1 or IKEv2.|
|Shared secret| A shared secret used for authentication by the VPN gateways. Configure the on-premise VPN gateway tunnel entry with the same shared secret.|
|Routing options| Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Remote network IP ranges| The on-premise CIDR blocks connecting to GCP from the VPN gateway.|
|Local subnetworks|The GCP CIDR blocks connecting on-premise with the VPN gateway.|
|Local IP ranges| The GCP IP ranges matching the selected subnet.|

To create a route:
1. From the GCP Console, go to Routes &gt; Create a route.
1. Enter the parameters. Click Create.

Add Image 3

**New Routes**

|Parameter|Description|
|---------|-----------|
|Name| Name of the route|
|Network| The GCP network the route attaches to.|
|Destination| IP range Destination IP address.|
|Priority| Route priority.|
|Next| hop Specify the VPN tunnel.|
|Next hop VPN tunnel| The Tunnel created.|

Note – Add ingress firewall rules to allow inbound network traffic as per your security
policy.


#Check Point

To create an Interoperable Device for Google Cloud on the Check Point
SmartConsole:

1. Open SmartConsole > **New** > **More** > **Network Object** > **More** > **Interoperable Device**.
1. Configure the IP address associated with GVC VPN peer (external IP).
1. Go to **General Properties** > **Topology** and manually add Google cloud IP addresses.

Add image 4

Step 4 Create a star community.

1. Open SmartConsole > **Security Policies** > **Access Tools** > **VPN Communities**.
2. Click **Star Community**. The New Star Community window opens.
3. Enter an **Object Name** for the VPN Community.
4. In the **Center Gateways** area, click the plus sign to add a Check Point Security Gateway object for the center of the community.
5. In the **Satellite Gateways** area, click the plus sign to add the GCP gateway object.

Add image 5

Step 5 Configure these ciphers for IKEv1.

Go to **Encryption** and change the Phase 1 and Phase 2 properties according what is specified in the Cipher configuration settings on page 3.

**Note:** Make sure you select Perfect Forward Secrecy (Phase 2). This example refers to IKEv1. You can also use IKEv2 in this scenario.

Add image 6

Step 6 Go to the **Advanced** tab and modify the Renegotiation Time.

**IKE for Phase 1**: 610 minutes
**IKE for Phase 2**: 10,800 seconds

Add image 7

Step 7 Configure the Access Control Rule Base and Install policy.
For more information, see the R80.10 Site To Site VPN Administration Guide.


#Route Based IPsec VPN Tunnel

##Configuration Using the Google Cloud Router and BGP

The environment below walks you through an IPSec VPN tunnel setup. Make sure to replace the IP addresses in the sample environment with your own IP addresses.
