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

## Setup ArmA server













