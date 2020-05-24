---
title: Setting up an Android Development environment on Compute Engine
description: Learn how to set up an Android development environment running on the Compute Engine.
author: Rishit-dagli
tags: Compute Engine
date_published: 2020-05-24
---

This tutorial shows how to set up an [Android Studio](https://developer.android.com/studio) on
Google Cloud Platform (GCP) in just a few minutes. Follow this tutorial to configure
Android Studio development environment on an Ubuntu or Windows server virtual machine instance on Compute Engine with the ability 
to use Android Emulators and accelerate your development.

We will set up a full fledged environment which is fast enough to do Gradle Builds in a second!

## Objectives

* Understand why a straightforward approach does not work.
* Understand nested virtualization in GCP.
* Connecting to a GUI based instance
* Using nested virtualization to test out your apps locally.

## Before you begin

You'll need a GCP project. You can use an existing project or
click the button to create a new project:

**[Create a project](https://console.cloud.google.com/project)**

## Costs

This tutorial uses billable components of GCP, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. New Cloud Platform users might be
eligible for a [free trial](https://cloud.google.com/free-trial).

Here is a prefilled Pricing calculator if you follow this tutorial:
* If you follow along using Linux VMs - [Costs](https://cloud.google.com/products/calculator#id=ca135004-465c-4a43-bc5b-701af07df644)
* If you follow along using Windows VMs - [Costs](https://cloud.google.com/products/calculator#id=eff1ebe1-1ed8-4475-a5f2-d07519fb5883)

## Why the simple approach doesn’t work

If you go on and start trying Android Development environment you might face an error like this while creating the AVD and testing your project-

![](error-with-simple-approach.png)

**HAXM does not support nested virtual machines.**

So, GCP will not provide you the ability to create nested virtual machines. 
It is blocked by default so the Android studio would work but you would not be able to run an AVD, that is not much useful so we will go
on to solve this problem

## How nested virtualization works?

Compute Engine VMs run on top of physical hardware (the host server) which is referred to as the `L0` environment. Within the host 
server, a pre-installed hypervisor allows a single server to host multiple Compute Engine VMs, which are referenced to as `L1` or native 
VMs on Compute Engine. When you use nested virtualization, you install another hypervisor on top of the `L1` guest OS and create nested VMs, referred to as `L2` VMs, using the `L1` hypervisor. `L1` or native Compute Engine VMs that are running a guest hypervisor and
nested VMs can also be referred to as host VMs.

Here is a diagram which might help you get the hang of it-

![](nested-virtualization-diagram.png)

In GCP-

* Nested virtualization can only be enabled for `L1` VMs running on Haswell processors or later. If the default processor for a zone is
Sandy Bridge or Ivy Bridge, you can use minimum CPU selection to choose Haswell or later for a particular instance.
* Nested virtualization is supported only for KVM-based hypervisors running on Linux instances
* Windows VMs do not support nested virtualization, only some Windows OSes support it.

We will also see how to set up a Windows VM as Windows VM require almost no additional setup to get started whereas in a linux instnace 
it might take you some time to get started. Also Linux usually uses VNC whereas Windows has developed RDP for remote connection. Also 
its complicated to have VNC and RDP running on Linux at the same time.

And RDP is undoubtedly better than VNC in performance. But again RDP usually refers to Windows while VNC is universal. You have RDP 
clients for Linux and MAC so there’s no need to worry. We will see both these approaches.

## Creating a Compute Engine Instance

GCP allows nested virtualization on the following VMs but still some setup is required:

* Debian 9 with kernel version 4.9 hosting the following nested VMs:
  + CentOS 6.5 with kernel version 2.6
  + Debian 9 with kernel version 4.9
  + RHEL 5.11 with kernel version 2.6
  + SLES 12 SP3 with kernel version 4.4
  + Ubuntu 16.04 LTS with kernel version 4.15
  + Windows Server 2016 Datacenter Edition
* SLES 12 SP3 with kernel version 4.4 hosting the following nested VMs:
  + SLES 12 SP3 with kernel version 4.4
* Ubuntu 16.04 LTS with kernel version 4.15 hosting the following nested VMs:
  + Ubuntu 16.04 LTS with kernel version 4.15
  
If you have not installed `gcloud` you can follow the steps at [this link](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

1. Make a boot disk

To spin up a Compute Engine Instance you need to create a boot disk. So here's how you would do this in `gcloud`.

```sh
gcloud compute disks create disk1 --image-project debian-cloud --image-family debian-9 --size 100 --zone us-central1-b
```

You are here making a boot disk called `disk1` with image, change it to `Windows Server 2016` if you want to make a Windows Server
instance. The size expects size of the disk in GBs. `100 GB` is good enough for starting out, you could change the value according to
your requirement. So for Windows server use

```sh
gcloud compute disks create disk1 --image-family windows-2016 --image-project gce-uefi-images --size 100 --zone us-central1-b
```

**Note: Your VM Image family should be from the [list](#creating-a-compute-engine-instance) mentioned above **

2. Using the boot disk that you created or a boot disk from an existing instance, create a custom image with the special license key
required for virtualization.

```sh
gcloud compute images create [name_of_image] 
--source-disk disk1 
--source-disk-zone us-central1-b 
--licenses "https://compute.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
```

replace [name_of_image] with a name you like. what you are doing is making a image from that boot disk and applying the license
necessary to allow it to perform nested virtualization.

3. After you create the image with the necessary license, you can delete the source disk if you no longer need it.

4. Create a VM instance using the new custom image with the license. You must create the instance in a zone that supports the `Haswell CPU` Platform or newer.

```sh
gcloud compute instances create [name_of_vm] 
--zone us-central1-b
--min-cpu-platform "Intel Haswell" 
--image [name_of_image]
--custom-cpu = 4 
--custom-memory = 15
```

You are creating a VM instance with the image you just created.
You can edit `custom cpu` and `custom_memory` this is the number of virtual CPUs and the RAM you need. This configuration is good enough
to run Android Studio at a good enough speed.
If you made a `Windows` instance you are done, you will now just have to test it out so head on to [Connecting to Instance section](#connecting-to-instance).
This is because GCP sets up a connection stream and a good desktop GUI needed for Android Studio only for Windows instances.

## Configuring your Instance

**Note: This step is ponly required for Linux Instances. For Windows Instances head on to [Connecting to Instance section](#connecting-to-instance).**

You now need to do is create a desktop environment and make a connection channel so you can connect to your VM with that desktop 
environment. You would need to do so as you need a GUI interface to use Android Studio.

1. Make a desktop environment

You can use `gnome`, `xfce` etc. There are so many options but for this tutorial we will use `xfce` which takes minimal time to
download. SSH in your Instance and enter the following commands-

```sh
sudo apt-get install lxde
```

You will be asked with some options, select “Yes”.

2. Setting Up Instance to connect to it

This command installs tight VNC server which will help us establish a VNC connection.

```sh
sudo apt-get install tightvncserver
```

3. Set up a firewall rule

Navigate to `VNC network > Firewall rules`
We need to do this as we want to allow `vnc server` to access port `5901`. Choose a name and target tag for it, set allowed protocols to
`tcp:5901`.

Now navigate to `VM instances > edit VM > Networking`

Add the target tag in the network tag textbox. You might need to stop the Instance to do this.

4. One last step

Navigate to `.vnc/xtsrtup` and open in this in your favourate text editor maybe `vim`, `nano` or some other. Add `/usr/bin/startlxde` at
it’s end. This will tell VNC to render `lxde` desktop at startup.

## Connecting to Instance

1. Linux

Let us first see whta the process would be if you were on a Linuzx instance.

SSH in your VM instance and type

```
vncserver
```

to start a `vncserver` session. Use a VNC viewer like [RealVNC](https://www.realvnc.com/en/connect/download/vnc/) or [Tight VNC](https://www.tightvnc.com/download.php) viewer.

Your VNC Viewer might look something like this-

![](vnc-client.png)

Enter the external IP of your VM followed by `:5901` to tell it to view port `5901`. 
And you are now done with connecting to a desktop environment.

2. Windows

You first need to make a firewall rule to allow RDP in your instance. Go to `VNC networks > Firewall` . Click create a firewall rule and
add `tcp:3389` in protoccols and ports section give a name and target tag to the firewall rule. Save it and come back to VM instances
page. Navigate to `edit VM > Network tags` add the target tag you just typed while creating the firewall rule.

The next step depends on the Local OS you have.

Your local OS-

* Windows — You are ready to connect without any more setup

Open the `Remote Desktop Connection` app preinstalled, it can also be excecuted by running `mstsc.exe`.

* Any other OS — install a RDP client like

  + For MAC — Download the [Microsoft Remote Desktop client](https://itunes.apple.com/app/microsoft-remote-desktop/id1295203466?mt=12) from the Mac App Store or [Cord](http://cord.sourceforge.net/).

  + For linux — [FreeRDP](http://freerdp.com/) or [Remmina](http://remmina.org/)
  
You are now ready to connect to your VM Instance. In GCP console click on `set windows password` , make a new account and save the 
password generated by GCP somewhere you remember.

Now enter your external IP of VM in your RDP client, it will ask you for `username` and `password` enter the credentials and you would have connected to your VM Instance. You should see a standard Windows GUI.

## Downloading Android Studio

Now that you have connected to your desktop GUI, let us go on and install Android Studio.

* Open the [official download URL](https://developer.android.com/studio) from the browser inside of your Instance
* Once you install Android Studio on your VM, navigate to AVD Manager in Android Studio on the top bar
* Create aa new AVD Device, with the configurations you like, the steps remain same!

And now you are all ready to start building on your Android Studio, here's a visual proof of the first Gradle build happening in almost 
just a second-

![](1-second-build.jpeg)

## Troubleshooting

1. `dev\kvm permission denied` (Linux Instances only)

* Install `qemu-kvm`.

```sh
sudo apt install qemu-kvm
```

* Use the `adduser` command to add your user to the `kvm` group.

```sh
sudo adduser <username> kvm
```

2. AVD does not start

* Edit Virtual Device
* Advanced options
* Heap size > Change to 512 MB or more

3. No Graphics rendered on AVD (GPU users only)

* `edit AVD > Graphics rendering > Software`
* Edit Virtual Device
* Advanced options
* Heap size > Change to 512 MB or more

## Cleaning up

After you've finished the Settin Up Android Development Environment on Commpute Engine tutorial, you can clean up the resources you
created on Google Cloud Platform so you won't be billed for them in the future. The following sections describe how to delete or turn 
off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Platform Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain
available.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Platform Console, go to the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the checkbox next to the instance you created.
1. Click the Delete button at the top of the page to delete the instance.

### Deleting firewall rules for the default network

To delete a firewall rule:

1. In the Cloud Platform Console, go to the **[Firewall Rules](https://console.cloud.google.com/networking/firewalls)** page.
1. Click the checkbox next to the firewall rule you want to delete.
1. Click the Delete button at the top of the page to delete the firewall rule.

## Next Steps

To know mmore about nested virtualization you could read [Nested Virtualization Docs](https://cloud.google.com/compute/docs/instances/enable-nested-virtualization-vm-instances)
