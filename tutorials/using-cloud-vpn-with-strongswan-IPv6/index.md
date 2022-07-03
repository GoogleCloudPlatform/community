---
title: How to set up a VPN between strongSwan and Cloud VPN with IPv6
description: Learn how to build a site-to-site IPsec VPN between strongSwan and Cloud VPN.
author: yinghli
tags: Compute Engine, Cloud VPN, strongSwan, BIRD
date_published: 2022-07-03
---


IPv6 is being developed across multiple tracks for GCP. This doc will provides an step-by-step of how IPv6 hybrid connectivity will be enabled for IPSec VPN. This guide walks you through how to configure [strongSwan](https://www.strongswan.org/) and [BIRD](https://bird.network.cz/) for integration with [Google Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview). 

# Environment overview

The equipment used in the creation of this guide is as follows:

* Vendor: strongSwan
* Software release: 5.7.2 on Debian 10

* Vendor: BIRD
* Software release: 2.0.7 on Debian 10

# Topology

The topology outlined by this guide is a basic site-to-site IPsec VPN tunnel
configuration using the referenced device:

![Topology](https://github.com/yinghli/community/blob/master/tutorials/using-cloud-vpn-with-strongswan-IPv6/overview.png)

# Configuring a dynamic (BGP) IPsec VPN tunnel with strongSwan and BIRD

In this example, a dynamic BGP-based VPN uses a VTI interface. This guide is based
on the official [strongSwan wiki](https://wiki.strongswan.org/projects/strongswan/wiki/RouteBasedVPN#VTI-Devices-on-Linux).

The following sample environment walks you through set up of a route-based VPN. Make sure
to replace the IP addresses in the sample environment with your own IP addresses.

This guide assumes that you have [BIRD](https://bird.network.cz/) 2.0.7 installed on your strongSwan server.

**Cloud VPN**

|Name | Value|
-----|------
|Cloud VPN(external IP)|`35.242.38.248`|
|VPC IPv4 CIDR|`172.17.0.0/16`|
|VPC IPv6 CIDR|`2600:2d00:4031:29c6::/64`|
|BGP IPv4 GCP|`169.254.52.201`|
|BGP IPv4 GCP|`2600:2d00:0:3:0:0:0:74b9`|
|GCP-ASN|`65001`|

**strongSwan**

|Name | Value|
-----|------
|External IP|`13.213.47.43`|
|IPv4 CIDR Behind strongSwan|`192.168.100.0/24`|
|IPv6 CIDR Behind strongSwan|`3000::/64`|
|IPv4 TUN-INSIDE- SW|`169.254.52.202`|
|IPv6 TUN-INSIDE- SW|`2600:2d00:0:3:0:0:0:74ba`|
|strongSwan ASN|`65002`|

## Configuration of Google Cloud

With a IPv6 enabled route-based VPN, you need to IKEv2 and dynamic routing. This example uses
dynamic (BGP) routing. [Cloud Router](https://cloud.google.com/network-connectivity/docs/router/) is used to establish
IPv4 BGP sessions between the two peers and exchange both IPv4 and IPv6 unicast address family route.

### Configuring a cloud router

**Step 1**: In the Cloud Console, select **Networking** > [**Cloud Routers**](https://console.cloud.google.com/hybrid/routers/list) > **Create Router**.

**Step 2**: Enter the following parameters, and click **Create**.

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`ipv6cr`|Name of the cloud router.|
|Description| `Support IPv4/IPv6`|Description of the cloud router.|
|Network|`ipv6internal`|The Google Cloud network the cloud router attaches to. This is the network that manages route information.|
|Region|`asia-east1`|The home region of the cloud router. Make sure the cloud router is in the same region as the subnetworks it is connecting to.|
|Google ASN|`65001`|The Autonomous System Number assigned to the cloud router. Use any unused private ASN (64512 - 65534, 4200000000 – 4294967294).|

### Configuring Cloud VPN

**Step 1**: In the Cloud Console, select **Networking** > **Interconnect** > [**VPN**](https://console.cloud.google.com/hybrid/vpn/list) > **CREATE VPN CONNECTION**.

**Step 2**: Enter the following parameters for the Compute Engine VPN gateway:

|Parameter|Value|Description|
|---------|-----------|-----|
|Name|`ipv6vpngw`|Name of the VPN gateway.|
|Description|`VPN tunnel connection between GCP and strongSwan`|Description of the VPN connection.|
|Network|`ipv6internal`| The Google Cloud network the VPN gateway attaches to. This network will get VPN connectivity.|
|Region|`asia-east1`|The home region of the VPN gateway. Make sure the VPN gateway is in the same region as the subnetworks it is connecting to.|
|IP address|`Cloud VPN IPv4 public IP`|The VPN gateway uses the static public IP address. An existing, unused, static public IP address within the project can be assigned, or a new one created.|
|VPN tunnel inner IP stack type|`IPv4 and IPv6 (dual-stack)`|The IP stack type will apply to all the tunnels associated with this VPN gateway.|

**Step 3**: Enter the following parameters for the tunnel:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`tunnel1`|Name of the VPN gateway|
|Description|`VPN tunnel connection between GCP and strongSwan`|Description of the VPN gateway|
|Remote peer IP address| `13.213.47.43`|Public IP address of the on-premises strongSwan.|
|IKE version|`IKEv2`|The IKE protocol version. IPv6 only support with IKEv2.|
|Shared secret|`secret`|A shared secret used for authentication by the VPN gateways. Configure the on-premises VPN gateway tunnel entry with the same shared secret.|
|Routing options|`Dynamic(BGP)`|Multiple routing options for the exchange of route information between the VPN gateways. This example uses static routing.|
|Cloud Router|`ipv6cr`|Select the cloud router you created previously.|
|BGP session| |BGP sessions enable your cloud network and on-premises networks to dynamically exchange routes|

**Step 4**: Enter the parameters as shown in the following table for the BGP peering:

|Parameter|Value|Description|
|---------|-----|-----------|
|Name|`mpbgp`|Name of the BGP session.|
|Peer ASN|`65002`|Unique BGP ASN of the on-premises router.|
|Multiprotocol BGP|`Enable IPv6 traffic`|BGP sessions are set up over IPv4, exchanging IPv4 and IPv6 addresses|
|Google BGP IPv4 address|`Automatically`|In this case, IPv4 is 169.254.52.201 |
|Peer BGP IPv4 address|`Automatically`|In this case, IPv4 is 169.254.52.202 |
|Google BGP IPv6 address|`Automatically`| In this case, IPv6 is 2600:2d00:0:3:0:0:0:74b9 |
|Peer BGP IPv6 address|`Automatically`|In this case, IPv6 is 2600:2d00:0:3:0:0:0:74ba |

Click **Save and Continue** to complete.

**Note**: Add ingress firewall rules to allow inbound network traffic as per your security policy.

## Configuration of strongSwan

This guide assumes that you have strongSwan and BIRD already installed. It also assumes a default layout of Debian 10.

**Step 0**: Configure Loopback Interface to simulate IPv4/IPv6 network. 

Setup Loopback interface `loop1` to simulate IPv4/IPv6 network behind strongSwan. 
    
        ip link add name loop1 type dummy
        ip link set loop1 up
        ip addr add 192.168.100.1/24 dev loop1
        ip -6 addr add 3000::1/64 dev loop1
        
After Loopback infterface setup, `ip addr` show as below.

      7: loop1: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether d2:ce:c2:ef:8f:58 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.1/24 scope global loop1
       valid_lft forever preferred_lft forever
    inet6 3000::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::d0ce:c2ff:feef:8f58/64 scope link
       valid_lft forever preferred_lft forever

**Step 1**: Configure BIRD. Enable IPv4 and IPv6 dual stack. Enable MG-BGP to carry IPv4/IPv6 address family in IPv4 BGP session.

**/etc/bird/bird.conf**
        
        # Config example for bird 2.0
        router id 169.254.52.202;

        ipv4 table master4;
        ipv6 table master6;

        protocol device {
        }

        protocol kernel kernel4 {
          ipv4 {
            export all;
          };
        }

        protocol kernel kernel6 {
          ipv6 {
            import all;
            export all;
          };
        }

        protocol static static4 {
          ipv4;
          route 192.168.100.0/24 via "loop1";
        }

        protocol static static6 {
          ipv6;
          route 3000::/64 via "loop1";
        }

        protocol bgp {
          local 169.254.52.202 as 65002;
          neighbor 169.254.52.201 as 65001;

          # regular IPv4 unicast (1/1)
          ipv4 {
            # connects to master4 table by default
            import all;
            export where source ~ [ RTS_STATIC, RTS_BGP ];
          };

          # regular IPv6 unicast (2/1)
          ipv6 {
            # connects to master6 table by default
            import all;
            export where source ~ [ RTS_STATIC, RTS_BGP ];
            next hop address 2600:2d00:0:3:0:0:0:74ba;
          };

        }

In IPv6 address family configuration, `next hop address` must change to IPv6 address, which assigned by Cloud VPN BGP Session. 

**Step 2**: Disable automatic routes in strongSwan

Routes are handled by BIRD, so you must disable automatic route creation in strongSwan.

**/etc/strongswan.d/vti.conf**

    charon {
        # We will handle routes by ourselves
        install_routes = no
    }

**Step 3**: Create a script that will configure the VTI interface

This script is called every time a new tunnel is established, and it takes care of proper
interface configuration, including MTU, etc.

**/var/lib/strongswan/ipsec-vti.sh**


    #!/bin/bash
    set -o nounset
    set -o errexit

    IP=$(which ip)
    
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

            # If you would like to use VTI for policy-based you shoud take care of routing by yourselv, e.x.
            #if [[ "${PLUTO_PEER_CLIENT}" != "0.0.0.0/0" ]]; then
            #    ${IP} r add "${PLUTO_PEER_CLIENT}" dev "${VTI_IF}"
            #fi
            ;;
        down-client)
            ${IP} tunnel del "${VTI_IF}"
            ;;
    esac

    # Enable IPv4 forwarding
    sysctl -w net.ipv4.ip_forward=1

    # Disable IPSEC Encryption on local net
    sysctl -w net.ipv4.conf.${LOCAL_IF}.disable_xfrm=1
    sysctl -w net.ipv4.conf.${LOCAL_IF}.disable_policy=1


You should also make `/var/lib/strongswan/ipsec-vti.sh` executable by using following command:

    chmod +x /var/lib/strongswan/ipsec-vti.sh

**Step 4**: Configure IPsec credentials
            
Ensure that the following line is in the file:

**/var/lib/strongswan/ipsec.secrets.inc**

    35.242.38.248 : PSK "secret"

**Step 5**: Configure IPsec connection

**/var/lib/strongswan/ipsec.conf.inc**

    include /etc/ipsec.d/gcp.conf

**/etc/ipsec.d/gcp.conf**

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
        leftupdown="/var/lib/strongswan/ipsec-vti.sh 0 169.254.52.201/30 169.254.52.202/30"
        left=172.31.25.241 # In case of NAT set to internal IP, e.x. 172.31.25.241
        leftid=13.213.47.43
        leftsubnet=0.0.0.0/0,::/0
        leftauth=psk
        right=35.242.38.248
        rightid=35.242.38.248
        rightsubnet=0.0.0.0/0,::/0
        rightauth=psk
        type=tunnel
        # auto=add - means strongSwan won't try to initiate it
        # auto=start - means strongSwan will try to establish connection as well
        # Note that Google Cloud will also try to initiate the connection
        auto=start
        # dpdaction=restart - means strongSwan will try to reconnect if Dead Peer Detection spots
        #                  a problem. Change to 'clear' if needed
        dpdaction=restart
        # mark=%unique - We use this to mark VPN-related packets with iptables
        #                %unique ensures that all tunnels will have a unique mark here
        mark=%unique

`leftupdown` contains a path to a script and its command-line parameters:
 * The first parameter is the tunnel ID because you cannot rely on strongSwan's `PLUTO_UNIQUEID` variable if you
 need the tunnel ID to be persistent.
 * The second parameter specifies the Cloud Router IP and configured subnet.
 * The third parameter specifies the IP address of the vti0 interface and where BIRD is configured.

`leftsubnet` and `rightsubnet` must have both IPv4 and IPv6 encryption traffic. `0.0.0.0/0,::/0`

**Step 6**: Check Status

Start strongSwan

    systemctl start strongswan

Check strongSwan with `ipsec statusall`
```
  Listening IP addresses:
    192.168.100.1
    3000::1
    2600:2d00:0:3::74ba
  Connections:
       net-net:  172.31.25.241...35.242.38.248  IKEv2, dpddelay=30s
       net-net:   local:  [13.213.47.43] uses pre-shared key authentication
       net-net:   remote: [35.242.38.248] uses pre-shared key authentication
       net-net:   child:  0.0.0.0/0 ::/0 === 0.0.0.0/0 ::/0 TUNNEL, dpdaction=restart
  Security Associations (1 up, 0 connecting):
       net-net[1]: ESTABLISHED 2 hours ago, 172.31.25.241[13.213.47.43]...35.242.38.248[35.242.38.248]
       net-net[1]: IKEv2 SPIs: 6f1218e3d03e98cb_i* 3226d0dc943bbc75_r, pre-shared key reauthentication in 7 hours
       net-net[1]: IKE proposal: AES_GCM_16_256/PRF_HMAC_SHA2_512/MODP_4096
       net-net{3}:  INSTALLED, TUNNEL, reqid 1, ESP in UDP SPIs: ce6cd2fe_i ce38f979_o
       net-net{3}:  AES_GCM_16_256/MODP_8192, 1651 bytes_i, 1670 bytes_o (27 pkts, 8s ago), rekeying in 2 hours
       net-net{3}:   0.0.0.0/0 ::/0 === 0.0.0.0/0 ::/0
```
Check the VTI interface `vti0` is up and manully configure IPv6 BGP address.

    ip -6 addr add 2600:2d00:0:3:0:0:0:74ba/125 remote 2600:2d00:0:3:0:0:0:74b9/125 dev vti0
    
```
vti0@NONE: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1387 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ipip 172.31.25.241 peer 35.242.38.248
    inet 169.254.52.202 peer 169.254.52.201/30 scope global vti0
       valid_lft forever preferred_lft forever
    inet6 2600:2d00:0:3::74ba peer 2600:2d00:0:3::74b9/125 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::5efe:ac1f:19f1/64 scope link
       valid_lft forever preferred_lft forever
 ```
    
Start BIRD

    systemctl start bird
    
Check with BGP session is Up and support IPv4/IPv6 address family.  
```
bird> show protocols all bgp1
Name       Proto      Table      State  Since         Info
bgp1       BGP        ---        up     12:49:36.779  Established
  BGP state:          Established
    Neighbor address: 169.254.52.201
    Neighbor AS:      65001
    Local AS:         65002
    Neighbor ID:      169.254.217.229
    Local capabilities
      Multiprotocol
        AF announced: ipv4 ipv6
```
Check BGP route is learned and installed in the routing table. 
```
bird> show route
Table master4:
192.168.100.0/24     unicast [static4 12:49:31.804] * (200)
	dev loop1
172.17.0.0/16        unicast [bgp1 12:49:36.826] * (100) [AS65001?]
	via 169.254.52.201 on vti0

Table master6:
3000::/64            unicast [static6 12:49:31.804] * (200)
	dev loop1
2600:2d00:4031:29c6::/64 unicast [bgp1 12:49:36.826 from 169.254.52.201] * (100) [AS65001?]
	via 2600:2d00:0:3::74b9 on vti0
```

In the strongSwan host, check `ip -6 route` table.
```
2600:2d00:0:3::74b9 dev vti0 proto kernel metric 256 pref medium
2600:2d00:0:3::74b8/125 dev vti0 proto kernel metric 256 pref medium
2600:2d00:4031:29c6::/64 via 2600:2d00:0:3::74b9 dev vti0 proto bird metric 32 pref medium
3000::/64 dev loop1 proto bird metric 32 pref medium
```

Initial a ping test from both side and ensure IPv4/IPv6 can communicate with eath other.
