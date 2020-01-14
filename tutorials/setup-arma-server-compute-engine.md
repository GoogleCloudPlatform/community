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

## Add Firewall rules

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

## Set up the Arma server

### Install SteamCMD and Support Utilities
[SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) requires lib32gcc1 and lib32stdc++6 to be installed on your system (vm)

Click the **SSH** button in the **Connect** column on the **VM instances** page to connect to your virtual machine instance using SSH.

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
