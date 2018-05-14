# Google Cloud VPN Interop Guide

Using Cloud VPN with <vendor name><product name>Learn how to build site-to-site IPSEC VPN between Cloud VPN and `<vendor name><product name>`.

<NOTE: Options or instructions are shown in angle brackets throughout this template. Change or remove these items as needed.>

<Place vendor logo or equipment photo here>

<Put trademark statements here>: <vendor terminology> and the <vendor> logo are trademarks of <vendor company name> or its affiliates in the United States and/or other countries.

_Disclaimer: This interoperability guide is intended to be informational in nature and shows examples only. Customers should verify this information by testing it. _ 

Author: <author name and email address>  

# Contents

- [Google Cloud VPN Interop Guide](#google-cloud-vpn-interop-guide)
- [Contents](#contents)
- [Introduction](#introduction)
- [Product environment](#product-environment)
- [Before you begin](#before-you-begin)
   - [Terminology](#terminology)
   - [Configuration overview](#configuration-overview)
      - [GCP-side configuration](#gcp-side-configuration)
      - [<vendor name><vendor product>-side configuration](#vendor-namevendor-product-side-configuration)
      - [](#)
      - [Final steps](#final-steps)
   - [Licenses and modules <if required>](#licenses-and-modules-if-required)
   - [Configuration parameters and values](#configuration-parameters-and-values)
      - [GCP parameter reference](#gcp-parameter-reference)
      - [IPsec parameters](#ipsec-parameters)
- [GCP-side configuration](#gcp-side-configuration)
   - [IPsec VPN using dynamic routing with the BGP protocol](#ipsec-vpn-using-dynamic-routing-with-the-bgp-protocol)
      - [Using the Cloud Platform Console](#using-the-cloud-platform-console)
      - [Using the gcloud command line tool](#using-the-gcloud-command-line-tool)
   - [IPsec VPN using "route based" static routing](#ipsec-vpn-using-"route-based"-static-routing)
      - [Using the Google Cloud Platform Console](#using-the-google-cloud-platform-console)
      - [Using the gcloud command-line tool](#using-the-gcloud-command-line-tool)
- [<Vendor name><vendor product> configuration](#vendor-namevendor-product-configuration)
   - [Creating the base network configuration](#creating-the-base-network-configuration)
   - [Creating the base VPN gateway configuration](#creating-the-base-vpn-gateway-configuration)
      - [Configure the IKEv2 proposal and policy](#configure-the-ikev2-proposal-and-policy)
      - [Configure the IKEv2 keyring](#configure-the-ikev2-keyring)
      - [Configure the IKEv2 profile](#configure-the-ikev2-profile)
      - [Configure the IPsec Security Association (SA)](#configure-the-ipsec-security-association-sa)
      - [Configure the IPsec transform set](#configure-the-ipsec-transform-set)
      - [Configure the IPsec profile](#configure-the-ipsec-profile)
      - [Configure the IPsec static virtual tunnel interface (SVTI)](#configure-the-ipsec-static-virtual-tunnel-interface-svti)
   - [Configuring the dynamic routing protocol (preferred)](#configuring-the-dynamic-routing-protocol-preferred)
   - [Configuring static routing](#configuring-static-routing)
   - [Saving the configuration](#saving-the-configuration)
   - [Testing the configuration](#testing-the-configuration)
- [Advanced VPN configurations](#advanced-vpn-configurations)
   - [Configuring VPN redundancy](#configuring-vpn-redundancy)
      - [Configuring <product name> Dynamic route priority settings](#configuring-product-name-dynamic-route-priority-settings)
      - [Configuring <product name> Static route metrics](#configuring-product-name-static-route-metrics)
      - [Configuring GCP BGP route priority (optional)](#configuring-gcp-bgp-route-priority-optional)
      - [Configuring GCP Static route metrics (optional)](#configuring-gcp-static-route-metrics-optional)
      - [Testing VPN Redundancy on <vendor name><device name>](#testing-vpn-redundancy-on-vendor-namedevice-name)
   - [Getting higher throughput](#getting-higher-throughput)
      - [Configuring <vendor name><product name>](#configuring-vendor-nameproduct-name)
      - [Configuring GCP](#configuring-gcp)
      - [Testing the higher-throughput configuration](#testing-the-higher-throughput-configuration)
- [Troubleshooting IPsec on <vendor name><product name>](#troubleshooting-ipsec-on-vendor-nameproduct-name)
- [Reference documentation](#reference-documentation)
   - [<vendor name><product name> documentation](#vendor-nameproduct-name-documentation)
   - [GCP documentation](#gcp-documentation)

# Introduction

This guide walks you through the process of configuring the `<vendor name><product name>` for integration with the [Google Cloud VPN service](https://cloud.google.com/vpn/docs).  This information is provided as an example only. Please note that this guide is not meant to be a comprehensive overview of IPsec and assumes basic familiarity with the IPsec protocol.  
  
If you are using this guide to configure your <product name> implementation, be sure to substitute the correct IP information for your environment.

For more information about Cloud VPN see [the Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview).  
  
Topology  
This guide describes two Cloud VPN topologies in the preferred order:   
<If needed, describe how the topology operates here.>

-  A site-to-site IPsec VPN tunnel configuration using Google Cloud Router and providing dynamic routing with the BGP protocol.
-  A site-to-site Route based IPsec VPN tunnel configuration using static routes.

The topology of each VPN topology can be configured with no redundancy, or, as an advanced solution, with redundancy on the GCP side, the on-premises side, or both. "On-premises" refers to the <vendor name><product name> side of the topology diagram.

![image]('googlecloudvpn--9gird3c1ka5.jpg')

Cloud VPN to <Example: `<vendor name><product name>` VPN solution without redundancy 

![image]('googlecloudvpn--am22bc08xg.jpg')

Cloud VPN to <Example: `<vendor name><product name>` VPN solution with redundant Cloud VPN gateways 

![image]('googlecloudvpn-lq8w2zqzrgd.jpg')

Cloud VPN to <Example: `<vendor name><product name>` VPN solution with redundant   
on premises gateways 

![image]('googlecloudvpn-n88re2fjlu.jpg')

Cloud VPN to <Example: `<vendor name><product name>` VPN solution with redundant   
GCP and redundant on-premises gateways 

# Product environment

The `<vendor name><product name>` equipment used in this guide is as follows:  

-  Vendor: <vendor name>
-  Model: <model name>
-  Software Release: <full software release name>

<This section is optional, as some vendors might only have one platform>  
Although the steps in this guide use  <model name>, this guide also applies to the following <product name> platforms:

-  <vendor model 1>
-  <vendor model 2>
-  <vendor model 3>

# Before you begin

Follow the steps in this section to prepare for VPN configuration.

## Terminology

Below are definitions of common terms used throughout this guide.

<Below is some sample terminology. Add additional terminology that needs explanation in this section.>

-  **GCP VPC network** – A single virtual network within a single GCP project.
-  **On-premises gateway, tunnel endpoint, or IP addresses** –The VPN device on the non-GCP side of the connection, which is usually a device in a physical data center or other cloud provider's network. GCP instructions are written from the point of view of the GCP VPC network, so the "on-premises gateway" is the gateway connecting to GCP.
-  **GCP peer address **–  A single static IP address within a GCP project that exists at the edge of the GCP network. Also known as a Cloud IP address.
-  **Static routing** – Manually specifying the route to subnets on the GCP-side and the on-premises side of the VPN gateway.
-  **Dynamic routing** – GCP Dynamic routing for VPN using the BGP protocol
-  `<vendor name><product name>` term
-  `<vendor name><product name>` term

## Configuration overview

The following is a high level overview of the configuration process covered in this guide:  
<Modify this sample overview and remove the steps that don't apply to the configuration for this VPN device or service.>

### GCP-side configuration

1. Configure either a GCP IPsec VPN that uses dynamic routing or that uses static routing.
1. For dynamic routing (preferred):
   1. Configure a custom GCP network and subnet.
   1. Create an external IP address for the VPN gateway.
   1. Configure the VPN gateway, at least one tunnel, and Cloud Router.
   1. If using the `gcloud` command line, configure forwarding rules to the on-premises gateway
   1. Configure firewall rules.

1. For static routing repeat the steps above except, in the tunnel configuration panel under Routing options, choose **route based** and configure the Remote network IP ranges for the on-premises network.

### <vendor name><vendor product>-side configuration

1. Configure the base <vendor name><vendor product> network configuration to establish L3 connectivity.
1. Configure the <vendor name><vendor product> VPN Gateway.
1. Set up the Base <vendor name><vendor product> VPN configuration <which may include the following steps>:
   1. Configure IKEv2 Proposal and Policy
   1. Configure IKEv2 keyring
   1. Configure IKEv2 profile
   1. Configure IPsec Security Association (SA)
   1. Configure IPsec transform set
   1. Configure IPsec profile
   1. Configure IPsec Static Virtual Tunnel Interface (SVTI)
   1. Configure the dynamic routing protocol (preferred) or static routing protocol to route traffic into the IPsec tunnel

### 

### Final steps

1. Test the IPsec connection through the VPN tunnel(s).
1. Set up Advanced VPN configurations.

## Licenses and modules <if required>

<This section is optional, as some VPN vendors can be open source or cloud providers that don't require licensing>

The first step in configuring your `<vendor name><product name>` for use with the Google Cloud VPN service is to make sure that the following licenses are available:  
  
<Below are some examples. Replace with information that applies to the product.>

-  Advanced Enterprise Services(SLASR1-AES) or Advanced IP Services Technology Package License (SLASR1-AIS  
-  IPsec RTU license (FLASR1-IPsec-RTU)
-  Encryption HW module (ASR1002HX-IPsecHW(=) and ASR1001HX-IPsecW(=)) and Tiered Crypto throughput license which applies to ASR1002-HX and ASR1001-HX chassis only.  
  
For a detailed <vendor name><product name> license information, refer to the  
<Vendor Guide link>.

## Configuration parameters and values

The configuration samples in this guide include numerous value substitutions provided only as examples.  When following this guide, replace any of the following references with the appropriate values for your environment:

-  Account information
-  Project names
-  Device IDs
-  IP addresses
-  Shared secrets
-  Keys

### GCP parameter reference

The following parameters are used when setting up the GCP side of the IPsec VPN  
configuration.

<table>
<thead>
<tr>
<th><strong>GCP parameter</strong></th>
<th><strong>Value</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>Name (project)</td>
<td><p><pre>
vpn-guide
</pre></p>

</td>
<td>GCP project name </td>
</tr>
<tr>
<td>Name (VPC network)</td>
<td><p><pre>
vpn-vendor-test-network
</pre></p>

</td>
<td>VPC network name</td>
</tr>
<tr>
<td>VPC subnet</td>
<td><p><pre>
vpn-scale-subnet-1
</pre></p>

</td>
<td>Subnet on <code>vpn-vendor-test-network</code></td>
</tr>
<tr>
<td>Region</td>
<td><p><pre>
us-east1
</pre></p>

</td>
<td>GCP region. Can be any region, but should be close to the on-premises gateway.</td>
</tr>
<tr>
<td>(Static external) IP address</td>
<td><p><pre>
vpn-scale-test-static-ip
</pre></p>

</td>
<td>Pre-existing external static IP address that you configure for the Internet side of the Cloud VPN gateway.</td>
</tr>
<tr>
<td>Subnet IP address range<br>
or local-traffic-selector value</td>
<td><p><pre>
172.16.100.0/24
</pre></p>

</td>
<td>IP address range for <code>subnet-1</code></td>
</tr>
<tr>
<td>Remote IP address range<br>
or destination range</td>
<td><p><pre>
10.0.0.0/8
</pre></p>

</td>
<td>IP address range for the on-premises subnet.</td>
</tr>
<tr>
<td>Name (Cloud Router)</td>
<td><p><pre>
vpn-scale-test-vendor-rtr
</pre></p>

</td>
<td>For dynamic routing: Cloud Router name</td>
</tr>
<tr>
<td>Name (BGP session)</td>
<td><p><pre>
bgp-peer1
</pre></p>

</td>
<td>For dynamic routing: BGP session name.</td>
</tr>
<tr>
<td>Name (gateway 1)</td>
<td><p><pre>
vpn-scale-test-<vendor-name>-gw-1
</pre></p>

</td>
<td>The name for the first GCP VPN gateway.</td>
</tr>
<tr>
<td>Name (tunnel 1)</td>
<td><p><pre>
vpn-scale-test-tunnel1
</pre></p>

</td>
<td>The name for the first VPN tunnel for <code>vpn-scale-test-<vendor-name>-gw-1</code></td>
</tr>
<tr>
<td>Forwarding rule</td>
<td><p><pre>
fr-esp
</pre></p>

</td>
<td>For the ESP protocol</td>
</tr>
<tr>
<td>Forwarding rule</td>
<td><p><pre>
fr-udp500
</pre></p>

</td>
<td>For the UDP protocol, port 500</td>
</tr>
<tr>
<td>Forwarding rule</td>
<td><p><pre>
fr-udp4500
</pre></p>

</td>
<td>For the UDP protocol, port 4500</td>
</tr>
</tbody>
</table>

### IPsec parameters

<vendor name><product name> supports the following IPsec parameters and ciphers for configuring the VPN gateways and tunnels as described in this document._  _For Cloud VPN, see the detailed list of [GCP-supported IKEv2 and IKEv1 ciphers](https://cloud.google.com/vpn/docs/concepts/advanced#supported_ike_ciphers).

<This is a sample table. Use supported parameters and values>

<table>
<thead>
<tr>
<th><strong>Parameter</strong></th>
<th><strong>Value</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>IPsec Mode</td>
<td>ESP+Auth Tunnel mode (Site-to-Site)</td>
</tr>
<tr>
<td>Authentication protocol</td>
<td>Pre-shared key</td>
</tr>
<tr>
<td>Key exchange version</td>
<td>IKEv2</td>
</tr>
<tr>
<td>Start</td>
<td>Auto</td>
</tr>
<tr>
<td>Perfect Forward Secrecy (PFS)</td>
<td>Group 16</td>
</tr>
<tr>
<td>Dead Peer Detection (DPD)</td>
<td>60 5 periodic</td>
</tr>
</tbody>
</table>

<This is a sample table. Use supported parameters and values for IKE phase 1 and phase 2>

<table>
<thead>
<tr>
<th><strong>Cipher Role</strong></th>
<th><strong>Cipher</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>Encryption (IPsec) Mode</td>
<td>esp-aes 256 esp-sha-hmac</td>
</tr>
<tr>
<td>Integrity</td>
<td>sha256</td>
</tr>
<tr>
<td>Diffie-Hellman (DH)</td>
<td>Group 16</td>
</tr>
<tr>
<td>Lifetime</td>
<td>36,000 seconds (10 hours)</td>
</tr>
</tbody>
</table>

# GCP-side configuration

This section covers configuring Cloud VPN using either dynamic routing with the BGP protocol (recommended) or static routing.

There are two ways to create VPN gateways on GCP, using the Google Cloud Platform Console and the `[gcloud `command-line tool.](https://cloud.google.com/sdk/) This section provides instructions for both.

## IPsec VPN using dynamic routing with the BGP protocol

For dynamic routing you use [Cloud Router](https://cloud.google.com/router/docs/concepts/overview)) to establish BGP sessions between GCP and the on-premises <vendor name><vendor product> equipment.

### Using the Cloud Platform Console

**Select a GCP project name**  
Before performing the tasks in this section, select the GCP project name in the drop-down menu at the top of the console screen. The sample name for use in with this guide is `vpn-guide.`

**Create a custom VPC network and subnet**

1. [GO TO THE VPC NETWORKS PAGE](https://console.cloud.google.com//networking/networks/list) in the Google Cloud Platform Console. 
1. Click **Create VPC network**.
1. Enter a **Name** of `vpn-vendor-test-network`.
1. Under **Subnets, Subnet creation mode**, select the **Custom** tab.
   1. Enter a **Name** of `vpn-scale-subnet-1`.
   1. Select a **Region** of `us-east1.`
   1. Enter an **IP address range** of `172.16.100.0/24`.
   1. In the **Subnets** window, click **Done**.

1. Click **Create**.
1. You're returned to the VPC Networks screen, where it takes about a minute for this network and its subnet to appear.

**Create the external IP address**

1. Go to the VPC Networks [EXTERNAL IP ADDRESS PAGE](https://console.cloud.google.com//networking/addresses/list) in the Google Cloud Platform Console. 
1. Click **Reserve Static Address**.
1. Populate the following fields for the Cloud VPN address:
   -  **Name** — The name of the address. Use `vpn-scale-test-static-ip`.
   -  **Region** — The region where you want to locate the VPN gateway. Normally, this is the region that contains the instances you wish to reach. In this case, use `us-east1`.

1. Click **Reserve**.
1. Make note of this IP address so that you can use it to configure the VPN gateway in the next section.

**Configure the VPN gateway**

1. [GO TO THE VPN PAGE](https://console.cloud.google.com/networking/vpn/list) in the Google Cloud Platform Console. 
1. Make sure to use the same Google Cloud Platform project that you used when creating the VPC network and subnets.
1. Click **Create VPN connection**.
1. **Populate the following fields for the gateway:**
   -  **Name** — The name of the VPN gateway. This name is displayed in the console and used in by the gcloud tool to reference the gateway. Use `vpn-scale-test-<vendor-name>-gw-1`.
   -  **Network** — The VPC network containing the instances the VPN gateway will serve. Use `vpn-vendor-test-network`.
   -  **Region** — The region where you want to locate the VPN gateway. Normally, this is the region that contains the instances you wish to reach. Use `us-east1`..
   -  **IP address** — Select the pre-existing [static external IP address](https://cloud.google.com/compute/docs/ip-addresses#reservedaddress), `vpn-scale-test-static-ip`, that you created for this gateway in the previous section.

1. **Populate the fields for at least one tunnel:**
   -  **Name** — The name of the VPN tunnel. Use `vpn-scale-test-tunnel1`.
   -  **Remote peer IP address **— The public, external IP address of the on-premises VPN gateway. 
   -  **IKE version** — IKEv2 or IKEv1. IKEv2 is preferred, but IKEv1 is supported if it is the only supported IKE version that the on-premises gateway can use.
   -  **Shared secret** — Character string used in establishing encryption for that tunnel. You must enter the same shared secret into both VPN gateways. If the VPN gateway device on the on-premises side of the tunnel doesn't generate one automatically, you can make one up.
   -  **Routing options** —  Select **Dynamic (BGP)**.
      -  **Cloud router** — Select **Create cloud router**, then populate the following fields. When you are done, click **Save and continue**.
      -  **Name** — The name of the Cloud Router. This name is displayed in the console and used by the `gcloud` command-line tool to reference the router. Example: `vpn-scale-test-<vendor-name>-rtr.
`      -  **Google ASN** — The [private ASN](https://tools.ietf.org/html/rfc6996) (64512- 65534, 4200000000 - 4294967294) for the router you are configuring. It can be any private ASN you are not already using. Example: `65002.`
      -  **BGP session** — Click the pencil icon, then populate the following fields. When you are done, click **Save and continue**.
      -  **Name** — `bgp-peer1`.
      -  **Peer ASN** — The [private ASN](https://tools.ietf.org/html/rfc6996) (64512 - 65534, 4200000000 - 4294967294) for the on-premises VPN device you are configuring. It can be any private ASN you are not already using. Example: `65001`.
      -  **Google BGP IP address** — The two BGP interface IP addresses must be  
**[link-local**](https://wikipedia.org/wiki/Link-local_address) IP addresses belonging to the same /30 subnet in `169.254.0.0/16`. Example: `169.254.1.1`.
      -  **Peer BGP IP address** — See [the explanation](https://cloud.google.com/router/docs/concepts/overview#dynamic_routing_for_vpn_tunnels_in_vpc_networks) for the **Google BGP IP address**. (link local address) IP address for the On-premises peer. Example: `169.254.1.2`. 

   -  **Remote network IP range** — The range of the "on-premises" subnet on the other side of the tunnel from this gateway. Configure as `10.0.0.0/8`.

1. Click **Create** to create the GCP VPN gateway, the Cloud Router, and initiate the tunnel, although the VPN gateways will not connect until you've configured the on-premises gateway and created firewall rules in GCP to allow traffic through the tunnel between the Cloud VPN  gateway and the on-premises gateway. This step automatically creates a static route to 10.0.2.0/24 as well as forwarding rules for udp:500, udp:4500, and esp traffic.

1. [Configure GCP firewall rules](https://cloud.google.com/compute/docs/vpn/creating-vpns#configuring_firewall_rules) to allow inbound traffic from the on-premises network subnets. You must also configure the on-premises network firewall to allow inbound traffic from your VPC subnet prefixes.
   1. Go to the [GCP Firewall rules](https://console.cloud.google.com/networking/firewalls) page
   1. Click **Create firewall rule**.
   1. Populate the following fields:
      -  **Name:** `vpnrule1`.
      -  **VPC network**: `vpn-vendor-test-network`
      -  **Source filter:** IP ranges.
      -  **Source IP ranges:** The on-premises IP ranges to accept from the on-premises VPN gateway.
      -  **Allowed protocols and ports:** `tcp;udp;icmp`

   1. Click **Create**.

### Using the gcloud command line tool

1. Create a custom VPC network (recommended). Make sure there is no conflict with your local network IP address range or any other configured subnets.  
  
`gcloud compute --project vpn-guide networks create vpn-vendor-test-network \`

`        --mode custom`  

1. Create a subnet on that network.
```
gcloud compute --project vpn-guide networks subnets create vpn-scale-subnet-1 \ 
        --network vpn-vendor-test-network \
        --region us-east1 --range 172.16.100.0/24
```

1. Create a GCP VPN gateway in the desired region. Normally, this is the region that contains the instances you want to reach. This step creates an unconfigured VPN gateway named `vpn-scale-test-<vendor-name>-gw-1` in your VPC network.  
  
`gcloud compute --project vpn-guide target-vpn-gateways create vpn-scale-test-<vendor-name>-gw-1 \`

```
        --network vpn-vendor-test-network \ 
        --region us-east1
```

1. Reserve a static IP address in the VPC network and region where you created the VPN gateway. Make a note of the created address for use in future steps.  
  
`gcloud compute --project vpn-guide addresses create \ `

`        --region us-east1 vpn-scale-test-static-ip`  

1. Create a forwarding rule that forwards ESP, IKE and NAT-T traffic toward the Cloud VPN gateway. Use the static IP address `vpn-scale-test-static-ip` you reserved earlier. This step generates a forwarding rule named `fr-esp,` `fr-udp500`, `fr-udp4500` resp.  
  
 `gcloud compute --project vpn-guide forwarding-rules create fr-esp \`

```
        --region us-east1 --ip-protocol ESP --address 35.185.3.177
          --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1

            gcloud compute --project vpn-guide forwarding-rules create fr-udp500 \ 
        --region us-east1 \
        --ip-protocol UDP --ports 500 --address 35.185.3.177 \
        --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1

      gcloud compute --project vpn-guide forwarding-rules create fr-udp4500 \ 
        --region us-east1 \
        --ip-protocol UDP --ports 4500 --address 35.185.3.177 \ 
```

`        --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1`  

1. Create [Cloud Router](https://cloud.google.com/compute/docs/cloudrouter) with the following command:
```
gcloud compute --project vpn-guide routers create vpn-scale-test-<vendor-name>-rtr --region us-east1 \
  --network vpn-vendor-test-network --asn 65002
```

1. Create a VPN tunnel on the Cloud VPN Gateway that points toward the external  
    IP address `[CUST_GW_EXT_IP]` of your on-premises VPN gateway. 
   1. Supply the shared secret. 
   1. Set the IKE version. The following example sets the IKE version to 2, which is the default, preferred IKE version. If you need to set it to 1, use `--ike_version 1`. 
   1. After you run this command, resources are allocated for this VPN tunnel, but it is not yet passing traffic.

        `gcloud compute --project vpn-guide vpn-tunnels create vpn-scale-test-tunnel1 \`

```
      --peer-address 204.237.220.4 \
      --region us-east1 --ike-version 2 \
      --shared-secret MySharedSecret \
      --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1 \ 
```

`      --router vpn-scale-test-<vendor-name>-rtr`  

1. Update the Cloud Router config to add a virtual interface (`--interface-name`) for the BGP peer. 
-  The BGP interface IP address must be a **[link-local**](https://wikipedia.org/wiki/Link-local_address) IP address belonging to the IP address range `169.254.0.0/16` and it must belong to same subnet as the interface address of the peer router. The recommended netmask length is `30`. 
-  Make sure each tunnel has a unique pair of IP addresses. Alternatively, you can leave `--ip-address` and `--mask-length blank, and leave `--peer-ip-address` blank in the next step, and the addresses will be automatically generated for you.  

```
gcloud compute --project vpn-guide routers add-interface vpn-scale-test-<vendor-name>-rtr \
  --interface-name if-1 --ip-address 169.254.1.1 --mask-length 30 \
        --vpn-tunnel tunnel1 --region us-east1
```

1. Update the Cloud Router config to add the BGP peer to the interface. 
-  This example uses ASN 65001 for the peer ASN. You can use your public ASN or  
 [private ASN](https://tools.ietf.org/html/rfc6996) (64512 - 65534, 4200000000 - 4294967294) that you are not already using in the peer network. 
-  The BGP peer interface IP address must be a **[link-local**](https://wikipedia.org/wiki/Link-local_address) IP address belonging to the IP address range `169.254.0.0/16`. It must belong to same subnet as the GCP-side interface. Make sure each tunnel has a unique pair of IPs.
```
gcloud compute --project vpn-guide routers add-bgp-peer vpn-scale-test-<vendor-name>-rtr \ 
        --peer-name bgp-peer1 --interface if-1 \ 
        --peer-ip-address 169.254.1.2  --peer-asn 65001 \ 
        --region us-east1
```

1. View details of the configured Cloud Router and confirm your settings.  
  
`gcloud compute --project vpn-guide routers describe vpn-scale-test-<vendor-name>-rtr --region us-east1`  

1. Create firewall rules to allow traffic between the on-premises network and the GCP VPC networks.  
  
`gcloud compute --project vpn-guide firewall-rules create vpnrule1`

```
        --network vpn-vendor-test-network \
        --allow tcp,udp,icmp --source-ranges 10.0.0.0/8
## IPsec VPN using "route based" static routing

This section covers the steps for creating a GCP IPsec VPN using static routing. This configuration is also known as "route based VPN." With route based VPN, traffic from all subnets in the same region as the GCP VPN gateway are forwarded through the VPN tunnel. For more information, see the Cloud VPN Overview.
```

### Using the Google Cloud Platform Console

1. Repeat the same steps as listed for setting up a GCP gateway for dynamic routing, except,  in the configuration for a tunnel under **Routing options, **choose** "route based" **and configure the following settings:
   1. **Remote network IP ranges** — The range, or ranges, of the on-premises network, which is the network on the other side of the tunnel from the Cloud VPN gateway you are currently configuring. Use `10.0.0.0/8`.   

1. Click **Create** to create the gateway and initiate all tunnels. This step automatically creates a network-wide route and necessary forwarding rules for the tunnel. The tunnels will not pass traffic until you've configured the firewall rules.   

1. [Configure firewall rules](https://cloud.google.com/compute/docs/vpn/creating-vpns#configuring_firewall_rules) to allow inbound traffic from the on-premises network subnets. You must also configure the on-premises network firewall to allow inbound traffic from your VPC subnet prefixes.
   1. Go to the [Firewall rules page](https://console.cloud.google.com/networking/firewalls).
   1. Click **Create firewall rule**.
   1. Populate the following fields:
      -  **Name:** `vpnrule1
`      -  **VPC network:** `vpn-vendor-test-network`
      -  **Source filter:** IP ranges.
      -  **Source IP ranges:** The peer ranges to accept from the peer VPN gateway.
      -  **Allowed protocols and ports:** `tcp;udp;icmp`

   1. Click **Create**.

### Using the gcloud command-line tool

1. Create a custom VPC network (preferred). Make sure there is no conflict with your local network IP address range.  
  
` gcloud compute --project vpn-guide networks create vpn-scale-test-<vendor-name> --mode custom`
```
      gcloud compute --project vpn-guide networks subnets create subnet-1 \ 
        --network vpn-vendor-test-network \
        --region us-east1 --range 172.16.100.0/24
```

1. Create a VPN gateway in the desired region. Normally, this is the region that contains the instances you wish to reach. This step creates an unconfigured VPN gateway named `vpn-scale-test-<vendor-name>-gw-1` in your GCP VPC network.  
  
` gcloud compute --project vpn-guide target-vpn-gateways create vpn-scale-test-<vendor-name>-gw-1 \  
   --network vpn-vendor-test-network --region us-east1`

1. Reserve a static IP address in the VPC network and region where you created the VPN gateway. Make a note of the address that was created for use in future steps.  
  
   `gcloud compute --project vpn-guide addresses create `

`         --region us-east1 vpn-scale-test-static-ip`  

1. Create a forwarding rule that forwards ESP, IKE, and, optionally, NAT-T traffic toward the Cloud VPN gateway. This step generates three forwarding rules named fr-esp, fr-udp500, and fr-udp450.  

1. Use the static IP address `vpn-scale-test-static-ip` that you reserved earlier. 35.185.3.177 address is a sample external IP address. Use the address that was generated for  `vpn-scale-test-static-ip.`

```
 
 gcloud compute --project vpn-guide forwarding-rules create fr-esp
        --region us-east1 \
        --ip-protocol ESP --address 35.185.3.177 \ 
        --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1

       gcloud compute --project vpn-guide forwarding-rules create fr-udp500 
         --region us-east1 \
         --ip-protocol=UDP --address 35.185.3.177 \ 
         --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1 --ports 500

       gcloud compute --project vpn-guide forwarding-rules create fr-udp4500
         --region us-east1 \
         --ip-protocol=UDP --ports 4500 --address 35.185.3.177 \ 
```

`         --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1`   
  
6. Create a VPN tunnel on the Cloud VPN Gateway that points toward the external IP address `[CUST_GW_EXT_IP]` of your on-premises VPN gateway. 

   1. Supply the shared secret. 
   1. Set the IKE version. The following example sets the IKE version to 2, which is the default, preferred IKE version. If you need to set it to 1, use `--ike_version 1`. 
   1. After you run this command, resources are allocated for this VPN tunnel, but it is not yet passing traffic.  
  
`gcloud compute --project vpn-guide vpn-tunnels create tunnel1 \`
```
        --peer-address 204.237.220.4 \
        --region us-east1 --ike-version 2 \ 
        --shared-secret MySharedSecret \ 
        --target-vpn-gateway vpn-scale-test-<vendor-name>-gw-1 \
```

`        --local-traffic-selector=172.16.100.0/24`  
  
7. Use a [static route](https://cloud.google.com/sdk/gcloud/reference/compute/routes/create) to forward traffic to the destination range of IP addresses,  
`[CIDR_DEST_RANGE]`, in your local on-premises network. You can repeat this  
 command to add multiple IP address ranges to the VPN tunnel. The region must be the  
 same region as for the VPN tunnel.  
  
 `gcloud compute --project vpn-guide routes create route`
```
        --network [NETWORK] --next-hop-vpn-tunnel vpn-scale-test-tunnel1
        --next-hop-vpn-tunnel-region us-east1 
```

`        --destination-range 10.0.0.0/8`  
  
8. Create firewall rules to allow traffic between on-premises network and GCP VPC networks.  
  
`gcloud compute --project vpn-guide firewall-rules create vpnrule1`  
`  --network vpn-vendor-test-network \  
  --allow tcp,udp,icmp --source-ranges 10.0.0.0/8`  

# <Vendor name><vendor product> configuration

<Below are some sample tasks to configure the on-premises side of the VPN gateway configuration using <vendor name> equipment.>

<For an example of how to fill in the instructions and parameters, see the [Cisco ASR1000 section ](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#configuration--cisco-asr-1000)of  [the VPN Interop guide for Cisco ASR](https://cloud.google.com/community/tutorials/using-cloud-vpn-with-cisco-asr#top_of_page). For each set of instructions, explain what purpose the configuration setting serves.> 

## Creating the base network configuration

Follow this procedure to create the base Layer 3 network configuration of <vendor name>. 

-  At least one internal-facing network interface is required to connect to your on-premises network, and one external-facing interface is required to connect to GCP. 
-  A sample interface configuration is provided below  
for reference:  

```
<insert configuration code snippet here>
## Creating the base VPN gateway configuration

Follow this multi-step procedure to create the base VPN configuration. 
```

<Eliminate any steps that are not required by the `<vendor name><product name>` device.>    

### Configure the IKEv2 proposal and policy

<Insert the instructions for creating the IKEv2 proposal and policy here. Below are some examples of IKE algorithms to specify as part of the instructions.>

-  **Encryption algorithm** – <list required algorithms here>
-  **Integrity algorithm** – <list required algorithms here>
-  **Diffie-Hellman group **– <list required group here>
```
<insert configuration code snippet here>
### Configure the IKEv2 keyring

<Insert the instructions for creating the IKEv2 keyring here.>

<insert configuration code snippet here>
```

### Configure the IKEv2 profile

<Insert the instructions for creating the IKEv2 profile here. Below are some examples of parameters to set.>  

-  `IKEv2 Lifetime` - Set the lifetime of the security associations, after which a reconnection occurs. Set to 36,000 seconds as recommended configuration on a <product name> router.
-  `DPD`** **– Set the dead peer detection interval and retry interval, if there are no response from the peer, the SA created for that peer is deleted. Set to 60 seconds keepalive interval and 5 seconds retry interval as recommended configuration on a <product name>router.  

```
<insert configuration code snippet here>
### Configure the IPsec Security Association (SA)

<Insert the instructions for creating the IPsec SA here. Below are some examples of parameters to set.>
```

-  `IPsec SA lifetime` – 1 hour is the recommended value on ASR 1000 router.
-  `IPsec SA replay window-size` – 1024 is the recommended value on ASR 1000 router.
```
<insert configuration code snippet here>
### Configure the IPsec transform set

<Insert the instructions for creating the IPsec transform set here.>
```

`<insert configuration code snippet here>`  

### Configure the IPsec profile

<Insert the instructions for creating the IPsec profile here. Below are some examples of parameters to set.>  

-  Perfect Forward Secrecy (PFS) - PFS ensures that the same key will not be generated again, so forces a new diffie-hellman key exchange. Set to group16 as recommended configuration on ASR 1000 router.
-  SA Lifetime - set the lifetime of the security associations (after which a  
  reconnection will occur). Set to `3600 seconds` as recommended configuration  
  on ASR 1000 router.
```
<insert configuration code snippet here>
### Configure the IPsec static virtual tunnel interface (SVTI)

<Insert the instructions for creating the IPsec SVTI here. Below are some examples of parameters to set.>
```

-  Adjust the maximum segment size (MSS) value of TCP packets going through a  
router. The recommended value is 1360 when the number of IP MTU bytes is set to  
1400. With these recommended settings, TCP sessions quickly scale back to  
1400-byte IP packets so the packets will "fit" in the tunnel.
```
<insert configuration code snippet here>
## Configuring the dynamic routing protocol (preferred)

To configure dynamic routing of traffic through the VPN tunnel(s) using the BGP routing protocol.  <Insert the instructions for configuring dynamic routing here. Below are some examples of parameters to set.>

BGP timers are adjusted to provide more rapid detection of outages.

To advertise additional prefixes to GCP, <insert instructions here>.

<insert configuration code snippet here>
```

## Configuring static routing

To configure static routing of traffic toward the GCP network through the VPN tunnel interface, enter the following command. Check [GCP Best Practices](https://cloud.google.com/router/docs/resources/best-practices) for further recommendations regarding on-premises routing configurations.
```
<insert configuration code snippet here>
## Saving the configuration

<Insert the instructions for saving the configuration here>.

<insert configuration code snippet here>
```

## Testing the configuration

It's important to test the VPN connection from both sides of a VPN tunnel. For either side, make sure that the subnet a machine or virtual machine is located on is being forwarded through the VPN tunnel.

First, create virtual machines (VM) on both sides of the tunnel.  Make sure to configure the VMs on a subnet that will pass traffic through the VPN tunnel.

-  Instructions for creating virtual machine for `<vendor name><product name>` platforms are located <here>.
-  Instructions for creating virtual machines in Google Compute Engine are located in the [Getting Started Guide](https://cloud.google.com/compute/docs/quickstart).

Once virtual machines have been deployed on both GCP and `<vendor name><product name>` platforms, an ICMP echo ("ping") test can ensure network connectivity through a VPN tunnel.

On the GCP side, you can SSH into a virtual machine (VM) instance and test the connection to another machine behind the on-premises gateway. 

1. From the Cloud console's [Compute Engine, VM Instances tab](https://cloud.google.com/compute/instances), find the GCP virtual machine you created. 
1. In the **Connect** column, click **SSH**.
1. A browser window opens at the VM's command line.
1. Ping a machine behind the on-premises gateway to test connectivity through the VPN tunnel from the GCP side.

<Insert any additional instructions for testing the VPN tunnels from the <vendor name><product name> here. For example, below is an example of a successful ping from a Cisco ASR router to GCP.>  
  
   ` cisco-asr#ping 172.16.100.2 source 10.0.200.1  
   Type escape sequence to abort.  
   Sending 5, 100-byte ICMP Echos to 172.16.100.2, timeout is 2 seconds:  
   Packet sent with a source address of 10.0.200.1  
   !!!!!  
   Success rate is 100 percent (5/5), round-trip min/avg/max = 18/19/20 ms`

# Advanced VPN configurations

This section covers configuring redundant on-premises VPN gatetways and how to get higher throughput through VPN tunnels.

## Configuring VPN redundancy

<insert a link to the <vendor name><product name> reference guide for configuring redundancy on the vendor product.>  
  
Using redundant on-premises VPN gateways ensures continuous availability when a tunnel fails.  
  
If a Cloud VPN tunnel fails, it restarts automatically. If an entire virtual VPN gateway device fails, Cloud VPN automatically creates a new one with the same configuration. The new gateway and tunnel connect automatically.  However, for the most robust redundancy, configuring 2 Cloud VPN gateways in different regions is recommended.

For hardware appliances such as `<vendor name><product name>`, for redundancy purposes, you should deploy 2 <product name> devices and create VPN tunnels to GCP from each device.  
  
The VPN redundancy configuration example is built based on the Dynamic Routing with  
BGP configuration described previously.

### Configuring <product name> Dynamic route priority settings

<Insert the instructions for configuring BGP route priority settings on the `<vendor name><product name>` device here. Indicated whether the preferred route is a higher or lower priority number>.
```
<insert configuration code snippet showing the existing BGP route configuration here>

<Insert the instructions for configuring BGP Multi-exit Discriminator (MED) values on the <vendor name><product name> device or service here>.

<insert configuration code snippet showing BGP MED values here>
### Configuring <product name> Static route metrics

<Insert the instructions for configuring static route on the <vendor name><product name> device or service here. State whether the metric for the preferred route is a higher or lower number>.

<insert configuration code snippet here>
```

### Configuring GCP BGP route priority (optional)

With GCP dynamic routing,  you can define advertised route priority. For details, see the[ Cloud Router overview](https://cloud.google.com/router/docs/concepts/overview) and [the Cloud Router API documentation](https://cloud.google.com/sdk/gcloud/reference/compute/routers/update-bgp-peer).  
  
If you have a preferred route announced to the on-premises side of the network, BGP will prefer the higher priority on-premises route first.  
  
`gcloud compute --project vpn-guide routers add-bgp-peer vpn-scale-test-<vendor-name>-rtr --peer-name bgp-peer1 \`

```
  --interface if-1 --peer-ip-address 169.254.1.2 \ 
  --peer-asn 65001 --region us-east1 \
  --advertised-route-priority=2000
```

### Configuring GCP Static route metrics (optional)

When using static routing, GCP gives you an option to customize route priority if there are multiple routes with the same prefix length. To enable symmetric traffic flow, make sure that you set the priority of your secondary GCP tunnel to a higher value than the primary tunnel (default priority is 1000). To define the route priority run the command below.  
  
`gcloud compute --project vpn-guide routes create route2 `

```
  --network vpn-vendor-test-network \
  --next-hop-vpn-tunnel vpn-scale-test-tunnel1 \ 
  --next-hop-vpn-tunnel-region us-east1 \
  --destination-range 10.0.0.0/8 \ 
  --priority=2000
```

### Testing VPN Redundancy on <vendor name><device name>

<Insert the instructions for testing VPN redundancy on the `<vendor name><product name>`  device here. Below is example testing output. Replace it with the output for the `<vendor name><product name>` device.>
```
cisco-asr#sh ip bgp 172.16.100.0
    BGP routing table entry for 172.16.100.0/24, version 690
    Paths: (3 available, best #1, table default)
    Multipath: eBGP
    Flag: 0x404200
      Advertised to update-groups:
         18
      Refresh Epoch 1
      65002
        169.254.0.1 from 169.254.0.1 (169.254.0.1)
          Origin incomplete, metric 100, localpref 2000, valid, external, best
          rx pathid: 0, tx pathid: 0x0
      Refresh Epoch 1
      65002, (received-only)
        169.254.0.1 from 169.254.0.1 (169.254.0.1)
          Origin incomplete, metric 100, localpref 100, valid, external
          rx pathid: 0, tx pathid: 0
      Refresh Epoch 1
      65002
        169.254.0.57 from 169.254.0.57 (169.254.0.1)
          Origin incomplete, metric 100, localpref 100, valid, external
          rx pathid: 0, tx pathid: 0

    cisco-asr#sh ip cef 172.16.100.0
    172.16.100.0/24
      nexthop 169.254.0.1 Tunnel1
## Getting higher throughput

As documented in GCP VPN Advanced Configurations, each Cloud VPN tunnel can support up to 3 Gbps when the tunnel traffic traverses a direct peering link, or 1.5 Gbps when the tunnel traffic the public Internet. 
```

To increase the VPN throughput, the recommendation is to add multiple Cloud VPN gateways in the same region to load balance the traffic across the tunnels. The 2 VPN tunnels configuration example here is based on the IPsec tunnel and BGP configuration described above,  
and can be expanded to more tunnels if required.

### Configuring <vendor name><product name>

<Describe how `<vendor name><product name>`  handles tunnel prioritization. For example, using ECMP. Also describe how many equal cost paths the device can handle.>  
  
`<insert configuration code snippet for existing code here>`

### Configuring GCP

GCP performs ECMP routing by default so there is no additional configuration required apart  
from creating x number of tunnels where x depends on your throughput requirements. You can either use a single VPN gateway to create multiple tunnels or create a separate VPN gateway for each tunnel.  
  
Actual tunnel throughput can vary depending on the following factors:  

-  Network capacity between the GCP and on-premises VPN gateways.
-  The capabilities of the on-premises VPN device. See your device's documentation for more information.
-  Packet size. Because processing happens on a per-packet basis, traffic with a significant percentage of smaller packets can reduce overall throughput.
-  [High Round Trip Time (RTT)](https://en.wikipedia.org/wiki/Round-trip_delay_time) and packet loss rates can greatly reduce throughput for TCP.

### Testing the higher-throughput configuration

The IPsec tunnel can be tested from the on-premises VPN device by using ICMP to ping a Virtual Machine (VM) host on GCP. 

<Add details here about how to initiate a ping from `<vendor name><product name>` similar to those mentioned previously >.
```
<insert ping output from on-premises device here>
# Troubleshooting IPsec on <vendor name><product name>

For troubleshooting information, refer to the <vendor name><product name> troubleshooting guide <add link>.

<Add details here about what kind of troubleshooting information can be found in the <vendor name><product name> guide>.
```

# Reference documentation

You can refer to the following `<vendor name><product name> `documentation and Cloud VPN documentation for additional information about both products.

## <vendor name><product name> documentation

For more product information on `<vendor name><product name>` , refer to the following <product name> feature configuration guides and datasheets:  

-  <guide name>
-  <guide name>
-  <guide name>

For common `<vendor name><product name>`  error messages and debug commands, refer to the following guides:  

-  <guide name>
-  <guide name>
-  <guide name>

## GCP documentation

To learn more about GCP networking, refer to the following documents:

-  [VPC Networks](https://cloud.google.com/vpc/docs)
-  [Cloud VPN Overview](https://cloud.google.com/compute/docs/vpn/overview)
-  [Advanced Cloud VPN Configurations](https://cloud.google.com/vpn/docs/concepts/advanced)
-  [Troubleshooting Cloud VPN](https://cloud.google.com/compute/docs/vpn/troubleshooting)
