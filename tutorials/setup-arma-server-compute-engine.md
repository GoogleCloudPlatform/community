---
title: How to quickly setup an ArmA 3 Server
description: Set up an ArmA 3 Server on Compute Engine.
author: omar2205
tags: Compute Engine, Gaming
date_published: 2019-12-29
---

# Introduction

This tutorial shows how to quickly set up an [ArmA 3](https://arma3.com/) server on Google Compute Engine (CE).

## Before you begin

You'll need a GCP project. You can use an existing project or
click the button to create a new project:

**[Create a project](https://console.cloud.google.com/project)**


## Costs

This tutorial uses billable components of GCP, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your server needs.


## Creating a Compute Engine instance
We are going to use a custom machine configuration, meaning we are going to choose our server specs. We are goin to use 2vCPU (Cores) and 4 GB (Ram).

1. Open Compute Engine then Choose VM Instances (If it's not chosen be default)
1. Click **Create instance** button.
1. Set Name to `arma-server`.
1. In the **Region** section Choose where you want your server to be.
1. In the **Machine configuration** section, We are going to choose a custom **Machine Type** and manually enter or move the slider to pick: 2vCPU and 4GB Ram.
1. In the **Boot disk** section: 
   1. Click **Change** and Select **Public Images** and pick **Operating system** as **Ubuntu** and the version to be `Ubuntu 18.04 LTS`
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
