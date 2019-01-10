---
title: Using Cloud IoT Core gateways with a Raspberry Pi
description: Learn how to set up gateways on Cloud IoT Core using a Raspberry Pi.
author: hongalex
tags: Cloud IoT Core, Gateways, Raspberry Pi, Python, MQTT, internet of things
date_published: 2018-12-10
---

Alex Hong | Developer Programs Engineer | Google Cloud IoT Core  
Fengrui Gu | Software Engineer | Google Cloud IoT Core

This tutorial shows you how to set up and use gateways on Cloud IoT Core. From the [documentation][gateways-overview], a "gateway is a device that connects less capable devices to Cloud IoT Core and performs several tasks on the device's behalf, such as communication, authentication, storage, and processing."

In this tutorial, you will create a gateway that manages two devices: a simple LED and a DHT22 sensor. Neither device will be directly connected to Cloud IoT Core, but will receive updates from and publish telemetry events to the cloud through the gateway.

[gateways-overview]: https://cloud.google.com/iot/docs/how-tos/gateways/

## Architecture

The following diagram gives a high-level overview of how the device/gateway architecture is structured.

![gateway architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/gateway-arch.png)

## Objectives

- Create a new gateway and bind devices to it
- Demonstrate changing configurations on a device bound to a gateway
- Demonstrate sending telemetry from a bound device to Cloud IoT Core

## Before you begin

This tutorial assumes you have a Google Cloud Platform (GCP) account and have completed the setup steps outlined in the [Cloud IoT Core getting started guide][iot-start]. For quick cleanup, create a new GCP project to use just for this tutorial.

For more information about the different authentication methods Cloud IoT Core offers, [see Authenticating over the MQTT bridge][iot-auth].

[iot-start]: https://cloud.google.com/iot/docs/how-tos/getting-started
[iot-auth]: https://cloud.google.com/iot/docs/how-tos/gateways/authentication#authenticating_over_the_mqtt_bridge

## Costs

This tutorial uses billable components of GCP, including:

- Cloud IoT Core
- Cloud Pub/Sub

This tutorial should not generate any usage that would not be covered by the free tier, but you can use the [pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538) to generate a cost estimate based on your projected usage.

## Required hardware

- Laptop or desktop with `git` and `python2`
- [Raspberry Pi 3][rpi] Model B (Other models should work, but they have not been verified)
- MicroSD card for [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) (8GB+ recommended)
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

## Enable Cloud IoT Core and Cloud Pub/Sub APIs

Click **Enable API** for each of the following:

- [Cloud IoT Core][cloud-iot] (for managing gateways and devices)
- [Cloud Pub/Sub](http://console.developers.google.com/cloudpubsub) (for ingesting device telemetry)

[cloud-iot]: https://console.developers.google.com/iot

## Create a registry

First, create a device registry that will contain your gateway and devices.

1. Open the [Cloud IoT Core console][cloud-iot].
2. Ensure the right project is selected in the upper left.
3. Click on **Create a device registry**.
4. For **Registry ID**, enter `my-registry`.
5. Select the region closest to you, but for the purposes of this demo we'll use `us-central1`.
6. Ensure the MQTT protocol is enabled for this registry.
7. Under **Cloud Pub/Sub topics**, create a new Cloud Pub/Sub topic for **Default telemetry topic**.
    - Click on the **Select a Cloud Pub/Sub topic** dropdown.
    - Click on the **Create a topic** option.
    - Enter a Cloud Pub/Sub topic name, such as `gateway-telemetry`.
8. Do the same for **Device state topic**, under a different PubSub topic named `gateway-state`.

    ![create registry](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/create-registry.png)

9. Leave everything else as-is, and click **Create**.

## Set up your gateway

For the purposes of this tutorial, you will use your laptop or desktop as the gateway device. You will first generate an RSA public/private key pair, which will be used to sign the JWTs for authenticating to Cloud IoT Core.

To set up your gateway:

1. Clone the following repository and change into the directory for this tutorial's code:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/cloud-iot-gateways-pi

2. Generate an RS256 public/private key pair by running the following:

        ./generate_keys.sh

3. In the [Cloud IoT Core console][cloud-iot], click on the registry you created.
4. Under the **Gateways** tab, click **Create Gateway**.
5. For **Gateway ID**, enter `my-gateway`.
6. Copy the contents of `rsa_public.pem` into the public key text area.
7. For **Device authentication method**, select **Association only**. For more details about why this option is used, see [Extra notes](#extra-notes) below.

    ![create gateway](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/create-gateway.png)

8. Click **Create**.
9. Export your Google Cloud project ID as an environment variable by running the following:

        export GOOGLE_CLOUD_PROJECT=your-project-id-123

10. Modify the `run-gateway` script by providing arguments for `registry_id` and `device_id` if you chose different names for those.
11. Download [Google's CA root certificate](https://pki.goog/roots.pem) into the same directory if it doesn't exist already.

        wget https://pki.goog/roots.pem

12. Install the following packages by running the following command. Feel free to do this in a virtual environment of your choice.

        pip install -r requirements-gateway.txt

13. Run the following command to start the gateway:

        source run-gateway

14. Keep this process running while you proceed through the next steps. We recommend that you use a new tab or window for each gateway and device.

15. Find the local IP address of the gateway using `ifconfig` on  Mac/Linux or `ipconfig /all` on Windows. Copy this somewhere as you will need to add this IP address to `led-light.py` and `thermostat.py` later for connecting devices to the gateway. Your gateway and devices need to be on the same network and be visible to each other.

## Raspberry Pi setup

In this tutorial, you'll use a [Raspberry Pi][rpi] to manage the LED/temperature sensor. Devices will connect to the gateway device through [UDP sockets][udp-socket] over a local network, which will connect to Cloud IoT Core via the [MQTT bridge][mqtt-bridge]. A Raspberry Pi could theoretically connect directly to the cloud (since the Pi can connect to the internet), so using a Raspberry Pi for this part is mostly for demonstration purposes.

1. [Download Raspbian][raspbian-download] (the full image with Desktop and recommended software) and follow [the installation guide][raspbian-installation] to flash Raspbian onto your microSD card.
2. Insert the microSD card with Raspbian into your Raspberry Pi.
3. Attach a power source to the Raspberry Pi using the microUSB cable (e.g., to a laptop USB port).
4. Connect your keyboard and mouse to the Raspberry Pi's USB ports.
5. Connect the Raspberry Pi to a monitor through the HDMI port.
6. Go through the default setup steps for Raspbian upon boot.
7. Open a terminal and make sure `git`, `python` (python2), and other required dependencies are installed. If not, install them by running:

        sudo apt update && sudo apt upgrade
        sudo apt install git
        sudo apt install python
        sudo apt install build-essential libssl-dev libffi-dev python-dev

8. Clone the following repository and change into the directory for this tutorial's code:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/cloud-iot-gateways-pi

9. Install Python dependencies by running the following:

        pip install -r requirements-pi.txt

    Feel free to do this part in the virtual environment manager of your choosing, though make sure to switch into those environments when opening new tabs.

[udp-socket]: https://docs.python.org/2/library/socket.html
[mqtt-bridge]: https://cloud.google.com/iot/docs/how-tos/mqtt-bridge
[raspbian-download]: https://www.raspberrypi.org/downloads/raspbian
[raspbian-installation]: https://www.raspberrypi.org/documentation/installation/installing-images/README.md
[rpi]: https://www.raspberrypi.org/

## Managing devices through config updates

Next, you will manage an LED light connected to the gateway through Cloud IoT Core config updates.

1. Switch to your browser and open the Cloud IoT Core dashboard.
2. Click on the registry you created.
        The gateway you created should be listed in this registry.
3. Click **Create Device**.
4. For **Device ID**, enter **led-light**.
5. Leave everything else blank or as-is. You don't need to enter a public key since the device will be authenticated through the gateway.
6. Bind the device to the gateway.
    - Click the browser's button to return to your registry page.
    - Click on `my-gateway` from the **Gateways** tab in `my-registry`.
    - Click on the **Bound devices** tab.
    - Click **Bind device** and then select the box next to `led-light`.
    - Confirm by clicking **Bind** in the lower right.

    ![bind device to gateway](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/bind-device.png)
7. Edit `led-light.py` and add the IP address of your gateway to line 18 `ADDR = ''`.
8. Connect the LED to the Raspberry Pi's [GPIO Pin 4][rpi-gpio] and ground while using an appropriate resistor.
9. Ensure the gateway Python sample is still running on your desktop or laptop.
10. Run the following from your terminal on the Raspberry Pi:

        source run-led-light

11. Make sure you see the `>>LED IS OFF<<` message

12. Switch back to a browser and go to the [Cloud IoT Core dashboard][cloud-iot].
13. Select your registry, and then select `led-light`.
14. Click **Update Config** at the top of the page.
15. In the configuration text area, enter `ON` or `OFF` to toggle the LED state.

    ![udpate config](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/update-config.png)

    These are preconfigured valid states the LED will respond to, defined in `led-light.py`. Sending configuration updates from the Cloud IoT Core console toggles the LED device through the gateway device.

[rpi-gpio]: https://www.raspberrypi.org/documentation/usage/gpio/

## Publishing telemetry events through the gateway

In this section, you will set up a DHT22 sensor to send telemetry from the sensor through the gateway to Cloud IoT Core.

1. Repeat steps 1-7 from [Managing devices through config updates][managing-devices], but use `thermostat` as the **Device ID**.
2. Wire the DHT22 sensor to the Raspberry Pi as described [in the setup section of this tutorial][dht22-tutorial].

3. Run the following from a terminal on the Raspberry Pi:

        source run-thermostat

4. If everything is done correctly, you should see the temperature on that terminal updating once per second.

    ![temperatures](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/temperature.png)

[managing-devices]: #managing-devices-through-config-updates
[dht22-tutorial]: https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22

## Create a subscription to your telemetry topic to view data

1. Open the [Cloud Pub/Sub dashboard][pub-sub].
2. Click the three dot menu button next to the telemetry topic you created earlier, and click **New subscription**.
3. Enter a subscription name, such as `my-subscription`.
4. Make sure **Delivery Type** is set to **Pull**, and leave everything else as-is.
5. Click the **Create** button to create the subscription.
6. Next, click the **Activate Cloud Shell** icon in the upper right area of the GCP window.

    ![cloud shell](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-gateways-rpi/cloud-shell.png)

7. In the Cloud Shell, enter the following:

        gcloud pubsub subscriptions pull my-subscription --auto-ack --limit=100

The topic should have received a lot of messages from both the LED and DHT22. In practice, services that ingest data from Pub/Sub should process that data in regular intervals as telemetry events are published.

[pub-sub]: https://console.cloud.google.com/cloudpubsub 

## Cleanup

To avoid incurring any future billing costs, it is recommended that you delete your project once you have completed the tutorial.

## Extra notes

- The reason why **Association Only** was chosen when creating the gateway is so that the device does not have to store its own JWT when authenticating to Cloud IoT Core. You can read more about [authentication methods here][iot-auth].
- You can set up a second Raspberry Pi or another internet enabled device to act as the gateway for a more realistic example.
- A slightly less expensive alternative to the DHT22 is the [DHT11][dht-alt].
- If you have difficulty installing the packages from `requirements-pi.txt`, make sure you are on the latest version of Raspbian. In addition, [updating some packages could solve the issue][installation-issue].

        sudo apt-get install build-essential libssl-dev libffi-dev python-dev

[dht-alt]: https://www.adafruit.com/product/386
[installation-issue]: https://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py

## Next steps

- [Real time data processing with Cloud IoT Core](https://cloud.google.com/community/tutorials/cloud-iot-rtdp)
- [Connect a Bluetooth device to a gateway](https://www.hackster.io/mayooghgirish/arduino-bluetooth-basic-tutorial-d8b737)
