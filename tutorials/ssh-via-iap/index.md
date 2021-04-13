---
title: Restrict SSH connections to virtual machine instances with Identity-Aware Proxy
description: Use Identity-Aware Proxy (IAP) to manage SSH connections to virtual machine instances.
author: erikesouza-google
tags: security, VM
date_published: 2021-03-19
---

Erike Souza | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Learn how to connect from a browser or the Google SDK to a virtual machine (VM) instance without using an external IP address, a bastion host, or network
address translation (NAT).

Creating a virtual machine instance and connecting to it through SSH is a straightforward process in Google Cloud. However, one thing that can make such
connections less secure is to use a firewall configuration that leaves the SSH port publicly exposed. If you manage your instances using SSH through the
Google Cloud Console or `gcloud` commands, you can create a firewall rule that allows access only from Google Cloud Identity-Aware Proxy (IAP) IP address ranges.

1.  [Create a Compute Engine VM instance](https://cloud.google.com/compute/docs/instances/create-start-instance).

1.  [Connect to the VM instance](https://cloud.google.com/compute/docs/ssh-in-browser) using the **SSH** button in the Cloud Console.

    ![SSH button](https://storage.googleapis.com/gcp-community/tutorials/ssh-via-iap/ssh-to-vm.png)

1.  Find the SSH client IP address connected to the instance:

        env | grep SSH_CLIENT

    ![SSH client IP address](https://storage.googleapis.com/gcp-community/tutorials/ssh-via-iap/check-ssh-client.png)

    The client IP address in the SSH connection will be part of the range `35.235.240.0/20`. This range is the pool of IP addresses used by IAP to proxy the
    connection from your browser to your instance. So, you can create a more restrictive VPC firewall rule allowing SSH connections only from this IP address
    range. As a result, only users allowed by IAP will be able to connect to VM using SSH.

1.  If you are using the default VPC network, remove the firewall rule `default-allow-ssh`, and create a new restrictive SSH firewall rule with the 
    settings shown in the following image:

    ![Firewall rule](https://storage.googleapis.com/gcp-community/tutorials/ssh-via-iap/fw-rule-ssh.png)

## What's next

- Learn more about [Identity-Aware Proxy](https://cloud.google.com/iap/docs/using-tcp-forwarding).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
