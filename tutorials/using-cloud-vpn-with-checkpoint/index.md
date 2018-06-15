---
title: How to Set Up VPN Between Check Point Security Gateway and Cloud VPN
description: Learn how to build site-to-site IPSEC VPN between Check Point security gateway and Cloud VPN.
author: ashishverm
tags: Compute Engine, Cloud VPN, Check Point security gateway, firewall
date_published: 2018-01-03
---

This guide walks you through the process to configure the [Check Point security gateway](https://www.checkpoint.com/products/next-generation-secure-web-gateway/)
for integration with the [Google Cloud VPN][cloud_vpn]. This information is
provided as an example only. Please note that this guide is not meant to be a
comprehensive overview of IPsec and assumes basic familiarity with the IPsec
protocol.

[cloud_vpn]: https://cloud.google.com/compute/docs/vpn/overview

# Environment overview

The equipment used in the creation of this guide is as follows:

* Vendor: Check Point
* Model: Check Point vSec
* Software Release: R80.10

## Topology

The topology outlined by this guide is a basic site-to-site IPsec VPN tunnel
configuration using the referenced device:

![Topology](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_0.png)

# Before you begin

## Prerequisities

To use a Check Point security gateway with Cloud VPN make sure the following prerequisites have been met:

* The Check Point Security Gateway is online and functioning with no faults detected.
* There is root access to the Check Point Security Gateway.
* There is at least one configured and verified functional internal interface.
* There is one configured and verified functional external interface.

## IPsec parameters

The following parameters and values are used in the Gateway’s IPSec configuration for the
purpose of this guide. Cloud VPN supports extensive
[list](https://cloud.google.com/vpn/docs/concepts/supported-ike-ciphers)
of ciphers that can be used per your security policies.

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
|Phase-1|Encryption|`aes-128` (IKEv1 or `aes-256`(IKEv2)|
|       |Integrity|`sha-1` (IKEv1) or `sha-256` (IKEv2)|
|       |Diffie-Helman|`Group2` (IKEv1) or `Group14` (IKEv2)|
|       |Phase1 lifetime| `36,600 seconds` (IKEv1) `36,000 seconds` (IKEv2) |
|Phase-2|Encryption|`aes-128`(IKEv1) or `aes-256`(IKEv2)|
|       |Integrity|`sha-1`|

# Configuring policy-based IPsec VPN

Below is a sample environment to walk you through set up of policy based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

**Cloud VPN**

|Name | Value|
-----|------
|Cloud VPN(external IP)|`35.195.227.26`|
|VPC CIDR|`10.132.0.0/20`|

**Check Point**

|Name | Value|
-----|------
|Check Point Security Gateway(external IP)|`199.203.248.181`|
|Addresses behind Check Point Security Gateway|`10.0.0.0/24`|

## Configuration - GCP

### Configuring Cloud VPN

To configure Cloud VPN:
1. In the Google Cloud Platform Console, select **Networking** > **[Create VPN connection](https://console.cloud.google.com/interconnect/vpn)**.

1. Click **CREATE VPN CONNECTION**.

1. Populate the fields for the gateway and tunnel as shown in the following table and click **Create**:

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`gcp-to-cp-vpn`|Name of the VPN gateway.|
|Description|`VPN tunnel connection between GCP and Check Point Security Gateway`|Description of the VPN connection.|
|Network|`to-cp`| The GCP network the VPN gateway attaches to. Note: This network will get VPN connectivity.|
|Region|`europe-west1`|The home region of the VPN gateway Note: Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`cloud-ip(35.195.227.26)`|The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|
|Remote peer IP address| `199.203.248.181`|Public IP address of the on-premise VPN appliance used to connect to the Cloud VPN.|
|IKE version|`IKEv1`|The IKE protocol version. You can select IKEv1 or IKEv2.|
|Shared secret|`secret`|A shared secret used for authentication by the VPN gateways. Configure the on-premise VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Static`|Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Remote network IP ranges| `10.0.0.0/24`|The on-premise CIDR blocks connecting to GCP from the VPN gateway.|
|Local IP ranges| `10.132.0.0/20`|The GCP IP ranges matching the selected subnet.|

![](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_2.PNG)

### Configuring a static route

1. In Google Cloud Platform Console, go to **[Routes](https://console.cloud.google.com/networking/routes)** > **Create Route**.
1. Enter the parameters as shown in the following table and click **Create**.

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`route-to-vpn`|Name of the route.|
|Network|`to-cp`| The GCP network the route attaches to.|
|Destination|`10.0.0.0/24`| IP range Destination IP address.|
|Priority|`1000`|Route priority.|
|Next hop|`Specify the VPN tunnel.`| |
|Next hop VPN tunnel|`gcp-to-cp-vpn-tunnel-1`| The Tunnel created.|

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_3.PNG)

**Note:** Add ingress firewall rules to allow inbound network traffic as per your security
policy.

## Configuration - Check Point Security Gateway

To create an Interoperable Device for Cloud VPN on the Check Point SmartConsole:

**Step 1**. Open SmartConsole > **New** > **More** > **Network Object** > **More** > **Interoperable Device**.

**Step 2**. Configure the IP address associated with Cloud VPN peer (external IP).

**Step 3**. Go to **General Properties** > **Topology** and manually add Google cloud IP addresses.

![Console user interface shows topology.](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_4.PNG)

**Step 4**. Create a star community.

1. Open SmartConsole > **Security Policies** > **Access Tools** > **VPN Communities**.
2. Click **Star Community**. The New Star Community window opens.
3. Enter an **Object Name** for the VPN Community.
4. In the **Center Gateways** area, click the plus sign to add a Check Point Security Gateway object for the center of the community.
5. In the **Satellite Gateways** area, click the **plus** sign to add the GCP gateway object.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_5.PNG)

**Step 5**. Configure these ciphers for IKEv1.

Go to **Encryption** and change the Phase 1 and Phase 2 properties according what is specified in the Cipher configuration settings on page 3.

**Note:** Make sure you select Perfect Forward Secrecy (Phase 2). This example refers to IKEv1. You can also use IKEv2 in this scenario.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_6.PNG)

**Step 6**. Go to the **Advanced** tab and modify the Renegotiation Time.

* **IKE for Phase 1**: 610 minutes
* **IKE for Phase 2**: 10,800 seconds

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_7.PNG)

**Step 7**. Configure the Access Control Rule Base and Install policy.

For more information, see the R80.10 Site To Site VPN Administration [Guide](http://dl3.checkpoint.com/paid/ea/ea41387591dcba2a8d551ba39084e9e6/CP_R80.10_SitetoSiteVPN_AdminGuide.pdf?HashKey=1515459944_c0affaeb9262c888e85d660e781d604d&xtn=.pdf).

# Configuring a route-based IPsec VPN Tunnel

Below is a sample environment to walk you through set up of route based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

**Google Cloud Platform**

|Name | Value|
-----|------
|GCP(external IP)|`35.195.227.26`|
|VPC CIDR|`10.132.0.0/20`|
|TUN-INSIDE GCP|`169.254.0.1`|
|GCP-ASN|`65000`|

**Check Point**

|Name | Value|
-----|------
|Check Point Security Gateway(external IP)|`199.203.248.181`|
|Addresses behind Check Point Security Gateway|`10.0.0.10/24`|
|TUN-INSIDE- CP|`169.54.0.2`|
|CP Security Gateway ASN|`65002`|

## Configuration - GCP

With route based VPN both static and dynamic routing can be used. This example will use
dynamic routing. [Cloud Router](https://cloud.google.com/router/docs/) is used to establish
BGP sessions between the 2 peers.

### Configuring cloud router

**Step 1**: In Google Cloud Platform Console, select **Networking** > **[Cloud Routers](https://console.cloud.google.com/interconnect/routers)** > **Create Router**.

**Step 2**: Enter the parameters as shown in the following table and click **Create**.

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`gcp-to-cp-router`|Name of the cloud router.|
|Description|           |Description of the cloud router.|
|Network|`to-cp`|The GCP network the cloud router attaches to. Note: This is the network which manages route information.|
|Region|`europe-west1`|The home region of the cloud router.Note: Make sure the cloud router is in the same region as the sub-networks it is connecting to.|
|Google ASN|`65000`|The Autonomous System Number assigned to the cloud router. Use any unused private ASN (64512 - 65534, 4200000000 – 4294967294).|

![](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_8.PNG)

### Configuring Cloud VPN

**Step 1**: In Google Cloud Platform Console, select **Networking** > **Interconnect** > **[VPN](https://console.cloud.google.com/interconnect/vpn)** > **CREATE VPN CONNECTION**.

**Step 2**: Enter the parameters as shown in the following table for the Google Compute Engine VPN gateway:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`gcp-to-cp-vpn`|Name of the VPN gateway|
|Description|`VPN tunnel connection between GCP and Check Point Security Gateway`|Description of the VPN gateway|
|Network|`to-cp`|The GCP network the VPN gateway attaches to **Note**: This network will get VPN connectivity|
|Region|`europe-west1`|The home region of the VPN gateway **Note**: Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`cloud-ip(35.195.227.26)`|The static public IP address used by the VPN gateway. An existing, unused, static public IP address within the project can be assigned, or a new one created.|

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_9.PNG)

**Step 3**: Enter the parameters as shown in the following table for the tunnel:

|Parameter|Value|Description|
|---------|------|-----------|
|Name|`gcp-to-cp-vpn`|Name of the VPN tunnel|
|Description|`VPN tunnel connection between GCP and Check Point Security Gateway`|Description of the VPN tunnel|
|Remote peer IP address|`199.203.248.181`|Public IP address of the on-premise VPN appliance used to connect to Cloud VPN.
|IKE version|`IKEv2`|The IKE protocol version. You can select IKEv1 or IKEv2.|
|Shared secret|`secret`|A shared secret for authentication by the VPN gateways. Configure the on-premise VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Dynamic(BGP)`|Cloud VPN supports multiple routing options for the exchange of route information between the VPN gateways. In this example, Cloud Router and BGP are configured.|
|Cloud Router|`gcp-to-cp-router`|Select the Cloud router created previously.|
|BGP session| |BGP sessions enable your cloud network and on-premise networks to dynamically exchange routes|

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_10.PNG)

**Step 4**: Enter the parameters as shown in the following table for the BGP peering:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`gcp-to-cp-bgp`|Name of the BGP session.|
|Peer ASN|`65002`|Unique BGP ASN of the on-premise router.|
|Google BGP IP address|`169.254.0.1`|
|Peer BGP IP address|`169.254.0.2`|

Click **Save and Continue** to complete.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_11.PNG)

**Note:** – Add ingress firewall rules to allow inbound network traffic as per your security policy.

## Configuration - Check Point Security Gateway

Create an interoperable device for Cloud VPN on the Check Point SmartConsole.

**Step 1**. Open SmartConsole > **New** > **More** > **Network Object** > **More** > **Interoperable Device**.

**Step 2**. Configure the IP address associated with Cloud VPN peer (external IP).

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_12.PNG)

**Step 3**. To force Route-based VPN to take priority, create a dummy (empty) group and assign it to the VPN domain.

1. Go to **Topology**, in the VPN Domain section. Select Manually defined.
1. Click the right to select the desired object.
1. Click **New** > **Group** > **Simple Group**.
1. Enter an **Object Name**, click **OK**. Do NOT assign any objects to this group.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_13.PNG)

**Step 4**. In `clish`, create a VPN Tunnel Interface (VTI).

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_14.PNG)

Write the Remote peer name, **exactly** as it is written in the gateway object in SmartConsole.

    add vpn tunnel [1-99] type numbered local { TUN-INSIDE- CP } remote { TUN-INSIDE- GCP } peer { Interoperable GVC object name in SmartConsole }

Example:

    add vpn tunnel 10 type numbered local 169.254.0.2 remote 169.254.0.1 peer Google_Cloud


**Step 5**. Edit the Topology.

1. Open **SmartConsole** > **Gateways & Servers**.
2. Select the Check Point Security Gateway and double-click.
3. From **General Properties** > **Network Management** > **Get Interfaces**.
4. The VTIs show in the topology.
    **Note**: The **Edit Topology** window lists the members of a VTI on the same line if these criteria match:

  * Remote peer name
  * Remote IP address
  * Interface name

5. Configure the VTI VIP in the Topology tab. Click **OK**.
6. From **VPN Domain**, select **Manually Defined** > **Empty_Group**.


![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_15.PNG)

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_16.PNG)

**Step 6**. Create a star community.

1. Open **SmartConsole** > **Security Policies** > **Access Tools** > **VPN Communities**.
2. Click **Star Community**.
3. Enter an **Object Name** for the VPN Community.
4. In the **Center Gateways** area, click the plus sign to add a Check Point Security Gateway object for the center of the community.
5. In the **Satellite Gateways** area, click the plus sign to add the GCP gateway object.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_17.PNG)

**Step 7**. Configure these ciphers for IKEv2.

Go to **Encryption** and change the Phase 1 and Phase 2 properties according what is specified within the Cipher configuration settings on page 3)
**Note:** You must select Perfect Forward Secrecy (Phase 2).

This example refers to IKEv2 specifically. You can also use IKEv1 in this scenario.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_18.PNG)

**Step 8**. Go to the **Advanced tab**. You can modify the more advanced settings for Phase 1 Phase 2 there.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_19.PNG)

**Step 9**. Setup for BGP Deployment.

**Virtual tunnel interface and initial BGP Setup**

Connect with SSH to your Security Gateway. If you are using the none default shell, change to clish. Run: `clish`
Run the commands below replacing variables surrounded by { } with your values:

    set AS {CP Security Gateway - ASN}
    set bgp external remote-as { GCP-ASN } on
    set bgp external remote-as { GCP-ASN } peer { TUN-INSIDE- GCP } on
    set bgp external remote-as { GCP-ASN } peer { TUN-INSIDE- GCP } as-override on
    set bgp external remote-as { GCP-ASN } peer { TUN-INSIDE- GCP } holdtime 30
    set bgp external remote-as { GCP-ASN } peer { TUN-INSIDE- GCP } keepalive 10
    set inbound-route- filter bgp-policy 512 based-on- as as { GCP-ASN }  on
    set inbound-route- filter bgp-policy 512 accept-all- ipv4
    set route-redistribution to bgp-as { GCP-ASN }  from interface {Redistributed from specific interface } on

Example:

    set as 65002
    set bgp external remote-as 65000 on
    set bgp external remote-as 65000 peer 169.254.0.1 on
    set bgp external remote-as 65000 peer 169.254.0.1 as-override on
    set bgp external remote-as 65000 peer 169.254.0.1 holdtime 30
    set bgp external remote-as 65000 peer 169.254.0.1 keepalive 10
    set inbound-route- filter bgp-policy 512 based-on- as as 65000 on
    set inbound-route- filter bgp-policy 512 accept-all- ipv4
    set route-redistribution to bgp-as 65000 from interface eth1 on

**Step 10**. Configure Directional Rules for Route-Based Scenario.

1. Open SmartConsole > **Global Properties** > **VPN** > **Advanced**.
2. Select **Enable VPN Directional Match in VPN Column**.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-checkpoint/Image_20.PNG)

**Note:** This is not relevant for a Policy Based scenario.

3. Add these directional match rules in the VPN column for every firewall rule related to VPN traffic:

        Internal_clear > Google Cloud VPN community name (VPN_Community)
        Google Cloud VPN community name > Google Cloud VPN community name
        (VPN_Community) Google Cloud VPN community name (VPN_Community) > Internal_clear

**Step 11**. Install policy.

For more information, see the R80.10 Site To Site VPN Administration [Guide](http://dl3.checkpoint.com/paid/ea/ea41387591dcba2a8d551ba39084e9e6/CP_R80.10_SitetoSiteVPN_AdminGuide.pdf?HashKey=1515459944_c0affaeb9262c888e85d660e781d604d&xtn=.pdf).
