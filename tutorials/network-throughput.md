---
title: Calculating Network Throughput
description: How to measure and troubleshoot Network Throughput in GCP
author: dcavalheiro
tags: Cloud Networking
datePublished: 2019-08-01
---

# Network Throughput

This page describes how to calculate network throughput both within GCP, and to your on-premises or 3rd-party cloud location; including how to analyse the
results, different variables that can affect the network performance, and a troubleshooting section at the end of the document.

## Common use cases

Dimensioning your applications and machine types for optimal network throughput is essential for balancing costs and networking performance. Here are the common use cases for a network throughput assessment:

* VM to VM (inside a [VPC](https://cloud.google.com/vpc) on the same zone, same region or different regions).
* VM to VM (different VPCs via [VPC Peering](https://cloud.google.com/vpc/docs/vpc-peering) or [Cloud VPN](https://cloud.google.com/vpn/docs/concepts/overview)).
* VM to On-premises (by using any of our [hybrid connectivity](https://cloud.google.com/hybrid-connectivity/) products).

## Know your tools

When calculating network throughput, it's important to use well-tested, well-documented tools:

* [iPerf/iPerf3](https://iperf.fr/) - is a commonly-used network testing tool that can create TCP/UDP data streams (single or multi-thread) and measure the throughput of the network that carries them.
* [Traceroute](https://en.wikipedia.org/wiki/Traceroute) is a computer network   diagnostic tool that measures and displays the routes that packets take across a network. Traceroute records the route's history as the round-trip times of packets received from each successive host in a route. The sum of the mean times in each hop is an approximate measure of the total time spent to establish the TCP connection.
* [TCPDump](https://en.wikipedia.org/wiki/Tcpdump) - is a command-line-based packet analyser that captures packet details and TCP/IP communications for more advanced troubleshooting. TCPDump is compatible with multiple other tools, such as [Wireshark](https://www.wireshark.org/).
* [TCP throughput calculator](https://www.switch.ch/network/tools/tcp_throughput/) - An interesting calculator on the [Switch Foundation website](https://www.switch.ch/about/foundation/) that measures theoretical network limits based on the [TCP window](https://tools.ietf.org/html/rfc1323#page-8) and [RTT](https://en.wikipedia.org/wiki/Round-trip_delay_time).
* [PerfKitBenchMarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker) - A tool that contains a set of benchmarks to measure and compare cloud offerings. The benchmarks use defaults to reflect what most users will see.

## Round Trip Time, Latency and Distances

When analyzing performance, one of the most common misconceptions is to measure data transfer speed without considering the distance between network endpoints.
This type of analysis is highly dependent on external factors, such as latency and distance.

For example, the speed of light traveling in a vacuum is around 300,000 km/s, but when using fiber-optic cable, which the internet is based on, the speed of light decreases by a factor of ~1.52. This reduces the total speed to an aproximatey 197,300 km/s.

Another important concept is that the distance between two Virtual Machines (VMs) isn't normally a straight line, but is, instead, a complex maze of connections increasing the total linear distance traveled. For example, the distance between New York City and Los Angeles is almost 3,944 km in a straight line, but driving can increase this value to a minimum of 4.466 km.

Due to [Bandwidth-delay product](https://en.wikipedia.org/wiki/Bandwidth-delay_product), even connections with large bandwidth capabilities will perform poorly when tested via TCP, since their [TCP Window](https://en.wikipedia.org/wiki/TCP_tuning#Window_size) may not allow for full link utilization.

For these reasons, choosing the closest distance from your on-premises location to the closest [GCP Cloud location](https://cloud.google.com/about/locations/) is the best approach to reduce latency.

You can also use [GCPing](http://www.gcping.com/), a third-party website that provides the median latencies from your on-premises location to different GCP regions.

## Egress per virtual machine limit (all network interfaces)

To choose the best egress bandwidth cap for your application, you can refer to [this reference](https://cloud.google.com/vpc/docs/quota#per_instance) which describes the maximum egress data rate per instance.

### Single-thread and multi-thread connection modes

Another important concept is the use of single or parallel threads when sending data over a network connection. For example, a machine's CPU can process network requests over a single or over multiple processor threads. Multi-connection, multi-thread, or parallel thread mode gives you maximum potential speed by using multiple CPU threads in parallel to send network packets.

For example, if you sequentially download a single file from start to end, you use a single thread, but when you download many smaller files, or break a large file into small chunks and download them at the same time, each thread is responsible for each file or chunk.

Because the maximum egress data rate is a *limit*, it is possible to achieve values close to this limit using multi-thread mode. However, even under ideal conditions the data rate will not go over this maximum egress limit.

Single connection mode is best for testing over a VPN (non HA) or simulating the download of a single file. Expect it to have lower transfer speeds than multi-thread mode.

### Measuring throughput with iPerf3:

Follow this procedure to measure throughput from the perspective of a single VM from any referred use cases.

#### Choose the right machine type

To perform throughput tests, it is recommended to use a large machine type such as n1-standard-8. This will provide a maximum egress throughput limit of 16Gb/s, thus the per-VM egress throughput will not interfere with the tests.

#### Install tcpdump and iPerf3

Install tcpdump and iPerf3 on a Linux VM machine. For example, to install both pieces of software on Debian or Ubuntu systems, run:

<pre class="devsite-click-to-copy">
sudo apt-get update
sudo apt-get install tcpdump
sudo apt-get install iperf3
</pre>

#### Run an iPerf3 server

Run iPerf3 server (-s flag). The server will accept connections on both the VM's internal and (if configured) external IP address. Unless you configure it with a custom port, the server will listen on port 5201 for both TCP and UDP traffic. To change the port, use the -p flag.:

<pre class="devsite-click-to-copy">
iperf3 -s -p <var>PORT_NUMBER</var>
</pre>

#### Allow the server and client communication through the GCP firewall

Create a firewall rule to the iPerf3 server to allow ingress TCP on the selected port, as in the [following example](https://cloud.google.com/vpc/docs/using-firewalls#creating_firewall_rules).

#### Run an iPerf3 client
Run iPerf3 with the -c (client flag) and specify the destination IP address of the iPerf3 server. By default, iPerf3 uses TCP, unless you specify the -u (UDP flag) in the client, no such flag is needed server-side for UDP. However, a firewall rule allowing incoming UDP traffic to the server is required.

If you run the server on a custom port, you'll need to specify that same port using the -p flag. Omitting the port, the client assumes destination port is 5201.

Use the -P (Parallel threads flag) to specify a number of simultaneous threads,and the -t (time flag) to specify the duration of the test, in seconds.

<pre class="devsite-click-to-copy">
iperf3 -c <var>VM_IP</var> -P <var>THREADS</var> -p <var>PORT_NUMBER</var> -t <var>DURATION</var> -R
</pre>

#### Capturing packets

On either the iperf3 client or server, it's sometimes helpful to get packet captures. The following example command shows you how to capture full packets for a given destination port range from an eth0 interface, saving a file in the working directory called mycap.pcap.

Important: Using -s (snaplen flag) with a value of 0 tcpdump will capture entire packets, just be aware that the packet captures could have sensitive information. Most tcpdump implementations interpret -s 0 to be the same as -s 262144. See the [tcpdump manpage](https://www.tcpdump.org/manpages/tcpdump.1.html) for details.

To reduce the chances of capturing sensitive information, you can capture just packet headers by providing a lower snaplen value (such as `-s 100`).

<pre class="devsite-click-to-copy">
sudo /usr/sbin/tcpdump -s 100 -i eth0 dst port <var>PORT_NUMBER</var> -w mycap.pcap
</pre>

You'll have to modify this command to suit the use case; for example, the interface name isn't always eth0 on all distributions, and you'll need to specifically choose the right interface for a [Multiple Network Interfaces VM](https://cloud.google.com/vpc/docs/multiple-interfaces-concepts).

### Measuring VPC network throughput with PerfKitBenchMarker

To measure network throughput performance from a given machine type in a specific zone, [PerfKitBenchMarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker) will be the right tool.

This option is very valuable because it creates an instance and measures its performance, without the need to install the tools on an existing VM. To use this tool, you just need to run the following commands, where:


+ `[MACHINE_TYPE]` is the machine type you want to test (for example,
   n1-standard-32).
+ `[ZONE]` is the zone to create the instance in.
+ `[NUMBER_OF_VCPUS]` is the number of vCPUs of the instance (for example, 32
   for n1-standard-32 machine type).

**To measure single thread performance:**

<pre class="devsite-click-to-copy">
    ./pkb.py --cloud=GCP --machine_type=<var>MACHINE_TYPE</var>
    --benchmarks=iperf --ip_addresses=INTERNAL --zones=<var>ZONE</var>
</pre>

**To measure multi-thread performance:**

<pre class="devsite-click-to-copy">
    ./pkb.py --cloud=GCP --machine_type=,<var>MACHINE_TYPE</var>
    --benchmarks=iperf --ip_addresses=INTERNAL --zones=<var>ZONE</var>
    --iperf_sending_thread_count=<var>NUMBER_OF_VCPUS</var>
</pre>

### Speed test

To measure network data transfer speed from a VM to the global Internet, there are a number of available tools.

* Using a browser with [speedtest.net](https://speedtest.net/)
* Using a browser with [fast.com](https://fast.com)
* Using this [Python utility](https://github.com/sindresorhus/speed-test)
  for command line-only machines.

## Troubleshooting

Capturing and analysing network throughput data is the most important step, but there are some common scenarios that require some extra investigation.

**iPerf3 server and client are not able to establish a connection:**

1. Verify the firewall rules allowing ingress and egress traffic to the VM on your VPC.
2. If using multiple VPCs, the firewall must allow traffic on the selected port for all VPCs.
3. Selecting the nic0 of the Instance will open a console page with the breakdown of the firewall rules and route that affect this specific Instance, very valuable source of information.

**TCP Window size and RTT not optimized:**

If you are not able to realize your full connection bandwidth over a TCP connection, the cause may be TCP send and receive windows.
This [video](https://www.youtube.com/watch?time_continue=5&v=iqEpoi00_Ws) explains this behavior, and you can use this [calculator](https://www.switch.ch/network/tools/tcp_throughput/) to understand the impact of window size on your connection bandwidth.

To fix this issue you may increase send and receive windows by raising the following:

`SO_RCVBUF` influenced by increasing these settings:

`net.core.rmem_default`

`net.core.rmem_max`

`SO_SNDBUF` influenced by increasing these settings:

`net.core.wmem_default`

`net.core.wmem_max`

{% endblock %}
