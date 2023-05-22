---
title: Using Fledge with IoT Core on Google Cloud
description: Learn how to process sensor data with Fledge.
author: gguuss
tags: Cloud IoT Core, Gateways, Raspberry Pi, Python, MQTT, internet of things, Fledge, FogLAMP, Dianomic
date_published: 2020-01-31
---

Gus Class | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Fledge (previously known as *FogLAMP*) is an open-source framework contributed by Dianomic
for getting data from sensors into data stores. Fledge provides a bridge between sensors
that communicate using the *South* service to Google Cloud as a data store using the
*North* service.

To see an architecture diagram that illustrates the use of Fledge in the context
of Google Cloud IoT Core, see the
[Fledge documentation](https://fledge-iot.readthedocs.io/en/latest/fledge_architecture.html).
That architecture diagram shows HTTPS traffic to a cloud platform; for IoT Core, message
traffic can also use the MQTT protocol.

For this tutorial, we use a Raspberry Pi to host the Fledge service.

## Set up your Raspberry Pi with the Raspbian Buster image

This tutorial requires that you use the Debian Buster version of the Raspberry
Pi software because it uses packages built for that version of Linux.

1.  Download a Raspbian Buster image from the
    [Raspbian downloads page](https://www.raspberrypi.org/software/operating-systems/).

1.  Extract the image that you downloaded, which creates a file with a name that ends
    in `.img`.
    
    For example, if you download the full version of Raspbian, the file is
    named `2019-09-26-raspbian-buster-full.img`.

1.  Create the SD card image for your Raspberry Pi using a disk image utility.

    Raspberry Pi recommends that you use [balenaEtcher](https://www.balena.io/etcher/).

1.  Flash your Raspberry Pi using the disk image that you created.

    For information about flashing your Raspberry Pi, see the detailed instructions in the
    [Raspberry Pi installation documentation](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

1.  Set up access to the Raspberry Pi. 

    *   If you intend to access the Raspberry Pi in headless mode, follow the instructions for
        [setting up headless](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md)
        on the Raspberry Pi site.
    *   If you intend to access your Raspberry Pi locally, connect it to a keyboard,
        mouse, and display.

1.  Do any final configuration of the Raspberry Pi—such as expanding the filesystem and
    setting the user password—with the
    [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md)
    utility.

You perform subsequent steps on the Raspberry Pi itself either over SSH if you're working in
headless mode or on the Raspberry Pi hardware if you're using the desktop UI.

## Download the Fledge packages

1.  Visit the
    [installing Fledge section of the Fledge site](https://fledge-iot.readthedocs.io/en/latest/quick_start.html#installing-fledge)
    and start from the pre-built packages linked in the instructions.
    
1.  When you receive the email message containing the link to the Fledge packages,
    copy the link referencing v1.7 for ARM-based devices (Buster), the package
    for Raspberry Pi devices.

1.  From your Raspberry Pi, use the following commands to download the Fledge
    packages to the file system and place them in a folder named `foglamp` in your
    user's home directory. Replace `[LINK_FROM_EMAIL]` with the link that you copied
    in the previous step.

        mkdir $HOME/fledge
        cd $HOME/fledge
        wget [LINK_FROM_EMAIL]
        tar -xzvf fledge-1.8.0_armv7l_buster.tgz

    The `fledge` folder in your user's home directory contains all the resources
    required for getting your Raspberry Pi up and running.

## Install the Fledge service and Fledge GUI on your Raspberry Pi

The Fledge graphical user interface (GUI) makes it easier to configure and
control Fledge from your Raspberry Pi.

1.  Browse to the folder that you downloaded the Fledge packages to, and install
    the Fledge and Fledge GUI packages:

        cd $HOME/fledge/fledge/1.8.0/buster/armv7l 
        sudo apt -y install ./fledge-1.8.0-armv7l.deb
        sudo apt -y install ./fledge-gui-1.8.0.deb

1.  Start the Fledge service and check its status:

        export FLEDGE_ROOT=/usr/local/fledge
        $FLEDGE_ROOT/bin/fledge start
        $FLEDGE_ROOT/bin/fledge status

## Open the Fledge GUI

To open the Fledge GUI, you use your web browser to go to the web server that
started running on the Raspberry Pi when you installed the Fledge GUI.

1.  To determine the IP address of your server, run the `ifconfig` command:

        ifconfig

    The output looks similar to the following:

        wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
                inet 192.168.1.217  netmask 255.255.255.0  broadcast 192.168.1.255
                inet6 fe80::9f73:3b56:93c2:4ed4  prefixlen 64  scopeid 0x20<link>
                ether dc:a6:32:03:b7:cb  txqueuelen 1000  (Ethernet)
                RX packets 426133  bytes 305815327 (291.6 MiB)
                RX errors 0  dropped 0  overruns 0  frame 0
                TX packets 274458  bytes 172317386 (164.3 MiB)
                TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

    In this example, the IP address is `192.168.1.217`.
    
1.  Use your web browser to go to the URL for the IP address from the previous step,
    such as this URL using the value from the previous example:
    
        http://192.168.1.217

    When you navigate to the web server, you see a dashboard similar to the following:

    ![Fledge GUI dashboard](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-gui.png)

## Install a Fledge South plugin for generating data

In this tutorial, you install a *South* plugin for generating and getting data and
a *North* plugin for publishing data to Google Cloud.

One quick way to get some data is with the "randomwalk" plugin.

1.  Install the `fledge-south-randomwalk` plugin:

        cd $HOME/fledge/fledge/1.8.0/buster/armv7l
        sudo apt install ./fledge-south-randomwalk-1.8.0-armv7l.deb

1.  In the left pane of the Fledge GUI, click **South**, and then click the **Add +** button
    in the upper-right corner of the **South Services** window:

    ![Add button](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-south-add.png)

1.  Select **randomwalk** in **South Plugin** list, give your plugin a name (for example, `random`), and
    click **Next**.

    ![Add random plugin](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-south-add-random.png)

1.  Click **Next** again on the next screen, and then click **Done**.

1.  In the left pane, click **Assets & Readings**.

    You should see random data generated by the South plugin that you just configured.

    ![Fledge Assets & Readings graph](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-south-readings.png)

## Install the Fledge North plugin for IoT Core

Now that you have data being generated by the South plugin, you can
publish that data to Google Cloud through the IoT Core device bridge. 

1.  Install the Fledge North plugin for Google Cloud IoT Core (GCP North plugin):

        cd $HOME/fledge/fledge/1.8.0/buster/armv7l
        sudo apt install ./fledge-north-gcp-1.8.0-armv7l.deb

1.  In the left pane of the Fledge GUI, click **North**, and then click the
    **Create North Instance +** button in the upper-right corner of the
    **North Instances** window:

    ![Create North instance](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-north-add.png)

1.  Select the `GCP` plugin, give your instance a name (for example, `GCP`), and
    click **Next**.

## Create a registry

For information on creating registries and devices, see the
[IoT Core documentation](https://cloud.google.com/iot/docs/how-tos/devices).

1.  Go to the [IoT Core page in the Cloud Console](https://console.cloud.google.com/iot).

1.  At the top of the page, click **Create registry**.

1.  Enter a registry ID (for example, `fledge`).

1.  Choose a region (for example, `us-central1`).

1.  Select an existing telemetry topic or create a new topic (for example, `projects/[YOUR_PROJECT_ID]/topics/fledge`).
    
1.  Click **Create**.

    ![Create registry form](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-north-create-registry.png)

After the registry is created, the registry overview page opens.
    
## Create and configure a device for communicating with IoT Core
    
In this section, you create a device that will be used to transmit data to IoT
Core. Before you can register a device, you need to
[create a key pair](https://cloud.google.com/iot/docs/how-tos/credentials/keys)
used to authenticate the device.

1.  Create an RSA public/private key pair:

        cd $HOME/fledge
        openssl genpkey -algorithm RSA -out rsa_private.pem -pkeyopt rsa_keygen_bits:2048
        openssl rsa -in rsa_private.pem -pubout -out rsa_public.pem

1.  Show the contents of the public key:

        cat rsa_public.pem

1.  In the left pane of the IoT Core page in the Cloud Console, click **Devices**.

1.  At the top of the **Devices** page, click **Create a device**.

    ![Create device screen](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-north-create-device.png)

1.  Enter a device ID (for example, `fledge`).

1.  Make sure the public key format matches the type of key that you created in the
    first step of this section (for example, `RS256`).
    
1.  Paste the contents of your public key in the **Public key value** field.

1.  Click **Create**.

    ![Add the device screen](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-north-create-device-contents.png)

## Configure the North plugin to communicate using your device

1.  Copy the device private key and the root certificate for Google Cloud IoT core
    to the Fledge certificate store:

        wget https://pki.goog/roots.pem
        cp roots.pem /usr/local/fledge/data/etc/certs/
        cp rsa_private.pem /usr/local/fledge/data/etc/certs/

1.  In the Fledge GUI, on the **Review Configuration** page, enter your Google Cloud project ID,
    the registry name that you used (`fledge` in the examples used in this tutorial), the
    device ID (`fledge`), and the key name that was created (`rsa_private`).
    
1.  Choose the JWT algorithm (**RS256**) and the data source (typically **readings**).

    ![Fledge North GCP plugin configuration](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/foglamp-north-configure-gcp.png)
    
1.  Click **Next**.

1.  Ensure that the plugin is enabled on the following screen, and click **Done**.

## Verify communication

1.  Return to the Fledge GUI dashboard.

    The count of readings sent and received readings should be increasing.
    
1.  Go to the IoT Core page for your device in the Cloud Console.

    Verify that telemetry events are received from the device.

    ![Cloud IoT Core Device page](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/cloud-iot-console-device-telemetry.png)

Congratulations! You have set up Fledge to publish data generated on the
Raspberry Pi!

To see the telemetry messages, you can create a Pub/Sub subscription.

## Create a Pub/Sub subscription to see telemetry messages

1.  On the Cloud Iot **Registry details** page, click the channel entry in the
    **Cloud Pub/Sub topics** section.

    ![Cloud IoT Registry details](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/cloud-iot-registry-page.png)

1.  Click **Create subscription**.

    ![Create Subscription page](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/cloud-iot-pubsub-create-subscription.png)

1.  Enter the subscription details, such as the name for your subscription
    (for example, `fledge`), and click **Create**.

    ![Input Subscription details page](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-fledge/cloud-iot-pubsub-create-subscription-details.png)

With the subscription created, you can see the messages published by Fledge
using the [Google Cloud SDK](https://cloud.google.com/sdk). The following
command lists the messages published to the `fledge` subscription:

    gcloud pubsub subscriptions pull --limit 500 fledge

The output includes JSON data corresponding to the generated data, such as the following.


```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬─────────────────┬────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    DATA                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   │    MESSAGE_ID   │             ATTRIBUTES             │                                                                                           ACK_ID                                                                                           │
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────────────┼────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {"randomwalk" : [ {"ts":"2020-01-08 22:22:23.126610","randomwalk" : 100},{"ts":"2020-01-08 22:22:24.126691","randomwalk" : 100},{"ts":"2020-01-08 22:22:25.126676","randomwalk" : 100},{"ts":"2020-01-08 22:22:26.126688","randomwalk" : 99},{"ts":"2020-01-08 22:22:27.126671","randomwalk" : 98}]} │ 928125343880036 │ deviceId=fledge                   │ IT4wPkVTRFAGFixdRkhRNxkIaFEOT14jPzUgKEUXAQgUBXx9d0FPdV1ecGhRDRlyfWBzPFIRUgEUAnpYURgEYlxORAdzMhBwdWB3b1kXAgpNU35cXTPyztSQrLSyPANORcajjpomIZzZldlsZiQ9XxJLLD5-NSxFQV5AEkw-GURJUytDCypYEU4EIQ │
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           │                 │ deviceNumId=2550637435869530       │                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           │                 │ deviceRegistryId=fledge           │                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           │                 │ deviceRegistryLocation=us-central1 │                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           │                 │ projectId=glassy-nectar-370        │                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           │                 │ subFolder=                         │                                                                                                                                                                                            │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴─────────────────┴────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Cleaning up

Now that you've seen how the plugin works, you can delete the North
instance to prevent data from continuing to be published:

1.  In the left pane of the Fledge GUI, click **North**.
1   Select your instance of the GCP plugin.
1.  Click **Delete instance**.

## Next steps

Fledge provides a robust solution for getting data into Google Cloud using IoT Core.
You can readily migrate the data from Pub/Sub to persistent data stores, including
the following:

* [BigQuery](https://cloud.google.com/bigquery/docs)
* [Cloud SQL](https://cloud.google.com/sql/docs)
* [Cloud Spanner](https://cloud.google.com/spanner/docs)

You can analyze the data using Google Cloud Analytics products.

You can evaluate other South plugins such as the [SenseHat](https://github.com/fledge-iot/fledge-south-sensehat)
plugin, which transmits gyroscope, accelerometer, magnetometer, temperature,
humidity, and barometric pressure.

You can look into the hardware partners for more robust and secure hardware
solutions. The following reference hardware solutions are available from Nexcom:

* [NISE50](http://www.nexcom.com/Products/industrial-computing-solutions/industrial-fanless-computer/atom-compact/fanless-nise-50-iot-gateway)
* [NISE105](http://www.nexcom.com/Products/industrial-computing-solutions/industrial-fanless-computer/atom-compact/fanless-computer-nise-105)
* [NISE3800](http://www.nexcom.com/Products/industrial-computing-solutions/industrial-fanless-computer/core-i-performance/fanless-pc-fanless-computer-nise-3800e)

You can look into advanced usage of the Fledge platform through features such as
[filters](https://fledge-iot.readthedocs.io/en/latest/fledge_architecture.html#filters),
[notifications](https://fledge-iot.readthedocs.io/en/latest/notifications.html),
and [API access to device data with](https://fledge-iot.readthedocs.io/en/latest/rest_api_guide/03_RESTuser.html#user-api-reference).
