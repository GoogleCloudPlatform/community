---
title: Google Cloud HA VPN interoperability guide for Fortigate
description: Describes how to build site-to-site IPSec VPNs between HA VPN on Google Cloud and Fortigate.
author: ashishverm
tags: HA VPN, Cloud VPN, interop, Fortinet, FortiOS
date_published: 2019-07-16
---

Ashish Verma | Technical Program Manager | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Fortinet terminology and the Fortinet logo are trademarks of Fortinet or its affiliates in the
United States and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

This guide walks you through the process of configuring a route-based VPN tunnel between
Fortigate and the [HA VPN service](https://cloud.google.com/network-connectivity/docs/vpn/) on Google Cloud.

For more information about HA or Classic VPN, see the
[Cloud VPN overview](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview).

## Terminology

Below are definitions of terms used throughout this guide.

-  **Google Cloud VPC network**: A single virtual network within a single Google Cloud project.
-  **On-premises gateway**: The VPN device on the non- Google Cloud side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. Google Cloud instructions are written from the
point of view of the Google Cloud VPC network, so *on-premises gateway* refers to the
gateway that's connecting _to_ Google Cloud.
-  **External IP address** or **Google Cloud peer address**: External IP
addresses used by peer VPN devices to establish HA VPN with Google Cloud.
External IP addresses are allocated automatically, one for each gateway interface within a
Google Cloud project.
-  **Dynamic routing**: Google Cloud dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
Note that HA VPN only supports dynamic routing.

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies).

This interop guide is based on the
[1-peer-2-address](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies#1-peer-2-addresses) topology.

The same HA VPN configuration also applies to the [2-peers](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies#2-peers)
topology.

## Product environment

The Fortigate equipment used in this guide is as follows:

-  **Vendor**: Fortinet
-  **Model**: Fortigate
-  **Software release**: 6.2.0

## Before you begin

1.  Review information about how
    [dynamic routing](https://cloud.google.com/network-connectivity/docs/vpn/concepts/choosing-networks-routing#dynamic-routing)
    works in Google Cloud.

1.  Make sure that your peer VPN gateway supports BGP and is directly connected to the internet. Fortigate configurations
    are not tested with a device behind 1:1 NAT.

1.  Select or [create](https://console.cloud.google.com/cloud-resource-manager) a Google Cloud project.

1.  Make sure that [billing](https://cloud.google.com/billing/docs/how-to/modify-project) is
    enabled for your Google Cloud project.

1.  [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1.  If you are using `gcloud` commands, set your project ID with the following command:

        gcloud config set project [PROJECT_ID]

    The `gcloud` instructions on this page assume that you have set your project ID before
    issuing commands.

1.  You can also view a project ID that has already been set:

        gcloud config list --format='text(core.project)'
        

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose values you must
provide. For example, a command might include a Google Cloud project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values used in this guide.

| Parameter description | Placeholder          | Example value                                          |
|-----------------------|----------------------|--------------------------------------------------------|
| Vendor name           | `[VENDOR_NAME]`      | Fortinet                                               |
| Google Cloud project name      | `[PROJECT_NAME]`     | `vpn-guide`                                            |
| Shared secret         | `[SHARED_SECRET]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| VPC network name      | `[NETWORK]`          | `network-a`                                            |
| Subnet mode           | `[SUBNET_MODE]`      | `custom`                                               |
| VPN BGP routing mode  | `[BGP_ROUTING_MODE]` | `global`                                               |
| Subnet on the Google Cloud VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_1]` | `subnet-a-central` |
| Subnet on the Google Cloud VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_2]` | `subnet-a-west` |
| Google Cloud region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION1]` | `us-central1` |
| Google Cloud region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION2]` | `us-west1` |
| IP address range for the Google Cloud VPC subnet (`vpn-subnet-1`) | `[RANGE_1]` | `10.0.1.0/24` |
| IP address range for the Google Cloud VPC subnet (`vpn-subnet-2`) | `[RANGE_2]` | `10.0.2.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to Google Cloud. | `[IP_ON_PREM_SUBNET]` | `192.168.1.0/24` |
| External static IP address for the first internet interface of Foritgate  | `[ON_PREM_GW_IP_0]` | `209.119.81.228` |
| External static IP address for the second internet interface of Foritgate | `[ON_PREM_GW_IP_1]` | `209.119.82.228` |
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
| Dead Peer Detection                     | `[phase1-interface]`        | `disable / on-idle / on demand`     |

## Configure the Google Cloud side

This section covers how to configure HA VPN. See
[deply-ha-vpn-with-terraform](https://cloud.google.com/community/tutorials/deploy-ha-vpn-with-terraform)
for a quick deployment.

There are two ways to create HA VPN gateways on Google Cloud: using the Cloud Console and using
[`gcloud` commands](https://cloud.google.com/sdk/gcloud/). This section describes how to perform the tasks
using `gcloud` commands.

### Initial tasks

Complete the following procedures before configuring a Google Cloud HA VPN gateway and tunnel.

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

    gcloud compute vpn-gateways create [GW_NAME] \
    --network [NETWORK] \
    --region [REGION]

The command should look similar to the following example:

    gcloud compute vpn-gateways create ha-vpn-gw-a \
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

- `[ROUTER_NAME]`: The name of the new Cloud Router, which you must create in the same Google Cloud
  region as the Cloud HA VPN gateway.
- `[GOOGLE_ASN]`: Any private ASN (64512-65534, 4200000000-4294967294) that you are not
  already using in the peer network. The Google ASN is used for all BGP sessions on the
  same Cloud Router, and it cannot be changed later.

The command should look similar to the following example:

    gcloud compute routers create router-a \
    --region us-central1 \
    --network network-a \
    --asn 65001

### Create an external VPN gateway resource

Create an external VPN gateway resource that provides information to Google Cloud about your peer VPN gateway or gateways.
Depending on the HA recommendations for your peer VPN gateway, you can create external VPN gateway resources for the
following different types of on-premises VPN gateways:

- Two separate peer VPN gateway devices, where the two devices are redundant with each other and each device
  has its own public IP address.
- A single peer VPN gateway that uses two separate interfaces, each with its own public IP address. For this
  kind of peer gateway, you can create a single external VPN gateway with two interfaces.
- A single peer VPN gateway with a single public IP address.

This interop guide only covers the second option (one peer, two addresses).

#### Create an external VPN gateway resource for a single peer VPN gateway with two separate interfaces

    gcloud compute external-vpn-gateways create [PEER_GW_NAME] \
    --interfaces 0=[ON_PREM_GW_IP_0],1=[ON_PREM_GW_IP_1] \

The command should look similar to the following example:

    gcloud compute external-vpn-gateways create peer-gw   \
     --interfaces 0=209.119.81.228,1=209.119.82.228 \

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

The command should look similar to the following example:

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
interfaces and BGP peers. This example uses the automatic method.

1.  For the first VPN tunnel, add a new BGP interface to the Cloud Router:

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

1.  Add a BGP peer to the interface for the first tunnel:

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

1.  For the second VPN tunnel, add a new BGP interface to the Cloud Router:

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

1.  Add a BGP peer to the interface for the second tunnel:

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

1.  Verify the Cloud Router configuration

        gcloud compute routers get-status router-a \
         --region us-central1 \
         --format='flattened(result.bgpPeerStatus[].name,
           result.bgpPeerStatus[].ipAddress, result.bgpPeerStatus[].peerIpAddress)'

        gcloud compute routers describe [ROUTER_NAME] \
        --region [REGION]

### Configure firewall rules

Configure firewall rules to allow inbound traffic from the on-premises
network subnets:

    gcloud compute firewall-rules create [VPN_RULE_NAME] \
    --network [NETWORK] \
    --allow tcp,udp,icmp \
    --source-ranges [IP_ON_PREM_SUBNET]

The command should look similar to the following example:

    gcloud compute firewall-rules create on-prem-to-network-a \
    --network network-a \
    --allow tcp,udp,icmp \
    --source-ranges 192.168.1.0/24

You must also configure the on-premises network firewall to allow inbound traffic from your
VPC subnet prefixes.

## Configure the Fortigate side

The instructions in this section use the command-line interface. You can also use the graphical 
user interface for these configurations.

### Creating the base network configuration

Follow the procedure listed in the configuration code below to create
the base Layer 3 network configuration of Fortigate.

At least one internal-facing network interface is required to
connect to your on-premises network, and one external-facing interface is
required to connect to Google Cloud.

For the 1-peer-2-address topology, configure a minimum of three interfaces:
two outside interfaces that are connected to the internet and one inside interface
that is connected to the private network.

Make sure to replace the IP addresses based on your environment:

    config system interface
        edit port1
            set vdom root
            set mode static
            set ip 209.119.81.228 255.255.255.248
            set allowaccess ping https ssh fgfm
            set description wan1
        next
        edit port2
            set vdom root
            set mode static
            set ip 209.119.82.228 255.255.255.248
            set allowaccess ping https ssh
            set description wan2
        next
        edit port3
            set vdom root
            set mode static
            set ip 192.168.1.10 255.255.255.0
            set allowaccess ping
            set description lan1
        next

### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

#### Google Cloud-compatible settings for IPSec and IKE

Make sure to configure only 
[ciphers supported by Google Cloud](https://cloud.google.com/network-connectivity/docs/vpn/how-to/configuring-peer-gateway#configuring_ike).

#### Configure Phase 1 policy

This configuration creates the Phase 1 proposal. Make sure to change the
`local-gw`, `remote-gw`, and `psksecret` for your environment.

    config vpn ipsec phase1-interface
        edit GCP-HA-VPN-INT0
            set interface port1
            set ike-version 2
            set keylife 36000
            set peertype any
            set proposal aes128-sha1 aes128-sha512 aes128-md5
            set remote-gw 35.242.121.143
            set local-gw 209.119.81.228
            set psksecret mysharedsecret
            set dpd[disable | on-idle | on demand]
            set dpd-retryinterval 15
            set dpd-retrycount 3
        next
        edit GCP-HA-VPN-INT1
            set interface port2
            set ike-version 2
            set keylife 36000
            set peertype any
            set proposal aes128-sha1 aes128-sha512 aes128-md5
            set remote-gw 35.220.86.219
            set local-gw 209.119.82.228
            set psksecret mysharedsecret
        next
    end

#### Configure Phase 2 policy

This configuration creates the Phase 2 proposal.

    config vpn ipsec phase2-interface
        edit GCP-HA-VPN-INT0
            set phase1name GCP-HA-VPN-INT0
            set proposal aes128-sha1 aes256-sha1 aes128-sha256 aes256-sha256 aes128gcm aes256gcm
            set dhgrp 15 14 5
            set keylifeseconds 10800
        next
        edit GCP-HA-VPN-INT1
            set phase1name GCP-HA-VPN-INT1
            set proposal aes128-sha1 aes256-sha1 aes128-sha256 aes256-sha256 aes128gcm aes256gcm
            set dhgrp 15 14 5
            set keylifeseconds 10800
        next
    end

#### Configure tunnel interfaces

Edit tunnel interfaces for each VPN tunnel. Change `ip` and `remote-ip` values accordingly.

    config system interface
        edit GCP-HA-VPN-INT0
            set ip 169.254.142.154 255.255.255.255
            set remote-ip 169.254.142.153 255.255.255.252
        next
        edit GCP-HA-VPN-INT1
            set ip 169.254.92.230 255.255.255.255
            set remote-ip 169.254.92.229 255.255.255.252
        next
    end

### Configuring the dynamic routing protocol

Follow the procedure in this section to configure dynamic routing for traffic
through the VPN tunnel or tunnels using the BGP routing protocol.

With the configuration below, BGP peering will be enabled and all "connected" routes
will be advertised to the peer. Change redistribution of routes based on your
environment.

    config router bgp
        set as 65002
        set router-id 169.254.142.154
        config neighbor
            edit 169.254.142.153
                set soft-reconfiguration enable
                set remote-as 65001
            next
        end
        config neighbor
            edit 169.254.92.229
                set soft-reconfiguration enable
                set remote-as 65001
            next
        end
        config redistribute connected
            set status enable
        end
    end

See [fortigate-advanced-routing](https://help.fortinet.com/fos50hlp/54/Content/FortiOS/fortigate-advanced-routing-54/Routing_BGP/Background_Concepts.htm)
for advanced BGP configurations.

### Configure firewall policies

Create firewall policies to allow traffic between on-premises and Google Cloud private networks.

These policies allow traffic from all source and destination addresses, make required changes to the policy to allow
specific services and IP ranges.

    config firewall policy
        edit 1
            set name allow-gcp-to-lan
            set srcintf GCP-HA-VPN-INT0 GCP-HA-VPN-INT1
            set dstintf port3
            set srcaddr all
            set dstaddr all
            set action accept
            set schedule always
            set service ALL
        next
        edit 2
            set name allow-lan-to-gcp
            set srcintf port3
            set dstintf GCP-HA-VPN-INT0 GCP-HA-VPN-INT1
            set srcaddr all
            set dstaddr all
            set action accept
            set schedule always
            set service ALL
        end

### Verify configurations

1.  Verify that the IPsec tunnels are up:

        get vpn ipsec tunnel summary

1.  Verify that BGP peering is up:

        get router bgp

1.  Verify that routes are being exchanged with Google Cloud:

        get router info bgp neighbors 169.254.142.153 advertised-routes

        get router info bgp neighbors 169.254.142.153 received-routes

### Test connectivity

It's important to test the VPN connection from both sides of a VPN tunnel. For either side,
make sure that the subnet that a machine or virtual machine is located in is being forwarded
through the VPN tunnel.

1.  Create VMs on both sides of the tunnel. Make sure that you configure the
    VMs on a subnet that will pass traffic through the VPN tunnel.

    Instructions for creating virtual machines in Compute Engine are in the
    [Getting started guide](https://cloud.google.com/compute/docs/quickstart).
    
1.  After you have deployed VMs on both Google Cloud and on-premises, you can use
    an ICMP echo (ping) test to test network connectivity through the VPN tunnel.

    On the Google Cloud side, use the following instructions to test the connection to a
    machine that's behind the on-premises gateway:

    1.  In the Cloud Console, [go to the VM Instances page](https://console.cloud.google.com/compute).
    1.  Find the Google Cloud virtual machine you created.
    1.  In the **Connect** column, click **SSH**. A Cloud Shell window opens at the VM command line.
    1.  Ping a machine that's behind the on-premises gateway.

    You can also check connectivity from Fortigate to the VM deployed in Google Cloud.

        execute ping-options source 192.168.1.10

        execute ping 10.0.20.2

## Troubleshooting IPSec on Fortigate

For troubleshooting information, see
the [Foritgate VPN troubleshooting guide](https://docs.fortinet.com/).

## Reference documentation

See the following Foritgate documentation and Cloud VPN documentation for additional information.

### Google Cloud documentation

To learn more about Google Cloud networking, see the following documents:

-  [VPC networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN overview](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview)
-  [Advanced Cloud VPN configurations](https://cloud.google.com/network-connectivity/docs/vpn/concepts/advanced)
-  [Check VPN status](https://cloud.google.com/network-connectivity/docs/vpn/how-to/checking-vpn-status)
-  [Terraform template for HA VPN](https://www.terraform.io/docs/providers/google/r/compute_ha_vpn_gateway.html)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/support/troubleshooting)

### Fortigate documentation

For more Fortigate product information, see the following feature configuration guides:

-  [Fortinet next generation firewalls](https://www.fortinet.com/products/next-generation-firewall.html#overview)
-  [IPSec VPN web wizard](https://help.fortinet.com/fos60hlp/60/Content/FortiOS/fortigate-ipsecvpn/IPsec_VPN_Web-based_Manager/ipsec_vpn_help.htm?Highlight=ipsec)
