---
title: Set up an Arma 3 server on Compute Engine
description: Learn how to quickly set up an Arma 3 server on Compute Engine.
author: omar2205
tags: Compute Engine, Gaming
date_published: 2020-01-10
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
1.  In the **Machine configuration** section, choose **Custom** from the **Machine Type** menu.
1.  Set **Cores** to  2 vCPU, and set **Memory** to 4 GB.
1.  In the **Boot disk** section, click **Change**, and make the following changes on the **Boot disk** page: 
    1. In the **Public images** section, set **Operating system** to **Ubuntu**, and set **Version** to
    **Ubuntu 18.04 LTS**.
    1. Change **Boot disk type** to your needs (Increase the size according to your use of mods), We will pick 80 GB.
1. in the **Firewall** section click **Management, security, disks, networking, sole tenancy**
   1. Switch to **Networking** tab, and enter `arma-server` in **Network tags** input (We are going to apply firewall rules to port forward ArmA 3 server's required ports by targeting this all the VMs with this specific tag) 
   1. In the **Network interfaces** click the pen icon and in the **External IP** dropbox change it from Ephemeral to Create IP address.
   1. Enter a name for our IP address, for this tutorial we aren't going to worry about Network Service Tier.
   1. Click **RESERVE**.
   1. Click **Done**
1. Click **Create**


It will take a few moments to create and boot up your new instance.

once your instance have been created click the **SSH** button under the Connect column in your VM instances page and you will ssh to your vm.

# Add Firewall rules
1. Open VPN network then Firewall rules or click here: https://console.cloud.google.com/networking/firewalls/list
1. Click **Create Firewall Rule**
1. Add Name, and Description.
1. Edit **Targets**
   1. Make sure **Specified target tags** is selected
   1. Add `arma-server` to **Target tags**
   1. **Source IP ranges** add `0.0.0.0/0`
1. **Protocols and ports**
   1. Make sure **Specified protocols and ports** is selecte
   1. in the tcp add the following: `2344,2345`
   1. in the udp add the following: `2344,2302-2306`
1. Click **Create**

## Setup ArmA server

### Install SteamCMD and Support Utilities
[SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) requires lib32gcc1 and lib32stdc++6 to be installed on your system (vm)
``` bash
$ sudo apt update
$ sudo apt install lib32gcc1 lib32stdc++6 -y
```

Now we are going to make a steam dir and go inside it to download and install SteamCMD
``` bash
$ mkdir steam && cd steam
$ wget "http://media.steampowered.com/installer/steamcmd_linux.tar.gz"
$ tar -xvzf steamcmd_linux.tar.gz
$ ./steamcmd.sh
```
After steam gets installed, Login to update steam to the latest version.
```
Steam> login anonymous
```
After that you can exit by typing `quit`

### Installing Arma 3 Server
We are going to need a steam account which owns arma 3.
``` bash
$ mkdir armaserver
$ cd steam
$ ./steamcmd.sh
Steam> login <steam_username> <steam_password>
Steam> force_install_dir /home/<user_name>/armaserver/
Steam> app_update 233780 validate
Steam> exit
```
Make sure to replace <user_name> with your user name (run `echo $USER` to get it) and <steam_username> and <steam_password> with the account's details.

### Updating the serveer
To update the server you will redo this process again:
``` bash
$ cd steam
$ ./steamcmd.sh
Steam> login <steam_username> <steam_password>
Steam> force_install_dir /home/<user_name>/armaserver
Steam> app_update 233780 validate
Steam> exit
```


To launch the server
``` bash
$ cd armaserver
$ ./armaserver -name=server -config=server.cfg
```

Please follow this BI's wiki for more info

https://community.bistudio.com/wiki/Arma_3_Dedicated_Server#Configuration
