---
title: Set up an OpenVPN server on Compute Engine
description: Learn how to quickly set up OpenVPN Access Server on Compute Engine.
author: incapio
tags: Compute Engine, VPC
date_published: 2021-11-11
---
<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial shows how to quickly set up an [OpenVPN](https://openvpn.net/access-server/) Access Server on Compute Engine
## Before you begin

To set up your server, you need a Google Cloud project. You can use an existing project or
[create a project](https://console.cloud.google.com/project).

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your server needs.

## Create a Compute Engine instance

For this tutorial, you use a custom machine configuration with 2 vCPU cores and 2 GB of RAM.

1.  Go to the Compute Engine [**VM instances**](https://console.cloud.google.com/compute/instances) page.
1.  Click **Create**.
1.  Set the instance name to `openvpn-as`.
1.  Set **Region** to where you want your server to be.
1.  In the **Machine configuration** section, choose **Custom** from the **Machine type** menu.
1.  Set **Cores** to  2 vCPU, and set **Memory** to 2 GB.
1.  In the **Boot disk** section, click **Change**, and make the following changes on the **Boot disk** page: 
    1.  In the **Public images** section, set **Operating system** to **Ubuntu**, and set **Version** to
    **Ubuntu 20.04 LTS**.
    1.  Set the **Boot disk type** and **Size** values to appropriate values for your setup. For this tutorial, we use 10 GB.
1.  Click **Select** to accept the changes in the **Boot disk** section.
1.  Click **Management, security, disks, networking, sole tenancy** to expand additional sections.
1.  Click the **Networking** tab, and make the following changes in the **Networking** settings:
    1.  Enter `op-firewall` in the **Network tags** field. You will apply firewall rules to forward data for the OpenVPN
        server's ports with this tag.
    1.  Enter `vpn.example.com` in the **Hostname** field. Set a custom hostname for this instance or leave it default. 
    2.  In the **IP Forwarding** field, check **Enable**.
    3.  In the **Network interfaces** section, click the pencil icon to edit the network interface settings. 
    4.  In the **External IP** menu, choose **Create IP address**.
    5.  Enter a name for your IP address. For this tutorial, don't change the **Network Service Tier** setting.
    6.  Click **Reserve**.
    7.  In the **Network interface** section, **Done**.
1. Click **Create**.

It takes a few moments to create and start your new instance.

To connect to your virtual machine instance using SSH, click the **SSH** button in the **Connect** column on the
**VM instances** page.

## Add Ingress firewall rules

1.  Go to [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) in the **VPC network** 
    section in the Cloud Console.
1.  Click **Create firewall rule**.
1.  On the **Create a firewall rule** page, enter a name and description.
2.  3.  In the **Targets** menu, select **Specified target tags**.
4.  In the **Target tags** field, enter `op-firewall` (which is the name that you gave in the **Network tags** field in
    the previous section).
1.  In the **Source IP ranges** field, enter `0.0.0.0/0`.
1.  In the **Protocols and ports** section, select **Specified protocols and ports**.
1.  Select **tcp** and enter the following: `tcp:443,943,22,945`
1.  Select **udp** and enter the following: `1194`
1.  Click **Create**.

## Add Egress firewall rules

1.  Go to [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) in the **VPC network** 
    section in the Cloud Console.
1.  Click **Create firewall rule**.
1.  On the **Create a firewall rule** page, enter a name and description.
2.  In the **Direction of Traffic**, choose **Egress**. 
3.  In the **Targets** menu, select **Specified target tags**.
4.  In the **Target tags** field, enter `op-firewall` (which is the name that you gave in the **Network tags** field in
    the previous section).
1.  In the **Destination IP ranges** field, enter `0.0.0.0/0`.
1.  In the **Protocols and ports** section, select **Allow all**.
1.  Click **Create**.

## Set up the OpenVPN Access Server

Run the following commands in the VM instance, using the SSH connection that you opened at the end of the procedure to
create the VM instance.
    
1.  Install the support packages:

        apt update && apt -y install ca-certificates wget net-tools gnupg
        wget -qO - https://as-repository.openvpn.net/as-repo-public.gpg | apt-key add -
        echo "deb http://as-repository.openvpn.net/as/debian focal main">/etc/apt/sources.list.d/openvpn-as-repo.list
        
2.  Install the OpenVPN Access Server:

        apt update && apt -y install openvpn-as
        
3.  Log in to OpenVPN Access Server Administration:

        https://[vm-external-ip]:943/admin 
        or 
        https://[vm-external-ip]/admin
        
4.  Log in to OpenVPN client:

        https://[vm-external-ip]?src=connect        
        
        
## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete
the project that you created for the tutorial.

1.  In the Cloud Console, go to the [**Projects** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
