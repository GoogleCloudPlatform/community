---
title: Using IoT Core gateways with a Raspberry Pi
description: Learn how to set up gateways on IoT Core using a Raspberry Pi.
author: hongalex
tags: Cloud IoT Core, gateways, Raspberry Pi, Python, MQTT, internet of things
date_published: 2018-12-10
---

Alex Hong | Developer Programs Engineer | Google

Fengrui Gu | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to set up and use gateways on IoT Core. From the [documentation][gateways-overview], a
"gateway is a device that connects less capable devices to IoT Core and performs several tasks on the device's behalf,
such as communication, authentication, storage, and processing."

In this tutorial, you create a gateway that manages two devices: a simple LED and a DHT22 sensor. Neither device is
directly connected to IoT Core, but receives updates from and publishes telemetry events to the cloud through the
gateway.

[gateways-overview]: https://cloud.google.com/iot/docs/how-tos/gateways/

## Architecture

The following diagram gives a high-level overview of how the device/gateway architecture is structured.

![gateway architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/gateway-arch.png)

## Objectives

- Create a new gateway and bind devices to it.
- Demonstrate changing configurations on a device bound to a gateway.
- Demonstrate sending telemetry from a bound device to IoT Core.

## Before you begin

This tutorial assumes that you have a Google Cloud account and have completed the setup steps outlined in the
[IoT Core getting started guide][iot-start]. For quick cleanup, create a new Google Cloud project to use just for this 
tutorial.

For more information about the different authentication methods that IoT Core offers,
[see Authenticating over the MQTT bridge][iot-auth].

[iot-start]: https://cloud.google.com/iot/docs/how-tos/getting-started
[iot-auth]: https://cloud.google.com/iot/docs/how-tos/gateways/authentication#authenticating_over_the_mqtt_bridge

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- IoT Core
- Pub/Sub

This tutorial should not generate any usage that would not be covered by the free tier, but you can use the
[pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538) to generate a 
cost estimate based on your projected usage.

## Required hardware

- Laptop or desktop with `git` and `python3`
- [Raspberry Pi 3][rpi] Model B (Other models should work, but they have not been verified.)
- MicroSD card for [Raspberry Pi OS](https://www.raspberrypi.org/software/operating-systems/) (8GB+ recommended)
- MicroSD card reader
- USB keyboard
- MicroUSB to USB-A cable
- Monitor with HDMI input
- HDMI cable
- LED
- [Adafruit DHT22 Temperature/Humidity Sensor](https://www.adafruit.com/product/385)
- 10k Ohm resistor
- Breadboard and jumper wires
- Jumper wires

## Enable IoT Core and Pub/Sub APIs

Click **Enable API** for each of the following:

- [IoT Core][cloud-iot] (for managing gateways and devices)
- [Pub/Sub](http://console.developers.google.com/cloudpubsub) (for ingesting device telemetry)

[cloud-iot]: https://console.developers.google.com/iot

## Create a registry

First, create a device registry that will contain your gateway and devices.

1.  Open the [IoT Core console][cloud-iot].
1.  Ensure that the right project is selected in the upper left.
1.  Click **Create a device registry**.
1.  For **Registry ID**, enter `my-registry`.
1.  Select the region closest to you. For the purposes of this tutorial we'll use `us-central1`.
1.  Ensure that the MQTT protocol is enabled for this registry.
1.  Under **Pub/Sub topics**, create a new Pub/Sub topic for **Default telemetry topic**.
    - Click the **Select a Pub/Sub topic** dropdown.
    - Click the **Create a topic** option.
    - Enter a Pub/Sub topic name, such as `gateway-telemetry`.
1.  Do the same for **Device state topic**, under a different Pub/Sub topic named `gateway-state`.

    ![create registry](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/create-registry.png)

1.  Leave everything else as-is, and click **Create**.

## Set up your gateway

For the purposes of this tutorial, you can use your laptop or desktop as the gateway device, for a simpler setup process. 
Alternatively, you can use a more realistic device like an additional Raspberry Pi\*.

You first generate an RSA public/private key pair, which is used to sign the JWTs for authenticating to IoT Core.

To set up your gateway:

1.  Clone the following repository and change into the directory for this tutorial's code:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/cloud-iot-gateways-rpi

1.  Generate an RS256 public/private key pair by running the following:

        ./generate_keys.sh

1.  In the [IoT Core console][cloud-iot], click the registry you created.
1.  Under the **Gateways** tab, click **Create Gateway**.
1.  For **Gateway ID**, enter `my-gateway`.
1.  Copy the contents of `rsa_public.pem` into the public key text area.
1.  For **Device authentication method**, select **Association only**. For more details about why this option is used, see
    [Extra notes](#extra-notes) below.

    ![create gateway](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/create-gateway.png)

1.  Click **Create**.
1.  Export your Google Cloud project ID as an environment variable by running the following:

        export GOOGLE_CLOUD_PROJECT=your-project-id-123

1.  Modify the `run-gateway` script by providing arguments for `registry_id` and `device_id` if you chose different names 
    for those.
1.  Download [Google's CA root certificate](https://pki.goog/roots.pem) into the same directory if it doesn't exist already:

        wget https://pki.goog/roots.pem

1.  Use a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to keep installations local to a
    workspace rather than installing libraries onto your system directly:

        python3 -m venv env
        source env/bin/activate

1.  Install the following packages by running the following command:

        pip install -r requirements-gateway.txt

1.  Run the following command to start the gateway:

        source run-gateway

1.  Keep this process running while you proceed through the next steps. We recommend that you use a new tab or window for 
    each gateway and device.

1.  Find the local IP address of the gateway using `ifconfig` on macOS or Linux or `ipconfig /all` on Windows. Copy this 
    somewhere as you will need to add this IP address to `led-light.py` and `thermostat.py` later for connecting devices to
    the gateway. Your gateway and devices need to be on the same network and be visible to each other.

## Raspberry Pi setup

In this tutorial, you use a [Raspberry Pi\*][rpi] to manage the LED/temperature sensor. Devices connect to the gateway
device through [UDP sockets][udp-socket] over a local network, which connect to IoT Core through the
[MQTT bridge][mqtt-bridge]. The Raspberry Pi is not really a constrained device, since it has IP connectivity and the 
ability to sign JWTs, so its use here is mostly for demonstration purposes.

1.  [Download Raspberry Pi software](https://www.raspberrypi.org/software/operating-systems/) (the full image with Desktop and recommended software) and
    follow [the installation guide][raspbian-installation] to flash Raspberry Pi OS onto your microSD card.
1.  Insert the microSD card with Raspberry Pi OS into your Raspberry Pi.
1.  Attach a power source to the Raspberry Pi using the microUSB cable (for example, to a laptop USB port).
1.  Connect your keyboard and mouse to the Raspberry Pi USB ports.
1.  Connect the Raspberry Pi to a monitor through the HDMI port.
1.  Go through the default setup steps for Raspberry Pi OS upon boot.
1.  Open a terminal and make sure that `git`, `python3`, and other required dependencies are installed. If not, install
    them by running the following:

        sudo apt update && sudo apt upgrade
        sudo apt install git
        sudo apt install python3
        sudo apt install build-essential libssl-dev libffi-dev python3-dev

1.  Clone the following repository and change into the directory for this tutorial's code:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/cloud-iot-gateways-rpi

1.  Create and activate your virtual environment. Make sure to run the last step whenever you open a new tab to activate the
    virtual environment.

        python3 -m virtualenv venv
        source env/bin/activate

1.  Install Python dependencies by running the following:

        pip install -r requirements-pi.txt

[udp-socket]: https://docs.python.org/3/library/socket.html 
[mqtt-bridge]: https://cloud.google.com/iot/docs/how-tos/mqtt-bridge
[raspbian-download]: https://www.raspberrypi.org/software/operating-systems/
[raspbian-installation]: https://www.raspberrypi.org/documentation/installation/installing-images/README.md
[rpi]: https://www.raspberrypi.org/

## Managing devices through configuration updates

Next, you manage an LED light connected to the gateway through IoT Core configuration updates.

1.  Switch to your browser and open the [IoT Core console][cloud-iot].
1.  Click the registry that you created. The gateway that you created should be listed in this registry.
1.  Click **Create Device**.
1.  For **Device ID**, enter `led-light`.
1.  Leave everything else blank or as-is. You don't need to enter a public key since the device will be authenticated
    through the gateway.
1.  Bind the device to the gateway:

    1.  Click the browser's button to return to your registry page.
    1.  Click `my-gateway` from the **Gateways** tab in `my-registry`.
    1.  Click the **Bound devices** tab.
    1.  Click **Bind device** and then select the box next to `led-light`.
    1.  Confirm by clicking **Bind** in the lower right.

    ![bind device to gateway](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/bind-device.png)

1.  Edit `led-light.py` by adding the IP address of your gateway on line 28: `ADDR = ''`.
1.  Connect the LED to the Raspberry Pi [GPIO Pin 14][rpi-gpio] and ground using an appropriate resistor.
1.  Ensure that the gateway Python sample is still running on your desktop or laptop.
1.  Run the following from your terminal on the Raspberry Pi:

        source run-led-light

1.  Make sure that you see the `>>LED IS OFF<<` message
1.  Switch back to a browser and go to the [IoT Core console][cloud-iot].
1.  Select your registry, and then select `led-light`.
1.  Click **Update Config** at the top of the page.
1.  In the configuration text area, enter `ON` or `OFF` to toggle the LED state.

    ![update config](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/update-config.png)

    These are preconfigured valid states that the LED will respond to, defined in `led-light.py`. Sending configuration 
    updates from the IoT Core console toggles the LED device through the gateway device.

[rpi-gpio]: https://www.raspberrypi.org/documentation/usage/gpio/

## Publishing telemetry events through the gateway

In this section, you set up a DHT22 sensor to send telemetry from the sensor through the gateway to IoT Core.

1.  Repeat steps 1-6 from the previous section, "Managing devices through configuration updates", but use `thermostat` as 
    the **Device ID**.
1.  Edit `thermostat.py` by adding the IP address of your gateway on line 27: `ADDR = ''`
1.  Wire the DHT22 sensor to the Raspberry Pi as described [in the setup section of this tutorial][dht22-tutorial].

1.  Run the following from a terminal on the Raspberry Pi:

        source run-thermostat

1.  If everything is done correctly, you should see the temperature on that terminal updating once per second.

    ![temperatures](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/temperature.png)

[dht22-tutorial]: https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22

## Create a subscription to your telemetry topic to view data

1.  Open the [Pub/Sub dashboard][pub-sub].
2.  Click the three-dot menu button next to the telemetry topic that you created earlier, and click **New subscription**.
3.  Enter a subscription name, such as `my-subscription`.
4.  Make sure that **Delivery Type** is set to **Pull**, and leave everything else as-is.
5.  Click the **Create** button to create the subscription.
6.  Click the **Activate Cloud Shell** icon in the upper right area of the Cloud Console window.

    ![cloud shell](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/cloud-shell.png)

7.  In Cloud Shell, enter the following:

        gcloud pubsub subscriptions pull my-subscription --auto-ack --limit=100

The topic should have received a lot of messages from both the LED and DHT22. In practice, services that ingest data from 
Pub/Sub should process that data in regular intervals as telemetry events are published.

[pub-sub]: https://console.cloud.google.com/cloudpubsub

## Cleanup

To avoid incurring any future billing costs, it is recommended that you delete your project once you have completed the 
tutorial.

## Extra notes

- The reason why **Association Only** was chosen when creating the gateway is so that the device does not have to store its
  own JWT when authenticating to IoT Core. You can read more about [authentication methods here][iot-auth].
- You can set up a second Raspberry Pi or another internet enabled device to act as the gateway for a more realistic 
  example.
- A slightly less expensive alternative to the DHT22 is the [DHT11][dht-alt].
- If you encounter issues while installing the packages from `requirements-pi.txt`, make sure you are on the latest version
  of Raspberry Pi OS. In addition, [updating some packages could solve the issue][installation-issue].

        sudo apt-get install build-essential libssl-dev libffi-dev python-dev

[dht-alt]: https://www.adafruit.com/product/386
[installation-issue]: https://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py

## Next steps

- [Real time data processing with IoT Core](https://cloud.google.com/community/tutorials/cloud-iot-rtdp)
- [Connect a Bluetooth device to a gateway](https://www.hackster.io/mayooghgirish/arduino-bluetooth-basic-tutorial-d8b737)

\*Raspberry Pi is a trademark of the Raspberry Pi Foundation.
