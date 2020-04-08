---
title: Google Cloud HA VPN Interop Guide for [PRODUCT]
description: Describes how to build site-to-site IPsec VPNs between HA VPN on Google Cloud Platform (GCP) and [VENDOR] [PRODUCT].
author: [AUTHOR]
tags: HA VPN, Cloud VPN, interop, [VENDOR], [PRODUCT]
date_published: YYYY-mm-dd
---

**BEGIN: HOW TO USE THIS TEMPLATE**

1. Make a copy of this template.
1. On your local computer, update and add information as indicated:
    + Fill in the metadata (title, description, author, date_published) at the top
      of this file.
    + There are notes in the template for you, the author, that explain where you need to
      make changes. These notes are enclosed in angle brackets (&lt; &gt;). Make sure you remove
      all text enclosed in angle brackets (&lt; &gt;).
    + The template contains placeholders for things like the vendor and 
      product name. These are also enclosed in brackets—for example, 
      every place you see `<vendor-name>` and `<product-name>`, 
      substitute approriate names.
    + After you've made appropriate updates, _remove_ content in angle brackets.
    + Remove these instructions.
    + Because this is a template for a variety of setups, it might contain
      content that isn't relevant to your scenario. Remove (or update)
      any sections that don't apply to you.
1. Fork the [GoogleCloudPlatform/community/](https://github.com/GoogleCloudPlatform/community/) repo.
1. In your fork, add a new folder named `/tutorials/[YOUR_TUTORIAL]`. For the
   folder name, use hyphens to separate words. We recommend that you 
   include a product name in the folder name, such as `using-cloud-vpn-with-cisco-asr`.
1. Copy the updated file to the `index.md` file of the new folder.
1. Create a branch.
1. Issue a PR to get your new content into the community site.
   
<**END: HOW TO USE THIS TEMPLATE**>

# Using HA VPN with \<vendor-name>\<product-name>

Author: \<author name and email address>

Learn how to build site-to-site IPSec VPNs between [HA VPN](https://cloud.google.com/vpn/docs/)
on Google Cloud Platform (GCP) and \<vendor-name>\<product-name>.

[TODO: Change it with a real HA VPN guide when available]
<To see a finished version of this guide, see the
[Using Cloud VPN with Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page).>

\<Put trademark statements here:> \<vendor terminology> and the \<vendor> logo are
trademarks of \<vendor company name> or its affiliates in the United States
and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

## Introduction

This guide walks you through the process of configuring route based VPN
tunnel between \<vendor-name>\<product-name> and the [HA VPN service](https://cloud.google.com/vpn/docs) 
on GCP.

For more information about HA or Classic VPN, see the
[Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

\<This is some sample terminology. Add any terminology to this section that needs
explanation.>

-  **GCP VPC network**: A single virtual network within a single GCP project.
-  **On-premises gateway**: The VPN device on the non-GCP side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. GCP instructions are written from the
point of view of the GCP VPC network, so *on-premises gateway* refers to the
gateway that's connecting _to_ GCP.
-  **External IP address** or **GCP peer address**: External IP 
addresses used by peer VPN devices to establish HA VPN with GCP. 
External IP addresses are allocated automatically, one for each gateway interface within a 
GCP project.
-  **Dynamic routing**: GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
Note that HA VPN only supports dynamic routing.
-  **\<vendor-name>\<product-name>**: Definition.
-  **\<vendor-name>\<product-name>**: Definition.

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/vpn/docs/concepts/topologies).

This interop guide is based on the [1-peer-2-address](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) topology.

## Product environment

The \<vendor-name>\<product-name> equipment used in this guide is as follows:

-  **Vendor**: \<vendor-name>
-  **Model**: \<model name>
-  **Software release**: \<full software release name>

## Before you begin

1.  Review information about how
    [dynamic routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#dynamic-routing)
    works in Google Cloud Platform.

1.  Make sure your peer VPN gateway supports BGP.

1.  Select or [create](https://console.cloud.google.com/cloud-resource-manager) a GCP project.

1.  Make sure that [billing](https://cloud.google.com/billing/docs/how-to/modify-project) is
    enabled for your GCP project.

1.  [Install and initialize the Cloud SDK](https://cloud.google.com/sdk/docs/).

1.  If you are using `gcloud` commands, set your project ID with the following command:

        gcloud config set project [PROJECT_ID]
        
    The `gcloud` instructions on this page assume that you have set your project ID before
    issuing commands.
    
1.  You can also view a project ID that has already been set:

        gcloud config list --format='text(core.project)'

### Licenses and modules

\<This section is optional, because some VPN vendors can be open source or cloud
providers that don't require such licensing.>

Before you configure your \<vendor-name>\<product-name> for use with HA VPN,
make sure that the following licenses are available:

\<Below are some examples. Replace with information that applies to the
product.>

-  Advanced Enterprise Services (SLASR1-AES) or Advanced IP Services
Technology Package License (SLASR1-AIS).
-  IPSec RTU license (FLASR1-IPSEC-RTU).
-  Encryption HW module (ASR1002HX-IPSECHW(=) and ASR1001HX-IPSECW(=)) and
Tiered Crypto throughput license, which applies to ASR1002-HX and ASR1001-HX
chassis only.

For detailed \<vendor-name>\<product-name> license information, see the
\<Vendor-Guide-link> documentation.

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a GCP project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values used in this guide. 

| Parameter description | Placeholder          | Example value                                          |
|-----------------------|----------------------|--------------------------------------------------------|
| Vendor name           | `[VENDOR_NAME]`      | Your product's vendor name. This value should have no spaces or punctuation in it other than underscores or hyphens, because it will be used as part of the names for GCP entities. |
| GCP project name      | `[PROJECT_NAME]`     | `vpn-guide`                                            |
| Shared secret         | `[SHARED_SECRET]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| VPC network name      | `[NETWORK]`          | `network-a`                                            |
| Subnet mode           | `[SUBNET_MODE]`      | `custom`                                               |
| VPN BGP routing mode  | `[BGP_ROUTING_MODE]` | `global`                                               |
| Subnet on the GCP VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_1]` | `subnet-a-central` |
| Subnet on the GCP VPC network (for example, `vpn-vendor-test-network`) | `[SUBNET_NAME_2]` | `subnet-a-west` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION1]` | `us-central1` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION2]` | `us-west1` |
| IP address range for the GCP VPC subnet (`vpn-subnet-1`) | `[RANGE_1]` | `10.0.1.0/24` |
| IP address range for the GCP VPC subnet (`vpn-subnet-2`) | `[RANGE_2]` | `10.0.2.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to GCP. | `[IP_ON_PREM_SUBNET]` | `192.168.1.0/24` |
| External static IP address for the first internet interface of \<vendor-name>\<product-name>  | `[ON_PREM_GW_IP_0]` | `199.203.248.181` |
| External static IP address for the second internet interface of \<vendor-name>\<product-name> | `[ON_PREM_GW_IP_1]` | `199.203.248.182` |
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

## Configure the GCP side

This section covers how to configure HA VPN.

There are two ways to create HA VPN gateways on GCP: using the GCP Console and using
[`gcloud` commands](https://cloud.google.com/sdk/).

This section describes how to perform the tasks using `gcloud` commands. 

### Initial tasks

Complete the following procedures before configuring a GCP HA VPN gateway and tunnel.

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

    gcloud beta compute vpn-gateways create [GW_NAME] \
    --network [NETWORK] \
    --region [REGION]
    
The command should look similar to the following example:
    
    gcloud beta compute vpn-gateways create ha-vpn-gw-a \
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

- `[ROUTER_NAME]`: The name of the new Cloud Router, which you must create in the same GCP
  region as the Cloud HA VPN gateway.
- `[GOOGLE_ASN]`: Any private ASN (64512-65534, 4200000000-4294967294) that you are not
  already using in the peer network. The Google ASN is used for all BGP sessions on the
  same Cloud Router, and it cannot be changed later.

The command should look similar to the following example:

    gcloud compute routers create router-a \
    --region us-central1 \
    --network network-a \
    --asn 65001
    
### Create an External VPN Gateway resource

Create an external VPN gateway resource that provides information to GCP about your peer VPN gateway or gateways.
Depending on the HA recommendations for your peer VPN gateway, you can create external VPN gateway resource for the 
following different types of on-premises VPN gateways:

- Two separate peer VPN gateway devices where the two devices are redundant with each other and each device
  has its own public IP address.
- A single peer VPN gateway that uses two separate interfaces, each with its own public IP address. For this
  kind of peer gateway, you can create a single external VPN gateway with two interfaces.
- A single peer VPN gateway with a single public IP address.

This interop guide only covers the second option (one peer, two addresses). 

#### Create an External VPN Gateway resource for a single peer VPN gateway with two separate interfaces

    gcloud beta compute external-vpn-gateways create [PEER_GW_NAME] \
    --interfaces 0=[ON_PREM_GW_IP_0],1=[ON_PREM_GW_IP_1] \

The command should look similar to the following example:
 
    gcloud beta compute external-vpn-gateways create peer-gw   \
     --interfaces 0=204.237.220.4,1=204.237.220.35 \

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
    
    gcloud compute firewall-rules create network-a-to-on-prem \
    --network network-a \
    --allow tcp,udp,icmp \
    --source-ranges 192.168.1.0/24
    
You must also configure the on-premises network firewall to allow inbound traffic from your
VPC subnet prefixes.
    
## Configure the \<vendor-name>\<vendor product> side

\<This section includes sample tasks that describe how to configure the
on-premises side of the VPN gateway configuration using \<vendor-name>
equipment.>

### Creating the base network configuration

\<The sample wording below assumes that you are showing the configuration steps
in the configuration code snippet below. If not, list the steps needed.>

Follow the procedure listed in the configuration code snippet below to create
the base Layer 3 network configuration of \<vendor-name>.

At least one internal-facing network interface is required in order to
connect to your on-premises network, and one external-facing interface is
required in order to connect to GCP.

\<Insert configuration code here, indented with four spaces so that it appears as a codeblock.>

### Creating the base VPN gateway configuration

Follow the procedures in this section to create the base VPN configuration.

\<This section contains outlines of subsections for different aspects of
configuring IPSec and IKE on the vendor side. Fill in the sections that are
relevant to the current configuration, and remove any sections that don't
apply.>

#### GCP-compatible settings for IPSec and IKE

Make sure to configure [Ciphers supported by GCP](https://cloud.google.com/vpn/docs/how-to/configuring-peer-gateway#configuring_ike) only.

#### Configure the IKE proposal and policy

\<Insert the instructions for creating the IKE proposal and policy here.>

\<Insert configuration code here, indented so that it appears as a codeblock.>

#### Configure the IKEv2 keyring

\<Insert the instructions for creating the IKEv2 keyring here.>

\<Insert configuration code here, indented so that it appears as a codeblock.>

#### Configure the IKEv2 profile

\<Insert the instructions for creating the IKEv2 profile here.>

\<Insert configuration code here, indented so that it appears as a codeblock.>

#### Configure the IPSec security association (SA)

\<Insert the instructions for creating the IPSec SA here. Below is an example of
parameters to set.>

- **IPsec SA replay window-size**: Set this to `1024`, which is the recommended value
  for \<vendor-name>\<product-name>.

\<Insert configuration code here, indented so that it appears as a codeblock.>

#### Configure the IPSec transform set

\<Insert the instructions for creating the IPSec transform set here.>

\<Insert configuration code here, indented so that it appears as a codeblock.>

#### Configure the IPSec static virtual tunnel interface (SVTI)

\<Insert the instructions for creating the IPSec SVTI here. Below is an 
example of parameters to set.>

- Adjust the maximum segment size (MSS) value of TCP packets going through
  a router as discussed in
  [MTU Considerations](https://cloud.google.com/vpn/docs/concepts/mtu-considerations)
  for Cloud VPN.

\<Insert configuration code here, indented so that it appears as a codeblock.>

### Configuring the dynamic routing protocol

Follow the procedure in this section to configure dynamic routing for traffic
through the VPN tunnel or tunnels using the BGP routing protocol.

\<Insert the instructions for configuring dynamic routing here. Indent code so that it appears as a codeblock.>

To advertise additional prefixes to GCP, \<insert instructions here>:

\<Insert configuration code here, indented so that it appears as a codeblock.>

Additional recommended BGP configurations:

- Configure keepalive timer = 20
- Hold timer = 60s; 
- BGP Graceful Restart time = 1s
- Stalepath-time = 300s

\<Insert configuration code here, indented so that it appears as a codeblock.>

### Saving the configuration

Follow the procedure in this section to save the on-premises configuration.

\<Insert the instructions for saving the configuration here.>

\<Insert configuration code here, indented so that it appears as a codeblock.>

### Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. For either side, 
make sure that the subnet that a machine or virtual machine is located in is being forwarded 
through the VPN tunnel.

1.  Create VMs on both sides of the tunnel. Make sure that you configure the
    VMs on a subnet that will pass traffic through the VPN tunnel.
    
    - Instructions for creating virtual machines in Compute Engine are in the
      [Getting started guide](https://cloud.google.com/compute/docs/quickstart).
    - Instructions for creating machines machines on-premises are located \<here>.

1.  After you have deployed VMs on both GCP and on-premises, you can use 
    an ICMP echo (ping) test to test network connectivity through the VPN tunnel.

    On the GCP side, use the following instructions to test the connection to a
    machine that's behind the on-premises gateway:

    1.  In the GCP Console, [go to the VM Instances page](https://console.cloud.google.com/compute).
    1.  Find the GCP virtual machine you created.
    1.  In the **Connect** column, click **SSH**. A Cloud Shell window opens at the VM command line.
    1.  Ping a machine that's behind the on-premises gateway.

    \<Insert any additional instructions for testing the VPN tunnels from the \<vendor-name>\<product-name>
    here. For example, below is an example of a successful ping from a Cisco ASR router to GCP.>

        cisco-asr#ping 172.16.100.2 source 10.0.200.1
        Type escape sequence to abort.
        Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:
        Packet sent with a source address of 10.0.200.1
        !!!!!
        Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms

## Troubleshooting IPSec on \<vendor-name>\<product-name>

For troubleshooting information, see the \<vendor-name>\<product-name> troubleshooting guide: \<add link>.

\<Add details here about what kind of troubleshooting information can be found in the \<vendor-name>\<product-name> guide.>

## Reference documentation

You can refer to the following \<vendor-name>\<product-name> documentation and
Cloud VPN documentation for additional information about both products.

### GCP documentation

To learn more about GCP networking, see the following documents:

-  [VPC networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Advanced Cloud VPN configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Check VPN status](#https://cloud.google.com/vpn/docs/how-to/checking-vpn-status)
-  [Terraform template for HA VPN](https://www.terraform.io/docs/providers/google/r/compute_ha_vpn_gateway.html)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### \<vendor-name>\<product-name> documentation

For more product information on \<vendor-name>\<product-name>, refer to the following
\<product-name> feature configuration guides and datasheets:

-  \<guide name and link>
-  \<guide name and link>

For common \<vendor-name>\<product-name> error messages and debug commands, see
the following guides:

-  \<guide name and link>
-  \<guide name and link>
