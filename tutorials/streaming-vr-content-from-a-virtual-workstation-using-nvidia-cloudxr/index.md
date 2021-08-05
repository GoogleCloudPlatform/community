---
title: Stream virtual reality content from a virtual workstation using NVIDIA CloudXR
description: Learn how to deploy, install, and test NVIDIA CloudXR on a virtual workstation on Google Cloud.
author: adrian-a-graham
tags: vr, ar, cloudxr, nvidia, virtual workstation, gpu
date_published: 2021-08-05
---

Adrian Graham | Cloud Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to stream virtual reality (VR) content from a virtual workstation on Google Cloud to a tetherless head-mounted display (HMD) such as
the Oculus&nbsp;Quest&nbsp;2.

NVIDIA CloudXR is supported on a variety of [HMDs](https://developer.nvidia.com/nvidia-cloudxr-sdk#:~:text=NATIVELY%20SUPPORTED%20HMDs). This tutorial provides 
instructions only for the [Oculus Quest 2](https://www.oculus.com/quest-2/). Where indicated, refer to the
[CloudXR SDK documentation](https://docs.nvidia.com/cloudxr-sdk/index.html) for instructions for other HMDs and devices.

## Objectives

+ Create a virtual workstation running Windows Server 2019.
+ Install SteamVR and NVIDIA CloudXR on the workstation.
+ Load the CloudXR client on a virtual reality head-mounted display (HMD).
+ Connect to the virtual workstation through the CloudXR client.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

+   [Compute Engine](https://cloud.google.com/compute), including vCPUs, memory, disk, and GPUs
+   [Internet egress](https://cloud.google.com/vpc/network-pricing) for streaming data to your HMD

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

In this section, you set up some basic resources that the tutorial depends on.

1.  Open [Cloud Shell](https://cloud.google.com/shell/docs/starting-cloud-shell).

    Instructions in this tutorial assume that you run commands in Cloud Shell, which is a
    command-line interface in the Cloud Console that has the Cloud SDK installed. If you prefer, you can install the
    [Google Cloud SDK](https://cloud.google.com/sdk/docs) on your local computer and run commands there.

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  [Enable the Compute Engine API.](https://console.cloud.google.com/flows/enableapi?apiid=compute_component)
1.  Make sure that your project has quota for [virtual workstation GPUs](https://cloud.google.com/compute/docs/gpus#gpu-virtual-workstations) in your selected
    [zone](https://cloud.google.com/compute/docs/gpus#gpus-list). You can check GPU availability with the following command:
    
        gcloud compute accelerator-types list
1.  Confirm that your project contains a [default network](https://cloud.google.com/vpc/docs/vpc#default-network).

    If you've [disabled the creation of default networks](https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints) in your 
    organization, then you must manually create an auto-mode VPC network named `default`.
1.  Make sure that you have access to the [NVIDIA CloudXR SDK](https://developer.nvidia.com/nvidia-cloudxr-sdk). You can register for a free account at 
    [developer.nvidia.com](https://developer.nvidia.com/).

## Set up the virtual workstation

In this section, you create and configure a virtual workstation, including setting up networking and installing utilities. 

### Create the virtual workstation

In this section, you create a virtual workstation by starting with a configuration from the Google Cloud Marketplace and modifying some of its default settings.

1.  Go to the [NVIDIA RTX Virtual Workstation - Windows Server 2019](https://console.cloud.google.com/marketplace/product/nvidia/nvidia-quadro-vws-win2019)
    page in the Google Cloud Marketplace.

1.  Click **Launch**.

    If prompted to enable additional APIs, click **Enable**.

    By default, this virtual workstation configuration creates an instance with 8 vCPUs, 30 GB of RAM, and a 50 GB boot disk.
    
1.  Set the following values to better accommodate the CloudXR workload:

    1.  For **Zone**, choose a zone with the lowest latency to your location.
    
        You can use [GCP ping](https://gcping.com/) to determine the median latency to Google Cloud regions.
        
        GPU availability is limited to certain zones. Google Cloud Marketplace only lists zones where the NVIDIA T4 GPU is available.

    1.  Set **Machine type** to **Custom**.
    1.  Increase **Cores** to 12.
    1.  Increase **Memory** to 64 GB.
    1.  For faster disk performance, change **Boot disk type** to **SSD Persistent Disk**.
    1.  Change the **Boot disk size in GB** value to **200** to increase disk performance and allow for more downloaded content.

1.  Note the value in the **Deployment name** field; you use this in the next section, when setting up network access.
1.  Click **Deploy**.

### Add a firewall rule and network tags

In this section, you create a firewall rule to allow access to the virtual workstation instance from your local workstation. CloudXR also requires
other ports for remote access. This firewall rule allows access only from your public IP address.

1.  Determine your local workstation's public IP address by going to [ifconfig.me](https://ifconfig.me/) in a web browser.
1.  In Cloud Shell, run the following command to create a firewall rule, replacing `[PUBLIC-IP]` with your local workstation's public IP address:

        gcloud compute firewall-rules create allow-cloudxr \  
          --direction=INGRESS \  
          --priority=1000 \  
          --network=default \  
          --action=ALLOW \  
          --rules=tcp:3389,tcp:5900,tcp:47998-48000,tcp:48002,tcp:48005,tcp:48010,udp:47998-48000,udp:48002,udp:48005,udp:48010 \  
          --source-ranges=[PUBLIC-IP] \  
          --target-tags=allow-cloudxr

1.  Allow traffic to your workstation by adding a network tag to the instance:  

        gcloud compute instances add-tags [NAME] \  
          --tags=allow-cloudxr \  
          --zone=[ZONE]
 
    Replace `[NAME]` with the name of your virtual workstation instance, and replace `[ZONE]` with your virtual workstation's zone.

## Set up the connection to your workstation

In this section, you connect to your instance using Microsoft Remote Desktop Protocol (RDP), install an alternative remote desktop utility, disconnect from
RDP, and reconnect using the alternative remote desktop utility. Because of a
[limitation](https://steamcommunity.com/app/250820/discussions/0/3264459260617027967/) in SteamVR, CloudXR connections show a solid green display if connected 
through Microsoft RDP.

### Create a default Windows password and connect to your virtual workstation

1.  Create a Windows password for your user with the following
    [`gcloud` command](https://cloud.google.com/compute/docs/instances/windows/creating-passwords-for-windows-instances#gcloud):  
  
        gcloud compute reset-windows-password [NAME] --zone=[ZONE]

    Replace `[NAME]` with the name of your workstation, and replace `[ZONE]` with your workstation's zone.

    You can also create a password with the
    [Cloud Console](https://cloud.google.com/compute/docs/instances/windows/creating-passwords-for-windows-instances#console).
  
1.  Using an RDP client, log in to your workstation using the credentials returned by the previous command.

### Install Chrome

Install Google Chrome on the VM instance:

1.  In your RDP session, launch PowerShell.
1.  At the prompt, enable HTTPS requests:  

        [Net.ServicePointManager]::SecurityProtocol = "tls12, tls11, tls"

1.  Download the Chrome installer:  

        $Installer = $env:TEMP + "\chrome_installer.exe";
            Invoke-WebRequest
            "http://dl.google.com/chrome/install/latest/chrome_installer.exe" -OutFile
            $Installer

1.  Run the Google Chrome installer:  
  
        Start-Process -FilePath $Installer -Args "/silent /install" -Verb RunAs -Wait

    When you are prompted, allow the installer to make changes.

1.  Remove the installer:  

        Remove-Item $Installer

### Install TightVNC or other VNC utility

In this section, you install an alternative remote desktop utility, such as Chrome Remote Desktop, Teradici PCoIP, or any variant of VNC. This tutorial uses
[TightVNC](https://www.tightvnc.com/), which is freely available and open source.

1.  Launch Google Chrome on your virtual workstation.
1.  Download and install [TightVNC](https://www.tightvnc.com/).
1.  Select **Typical** for the setup type.
1.  Accept the default configuration settings.
1.  When prompted to set passwords, choose a strong password for **Remote Access**.

    Do not change the value for **Administrative Password**.

## Install Steam and SteamVR

In this section, you download and install [Steam](https://store.steampowered.com/) and [SteamVR](https://store.steampowered.com/steamvr). Both are free to 
download and install.

1.  On your virtual workstation, download, install, and launch [Steam](https://store.steampowered.com/about/).
1.  To install SteamVR, right-click the Steam icon on the taskbar and select **SteamVR**. The application will download and install.
1.  Launch SteamVR to initialize the software.
1.  Quit both Steam and SteamVR.

## Install the CloudXR Server

1.  On your virtual workstation, download and install [NVIDIA CloudXR SDK](https://developer.nvidia.com/nvidia-cloudxr-sdk).
1.  Extract the downloaded archive and run `CloudXR-Setup.exe`, located under the subdirectory `Installer`.

    If you are prompted with a "Windows protected your PC" warning, click **More Info**, and then click **Run anyway**.

1.  When prompted, choose components for the server installation only:

    1.  Select **CloudXR Server**.
    1.  Deselect **CloudXR Client Program**.
    1.  Ensure that the **Redistributables** checkbox is selected (required only for a first-time installation).

## Install the Android Studio SDK

To load files onto your HMD, you use the [Android Debug Bridge (ADB)](https://developer.android.com/studio/command-line/adb), which is part of the
[Android Studio SDK](https://developer.android.com/studio).

1.  On your local workstation, download and install the [Android Studio SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
    for your operating system.

## Connect your workstation to your HMD

1.  On your local workstation, download and extract **_but do not install_** the [NVIDIA CloudXR SDK](https://developer.nvidia.com/nvidia-cloudxr-sdk).
1.  If required, enable Developer Mode on your device (typically only required on the
    [Oculus Quest 2](https://developer.oculus.com/documentation/native/android/mobile-device-setup#enable-developer-mode)).
1.  Connect your HMD to your workstation using the appropriate cable (typically USB 3.0).

    You can also [connect over WiFi](https://developer.android.com/studio/command-line/adb#connect-to-a-device-over-wi-fi-android-11+).
    
1.  If prompted, select **Allow USB Debugging** on the HMD.
1.  Verify that your HMD is connected by running the following in a command shell (terminal on Linux or Mac OS, PowerShell on Windows):  
  
        adb devices -l
  
    You should see your HMD listed, along with the status of the device, as in the following example output:

        List of devices attached
        1WMHHXXXXDXXXX         device usb:1-4.3 product:hollywood model:Quest_2 device:hollywood transport_id:1

    If your HMD isn't listed, check your cable connections, verify that your USB port is USB 3.0, and repeat the steps in this section.

## Install the sample application

In this section, you install the sample application on your HMD. Sample apps for all supported HMDs are provided with the CloudXR SDK.

**Note:** This section covers client installation only for the Oculus Quest 2. For other HMDs, see the
[NVIDIA CloudXR documentation](https://docs.nvidia.com/cloudxr-sdk/index.html).

1.  In a command shell on your local workstation, go to where you extracted the NVIDIA CloudXR SDK, and then go to the subdirectory that contains the sample app
    for the Oculus Quest 2: `Sample/Android/OculusVR`.

1.  Install the sample application on your Oculus Quest 2:  
  
        adb install -r ovr-sample.apk
  
    On the Oculus Quest 2, the CloudXR Client is located under **Apps > Unknown Sources**.

## Install the configuration file

1.  On your local workstation, create a plain-text file named `CloudXRLaunchOptions.txt` containing the following:  
  
        -s [VM-EXTERNAL-IP]

    Replace `[VM-EXTERNAL-IP]` with the external IP address of your virtual workstation. You can find the external IP address of your VM using the
    [Cloud Console](https://cloud.google.com/compute/docs/instances/view-ip-address#console), the
    [`gcloud` command-line tool](https://cloud.google.com/compute/docs/instances/view-ip-address#gcloud), or the
    [API](https://cloud.google.com/compute/docs/instances/view-ip-address#api).  
  
1.  Save the file on your local workstation.
1.  In a terminal on your local workstation, load the configuration file onto your Oculus Quest 2:  

        adb push CloudXRLaunchOptions.txt /sdcard/CloudXRLaunchOptions.txt

1.  Disconnect the cable from the HMD.

## Launch the CloudXR client

Connect to your virtual workstation using the CloudXR client on your HMD.

1.  On your local workstation, connect to your virtual workstation using a VNC client.
1.  Launch SteamVR.

    You will see the message *Headset Not Detected*:  

    ![image](https://storage.googleapis.com/gcp-community/tutorials/streaming-vr-content-from-a-virtual-workstation-using-nvidia-cloudxr/headset-not-detected.png)

1.  On your HMD, start the CloudXR Client.

    The first time you launch the application, you are prompted on your HMD to grant permissions to allow access.
    
1.  Follow the prompts to allow access.

When the connection is established, the SteamVR app shows the connection status of your HMD and controllers:

![image](https://storage.googleapis.com/gcp-community/tutorials/streaming-vr-content-from-a-virtual-workstation-using-nvidia-cloudxr/headset-connected.png)

The default CloudXR environment appears in your HMD display. You can preview this display on your virtual workstation by right-clicking the
SteamVR icon on the taskbar and selecting **Display VR View**:

![image](https://storage.googleapis.com/gcp-community/tutorials/streaming-vr-content-from-a-virtual-workstation-using-nvidia-cloudxr/display-vr-view.png)

A window will open showing a preview of the CloudXR environment:

![image](https://storage.googleapis.com/gcp-community/tutorials/streaming-vr-content-from-a-virtual-workstation-using-nvidia-cloudxr/cloudxr-env.png)

You can now launch SteamVR games or experiences on your virtual workstation, where they will be streamed to your HMD. Any application that uses the
[OpenVR SDK](https://en.wikipedia.org/wiki/OpenVR) will play over CloudXR, even ones not launched from SteamVR.

## Clean up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

+   Install SteamVR games and experiences and play them through your HMD.
+   Learn more about [NVIDIA CloudXR SDK](https://developer.nvidia.com/nvidia-cloudxr-sdk).
+   Read the [CloudXR documentation](https://docs.nvidia.com/cloudxr-sdk/index.html).
+   Learn more about [creating a virtual workstation](https://cloud.google.com/architecture/creating-a-virtual-workstation).
