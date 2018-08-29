---
title: How to Set Up VPN between Juniper SRX and Cloud VPN
description: Learn how to build site-to-site IPSEC VPN between Juniper SRX and Cloud VPN.
author: antiabong, ashishverm
tags: Compute Engine, Cloud VPN, Juniper SRX
date_published: 2017-08-28
---

This guide walks you through the process to configure the Juniper SRX 300 for
integration with the [Google Cloud VPN Services][cloud_vpn]. This information is
provided as an example only. Please note that this guide is not meant to be a
comprehensive overview of IPsec and assumes basic familiarity with the IPsec
protocol.

[cloud_vpn]: https://cloud.google.com/compute/docs/vpn/overview

## Environment overview

The equipment used in the creation of this guide is as follows:

* Vendor: Juniper 
* Model: SRX300
* JUNOS Software Release [15.1X49-D100.6]

Although this guide is created with Juniper SRX300 exactly the same configuration
also apply to other SRX platforms:

* SRX220
* SRX550
* SRX1400
* SRX3400
* vSRX

## Topology

The topology outlined by this guide is a basic site-to-site IPsec VPN tunnel
configuration using the referenced device:

![Topology](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-cisco-asr/GCP-Cisco-ASR-Topology.jpg)

## Before you begin

### Overview

The configuration samples which follow will include numerous value substitutions
provided for the purpose of example only. Any references to IP addresses, device
IDs, shared secrets or keys account information or project names should be
replaced with the appropriate values for your environment when following this
guide.

This guide is not meant to be a comprehensive setup overview for the device
referenced, but rather is only intended to assist in the creation of IPsec
connectivity to Google Cloud Platform (GCP) VPC networks. The following is a
high level overview of the configuration process which will be covered:

* Configure the base network configurations to establish L3 connectivity
* Set up the Base VPN configuration, including:
  * Configure IKEv2 Proposal and Policy
  * Configure IKEv2 Keyring
  * Configure IKEv2 profile
  * Configure IPsec Security Association (SA)
  * Configure IPsec transform set
  * Configure IPsec profile
  * Configure IPsec Static Virtual Tunnel Interface (SVTI)
  * Juniper
  * Configure Static or Dynamic Routing Protocol to route traffic into the IPsec tunnel
* Testing the IPsec connection
* Advanced VPN configurations

### Getting started

The first step in configuring your Juniper SRX300 for use with the Google Cloud
VPN service is to ensure that the following prerequisite conditions have been
met:

* Junos Software Base (JSB/JB) license for SRX300 or Junos Software Enhanced (JSE/JE) license

For a detailed Juniper SRX series license information, refer to the
[SRX Series Services Gateways](https://www.juniper.net/us/en/products-services/security/srx-series/).

### IPsec parameters

For the Juniper SRX IPsec configuration, the following details will be used:

|Parameter | Value|
--------- |  -----
|VPN Type| `Route-Based VPN` |
|IPsec Mode | `Tunnel mode` |
|Auth protocol | `Pre-shared-key` |
|Key Exchange | `IKEv2` |
|Start | `Auto` |
|Perfect Forward Secrecy (PFS) | `Group 14` |
|Dead Peer Detection (DPD) | `60 5 periodic` |

The IPsec configuration used in this guide is specified below:

| Cipher Role | Cipher |
| ------------| -------|
| Encryption | `esp-aes 256 esp-sha-hmac` |
| Integrity | `sha256` |
| Diffie-Hellman (DH) | `group 14` |
| Lifetime | `36,000 seconds (10 hours)` |

*Note: Juniper SRX(es) mostly support only tunnel mode VPN*

## Configuration – GCP

### IPsec VPN using dynamic routing

For dynamic routing you use [Cloud Router](https://cloud.google.com/router/docs/concepts/overview)
to establish BGP sessions between the 2 peers.

#### Using the Cloud Platform Console

1.  [Go to the VPN page](https://console.cloud.google.com/networking/vpn/list)
    in the Google Cloud Platform Console.
2.  Click **Create VPN connection**.
3.  Populate the following fields for the gateway:

    * **Name** — The name of the VPN gateway. This name is displayed in the
      console and used in by the `gcloud` command-line tool to reference the gateway.
    * **VPC network** — The VPC network containing the instances the VPN gateway
      will serve. In this case it is `vpn-scale-test-juniper`, a
      [custom VPC network](https://cloud.google.com/compute/docs/vpc/using-vpc#create-custom-network).
    * **Region** — The region where you want to locate the VPN gateway.
      Normally, this is the region that contains the instances you wish to
      reach. Example: `us-east1`
    * **IP address** — Select a pre-existing [static external IP address](https://cloud.google.com/compute/docs/ip-addresses#reservedaddress).
      If you don't have a static external IP address, you can create one by
      clicking **New static IP address** in the pull-down menu. Selected
      `vpn-scale-test0` for this guide.

4.  Populate fields for at least one tunnel:

    * **Peer IP address** — `204.237.220.4` Public IP address of the peer
      gateway.
    * **IKE version** — IKEv2 is preferred, but IKEv1 is supported if that is
      all the peer gateway can manage.
    * **Shared Secret** — Character string used in establishing encryption for
      that tunnel. You must enter the same shared secret into both VPN gateways.
      If the VPN gateway device on the peer side of the tunnel doesn't generate
      one automatically, you can make one up.
    * **Routing options** — Select **Dynamic (BGP)**.
    * **Cloud router** — Select **Create cloud router**, then populate the
      following fields. When you are done, click **Save and continue**.
    * **Name** — The name of the Cloud Router. This name is displayed in the
      console and used by the `gcloud` command-line tool to reference the
      router. Example: `vpn-scale-test-juniper-rtr`
    * **Google ASN** — The [private ASN](https://tools.ietf.org/html/rfc6996)
      (64512 - 65534, 4200000000 - 4294967294) for the router you are
      configuring. It can be any private ASN you are not already using.
      Example: `65002`
    * **BGP session** — Click the pencil icon, then populate the following
      fields. When you are done, click **Save and continue**.
    * **Name** — `bgp-peer1`
    * **Peer ASN** — The [private ASN](https://tools.ietf.org/html/rfc6996)
      (64512 - 65534, 4200000000 - 4294967294) for the router you are
      configuring. It can be any private ASN you are not already using.
      Example: `65001`
    * **Google BGP IP address** — The two BGP interface IP addresses must be
      *link-local* IP addresses belonging to the same /30 subnet in
      `169.254.0.0/16`. Example: `169.254.1.1`
    * **Peer BGP IP address** — See explanation for **Google BGP IP address**.
      Example: `169.254.1.2`

5.  Click **Create** to create the gateway, Cloud Router, and all tunnels,
    though tunnels will not connect until you've configured the peer router as
    well.

    This step automatically creates the necessary forwarding rules for the
    gateway and tunnels.

6.  [Configure your firewall rules](https://cloud.google.com/compute/docs/vpn/creating-vpns#configuring_firewall_rules)
    to allow inbound traffic from the peer network subnets, and you must
    configure the peer network firewall to allow inbound traffic from your
    Compute Engine prefixes.

    * Go to the [Firewall rules](https://console.cloud.google.com/networking/firewalls)
      page.
    * Click **Create firewall rule**.
    * Populate the following fields:
      * **Name:** `vpnrule1`
      * **VPC network:** `my-network`
      * **Source filter:** IP ranges.
      * **Source IP ranges:** The peer ranges to accept from the peer VPN gateway.
      * **Allowed protocols and ports:** tcp;udp;icmp
    * Click **Create**.

#### Using the `gcloud` command-line tool

1.  Create a custom VPC network. You can also use auto VPC network, make sure
    there is no conflict with your local network range.

        gcloud compute networks create vpn-scale-test-juniper --subnet-mode custom

        gcloud compute networks subnets create subnet-1 --network vpn-scale-test-juniper \
            --region us-east1 --range 172.16.100.0/24

1.  Create a VPN gateway in the desired region. Normally, this is the region
    that contains the instances you want to reach. This step creates an
    unconfigured VPN gateway named `vpn-scale-test-juniper-gw-0` in your VPC
    network.

        gcloud compute target-vpn-gateways create vpn-scale-test-juniper-gw-0 --network \
            vpn-scale-test-juniper --region us-east1

1.  Reserve a static IP address in the VPC network and region where you created
    the VPN gateway. Make a note of the created address for use in future steps.

        gcloud compute --project vpn-guide addresses create --region us-east1 vpn-static-ip

1.  Create a forwarding rule that forwards ESP, IKE and NAT-T traffic toward the
    Cloud VPN gateway. Use the static IP address `vpn-static-ip` you reserved
    earlier. This step generates a forwarding rule named `fr-esp`, `fr-udp500`,
    `fr-udp4500` resp.

        gcloud compute --project vpn-guide forwarding-rules create fr-esp  --region us-east1 \
            --ip-protocol ESP --address 35.185.3.177 --target-vpn-gateway vpn-scale-test-juniper-gw-0

        gcloud compute --project vpn-guide forwarding-rules create fr-udp500 --region us-east1 \
            --ip-protocol UDP --ports 500 --address 35.185.3.177 --target-vpn-gateway vpn-scale-test-juniper-gw-0

        gcloud compute --project vpn-guide forwarding-rules create fr-udp4500 --region us-east1 \
            --ip-protocol UDP --ports 4500 --address 35.185.3.177 --target-vpn-gateway vpn-scale-test-juniper-gw-0

1.  Create [Cloud Router](https://cloud.google.com/compute/docs/cloudrouter) as
    shown below:

        gcloud compute --project vpn-guide routers create vpn-scale-test-juniper-rtr --region us-east1 \
            --network vpn-scale-test-juniper --asn 65002

1.  Create a VPN tunnel on the Cloud VPN Gateway that points toward the external
    IP address `[CUST_GW_EXT_IP]` of your peer VPN gateway. You also need to
    supply the shared secret. The default, and preferred, IKE version is 2. If
    you need to set it to 1, use --ike_version 1. The following example sets IKE
    version to 2. After you run this command, resources are allocated for this
    VPN tunnel, but it is not yet passing traffic.

        gcloud compute --project vpn-guide vpn-tunnels create tunnel1 --peer-address 204.237.220.4 \
            --region us-east1 --ike-version 2 --shared-secret MySharedSecret --target-vpn-gateway \
            vpn-scale-test-juniper-gw-0 --router vpn-scale-test-juniper-rtr

1.  Update the Cloud Router config to add a virtual interface (--interface-name)
    for the BGP peer. The BGP interface IP address must be a *link-local* IP
    address belonging to the IP address range `169.254.0.0/16` and it must
    belong to same subnet as the interface address of the peer router. The
    netmask length is recommended to be 30. Make sure each tunnel has a unique
    pair of IPs. Alternatively, you can leave `--ip-address` and `--mask-length`
    blank, and leave `--peer-ip-address` blank in the next step, and IP
    addresses will be automatically generated for you.

        gcloud compute --project vpn-guide routers add-interface vpn-scale-test-juniper-rtr \
            --interface-name if-1 --ip-address 169.254.1.1 --mask-length 30 --vpn-tunnel tunnel1 --region us-east1

1.  Update the Cloud Router config to add the BGP peer to the interface. This
    example uses ASN 65001 for the peer ASN. You can use your public ASN or
    [private ASN](https://tools.ietf.org/html/rfc6996)
    (64512 - 65534, 4200000000 - 4294967294) that you are not already using in
    the peer network. The BGP peer interface IP address must be a *link-local*
    IP address belonging to the IP address range `169.254.0.0/16`. It must
    belong to same subnet as the GCP-side interface. Make sure each tunnel has a
    unique pair of IPs.

        gcloud compute --project vpn-guide routers add-bgp-peer vpn-scale-test-juniper-rtr --peer-name \
            bgp-peer1 --interface if-1 --peer-ip-address 169.254.1.2 --peer-asn 65001 --region us-east1

1.  View details of the Cloud Router and confirm your settings.

        gcloud compute --project vpn-guide routers describe vpn-scale-test-juniper-rtr --region us-east1

1.  Create firewall rules to allow traffic between on-prem network and GCP VPC networks.

        gcloud  compute --project vpn-guide firewall-rules create vpnrule1 --network vpn-scale-test-juniper \
            --allow tcp,udp,icmp --source-ranges 10.0.0.0/8
            
### IPsec VPN using static routing

This section provides the steps to create [Cloud VPN on GCP][compute_vpn]. There are two
ways to create VPN on GCP, using Google Cloud Platform Console and the `gcloud`
command-line tool. The upcoming section provide details to both in detail below:

[compute_vpn]: https://cloud.google.com/compute/docs/vpn/overview

#### Using the Google Cloud Platform Console

1.  [Go to the VPN page](https://console.cloud.google.com/networking/vpn/list) in the Google Cloud Platform Console.
2.  Click **Create VPN connection**.
3.  Populate the following fields for the gateway:

    * **Name** — The name of the VPN gateway. This name is displayed in the
      console and used by the `gcloud` command-line tool to reference the gateway.
    * **VPC network** — The VPC network containing the instances the VPN gateway
      will serve. In this case it is `vpn-scale-test-juniper`, a
      [custom VPC network](https://cloud.google.com/compute/docs/vpc/using-vpc#create-custom-network).
      Ensure this network does not conflict with your on-premises networks.
    * **Region** — The region where you want to locate the VPN gateway.
      Normally, this is the region that contains the instances you wish to
      reach. Example: `us-east1`
    * **IP address** — Select a pre-existing [static external IP address](https://cloud.google.com/compute/docs/ip-addresses#reservedaddress).
      If you don't have a static external IP address, you can create one by
      clicking **New static IP address** in the pull-down menu. Selected
      `vpn-scale-test0` for this guide.
4.  Populate fields for at least one tunnel:

    * **Peer IP address** — Enter your on-premises public IP address here, with the
      above mentioned topology it is `204.237.220.4`
    * **IKE version** — IKEv2 is preferred, but IKEv1 is supported if that is
      all the peer gateway can manage.
    * **Shared secret** — Used in establishing encryption for that tunnel. You
      must enter the same shared secret into both VPN gateways. If the VPN
      gateway device on the other side of the tunnel doesn't generate one
      automatically, you can make one up.
    * **Remote network IP range** — `10.0.0.0/8`. The range, or ranges, of the
      peer network, which is the network on the other side of the tunnel from
      the Cloud VPN gateway you are currently configuring.
    * **Local subnets** — Specifies which IP ranges will be routed through the
      tunnel. This value cannot be changed after the tunnel is created because
      it is used in the IKE handshake.
    * Select the gateway's entire subnet in the pull-down menu. Or, you can
      leave it blank since the local subnet is the default.
    * Leave **Local IP ranges** blank except for the gateway's subnet.
5.  Click **Create** to create the gateway and initiate all tunnels, though
    tunnels will not connect until you've completed the additional steps below.
    This step automatically creates a network-wide route and necessary
    forwarding rules for the tunnel.
6.  [Configure your firewall rules](https://cloud.google.com/compute/docs/vpn/creating-vpns#configuring_firewall_rules)
    to allow inbound traffic from the peer network subnets, and you must
    configure the peer network firewall to allow inbound traffic from your
    Compute Engine prefixes.

    * Go to the [Firewall rules](https://console.cloud.google.com/networking/firewalls)
      page.
    * Click **Create firewall rule**.
    * Populate the following fields:
      * **Name:** `vpnrule1`
      * **VPC network:** `vpn-scale-test-juniper`
      * **Source filter:** IP ranges.
      * **Source IP ranges:** The peer ranges to accept from the peer VPN
        gateway.
      * **Allowed protocols and ports:** `tcp;udp;icmp`
    * Click **Create**.

#### Using the `gcloud` command-line tool

1.  Create a custom VPC network. You can also use auto VPC network, make sure
    there is no conflict with your local network range.

        gcloud compute networks create vpn-scale-test-juniper --mode custom
        gcloud compute networks subnets create subnet-1 --network vpn-scale-test-juniper \
            --region us-east1 --range 172.16.100.0/24

2.  Create a VPN gateway in the desired region. Normally, this is the region
    that contains the instances you wish to reach. This step creates an
    unconfigured VPN gateway named `vpn-scale-test-juniper-gw-0` in your VPC
    network.

        gcloud compute target-vpn-gateways create vpn-scale-test-juniper-gw-0 \
            --network vpn-scale-test-juniper --region us-east1

3.  Reserve a static IP address in the VPC network and region where you created
    the VPN gateway. Make a note of the created address for use in future steps.

        gcloud compute --project vpn-guide addresses create --region us-east1 vpn-static-ip

4.  Create a forwarding rule that forwards ESP, IKE and NAT-T traffic toward the
    Cloud VPN gateway. Use the static IP address `vpn-static-ip` you reserved
    earlier. This step generates a forwarding rule named `fr-esp`, `fr-udp500`,
    `fr-udp4500` resp.

        gcloud compute --project vpn-guide forwarding-rules create fr-esp --region us-east1 \
            --ip-protocol ESP --address 35.185.3.177 --target-vpn-gateway vpn-scale-test-juniper-gw-0

        gcloud compute forwarding-rules create fr-udp500 --project vpn-guide --region us-east1 \
            --address 104.196.200.68 --target-vpn-gateway vpn-scale-test-juniper-gw-0 --ip-protocol=UDP --ports 500

        gcloud compute forwarding-rules create fr-udp4500 --project vpn-guide --region us-east1 \
            --address 104.196.200.68 --target-vpn-gateway vpn-scale-test-juniper-gw-0 --ip-protocol=UDP --ports 4500

5.  Create a VPN tunnel on the Cloud VPN Gateway that points toward the external
    IP address `[CUST_GW_EXT_IP]` of your peer VPN gateway. You also need to
    supply the shared secret. The default, and preferred, IKE version is 2. If
    you need to set it to 1, use --ike_version 1. The following example sets IKE
    version to 2. After you run this command, resources are allocated for this
    VPN tunnel, but it is not yet passing traffic.

        gcloud compute --project vpn-guide vpn-tunnels create tunnel1 --peer-address 204.237.220.4 \
            --region us-east1 --ike-version 2 --shared-secret MySharedSecret --target-vpn-gateway \
            vpn-scale-test-juniper-gw-0 --local-traffic-selector=172.16.100.0/24

6.  Use a [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create)
    to forward traffic to the destination range of IP addresses
    ([CIDR_DEST_RANGE]) in your local on-premises network. You can repeat this
    command to add multiple ranges to the VPN tunnel. The region must be the
    same as for the tunnel.

        gcloud compute --project vpn-guide routes create route1 --network [NETWORK] --next-hop-vpn-tunnel \
            tunnel1 --next-hop-vpn-tunnel-region us-east1 --destination-range 10.0.0.0/8

7.  Create firewall rules to allow traffic between on-premises network and GCP
    VPC networks.

        gcloud compute --project vpn-guide firewall-rules create vpnrule1 --network vpn-scale-test-juniper \
            --allow tcp,udp,icmp --source-ranges 10.0.0.0/8

## Configuration – Juniper SRX300

### Base network configurations (to establish L3 connectivity)

This section provides the base network configuration of Juniper to
establish network connectivity. At least one internal facing interface is
required to connect to your own network, and one external facing interface is
required to connect to GCP. A sample interface configuration is provided below
for reference:

	[edit]
    root@vsrx#
    # Internal interface configuration
    set interfaces ge-0/0/1 unit 0 family inet address 192.168.1.1/24
    set interfaces ge-0/0/1 unit 0 description "internal facing interface"
    # External interface configuration
    set interfaces ge-0/0/0 unit 0 family inet address 192.168.1.1/24
    set interfaces ge-0/0/0 unit 0 description "external facing interface"
    # Tunnel interface configuration
    set interfaces st0 unit 0 family inet mtu 1460
    set interfaces st0 unit 0 family inet address 169.254.0.2/30


### Base VPN configurations

#### Configure IKEv2 proposal and policy

Create an Internet Key Exchange (IKE) version 2 proposal object. IKEv2 proposal
objects contain the parameters required for creating IKEv2 proposals when
defining remote access and site-to-site VPN policies. IKE is used to
authenticate IPsec peers, negotiate and distribute IPsec encryption keys, and
automatically establish IPsec security associations (SAs). The default proposal
associated with the default policy is used for negotiation. An IKEv2 policy with
no proposal is considered incomplete. In this block, the following parameters
are set:

* Encryption algorithm - set to `AES-CBC-256`
* Integrity algorithm - set to SHA256
* Diffie-Hellman group - set to 14
* IKEv2 Lifetime - set the lifetime of the security associations (after which a 
reconnection will occur). The default on most SRX platforms is 28800 seconds

		[edit]
        root@vsrx#
        set security ike proposal ike-phase1-proposal authentication-method pre-shared-keys
        set security ike proposal ike-phase1-proposal dh-group group14
        set security ike proposal ike-phase1-proposal authentication-algorithm sha-256
        set security ike proposal ike-phase1-proposal encryption-algorithm aes-256-cbc
        set security ike proposal ike-phase1-proposal lifetime-seconds 28800
        set security ike policy ike_pol_home-2-gcp-vpn mode main
        set security ike policy ike_pol_home-2-gcp-vpn proposals ike-phase1-proposal
        set security ike policy ike_pol_home-2-gcp-vpn pre-shared-key ascii-text <*****>



#### Configure IKEv2 Gateway

An IKEv2 profile must be configured and must be attached to an IPsec profile on
both the IKEv2 initiator and responder. In this block, the following parameters
are set:

* DPD – set the dead peer detection interval and retry threshold, if there are no
  response from the peer, the SA created for that peer is deleted. Set DPD type to `probe-idle-tunnel`,  
  set DPD interval to `20` and the DPD retry threshold to `4`.

* Set the IKE remote address, IKE external interface and the IKE version (v2)
* The IKE local identity should be the IP address of the external interface. If SRX device is sitting 
behind a NAT, the local identity should be configured as the public IP address of the NAT. Where NAT maps 
to a pool of public IP addresses, a dedicated 1-to-1 NAT should be configured to the SRX device.

		[edit]
        root@vsrx#
        set security ike gateway gw_home-2-gcp-vpn ike-policy ike_pol_home-2-gcp-vpn
        set security ike gateway gw_home-2-gcp-vpn address 35.187.170.191
        set security ike gateway gw_home-2-gcp-vpn dead-peer-detection probe-idle-tunnel
        set security ike gateway gw_home-2-gcp-vpn dead-peer-detection interval 20
		set security ike gateway gw_home-2-gcp-vpn dead-peer-detection threshold 4
        set security ike gateway gw_home-2-gcp-vpn local-identity inet 104.196.65.171
        set security ike gateway gw_home-2-gcp-vpn external-interface ge-0/0/1.0
        set security ike gateway gw_home-2-gcp-vpn version v2-only

#### Configure IPsec Proposal and Policy

Defines the IPsec parameters that are to be used for IPsec encryption between
two IPsec routers in IPsec profile configuration. In this block, the following
parameters are set

* `IPsec SA lifetime` – 1 hour `3600 seconds` is the recommended value for most VPN sessions.
The default on a Juniper SRX is 3600 seconds

* Perfect Forward Secrecy (PFS) - PFS ensures that the same key will not be
  generated again, so forces a new diffie-hellman key exchange. This config is 
  set to group14 
  
        [edit]
        root@vsrx#
        set security ipsec proposal ipsec-phase2-proposal protocol esp
        set security ipsec proposal ipsec-phase2-proposal lifetime-seconds 3600
        set security ipsec proposal ipsec-phase2-proposal authentication-algorithm hmac-sha-256-128
        set security ipsec proposal ipsec-phase2-proposal encryption-algorithm aes-256-cbc
        set security ipsec policy ipsec_pol_home-2-gcp-vpn perfect-forward-secrecy keys group14
        set security ipsec policy ipsec_pol_home-2-gcp-vpn proposals ipsec-phase2-proposal


#### Configure IPsec Profile and Tunnel Binding Interface

A tunnel interface is configured to be the logical interface associated with the
tunnel. All traffic routed to the tunnel interface will be encrypted and
transmitted to the GCP. Similarly, traffic from the GCP will be logically
received on this interface.

Association with the IPsec security association is done through the
`tunnel protection` command.

Adjust the maximum segment size (MSS) value of TCP packets going through a
router. The recommended value is 1360 when the number of IP MTU bytes is set to 1460

1. With these recommended settings, TCP sessions quickly scale back to
1400-byte IP packets so the packets will "fit" in the tunnel.

        [edit]
        root@vsrx#
        set security ipsec vpn home-2-gcp-vpn bind-interface st0.0
        set security ipsec vpn home-2-gcp-vpn ike gateway gw_home-2-gcp-vpn
        set security ipsec vpn home-2-gcp-vpn ike ipsec-policy ipsec_pol_home-2-gcp-vpn
        set security ipsec vpn home-2-gcp-vpn establish-tunnels immediately
        set security flow tcp-mss ipsec-vpn mss 1360
        set security flow tcp-session rst-invalidate-session



#### Configure Security Policies
Juniper SRX requires security policies....
	
    [edit]
    root@vsrx#
    set security zones security-zone untrust interfaces ge-0/0/1.0 host-inbound-traffic system-services ike
    set security zones security-zone vpn-gcp host-inbound-traffic protocols bgp
    set security zones security-zone vpn-gcp interfaces st0.0
    # Allow BGP Session
    set security zones security-zone vpn-gcp host-inbound-traffic protocols bgp


    

#### Configure static or dynamic routing protocol to route traffic into the IPsec tunnel

BGP is used within the tunnel to exchange prefixes between the GCP cloud router and the Juniper SRX appliance. The GCP cloud router will announce the prefix corresponding to your GCP VPC.

BGP timers are adjusted to provide more rapid detection of outages.

* Configure BGP peering between SRX and cloud router

		[edit]
        root@vsrx#
        set protocols bgp group ebgp-peers type external
        set protocols bgp group ebgp-peers multihop
        set protocols bgp group ebgp-peers local-as 65501
        set protocols bgp group ebgp-peers neighbor 169.254.1.1 peer-as 65500

* Configure routing policies to inject routes into BGP and advertise it to the cloud router

		[edit]
        root@vsrx#
		set policy-options policy-statement gcp-bgp-policy term 1 from protocol direct
        set policy-options policy-statement gcp-bgp-policy term 1 from route-filter 192.168.1.0/24 exact
        set policy-options policy-statement gcp-bgp-policy term 1 then accept
        set protocols bgp group ebgp-peers export gcp-bgp-policy

Alternatively, static routes to GCP networks can be configured to point to the Tunnel interface `st0.0`.

    [edit]
    root@vsrx#
    set routing-options static route 172.16.0.0/16 next-hop st0.0

Check [Best practices](https://cloud.google.com/router/docs/resources/best-practices) 
for further recommendations on peer configurations.

### Saving the configuration

To save the running configuration and set it as the default startup, run the
following command on Cisco IOS terminal:

    [edit]
    root@vsrx#
    commit

### Test result

    cisco-asr#ping 172.16.100.2 source 10.0.200.1
    Type escape sequence to abort.
    Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:
    Packet sent with a source address of 10.0.200.1
    !!!!!
    Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms

### Advanced VPN configurations

#### Configure VPN redundancy

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-cisco-asr/GCP-Cisco-ASR-Topology-Redundant.jpg)

Using redundant tunnels ensures continuous availability in the case of a tunnel fails.

If a Cloud VPN tunnel goes down, it restarts automatically. If an entire virtual
device fails, Cloud VPN automatically instantiates a new one with the same
configuration, so you don't need to build two Cloud VPN gateways. The new
gateway and tunnel connect automatically. For hardware appliances such as Cisco
ASR it is recommended that you deploy atleast 2 ASRs and create VPN tunnels to
GCP from each for redundancy purposes.

The VPN redundancy configuration example is built based on the IPsec tunnel and
BGP configuration illustrated above.

##### Cisco ASR

Cisco IOS BGP prefer the path with the highest `LOCAL-PREF`, the BGP routes are
set with a value of 100 by default, by setting the `LOCAL-PREF` to 200 for the
routes received from Tunnel1, BGP will choose Tunnel1 as the preferred VPN
tunnel to the GCP, in the event of Tunnel 1 failure, BGP will reroute the
traffic to Tunnel2.

    crypto ikev2 keyring VPN_SCALE_TEST_KEY
     peer GCP1
     address 104.196.200.68
     pre-shared-key MySharedSecret
     peer GCP2
     address 35.186.108.199
     pre-shared-key MySharedSecret
    !
    interface Tunnel1
     description VPN tunnel to the east coast DC
     ip address 169.254.0.2 255.255.255.252
     ip mtu 1400
     ip tcp adjust-mss 1360
     tunnel source TenGigabitEthernet0/0/0
     tunnel mode ipsec ipv4
     tunnel destination 104.196.200.68
     tunnel protection ipsec profile VPN_SCALE_TEST_VTI
    !
    interface Tunnel2
     description VPN tunnel to the west coast DC
     ip address 169.254.0.6 255.255.255.252
     ip mtu 1400
     ip tcp adjust-mss 1360
     tunnel source TenGigabitEthernet0/0/0
     tunnel mode ipsec ipv4
     tunnel destination 35.186.108.199
     tunnel protection ipsec profile VPN_SCALE_TEST_VTI_2
    !

###### Dynamic Routing

    router bgp 65001
     bgp log-neighbor-changes
     neighbor 169.254.0.1 description BGP session over Tunnel1
     neighbor 169.254.0.1 remote-as 65002
     neighbor 169.254.0.1 timers 20 60 60
     neighbor 169.254.0.5 description BGP session over Tunnel2
     neighbor 169.254.0.5 remote-as 65002
     neighbor 169.254.0.5 timers 20 60 60
     !
     address-family ipv4
      network 10.0.0.0
      neighbor 169.254.0.1 activate
      neighbor 169.254.0.1 route-map LP200 in
      neighbor 169.254.0.5 activate
     exit-address-family
    !
    route-map LP200 permit 10
     set local-preference 200

To ensure symmetry in your traffic flow, you can configure MED to influence the
inbound traffic from GCP for the same tunnel you are sending outbound traffic
to. Note that lower the MED, higher the preference.

    router bgp 65001
     address-family ipv4
      neighbor 169.254.0.1 route-map SET-MED-10 out
      neighbor 169.254.0.5 activate
     exit-address-family
    !

    route-map SET-MED-10 permit 10
     set metric 10

###### Static Routing

If you are using static routing then instead of BGP configurations mentioned
above, you can change the metric (higher the metric lower the preference) for
your static route as shown below:

      cisco-asr#ip route 172.16.100.0 255.255.255.0 Tunnel2 10

##### Configuring route priority – GCP

###### Dynamic Routing (Optional)

With dynamic routing you have an option to define advertised-route-priority,
lower priority is preferred. More details can be found [here](https://cloud.google.com/sdk/gcloud/reference/compute/routers/update-bgp-peer).
Note that if you have local_preference configured on the peer network as
mentioned above, BGP will prefer the higher `local_preference` first.


    gcloud compute --project vpn-guide routers add-bgp-peer vpn-scale-test-cisco-rtr --peer-name \
        bgp-peer1 --interface if-1 --peer-ip-address 169.254.1.2 --peer-asn 65001 --region us-east1 \
        --advertised-route-priority=2000

###### Static Routing (Optional)

When using static routing GCP provides you an option to customize the priority
in case there are multiple routes with the same prefix length. In order to have
symmetric traffic flow make sure that you set the priority of your secondary
tunnel to higher value than the primary tunnel (default priority is 1000). To
define the route priority run the below command.

    gcloud compute --project vpn-guide routes create route2 --network vpn-scale-test-cisco \
        --next-hop-vpn-tunnel tunnel1 --next-hop-vpn-tunnel-region us-east1 --destination-range \
        10.0.0.0/8 --priority=2000

###### Test output on Juniper SRX
1. Show IKE Security Associations
        root@vsrx# run show security ike security-associations
        Index   State  Initiator cookie  Responder cookie  Mode           Remote Address
        7877087 UP     412c5a43aad7682b  b6d24ef8bf25e9ea  IKEv2          35.187.170.191
2. Show IPSec Security Associations
        root@vsrx# run show security ipsec security-associations
        Total active tunnels: 1
        ID    Algorithm       SPI      Life:sec/kb  Mon lsys Port  Gateway
        <131073 ESP:aes-cbc-256/sha256 9beb1bf0 729/ unlim - root 4500 35.187.170.191
        >131073 ESP:aes-cbc-256/sha256 97791a28 729/ unlim - root 4500 35.187.170.191  		
3. List BGP learned routes:

        root@vsrx# run show route protocol bgp

        inet.0: 11 destinations, 11 routes (11 active, 0 holddown, 0 hidden)
        + = Active Route, - = Last Active, * = Both

        172.16.0.0/24      *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0
        172.16.11.0/24     *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0
        172.16.21.0/24     *[BGP/170] 23:02:00, MED 100, localpref 100
                              AS path: 65500 ?, validation-state: unverified
                            > to 169.254.0.1 via st0.0

#### Getting higher throughput

As documented in the [GCP Advanced Configurations](https://cloud.google.com/compute/docs/vpn/advanced),
each Cloud VPN tunnel can support up to 3 Gbps when the traffic is traversing a
[direct peering](https://cloud.google.com/interconnect/direct-peering) link, or
1.5 Gbps when traversing the public Internet. To increase the VPN throughput the
recommendation is to add multiple Cloud VPN gateway on the same region to load
balance the traffic across the tunnels. The 2 VPN tunnels configuration example
here is built based on the IPsec tunnel and BGP configuration illustrated above,
can be expanded to more tunnels if required.

##### Cisco ASR configuration

The ASR 1000 router run cef load balancing based on source and destination ip
address hash, each VPN tunnels will be treated as an equal cost path by routing,
it can support up to 16 equal cost paths load balancing.

    crypto ikev2 keyring VPN_SCALE_TEST_KEY
     peer GCP1
      address 104.196.200.68
      pre-shared-key MySharedSecret
     peer GCP3
      address 35.185.3.177
      pre-shared-key MySharedSecret
    !

    interface Tunnel1
     description VPN tunnel1 to same region GCP for load balancing
     ip address 169.254.0.2 255.255.255.252
     ip mtu 1400
     ip tcp adjust-mss 1360
     tunnel source TenGigabitEthernet0/0/0
     tunnel mode ipsec ipv4
     tunnel destination 104.196.200.68
     tunnel protection ipsec profile VPN_SCALE_TEST_VTI
    !

    interface Tunnel3
     description VPN tunnel3 to the same region GCP for load balancing
     ip address 169.254.0.10 255.255.255.252
     ip mtu 1400
     ip tcp adjust-mss 1360
     tunnel source TenGigabitEthernet0/0/0
     tunnel mode ipsec ipv4
     tunnel destination 35.185.3.177
     tunnel protection ipsec profile VPN_SCALE_TEST_VTI_3
    !

    router bgp 65001
     bgp log-neighbor-changes
     neighbor GCP peer-group
     neighbor GCP remote-as 65002
     neighbor GCP timers <b>20 60 60
     neighbor 169.254.0.1 peer-group GCP
     neighbor 169.254.0.9 peer-group GCP
    !

     address-family ipv4
      network 10.0.0.0
      neighbor 169.254.0.1 activate
      neighbor 169.254.0.9 activate
      maximum-paths 16
     exit-address-family
    !

##### GCP Configuration

GCP does ECMP by default so there is no additional configuration required apart
from creating x number of tunnels where x depends on your throughput
requirements. You can either use a single VPN gateway to create multiple tunnels
or create separate VPN gateway for each tunnel.

Note: Actual performance vary depending on the following factors:

* Network capacity between the two VPN peers.
* The capabilities of the peer device. See your device's documentation for more
  information.
* Packet size. Because processing happens on a per-packet basis, having a
  significant percentage of smaller packets can reduce overall throughput.
* High [RTT](https://wikipedia.org/wiki/RTT) and packet loss rates can greatly
  reduce throughput for TCP.

## Testing the IPsec connection

The IPsec tunnel can be tested from the router by using ICMP to ping a host on
GCP. Be sure to use the `inside interface` on the ASR 1000.

    cisco-asr#ping 172.16.100.2 source 10.0.200.1
    Type escape sequence to abort.
    Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:
    Packet sent with a source address of 10.0.200.1
    !!!!!
    Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms

## Troubleshooting IPsec on ASR 1000

Please refer to the troubleshooting [ASR1k made easy](http://d2zmdbbm9feqrf.cloudfront.net/2017/usa/pdf/BRKCRS-3147.pdf) for

* The ASR 1000 system architecture
* IPsec Packet Flow
* IPsec show command
* Conditional feature debugging
* Packet Tracer
* IOS XE resource monitoring

## References

Please refer to the following documentation for Juniper SRX300 Platform feature
configuration guide and datasheet:

* [proposal-set (Security IKE)](https://www.juniper.net/documentation/en_US/junos/topics/reference/configuration-statement/security-edit-proposal-set-ike.html)
* [Example: Configuring a Route-Based VPN](https://www.juniper.net/documentation/en_US/junos/topics/example/ipsec-route-based-vpn-configuring.html)
* [IPsec VPN Overview](https://www.juniper.net/documentation/en_US/junos/topics/concept/vpn-security-overview.html)
* [BGP Configuration Guide](http://www.cisco.com/c/en/us/td/docs/ios-xml/ios/iproute_bgp/configuration/xe-3s/irg-xe-3s-book.html)
* [Load Balancing Configuration Guide](http://www.cisco.com/c/en/us/td/docs/ios-xml/ios/ipswitch_cef/configuration/xe-3s/isw-cef-xe-3s-book/isw-cef-load-balancing.html)
* [ASR 1000 Routers Datasheet](http://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/datasheet-c78-731632.html)
* [ASR 1000 ESP Datasheet](http://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/datasheet-c78-731640.html)
* [ASR 1000 Ordering Guide](http://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/guide-c07-731639.html)
* [IOS-XE NGE Support Product Tech Note](http://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/116055-technote-ios-crypto.html)

Refer to the following documentation for common error messages and debug commands:

* [IPsec Troubleshooting: Understanding and Using debug Commands](http://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/5409-ipsec-debug-00.html)
* [Resolve IP Fragmentation, MTU, MSS, and PMTUD Issues with GRE and IPsec](http://www.cisco.com/c/en/us/support/docs/ip/generic-routing-encapsulation-gre/25885-pmtud-ipfrag.html)
* [Invalid SPI](http://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/115801-technote-iosvpn-00.html)
* [IPsec Anti-Replay Check Failures](http://www.cisco.com/c/en/us/support/docs/ip/internet-key-exchange-ike/116858-problem-replay-00.html)
* [IKEv2 Selection Rules for Keyrings and Profiles](http://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/117259-trouble-ios-ike-00.html)
* [Embedded Packet Capture for IOS-XE ](http://www.cisco.com/c/en/us/support/docs/ios-nx-os-software/ios-embedded-packet-capture/116045-productconfig-epc-00.html)

To learn more about GCP networking, refer to below documents:

* [GCP VPC Networks](https://cloud.google.com/compute/docs/vpc/)
* [GCP Cloud VPN](https://cloud.google.com/compute/docs/vpn/overview)
* [GCP advanced VPN](https://cloud.google.com/compute/docs/vpn/advanced)
* [Troubleshooting VPN on GCP](https://cloud.google.com/compute/docs/vpn/troubleshooting)
