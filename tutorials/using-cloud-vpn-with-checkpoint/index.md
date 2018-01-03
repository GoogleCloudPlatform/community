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
|Phase-2|Encryption|aes-128(IKEv1)|
|       |          |aes-256(IKEv2)|
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
1. Log on to the GCP Developers Console > Networking > Create VPN connection.
1. Select the VPN node and click Create VPN.
