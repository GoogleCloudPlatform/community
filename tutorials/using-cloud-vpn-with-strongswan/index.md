---
title: How to Set Up VPN Between Strongswan and Cloud VPN
description: Learn how to build site-to-site IPSEC VPN between Strongswan and Cloud VPN.
author: civiloid,brona
tags: Compute Engine, Cloud VPN, Strongswan, Libreswan, firewall
date_published: TBD
---

This guide walks you through the process to configure the [Strongswan](https://www.strongswan.org/)
for integration with the [Google Cloud VPN][cloud_vpn]. This information is
provided as an example only. Please note that this guide is not meant to be a
comprehensive overview of IPsec and assumes basic familiarity with the IPsec
protocol.

[cloud_vpn]: https://cloud.google.com/compute/docs/vpn/overview

# Environment overview

The equipment used in the creation of this guide is as follows:

* Vendor: Strongswan
* Software Release: 5.5.1 on Debian 9.6

## Topology

The topology outlined by this guide is a basic site-to-site IPsec VPN tunnel
configuration using the referenced device:

![Topology](https://storage.googleapis.com/gcp-community/tutorials/using-cloud-vpn-with-strongswan/Overview.png)

# Before you begin

## Prerequisities

To use a Strongswan with Cloud VPN make sure the following prerequisites have been met:

* VM or Server that runs Strongswan is healthy and have no known issues. 
* There is root access to the Strongswan instance.
* Your on-prem firewall allows udp port 500, udp port 4500 and esp packets.
* You should be able to configure your on-prem router to route traffic through Strongswan VPN gateway. Some environments might not give you that option.


## IPsec parameters

Cloud VPN supports extensive
[list](https://cloud.google.com/vpn/docs/concepts/supported-ike-ciphers)
of ciphers that can be used per your security policies. The following parameters and values are used in the Gateway’s IPSec configuration for the
purpose of this guide.

|Parameter | Value|
--------- |  -----
|IPsec Mode | `Tunnel mode` |
|Auth protocol | `Pre-shared-key` |
|Key Exchange | `IKEv2` |
|Start | `Auto` |
|Perfect Forward Secrecy (PFS) | `on` |

These are the Cipher configuration settings for IKE phase 1 and phase 2 that are used
in this guide.

|Phase | Cipher Role | Cipher|
-------|-------------|-------
|Phase-1|Encryption|`aes256gcm16`|
| (ike) |Integrity|`sha512`|
|       |Diffie-Helman|`modp4096` (Group 16)|
|       |Phase1 lifetime| `36,000 seconds` |
|Phase-2|Encryption|`aes256gcm16`|
| (esp) |Integrity|`sha512`|
|       |Diffie-Helman|`modp8192` (Group 18)|
|       |Phase2 lifetime| `10,800 seconds`|

# Configuring policy-based IPsec VPN

Below is a sample environment to walk you through set up of policy based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

**Cloud VPN**

|Name | Value|
-----|------
|Cloud VPN(external IP)|`35.204.151.163`|
|VPC CIDR|`192.168.0.0/24`|

**Strongswan**

|Name | Value|
-----|------
|External IP|`35.204.200.153`|
|CIDR Behind Strongswan|`10.164.0.0/20`|

## Configuration - GCP

To configure Cloud VPN:
1. In the Google Cloud Platform Console, select **Networking** > **[Create VPN connection](https://console.cloud.google.com/interconnect/vpn)**.

1. Click **CREATE VPN CONNECTION**.

1. Populate the fields for the gateway and tunnel as shown in the following table and click **Create**:

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`gcp-to-strongswan-1`|Name of the VPN gateway.|
|Description|`VPN tunnel connection between GCP and Strongswan`|Description of the VPN connection.|
|Network|`to-sw`| The GCP network the VPN gateway attaches to. Note: This network will get VPN connectivity.|
|Region|`europe-west4`|The home region of the VPN gateway Note: Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`gcp-to-strangswan(35.204.151.163)`|The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|
|Remote peer IP address| `35.204.200.153`|Public IP address of the on-premise VPN appliance used to connect to the Cloud VPN.|
|IKE version|`IKEv2`|The IKE protocol version. You can select IKEv1 or IKEv2.|
|Shared secret|`secret`|A shared secret used for authentication by the VPN gateways. Configure the on-premise VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Policy-based`|Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Remote network IP ranges| `10.164.0.0/20`|The on-premise CIDR blocks connecting to GCP from the VPN gateway.|
|Local IP ranges| `192.168.0.0/24`|The GCP IP ranges matching the selected subnet.|

## Configuration - Strongswan

This guide will assume that you have strongswan already installed. It will also rely on default
filesystem layout of Debian 9.6.

**Step 1**: Ensure ip forwarding is enabled

Server that host strongswan will act as a gateway, so it's required to `net.ipv4.ip_forwarding`
sysctl.

To check it's current status you can use following command:
```
sysctl net.ipv4.ip_forward
```

To temporary enable it (until reboot), you can use following command:
```
sysctl -w net.ipv4.ip_forward=1
```

To make changes permanent you should add a line to sysctl.conf:

**/etc/sysctl.d/99-forwarding.conf**:
```
net.ipv4.ip_forward = 1
```

**Step 2**: Configure IPSec credentials

Ensure that the following line present in file:

**/var/lib/strongswan/ipsec.secrets.inc**
```
35.204.151.163 : PSK "secret"
```

**Step 3**: Configure IPSec connection

**/var/lib/strongswan/ipsec.conf.inc**
```
include /etc/ipsec.d/gcp.conf
```

**/etc/ipsec.d/gcp.conf**
```
conn %default
    ikelifetime=600m # 36,000 s
    keylife=180m # 10,800 s
    rekeymargin=3m
    keyingtries=3
    keyexchange=ikev2
    mobike=no
    ike=aes256gcm16-sha512-modp4096
    esp=aes256gcm16-sha512-modp8192
    authby=psk

conn net-net
    left=35.204.200.153 # In case of NAT set to internal IP, e.x. 10.164.0.6
    leftid=35.204.200.153
    leftsubnet=10.164.0.0/20
    leftauth=psk
    right=35.204.151.163
    rightid=35.204.151.163
    rightsubnet=192.168.0.0/24
    rightauth=psk
    type=tunnel
    # auto=add - means strongswan won't try to initiate it
    # auto=start - means strongswan will try to establish connection as well
    # Please note that GCP will also try to initiate the connection
    auto=start
    # dpdaction=restart - means strongswan will try to reconnect if Dead Peer Detection spots
    #                  a problem. Change to 'clear' if needed
    dpdaction=restart
    closeaction=restart
```

**Step 4**: Start the Strongswan

Now you can start strongswan:
```
systemctl start strongswan
```

After you make sure it's working as expected, you can add strongswan to autostart:
```
systemctl enable strongswan
```

# Configuring a Dynamic (BGP) IPsec VPN Tunnel with Strongswan and BIRD

In this example Dynamic (BGP) based VPN will use VTI interface. Guide is based on official [strongswan wiki](https://wiki.strongswan.org/projects/strongswan/wiki/RouteBasedVPN#VTI-Devices-on-Linux).

Below is a sample environment to walk you through set up of route based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

This guide will assume that you have bird 1.6.3 installed on your strongswan server.

**Cloud VPN**

|Name | Value|
-----|------
|Cloud VPN(external IP)|`35.204.151.163`|
|VPC CIDR|`192.168.0.0/24`|
|TUN-INSIDE GCP|`169.254.2.1`|
|GCP-ASN|`65000`|

**Strongswan**

|Name | Value|
-----|------
|External IP|`35.204.200.153`|
|CIDR Behind Strongswan|`10.164.0.0/20`|
|TUN-INSIDE- SW|`169.254.2.2`|
|Strongswan ASN|`65002`|

## Configuration - GCP

With route based VPN both static and dynamic routing can be used. This example will use
dynamic (BGP) routing. [Cloud Router](https://cloud.google.com/router/docs/) is used to establish
BGP sessions between the 2 peers.

### Configuring cloud router

**Step 1**: In Google Cloud Platform Console, select **Networking** > **[Cloud Routers](https://console.cloud.google.com/interconnect/routers)** > **Create Router**.

**Step 2**: Enter the parameters as shown in the following table and click **Create**.

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`gcp-to-strongswan-router-1`|Name of the cloud router.|
|Description|           |Description of the cloud router.|
|Network|`to-sw`|The GCP network the cloud router attaches to. Note: This is the network which manages route information.|
|Region|`europe-west4`|The home region of the cloud router.Note: Make sure the cloud router is in the same region as the sub-networks it is connecting to.|
|Google ASN|`65000`|The Autonomous System Number assigned to the cloud router. Use any unused private ASN (64512 - 65534, 4200000000 – 4294967294).|

### Configuring Cloud VPN

**Step 1**: In Google Cloud Platform Console, select **Networking** > **Interconnect** > **[VPN](https://console.cloud.google.com/interconnect/vpn)** > **CREATE VPN CONNECTION**.

**Step 2**: Enter the parameters as shown in the following table for the Google Compute Engine VPN gateway:

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`gcp-to-strongswan-1`|Name of the VPN gateway.|
|Description|`VPN tunnel connection between GCP and Strongswan`|Description of the VPN connection.|
|Network|`to-sw`| The GCP network the VPN gateway attaches to. Note: This network will get VPN connectivity.|
|Region|`europe-west4`|The home region of the VPN gateway Note: Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`gcp-to-strangswan(35.204.151.163)`|The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|

**Step 3**: Enter the parameters as shown in the following table for the tunnel:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`gcp-to-strongswan-1-tunnel-1`|Name of the VPN gateway|
|Description|`VPN tunnel connection between GCP and Strongswan`|Description of the VPN gateway|
|Remote peer IP address| `35.204.200.153`|Public IP address of the on-premise VPN appliance used to connect to the Cloud VPN.|
|IKE version|`IKEv2`|The IKE protocol version. You can select IKEv1 or IKEv2.|
|Shared secret|`secret`|A shared secret used for authentication by the VPN gateways. Configure the on-premise VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Dynamic(BGP)`|Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Cloud Router|`gcp-to-strongswan-router-1`|Select the Cloud router created previously.|
|BGP session| |BGP sessions enable your cloud network and on-premise networks to dynamically exchange routes|

**Step 4**: Enter the parameters as shown in the following table for the BGP peering:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`gcp-to-strongswan-bgp`|Name of the BGP session.|
|Peer ASN|`65002`|Unique BGP ASN of the on-premise router.|
|Google BGP IP address|`169.254.2.1`|
|Peer BGP IP address|`169.254.2.2`|

Click **Save and Continue** to complete.

**Note:** – Add ingress firewall rules to allow inbound network traffic as per your security policy.

## Configuration - Strongswan

This guide will assume that you have strongswan already installed. It will also rely on default layout of Debian 9.6.

**Step 1**: Configure BIRD

**/etc/bird/bird.conf**
```
# Config example for bird 1.6 
#debug protocols all;

router id 169.254.2.2;

# Watch interface up/down events
protocol device {
       scan time 10;
}

# Import interface routes (Connected)
# (Not required in this example as kernel import all is used here to workaround the /32 on eth0 GCE VM setup)
#protocol direct {
#       interface "*";
#}

# Sync routes to kernel
protocol kernel {
       learn;
       merge paths on; # For ECMP
       export all; # Sync all routes to kernel
       import all; # Required due to /32 on GCE VMs for the static route below
}

# Configure a static route to make sure route exists
protocol static {
       # Network connected to eth0
       route 10.164.0.0/20 recursive 10.164.0.1; # Network connected to eth0
       # Or blackhole the aggregate
       # route 10.164.0.0/20 blackhole; 
}

# Prefix lists for routing security
# (Accept /24 as the most specific route)
define GCP_VPC_A_PREFIXES = [ 192.168.0.0/16{16,24} ]; # VPC A address space
define LOCAL_PREFIXES     = [ 10.164.0.0/16{16,24} ];  # Local address space

# Filter received prefixes
filter gcp_vpc_a_in
{
      if (net ~ GCP_VPC_A_PREFIXES) then accept;
      else reject;
}

# Filter advertised prefixes
filter gcp_vpc_a_out
{
      if (net ~ LOCAL_PREFIXES) then accept;
      else reject;
}

template bgp gcp_vpc_a {
       keepalive time 20;
       hold time 60;
       graceful restart aware; # Cloud Router uses GR during maintenance
       #multihop 3; # Required for Dedicated/Partner Interconnect

       import filter gcp_vpc_a_in;
       import limit 10 action warn; # restart | block | disable

       export filter gcp_vpc_a_out;
       export limit 10 action warn; # restart | block | disable
}

protocol bgp gcp_vpc_a_tun1 from gcp_vpc_a
{
       local 169.254.2.2 as 65002;
       neighbor 169.254.2.1 as 65000;
}
```

**Step 2**: Disable automatic routes in Strongswan

Routes will be handled by BIRD, so it's required to disable automatic route creation in strongswan.

**/etc/strongswan.d/vti.conf**
```
charon {
    # We will handle routes by ourselves
    install_routes = no
}
```

**Step 3**: Create a script that will configure VTI interface

This script will be called everytime new tunnel is established and it will take care of proper
interface configuration, including MTU, etc.

**/var/lib/strongswan/ipsec-vti.sh**
```
#!/bin/bash
set -o nounset
set -o errexit

IP=$(which ip)
IPTABLES=$(which iptables)

PLUTO_MARK_OUT_ARR=(${PLUTO_MARK_OUT//// })
PLUTO_MARK_IN_ARR=(${PLUTO_MARK_IN//// })

VTI_TUNNEL_ID=${1}
VTI_REMOTE=${2}
VTI_LOCAL=${3}

LOCAL_IF="${PLUTO_INTERFACE}"
VTI_IF="vti${VTI_TUNNEL_ID}"
# GCP's MTU is 1460, so it's hardcoded
GCP_MTU="1460"
# ipsec overhead is 73 bytes, we need to compute new mtu.
VTI_MTU=$((GCP_MTU-73))

case "${PLUTO_VERB}" in
    up-client)
        ${IP} link add ${VTI_IF} type vti local ${PLUTO_ME} remote ${PLUTO_PEER} okey ${PLUTO_MARK_OUT_ARR[0]} ikey ${PLUTO_MARK_IN_ARR[0]}
        ${IP} addr add ${VTI_LOCAL} remote ${VTI_REMOTE} dev "${VTI_IF}"
        ${IP} link set ${VTI_IF} up mtu ${VTI_MTU}

        # Disable IPSEC Policy
        sysctl -w net.ipv4.conf.${VTI_IF}.disable_policy=1

        # Enable loosy source validation, if possible. Otherwise disable validation.
        sysctl -w net.ipv4.conf.${VTI_IF}.rp_filter=2 || sysctl -w net.ipv4.conf.${VTI_IF}.rp_filter=0

        ${IPTABLES} -t mangle -I INPUT -p esp -s ${PLUTO_PEER} -d ${PLUTO_ME} -j MARK --set-xmark ${PLUTO_MARK_IN}

        # If you would like to use VTI for policy-based you shoud take care of routing by yourselv, e.x.
        #if [[ "${PLUTO_PEER_CLIENT}" != "0.0.0.0/0" ]]; then
        #    ${IP} r add "${PLUTO_PEER_CLIENT}" dev "${VTI_IF}"
        #fi
        ;;
    down-client)
        ${IP} tunnel del "${VTI_IF}"
        ${IPTABLES} -t mangle -D INPUT -p esp -s ${PLUTO_PEER} -d ${PLUTO_ME} -j MARK --set-xmark ${PLUTO_MARK_IN}
        ;;
esac

# Enable IPv4 forwarding
sysctl -w net.ipv4.ip_forward=1

# Disable IPSEC Encryption on local net
sysctl -w net.ipv4.conf.${LOCAL_IF}.disable_xfrm=1
sysctl -w net.ipv4.conf.${LOCAL_IF}.disable_policy=1
```

You should also make `/var/lib/strongswan/ipsec-vti.sh` executable, by using following command:
```
chmod +x /var/lib/strongswan/ipsec-vti.sh
```

**Step 4**: Configure IPSec credentials
            
Ensure that the following line present in file:

**/var/lib/strongswan/ipsec.secrets.inc**
```
35.204.151.163 : PSK "secret"
```

**Step 5**: Configure IPSec connection

**/var/lib/strongswan/ipsec.conf.inc**
```
include /etc/ipsec.d/gcp.conf
```

**/etc/ipsec.d/gcp.conf**
```
conn %default
    ikelifetime=600m # 36,000 s
    keylife=180m # 10,800 s
    rekeymargin=3m
    keyingtries=3
    keyexchange=ikev2
    mobike=no
    ike=aes256gcm16-sha512-modp4096
    esp=aes256gcm16-sha512-modp8192
    authby=psk

conn net-net
    leftupdown="/var/lib/strongswan/ipsec-vti.sh 0 169.254.2.1/30 169.254.2.2/30"
    left=35.204.200.153 # In case of NAT set to internal IP, e.x. 10.164.0.6
    leftid=35.204.200.153
    leftsubnet=0.0.0.0/0
    leftauth=psk
    right=35.204.151.163
    rightid=35.204.151.163
    rightsubnet=0.0.0.0/0
    rightauth=psk
    type=tunnel
    # auto=add - means strongswan won't try to initiate it
    # auto=start - means strongswan will try to establish connection as well
    # Please note that GCP will also try to initiate the connection
    auto=start
    # dpdaction=restart - means strongswan will try to reconnect if Dead Peer Detection spots
    #                  a problem. Change to 'clear' if needed
    dpdaction=restart
    closeaction=restart
    # mark=%unique - We use this to mark VPN-related packets with iptables
    #                %unique ensures that all tunnels will have a unique mark here
    mark=%unique
```

`leftupdown` contains a path to a script and it's command line parameters:
 * First parameter is tunnel ID as you cannot rely on Strongswan's `PLUTO_UNIQUEID` variable if you
 need the tunnel id to be persistent
 * Second parameter specified's GCP's Cloud Router IP and configured subnet.
 * Third parameter specifies IP address that would be on vti0 interface and where Bird is configured.

**Step 3**: Start the Strongswan and BIRD

```
systemctl start bird
systemctl start strongswan
```

After you make sure it's working as expected, you can add bird and strongswan to autostart:
```
systemctl enable bird
systemctl enable strongswan
```