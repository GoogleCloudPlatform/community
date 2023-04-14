---
title: Using Cloud VPN with Alibaba Cloud VPN Gateway with redundancy
description: Describes how to build IPsec VPNs between Cloud VPN on Google Cloud and Alibaba Cloud VPN Gateway with redundancy.
author: epluscloudservices
tags: VPN, interop, alibaba, alibaba cloud vpn gateway, redundancy
date_published: 2018-08-31
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

_Disclaimer: This interoperability guide is intended to be informational in
nature and shows examples only. Customers should verify this information by
testing it._

## Introduction

This guide walks you through the process of configuring
Alibaba Cloud VPN Gateway for integration with the
[Cloud VPN service](https://cloud.google.com/vpn/docs) on Google Cloud with redundancy.

If you are using this guide to configure your Alibaba Cloud VPN
Gateway implementation, be sure to substitute the correct IP
information for your environment.

For more information about Cloud VPN, see the
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).

## Terminology

Below are definitions of terms used throughout this guide.

**Google Cloud terminology**

-  **Google Cloud VPC network**—A single virtual network within a single Google Cloud project.
-  **On-premises gateway**—The VPN device on the non-Google side of the
connection, which is usually a device in a physical data center or in
another cloud provider's network. Google Cloud instructions are written from the
point of view of the Google Cloud VPC network, so "on-premises gateway" refers to the
gateway that's connecting _to_ Google Cloud.
-  **External IP address** or **Google Cloud peer address**—a single static IP address
within a Google Cloud project that exists at the edge of the Google Cloud network.
-  **Static routing**—Manually specifying the route to subnets on the Google Cloud
side and to the on-premises side of the VPN gateway.

**Alibaba terminology**

-  **Alibaba Cloud VPC**-A private network established in Alibaba Cloud. VPCs 
are logically isolated from other virtual networks in Alibaba Cloud. VPCs allow 
you to launch and use Alibaba Cloud resources in your VPC.
-  **Alibaba Cloud VSwitch**-A VSwitch is a basic network device of a VPC and 
used to connect different cloud product instances. When creating a cloud product 
instance in a VPC, you must specify the VSwitch that the instance is located.
-  **Alibaba Cloud Zone**-Zones are physical areas with independent power grids 
and networks in one region. Alibaba recommends creating different VSwitches in 
different zones to achieve disaster recovery.
-  **Alibaba Cloud VPN Gateway**-The VPN gateway is the IPsec VPN gateway created 
on the Alibaba Cloud side. One VPN gateway can have multiple VPN connections.
-  **Alibaba Cloud Customer Gateway**-The customer gateway is the VPN service 
deployed in the on-premises data center or, in this case, the Google Cloud VPN gateway. 
By creating a customer gateway, you can register the VPN information to the cloud, 
and then create a VPN connection to connect the VPN gateway and the customer gateway.
-  **Alibaba Cloud VRouter**-A VRouter is a hub in the VPC that connects all 
VSwitches in the VPC and serves as a gateway device that connects the VPC to 
other networks. VRouter routes the network traffic according to the configurations 
of route entries.
-  **Alibaba Cloud Route Entry**-A route entry specifies the next hop address for the 
network traffic destined to a CIDR block. It has two types of entries: system route 
entry and custom route entry.
-  **Alibaba Cloud Route Table**-A route table is a list of route entries in a VRouter.

## Topology

Cloud VPN supports the following topology with Alibaba Cloud VPN Gateway:

- Redundant IPsec VPN tunnel configuration using static routing.

  ![topology-redundancy](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-alibaba-redundancy/topology-redundancy.PNG)

For detailed topology information, see the following resources:

-  For basic VPN topologies, see 
[Cloud VPN overview](https://cloud.google.com/vpn/docs/concepts/overview).
-  For redundant topologies, see the
[Cloud VPN documentation on redundant and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns).

Disclaimer: At time of this writing, IPsec VPN tunnel configuration using dynamic routing between Cloud VPN and Alibaba Cloud VPN Gateway is not supported. 

## Product environment

The on-premises VPN gateway used in this guide is as follows:

-  Vendor—Alibaba Cloud
-  Service—VPN Gateway

## Before you begin

Follow the steps in this section to prepare for VPN configuration.

**Note**: This guide assumes that you have basic knowledge of the
[IPsec](https://wikipedia.org/wiki/IPsec) protocol.

### Google Cloud account and project

Make sure you have a Google Cloud account. When you begin, you must select or create a
Google Cloud project where you will build the VPN. For details, see
[Creating and Managing Projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

### Permissions

To create a Google Cloud network, a subnetwork, and other entities described in this
guide, you must be able to sign in to Google Cloud as a user who has
[Network Admin](https://cloud.google.com/compute/docs/access/iam#network_admin_role)
permissions. For details, see
[Required permissions](https://cloud.google.com/vpn/docs/how-to/creating-vpn-dynamic-routes#required_permissions)
in the article
[Creating a VPN tunnel using dynamic routing](https://cloud.google.com/vpn/docs/how-to/creating-vpn-dynamic-routes).

### IP ranges

The IP address ranges of the Google Cloud VPC and the Alibaba VPC must not overlap.

### Google Cloud compatible settings for IPSec and IKE

Configuring the vendor side of the VPN network requires you to use IPsec and IKE
settings that are compatible with the Google Cloud side of the network. The following
table lists settings and information about values compatible with Google Cloud VPN.
Use these settings for the procedures in the subsections that follow.

| Setting       | Description or value                |
|---------------|-------------------------------------|
|    IPsec Mode | ESP+Auth Tunnel mode (Site-to-Site) |
| Auth Protocol | Pre-shared Key (psk)                |
| Shared Secret | Also known as an IKE pre-shared key. Choose a strong password by following [these guidelines](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key). The shared secret is very sensitive, because it allows access into your network. |
| Start         | `Auto` (on-premises device should automatically restart the connection if it drops) |
| PFS (Perfect Forward Secrecy) | group1, group2, group5, group14, group24 |
| IKE ciphers | aes, aes192, aes256, des, 3des (For details about IKE ciphers for IKEv1 or IKEv2 supported by Google Cloud, including the additional ciphers for PFS, see [Supported IKE ciphers](https://cloud.google.com/vpn/docs/concepts/supported-ike-ciphers).) |

#### Recommended Alibaba Cloud VPN Gateway IKE proposal and policy
Below are fields you may be asked to complete for the Alibaba Cloud side configurations. 
The defaults indicated below will work with the defaults used on the Google Cloud side.

-  **Encryption algorithm**—`aes` 
-  **Integrity algorithm**—`sha1`
-  **Diffie-Hellman group**—`group2`
-  **Lifetime/SA Life Cycles**—`86400` seconds 


## Configuration overview

The Google Cloud VPN with Alibaba Cloud VPN Gateway configuration consists of the following steps.

1. Configure the Google Cloud side
1. Configure the Alibaba Cloud side

## Configure the Google Cloud side

This section covers the steps for creating a redundant Google Cloud IPsec VPN using static routing.
Both route-based Cloud VPN and policy-based Cloud VPN use static routing. For
information on how this works, see the 
[Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).

There are two ways to create VPN gateways on Google Cloud: using the Cloud Console and using the
[gcloud command-line tool](https://cloud.google.com/sdk/).
This section describes how to perform the tasks using the Cloud Console. To see
the `gcloud` commands for performing these tasks, see the
[appendix](#appendix-using-gcloud-commands).

### Initial tasks

Complete the following procedures before configuring a static Google Cloud VPN gateway 
and tunnel.

**Important:** Throughout these procedures, you assign names to entities like
the VPC network and subnet, and IP address. Each time you assign a name,
make a note of it, because you often need to use those names in later
procedures.

#### Select a Google Cloud project name

1. [Open the Cloud Console](https://console.cloud.google.com).
1. At the top of the page, select the Google Cloud project you want to use.

    **Note**: Make sure that you use the same Google Cloud project for all of the Google Cloud
    procedures in this guide.

#### Create a custom VPC network and subnet

1. In the Cloud Console,
[go to the VPC Networks page](https://pantheon.corp.google.com/networking/networks/list).
1. Click **Create VPC network**.
1. For **Name**, enter a name such as `vpn-vendor-test-network`. Remember
this name for later.
1. Under **Subnets, Subnet creation mode**, select the **Custom** tab and then populate the following fields:
+ **Name**—The name for the subnet, such as `vpn-subnet-1`.
+ **Region**—The region that is geographically closest to the
    on-premises gateway, such as  `us-east1`.
+ **IP address range**—A range such as `172.16.1.0/24`.
1. In the **New subnet** window, click **Done**.
1. Click **Create**. You're returned to the **VPC networks** page, where it
takes about a minute for this network and its subnet to appear.

#### Create the Google Cloud external IP addresses for Cloud VPN gateways

Two Cloud VPN gateways on the Google Cloud side are needed for redundancy.

The following procedure configures one external IP address for the first Cloud VPN gateway. 

Repeat the procedure to create a second external IP address for the second Cloud VPN gateway.

1.  In the Cloud Console,
[go to the External IP addresses page](https://pantheon.corp.google.com/networking/addresses/list).

1. Click **Reserve Static Address**.
1. Populate the following fields for the Cloud VPN address:
-  **Name**—The name of the address, such as `vpn-test-static-ip-1`.
    Remember the name for later.
-  **Region**—The region where you want to locate the VPN gateway.
    Normally, this is the region that contains the instances you want to
    reach.
1. Click **Reserve**. You are returned to the **External IP addresses** page.
After a moment, the page displays the static external IP address that you
have created.

1. Make a note of the IP address that is created so that you can use it to
configure the VPN gateways later.

1. Repeat the steps using a different name, such as `vpn-test-static-ip-2`.

### Configure route-based IPSec VPN using static routing

#### Configure the VPN gateways

Two VPN gateways are needed for redundancy.

The following procedure configures the first VPN gateway with two tunnels.

Repeat the procedure to configure the second VPN gateway with two tunnels.

1. In the Cloud Console, 
[go to the VPN page](https://console.cloud.google.com/networking/vpn/list).
1. Click **Create VPN connection**.
1. Populate the following fields for the gateway:
    -  **Name**—The name of the VPN gateway. This name is displayed in the
    console and used in by the gcloud tool to reference the gateway. Use a
    name like `vpn-test-alibaba-gw-1`, where `alibaba` is a
    string that identifies the vendor.
    -  **Network**—The VPC network that you created previously (for
    example, `vpn-vendor-test-network`) that contains the instances that the
    VPN gateway will serve.
    -  **Region**—The region where you want to locate the VPN gateway.
    Normally, this is the region that contains the instances you want to reach.
    -  **IP address**—Select the 
    [static external IP address](#create-the-gcp-external-ip-address)
    (for example, `vpn-test-static-ip-1`) that you created for this gateway
    in the previous section.
1. Populate the fields for the first tunnel:
    -  **Name**—The name of the VPN tunnel, such as `vpn-gw-1-tunnel1`.
    -  **Remote peer IP address**—The public external IP address of the
    on-premises VPN gateway.
    -  **IKE version**—`IKEv2` 
    -  **Shared secret**—A character string used in establishing encryption
    for the tunnel. You must enter the same shared secret into both VPN
    gateways. For more information, see
    [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).
1. Repeat previous the step for the second tunnel and use a different name, such as `vpn-gw-1-tunnel2`.
1. Under **Routing options**, select the **Route based** or **Policy based** tab.
1. Populate the following fields:
    -  **Remote network IP range**—The range or ranges of the on-premises network,
   which is the network on the other side of the tunnel from the Cloud VPN gateway
   you are currently configuring. 
    -  **Local subnetworks**—The local subnet or subnets of the Cloud VPN's VPC. 
1. Click **Create**. The Google Cloud VPN gateway is initiated, and the tunnel is initiated.
This procedure automatically creates a static route to the on-premises subnet as
well as forwarding rules for UDP ports 500 and 4500 and for ESP traffic. The VPN
gateways will not connect until you've configured the on-premises gateway and
created firewall rules in Google Cloud to allow traffic through the tunnel between the
Cloud VPN  gateway and the on-premises gateway.
1. Repeat all steps above to create the second VPN gateway with two tunnels.

#### Configure Custom Static Routes with Route Prioritization (Optional)

While configuring routing options for the VPN gateways in the prior section, Google Cloud automatically creates static routes for the remote network IP range with unique tunnels as the next hop. By default, each dynamically created static route will have the same route priority resulting in equal cost pathing across each pair of tunnels on each VPN gateway.

To forward traffic across a specific tunnel on each VPN gateway, manually create static routes with different priorities.

Set one tunnel to be primary and other tunnel to be secondary by using a lower numeric value on the primary tunnel. 

For example, a route with a priority value of 100 will have higher priority than one with a priority value of 200.

1. In the Cloud Console, [go to the Routes page](https://console.cloud.google.com/networking/routes).
2. Click **Create route**.
3. Specify a **Name** and a **Description** for the route.
4. Select an existing **Network** where the route will apply.
5. Specify a **Destination IP range** to define the destination of the route.
6. Specify a **Priority** for the route. A priority is only used to to determine routing order if routes have equivalent destinations. 
7. Leave the field blank to make the route applicable to all instances in the network. To make the route applicable only to select instances with matching network tags, specify those in the Instance tags field.
8. Select a **Next hop** for the route. **VPN tunnel** allows you to select an existing Cloud VPN tunnel as a next hop. 
9. Click **Create**
10. Repeat the steps for remaining VPN tunnels.

**Important**: You cannot edit or update a route after you create it. To modify a custom static route, you must delete it and create a replacement.

### Configure firewall rules

Next, you configure Google Cloud firewall rules to allow inbound traffic from the
on-premises network subnets. You must also configure the on-premises network
firewall to allow inbound traffic from your VPC subnet prefixes.

1. In the Cloud Console,
[go to the firewall rules page](https://console.cloud.google.com/networking/firewalls).
1. Click **Create firewall rule**.
1. Populate the following fields:

    - **Name**—A name such as `vpnrule1`.
    - **Network**—The name of the VPC network that you created previously (for example, `vpn-vendor-test-network`).
    - **Target tags:**—All instances in the network  
    - **Source filter**—A filter to apply your rule to specific sources of traffic. In this case, choose source IP ranges.
    - **Source IP ranges**—The on-premises IP ranges to accept from the on-premises VPN gateway.
    - **Allowed protocols and ports**—The string `tcp;udp;icmp`.

1. Click **Create**.

## Configure the Alibaba Cloud side

This section includes sample tasks that describe how to configure the
on-premises side of the VPN gateway configuration using Alibaba Cloud VPN Gateway.

### Create an Alibaba Cloud VPC

This section covers the steps of creating an Alibaba Cloud VPC.

1. Log in to the Alibaba Management Console.
    - Go to **Products > Virtual Private Cloud**.
1. Create a new VPC.
    - Select a **Region**  (for example, US (Silicon Valley)).
    - Click the **Create VPC** button.
1. Configure the following VPC settings:
    - **VPC Name**—Enter the name of the VPC (for example, `alibaba-vpc`).
    - **Destination CIDR Block**—Specify the IP address range for the VPC in the form of a Classless Inter-Domain Routing (CIDR) block (for example, `192.168.0.0/16`).


### Create an Alibaba Cloud VSwitch

This section covers the steps of configuring the Alibaba Cloud VSwitch.

1. Within the same VPC configuration window pane, configure the following VSwitch settings:
    - **VSwitch Name**—Enter the name of the VSwitch (for example, `alibaba-vswitch`).
    - **Zone**—Select a zone for the VSwitch (for example, `USA West 1 Zone A`).
    - **Destination CIDR Block**—Specify a subnet from the VPC’s CIDR IP address range (for example, `192.168.1.0/24`).
1. Click **OK** followed by the **Complete** button.
1. Verify the VPC and VSwitch status indicate “Available”.

### Create Alibaba Cloud VPN gateways

This section covers the steps of configuring the Alibaba Cloud VPN Gateway.

The steps below will configure a single Alibaba Cloud VPN Gateway.

Repeat these steps to get a second Alibaba Cloud VPN Gateway.

1. Go to **Products > Virtual Private Cloud > VPN Gateways**
1. Click **Create VPN Gateway**
1. Configure the following settings:
    - **Region**—Select a region (for example, `US (Silicon Valley)`).
    - **Name**—Give the VPN Gateway a name (for example, `alibaba-vpn-gateway-1`).
    - **VPC**—Select the VPC (for example, `alibaba-vpc`).
    - Keep all other values as default.
1. Click **Buy Now**  
    - Check the **VPN Gateway Agreement of Service** checkbox and click the **Activate** button.
    - Click **Console** and navigate back to **Products > Virtual Private Cloud > VPN Gateways** to verify the status and take note of the IP address, since this will be used for Google-side configuration. The VPN Gateway will take several minutes to come up and obtain a public IP address. 
1. Repeat these steps to create the second Alibaba Cloud VPN Gateway, using a different name, such as `alibaba-vpn-gateway-2`.

### Configure Alibaba Cloud customer gateways

1. Log in to the Alibaba Cloud console.
1. Go to **Products > Virtual Private Cloud > Customer Gateways**.
1. Select **Region** (for example, `US (Silicon Valley)`) and then click **Create Customer Gateway**.
1. Complete the following settings:
    - **Name**—Provide a name to the customer gateway (for example, `gcp-customer-gateway-1`).
    - **IP Address**—Provide the Public IP address of Google Cloud customer gateway (for example, `35.197.191.225`).
    - Click **OK**
1. Repeat this procedure to create a second customer gateway, using a different name, such as `gcp-customer-gateway-2`
and provide the IP address of the second Google Cloud customer gateway.

### Configure Alibaba Cloud IPSec connections

This section covers the steps of creating an Alibaba IPSec connection with the Google Cloud gateway.  

1. Go to **Products > Virtual Private Cloud > IPSec Connections**.
1. Click **Create IPsec Connection**.
1. Complete the following settings:
    - **Name**—Provide a name to the VPN connection (for example, `ali-gw-1-tunnel-1`).
    - **VPN Gateway**—Choose the VPN gateway in the dropdown which was created earlier (for example, `alibaba-vpn-gateway-1`).
    - **Customer Gateway**—Choose the customer gateway in the dropdown which was created earlier (for example, `gcp-customer-gateway-1`).
    - **Local network**—Provide the local subnet for Alibaba (for example, `192.168.1.0/24`).
    - **Remote Network**—Provide the remote subnet for Google Cloud (for example, `172.16.1.0/24`).
    - **Effective Immediately**—Yes
1. Click **Advanced Configuration**.
1. Complete the following settings:
    - **Pre-shared Key**—Enter the pre-shared key used on the Google Cloud side. IPsec tunneling requires that both agents use the same key. 
    - **Version**—ikev2
    - Leave all other options default.
1. Click **OK**
1. Verify the IPSec Tunnel is established. It may take a few minutes.

The tunnel status should eventually indicate Phase 2 of IKE Tunnel 
Negotiation Succeeded. And from the Google Cloud side, the VPN tunnel status should transition from Negotiation failure to Established. You may need to refresh the Cloud Console page until the Established state appears. If the tunnel status in the Alibaba Cloud management console does not reach Succeeded or the tunnel status on the Cloud Console does not reach Established, refer to the Troubleshooting section of this document.

Repeat to create the remaining three tunnels. When you are done, you should have something similar to the following:

**Alibaba tunnel name and gateway mappings**

| VPN Gateway name      | Instance ID/Name  | Peer IP address                                   |
|-----------------------|-------------------|---------------------------------------------------|
| alibaba-vpn-gateway-1 | ali-gw-1-tunnel-1 | public IP address of 1st Google Cloud VPN Gateway |
| alibaba-vpn-gateway-1 | ali-gw-1-tunnel-2 | public IP address of 2nd Google Cloud VPN Gateway |
| alibaba-vpn-gateway-2 | ali-gw-2-tunnel-1 | public IP address of 1st Google Cloud VPN Gateway |
| alibaba-vpn-gateway-2 | ali-gw-2-tunnel-2 | public IP address of 2nd Google Cloud VPN Gateway |


### Configure an Alibaba Cloud static route entry

Finally, in order to route traffic from the Alibaba Cloud VPC to Google Cloud VPC via the IPsec tunnel, you need to add a custom route entry for the VSwitch subnet.

1. Add a static route entry.
    - Go to **Products > Virtual Private Cloud > VPCs > Route Tables > Instance ID/Name of route table**.
1. Click **Add Route Entry**.
1. Configure the following route settings:
    - **Destination CIDR Block** – The destination Subnet (e.g., 172.16.1.0/24) 
    - **Next Hop Type** – VPN Gateway
    - **VPN Gateway** – The VPN Gateway created earlier (e.g., alibaba-vpn-gateway)
1. Click **OK**.

When adding a static route entry, only one VPN Gateway can be selected. Multiple static route entries to the same prefix with different VPN Gateways are not supported.

When forwarding egress traffic, the selected VPN Gateway performs equal cost load balancing across both its tunnels. Tunnel prioritization is not supported. In other words, both tunnels are always utilized for forwarding egress traffic on the selected VPN Gateway.

### Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. 
For either side, make sure that the subnet that a machine or virtual machine 
is located in is being forwarded through the VPN tunnel.

First, create virtual machines (VMs) on both sides of the tunnel. Make sure 
that you configure the VMs on a subnet that will pass traffic through the VPN 
tunnel.

-  Instructions for creating virtual machines in Compute Engine are located
in the [Getting started guide](https://cloud.google.com/compute/docs/quickstart).
-  Instructions for creating virtual machines in Alibaba Cloud Elastic Compute Service (ECS)
are located at [ECS operation instructions](https://www.alibabacloud.com/help/doc-detail/25430.htm).
(When creating an ECS instance, select **Pay-as-You-Go** for the billing method unless you
intend to place the instance under the **Subscription** billing method.)

After VMs have been deployed on both the Google Cloud and Alibaba Cloud platforms, 
you can use an ICMP echo (ping) test to test network connectivity
through the VPN tunnel.

On the Google Cloud side, use the following instructions to test the connection to a
machine that's behind the on-premises gateway:

1. In the Cloud Console,
[go to the VM Instances page](https://console.cloud.google.com/compute?).
1. Find the Google Cloud virtual machine you created.
1. In the **Connect** column, click **SSH**. A browser window opens at the VM
command line.
1. Ping a machine that's behind the on-premises gateway.


## Troubleshooting IPsec on Alibaba Cloud VPN Gateway

For troubleshooting information, see the [Alibaba IPSec Connections Troubleshooting Guide](https://partners-intl.aliyun.com/help/doc-detail/65802.htm?spm=a2c63.o282931.b99.27.4973a641RT0hOX) and [View IPSec Connections Logs](https://www.alibabacloud.com/help/doc-detail/65288.htm?spm=5176.11182206.0.0.3c5b4c8f4JJqGH#h2-view-ipsec-connection-logs5).


## Reference documentation

You can refer to the following Alibaba Cloud VPN Gateway documentation and
Cloud VPN documentation for additional information about both products.

### Google Cloud documentation

To learn more about Google Cloud networking, see the following documents:

-  [VPC networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Creating route-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-route-based-vpns)
-  [Creating policy-based VPNs](https://cloud.google.com/vpn/docs/how-to/creating-policy-based-vpns)
-  [Advanced Cloud VPN configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Redundant and high-throughput VPNs](https://cloud.google.com/vpn/docs/concepts/redundant-vpns)
-  [Static routes overview](https://cloud.google.com/vpc/docs/routes#routeselection)
-  [Networks and tunnel routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)

### Alibaba Cloud VPN Gateway documentation

For more product information on Alibaba Cloud VPN Gateway, see the following
Alibaba Cloud VPN Gateway feature configuration guides and datasheets:

-  [Alibaba VPN Gateway](https://www.alibabacloud.com/product/vpn-gateway)
-  [Document Center: VPN Gateway](https://partners-intl.aliyun.com/help/product/65234.htm?spm=a2c63.m28257.a1.26.25cb4fca3Qi2Bv)
-  [Configure a Site-to-Site VPN](https://partners-intl.aliyun.com/help/doc-detail/65072.htm?spm=a2c63.l28256.a3.7.13b5e889MWMzAE)
-  [Alibaba Cloud Region and Endpoint Names](https://www.alibabacloud.com/help/doc-detail/31837.htm)


## Appendix: Using gcloud commands

The instructions in this guide focus on using the Cloud Console. However, you can
perform many of the tasks for the GPC side of the VPN configuration by using the
[gcloud command-line tool](https://cloud.google.com/sdk/gcloud/). Using `gcloud`
commands can be faster and more convenient if you're comfortable with using a
command-line interface.

### Running gcloud commands

You can run `gcloud` commands on your local computer by installing the [Cloud
SDK](https://cloud.google.com/sdk/). Alternatively, you can run `gcloud`
commands in [Cloud Shell](https://cloud.google.com/shell/), a browser-based
command line. If you use Cloud Shell, you don't need to install the SDK on your
own computer, and you don't need to set up authentication.

**Note**: The `gcloud` commands presented in this guide assume you are working
in a Linux environment. (Cloud Shell is a Linux environment.)

### Configuration parameters and values

The `gcloud` commands in this guide include parameters whose value you must
provide. For example, a command might include a Google Cloud project name or a region or
other parameters whose values are unique to your context. The following table
lists the parameters and gives examples of the values. The section that follows
the table describes how to set Linux environment variables to hold the values
you need for these parameters.

| Parameter description | Placeholder                    | Example value         |
|-----------------------|--------------------------------|-----------------------|
| Vendor name           | `[VENDOR_NAME]`      | (Your product's vendor name. This value should have no spaces or punctuation in it other than underscores or hyphens, because it will be used as part of the names for Google Cloud entities.) |
| Google Cloud project name      | `[PROJECT_NAME]`     | `vpn-guide` |
| Shared secret         | `[SHARED_SECRET]`    | See [Generating a strong pre-shared key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key). |
| VPC network name      | `[VPC_NETWORK_NAME]` | `vpn-vendor-test-network` |
| Subnet on the Google Cloud VPC network (for example, `vpn-vendor-test-network`) | `[VPC_SUBNET_NAME]` | `vpn-subnet-1` |
| Google Cloud region. Can be any region, but it should be geographically close to the on-premises gateway. | `[REGION]` | `us-east1` |
| Pre-existing external static IP address that you configure for the internet side of the Cloud VPN gateway. | `[STATIC_EXTERNAL_IP]`| `vpn-test-static-ip` |
| IP address range for the Google Cloud VPC subnet (`vpn-subnet-1`) | `[SUBNET_IP]` | `172.16.100.0/24` |
| IP address range for the on-premises subnet. You will use this range when creating rules for inbound traffic to Google Cloud. | `[IP_ON_PREM_SUBNET]` | `10.0.0.0/8` |
| External static IP address for the internet interface of [vendor name][product-name] | `[CUST_GW_EXT_IP]` |`199.203.248.181` |
| The name for the first Google Cloud VPN gateway. | `[VPN_GATEWAY_1]` | `vpn-test-alibaba-gw-1`, where `alibaba` is the `alibaba` string |
| The name for the first VPN tunnel for `vpn-test-[VENDOR_NAME]-gw-1` | `[VPN_TUNNEL_1]` | `vpn-test-tunnel1` |
| The name of a firewall rule that allows traffic between the on-premises network and Google Cloud VPC networks | `[VPN_RULE]` | `vpnrule1` |
| The name for the [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create) used to forward traffic to the on-premises network. You need this value only if you are creating a VPN using a static route. | `[ROUTE_NAME]` | `vpn-static-route` |
| The name for the forwarding rule for the [ESP protocol](https://wikipedia.org/wiki/IPsec#Encapsulating_Security_Payload) |  `[FWD_RULE_ESP]` | `fr-esp` |
| The name for the forwarding rule for the [UDP protocol](https://wikipedia.org/wiki/User_Datagram_Protocol), port 500 | `[FWD_RULE_UDP_500]` | `fr-udp500` |
| The name for the forwarding rule for the UDP protocol, port 4500 | `[FWD_RULE_UDP_4500]` | `fr-udp4500` |

### Setting environment variables for gcloud command parameters

To make it easier to run `gcloud` commands that contain parameters, you can
create environment variables to hold the values you need, such as your project
name, the names of subnets and forwarding rules, and so on. The `gcloud`
commands presented in this section reference variables that contain your
values.

To set the environment variables, run the following commands at the command line
_before_ you run `gcloud` commands, substituting your own values for all the
placeholders in square brackets, such as `[PROJECT_NAME]`, `[VPC_NETWORK_NAME]`,
and `[SUBNET_IP]`. If you don't know what values to use for the placeholders,
use the example values from the parameters table in the preceding section.

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


### Configuring route-based IPsec VPN using static routing

This section describes how to use the `gcloud` command-line tool to configure
IPsec VPN with static routing. To perform the same task using the GPC Console,
see
[Configuring IPsec VPN using static routing](#configuring-route-based-ipsec-vpn-using-static-routing)
earlier in this guide.

The procedure suggests creating a custom VPC network. This is preferred over
using an auto-created network. For more information, see
[Networks and Tunnel Routing](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#network-types)
in the Cloud VPN documentation.

**Note**: Before you run the `gcloud` commands in this section, make sure that
you've set the variables as described earlier under
[Setting environment variables for gcloud command parameters](#setting-environment-variables-for-gcloud-command-parameters).

1. Create a custom VPC network. Make sure there is no conflict with your
local network IP address range. Note the following:

   -  For `[RANGE]`, substitute an appropriate CIDR range, such as `172.16.100.0/24`.

            gcloud compute networks create $VPC_NETWORK_NAME \
            --project $PROJECT_NAME \
            --subnet-mode custom

            gcloud compute networks subnets create $VPC_SUBNET_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION \
            --range [RANGE]

1. Create a VPN gateway in the region you are using. Normally, this is the
region that contains the instances you want to reach.

        gcloud compute target-vpn-gateways create $VPN_GATEWAY_1 \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --region $REGION

This step creates an unconfigured VPN gateway in your Google Cloud VPC network.

1. Reserve a static IP address in the VPC network and region where you
created the VPN gateway. Make a note of the address that is created for use
in future steps.

        gcloud compute addresses create $STATIC_EXTERNAL_IP \
            --project $PROJECT_NAME \
            --region $REGION
    
1. Create three forwarding rules, one each to forward ESP, IKE, and NAT-T
traffic to the Cloud VPN gateway. Note the following:

   -  For `[STATIC_IP_ADDRESS]`, use the static IP address that you reserved in the previous step.

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

1. Create a VPN tunnel on the Cloud VPN Gateway that points to the external
IP address of your on-premises VPN gateway. Note the following:

-  Set the IKE version. The following command sets the IKE version to
    2, which is the default, preferred IKE version. If you need to set it to
    1, use `--ike-version 1`.
-  For `[SHARED_SECRET]`, supply the shared secret.  For details, see
    [Generating a Strong Pre-shared Key](https://cloud.google.com/vpn/docs/how-to/generating-pre-shared-key).
-  For `[LOCAL_TRAFFIC_SELECTOR_IP]`, supply an IP address range, like
    `172.16.100.0/24`,  that will be accessed on the Google Cloud side of the  tunnel,
    as described in
    [Traffic selectors](https://cloud.google.com/vpn/docs/concepts/choosing-networks-routing#static-routing-networks)
    in the Google Cloud VPN networking documentation.

        gcloud compute vpn-tunnels create $VPN_TUNNEL_1 \
            --project $PROJECT_NAME \
            --peer-address $CUST_GW_EXT_IP \
            --region $REGION \
            --ike-version 2 \
            --shared-secret [SHARED_SECRET] \
            --target-vpn-gateway $VPN_GATEWAY_1 \
            --local-traffic-selector [LOCAL_TRAFFIC_SELECTOR_IP]
   

    After you run this command, resources are allocated for this VPN tunnel, but it
    is not yet passing traffic.

1. Use a [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create) to forward traffic to the destination range of IP addresses in your on-premises network. The region must be the same region as for the VPN tunnel.

        gcloud compute routes create $ROUTE_NAME \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --next-hop-vpn-tunnel $VPN_TUNNEL_1 \
            --next-hop-vpn-tunnel-region $REGION \
            --destination-range $IP_ON_PREM_SUBNET
    

1. If you want to pass traffic from multiple subnets through the VPN tunnel,
repeat the previous step to forward the IP address of each of the subnets.

1. Create firewall rules to allow traffic between the on-premises network and
Google Cloud VPC networks.

        gcloud compute firewall-rules create $VPN_RULE \
            --project $PROJECT_NAME \
            --network $VPC_NETWORK_NAME \
            --allow tcp,udp,icmp \
            --source-ranges $IP_ON_PREM_SUBNET
   
