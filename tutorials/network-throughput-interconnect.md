# Calculating network throughput over Cloud Interconnect

## Objectives

This document describes how to calculate network throughput, both within Google Cloud and to your on-premises or third-party cloud locations, connected using Cloud Interconnect. This document includes information on how to analyze results, explanations of variables that can affect network performance, and troubleshooting tips.

## Limitations

-  Cloud Interconnect limitations apply. For more information, see [Cloud Interconnect Quotas](https://cloud.google.com/network-connectivity/docs/interconnect/quotas#limits).
-  CPU/NIC limits: Google Cloud accounts for bandwidth per virtual machine (VM) instance, not per network interface (NIC) or IP address. A VM's machine type defines its maximum possible egress rate; however, that can only be achieved in specific situations. See this [table](https://cloud.google.com/compute/docs/machine-types#machine_type_comparison) for the number of vCPUs per machine type.
-  Other devices in the path (Firewall, switches w/ small buffers, vendors)
   -  CPU/Network stats on firewalls, and switches in the path
   -  For Cloud Interconnect testing, it's best to bypass as many devices as possible between the on-premises host and the PF. 
   -  All devices in the path between on-premises and GCP VM should be identified and investigated as the source of throughput issues.

## Know your tools

When calculating network throughput, it's important to use well-tested, well-documented tools:

[iPerf3](https://iperf.fr/): A commonly used network testing tool that can create TCP/UDP data streams (single-thread or multi-thread) and measure the throughput of the network that carries them.

**Note**: iPerf3 may only be appropriate for single-CPU machines.

[Netperf](https://hewlettpackard.github.io/netperf/): Similar to iPerf3 but more appropriate for throughput testing on multi-CPU instances that are CPU-bound on a single CPU.

[tcpdump](https://en.wikipedia.org/wiki/Tcpdump): A command-line packet analyzer that captures packet details and TCP/IP communications for more advanced troubleshooting. tcpdump is compatible with other tools, such as Wireshark.

[Netstat](https://en.wikipedia.org/wiki/Netstat): A command-line network utility that displays network connections for Transmission Control Protocol (both incoming and outgoing), routing tables, and a number of network interface (network interface controller or software-defined network interface) and network protocol statistics.

## Measuring throughput with iPerf3

Follow this procedure to measure throughput from the perspective of a single virtual machine.

### Choose a large machine type

To perform throughput tests, we recommend that you use a large machine type, such as n1-standard-8. This machine type provides a maximum egress throughput limit of 16 Gbps, so the per-VM egress throughput will not interfere with the tests.

### Install the tools

Install iPerf3, mtr, netstat, and tcpdump on a Linux VM machine.

Run the following commands, according to the distro versions:

<table>
<thead>
<tr>
<th><p><pre>
Debian based distros:
sudo apt-get update
sudo apt-get install iperf3 tcpdump mtr netstat
<br>
Redhat based distros:
yum update
yum install iperf3 tcpdump mtr netstat
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Install netperf (only needs to compile from source to enable demo option)

<table>
<thead>
<tr>
<th><p><pre>
Debian based distros:
sudo apt-get install git build-essential autoconf texinfo -y
git clone https://github.com/HewlettPackard/netperf.git
cd netperf
./autogen.sh
./configure --enable-histogram --enable-demo=yes
make
cp src/netserver ~/.local/bin
cp src/netperf ~/.local/bin
<br>
Redhat based distros:
sudo yum install git build-essential autoconf texinfo -y
git clone https://github.com/HewlettPackard/netperf.git
cd netperf
./autogen.sh
./configure --enable-histogram --enable-demo=yes
make
cp src/netserver ~/.local/bin
cp src/netperf ~/.local/bin
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### Run the prerequisite tests

1. Make sure the VLAN Attachment sizes are configured correctly.
1. On both ends of the connection, perform the following step:
   1. On each terminal, start **top/htop** to monitor CPU usage.  

1. Collect netstat before running any tests.

```
netstat -s >> netstat.log
```

1. On another terminal, run **tcpdump** before any capture with a snaplen of 128.

   It should be run on both the endpoints.

```
sudo /usr/sbin/tcpdump -s 128 -i [DEVICE_INTERFACE] host [IP_ADDRESS of remote side] -w mycap.pcap
```

1. Get the read/write memory size on source and destination hosts.

```
$ sysctl net.ipv4.tcp_rmem
$ sysctl net.ipv4.tcp_wmem
$ sysctl net.core.rmem_max
$ sysctl net.core.rmem_default
$ net.core.wmem_max
$ net.core.wmem_default
$ uname -r
$ cat /etc/os-release
```

1. Get the port details on the PF interface before and after you run the iperf test.  Check for an increase in input errors, CRC, frame, overrun, ignored and abort alert. Make sure the packet count also matches with the throughput during the test.

<table>
<thead>
<tr>
<th>$ show int <interface name> detail<br>
<br>
.<br>
.<br>
.<br>
  MTU 1518 bytes, BW 10000000 Kbit (Max: 10000000 Kbit)<br>
     reliability 255/255, txload 0/255, rxload 0/255<br>
  Encapsulation ARPA,<br>
  Full-duplex, 10000Mb/s, LR, link type is force-up<br>
  output flow control is off, input flow control is off<br>
  Carrier delay (up) is 3000 msec<br>
  loopback set (Internal),<br>
  Last link flapped 7w5d<br>
  Last input 00:00:00, output 00:00:00<br>
  Last clearing of "show interface" counters never<br>
  30 second input rate 1936000 bits/sec, 3872 packets/sec<br>
  30 second output rate 1936000 bits/sec, 3872 packets/sec<br>
     9168717360 packets input, 573048314602 bytes, 0 total input drops<br>
     0 drops for unrecognized upper-level protocol<br>
     Received 6 broadcast packets, 156674 multicast packets<br>
              0 runts, 0 giants, 0 throttles, 0 parity<br>
     <strong>0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored, 0 abort</strong><br>
     9168717356 packets output, 573048314484 bytes, 0 total output drops<br>
     Output 6 broadcast packets, 156674 multicast packets<br>
     0 output errors, 0 underruns, 0 applique, 0 resets<br>
     0 output buffer failures, 0 output buffers swapped out<br>
     1 carrier transitions<br>
<br>
</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### Run the iperf3 tests

Due to the per Bandwidth limitation of 3 Gbit/s per flow, it is recommended to run multiple parallel streams of iperf3 tests. Make sure you run a minimum of 4 tests and ideally 10 tests.   
   
On another terminal, run **iperf3** server on one end of the connection (a VM, or an on-premise machine): Multiple streams will require multiple **iperf3** servers.

The iperf tool should be run with an udp flag for Interconnect testing. If the desired throughput with UDP is achieved, the issue must be elsewhere and further steps must be taken to troubleshoot. 

##### 

<table>
<thead>
<tr>
<th><p><pre>
Multiple iperf3 servers from Command line:
UDP
Command Line:
$ iperf3 -s -u -p 5101&; iperf3 -s -u -t 30 -p 5102&; iperf3 -s -u -p 5103 &
<br>
Bash script to run iperf3 servers:
#!/bin/bash
#start iperf3 server running in background
<br>
for i in `seq 0 9`;
do
        iperf3 -s  -B 10.0.100.35 -t 30 -u -p 521$i &
done
<br>
TCP
Command Line:
$ iperf3 -s -p 5101&; iperf3 -s -t 30 -p 5102&; iperf3 -s -p 5103 &
<br>
Bash script to run iperf3 servers:
#!/bin/bash
#start iperf3 server running in background
<br>
for i in `seq 0 9`;
do
        iperf3 -s  -B 10.0.100.35 -t 30 -p 521$i &
done
</pre></p>

</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

The **iperf3 client** runs for 10s by default which may not be enough for TCP to ramp up to reach the maximum possible throughput. Set DURATION to at least 30s to achieve more reliable results. 

```
iperf3 -c [server IP address] -P [THREADS] -t [DURATION]
```

While iperf3 is running, monitor the CPU load on both the devices. If the CPU load is close to 100%, CPU is a bottleneck for one iperf3 thread. Then, switch to using Netperf as Netperf supports multiple CPUs.

If that is not possible, a workaround is to start multiple iperf3 servers and clients on different terminals and different ports at the same time.

### Analyze the test results

Perform the following steps.

1. Check iperf3 client results for bandwidth and packet loss.
1. Check iperf3 server for any out of order packets.
1. Packet capture analysis: Run the following command to get the total of packets and out of order packets.

<table>
<thead>
<tr>
<th>grep -e "Total" -A1 <pcap filename><br>
<br>
gcpvm-send-5210.txt:<strong>Total</strong> UDP packets:  874032<br>
gcpvm-send-5210.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5211.txt:<strong>Total</strong> UDP packets:  791218<br>
gcpvm-send-5211.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5212.txt:<strong>Total</strong> UDP packets:  961510<br>
gcpvm-send-5212.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5213.txt:<strong>Total</strong> UDP packets:  961517<br>
gcpvm-send-5213.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5214.txt:<strong>Total</strong> UDP packets:  961501<br>
gcpvm-send-5214.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5215.txt:<strong>Total</strong> UDP packets:  961521<br>
gcpvm-send-5215.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5216.txt:<strong>Total</strong> UDP packets:  889932<br>
gcpvm-send-5216.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5217.txt:<strong>Total</strong> UDP packets:  961483<br>
gcpvm-send-5217.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5218.txt:<strong>Total</strong> UDP packets:  961479<br>
gcpvm-send-5218.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
gcpvm-send-5219.txt:<strong>Total</strong> UDP packets:  961518<br>
gcpvm-send-5219.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 0<br>
<br>
<strong>The below analysis shows packet loss during a perf test:</strong><br>
$ grep -e "Total" -A1 onPrem-send-*.txt <br>
onPrem-send-5210.txt:<strong>Total</strong> UDP packets:  858698<br>
onPrem-send-5210.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5408<br>
--<br>
onPrem-send-5211.txt:<strong>Total</strong> UDP packets:  857667<br>
onPrem-send-5211.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 4929<br>
--<br>
onPrem-send-5212.txt:<strong>Total</strong> UDP packets:  857126<br>
onPrem-send-5212.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5349<br>
--<br>
onPrem-send-5213.txt:<strong>Total</strong> UDP packets:  857424<br>
onPrem-send-5213.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5495<br>
--<br>
onPrem-send-5214.txt:<strong>Total</strong> UDP packets:  857139<br>
onPrem-send-5214.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 4692<br>
--<br>
onPrem-send-5215.txt:<strong>Total</strong> UDP packets:  857175<br>
onPrem-send-5215.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 4789<br>
--<br>
onPrem-send-5216.txt:<strong>Total</strong> UDP packets:  857104<br>
onPrem-send-5216.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5196<br>
--<br>
onPrem-send-5217.txt:<strong>Total</strong> UDP packets:  857122<br>
onPrem-send-5217.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5423<br>
--<br>
onPrem-send-5218.txt:<strong>Total</strong> UDP packets:  857383<br>
onPrem-send-5218.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 5283<br>
--<br>
onPrem-send-5219.txt:<strong>Total</strong> UDP packets:  857313<br>
onPrem-send-5219.txt:<strong>Total</strong> out-of-order packets: 0, missing packets: 4934<br>
</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

1. Run the following command to check the port throughput:

   `go/device/<device name>` 

1. If there are errors on the PF interface, inform the Cloud Interconnect team.
1. If Netstat output shows read/write errors, TCP/UDP bulk flow tuning may be required.
1. If there are out of order packets, the packet captures should be performed in the VPN Gateways with the help of TSE for further analysis.  
1. If the iperf3 UDP test achieves the desired throughput, the issue must be elsewhere and TCP tuning may be required. See go/tcp-bulk-flow-testing for further considerations. 