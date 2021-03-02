---
title: SSH via IAP
description: IAP is the simple and secure way to manage instance via SSH.
author: erikesouza-google
tags: iap, ssh, 
date_published: 2021-03-02
---

Erike Souza | Community Editor | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Creating an instance in GCP and connecting to it via SSH is really straightforward and secure. But one thing that normally I see in some 
GCP firewall configuration is SSH port open to the world. If you manage your instances using SSH via GCP console or gcloud command 
you can create a firewall rule restricting access only from GCP Identity Aware Proxy IP address range.

# What is the Identity Aware Proxy IP address range?

Create an GCP instance and connect to it using the SSH Button in GCP Console

![SSH button](ssh-to-vm.png?raw=true)


Check the SSH Client Ip address connected to the instance

![SSH client IP Address](check-ssh-client.png?raw=true)


The Client IP address in the SSH connection will be part of the range 35.235.240.0/20. This range is the Pool of IP address used by IAP to proxy the connection 
from your browser to your instance. So, you can create a more restrictive VPC firewall rule allowing SSH only from this IP address range
in consequence only controlled users via IAP will be able to hit SSH port into the VMs via IAP

If you are using the default VPC remove the firewall rule "default-allow-ssh"and create a new restrictive SSH firewall rule.  
![Firewall Rule](fw-rule-ssh.png?raw=true)

