---
title: Calculating network throughput
description: How to measure and troubleshoot network throughput in Google Cloud.
author: dcavalheiro,bernieongewe
tags: Cloud Networking
date_published: 2019-08-07
---

This document describes how to calculate network throughput, both within Google Cloud and to your on-premises or third-party 
cloud locations. This document includes information on how to analyze results, explanations of variables that can affect 
network performance, and troubleshooting tips.

## Common use cases

Choosing and configuring your applications and machine types for optimal network throughput is essential for balancing costs 
and networking performance.

Here are the common use cases for a network throughput assessment:

* VM to VM in the same [VPC network](https://cloud.google.com/vpc), whether in the same zone or in different regions or
  zones.
* VM to VM in different VPC networks using [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering)
  or [Cloud VPN](https://cloud.google.com/vpn/docs/concepts/overview).
* VM to on-premises, using any of the Google Cloud [hybrid connectivity](https://cloud.google.com/hybrid-connectivity/) 
  products.

## Know your tools

When calculating network throughput, it's important to use well-tested, well-documented tools:

* [iPerf3](https://iperf.fr/): A commonly used network testing tool that can
  create TCP/UDP data streams (single-thread or multi-thread) and measure the
  throughput of the network that carries them.
  
  **Note**: iPerf3 may only be appropriate for single-CPU machines.
  
* [Netperf](https://hewlettpackard.github.io/netperf/): Similar to iPerf3 but
  more appropriate for throughput testing on multi-CPU instances that are
  CPU-bound on a single CPU.
* [`traceroute`](https://en.wikipedia.org/wiki/Traceroute): A computer network diagnostic tool that measures and displays 
  the routes that packets take across a network. The `traceroute` tool records the route's history as the round-trip times 
  of packets received from each successive host in a route. The sum of the mean times in each hop is an approximate measure 
  of the total time spent to establish the TCP connection.
* [`tcpdump`](https://en.wikipedia.org/wiki/Tcpdump): A command-line packet analyzer that captures packet details and
  TCP/IP communications for more advanced troubleshooting. `tcpdump` is compatible with other tools, such as 
  [Wireshark](https://www.wireshark.org/).
* [TCP throughput calculator](https://www.switch.ch/network/tools/tcp_throughput/): A calculator on the
  [SWITCH Foundation website](https://www.switch.ch/about/foundation/) that measures theoretical network limits based on the
  [TCP window](https://tools.ietf.org/html/rfc1323#page-8) and [RTT](https://en.wikipedia.org/wiki/Round-trip_delay_time).
* [Perfkit Benchmarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker): A tool that contains a set of benchmarks 
  to measure and compare cloud offerings. The benchmarks use defaults to reflect what most users will see.
* [`gcping`](https://github.com/googlecloudplatform/gcping): A command-line tool that provides median latencies to Google 
  Cloud regions.  

## Round-trip time, latency, and distances

When analyzing network performance, one of the most common mistakes is to measure data transfer speed without considering 
the characteristics of the network or the actual distance between network endpoints. Network performance analysis is highly 
dependent on factors such as latency and distance. You need to consider these real-world characteristics, and not rely on
simple assumptions.

For example, the speed of light traveling in a vacuum is around 300,000 km/s, but the speed of light through the fiber-optic
cable that makes up most of the internet is approximatey 200,000 km/s.

Another important consideration is that the distance between two virtual machines (VMs) isn't normally a straight line, but
is instead a complex maze of connections, increasing the total distance traveled. This is analogous to the fact that the
distance between New York City and Los Angeles is almost 3,944 km in a straight line, but driving on roads increases this 
value to at least 4,466 km.

Because of the [bandwidth-delay product](https://en.wikipedia.org/wiki/Bandwidth-delay_product), even connections with large 
bandwidth capabilities will perform poorly when tested via TCP, since their
[TCP window](https://en.wikipedia.org/wiki/TCP_tuning#Window_size) may not allow for full link utilization.

Choosing the closest [Google Cloud location](https://cloud.google.com/about/locations/) to your on-premises location is the
best approach to reduce latency.

You can use the [`gcping`](https://github.com/googlecloudplatform/gcping) command-line tool to determine median latencies
from any location to various Google Cloud regions.

## Egress per virtual machine limit (all network interfaces)

To choose the best egress bandwidth cap for your application, refer to the 
[per-instance VPC resource limits](https://cloud.google.com/vpc/docs/quota#per_instance) for the maximum egress data rate.

### Single-thread and multi-thread connection modes

Another important concept is the use of single or parallel threads when sending data over a network connection. For example,
a machine's CPU can process network requests over a single or over multiple processor threads. Multi-connection, 
multi-thread, or parallel-thread mode gives you maximum potential speed by using multiple CPU threads in parallel to send 
network packets.

For example, if you sequentially download a single file from start to end, you use a single thread, but when you download
many smaller files, or break a large file into small chunks and download them at the same time, each thread is responsible
for each file or chunk.

It is possible to achieve values close to the maximum egress data rate using multi-thread mode. However, because the maximum
egress data rate is a *limit*, the data rate will not go over the maximum egress data rate, even under ideal conditions.

Single-connection mode is best for testing over a VPN (non-HA) or simulating the download of a single file. Expect it to 
have lower transfer speeds than multi-thread mode.

### Measuring throughput with iPerf3

Follow this procedure to measure throughput from the perspective of a single virtual machine.

#### Choose a large machine type

To perform throughput tests, we recommend that you use a large machine type, such as n1-standard-8. This machine type
provides a maximum egress throughput limit of 16 Gbps, so the per-VM egress throughput will not interfere with the tests.

#### Install tcpdump and iPerf3

Install `tcpdump` and iPerf3 on a Linux VM machine.

To install both pieces of software on a Debian or Ubuntu system, run the following commands:

    sudo apt-get update
    sudo apt-get install tcpdump
    sudo apt-get install iperf3

#### Run an iPerf3 server

The iPerf3 server accepts connections on both the VM's internal address and (if configured) its external IP address.
By default, the server listens on port 5201 for both TCP and UDP traffic. To change the port, use the `-p` flag.

    iperf3 -s -p [PORT_NUMBER]
    
The `-s` flag tells iPerf3 to run as a server. 

#### Allow the server and client communication through the Google Cloud firewall

Create a firewall rule to the iPerf3 server to allow ingress TCP on the selected port, as described in 
[Creating firewall rules](https://cloud.google.com/vpc/docs/using-firewalls#creating_firewall_rules).

#### Run an iPerf3 client

Run iPerf3 with the `-c` (client) flag and specify the destination IP address of the iPerf3 server. By default, iPerf3 uses 
TCP, unless you specify the `-u` (UDP) flag for the client. No such flag is needed server-side for UDP; however, a firewall
rule allowing incoming UDP traffic to the server is required.

If you run the server on a custom port, you need to specify that same port using the `-p` (port) flag. If you omit the 
port flag, the client assumes that the destination port is 5201.

Use the `-P` (parallel threads) flag to specify a number of simultaneous threads, and use the `-t` (time) flag to specify 
the duration of the test, in seconds.

    iperf3 -c [VM_IP] -P [THREADS] -p [PORT_NUMBER] -t [DURATION] -R

#### Capturing packets

It's sometimes helpful to get packet captures on the iPerf3 client or server. The following example command shows you how to
capture full packets for a given destination port range from an `eth0` interface, saving a file in the working directory 
called `mycap.pcap`.

    sudo /usr/sbin/tcpdump -s 100 -i eth0 dst port [PORT_NUMBER] -w mycap.pcap

**Important**: If you use the `-s` (snapshot length) flag with a value of `0`, then `tcpdump` will capture entire packets. 
Be aware that the packet captures can contain sensitive information. Most `tcpdump` implementations interpret `-s 0` to be 
the same as `-s 262144`. See the [tcpdump man page](https://www.tcpdump.org/manpages/tcpdump.1.html) for details. To reduce 
the chances of capturing sensitive information, you can capture just packet headers by providing a lower snapshot length 
value, such as `-s 100`.

Modify this command to suit your use case; for example, the interface name isn't always `eth0` on all
distributions, and you'll need to specifically choose the right interface for a
[multiple network interface VM](https://cloud.google.com/vpc/docs/multiple-interfaces-concepts).

#### Limitations of using iPerf3

CPU throttling is likely to be a bottleneck when testing with `iperf3`. The `-P` flag launches multiple client streams, but
these all run in a single thread.

From the `iperf3` man pages:

    > -P, --parallel n \
    > number of parallel client streams to run. Note that iperf3 is single threaded,
    > so if you are CPU bound, this will not yield higher throughput.

Also, any attempt to launch multiple clients returns the following complaint on the second attempt:

    $ iperf3 -c 10.150.0.12 -t 3600 \
    iperf3: error - the server is busy running a test. try again later

Allowing only a single process to run is [also by design choice](https://github.com/esnet/iperf/issues/140).

To exercise multiple CPUs, use Netperf.

### Measuring throughput with multiple CPUs with Netperf

Install Netperf:

    sudo apt-get install git build-essential autoconf texinfo -y
    git clone https://github.com/HewlettPackard/netperf.git
    cd netperf
    ./autogen.sh
    ./configure --enable-histogram --enable-demo=yes
    make

Start the server:

    src/netserver

Start the client:

    src/netperf -D $reporting_interval -H $server_ip -f $reporting_units

The following is an example command to run the Netperf client:

    src/netperf -D 2 -H 10.150.0.12 -f G

The following is an example of output from Netperf:

    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 10.150.0.12
    \
    () port 0 AF_INET : histogram : demo Interim result: 1.66 GBytes/s over 2.444
    \
    seconds ending at 1582948175.660 Interim result: 1.81 GBytes/s over 2.008 \
    seconds ending at 1582948177.669 Interim result: 1.81 GBytes/s over 2.000 \
    seconds ending at 1582948179.669 Interim result: 1.81 GBytes/s over 2.001 \
    seconds ending at 1582948181.670 Interim result: 1.80 GBytes/s over 1.546 \
    seconds ending at 1582948183.216 Recv Send Send Socket Socket Message Elapsed
    \
    Size Size Size Time Throughput bytes bytes bytes secs. GBytes/sec \
    \
    87380 16384 16384 10.00 1.77

You can then start multiple clients, assigning them to different CPUs. The example below starts 10 processes and assigns
them to the respective CPUs:

    for i in {1..10}
    do
    taskset -c $i src/netperf -D 2 -H [server_IP_address] -f G &
    done

### Measuring VPC network throughput with PerfKit Benchmarker

To measure network throughput performance from a given machine type in a specific zone, use
[PerfKit Benchmarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker). This tool is valuable because it creates 
an instance and measures its performance, without the need to install the tools on an existing VM.

Replace the placeholders in the commands below with the following:

+ `[MACHINE_TYPE]`: The machine type that you want to test (for example, n1-standard-32).
+ `[ZONE]`: The zone to create the instance in.
+ `[NUMBER_OF_VCPUS]`: The number of vCPUs of the instance (for example, 32 for the n1-standard-32 machine type).

Measure single-thread performance:

    ./pkb.py --cloud=GCP --machine_type=[MACHINE_TYPE]
    --benchmarks=iperf --ip_addresses=INTERNAL --zones=[ZONE]

Measure multi-thread performance:

    ./pkb.py --cloud=GCP --machine_type=,[MACHINE_TYPE]
    --benchmarks=iperf --ip_addresses=INTERNAL --zones=[ZONE]
    --iperf_sending_thread_count=[NUMBER_OF_VCPUS]

### Speed test

To measure network data transfer speed from a VM to the global internet, you can choose from many available tools, including
the following:

* [Speedtest website](https://speedtest.net/), provided by Ookla.
* [FAST.com website](https://fast.com), provided by Netflix.
* [speed-test Python utility](https://github.com/sindresorhus/speed-test), for when you need a command-line interface.

## Troubleshooting

This section includes tips for investigating and troubleshooting some common issues that may occur when measuring 
network throughput.

### iPerf3 server and client are not able to establish a connection

1. Verify that the firewall rules allow ingress and egress traffic to and from the VM on your VPC.
2. If using multiple VPCs, the firewall must allow traffic on the selected port for all VPCs.
3. Selecting the nic0 of the instance will open a console page with the breakdown of the firewall rules and route that 
   affect this specific instance, which is a very valuable source of information.

### TCP window size and RTT not optimized

If you are not able to realize your full connection bandwidth over a TCP connection, the cause may be TCP send and receive 
windows. For an explanation of this behavior, see
[this video on the bandwidth delay problem](https://www.youtube.com/watch?time_continue=5&v=iqEpoi00_Ws). You can use
the [TCP throughput calculator](https://www.switch.ch/network/tools/tcp_throughput/) to understand the impact of window size
on your connection bandwidth.

To fix this issue, you may increase the TCP send and receive windows:

- `SO_RCVBUF` is influenced by increasing `net.core.rmem_default` and `net.core.rmem_max`.
- `SO_SNDBUF` is influenced by increasing `net.core.wmem_default` and `net.core.wmem_max`.
