---
title: Google Cloud HA VPN interoperability guide for AWS
description: Describes how to build site-to-site IPSec VPNs between HA VPN on Google Cloud Platform (GCP) and AWS.
author: ashishverm,
tags: HA VPN, Cloud VPN, interop, AWS
date_published: 2019-07-16
---

Learn how to build site-to-site IPSec VPNs between [HA VPN](https://cloud.google.com/vpn/docs/)
on Google Cloud Platform (GCP) and AWS.

AWS terminology and the AWS logo are trademarks of Amazon Web Services or its affiliates
in the United States and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

## Introduction

This guide walks you through the process of configuring route-based VPN tunnels between
AWS and the [HA VPN service](https://cloud.google.com/vpn/docs) on GCP.

For more information about HA or Classic VPN, see the
[Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

-  **GCP VPC network**: A single virtual network within a single GCP project.
-  **On-premises gateway**: The VPN device on the non-GCP side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. GCP instructions are written from the
point of view of the GCP VPC network, so *on-premises gateway* refers to the
gateway that's connecting *to* GCP.
-  **External IP address** or **GCP peer address**: External IP
addresses used by peer VPN devices to establish HA VPN with GCP.
External IP addresses are allocated automatically, one for each gateway interface within a
GCP project.
-  **Dynamic routing**: GCP dynamic routing for VPN using the
[Border Gateway Protocol (BGP)](https://wikipedia.org/wiki/Border_Gateway_Protocol).
Note that HA VPN only supports dynamic routing.

## Topology

HA VPN supports [multiple topologies](https://cloud.google.com/vpn/docs/concepts/topologies).

This interop guide is based on the
[AWS-peer-gateways](https://cloud.google.com/vpn/docs/concepts/topologies#aws_peer_gateways) topology
using with `REDUNDANCY_TYPE` of `FOUR_IPS_REDUNDANCY`.

There are three major gateway components to set up for this configuration, as shown in the following topology diagram:

-  An HA VPN gateway in GCP with two interfaces.
-  Two AWS virtual private gateways, which connect to your HA VPN gateway.
-  An external VPN gateway resource in GCP that represents your AWS virtual private gateway. This resource provides 
   information to GCP about your AWS gateway.

![Topology diagram](https://storage.googleapis.com/gcp-community/tutorials/using-ha-vpn-with-aws/gcp-aws-ha-vpn-topology.png)

The supported AWS configuration uses a total of four tunnels:

-  Two tunnels from one AWS virtual private gateway to one interface of the HA VPN gateway.
-  Two tunnels from the other AWS virtual private gateway to the other interface of the HA VPN gateway.

## Before you begin

1.  Review information about how
    [dynamic routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#dynamic-routing)
    works in GCP.

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

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a GCP project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values used in this guide.

| Parameter description | Placeholder          | Example value                                          |
|-----------------------|----------------------|--------------------------------------------------------|
| Vendor name           | `[VENDOR_NAME]`      | AWS                                                    |
| GCP project name      | `[PROJECT_NAME]`     | `vpn-guide`                                            |
| Shared secret         | `[SHARED_SECRET_0]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| Shared secret         | `[SHARED_SECRET_1]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| Shared secret         | `[SHARED_SECRET_2]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| Shared secret         | `[SHARED_SECRET_3]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).                                   |
| VPC network name      | `[NETWORK]`          | `network-a`                                            |
| Subnet mode           | `[SUBNET_MODE]`      | `custom`                                               |
| VPN BGP routing mode  | `[BGP_ROUTING_MODE]` | `global`                                               |
| Subnet on the GCP VPC network | `[SUBNET_NAME_1]` | `subnet-a-central` |
| Subnet on the GCP VPC network | `[SUBNET_NAME_2]` | `subnet-a-west` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION1]` | `us-central1` |
| GCP region. Can be any region, but should be geographically close to on-premises gateway. | `[REGION2]` | `us-west1` |
| IP address range for the GCP VPC subnet | `[RANGE_1]` | `10.0.1.0/24` |
| IP address range for the GCP VPC subnet | `[RANGE_2]` | `10.0.2.0/24` |
| IP address range for the AWS subnet. You will use this range when creating rules for inbound traffic to GCP. | `[IP_ON_PREM_SUBNET]` | `192.168.1.0/24` |
| First external IP address for the first AWS VPN connection  | `[AWS_GW_IP_0]` | `52.52.128.71` |
| Second external IP address for the first AWS VPN connection  | `[AWS_GW_IP_1]` | `184.169.223.3` |
| First external IP address for the second AWS VPN connection  | `[AWS_GW_IP_2]` | `13.52.115.71` |
| Second external IP address for the second AWS VPN connection  | `[AWS_GW_IP_3]` | `52.9.164.225` |
| HA VPN gateway                          | `[GW_NAME]`                 | `ha-vpn-gw-a`                       |
| Cloud Router name (for dynamic routing) | `[ROUTER_NAME]`             | `router-a`                          |
| Google ASN                              | `[GOOGLE_ASN]`              | `65001`                             |
| Peer ASN                                | `[PEER_ASN]`                | `65002`                             |
| External VPN gateway resource           | `[PEER_GW_NAME]`            | `peer-gw`                           |
| First VPN tunnel                        | `[TUNNEL_NAME_IF0]`         | `tunnel-a-to-aws-connection-0-ip0`  |
| Second VPN tunnel                       | `[TUNNEL_NAME_IF1]`         | `tunnel-a-to-aws-connection-0-ip1`  |
| Third VPN tunnel                        | `[TUNNEL_NAME_IF2]`         | `tunnel-a-to-aws-connection-1-ip0`  |
| Fourth VPN tunnel                       | `[TUNNEL_NAME_IF3]`         | `tunnel-a-to-aws-connection-1-ip1`  |
| First BGP peer interface                | `[ROUTER_INTERFACE_NAME_0]` | `bgp-peer-tunnel-a-to-aws-connection-0-ip0` |
| Second BGP peer interface               | `[ROUTER_INTERFACE_NAME_1]` | `bgp-peer-tunnel-a-to-aws-connection-0-ip1` |
| Third BGP peer interface                | `[ROUTER_INTERFACE_NAME_3]` | `bgp-peer-tunnel-a-to-aws-connection-1-ip0` |
| Fourth BGP peer interface               | `[ROUTER_INTERFACE_NAME_4]` | `bgp-peer-tunnel-a-to-aws-connection-1-ip1` |
| BGP interface netmask length            | `[MASK_LENGTH]`             | `/30`                               |

## High-level configuration steps
Because HA VPN is dependent on BGP IP settings generated by AWS, you must configure Cloud VPN and AWS components in the following sequence:

1.  Create the HA VPN gateway and create a Cloud Router.
1.  Create two AWS virtual private gateways.
1.  Create two AWS site-to-site VPN connections and customer gateways, one for each AWS virtual private gateway.
1.  Download the AWS configuration files.
1.  Create four VPN tunnels on the HA VPN gateway.
1.  Configure BGP sessions on the Cloud Router using the BGP IP addresses from the downloaded AWS configuration files.

## Configure the GCP side

This section covers how to configure HA VPN.

There are two ways to create HA VPN gateways on GCP: using the GCP Console and using
[`gcloud` commands](https://cloud.google.com/sdk/gcloud). This section describes how to perform the tasks
using `gcloud` commands.

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
    
## Configure AWS VPN gateways

Create two AWS virtual private gateways, each associated with an AWS site-to-site VPN connection and a customer gateway. The
first AWS gateway has one site-to-site connection and two customer gateways. The first AWS configuration connects to 
interface 0 on the HA VPN gateway. The second AWS gateway has the same configuration and connects to interface 1 on the
HA VPN gateway.

Create all AWS components in the AWS VPC console dashboard by selecting each top-level component in the dashboard's 
navigation bar.

These instructions assume that you have created an AWS VPC for this gateway.

### Known issue

When configuring VPN tunnels to AWS, use the IKEv2 encryption protocol and select fewer transform sets on the AWS side.
Otherwise, the Cloud VPN tunnel can fail to rekey. For example, select a combination of single Phase 1 and Phase 2
encryption algorithms, integrity algorithms, and DH group numbers.

This rekeying issue is caused by a large SA payload size for the default set of AWS transform sets. This large payload size 
results in IP fragmentation of IKE packets on the AWS side, which Cloud VPN does not support.

### Create the AWS gateway and attach it to a VPC

1. In the AWS dashboard, under **Virtual Private Network**, select **Virtual Private Gateways**.
1. Click **Create Virtual Private Gateway**.
1. Enter a **Name** for the gateway.
1. Select **Custom ASN** and give the gateway an AWS ASN that doesn't conflict with the `[GOOGLE_ASN]`.
1. Click **Create Virtual Private Gateway**. Click **Close**.
1. Attach the gateway to the AWS VPC by selecting the gateway you just created, clicking **Actions, Attach to VPC**.
   1. Pull down the menu and select a VPC for this gateway and click **Yes, Attach**.
   1. Note the ID of the gateway for the steps that follow.

### Create a site-to-site connection and customer gateway

1. In the AWS dashboard, under **Virtual Private Network** select **Site-to-site VPN connections**.
1. Click **Create VPN connection**.
1. Enter a **Name** for the connection.
1. Pull down the **Virtual Private Gateway** menu and select the ID of the virtual private gateway you just created.
1. Under **Customer gateway** select `New`.
     1. For **IP address**, use the public IP address that was automatically generated for interface 0 of the
        HA VPN gateway you created earlier.
     1. For **BGP ASN**, use the value for `[GOOGLE_ASN]`.
     1. Under **Routing options** make sure that `dynamic` is selected.
     1. For **Tunnel 1** and **Tunnel 2**, specify the **Inside IP CIDR** for your AWS VPC network, 
        which is a BGP IP address from a /30 CIDR in the `169.254.0.0/16` range. 
        For example, `169.254.1.4/30`. This address must not overlap with the BGP IP address 
        for the GCP side. When you specify the pre-shared key, you must use the same pre-shared
        key for the tunnel from the HA VPN gateway side. If you specify a key, AWS doesn't autogenerate it.
     1. Click **Create VPN connection**.
     
### Create the second AWS gateway

Repeat the above steps to create a second AWS gateway, site-to-site connection, and customer gateway, 
but use the IP address generated for HA VPN gateway interface 1 instead. Use the same `[GOOGLE_ASN]`.

### Download the AWS configuration settings for each site-to-site connection

1.  As of this writing, you can download the configuration settings from your AWS virtual private gateway
    into a text file that you can reference when configuring HA VPN. You do this after you've configured 
    the HA VPN gateway and Cloud Router:
1.  On the AWS **VPC Dashboard** screen, in the left navigation bar, select **Site-to-Site VPN Connections**.
1.  Check the checkbox for the first VPN connection to download.
1.  At the top of the screen, click the middle button that reads **Download Configuration**. The **Download Configuration** 
    button provides only one configuration file, the one for the selected connection.
1.  In the pop-up dialog box, choose `vendor: generic`. There is no need to change the rest of the fields, 
    Click the **Download** button.
1.  Repeat the above steps, but choose the second VPN connection to download the file.

## Create an external VPN gateway resource

When you create a GCP external VPN gateway resource for an AWS virtual private gateway, 
you must create it with four interfaces, as as shown in the AWS topology diagram.

Note: For successful configuration, you must use the public IP addresses for the AWS 
interfaces as referenced in the two AWS configuration files you downloaded earlier.
You must also match each AWS public IP address exactly with a specific HA VPN interface. 
The instructions below describe this task in detail.

Use the following command to create the External VPN gateway resource. Replace the options as noted below:

-   For `[AWS_GW_IP_0]`, in the configuration file you downloaded for AWS Connection 0,
    under **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address 
    under **Outside IP address, Virtual private gateway**.
-   For `[AWS_GW_IP_1]`, in the configuration file you downloaded for AWS Connection 0, 
    under **IPSec tunnel #2, #3 Tunnel Interface Configuration**, use the IP address under 
    **Outside IP address, Virtual private gateway**.
-   For `[AWS_GW_IP_2]`, in the configuration file you downloaded for AWS Connection 1, 
    under **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address under 
    **Outside IP address, Virtual private gateway**.
-   For `[AWS_GW_IP_3]`, in the configuration file you downloaded for AWS Connection 1, 
    under **IPSec tunnel #2, #3 Tunnel Interface Configuration**, use the IP address under
    **Outside IP address, Virtual private gateway**.

        gcloud compute external-vpn-gateways create [PEER_GW_NAME] \
        --interfaces 0=[AWS_GW_IP_0],  \
                     1=[AWS_GW_IP_1],  \
                     2=[AWS_GW_IP_2],  \
                     3=[AWS_GW_IP_3]

The command should look similar to the following example:

    gcloud compute external-vpn-gateways create peer-gw --interfaces \   
    0=52.52.128.71,1=184.169.223.3,2=13.52.115.71,3=52.9.164.225

## Create VPN tunnels on the HA VPN gateway

Create four VPN tunnels, two for each interface, on the HA VPN gateway created previously.

In the following commands to create each tunnel, replace the options as noted in the configuration below:

-   Replace `[TUNNEL_NAME_IF0]` with the name of the tunnel to `tunnel-a-to-aws-connection-0-ip0`.
-   Replace `[TUNNEL_NAME_IF1]` with the name of the tunnel to `tunnel-a-to-aws-connection-0-ip1`.
-   Replace `[TUNNEL_NAME_IF2]` with the name of the tunnel to `tunnel-a-to-aws-connection-1-ip0`.
-   Replace `[TUNNEL_NAME_IF3]` with the name of the tunnel to `tunnel-a-to-aws-connection-1-ip1`.
-   Replace `PEER_GW_NAME]` with a name of the external peer gateway created earlier.
-   Replace `[IKE_VERS]` with 2. Although the AWS virtual private gateway supports IKEv1 or IKEv2, using IKEv2 is 
    recommended. All four tunnels created in this example use IKEv2.
-   Replace `[SHARED_SECRET_0]` through `[SHARED_SECRET_3]` with the shared secret, which must be the same as the
    shared secret used for the partner tunnel you create on your AWS virtual gateway. See
    [Generating a strong pre-shared key](https://cloud-dot-devsite.googleplex.com/vpn/docs/how-to/generating-pre-shared-key)
    for recommendations. You can also find the shared secrets in the AWS configuration files that you downloaded 
    earlier.
-   Replace `[INT_NUM_0]` with the number `0` for the first interface on the HA VPN gateway you created earlier.
-   Replace `[INT_NUM_1]` with the number `1` for the second interface on the HA VPN gateway you created earlier.

### Create the tunnel to AWS Connection 0, IP address 0

    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF0] \
       --peer-external-gateway [PEER_GW_NAME] \
       --peer-external-gateway-interface 0  \
       --region [REGION] \
       --ike-version [IKE_VERS] \
       --shared-secret [SHARED_SECRET0] \
       --router [ROUTER_NAME] \
       --vpn-gateway [GW_NAME] \
       --interface [INT_NUM_0]
     
### Create the tunnel to AWS Connection 0, IP address 1

    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF1] \
       --peer-external-gateway [PEER_GW_NAME] \
       --peer-external-gateway-interface 1 \
       --region [REGION] \
       --ike-version [IKE_VERS] \
       --shared-secret [SHARED_SECRET_1] \
       --router [ROUTER_NAME] \
       --vpn-gateway [GW_NAME] \
       --interface [INT_NUM_0]

### Create the tunnel to AWS Connection 1, IP address 0

    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF2] \
       --peer-external-gateway [PEER_GW_NAME] \
       --peer-external-gateway-interface 2 \
       --region [REGION] \
       --ike-version [IKE_VERS] \
       --shared-secret [SHARED_SECRET_2] \
       --router [ROUTER_NAME] \
       --vpn-gateway [GW_NAME] \
       --interface [INT_NUM_1]
       
### Create the tunnel to AWS Connection 1, IP address 1

    gcloud compute vpn-tunnels create [TUNNEL_NAME_IF3] \
       --peer-external-gateway [PEER_GW_NAME] \
       --peer-external-gateway-interface 3 \
       --region [REGION] \
       --ike-version [IKE_VERS] \
       --shared-secret [SHARED_SECRET_3] \
       --router [ROUTER_NAME] \
       --vpn-gateway [GW_NAME] \
       --interface [INT_NUM_1]
       
The command output should look similar to the following example:

    gcloud compute vpn-tunnels create tunnel-a-to-aws-connection-0-ip0 --peer-external-gateway \
    peer-gw --peer-external-gateway-interface 0 --region us-central1 --ike-version 2 \
    --shared-secret mysharedsecret --router router-a --vpn-gateway ha-vpn-gw-a --interface 0
    Creating VPN tunnel...done.
    NAME                              REGION       GATEWAY      VPN_INTERFACE  PEER_ADDRESS
    tunnel-a-to-aws-connection-0-ip0  us-central1  ha-vpn-gw-a  0              52.52.128.71

    gcloud compute vpn-tunnels create tunnel-a-to-aws-connection-0-ip1 --peer-external-gateway \
    peer-gw --peer-external-gateway-interface 1 --region us-central1 --ike-version 2 \
      --shared-secret mysharedsecret --router router-a --vpn-gateway ha-vpn-gw-a --interface 0
    Creating VPN tunnel...done.
    NAME                              REGION       GATEWAY      VPN_INTERFACE  PEER_ADDRESS
    tunnel-a-to-aws-connection-0-ip1  us-central1  ha-vpn-gw-a  0              184.169.223.3

    gcloud compute vpn-tunnels create tunnel-a-to-aws-connection-1-ip0 --peer-external-gateway \
    peer-gw --peer-external-gateway-interface 2 --region us-central1 --ike-version 2 \
    --shared-secret mysharedsecret --router router-a --vpn-gateway ha-vpn-gw-a --interface 1
    Creating VPN tunnel...done.
    NAME                              REGION       GATEWAY      VPN_INTERFACE  PEER_ADDRESS
    tunnel-a-to-aws-connection-1-ip0  us-central1  ha-vpn-gw-a  1              13.52.115.71

    gcloud compute vpn-tunnels create tunnel-a-to-aws-connection-1-ip1 --peer-external-gateway \
    peer-gw --peer-external-gateway-interface 3 --region us-central1 --ike-version 2 \
    --shared-secret mysharedsecret --router router-a --vpn-gateway ha-vpn-gw-a --interface 1
    Creating VPN tunnel...done.
    NAME                              REGION       GATEWAY      VPN_INTERFACE  PEER_ADDRESS
    tunnel-a-to-aws-connection-1-ip1  us-central1  ha-vpn-gw-a  1              52.9.164.225
      
## Create Cloud Router interfaces and BGP peers

This section covers configuring a BGP interface and peer on Cloud Router for each of the four VPN tunnels configured 
on the HA VPN gateway as described in the previous section.

**Caution:** Because you must use the BGP IP addresses for both GCP and AWS from the AWS configuration files you downloaded
earlier, you must specify GCP BGP IP addresses manually. For both the console and `gcloud` commands, if you don't specify 
the BGP peer IP address, it is created automatically and won't match the addresses in the file downloaded from AWS.

Create a Cloud Router BGP interface and BGP peer for each tunnel you previously configured on the HA VPN gateway interfaces.
In the following commands, replace the options as noted below:

-   Replace `[ROUTER_INTERFACE_NAME_0]` through `[ROUTER_INTERFACE_NAME_3]` with a name for the Cloud Router BGP interface.
    Using names related to the AWS tunnel names configured previously can be helpful.
-   Use a `[MASK_LENGTH]` of 30.

Each BGP session on the same Cloud Router must use a unique /30 CIDR from the 169.254.0.0/16 block.

-   Replace `[TUNNEL_NAME_IF0]` with the name of the tunnel to `aws-connection-0-ip0`.
-   Replace `[TUNNEL_NAME_IF1]` with the name of the tunnel to `aws-connection-0-ip1`.
-   Replace `[TUNNEL_NAME_IF2]` with the name of the tunnel to `aws-connection-1-ip0`.
-   Replace `[TUNNEL_NAME_IF3]` with the name of the tunnel to `aws-connection-1-ip1`.

### Assign BGP IP addresses

Follow the instructions below to assign BGP IP addresses to Cloud Router interfaces and to BGP peer interfaces.

For each VPN tunnel, get the BGP IP addresses and ASNs for both AWS and GCP from the AWS configuration files you downloaded 
earlier.

Replace the options for the GCP side as noted below:

-   For `[GOOGLE_BGP_IP_0]`, in the configuration file you downloaded for AWS Connection 0, under
    **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Customer gateway**.
-   For `[GOOGLE_BGP_IP_1]`, in the configuration file you downloaded for AWS Connection 0, under
    **IPSec tunnel #2, #3 Tunnel   Interface Configuration**, use the IP address under
    **Inside IP address, Customer gateway**.
-   For `[GOOGLE_BGP_IP_2]`, in the configuration file you downloaded for AWS Connection 1, under
    **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Customer gateway**.
-   For `[GOOGLE_BGP_IP_3]`, in the configuration file you downloaded for AWS Connection 1, under
    **IPSec tunnel #2, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Customer gateway**.
   
Replace the options for the AWS side as noted below:

-   For `[AWS_BGP_IP_0]`, in the configuration file you downloaded for AWS Connection 0, under
    **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Virtual private gateway**.
-   For `[AWS_BGP_IP_1]`, in the configuration file you downloaded for AWS Connection 0, under
    **IPSec tunnel #2, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Virtual private gateway**.
-   For `[AWS_BGP_IP_2]`, in the configuration file you downloaded for AWS Connection 1, under
    **IPSec tunnel #1, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Virtual private gateway**.
-   For `[AWS_BGP_IP_3]`, in the configuration file you downloaded for AWS Connection 1, under
    **IPSec tunnel #2, #3 Tunnel Interface Configuration**, use the IP address under
    **Inside IP address, Virtual private gateway**.
    -   `[PEER_ASN]` Use the following ASNs under BGP subsection #4:
       -   For `[TUNNEL_NAME_0]`, in the AWS configuration file for AWS Connection 0, use the
           `Virtual Private Gateway ASN` under IPSec Tunnel #1.
       -   For `[TUNNEL_NAME_1]`, in the AWS configuration file for AWS Connection 0, use the
           `Virtual Private Gateway ASN` under IPSec Tunnel #2.
       -   For `[TUNNEL_NAME_2]`, in the AWS configuration file for AWS Connection 1, use the
           `Virtual Private Gateway ASN` under IPSec Tunnel #1.
       -   For `[TUNNEL_NAME_3]`, in the AWS configuration file for AWS Connection 1, use the
           `Virtual Private Gateway ASN` under IPSec Tunnel #2.

**For the first VPN tunnel, do the following:**

1.  Add a new BGP interface to the Cloud Router. Supply a name for the interface by replacing `[ROUTER_INTERFACE_NAME_0]`.

        gcloud compute routers add-interface [ROUTER_NAME] \
           --interface-name [ROUTER_INTERFACE_NAME_0] \
           --vpn-tunnel [TUNNEL_NAME_0] \
           --ip-address [GOOGLE_BGP_IP_0] \
           --mask-length 30 \
           --region [REGION]

    The command output should look similar to the following example:

        gcloud compute routers add-interface router-a --interface-name if-tunnel-a-to-aws-connection-0-ip0 \
        --vpn-tunnel tunnel-a-to-aws-connection-0-ip0 --ip-address 169.254.1.10 --mask-length 30 \
        --region us-central1
        Updated [https://www.googleapis.com/compute/v1/projects/cpe-vpn-testing/regions/us-central1/routers/router-a].
         
1.  Add a BGP peer to the interface. Replace `[PEER_NAME]` with a name for the peer, and `[PEER_ASN]` 
    with the ASN configured for the peer VPN gateway.
   
        gcloud compute routers add-bgp-peer [ROUTER_NAME] \
         --peer-name [PEER_NAME] \
         --peer-asn [PEER_ASN] \
         --interface [ROUTER_INTERFACE_NAME_0] \
         --peer-ip-address [AWS_BGP_IP_0] \
         --region [REGION]
       
    The command output should look similar to the following example:

        gcloud compute routers add-bgp-peer router-a --peer-name bgp-peer-tunnel-a-to-aws-connection-0-ip0 \ 
        --peer-asn 65002 --interface if-tunnel-a-to-aws-connection-0-ip0 --peer-ip-address 169.254.1.9 \
        --region us-central1
        Creating peer [bgp-peer-tunnel-a-to-aws-connection-0-ip0] in router [router-a]...done.

**For the second VPN tunnel, do the following:**

1.  Add a new BGP interface to the Cloud Router. Supply a name for the interface by replacing `[ROUTER_INTERFACE_NAME_1]`.
   
        gcloud compute routers add-interface [ROUTER_NAME] \
            --interface-name [ROUTER_INTERFACE_NAME_1] \
            --vpn-tunnel [TUNNEL_NAME_1] \
            --ip-address [GOOGLE_BGP_IP_1] \
            --mask-length 30 \
            --region [REGION]
    
1.  Add a BGP peer to the interface. Replace `[PEER_NAME]` with a name for the peer, and `[PEER_ASN]` with the ASN 
    configured for the peer VPN gateway.
   
        gcloud compute routers add-bgp-peer [ROUTER_NAME] \
            --peer-name [PEER_NAME] \
            --peer-asn [PEER_ASN] \
            --interface [ROUTER_INTERFACE_NAME_1] \
            --peer-ip-address [AWS_BGP_IP_1] \
            --region [REGION]

**For the third VPN tunnel, do the following:**

1.  Add a new BGP interface to the Cloud Router. Supply a name for the interface by replacing `[ROUTER_INTERFACE_NAME_2]`.
   
        gcloud compute routers add-interface [ROUTER_NAME] \
            --interface-name [ROUTER_INTERFACE_NAME_2] \
            --vpn-tunnel [TUNNEL_NAME_2] \
            --ip-address [GOOGLE_BGP_IP_2] \
            --mask-length 30 \
            --region [REGION]
    
1.  Add a BGP peer to the interface. Replace `[PEER_NAME]` with a name for the peer, and `[PEER_ASN]` with the ASN
    configured for the peer VPN gateway.
   
        gcloud compute routers add-bgp-peer [ROUTER_NAME] \
            --peer-name [PEER_NAME] \
            --peer-asn [PEER_ASN] \
            --interface [ROUTER_INTERFACE_NAME_2] \
            --peer-ip-address [AWS_GW_IP_2] \
            --region [REGION]
  
**For the fourth VPN tunnel, do the following:**

1.  Add a new BGP interface to the Cloud Router. Supply a name for the interface by replacing `[ROUTER_INTERFACE_NAME_3]`.

        gcloud compute routers add-interface [ROUTER_NAME] \
            --interface-name [ROUTER_INTERFACE_NAME_3] \
            --vpn-tunnel [TUNNEL_NAME_3] \
            --ip-address [GOOGLE_BGP_IP_3] \
            --mask-length 30 \
            --region [REGION]
                
1.  Add a BGP peer to the interface. Replace `[PEER_NAME]` with a name for the peer, and `[PEER_ASN]` with the ASN 
    configured for the peer VPN gateway.
   
        gcloud compute routers add-bgp-peer [ROUTER_NAME] \
            --peer-name [PEER_NAME] \
            --peer-asn [PEER_ASN] \
            --interface [ROUTER_INTERFACE_NAME_3] \
            --peer-ip-address [AWS_GW_IP_3] \
            --region [REGION]
             
    The command output should look similar to the following example:
        
        gcloud compute routers add-interface router-a --interface-name if-tunnel-a-to-aws-connection-0-ip1 \
        --vpn-tunnel tunnel-a-to-aws-connection-0-ip1 --ip-address 169.254.1.6 --mask-length 30 \
        --region us-central1
        Updated [https://www.googleapis.com/compute/v1/projects/cpe-vpn-testing/regions/us-central1/routers/router-a].

        gcloud compute routers add-bgp-peer router-a --peer-name bgp-peer-tunnel-a-to-aws-connection-0-ip1 \
        --peer-asn 65002 --interface if-tunnel-a-to-aws-connection-0-ip1 --peer-ip-address 169.254.1.5 \
        --region us-central1
        Creating peer [bgp-peer-tunnel-a-to-aws-connection-0-ip1] in router [router-a]...done.

        gcloud compute routers add-interface router-a --interface-name if-tunnel-a-to-aws-connection-1-ip0 \
        --vpn-tunnel tunnel-a-to-aws-connection-1-ip0 --ip-address 169.254.1.18 --mask-length 30 \
        --region us-central1
        Updated [https://www.googleapis.com/compute/v1/projects/cpe-vpn-testing/regions/us-central1/routers/router-a].

        gcloud compute routers add-bgp-peer router-a --peer-name bgp-peer-tunnel-a-to-aws-connection-1-ip0 \
        --peer-asn 65002 --interface if-tunnel-a-to-aws-connection-1-ip0 --peer-ip-address 169.254.1.17 \
        --region us-central1
        Creating peer [bgp-peer-tunnel-a-to-aws-connection-1-ip0] in router [router-a]...done.

        gcloud compute routers add-interface router-a --interface-name if-tunnel-a-to-aws-connection-1-ip1 \
        --vpn-tunnel tunnel-a-to-aws-connection-1-ip1 --ip-address 169.254.1.14 --mask-length 30 \
        --region us-central1
        Updated [https://www.googleapis.com/compute/v1/projects/cpe-vpn-testing/regions/us-central1/routers/router-a].

        gcloud compute routers add-bgp-peer router-a --peer-name bgp-peer-tunnel-a-to-aws-connection-1-ip1 \
        --peer-asn 65002 --interface if-tunnel-a-to-aws-connection-1-ip1 --peer-ip-address 169.254.1.13 \
        --region us-central1
        Creating peer [bgp-peer-tunnel-a-to-aws-connection-1-ip1] in router [router-a]...done.

## Verify the Cloud Router configuration

There are two methods you can use to verify the Cloud Router configuration; one produces a short report and the other 
produces a long report.

The short report method lists only the GCP BGP interface name, the four BGP IP addresses (`[GOOGLE_BGP_IP_0]` through 
`[GOOGLE_BGP_IP_3]`) and the four AWS BGP IP addresses (`[AWS_GW_IP_0]` through `[AWS_GW_IP_3]`). The BGP IP addresses for 
the interfaces most recently added to Cloud Router are listed with the highest index number. Use the AWS BGP IP addresses to 
configure the connections on your AWS virtual gateway.
   
    gcloud compute routers get-status [ROUTER_NAME] \
      --region [REGION] \
      --format='flattened(result.bgpPeerStatus[].name, result.bgpPeerStatus[].ipAddress, result.bgpPeerStatus[].peerIpAddress)'

The command output should look similar to the following example:
 
    gcloud compute routers get-status router-a  --region us-central1  --format='flattened(result.bgpPeerStatus[].name, result.bgpPeerStatus[].ipAddress, result.bgpPeerStatus[].peerIpAddress)'

    result.bgpPeerStatus[0].ipAddress:     169.254.1.6
    result.bgpPeerStatus[0].name:          bgp-peer-tunnel-a-to-aws-connection-0-ip0
    result.bgpPeerStatus[0].peerIpAddress: 169.254.1.5
    result.bgpPeerStatus[1].ipAddress:     169.254.1.10
    result.bgpPeerStatus[1].name:          bgp-peer-tunnel-a-to-aws-connection-0-ip1
    result.bgpPeerStatus[1].peerIpAddress: 169.254.1.9
    result.bgpPeerStatus[2].ipAddress:     169.254.1.14
    result.bgpPeerStatus[2].name:          bgp-peer-tunnel-a-to-aws-connection-1-ip0
    result.bgpPeerStatus[2].peerIpAddress: 169.254.1.13
    result.bgpPeerStatus[3].ipAddress:     169.254.1.18
    result.bgpPeerStatus[3].name:          bgp-peer-tunnel-a-to-aws-connection-1-ip1
    result.bgpPeerStatus[3].peerIpAddress: 169.254.1.17
            
## Testing connectivity
 
1.  Create VMs on both sides of the tunnel. Make sure that you configure the VMs on a subnet that will pass traffic through 
    the VPN tunnel.

    Instructions for creating virtual machines in Compute Engine are in the
    [getting started guide](https://cloud.google.com/compute/docs/quickstarts).
    
    See [Launch a virtual machine](https://aws.amazon.com/getting-started/tutorials/launch-a-virtual-machine/)
    for AWS instructions.

1.  After you have deployed VMs on both GCP and on-premises, you can use an ICMP echo (ping) test to test network 
    connectivity through the VPN tunnel.

    1.  In the GCP Console, go to the **VM Instances** page.
    1.  Find the GCP virtual machine you created.
    1.  In the **Connect** column, click **SSH**. A Cloud Shell window opens at the VM command line.
    1.  Ping a machine that's behind the on-premises gateway:

            host@gcp-ha-vpn-test-instance:~$ ping 192.168.1.134
            PING 192.168.1.134 (192.168.1.134) 56(84) bytes of data.
            64 bytes from 192.168.1.134: icmp_seq=1 ttl=253 time=39.1 ms
            64 bytes from 192.168.1.134: icmp_seq=2 ttl=253 time=37.7 ms
            64 bytes from 192.168.1.134: icmp_seq=3 ttl=253 time=37.6 ms
            --- 192.168.1.134 ping statistics ---
            11 packets transmitted, 11 received, 0% packet loss, time 10015ms
            rtt min/avg/max/mdev = 37.673/37.890/39.145/0.417 ms
