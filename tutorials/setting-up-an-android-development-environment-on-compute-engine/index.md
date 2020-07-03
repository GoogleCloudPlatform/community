---
title: Set up an Android development environment on Compute Engine
description: Learn how to set up an Android development environment running on Compute Engine.
author: Rishit-dagli
tags: Compute Engine
date_published: 2020-07-06
---

This tutorial shows how to set up [Android Studio](https://developer.android.com/studio) on Google Cloud in just a few minutes. Follow this tutorial to configure
an Android Studio development environment on an Ubuntu or Windows Server virtual machine (VM) instance on Compute Engine with the ability to use the Android 
Emulator and accelerate your development. This setup creates a full-fledged environment that can do Gradle builds in as little as a second.

## Objectives

* Understand why a straightforward approach does not work.
* Understand nested virtualization in Google Cloud.
* Connect to a GUI-based instance.
* Use nested virtualization to test your apps.

## Before you begin

To follow the steps in this tutorial, you need a Google Cloud project. You can use an existing project or
[create a new project](https://console.cloud.google.com/project).

You run the commands in this tutorial using the `gcloud` command-line tool. To install the Google Cloud SDK, which includes the `gcloud` tool, follow 
[these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage. New Google Cloud
users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Why the simple approach doesn’t work

If you have tried to use the Android development environment without following the steps in this tutorial, you might have encountered an error like the following
while creating the AVD and testing your project: "HAXM doesn't support nested virtual machines."

![](https://storage.googleapis.com/gcp-community/tutorials/setting-up-an-android-development-environment-on-compute-engine/error-with-simple-approach.png)

By default, Google Cloud blocks the ability to create nested virtual machines, so Android Studio runs, but you can't run an AVD using the emulator. This
tutorial shows how to solve this problem, using nested virtualization.

For details of how nested virtualization works and what restrictions exist for nested virtualization, see 
[Enabling nested virtualization for VM instances](https://cloud.google.com/compute/docs/instances/enable-nested-virtualization-vm-instances#how_nested_virtualization_works).

## Create a Compute Engine instance

1.  Make a boot disk:

        gcloud compute disks create disk1 --image-project debian-cloud --image-family debian-9 --size 100 --zone us-central1-b

    This command makes a boot disk called `disk1` with a Debian Linux image. If you want to make a Windows Server instance, for example, you can change the 
    parameters as follows:

        gcloud compute disks create disk1 --image-family windows-2016 --image-project gce-uefi-images --size 100 --zone us-central1-b

    The VM image family must be from [this list](https://cloud.google.com/compute/docs/instances/enable-nested-virtualization-vm-instances#tested_os_versions).

1.  Create a custom image with the special license key required for virtualization, replacing `[NAME_OF_IMAGE]` with any name that you like:

        gcloud compute images create [NAME_OF_IMAGE] 
        --source-disk disk1 
        --source-disk-zone us-central1-b 
        --licenses "https://compute.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"

     This command creates an image from the boot disk and applies the license necessary to allow nested virtualization.

1.  Delete the source disk if you no longer need it.

1.  Create a VM instance using the new custom image with the license.

        gcloud compute instances create [NAME_OF_VM] 
        --zone us-central1-b
        --min-cpu-platform "Intel Haswell" 
        --image [NAME_OF_IMAGE]
        --custom-cpu = 4 
        --custom-memory = 15

    This command creates a VM instance with the image you just created. You can change the `custom-cpu` and `custom-memory` values, but the values given here are 
    enough to run Android Studio.

If you made a Windows instance, then you are done with this setup, and you should continue to the "Connecting to an instance" section below. This is because
Google Cloud sets up a connection stream and desktop (graphical user interface) GUI needed for Android Studio for Windows instances.

If you made a Linux instance, then you need to complete the steps in the next section.

## Configure the instance (Linux only)

You need a graphical user interface to use Android Studio, which is not set up by default for Linux instances. In this section, you create a desktop environment 
and make a connection channel so that you can connect to your VM with that desktop environment. You can use GNOME, Xfce, or any of a large number of options.
This tutorial uses LXDE, because it takes little time to download. 

1.  Connect to your instance using SSH.

1.  Install LXDE:

        sudo apt-get install lxde

    Follow the instructions and agree to the questions to install the package.

1.  Install TightVNC Server, is used to establish a VNC connection:

        sudo apt-get install tightvncserver

1.  Set up a firewall rule to allow the VNC server to access port 5901:

    1.  Navigate to **VNC network** > **Firewall rules**.
    1.  Choose a name and target tag for the firewall rule, and set allowed protocols to `tcp:5901`.
    1.  Navigate to **VM instances** > **Edit VM** > **Networking**.
    1.  Add the target tag in the network tag textbox. You might need to stop the instance to do this.

1.  Open `.vnc/xtsrtup` in a text editor and add `/usr/bin/startlxde` at the end of the file. This tells VNC to render the LXDE desktop at startup.

## Connect to an instance

This document shows approaches using VNC and RDP for remote connection. Linux typically uses VNC, whereas RDP is typically limited to Windows. Generally, RDP 
performs better than VNC, but VNC has the advantage of being universal. RDP clients exist for Linux and macOS. It can be complicated to have VNC and RDP running 
on Linux at the same time.

1. Linux

Let us first see whta the process would be if you were on a Linuzx instance.

SSH in your VM instance and type

```
vncserver
```

to start a `vncserver` session. Use a VNC viewer like [RealVNC](https://www.realvnc.com/en/connect/download/vnc/) or [Tight VNC](https://www.tightvnc.com/download.php) viewer.

Your VNC Viewer might look something like this-

![](https://storage.googleapis.com/gcp-community/tutorials/setting-up-an-android-development-environment-on-compute-engine/vnc-client.png)

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

## Download and install Android Studio

1.  Go to the [Android Studio download page](https://developer.android.com/studio) from the browser inside your instance.
1.  Follow the instructions to install Android Studio on your VM.
1.  Follow [these instructions](https://developer.android.com/studio/run/managing-avds#createavd) to create a new AVD configured however you like.

You're ready to start building with Android Studio. 

Here's an indication of the first Gradle build happening in just over a second when the author used this setup:

![](https://storage.googleapis.com/gcp-community/tutorials/setting-up-an-android-development-environment-on-compute-engine/1-second-build.jpeg)

## Troubleshooting

### Permission denied message

If you get a `dev\kvm permission denied` message for a Linux instance, do the following:

1.  Install `qemu-kvm`:
    
        sudo apt install qemu-kvm
                
1.  Add your user to the `kvm` group:

        sudo adduser [USERNAME] kvm

### AVD doesn't start

If your AVD doesn't start, [edit your advanced AVD settings](https://developer.android.com/studio/run/managing-avds#workingavd) to increase the heap size to
512 MB or more.

### Graphics aren't rendered on AVD

If graphics aren't rendered on the AVD when you are using the GPU,
[edit your AVD settings](https://developer.android.com/studio/run/managing-avds#workingavd) to switch the **Emulated Performance** setting to **Software**.

## Cleaning up

After you've finished the tutorial, you can clean up the resources that you created on Google Cloud so that you won't be billed for them in the future. The 
following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

**Warning**: If you used an existing project, deleting a project also deletes any other work that you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead; this ensures that URLs that use the project ID, such as an `appspot.com` URL, remain
available.

To delete the project:

1. In the Cloud Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

### Deleting instances

To delete a Compute Engine instance, do the following:

1. In the Cloud Console, go to the **[VM instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the checkbox next to the instance that you created.
1. Click the **Delete** button at the top of the page to delete the instance.

### Deleting firewall rules for the default network

To delete a firewall rule, do the following:

1. In the Cloud Console, go to the **[Firewall rules](https://console.cloud.google.com/networking/firewalls)** page.
1. Click the checkbox next to the firewall rule that you want to delete.
1. Click the **Delete** button at the top of the page to delete the firewall rule.

## Next steps

To learn more about nested virtualization, read
[Enabling nested virtualization for VM instances](https://cloud.google.com/compute/docs/instances/enable-nested-virtualization-vm-instances).
