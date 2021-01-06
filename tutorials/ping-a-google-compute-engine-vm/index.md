---
title: Ping a Compute Engine virtual machine
description: Send a ping to a virtual machine using its domain name or IP address.
author: gpriester
tags: Compute Engine, Cloud DNS
date_published: 2019-04-24
---

Geoffrey Priester | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Pinging](https://en.wikipedia.org/wiki/Ping_(networking_utility)) is a common method of testing the reachability of a
host (like a virtual machine) from an external network.

Sending a *ping* to a host entails sending an ICMP packet to the target and waiting for a response. A ping also provides
a measure of the round-trip time between a client and host.

Pinging is also a handy utility to check the DNS resolution of a domain name you may have configured using Cloud DNS.

## Obtain the domain name or virtual machine IP address

### Locate the domain name

1. To locate a domain name (or hostname) that you've configured, open
[Cloud DNS](https://console.cloud.google.com/net-services/dns/zones) in the Cloud Console.

2. Select a zone that you have previously configured. The zone's DNS name (e.g., `examplepetstore.com`) can be used for
pinging/DNS resolution.

### Locate the IP address

1. To locate the external IP address of a virtual machine, open the
[Compute Engine instances page](https://console.cloud.google.com/compute/instances) in the Cloud Console.

2. Identify the virtual machine that you want to ping. Copy the IP address listed under the **External IP** column in the
table.

## Ping from a Windows client

On Microsoft Windows clients (e.g., a desktop running Windows 10), you ping with the Command Prompt application. To ping a 
hostname (e.g., `example.com`), perform the following steps:

1.  Open a command prompt by opening the **Start** menu and typing `cmd`.

2.  Type `ping example.com`, replacing `example.com` with your domain name, and press **Enter**. You should see results 
    similar to the following:

        Microsoft Windows [Version 10.0.17134.706]
        (c) 2018 Microsoft Corporation. All rights reserved.

        C:\Users\username>ping example.com

        Pinging example.com [93.184.216.34] with 32 bytes of data:
        Reply from 93.184.216.34: bytes=32 time=12ms TTL=56
        Reply from 93.184.216.34: bytes=32 time=11ms TTL=56
        Reply from 93.184.216.34: bytes=32 time=11ms TTL=56
        Reply from 93.184.216.34: bytes=32 time=11ms TTL=56

        Ping statistics for 93.184.216.34:
          Packets: Sent = 4, Received =4, Lost = 0 (0% loss),
        Approximate round trip times in milli-seconds:
          Minimum = 11ms, Maximum = 12ms, Average = 11ms

The IP address associated with the domain name you enter is written in brackets.

To ping an IP address instead, replace the domain name in the command with the IP address. For example:

    ping 93.184.216.34

## Ping from a macOS client

On macOS clients (e.g., iMac, MacBook), you ping with the Terminal application. To ping a hostname (e.g., `example.com`),
perform the following steps:

1.  Press **Command+Space** to open Spotlight Search, type `Terminal` and press **Enter**.

2.  Type `ping example.com`, replacing `example.com` with your domain name, and press **Enter**. You should see results 
    similar to the following:

        mycomputer:~ username$ ping example.com
        PING example.com (93.184.216.34): 56 data bytes
        64 bytes from 93.184.216.34: icmp_seq=0 ttl=56 time=7.471 ms
        64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=4.647 ms
        64 bytes from 93.184.216.34: icmp_seq=2 ttl=56 time=3.545 ms
        64 bytes from 93.184.216.34: icmp_seq=3 ttl=56 time=3.389 ms

        --- example.com ping statistics ---
        4 packets transmitted, 4 packets received, 0.0% packet loss
        round-trip min/avg/max/stddev = 2.315/3.881/7.471/1.371 ms

On macOS, the ping command will continue to run until you close the Terminal window or stop the ping application by pressing
**Ctrl+C**.

The IP address associated with the domain name you enter is written in parentheses.

To ping an IP address instead, replace the domain name in the command with the IP address. For example:

    ping 93.184.216.34
