---
title: Google Cloud HA VPN interoperability guide for Cisco ASA 5506H
description: Build site-to-site IPSec VPNs between HA VPN on Google Cloud and Cisco ASA 5506H.
author: ashishverm
tags: HA VPN, Cloud VPN, interop, Cisco, ASA 5506H
date_published: 2019-07-12
---

Ashish Verma | Technical Program Manager | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Cisco terminology and the Cisco logo are trademarks of Cisco or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

This guide walks you through the process of configuring a route-based VPN tunnel
between Cisco ASA 5506H and the [HA VPN service](https://cloud.google.com/network-connectivity/docs/vpn/)
on Google Cloud.

For more information about HA and Classic VPN, see the
[Cloud VPN overview](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview).

## Terminology

Below are definitions of terms used throughout this guide.

-   **Google Cloud VPC network**: A single virtual network within a single Google Cloud project.
-   **On-premises gateway**: The VPN device on the non- Google Cloud side of the
    connection, which is usually a device in a physical data center or in
    another cloud provider's network. Google Cloud instructions are written from the
    point of view of the Google Cloud VPC network, so *on-premises gateway* refers to the
    gateway that's connecting _to_ Google Cloud.
-   **External IP address** or **Google Cloud peer address**: External IP
    addresses used by peer VPN devices to establish HA VPN with Google Cloud.
    External IP addresses are allocated automatically, one for each gateway interface within a
    Google Cloud project.
-   **Dynamic routing**: Google Cloud dynamic routing for VPN using the
    [Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
    Note that HA VPN only supports dynamic routing.
-   **VTI**: The ASA supports a logical interface called Virtual Tunnel Interface (VTI). 
    A VPN tunnel can be created between peers with Virtual Tunnel Interfaces configured. 

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies).

This interop guide is based on the [1-peer-2-address](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies#1-peer-2-addresses) topology.

## Product environment

The Cisco ASA 5506H equipment used in this guide is as follows:

-  **Vendor**: Cisco
-  **Model**: ASA 5506H
-  **Software release**: 9.9.2

## Before you begin

1.  Review information about how
    [dynamic routing](https://cloud.google.com/network-connectivity/docs/vpn/concepts/choosing-networks-routing#dynamic-routing)
    works in Google Cloud.

1.  Make sure that your peer VPN gateway supports BGP.

1.  For IKEv2 route-based VPN using VTI on ASA: Make sure that the code version is 9.8(1) or later. 

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

### Licenses and modules

There are no additional licenses required for site-to-site VPN on Cisco ASA 5506H.

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a Google Cloud project name or a region or
other parameters whose values are unique to your context. The following table 
lists the parameters and gives examples of the values used in this guide:

| Parameter description         | Placeholder               | Example value                                          |
|-------------------------------|---------------------------|--------------------------------------------------------|
| Vendor name                   | `[VENDOR_NAME]`           | Cisco                                                  |
| Google Cloud project name              | `[PROJECT_NAME]`          | `vpn-guide`                                            |
| Shared secret                 | `[SHARED_SECRET]`         | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                                |
| VPC network name              | `[NETWORK]`               | `network-a`                                            |
| Subnet mode                   | `[SUBNET_MODE]`           | `custom`                                               |
| VPN BGP routing mode          | `[BGP_ROUTING_MODE]`      | `global`                                               |
| Subnet on the Google Cloud VPC network | `[SUBNET_NAME_1]`         | `subnet-a-central`                                     |
| Subnet on the Google Cloud VPC network | `[SUBNET_NAME_2]`         | `subnet-a-west`                                        |
| Google Cloud region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION1]` | `us-central1` |
| Google Cloud region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION2]` | `us-west1` |
| IP address range for the Google Cloud VPC subnet | `[RANGE_1]` | `10.0.1.0/24` |
| IP address range for the Google Cloud VPC subnet | `[RANGE_2]` | `10.0.2.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to Google Cloud. | `[IP_ON_PREM_SUBNET]` | `192.168.1.0/24` |
| External static IP address for the first internet interface of Cisco ASA 5506H  | `[ON_PREM_GW_IP_0]` | `209.119.81.225` |
| External static IP address for the second internet interface of Cisco ASA 5506H | `[ON_PREM_GW_IP_1]` | `209.119.82.226` |
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

## Configure the Google Cloud side

This section covers how to configure HA VPN.

There are two ways to create HA VPN gateways on Google Cloud: using the Cloud Console and using
[`gcloud` commands](https://cloud.google.com/sdk/).

This section describes how to perform the tasks using `gcloud` commands.

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
     --interfaces 0=209.119.81.225,1=209.119.82.226

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
        --region us-central1

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
        --region [REGION]

    The command should look similar to the following example:

        gcloud compute routers add-bgp-peer router-a \
        --peer-name peer-a \
        --peer-asn 65002 \
        --interface if-tunnel-a-to-on-prem-if-1 \
        --region us-central1

1.  Verify the Cloud Router configuration

        gcloud compute routers get-status router-a \
         --region us-central1 \
         --format='flattened(result.bgpPeerStatus[].name,
           result.bgpPeerStatus[].ipAddress, result.bgpPeerStatus[].peerIpAddress)'

        gcloud compute routers describe router-a \
        --region us-central1

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

## Configure the Cisco ASA 5506H side

### Creating the base network configuration

For the [1-peer-2-address](https://cloud.google.com/network-connectivity/docs/vpn/concepts/topologies#1-peer-2-addresses)
topology, configure a minimum of three interfaces, named `outside-0`, `outside-1`, and `inside`. Outside 
interfaces are connected to the internet; the inside interface is connected to the private network.

Enter the configuration mode to create the base Layer 3 network configuration for the Cisco system,
replacing the IP addresses based on your environment:

    configure terminal
    interface GigabitEthernet1/1
     nameif outside-0
     security-level 0
     ip address 209.119.81.225 255.255.255.248
    !
    interface GigabitEthernet1/2
     nameif inside
     security-level 100
     ip address 192.168.1.1 255.255.255.0
    !
    interface GigabitEthernet1/3
     nameif outside-1
     security-level 0
     ip address 209.119.82.226 255.255.255.248
    !
    
### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

Make sure to configure [ciphers supported by Google Cloud](https://cloud.google.com/network-connectivity/docs/vpn/how-to/configuring-peer-gateway#configuring_ike) only.

#### Configure the IKEv2 policy

Enter the configuration mode on Cisco ASA and create IKEv2 policies.

    crypto ikev2 policy 10
     encryption aes-gcm-256
     group 14
     prf sha512 sha384 sha256 sha
     lifetime seconds 36000
    crypto ikev2 enable outside-0
    crypto ikev2 enable outside-1
    
#### Configure the IKEv2 proposal

    crypto ipsec ikev2 ipsec-proposal GCP
     protocol esp encryption aes-gcm-256
     protocol esp integrity sha-512

#### Configure the IPSec profile

    crypto ipsec profile GCP
     set ikev2 ipsec-proposal GCP
     set pfs group14
     set security-association lifetime seconds 10800
     set security-association lifetime kilobytes unlimited

#### Configure tunnel groups for each peer IP address

Tunnel group parameters set the access policies and protocol-specific connection 
parameters for the IPSec tunnel. The first command sets the tunnel type to `ipsec-l2l` 
(site-to-site or, in Cisco terms, lan-to-lan). The next command block sets 
the `general-attributes` for the IPSec tunnel. In this case the `default-group-policy`
for the tunnel is being set to the policy named `GCP` and the `ipsec-attributes`
for the tunnel are being set. 

    group-policy GCP internal
    group-policy GCP attributes
     vpn-tunnel-protocol ikev2 

    tunnel-group 35.242.106.213 type ipsec-l2l
    tunnel-group 35.242.106.213 general-attributes
     default-group-policy GCP
    tunnel-group 35.242.106.213 ipsec-attributes
     isakmp keepalive threshold 10 retry 3
     ikev2 remote-authentication pre-shared-key mysharedsecret
     ikev2 local-authentication pre-shared-key mysharedsecret

    tunnel-group 35.220.86.219 type ipsec-l2l
    tunnel-group 35.220.86.219 general-attributes
     default-group-policy GCP
    tunnel-group 35.220.86.219 ipsec-attributes
     isakmp keepalive threshold 10 retry 3
     ikev2 remote-authentication pre-shared-key mysharedsecret
     ikev2 local-authentication pre-shared-key mysharedsecret

#### Configure the IPSec virtual tunnel interface (VTI)

VTI allows route-based VPNs on Cisco ASA. This configuration creates two VTIs with 
interface name and ipsec configurations:

    interface Tunnel10
     nameif gcp-if-0
     ip address 169.254.163.218 255.255.255.252 
     tunnel source interface outside-0
     tunnel destination 35.242.106.213
     tunnel mode ipsec ipv4
     tunnel protection ipsec profile GCP
    !
    interface Tunnel20
     nameif gcp-if-1
     ip address 169.254.92.230 255.255.255.252 
     tunnel source interface outside-1
     tunnel destination 35.220.86.219
     tunnel mode ipsec ipv4
     tunnel protection ipsec profile GCP
    !

### Configuring the dynamic routing protocol and access policies

Follow the procedure in this section to configure dynamic routing for traffic
through the VPN tunnel or tunnels using the BGP routing protocol. This configuration
will use ECMP to load-balance the traffic between the two tunnels.

Configure prefix lists to limit the inbound and outbound prefix advertisement:

    prefix-list GCP-IN seq 5 permit 10.0.1.0/24 le 32
    prefix-list GCP-IN seq 6 permit 10.0.2.0/24 le 32
    prefix-list GCP-OUT seq 5 permit 192.168.1.0/24 le 32

Configure BGP peers to dynamically exchange prefixes between on-premises and Google Cloud:

    router bgp 65002
     bgp log-neighbor-changes
     bgp graceful-restart
     bgp router-id 192.168.1.1
     address-family ipv4 unicast
      neighbor 169.254.163.217 remote-as 65001
      neighbor 169.254.163.217 ebgp-multihop 2
      neighbor 169.254.163.217 activate
      neighbor 169.254.163.217 prefix-list GCP-IN in
      neighbor 169.254.163.217 prefix-list GCP-OUT out
      neighbor 169.254.163.217 maximum-prefix 100 70
      neighbor 169.254.92.229 remote-as 65001
      neighbor 169.254.92.229 ebgp-multihop 2
      neighbor 169.254.92.229 activate
      neighbor 169.254.92.229 prefix-list GCP-IN in
      neighbor 169.254.92.229 prefix-list GCP-OUT out
      neighbor 169.254.92.229 maximum-prefix 100 70
      network 192.168.1.0
      maximum-paths 2
      no auto-summary
      no synchronization
     exit-address-family
    !
    
Create an access list to allow traffic from Google Cloud and apply on tunnel interfaces.

    access-list GCP-IN extended permit ip any any 
    access-group GCP-IN in interface gcp-if-0
    access-group GCP-IN in interface gcp-if-0 control-plane
    access-group GCP-IN in interface gcp-if-1
    access-group GCP-IN in interface gcp-if-1 control-plane

### Save the configuration

Save the on-premises configuration:

    write memory

### Verify the configurations

    CISCO-ASA5506H-001# sh crypto ikev2 sa  detail

    IKEv2 SAs:

    Session-id:100, Status:UP-ACTIVE, IKE count:1, CHILD count:1

    Tunnel-id Local                   Remote                Status         Role
    1738689761 209.119.81.225/500     35.220.72.68/500       READY    INITIATOR
          Encr: AES-GCM, keysize: 256, Hash: N/A, DH Grp:14, Auth sign: PSK, Auth verify: PSK
          Life/Active Time: 36000/24695 sec
          Session-id: 100
          
    CISCO-ASA5506H-001# sh crypto ipsec sa detail
    interface: tunnel-a
        Crypto map tag: __vti-crypto-map-4-0-10, seq num: 65280, local addr: 209.119.81.225

      local ident (addr/mask/prot/port): (0.0.0.0/0.0.0.0/0/0)
      remote ident (addr/mask/prot/port): (0.0.0.0/0.0.0.0/0/0)
      current_peer: 35.242.111.74

### Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. For either side,
make sure that the subnet that a machine or virtual machine is located in is being forwarded
through the VPN tunnel.

1.  Create a VM on Google Cloud, configuring the VMs on a subnet that will pass traffic through the VPN tunnel:
    
        gcloud compute instances create test-vpn-tunnel-1 --subnet=subnet-a-central \
        --machine-type=f1-micro --image-family=debian-9 --image-project=debian-cloud --no-address      

1.  After you have deployed VMs on Google Cloud and on-premises, you can use
    an ICMP echo (ping) test to test network connectivity through the VPN tunnel.

    On the Google Cloud side, use the following instructions to test the connection to a
    machine that's behind the on-premises gateway:

    1.  In the Cloud Console, [go to the VM Instances page](https://console.cloud.google.com/compute).
    1.  Find the Google Cloud virtual machine you created.
    1.  In the **Connect** column, click **SSH**. A Cloud Shell window opens at the VM command line.
    1.  Ping a machine that's behind the on-premises gateway.

            CISCO-ASA5506H-001#ping 10.0.1.3 source 192.168.1.1
            Type escape sequence to abort.
            Sending 5, 100-byte ICMP Echos to 10.0.1.3, timeout is 2 seconds:
            Packet sent with a source address of 192.168.1.1
            !!!!!
            Success rate is 100 percent (5/5), round-trip min/avg/max = 20/21/20 ms

## Reference documentation

See the following Cisco ASA 5506H documentation and Cloud VPN documentation for additional information
about both products.

### Google Cloud documentation

To learn more about Google Cloud networking, see the following documents:

-  [VPC networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN overview](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview)
-  [Advanced Cloud VPN configurations](https://cloud.google.com/network-connectivity/docs/vpn/concepts/advanced)
-  [Check VPN status](https://cloud.google.com/network-connectivity/docs/vpn/how-to/checking-vpn-status)
-  [Terraform template for HA VPN](https://www.terraform.io/docs/providers/google/r/compute_ha_vpn_gateway.html)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/support/troubleshooting)
-  [Create a virtual machine on Google Cloud](https://cloud.google.com/compute/docs/quickstart)

### Cisco ASA 5506H documentation

-  [ASA Virtual Tunnel Interface](https://www.cisco.com/c/en/us/td/docs/security/asa/asa97/configuration/vpn/asa-97-vpn-config/vpn-vti.html)
-  [ASA site2site VPN](https://www.cisco.com/c/en/us/td/docs/security/asa/asa84/configuration/guide/asa_84_cli_config/vpn_site2site.html)
