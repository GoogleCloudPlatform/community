---
title: Cloud VPN interoperability guide for Juniper SRX
description: Describes how to build site-to-site IPsec VPNs between Cloud VPN on Google Cloud Platform and Juniper SRX300.
author: antiabong,ashishverm
tags: VPN, interop, Juniper, SRX
date_published: 2019-09-12
---

Juniper, SRX, and Junos are trademarks of Juniper Networks, Inc. or its affiliates in the United States and/or other 
countries.

_Disclaimer: This interoperability guide is intended to be informational in nature and shows examples only. Customers
should verify this information by testing it._

## Introduction

Learn how to build site-to-site IPsec VPNs between [Cloud VPN](https://cloud.google.com/vpn/docs/) on Google Cloud
Platform (GCP) and Juniper SRX300.

For more information about Cloud VPN, see the [Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview).

Note: This guide assumes that you have basic knowledge of the [IPsec](https://wikipedia.org/wiki/IPsec) protocol.

## Terminology

Definitions of terms used throughout this guide:

-   **GCP VPC network**: A single virtual network within a single GCP project.
-   **On-premises gateway**: The VPN device on the non-GCP side of the connection, which is usually a device in a physical 
    data center or in another cloud provider's network. GCP instructions are written from the point of view of the GCP VPC
    network, so *on-premises gateway* refers to the gateway that's connecting *to* GCP.
-   **External IP address** or **GCP peer address**: A single static IP address within a GCP project that exists at the edge
    of the GCP network.
-   **Static routing**: Manually specifying the route to subnets on the GCP side and to the on-premises side of the VPN 
    gateway.
-   **Dynamic routing**: GCP dynamic routing for VPN using the
    [Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).

## Topology

Cloud VPN supports the following topologies:

-   A site-to-site IPsec VPN tunnel configuration using [Cloud Router](https://cloud.google.com/router/docs/) and 
    providing dynamic routing with the [Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
-   A site-to-site IPsec VPN tunnel configuration using static routing.

For detailed topology information, see the following resources:

-   For basic VPN topologies, see [Cloud VPN overview](https://cloud.google.com/vpn/docs/concepts/overview).
-   For redundant topologies, the Cloud VPN documentation on 
    [redundant and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns). 

This tutorial uses the topology shown below as a guide to create the SRX300 configurations and GCP environment:

![Topology](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-juniper-srx/Juniper-SRX-VPN.png)

## Product environment

The equipment used in this guide is as follows:

-   Vendor: Juniper
-   Model: SRX300
-   Software release: Junos software release 15.1X49-D100.6

Although the steps in this guide use Juniper SRX300, this guide also applies to the following SRX platforms:

-   SRX220 and SRX240
-   SRX550
-   SRX1400
-   SRX3400
-   vSRX

## Before you begin

Follow the steps in this section to prepare for VPN configuration.

Important: Throughout these procedures, you assign names to entities such as the VPC network, subnet, and IP address. Each 
time you assign a name, make a note of it, because you often need to use those names in later procedures.

### GCP account and project

Make sure that you have a GCP account. When you begin, you must select or create a GCP project where you will build
the VPN. For details, see
[Creating and managing projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects). 

### Permissions

To create a GCP network, a subnetwork, and other entities described in this guide, you must be able to sign in to GCP as a 
user who has the [Network Admin](https://cloud.google.com/compute/docs/access/iam#network_admin_role) role. For details,
see
[Required permissions](https://cloud.google.com/vpn/docs/how-to/creating-vpn-dynamic-routes#required_permissions).

### Licenses and modules

Before you configure your Juniper SRX300 for use with Cloud VPN, make sure that this license is available:

- Junos Software Base (JSB/JB) license for SRX300 or Junos Software Enhanced (JSE/JE) license

For detailed Juniper SRX series license information, refer to
[SRX Series Services Gateways](https://www.juniper.net/us/en/products-services/security/srx-series/).

## Configure the GCP side

This section covers how to configure Cloud VPN. The preferred approach is to use dynamic routing with the BGP protocol, but
this section also includes instructions for configuring static routing.

There are two ways to create VPN gateways on GCP: using the Google Cloud Platform Console and using the
[`gcloud` command-line tool](https://cloud.google.com/sdk/). This section describes how to perform the tasks using the GCP
Console. For the `gcloud` commands for performing these tasks, see the [appendix](#appendix-using-gcloud-commands).

### Initial tasks

Complete the following procedures before configuring a GCP VPN gateway and tunnel.

These initial tasks are the same whether you are creating an IPsec VPN using dynamic routing or static routing.

#### Select a GCP project

1.  [Open the GCP Console](https://console.cloud.google.com).
1.  At the top of the page, select the GCP project you want to use.

    Note: Make sure that you use the same GCP project for all of the GCP procedures in this guide.

#### Create a custom VPC network and subnet

1.  In the GCP Console, go to the [**VPC networks** page](https://console.cloud.google.com/networking/networks/list).
1.  Click **Create VPC network**.
1.  For **Name**, enter a name, such as `vpn-juniper-test-network`. Remember this name for later.
1.  In the **Subnets** section, for **Subnet creation mode**, select **Custom**.
1.  In the **New subnet** section, enter the following values:
    -   **Name**: The name for the subnet, such as `vpn-subnet-1`.
    -   **Region**: The region that is geographically closest to the on-premises gateway, such as  `us-east1`.
    -   **IP address range**: An IP address range, such as `172.16.100.0/24`.
1.  In the **New subnet** section, click **Done**.
1.  Click **Create**.

The creation of the network and its subnet can take a minute or more.

#### Create the GCP external IP address

1.  In the GCP Console, go to the
    [**External IP addresses** page](https://console.cloud.google.com/networking/addresses/list).
1.  Click **Reserve static address**.
1.  For **Name**, enter a name, such as `vpn-test-static-ip`. Remember the name for later.
1.  For **Region**, select the region where you want to locate the VPN gateway. Normally, this is the region that contains
    the instances you want to reach.
1.  Click **Reserve**.

    It can take several seconds for your static external IP address to appear on the **External IP addresses** page.

1. Make a note of the IP address so that you can use it to configure the VPN gateway later.

### Configuring an IPsec VPN using dynamic routing

For dynamic routing, you use [Cloud Router](https://cloud.google.com/router/docs/concepts/overview) to establish BGP
sessions between GCP and the on-premises Juniper SRX300 equipment. We recommend dynamic routing over static routing where 
possible, as discussed in the [Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview) and
[Cloud VPN network and tunnel routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing) documents.

#### Configure the VPN gateway

1.  In the GCP Console, go to the [**VPN** page](https://console.cloud.google.com/networking/vpn/list).
1.  Click **Create VPN connection**.
1.  Choose **Claasic VPN** and click **Continue**.
1.  Set the following values for the VPN gateway:
    -   **Name**: The name of the VPN gateway. This name is displayed in the GCP Console and is used by the `gcloud`
        command-line tool to refer to the gateway. Use a name like `vpn-test-juniper-gw-1`.
    -   **Network**: The VPC network that you created previously (for example, `vpn-juniper-test-network`) that contains the
        instances that the VPN gateway will serve.
    -   **Region**: Normally, you put the gateway in the region that contains the instances that you want to reach.
    -   **IP address**: Select the [static external IP address](#create-the-gcp-external-ip-address) (for example,
        `vpn-test-static-ip`) that you created for this gateway in the previous section.
1.  Set the following values for at least one tunnel:
    -   **Name**: The name of the VPN tunnel, such as `vpn-test-tunnel1`.
    -   **Remote peer IP address**: The public external IP address of the on-premises VPN gateway.
    -   **IKE version**: `IKEv2` or `IKEv1`. IKEv2 is preferred, but you can use IKEv1 if it is the only IKE version that
        the on-premises gateway can use.
    -   **IKE pre-shared key**: A character string, also known as a *shared secret*, that is used in establishing encryption
        for the tunnel. You must enter the same shared secret into both VPN gateways. For more information, see
        [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).
1.  Under **Routing options**, select the **Dynamic (BGP)** tab.
1.  In the **Cloud router** menu, select **Create cloud router** and set the following values in the
    **Create a cloud router** dialog:
    -   **Name**: The name of the Cloud Router, such as `vpn-test-juniper-rtr`. This name is displayed in the GCP Console.
        If you use the `gcloud` command-line tool to perform VPN tasks, you use this name to refer to the router.
    -   **Google ASN**: The [private ASN](https://tools.ietf.org/html/rfc6996) for the router you are configuring. It can be
        any private ASN in the range `64512–65534` or `4200000000–4294967294` that you are not already using. Example:
        `65002`.
1.  Click **Save and continue**.
1.  Next to the **BGP session** menu, click the **Add BGP session** button (pencil icon) and set the following values:
    -   **Name**: A name for the session, such as `bgp-peer1`.
    -   **Peer ASN**: The [private ASN](https://tools.ietf.org/html/rfc6996) for the on-premises VPN device you are
        configuring. It can be any private ASN in the range `64512–65534` or `4200000000–4294967294` that you are not
        already using. Example: `65001`.
    -   **Google BGP IP address**: A [link-local](https://wikipedia.org/wiki/Link-local_address) IP address that belongs to 
        the same `/30` subnet in `169.254.0.0/16`. Example: `169.254.1.1`.
    -   **Peer BGP IP address**: A link-local IP address for the on-premises peer. Example: `169.254.1.2`. For details, see
        [this explanation of dynamic routing for VPN tunnels in VPC networks](https://cloud.google.com/router/docs/concepts/overview#dynamic_routing_for_vpn_tunnels_in_vpc_networks).
    -   **Remote network IP range**: The IP address range of the on-premises subnet on the other side of the tunnel from
        this gateway.
    -   **Advertised route priority**: Configure this option if you want to set up redundant or high-throughput VPNs as 
        described in [advanced VPN configurations](#advanced-vpn-configurations). Note that if you don't need advanced VPN 
        now, you will need to configure a new VPN tunnel later to support it. The advertised route priority is the base
        priority that Cloud Router uses when advertising the "to GCP" routes. For more information, see
        [Route metrics](https://cloud.google.com/router/docs/concepts/overview#route_metrics).
        Your on-premises VPN gateway imports these as MED values.
1.  Click **Save and continue**.
1.  Click **Create**.

    The GCP VPN gateway and Cloud Router are initiated, and the tunnel is initiated.

This procedure automatically creates a static route to the on-premises subnet as well as forwarding rules for UDP ports
500 and 4500 and for ESP traffic. The VPN gateways will not connect until you've configured the on-premises gateway and 
created firewall rules in GCP to allow traffic through the tunnel between the Cloud VPN  gateway and the on-premises 
gateway.

#### Configure firewall rules

You configure GCP firewall rules to allow inbound traffic from the on-premises network subnets. You configure the
on-premises network firewall to allow inbound traffic from your VPC subnet prefixes.

1.  In the GCP Console, go to the [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls).
1.  Click **Create firewall rule**.
1.  Set the following values:
    -   **Name**: A name for the firewall rule, such as `vpnrule1`.
    -   **VPC network**: The name of the VPC network that you created previously (for example, `vpn-juniper-test-network`).
    -   **Source filter**: A filter to apply your rule to specific sources of traffic. In this case, choose **IP ranges**.
    -   **Source IP ranges**: The on-premises IP ranges to accept from the on-premises VPN gateway.
    -   **Allowed protocols and ports**: The string `tcp;udp;icmp`.
1. Click **Create**.

### Configuring a route-based IPsec VPN using static routing

This section covers the steps for creating a GCP IPsec VPN using static routing. Both route-based Cloud VPN and
policy-based Cloud VPN use static routing. For information on how this works, see the
[Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview).

Note: Most steps in the procedure for configuring an IPsec VPN using static routing are the same as for configuring an 
IPsec VPN using dynamic routing. Rather than repeat those steps in the following procedure, the procedure links to the 
previous section.

1.  Follow the steps for [configuring an IPsec VPN using dynamic routing](#configuring-an-ipsec-vpn-using-dynamic-routing), 
    with these changes:
    -   In the configuration for a tunnel, under **Routing options**, select **Route-based**.
    -   For **Remote network IP ranges**, set the IP address range or ranges of the on-premises network, which is the 
        network on the other side of the tunnel from the Cloud VPN gateway that you are currently configuring.
1.  Follow the steps for configuring firewall rules in the previous section, and set the following values:
    -   **Name**: A name for the firewall rule, such as `vpnrule1`.
    -   **VPC network**: The name you used earlier for the VPC network, such as `vpn-juniper-test-network`.
    -   **Source filter**: A filter to apply your rule to specific sources of traffic. In this case, choose **IP ranges**.
    -   **Source IP ranges**: The peer ranges to accept from the peer VPN gateway.
    -   **Allowed protocols and ports**: The string `tcp;udp;icmp`.

## Configure the Juniper SRX300 side

### Creating the base network configuration

Follow the procedure listed in the configuration code snippet below to create the base Layer 3 network configuration for 
Juniper SRX300. 

At least one internal-facing network interface is required in order to connect to your on-premises network, and one 
external-facing interface is required in order to connect to GCP.

A sample interface configuration is provided below for reference:

    [edit]
    root@vsrx#
    # Internal interface configuration
    set interfaces ge-0/0/1 unit 0 family inet address 192.168.0.1/24
    set interfaces ge-0/0/1 unit 0 description "internal facing interface 1"
    set interfaces ge-0/0/2 unit 0 family inet address 192.168.1.1/24
    set interfaces ge-0/0/2 unit 0 description "internal facing interface 2"
    # External interface configuration
    set interfaces ge-0/0/0 unit 0 family inet address 104.196.65.171/31
    set interfaces ge-0/0/0 unit 0 description "external facing interface"
    # Tunnel interface configuration
    set interfaces st0 unit 0 family inet mtu 1460
    set interfaces st0 unit 0 family inet address 169.254.0.2/30

### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

#### GCP-compatible settings for IPsec and IKE

Configuring the vendor side of the VPN network requires you to use IPsec and IKE settings that are compatible with the GCP 
side of the network. The following table lists settings and information about values compatible with GCP VPN. Use these 
settings for the procedures in the subsections that follow.

Note: The Juniper SRX300 solution might have its own specifications for replay window size.

| Setting       | Description or value                   |
|---------------|----------------------------------------|
| IPsec Mode    | ESP+Auth Tunnel mode (Site-to-Site)    |
| Auth Protocol | `psk`                                  |
| Shared Secret | Also known as an IKE pre-shared key. Choose a strong password by following [these guidelines](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key). The shared secret is very sensitive because it allows access to your network. |
| Start         | `auto` (On-premises device should automatically restart the connection if it drops.) |
| PFS (Perfect Forward Secrecy) | on |
| DPD (Dead Peer Detection) |  Recommended: `Aggressive`. DPD detects when the Cloud VPN restarts and routes traffic using alternate tunnels. |
| INITIAL_CONTACT (sometimes called *uniqueids*) | Recommended: `on` (sometimes called `restart`). The purpose is to detect restarts faster so that perceived downtime is reduced. |
| TSi (Traffic Selector - Initiator) | **Subnet networks**: the ranges specified by the GCP local traffic selector. If no local traffic selector range was specified because the VPN is in an auto-mode VPC network and is announcing only the gateway's subnet, that subnet range is used. **Legacy networks**: the range of the network. |
| TSr (Traffic Selector - Responder) | **IKEv2**: The destination ranges of all of the routes that have the next hop VPN tunnel set to this tunnel on the GCP side. **IKEv1**: Arbitrarily, the destination range of one of the routes that has the next hop VPN tunnel set to this tunnel on the GCP side. |
| MTU | The MTU of the on-premises VPN device must be set to 1460 or lower. ESP packets leaving the device must not exceed 1460 bytes. You must enable prefragmentation on your device, which means that packets must be fragmented first, then encapsulated. For more information, see [MTU considerations](https://cloud.google.com/vpn/docs/concepts/mtu-considerations). |
| IKE ciphers | For details about IKE ciphers for IKEv1 or IKEv2 supported by GCP, including the additional ciphers for PFS, see [Supported IKE ciphers](https://cloud.google.com/vpn/docs/concepts/supported-ike-ciphers). |

### Configure the IKE proposal and policy

Create an Internet Key Exchange (IKE) version 2 proposal object. IKEv2 proposal objects contain the parameters required for
creating IKEv2 proposals when defining remote access and site-to-site VPN policies. IKE is used to authenticate IPsec peers, 
negotiate and distribute IPsec encryption keys, and automatically establish IPsec security associations (SAs). The default 
proposal associated with the default policy is used for negotiation. An IKEv2 policy with no proposal is considered 
incomplete.

In this block, the following parameters are set:

-   **Encryption algorithm**: `AES-CBC-256`
-   **Integrity algorithm**: `SHA256`
-   **Diffie-Hellman group**: `14`
-   **IKEv2 Lifetime** : The lifetime of the security associations, after which a reconnection will occur. The default
    on most SRX platforms is 28800 seconds.

        [edit]
          root@vsrx#
          set security ike proposal ike-phase1-proposal authentication-method pre-shared-keys
          set security ike proposal ike-phase1-proposal dh-group group14
          set security ike proposal ike-phase1-proposal authentication-algorithm sha-256
          set security ike proposal ike-phase1-proposal encryption-algorithm aes-256-cbc
          set security ike proposal ike-phase1-proposal lifetime-seconds 28800
          set security ike policy ike_pol_onprem-2-gcp-vpn mode main
          set security ike policy ike_pol_onprem-2-gcp-vpn proposals ike-phase1-proposal
          set security ike policy ike_pol_onprem-2-gcp-vpn pre-shared-key ascii-text [*****]

#### Configure IKEv2 Gateway

An IKEv2 profile must be configured and must be attached to an IPsec profile on both the IKEv2 initiator and the responder.

In this block, the following parameters are set:

-   **DPD**: The dead peer detection interval and retry threshold. If there are no responses from the peer, the security
    association created for that peer is deleted. Set the DPD type to `probe-idle-tunnel`, the DPD interval to `20`, and the
    DPD retry threshold to `4`.
-   **IKE**: Set the IKE remote address, IKE external interface, and the IKE version (v2). Set the IKE local identity to
    the IP address of the external interface. If the SRX device is behind a NAT, the local identity should be configured as
    the public IP address of the NAT. Where the NAT maps to a pool of public IP addresses, a dedicated 1-to-1 NAT should be
    configured to the SRX device.

        [edit]
          root@vsrx#
          set security ike gateway gw_onprem-2-gcp-vpn ike-policy ike_pol_onprem-2-gcp-vpn
          set security ike gateway gw_onprem-2-gcp-vpn address 35.187.170.191
          set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection probe-idle-tunnel
          set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection interval 20
          set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection threshold 4
          set security ike gateway gw_onprem-2-gcp-vpn external-interface ge-0/0/1.0
          set security ike gateway gw_onprem-2-gcp-vpn version v2-only
    
        #Configure local-identity as public IP address of the VPN device, if behind NAT
          set security ike gateway gw_onprem-2-gcp-vpn local-identity inet 104.196.65.171

### Configure the IPsec security association

Define the IPsec parameters that are used for IPsec encryption between two IPsec routers in IPsec profile configuration.

In this block, the following parameters are set:

-   **IPsec SA lifetime**: Setting `lifetime-seconds` to `3600` (1 hour) is recommended for most VPN sessions. The default
    on a Juniper SRX is 3600 seconds.
-   **Perfect Forward Secrecy (PFS)**: PFS forces a new Diffie-Hellman key exchange. The same key will not be generated
    again. This value is set to `group14`. 

        [edit]
          root@vsrx#
          set security ipsec proposal ipsec-phase2-proposal protocol esp
          set security ipsec proposal ipsec-phase2-proposal lifetime-seconds 3600
          set security ipsec proposal ipsec-phase2-proposal authentication-algorithm hmac-sha-256-128
          set security ipsec proposal ipsec-phase2-proposal encryption-algorithm aes-256-cbc
          set security ipsec policy ipsec_pol_home-2-gcp-vpn perfect-forward-secrecy keys group14
          set security ipsec policy ipsec_pol_home-2-gcp-vpn proposals ipsec-phase2-proposal

#### Configure IPsec profile and tunnel binding interface

A tunnel interface is configured to be the logical interface associated with the tunnel. All traffic routed to the tunnel 
interface will be encrypted and transmitted to GCP. Similarly, traffic from GCP will be logically received on this 
interface.

Adjust the maximum segment size (MSS) value of TCP packets going through a router. The recommended value is `1360` when the
number of IP MTU bytes is set to 1460.

With these recommended settings, TCP sessions quickly scale back to 1400-byte IP packets so the packets will "fit" in the
tunnel.

       [edit]
       root@vsrx#
       set security ipsec vpn home-2-gcp-vpn bind-interface st0.0
       set security ipsec vpn home-2-gcp-vpn ike gateway gw_home-2-gcp-vpn
       set security ipsec vpn home-2-gcp-vpn ike ipsec-policy ipsec_pol_home-2-gcp-vpn
       set security ipsec vpn home-2-gcp-vpn establish-tunnels immediately
       set security flow tcp-mss ipsec-vpn mss 1360
       set security flow tcp-session rst-invalidate-session

#### Configure security zones and policies

##### Security zone configuration

Juniper SRX uses security zones to isolate network segments and regulates traffic inbound and outbound from these zones 
using security policies. Security zones logically bind interfaces (which may represent network segments). For this 
configuration, there are three security zones: the `untrust` zone, with which the internet-facing interface `ge-0/0/0.0` is
bound; the `trust` zone, with which the internal-facing interfaces `ge-0/0/1.0`and `ge-0/0/2.0` are bound; and the `vpn-gcp`
zone, with which the VPN tunnel interface `st0.0` is bound. In addition to binding interfaces to the defined zones, traffic
destined for the Juniper device is allowed or denied in the security zone configuration; also, address-book configuration
(which can be used in security policies to specify what IP addresses are allowed to pass traffic from a zone) is configured
here. For more information on how to configure security zones, see
[Juniper security zone configuration](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/security-zone-configuration.html).

Below is the security zone configuration for the on-premises Juniper SRX300 device:

    [edit]
    root@vsrx#
    set security zones security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services ike
    set security zones security-zone vpn-gcp host-inbound-traffic protocols bgp
    set security zones security-zone vpn-gcp interfaces st0.0
    
    # Allow BGP Session
    set security zones security-zone vpn-gcp host-inbound-traffic protocols bgp
    
    #Address book configuration on-prem prefix
    set security zones security-zone trust address-book address 192.168.0.0/24 192.168.0.0/24
    set security zones security-zone trust address-book address 192.168.1.0/24 192.168.1.0/24
    set security zones security-zone trust address-book address 172.16.0.0/24 172.16.0.0/24
    set security zones security-zone trust address-book address 172.16.1.0/24 172.16.1.0/24
    set security zones security-zone trust address-book address-set onprem-addr-prefixes address 192.168.0.0/24
    set security zones security-zone trust address-book address-set onprem-addr-prefixes address 192.168.1.0/24
    set security zones security-zone trust address-book address-set onprem-addr-prefixes address 172.16.0.0/24
    set security zones security-zone trust address-book address-set onprem-addr-prefixes address 172.16.1.0/24
    set security zones security-zone trust tcp-rst
    set security zones security-zone trust host-inbound-traffic system-services all
    set security zones security-zone trust host-inbound-traffic protocols all
    set security zones security-zone trust interfaces ge-0/0/1.0
    set security zones security-zone trust interfaces ge-0/0/2.0
    set security zones security-zone untrust screen untrust-screen
    set security zones security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services dhcp
    set security zones security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services tftp
    set security zones security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services ssh
    set security zones security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services ike
    set security zones security-zone vpn-gcp host-inbound-traffic protocols bgp
    set security zones security-zone vpn-gcp interfaces st0.0
    
    #Address book configuration for GCP prefixes
    set security zones security-zone vpn-gcp address-book address 10.120.0.0/16 10.120.0.0/16
    set security zones security-zone vpn-gcp address-book address 10.121.0.0/16 10.121.0.0/16
    set security zones security-zone vpn-gcp address-book address-set gcp-addr-prefixes address 10.120.0.0/16
    set security zones security-zone vpn-gcp address-book address-set gcp-addr-prefixes address 10.121.0.0/16

##### Configure security policies

Security policies are statements that allow for control to placed on traffic going from a specific source to a specific 
destination using a specific service or IP address. For more information on security zones, see
[Juniper security policy configuration](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/security-policy-configuration.html).

For the configuration below, the sources and destinations are the zones `untrust`, `trust`, and `vpn-gcp` configured above. 

    [edit]
    root@vsrx#
    set security policies from-zone trust to-zone trust policy default-permit match source-address any
    set security policies from-zone trust to-zone trust policy default-permit match destination-address any
    set security policies from-zone trust to-zone trust policy default-permit match application any
    set security policies from-zone trust to-zone trust policy default-permit then permit
    set security policies from-zone trust to-zone trust policy trust-to-trust match source-address any
    set security policies from-zone trust to-zone trust policy trust-to-trust match destination-address any
    set security policies from-zone trust to-zone trust policy trust-to-trust match application any
    set security policies from-zone trust to-zone trust policy trust-to-trust then permit
    set security policies from-zone trust to-zone untrust policy default-permit match source-address any
    set security policies from-zone trust to-zone untrust policy default-permit match destination-address any
    set security policies from-zone trust to-zone untrust policy default-permit match application any
    set security policies from-zone trust to-zone untrust policy default-permit then permit
    set security policies from-zone trust to-zone untrust policy trust-to-untrust match source-address any
    set security policies from-zone trust to-zone untrust policy trust-to-untrust match destination-address any
    set security policies from-zone trust to-zone untrust policy trust-to-untrust match application any
    set security policies from-zone trust to-zone untrust policy trust-to-untrust then permit
    set security policies from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match source-address onprem-addr-prefixes
    set security policies from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match destination-address gcp-addr-prefixes
    set security policies from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match application any
    set security policies from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn then permit
    set security policies from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match source-address gcp-addr-prefixes
    set security policies from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match destination-address onprem-addr-prefixes
    set security policies from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match application any
    set security policies from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn then permit

### Configuring the dynamic routing protocol

BGP is used within the tunnel to exchange prefixes between the GCP Cloud Router and the Juniper SRX appliance. The GCP
Cloud Router will announce the prefix corresponding to your GCP VPC.

BGP timers are adjusted to provide more rapid detection of outages.

1.  Configure BGP peering between SRX and Cloud Router

        [edit]
        root@vsrx#
        set protocols bgp group ebgp-peers type external
        set protocols bgp group ebgp-peers multihop
        set protocols bgp group ebgp-peers local-as 65501
        set protocols bgp group ebgp-peers neighbor 169.254.1.1 peer-as 65500

1.  Configure routing policies to inject routes into BGP and advertise it to the Cloud Router. In this case, only
    `192.168.0.0/24` and `192.168.1.0/24` are advertised:

        [edit]
        root@vsrx#
        set policy-options policy-statement gcp-bgp-policy term 1 from protocol direct
        set policy-options policy-statement gcp-bgp-policy term 1 from route-filter 192.168.1.0/24 exact
        set policy-options policy-statement gcp-bgp-policy term 1 then accept
        set policy-options policy-statement gcp-bgp-policy term 2 from protocol direct
        set policy-options policy-statement gcp-bgp-policy term 2 from route-filter 192.168.0.0/24 exact
        set policy-options policy-statement gcp-bgp-policy term 2 then accept
        set protocols bgp group ebgp-peers export gcp-bgp-policy

### Configuring static routing (optional if using Cloud Router)

Follow the procedure in this section to configure static routing of traffic to the GCP network through the VPN tunnel 
interface `st0.0`.

    [edit]
    root@vsrx#
    set routing-options static route 10.120.0.0/16 next-hop st0.0
    set routing-options static route 10.121.0.0/16 next-hop st0.0

For more recommendations about on-premises routing configurations, see
[GCP best practices](https://cloud.google.com/router/docs/resources/best-practices).

### Saving the configuration

Use this command to save the on-premises configuration:

    root@vsrx# commit and-quit 

### Testing and verifying the VPN configuration and connectivity

It's important to test the VPN connection from both sides of a VPN tunnel. For either side, make sure that the subnet that
a machine or virtual machine is located in is being forwarded through the VPN tunnel.

First, create VMs/hosts on both sides of the tunnel, depending on the scenario being tested. Make sure that you configure
the VMs/hosts on a subnet that will pass traffic through the VPN tunnel.

Instructions for creating virtual machines in Compute Engine are located in the
[getting started guide](https://cloud.google.com/compute/docs/quickstart).

After VMs have been deployed on both the GCP and the other side of the tunnel (for example, on-premises or another cloud),
you can use an ICMP echo (`ping`) test to test network connectivity through the VPN tunnel, and you can use `telnet` or 
`netcat` to test TCP connectivity.

On the GCP side, use the following instructions to test the connection to a machine that's behind the on-premises gateway:

1.  In the GCP Console, go to the [VM instances page](https://console.cloud.google.com/compute).
1.  Find the GCP virtual machine you created.
1.  In the **Connect** column, click **SSH**. A browser window opens at the VM command line.
1.  Ping a machine that's behind the on-premises gateway:

        root@freebsd:~ # ping 192.168.1.91
        PING 192.168.1.91 (192.168.1.91): 56 data bytes
        64 bytes from 192.168.1.91: icmp_seq=0 ttl=63 time=21.387 ms
        64 bytes from 192.168.1.91: icmp_seq=1 ttl=63 time=19.402 ms
        64 bytes from 192.168.1.91: icmp_seq=2 ttl=63 time=20.535 ms
        64 bytes from 192.168.1.91: icmp_seq=3 ttl=63 time=35.592 ms
        64 bytes from 192.168.1.91: icmp_seq=4 ttl=63 time=23.347 ms
        64 bytes from 192.168.1.91: icmp_seq=5 ttl=63 time=17.600 ms
        64 bytes from 192.168.1.91: icmp_seq=6 ttl=63 time=19.083 ms
        64 bytes from 192.168.1.91: icmp_seq=7 ttl=63 time=19.383 ms
        64 bytes from 192.168.1.91: icmp_seq=8 ttl=63 time=21.689 ms
        64 bytes from 192.168.1.91: icmp_seq=9 ttl=63 time=28.000 ms
        ^C
        --- 192.168.1.91 ping statistics ---
        11 packets transmitted, 10 packets received, 9.1% packet loss
        round-trip min/avg/max/stddev = 17.600/22.602/35.592/5.129 ms
        root@freebsd:~ #

##### Testing and verifying VPN connectivity on Juniper SRX

1.  Show IKE security associations:

        root@vsrx# run show security ike security-associations
        Index   State  Initiator cookie  Responder cookie  Mode           Remote Address
        7877087 UP     412c5a43aad7682b  b6d24ef8bf25e9ea  IKEv2          35.187.170.191

1.  Show IPsec security associations:

        root@vsrx# run show security ipsec security-associations
        Total active tunnels: 1
        ID    Algorithm       SPI      Life:sec/kb  Mon lsys Port  Gateway
        <131073 ESP:aes-cbc-256/sha256 9beb1bf0 729/ unlim - root 4500 35.187.170.191
        >131073 ESP:aes-cbc-256/sha256 97791a28 729/ unlim - root 4500 35.187.170.191

1.  List BGP learned routes:

        root@vsrx# run show route protocol bgp
   
        inet.0: 11 destinations, 11 routes (11 active, 0 holddown, 0 hidden)
        + = Active Route, - = Last Active, * = Both
        
        10.120.0.0/16      *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0
        10.121.0.0/16      *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0
        10.122.0.0/16      *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0

1.  Ping an IP address in GCP through the tunnel:

        root@vsrx> ping 10.120.0.2 count 5 source 192.168.1.1
        PING 10.120.0.2 (10.120.0.2): 56 data bytes
        64 bytes from 10.120.0.2: icmp_seq=0 ttl=64 time=20.758 ms
        64 bytes from 10.120.0.2: icmp_seq=1 ttl=64 time=20.024 ms
        64 bytes from 10.120.0.2: icmp_seq=2 ttl=64 time=23.783 ms
        64 bytes from 10.120.0.2: icmp_seq=3 ttl=64 time=19.472 ms
        64 bytes from 10.120.0.2: icmp_seq=4 ttl=64 time=21.183 ms
        
        --- 172.16.0.2 ping statistics ---
        5 packets transmitted, 5 packets received, 0% packet loss
        round-trip min/avg/max/stddev = 19.472/21.044/23.783/1.491 ms
        
        root@vsrx>

## Advanced VPN configuration

This section covers how to configure redundant on-premises VPN gateways and how to get higher throughput through VPN
tunnels.

### Configuring VPN redundancy

Using redundant on-premises VPN gateways ensures continuous availability when a tunnel fails. The article
[Redundancy and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns) in the Cloud VPN 
documentation provides configuration guidelines for both GCP and on-premises VPN gateways, including guidance on setting 
route priorities for redundant gateways. Juniper SRX devices use chassis clustering to provide high availability. This 
feature is not supported in the SRX300 series devices. See
[Chassis Clustering](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/security-chassis-cluster-verification.html) and
[Chassis Cluster Overview](https://www.juniper.net/documentation/en_US/release-independent/nce/topics/concept/chassis-cluster-high-end-srx-overview.html) for more information.

To achieve high availability in the SRX300 platform, multiple (at least two) SRX300 devices are needed. The high 
availability is accomplished by manipulating BGP routing within the devices. This is beyond the scope of this document. See
the [Juniper BGP Feature Guide](https://www.juniper.net/documentation/en_US/junos/information-products/pathway-pages/config-guide-routing/config-guide-routing-bgp.html)
for more in-depth information on how to configure BGP (internal and external) and manipulate BGP attributes for different 
route preferences.

This section contains procedures for configuring route priority settings on Juniper SRX300 and GCP. The GCP instructions 
assume that you have built each GCP gateway in a set of redundant gateways as described in the
[dynamic routing section](#configuring-an-ipsec-vpn-using-dynamic-routing) and configured the **Advertised route priority** 
field when you [configured the VPN gateway](#configure-the-vpn-gateway). If you didn't do this, then you will need to create
a new tunnel and BGP session for the gateways involved and configure the Advertised route priority field as described in the 
following sections.

Note: Some of the procedures in this section use `gcloud` commands. For information about using `gcloud` commands, and about
setting environment variables for parameter values such as the GCP network name, see the
[appendix](#appendix-using-gcloud-commands).

#### Configuring Juniper SRX300 dynamic route priority settings using BGP MED

GCP Cloud Router uses only BGP MED (Multi-Exit Discriminator) values to determine route priorities. For more information,
see [this page](https://cloud.google.com/router/docs/concepts/overview). MED is a routing metric; routes with lower values
are considered better routes. MED values on SRX300 devices can be set for all prefixes per neighbor or for specific 
routes using route filters. See the 
[Configuring BGP MED](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/bgp-med.html) and
[Configuring the MED Using Route Filters](https://www.juniper.net/documentation/en_US/junos/topics/example/bgp-med-route-filter.html)
sections of the Juniper documentation for details of how to set BGP MED in the Juniper SRX300.

This sample configuration sets MED values of all routes advertised to a BGP neighbor (for example, GCP Cloud Router) to 
`100`:

    set protocols bgp group ebgp-peers neighbor 169.254.0.1 metric-out 100

Note: The `set protocols bgp metric-out [METRIC_VALUE]` command sets the BGP metric for all neighbors, which may be
undesirable.

To list the BGP metrics of routes received by a BGP peer (GCP Cloud Router), enter the command below. The MED is shown in
the third column.

    root@vsrx# run show route receive-protocol bgp 169.254.0.1    

    inet.0: 11 destinations, 11 routes (11 active, 0 holddown, 0 hidden)
      Prefix                 Nexthop              MED     Lclpref    AS path
    * 10.120.0.0/16          169.254.0.1          100                65500 ?
    * 10.121.0.0/16          169.254.0.1          100                65500 ?
    * 10.122.0.0/16          169.254.0.1          100                65500 ?

#### Configuring Juniper SRX300 static route metrics

Route metrics can be configured with Juniper SRX300 static routes, which dictate how the device chooses paths for 
packets to the destination prefix. Static route metrics can be useful when the device has multiple tunnels to GCP and 
BGP is not used to exchange prefixes between GCP and on-premises, and preferences need to placed on the tunnels.

This configuration sets static routes with metrics in the Juniper SRX300:

    set routing-options static route 172.16.0.0/16 next-hop st0.0 metric 100

#### Configuring GCP BGP route priority

With GCP dynamic routing, you can configure advertised route priority. For details, see the
[Cloud Router overview](https://cloud.google.com/router/docs/concepts/overview) and the
[Cloud Router API documentation](https://cloud.google.com/sdk/gcloud/reference/compute/routers/update-bgp-peer). If you have 
a preferred route announced to the on-premises side of the network, BGP prefers the higher-priority on-premises route.

You can set BGP route priority using [the console](#configure-the-vpn-gateway) or the following `gcloud` command.

Note the following:

-   Make sure that you've set environment variables as described in the [appendix](#appendix-using-gcloud-commands).
-   For `[PEER_ASN]`, use a [private ASN](https://tools.ietf.org/html/rfc6996) value
    (`64512–65534`, `4200000000–4294967294`) that's not already in use, such as `65001`.
-   For `[PRIORITY]`, use an appropriate value, such as `2000`.
-   For `[PEER-IP-ADDRESS]`, use an address in the range `169.254.n.n`.

        gcloud compute --project $PROJECT_NAME routers add-bgp-peer \
            $CLOUD_ROUTER_NAME \
            --peer-name $BGP_SESSION_NAME \
            --interface $BGP_IF \
            --peer-ip-address [PEER-IP-ADDRESS] \
            --peer-asn [PEER_ASN] \
            --region $REGION \
            --advertised-route-priority=[PRIORITY]

#### Configuring GCP static route priority

When you use static routing, GCP gives you an option to customize route priority if there are multiple routes with the same
prefix length. To enable symmetric traffic flow, make sure that you set the priority of your secondary GCP tunnel to a 
higher value than the primary tunnel. (The default priority is 1000.) To define the route priority, run the command below.

Note the following:

-   Make sure that you've set environment variables as described in the [appendix](#appendix-using-gcloud-commands).
-   For `[PRIORITY]`, use an appropriate priority value, such as `2000`.

        gcloud compute routes create $ROUTE_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --next-hop-vpn-tunnel $VPN_TUNNEL_1 \
            --next-hop-vpn-tunnel-region $REGION \
            --destination-range $IP_ON_PREM_SUBNET \
            --priority=[PRIORITY]

### Getting higher throughput

Each Cloud VPN tunnel can support up to 3 Gbps when the tunnel traffic traverses a direct peering link, or 1.5 Gbps when 
the tunnel traffic traverses the public internet. For more information, see
[Redundant and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns).

#### Configuring GCP for higher throughput

To increase throughput, add multiple Cloud VPN gateways in the same region to load-balance the traffic across the tunnels. 
For more information, see the [Topology](#topology) section in this guide. 

GCP performs ECMP routing by default, so no additional configuration is required apart from creating the number of tunnels 
that meet your throughput requirements. You can either use a single VPN gateway to create multiple tunnels, or you can 
create a separate VPN gateway for each tunnel.

Actual tunnel throughput can vary, depending on the following factors:

-   **Network capacity**: Bandwidth between the GCP and on-premises VPN gateways is a limiting factor.
-   **Capabilities of the on-premises VPN device**: See your device's documentation for more information.
-   **Packet size**: Because processing happens on a per-packet basis, traffic with a significant percentage of smaller 
    packets can reduce overall throughput.
-   **[High round-trip time (RTT)](https://en.wikipedia.org/wiki/Round-trip_delay_time) and packet loss rates**: These
    factors can greatly reduce throughput for TCP.

#### Configuring Juniper SRX300 for higher throughput (using ECMP)

Juniper SRX300 uses ECMP to forward traffic when multiple paths exists to a destination prefix and all of the metrics 
considered for selecting paths to the destination are the equal. For more information on how BGP routing decisions are made
in the SRX300, see
[BGP Path Selection](https://www.juniper.net/documentation/en_US/junos/topics/reference/general/routing-protocols-address-representation.html).

##### Juniper SRX configuration

This section includes the complete configuration for setting up multiple tunnels on the same SRX300 device for higher 
throughput.

###### Configure basic networking

    [edit]
    root@vsrx#
    # Internal interface configuration
    set interfaces ge-0/0/1 unit 0 family inet address 192.168.0.1/24
    set interfaces ge-0/0/1 unit 0 description "internal facing interface"
    set interfaces ge-0/0/2 unit 0 family inet address 192.168.1.1/24
    set interfaces ge-0/0/2 unit 0 description "internal facing interface"
    # External interface configuration
    set interfaces ge-0/0/0 unit 0 family inet address 76.104.213.79/31
    set interfaces ge-0/0/0 unit 0 description "external facing interface"
    # Tunnel interfaces configuration
    set interfaces st0 unit 0 family inet mtu 1460
    set interfaces st0 unit 0 family inet address 169.254.1.2/30
    set interfaces st0 unit 1 family inet mtu 1460
    set interfaces st0 unit 1 family inet address 169.254.2.2/30

###### Configure IKE policy and IKE gateway

    [edit]
    root@vsrx#
    set security ike policy ike_pol_onprem-2-gcp-vpn mode main
    set security ike policy ike_pol_onprem-2-gcp-vpn proposal-set standard
    set security ike policy ike_pol_onprem-2-gcp-vpn pre-shared-key ascii-text "********"
    set security ike gateway gw_onprem-2-gcp-vpn ike-policy ike_pol_onprem-2-gcp-vpn
    set security ike gateway gw_onprem-2-gcp-vpn address 35.230.59.183
    set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection probe-idle-tunnel
    set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection interval 20
    set security ike gateway gw_onprem-2-gcp-vpn dead-peer-detection threshold 3
    set security ike gateway gw_onprem-2-gcp-vpn local-identity inet 76.104.213.79
    set security ike gateway gw_onprem-2-gcp-vpn external-interface ge-0/0/0.0
    set security ike gateway gw_onprem-2-gcp-vpn version v2-only
    set security ike gateway gw_onprem-2-gcp-vpn-2 ike-policy ike_pol_onprem-2-gcp-vpn
    set security ike gateway gw_onprem-2-gcp-vpn-2 address 35.233.197.145
    set security ike gateway gw_onprem-2-gcp-vpn-2 dead-peer-detection probe-idle-tunnel
    set security ike gateway gw_onprem-2-gcp-vpn-2 dead-peer-detection interval 20
    set security ike gateway gw_onprem-2-gcp-vpn-2 dead-peer-detection threshold 3
    set security ike gateway gw_onprem-2-gcp-vpn-2 local-identity inet 76.104.213.79
    set security ike gateway gw_onprem-2-gcp-vpn-2 external-interface ge-0/0/0.0
    set security ike gateway gw_onprem-2-gcp-vpn-2 version v2-only

###### Configure IPsec policy and IPsec VPN

Note the use of Juniper's built-in proposal set (`standard`) in the `ike policy` configuration above and in the
`ipsec policy` configuration below.

    [edit]
    root@vsrx#
    set security ipsec policy ipsec_pol_onprem-2-gcp-vpn perfect-forward-secrecy keys group2
    set security ipsec policy ipsec_pol_onprem-2-gcp-vpn proposal-set standard
    set security ipsec policy ipsec_pol_onprem-2-gcp-vpn-2 perfect-forward-secrecy keys group2
    set security ipsec policy ipsec_pol_onprem-2-gcp-vpn-2 proposal-set standard
    set security ipsec vpn onprem-2-gcp-vpn bind-interface st0.0
    set security ipsec vpn onprem-2-gcp-vpn ike gateway gw_onprem-2-gcp-vpn
    set security ipsec vpn onprem-2-gcp-vpn ike ipsec-policy ipsec_pol_onprem-2-gcp-vpn
    set security ipsec vpn onprem-2-gcp-vpn establish-tunnels immediately
    set security ipsec vpn onprem-2-gcp-vpn-2 bind-interface st0.1
    set security ipsec vpn onprem-2-gcp-vpn-2 ike gateway gw_onprem-2-gcp-vpn-2
    set security ipsec vpn onprem-2-gcp-vpn-2 ike ipsec-policy ipsec_pol_onprem-2-gcp-vpn-2
    set security ipsec vpn onprem-2-gcp-vpn-2 establish-tunnels immediately
    set security flow tcp-mss ipsec-vpn mss 1300

###### Configure security zones

    [edit]
    root@vsrx# edit security zones
    
    [edit security zones]
    root@vsrx#
    set security-zone trust address-book address addr_192_168_1_0_24 192.168.1.0/24
    set security-zone trust host-inbound-traffic system-services all
    set security-zone trust host-inbound-traffic protocols all
    set security-zone trust interfaces irb.0
    set security-zone untrust interfaces ge-0/0/0.0 host-inbound-traffic system-services ike
    set security-zone vpn-gcp address-book address 10.0.0.0/8 10.0.0.0/8
    set security-zone vpn-gcp address-book address 172.16.0.0/16 172.16.0.0/16
    set security-zone vpn-gcp address-book address-set gcp-addr-prefixes address 172.16.0.0/16
    set security-zone vpn-gcp address-book address-set gcp-addr-prefixes address 10.0.0.0/8
    set security-zone vpn-gcp host-inbound-traffic protocols bgp
    set security-zone vpn-gcp interfaces st0.0
    set security-zone vpn-gcp interfaces st0.1

    [edit security zones]
    root@vsrx#
    exit

###### Configure security policies

    [edit]
    root@vsrx# edit security policies
    
    [edit security policies]
    root@vsrx#
    set from-zone trust to-zone trust policy trust-to-trust match source-address any
    set from-zone trust to-zone trust policy trust-to-trust match destination-address any
    set from-zone trust to-zone trust policy trust-to-trust match application any
    set from-zone trust to-zone trust policy trust-to-trust then permit
    set from-zone trust to-zone untrust policy trust-to-untrust match source-address any
    set from-zone trust to-zone untrust policy trust-to-untrust match destination-address any
    set from-zone trust to-zone untrust policy trust-to-untrust match application any
    set from-zone trust to-zone untrust policy trust-to-untrust then permit
    set from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match source-address addr_192_168_1_0_24
    set from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match destination-address gcp-addr-prefixes
    set from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn match application any
    set from-zone trust to-zone vpn-gcp policy policy_out_onprem-2-gcp-vpn then permit
    set from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match source-address gcp-addr-prefixes
    set from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match destination-address addr_192_168_1_0_24
    set from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn match application any
    set from-zone vpn-gcp to-zone trust policy policy_in_onprem-2-gcp-vpn then permit

    [edit security policies]
    root@vsrx#
    exit

###### Configure BGP routing

    [edit]
    root@vsrx#
    set routing-options aggregate route 192.168.1.0/24
    set protocols bgp group ebgp-peers type external
    set protocols bgp group ebgp-peers multihop
    set protocols bgp group ebgp-peers export gcp-bgp-policy
    set protocols bgp group ebgp-peers local-as 65501
    set protocols bgp group ebgp-peers neighbor 169.254.1.1 peer-as 65500
    set protocols bgp group ebgp-peers neighbor 169.254.2.1 peer-as 65500
    set protocols l2-learning global-mode switching
    set policy-options policy-statement gcp-bgp-policy term 1 from protocol direct
    set policy-options policy-statement gcp-bgp-policy term 1 from route-filter 192.168.1.0/24 exact
    set policy-options policy-statement gcp-bgp-policy term 1 then accept
    
    [edit]
    root@vsrx#

#### Testing the higher-throughput configuration

You can test the IPsec tunnel from GCP with the instructions in the
[Building high-throughput VPNs](https://cloud.google.com/solutions/building-high-throughput-vpns) guide.
You can verify and test that multiple tunnels have been initiated and established between your on-premises environment and 
GCP with the commands below.

###### Listing security associations for bundled tunnel

1.  Show IKE security associations:

        root@vsrx# run show security ike security-associations
        Index   State  Initiator cookie  Responder cookie  Mode           Remote Address
        1590399 UP     e1f16b380e661b93  34379d5726ea8545  IKEv2          35.233.197.145
        1590402 UP     9d0688eeb4ced592  3e2a86428dbd9d01  IKEv2          35.230.59.183

1.  Show IPsec security associations:

        root@vsrx# run show security ipsec security-associations
          Total active tunnels: 2
          ID    Algorithm       SPI      Life:sec/kb  Mon lsys Port  Gateway
          <131073 ESP:aes-cbc-128/sha1 a2fde6d8 2618/ unlim - root 500 35.230.59.183
          >131073 ESP:aes-cbc-128/sha1 a1854938 2618/ unlim - root 500 35.230.59.183
          <131074 ESP:aes-cbc-128/sha1 9b593cad 2310/ unlim - root 500 35.233.197.145
          >131074 ESP:aes-cbc-128/sha1 6ecac98d 2310/ unlim - root 500 35.233.197.145

###### Listing routing table

As shown below, there are multiple paths listed for the BGP routes. This indicates that packets destined for routes in GCP 
will be routed with ECMP.

    root@vsrx# run show route
    
    inet.0: 59 destinations, 88 routes (59 active, 0 holddown, 0 hidden)
    + = Active Route, - = Last Active, * = Both
    
    10.44.0.0/14       *[BGP/170] 00:00:17, MED 371, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.1.1 via st0.0
                        [BGP/170] 00:00:36, MED 371, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.2.1 via st0.1
    10.110.0.0/20      *[BGP/170] 00:00:17, MED 371, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.1.1 via st0.0
                        [BGP/170] 00:00:36, MED 371, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.2.1 via st0.1
    10.128.0.0/20      *[BGP/170] 00:00:17, MED 337, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.1.1 via st0.0
                        [BGP/170] 00:00:36, MED 337, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.2.1 via st0.1
    10.132.0.0/20      *[BGP/170] 00:00:17, MED 448, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.1.1 via st0.0
                        [BGP/170] 00:00:36, MED 448, localpref 100
                          AS path: 65500 ?, validation-state: unverified
                        > to 169.254.2.1 via st0.1

BGP peers listed from BGP summary:

    root@vsrx# run show bgp summary
    Groups: 1 Peers: 2 Down peers: 0
    Table          Tot Paths  Act Paths Suppressed    History Damp State    Pending
    inet.0
                          56         28          0          0          0          0
    Peer                     AS      InPkt     OutPkt    OutQ   Flaps Last Up/Dwn State|#Active/Received/Accepted/Damped...
    169.254.1.1           65500         36         21       0       5        5:48 28/28/28/0           0/0/0/0
    169.254.2.1           65500         37         23       0       0        6:07 0/28/28/0            0/0/0/0

Finally, run pings from on-premises to GCP and vice-versa:

    root@freebsd:~ # ping 192.168.1.91
    PING 192.168.1.91 (192.168.1.91): 56 data bytes
    64 bytes from 192.168.1.91: icmp_seq=0 ttl=63 time=21.387 ms
    64 bytes from 192.168.1.91: icmp_seq=1 ttl=63 time=19.402 ms
    64 bytes from 192.168.1.91: icmp_seq=2 ttl=63 time=20.535 ms
    64 bytes from 192.168.1.91: icmp_seq=3 ttl=63 time=35.592 ms
    64 bytes from 192.168.1.91: icmp_seq=4 ttl=63 time=23.347 ms
    64 bytes from 192.168.1.91: icmp_seq=5 ttl=63 time=17.600 ms
    64 bytes from 192.168.1.91: icmp_seq=6 ttl=63 time=19.083 ms
    64 bytes from 192.168.1.91: icmp_seq=7 ttl=63 time=19.383 ms
    64 bytes from 192.168.1.91: icmp_seq=8 ttl=63 time=21.689 ms
    64 bytes from 192.168.1.91: icmp_seq=9 ttl=63 time=28.000 ms
    ^C
    --- 192.168.1.91 ping statistics ---
    11 packets transmitted, 10 packets received, 9.1% packet loss
    round-trip min/avg/max/stddev = 17.600/22.602/35.592/5.129 ms
    root@freebsd:~ #

## Troubleshooting IPsec on Juniper SRX300

For troubleshooting information, see the
[Juniper SRX VPN troubleshooting guide](https://kb.juniper.net/InfoCenter/index?page=content&id=KB21899&actp=METADATA), 
which includes the JTAC-certified resolution guide for SRX VPNs. 

## Reference documentation

Refer to the following documentation for additional information.

### GCP documentation

To learn more about GCP networking, see the following documents:

-  [VPC networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Creating route-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-route-based-vpns)
-  [Creating policy-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-policy-based-vpns)
-  [Advanced Cloud VPN configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### Juniper SRX documentation

For more information about Juniper SRX devices, see the following documents:

-  [Juniper Route-Based IPsec VPNs](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/security-route-based-ipsec-vpns.html)
-  [Juniper Security Policies](https://www.juniper.net/documentation/en_US/junos/information-products/pathway-pages/security/security-policies-feature-guide.html)
-  [Juniper BGP Feature Guide](https://www.juniper.net/documentation/en_US/junos/topics/concept/routing-protocol-bgp-security-peering-session-understanding.html)

For common Juniper SRX troubleshooting steps and commands, see the following documents:

-  [Troubleshooting VPNs in SRX](https://kb.juniper.net/InfoCenter/index?page=content&id=KB10104&actp=METADATA)
-  [Checklist for verifying BGP in JunOS](https://www.juniper.net/documentation/en_US/junos/topics/task/verification/bgp-configuration-process-summary.html)

## Appendix: Using gcloud commands

The instructions in this guide focus on using the GCP Console. However, you can perform many of the tasks for the GPC side 
of the VPN configuration by using the [gcloud command-line tool](https://cloud.google.com/sdk/gcloud/). Using `gcloud`  
commands can be faster and more convenient if you're comfortable using a command-line interface.

### Running gcloud commands

You can run `gcloud` commands on your local computer by installing the [Cloud SDK](https://cloud.google.com/sdk/). 
Alternatively, you can run `gcloud` commands in [Cloud Shell](https://cloud.google.com/shell/), a browser-based command 
shell. If you use Cloud Shell, you don't need to install the SDK on your own computer, and you don't need to set up 
authentication.

Note: The `gcloud` commands presented in this guide assume that you're working in a Linux environment. (Cloud Shell is a 
Linux environment.)

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must provide. For example, a command might include a
GCP project name or a region or other parameters whose values are unique to your context. The following table lists the 
parameters and gives examples of the values. The section that follows the table describes how to set Linux environment 
variables to hold the values that you need for these parameters.


| Parameter description | Placeholder          | Example value                             |
|-----------------------|----------------------|-------------------------------------------|
| GCP project name      | `[PROJECT_NAME]`     | `vpn-guide`                               |
| Shared secret         | `[SHARED_SECRET]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key). |
| VPC network name      | `[VPC_NETWORK_NAME]` | `vpn-juniper-test-network` |
| Subnet on the GCP VPC network (for example, `vpn-juniper-test-network`) | `[VPC_SUBNET_NAME]` | `vpn-subnet-1` |
| GCP region. Can be any region, but should be geographically close to the on-premises gateway. | `[REGION]` | `us-east1` |
| Pre-existing external static IP address that you configure for the internet side of the Cloud VPN gateway. | `[STATIC_EXTERNAL_IP]` | `vpn-test-static-ip` |
| IP address range for the GCP VPC subnet (`vpn-subnet-1`) | `[SUBNET_IP]` | `172.16.100.0/24` and `172.16.200.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to GCP. | `[IP_ON_PREM_SUBNET]` | `10.1.0.0/16` and `10.0.0.0/16` |
| External static IP address for the internet interface of Juniper SRX | `[CUST_GW_EXT_IP]` | `199.203.248.181` |
| Cloud Router name (for dynamic routing) | `[CLOUD_ROUTER_NAME]` | `vpn-test-juniper-rtr` |
| BGP interface name    | `[BGP_IF]` | `if-1` |
| BGP session name (for dynamic routing) | `[BGP_SESSION_NAME]` | `bgp-peer1` |
| Name for the first GCP VPN gateway | `[VPN_GATEWAY_1]`    | `vpn-test-juniper-gw-1` |
| Name for the first VPN tunnel for `vpn-test-juniper-gw-1` | `[VPN_TUNNEL_1]` | `vpn-test-tunnel1` |
| Name of a firewall rule that allows traffic between the on-premises network and GCP VPC networks | `[VPN_RULE]` | `vpnrule1` |
| Name for the [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create) used to forward traffic to the on-premises network. Note: You need this value only if you are creating a VPN using a static route. | `[ROUTE_NAME]` | `vpn-static-route` |
| Name for the forwarding rule for the [ESP protocol](https://wikipedia.org/wiki/IPsec#Encapsulating_Security_Payload) | `[FWD_RULE_ESP]` | `fr-esp` |
| Name for the forwarding rule for the (https://wikipedia.org/wiki/User_Datagram_Protocol)[UDP protocol], port 500 | `[FWD_RULE_UDP_500]` | `fr-udp500` |
| Name for the forwarding rule for the UDP protocol, port 4500 | `[FWD_RULE_UDP_4500]` | `fr-udp4500` |

### Setting environment variables for gcloud command parameters

To make it easier to run `gcloud` commands that contain parameters, you can create environment variables to hold the values 
you need, such as your project name and the names of subnets and forwarding rules. The `gcloud` commands presented 
in this section refer to variables that contain your values.

To set the environment variables, run the following commands at the command line _before_ you run `gcloud` commands, 
substituting your own values for all the placeholders in square brackets, such as `[PROJECT_NAME]`, `[VPC_NETWORK_NAME]`, 
and `[SUBNET_IP]`. If you don't know what values to use for the placeholders, use the example values from the parameters 
table in the preceding section.

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

### Configuring an IPsec VPN using dynamic routing

This section describes how to use the `gcloud` command-line tool to configure IPsec VPN with dynamic routing. To perform
the same task using the GCP Console, see
[Configuring IPsec VPN using dynamic routing](##configuring-an-ipsec-vpn-using-dynamic-routing) earlier in this guide.

Note: Before you run the `gcloud` commands in this section, make sure that you've set the variables as described earlier, in
[Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters).

1.  Create a custom VPC network.

        gcloud compute networks create $VPC_NETWORK_NAME \
            --project $PROJECT_NAME \
            --subnet-mode custom

1.  Create a subnet on that network. Make sure that there is no conflict with your local network IP address range or any 
    other configured subnets.

        gcloud compute networks subnets create $VPC_SUBNET_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION \
            --range $SUBNET_IP

1.  Create a GCP VPN gateway in the region you are using.

        gcloud compute target-vpn-gateways create $VPN_GATEWAY_1 \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION

    This step creates an unconfigured VPN gateway in your VPC network.

1.  Reserve a static IP address in the VPC network and region where you created the VPN gateway. Make a note of the
    created address for use in future steps.

        gcloud compute addresses create $STATIC_EXTERNAL_IP \
            --project $PROJECT_NAME \
            --region $REGION

1.  Create three forwarding rules, one each to forward ESP, IKE, and NAT-T traffic to the Cloud VPN gateway.

    For the `[STATIC_IP_ADDRESS]` in the following commands, use the static IP address that you reserved in the previous
    step.

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

1.  Create a [Cloud Router](https://cloud.google.com/compute/docs/cloudrouter).

    For `[PRIVATE_ASN]`, use the [private ASN](https://tools.ietf.org/html/rfc6996)
    (`64512–65534`, `4200000000–4294967294`) for the router that you are configuring. It can be any private ASN that you
    are not already using, such as `65001`.

        gcloud compute routers create $CLOUD_ROUTER_NAME \
            --project $PROJECT_NAME \
            --region $REGION \
            --network $VPC_NETWORK_NAME \
            --asn [PRIVATE_ASN]

1.  Create a VPN tunnel on the Cloud VPN gateway that points to the external IP address of your on-premises VPN gateway. 

    Note the following:

    -   Set the IKE version. The following command sets the IKE version to 2, which is the default, preferred IKE version. 
        If you need to set it to 1, use `--ike-version 1`.
    -   For `[SHARED_SECRET]`, supply the shared secret. For details, see
        [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).

            gcloud compute vpn-tunnels create $VPN_TUNNEL_1 \
                --project $PROJECT_NAME \
                --region $REGION \
                --ike-version 2 \
                --target-vpn-gateway $VPN_GATEWAY_1 \
                --router $CLOUD_ROUTER_NAME \
                --peer-address $CUST_GW_EXT_IP \
                --shared-secret [SHARED_SECRET]
    
    After you run this command, resources are allocated for this VPN tunnel, but the
    tunnel is not yet passing traffic.

1.  Update the Cloud Router configuration to add a virtual interface (`--interface-name`) for the BGP peer.

    Note the following:

    -   The recommended netmask length is `30`.
    -   Make sure that each tunnel has a unique pair of IP addresses. Alternatively, you can leave out `--ip-address`
        and `--mask-length`, in which case the addresses will be automatically generated.
    -   For `[BGP_IF_IP_ADDRESS]`, use a [link-local](https://wikipedia.org/wiki/Link-local_address) IP address belonging
        to the IP address range `169.254.0.0/16`. The address must belong to the same subnet as the interface address of
        the peer router.

            gcloud compute routers add-interface $CLOUD_ROUTER_NAME \
                --project $PROJECT_NAME \
                --interface-name $BGP_IF \
                --mask-length 30 \
                --vpn-tunnel $VPN_TUNNEL_1 \
                --region $REGION \
                --ip-address [BGP_IF_IP_ADDRESS]

1.  Update the Cloud Router configuration to add the BGP peer to the interface.

    Note the following:

    -   For `[PEER_ASN]`, use your public ASN or any [private ASN](https://tools.ietf.org/html/rfc6996)
        (`64512–65534`, `4200000000–4294967294`) that you are not already using in the peer network. For example, you can
        use `65001`.
    -   For `[PEER_IP_ADDRESS]`, use a [link-local](https://wikipedia.org/wiki/Link-local_address) IP address belonging to 
        the IP address range `169.254.0.0/16`. It must belong to the same subnet as the GCP-side interface.
    -   If you left out the IP address and mask length in the previous step, leave out the peer IP address in this command.
    -   Make sure that each tunnel has a unique pair of IP addresses.

            gcloud compute routers add-bgp-peer $CLOUD_ROUTER_NAME \
                --project $PROJECT_NAME \
                --region $REGION \
                --peer-name $BGP_SESSION_NAME \
                --interface $BGP_IF \
                --peer-asn [PEER_ASN] \
                --peer-ip-address [PEER_IP_ADDRESS]

1.  View details of the configured Cloud Router to confirm your settings.

        gcloud compute routers describe $CLOUD_ROUTER_NAME \
            --project $PROJECT_NAME \
            --region $REGION

    The output for a configured Cloud Router looks like the following example. This output shows sample values.
    Your output will include an ID unique to you, your project name, the region you've selected, and so on.

        Output:
         bgp:
         advertiseMode: DEFAULT
         asn: 65001
         creationTimestamp: '2018-04-23T09:54:46.633-07:00'
         description: ''
         id: '2327390853769965881'
         kind: compute#router
         name: vpn-test-juniper
         network: https://www.googleapis.com/compute/v1/projects/vpn-guide/global/networks/default
         region: https://www.googleapis.com/compute/v1/projects/vpn-guide/regions/us-east1
         selfLink: https://www.googleapis.com/compute/v1/projects/vpn-guide/regions/us-east1/routers/vpn-test-juniper

1.  Create GCP firewall rules to allow inbound traffic from the on-premises network subnets and from your VPC subnet 
    prefixes.

        gcloud compute firewall-rules create $VPN_RULE \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --allow tcp,udp,icmp \
            --source-ranges $IP_ON_PREM_SUBNET

### Configuring route-based IPsec VPN using static routing

This section describes how to use the `gcloud` command-line tool to configure an IPsec VPN with static routing. To perform 
the same task using the GPC Console, see
[Configuring IPsec VPN using static routing](#configuring-route-based-ipsec-vpn-using-static-routing) 
earlier in this guide.

The procedure suggests creating a custom VPC network. This is preferred over using an auto-created network. For more 
information, see
[Networks and tunnel routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#network-types)
in the Cloud VPN documentation.

Note: Before you run the `gcloud` commands in this section, make sure that you've set the variables as described earlier in
[Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters).

1.  Create a custom VPC network. Make sure there is no conflict with your local network IP address range.

    For `[RANGE]`, substitute an appropriate CIDR range, such as `172.16.100.0/24`.

        gcloud compute networks create $VPC_NETWORK_NAME \
            --project $PROJECT_NAME \
            --subnet-mode custom
    
        gcloud compute networks subnets create $VPC_SUBNET_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION \
            --range [RANGE]

1.  Create a VPN gateway in the region you are using. Normally, this is the region that contains the instances that you 
    want to reach.

        gcloud compute target-vpn-gateways create $VPN_GATEWAY_1 \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION

    This step creates an unconfigured VPN gateway in your GCP VPC network.

1.  Reserve a static IP address in the VPC network and region where you created the VPN gateway. Make a note of the address
    for use in future steps.

        gcloud compute addresses create $STATIC_EXTERNAL_IP \
            --project $PROJECT_NAME \
            --region $REGION

1.  Create three forwarding rules, one each to forward ESP, IKE, and NAT-T traffic to the Cloud VPN gateway.

    For `[STATIC_IP_ADDRESS]`, use the static IP address that you reserved in the previous step.

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

1.  Create a VPN tunnel on the Cloud VPN gateway that points to the external IP address of your on-premises VPN gateway. 

    Note the following:

    -   Set the IKE version. The following command sets the IKE version to 2, which is the default, preferred IKE version.
        If you need to set it to 1, use `--ike-version 1`.
    -   For `[SHARED_SECRET]`, supply the shared secret. For details, see
        [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).
    -   For `[LOCAL_TRAFFIC_SELECTOR_IP]`, supply an IP address range, like `172.16.100.0/24`, that will be accessed on the 
        GCP side of the  tunnel, as described in
        [Traffic selectors](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#static-routing-networks)
        in the GCP VPN networking documentation.

            gcloud compute vpn-tunnels create $VPN_TUNNEL_1 \
                --project $PROJECT_NAME \
                --peer-address $CUST_GW_EXT_IP \
                --region $REGION \
                --ike-version 2 \
                --shared-secret [SHARED_SECRET] \
                --target-vpn-gateway $VPN_GATEWAY_1 \
                --local-traffic-selector [LOCAL_TRAFFIC_SELECTOR_IP]

After you run this command, resources are allocated for this VPN tunnel, but it is not yet passing traffic.

1.  Use a [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create) to forward traffic to the 
    destination range of IP addresses in your on-premises network. The region must be the same region as for the VPN tunnel.

        gcloud compute routes create $ROUTE_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --next-hop-vpn-tunnel $VPN_TUNNEL_1 \
            --next-hop-vpn-tunnel-region $REGION \
            --destination-range $IP_ON_PREM_SUBNET

1.  If you want to pass traffic from multiple subnets through the VPN tunnel, repeat the previous step to forward the IP 
    address of each of the subnets.

1.  Create firewall rules to allow traffic between the on-premises network and GCP VPC networks.

        gcloud compute firewall-rules create $VPN_RULE \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --allow tcp,udp,icmp \
            --source-ranges $IP_ON_PREM_SUBNET
