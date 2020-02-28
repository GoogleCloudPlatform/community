---
title: Set up an Arma 3 server on Compute Engine
description: Learn how to quickly set up an Arma 3 server on Compute Engine.
author: omar2205
tags: Compute Engine, Gaming
date_published: 2020-01-14
---

This tutorial shows how to quickly set up an [Arma 3](https://arma3.com/) server on Compute Engine.

## Before you begin

To set up your server, you need a Google Cloud project. You can use an existing project or
[create a project](https://console.cloud.google.com/project).

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your server needs.

## Create a Compute Engine instance

For this tutorial, you use a custom machine configuration with 2 vCPU cores and 4 GB of RAM.

1.  Go to the Compute Engine [**VM instances**](https://console.cloud.google.com/compute/instances) page.
1.  Click **Create**.
1.  Set the instance name to `arma-server`.
1.  Set **Region** to where you want your server to be.
1.  In the **Machine configuration** section, choose **Custom** from the **Machine type** menu.
1.  Set **Cores** to  2 vCPU, and set **Memory** to 4 GB.
1.  In the **Boot disk** section, click **Change**, and make the following changes on the **Boot disk** page: 
    1.  In the **Public images** section, set **Operating system** to **Ubuntu**, and set **Version** to
    **Ubuntu 18.04 LTS**.
    1.  Set the **Boot disk type** and **Size** values to appropriate values for your setup. The amount of disk space
        required increases with your use of mods (add-ons). For this tutorial, we use 80 GB.
1.  Click **Select** to accept the changes in the **Boot disk** section.
1.  Click **Management, security, disks, networking, sole tenancy** to expand additional sections.
1.  Click the **Networking** tab, and make the following changes in the **Networking** settings:
    1.  Enter `arma-server` in the **Network tags** field. You will apply firewall rules to forward data for the Arma 3
        server's ports with this tag.
    1.  In the **Network interfaces** section, click the pencil icon to edit the network interface settings. 
    1.  In the **External IP** menu, choose **Create IP address**.
    1.  Enter a name for your IP address. For this tutorial, don't change the **Network Service Tier** setting.
    1.  Click **Reserve**.
    1.  In the **Network interface** section, **Done**.
1. Click **Create**.

It takes a few moments to create and start your new instance.

To connect to your virtual machine instance using SSH, click the **SSH** button in the **Connect** column on the
**VM instances** page.

## Add firewall rules

1.  Go to [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) in the **VPC network** 
    section in the Cloud Console.
1.  Click **Create firewall rule**.
1.  On the **Create a firewall rule** page, enter a name and description.
1.  In the **Targets** menu, select **Specified target tags**.
1.  In the **Target tags** field, enter `arma-server` (which is the name that you gave in the **Network tags** field in
    the previous section).
1.  In the **Source IP ranges** field, enter `0.0.0.0/0`.
1.  In the **Protocols and ports** section, select **Specified protocols and ports**.
1.  Select **tcp** and enter the following: `2344,2345`
1.  Select **udp** and enter the following: `2344,2302-2306`
1.  Click **Create**.

## Set up the Arma server

### Install SteamCMD and support utilities

The Arma server depends on the [Steam Console Client (SteamCMD)](https://developer.valvesoftware.com/wiki/SteamCMD), a 
command-line version of the Steam client, from the
[Valve Developer Community](https://developer.valvesoftware.com/wiki/Valve_Developer_Community:About).

SteamCMD requires `lib32gcc1` and `lib32stdc++6` to be installed on your VM instance.

Run the following commands in the VM instance, using the SSH connection that you opened at the end of the procedure to
create the VM instance.
    
1.  Install the support packages:

        $ sudo apt update
        $ sudo apt install lib32gcc1 lib32stdc++6 -y

1.  Install SteamCMD:

        $ mkdir steam && cd steam
        $ wget "http://media.steampowered.com/installer/steamcmd_linux.tar.gz"
        $ tar -xvzf steamcmd_linux.tar.gz
        $ ./steamcmd.sh

1.  Log in to update Steam to the latest version:

        Steam> login anonymous
        
1.  Enter `quit` to exit.

### Install the Arma 3 server

To install the Arma 3 server, you need a Steam account that has Arma 3.

In the following commands, replace [user_name] with your username. You can run `echo $USER` to get your username. Replace 
[steam_username] and [steam_password] with your Steam account details.

    $ mkdir armaserver
    $ cd steam
    $ ./steamcmd.sh
    Steam> login [steam_username] [steam_password]
    Steam> force_install_dir /home/[user_name]/armaserver/
    Steam> app_update 233780 validate
    Steam> exit

### Update the server

To update the server, you repeat many of the installation steps, except for creating the directory:

    $ cd steam
    $ ./steamcmd.sh
    Steam> login [steam_username] [steam_password]
    Steam> force_install_dir /home/[user_name]/armaserver
    Steam> app_update 233780 validate
    Steam> exit

### Start the server

    $ cd armaserver
    $ ./armaserver -name=server -config=server.cfg

For information about the contents of the configuration file, see the
[Arma 3 dedicated server page](https://community.bistudio.com/wiki/Arma_3_Dedicated_Server#Configuration) on the 
Bohemia Interactive wiki.

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete
the project that you created for the tutorial.

1.  In the Cloud Console, go to the [**Projects** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
