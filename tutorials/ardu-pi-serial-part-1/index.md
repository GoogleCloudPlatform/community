---
title: Locally connected microcontrollers and real-time analytics (part 1 of 2)
description: Learn how to integrate an Arduino with a Raspberry Pi, and connect them as one device to Cloud IoT Core.
author: lepistom
tags: IoT, Internet of Things, Arduino, Raspberry Pi, MCU
date_published: 2018-08-31
---

Markku Lepisto | Solutions Architect | Google Cloud Platform

This two-part tutorial demonstrates how to use an [Arduino Microcontroller][arduino]
to provide analog sensor readings to a [Raspberry Pi][pi], connect the devices
to [Cloud IoT Core][iotcore], post telemetry data from the devices, and
analyze the data in real time. Part 1 of the tutorial creates a 'hybrid' device,
combining the strengths of a Linux-based microprocessor with internet
connectivity and TLS stack, together with a constrained microcontroller for
analog I/O. The devices act as a cloud-connected solar and wind power generator.

![devices diagram][devicesdiag]

## Part 1 objectives

- Program the Arduino with the [Sketch][sketch] language.
- Read analog sensor values.
- Transmit the data over a serial connection to the Raspberry Pi.
- Program the Pi in [Python][python] to read digital sensor values.
- Post the combined analog and digital sensor data to Cloud IoT Core over
  a secure [MQTT][mqtt] connection.

In [part 2][part2] of the tutorial, you will learn how to process, store, and analyze the streaming data in real time.

![architecture diagram][archdiag]

[arduino]: https://www.arduino.cc/
[pi]: https://www.raspberrypi.org/
[iotcore]: https://cloud.google.com/iot-core/
[python]: https://www.python.org/
[sketch]: https://www.arduino.cc/en/tutorial/sketch
[mqtt]: http://mqtt.org/
[devicesdiag]: https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-1/devices.jpg
[archdiag]: https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-1/architecture.png
[part2]: https://cloud.google.com/community/tutorials/ardu-pi-serial-part-2

## Before you begin

This tutorial assumes you already have a [Google Cloud Platform (GCP)][gcp] account set up.
You will also need to download and install the [Arduino IDE][ide] on your local
development environment.

[gcp]: https://console.cloud.google.com/freetrial
[ide]: https://www.arduino.cc/en/Main/Software

## Costs

This tutorial uses billable components of GCP, including the following:

- Cloud IoT Core
- Cloud Pub/Sub

This tutorial should not generate any usage that would not be covered by the
[free tier](https://cloud.google.com/free/), but you can use the
[Pricing Calculator](https://cloud.google.com/products/calculator/) to generate
a cost estimate based on your projected production usage.

## Required hardware

- Raspberry Pi 3 Model [B][3b] or [B+][3b+]. **Note:** the instructions should
  work on other Pi models as well, but this has not been verified.
- Raspberry Pi case (optional but recommended)
- Raspberry Pi power supply, rated at 2.5A or more
- MicroSD card for Raspbian OS. Minimum 8GB card recommended
- [Raspberry Pi Sense HAT][sensehat] add-on board
- [Arduino Uno Genuino][arduinouno] or 100% compatible microcontroller
- Two (recommended) analog sensors for the Arduino. In this tutorial we use a
  small [solar panel][solarpanel] and a small [DC motor][dcmotor] to generate
  analog voltage readings
- USB type A to type B cable (to interconnect the Pi and Arduino)
- USB keyboard
- Monitor with HDMI input
- HDMI cable

[3b]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b/
[3b+]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[sensehat]: https://www.raspberrypi.org/products/sense-hat/
[arduinouno]: https://www.arduino.cc/en/Guide/BoardAnatomy
[solarpanel]: https://www.adafruit.com/product/700
[dcmotor]: https://www.sparkfun.com/products/11696

## Create an IoT Core registry and device

First, execute all the steps in the IoT Core [Quickstart][quickstart] *on your
local development environment e.g laptop*. But *do not clean up* the environment.
The rest of this tutorial will use the registry, device, and device keys created
with the quickstart.

[quickstart]: https://cloud.google.com/iot/docs/quickstart

## Raspberry Pi installation and configuration

###  Raspbian OS installation and configuration

1.  Follow the instructions [here][raspbian] to download the latest
    [Raspbian Lite OS image][raspbianimg], and write it on your MicroSD card.
    All the steps in this tutorial run in console mode on the Pi, or over SSH to
    the Pi.
1.  Insert your Pi into the Pi case.
1.  Plug your Sense HAT into the Pi's 40-pin connector.
1.  Insert the MicroSD card into the Pi card slot.
1.  Connect the USB keyboard into the Pi.
1.  Connect the Pi to your monitor with the HDMI cable.
1.  Optionally, if you use Ethernet connectivity, connect your ethernet cable to
    the Pi.
1.  Connect the Pi power supply to the wall socket and to the Pi, to boot up
    Raspbian OS.
1.  Login to the Pi with the initial username: `pi` and password: `raspberry`
1.  Execute raspi-config as the superuser with:

        sudo raspi-config

1.  Change the pi user's password by selecting: **1 Change User Password**
1.  If you are using Wi-fi, select: **2 Network Options** then **N2 Wi-fi** to
    configure your Wi-fi country settings, SSID and passphrase.
1.  To get most console apps to display text correctly, select:
    **4 Localisation options** then **I1 Change Locale**. Scroll down with the
    down arrow key, and deselect the default option (`en_GB.UTF-8 UTF-8`) using
    the space bar.
1.  Scroll down to `en_US.UTF-8 UTF-8` and select that option with the space
    bar.
1.  Press Tabulator and select: **Ok**
1.  Use the arrow keys in the **Configuring locales** window to select
    `en_US.UTF-8` from the list of choices as the default locale. Press
    Tabulator and select: **Ok**
1.  To set your system timezone, select: **4 Localisation options** then
    **I2 Change Timezone** and use the menu options to find your geographic
    region and country. Setting the timezone is important because Google IoT
    Core requires client devices' system clocks to be within 10 minutes of real
    time. Raspbian uses global NTP time servers to synchronize the clock.
1.  Optionally, select: **4 Localisation options** then
    **I3 Change Keyboard Layout** to match your layout. If you are not sure,
    select: **Generic 105-key (Intl) PC**, then **English (US)**, then **The
    default for the keyboard layout**, then **No compose key**.
1.  Select: **Interfacing Options**, then **P2 SSH**, then **Yes** to enable the
    SSH server on your Pi.
1.  Select: **Interfacing Options**, then **P5 I2C**, then **Yes** to load the
    ARM I2C kernel module. The Raspberry Pi Sense HAT sensor module used in this
    tutorial uses I2C.
1.  Select: **Finish**, to exit the raspi-config tool and accept to restart the
    Pi. If you are not prompted to reboot when you exit raspi-config, reboot the
    Pi by executing:

        sudo reboot

1.  Log in as the `pi` user with your new custom password.
1.  Verify that you have an IP address on your Pi by executing:

        ifconfig -a

    You should see a client IP from your local network segment in either the
    `wlan0` or `eth0` interface.

1.  Verify that your DNS resolution and internet connection work, by executing:

        ping www.google.com

1.  If you do not have an IP address, or DNS resolution or internet connectivity
    fail, do not proceed further until you have fixed your Pi's network
    configuration.
1.  For Wi-fi connectivity only - check if your Wi-fi adapter has power saving
    enabled. We have to disable Wi-fi power saving, or it will give you sporadic
    network connectivity issues later on. Check the current state by executing:

        iwconfig

    Look for "Power Management" under the `wlan0` interface. If you see
    `Power Management:on`, then we have to disable it.

1.  On Pi 3 model B/B+, disable `wlan0` Wi-fi power management by configuring
    `/etc/network/interfaces`. Execute:

        sudo vi /etc/network/interfaces

    or use the nano editor if you prefer. Add these lines to the end of the file:

        allow-hotplug wlan0
        iface wlan0 inet manual
            # disable wlan0 power saving
            post-up iw dev $IFACE set power_save off

1.  Reboot the Pi with:

        sudo reboot

    to apply the changes. Then log in again as the `pi` user.

1.  Execute:

        iwconfig

    to ensure that Wi-fi power management is now: `Power Management:off` for
    `wlan0`.

1.  Execute:

        ping www.google.com

    to check your internet connectivity.

1.  Upgrade the Raspbian packages to latest versions with:

        sudo apt-get update && sudo apt-get upgrade -y

[raspbian]: https://www.raspberrypi.org/documentation/installation/installing-images/README.md
[raspbianimg]: https://www.raspberrypi.org/downloads/raspbian/

### Install Cloud SDK and dependencies for Pi Sense HAT

1.  SSH to the Raspberry Pi with:

        ssh pi@YOUR_PI_IP

1.  On the Pi, follow all the steps [here][cloudsdk] to install and initialize
    Cloud SDK for Debian systems.
1.  Check that Cloud SDK is installed and initialized with:

        gcloud info

    Ensure that the `Account` and `Project` properties are set correctly.

1.  Install Git, Python development packages and Sense HAT dependencies with:

        sudo apt-get update && sudo apt-get install -y git virtualenv python-dev sense-hat libffi-dev libssl-dev libopenjp2-7 libjpeg-dev

### Clone the Pi client app and install its dependencies

1.  Using the SSH connection to the Pi, clone the repository associated with the
    community tutorials:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Change to the tutorial directory:

        community/tutorials/ardu-pi-serial/part1

1.  Create a Python virtual environment:

        virtualenv venv

1.  Activate the virtualenv:

        source venv/bin/activate

1.  Upgrade pip and setuptools:

        pip install -U pip setuptools

1.  Install the required Python modules:

        pip install -r requirements.txt

1.  Copy the private key file that you generated from IoT Core
    [Quickstart][quickstart] guide to the app's current working directory on the
    Pi. Back on your laptop command line, you can use `scp` to transfer the file
    to the Pi, with for example:

        scp rsa_private.pem pi@YOUR_PI_IP:ardu-pi-serial/

You can check your Pi's IP address by executing:

    ifconfig

on the Pi.

[cloudsdk]: https://cloud.google.com/sdk/docs/#deb

## Arduino Uno installation and configuration

### Connect the sensors to the Arduino

**IoT boards and components**
![boards diagram](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-1/ardu-pi.png)

1.  Connect 2 analog sensors to the Arduino. See the board diagram above to see
    how to wire the 2 sensors to the Arduino. In this example, we will read the
    analog voltage values of a DC motor, and a solar panel. *Note: you can
    replace the DC motor and solar panel with other analog sensors—but you
    **have to ensure that the sensor output does not exceed 5V** or it can
    damage the Arduino pin.*
1.  Connect the first sensor (small DC motor) to the Arduino. Connect the black
    ground wire of the motor to a `GND` port, and the red (voltage input/output)
    wire to port `A0` on the Arduino.
1.  Connect the second sensor (small solar panel) to the Arduino. Connect the
    black ground wire of the panel to a `GND` port, and the red (voltage output)
    wire to port `A1` on the Arduino.

### Compile the Arduino Sketch

1.  Connect your Arduino to your local development machine with a USB cable.
    Note that the Arduino Uno board used as the example in this tutorial has a
    USB type B connector on the board. The USB cable will provide both power and
    serial data connectivity to the Arduino from your machine.
1.  Launch the Arduino IDE software on your local machine.
1.  Go to the **Arduino menu bar**, then **Tools**, then **Board** and select
    **Arduino/Genuino Uno**.
1.  Check the **Port** options under **Tools** and select the port on your
    computer that has **Arduino/Genuino Uno** visible and connected.
1.  Select **File** then **New** to open a new Sketch.
1.  Delete all the text in the new Sketch template.
1.  Copy and paste this code into your new Sketch:

        #define WINDGEN_PIN A0
        #define SOLARGEN_PIN A1

        String inputString = "";
        boolean stringComplete = false;

        int windgen = 0;
        int solargen = 0;
        char sendBuffer[32];
        char ch = 0;

        void setup() {
          Serial.begin(115200);
          inputString.reserve(200);
          pinMode(LED_BUILTIN, OUTPUT);
          digitalWrite(LED_BUILTIN, LOW);
        }

        void loop(){
          if (Serial.available()) {
             ch = Serial.read();
             if ( ch == '0' ) {
               sendTelemetry();
             }
          }
        }

        void sendTelemetry() {
          digitalWrite(LED_BUILTIN, HIGH);
          memset(sendBuffer, 0, sizeof(sendBuffer));
          int windgen = analogRead(WINDGEN_PIN);
          int solargen = analogRead(SOLARGEN_PIN);
          sprintf(sendBuffer, "S s:%d w:%d", solargen, windgen);
          Serial.println(sendBuffer);
          digitalWrite(LED_BUILTIN, LOW);
        }

1.  Select **File** then **Save As...** and save your sketch with a suitable
    name such as `ardu-pi-serial`.

**Arduino IDE and Sketch**
![Sketch diagram](https://storage.googleapis.com/gcp-community/tutorials/ardu-pi-serial-part-1/sketch.png)

### Test reading Arduino sensors over serial connection from your machine

The Arduino Sketch client has the following functionality:

- Check if the serial connection has data available to read
- If the received character (command) is 0:
    - Read the voltage values of pins A0 and A1
    - Print the sensor values to the serial connection

Perform the following steps to deploy and test the Arduino sketch:

1.  Select **Sketch** then **Verify/Compile** from the Arduino IDE menu. If the
    code is successfully verified, the Arduino IDE should display **Done
    compiling**. You should also see output similar to the following:

        Sketch uses 4708 bytes (14%) of program storage space. Maximum is 32256 bytes.
        Global variables use 249 bytes (12%) of dynamic memory, leaving 1799 bytes for local variables. Maximum is 2048 bytes.

1.  Select **Sketch** then **Upload** to transfer the compiled Sketch to your
    Arduino over the USB serial connection. You should see the Arduino's LEDs
    blink rapidly while the binary is transferred over.
1.  Select **Tools** then **Serial Monitor** to open the Serial Monitor window.
1.  Ensure that the baud rate is set to "115200 baud".
1.  Test requesting the current sensor values from the Arduino, by typing `0`
    (zero) in the Serial Monitor's input window, and pressing **Enter**. If the
    Sketch and serial connection works, you should see a response similar to:
    `S s:136 w:43` in the Serial Monitor.

Here, `S` indicates sensor output, `s:136` is the current value of the solar
panel (analog pin `A1`) and `w:43` is the current value of the wind generator /
DC motor (analog pin `A0`). This is how the Python client app on the Pi will
request the sensor readings from the Arduino later on. Command `0` is an example
of a simple protocol used to command an Arduino program.

Different inputs (e.g `1`) could be used to command the Arduino to perform a
different action, such as turning a servo motor. In this tutorial, the Arduino
Sketch implements a single command `0`, which reads the voltage values of analog
pins `A0` and `A1`.

- Unplug the USB cable from your local machine to disconnect and power down the
Arduino. The Arduino will now run the sketch automatically, whenever it is
connected to a power source.

## Connect the Arduino to the Pi and run the IoT Core client app

The Pi Python client has the following functionality:

- Sign a JWT token with the device private key
- Create and connect an IoT Core client
- Create a Sense HAT sensor board client
- Open the serial connection to the Arduino
- Read the Sense HAT environmental sensors
- Request the analog sensor readings from Arduino over the serial connection
- Publish the sensor readings as a JSON document once a second
- Re-generate and sign a new JWT token after it expires

1.  SSH to the Raspberry Pi with:

        ssh pi@YOUR_PI_IP

1.  Connect the Arduino to the Pi with a USB cable. This will power on the
    Arduino, and create a USB serial port on the Pi, for serial communications.
1.  On the Pi, check that you now have a serial port connected to the Pi.
    Execute: 

        file /dev/ttyACM0

    The output should be similar to:

        /dev/ttyACM0: character special (166/0)

1.  With your virtualenv active, run the client app on the Pi, by executing:

        python ardu-pi-serial.py  \
            --project_id your_project_id \
            --registry_id my-registry \
            --device_id my-device \
            --private_key_file rsa_private.pem \
            --algorithm RS256 \
            --cloud_region us-central1 \
            --ca_certs roots.pem \
            --message_type event \
            --device_type pi

    To see the command line argument options, execute:

        python ardu-pi-serial.py --help

    If the client app starts correctly, you should see output similar to this:

        Creating JWT using RS256 from private key file rsa_private.pem
        Creating and flushing serial port. Rebooting Arduino..
        ('gcp_on_connect', '0: No error.')
        Received message '' on topic '/devices/my-device/config' with Qos 1
        Sleeping 3s..
        Received from Arduino: S s:89 w:42
        Publishing message: {"temperature": 37.32, "timestamp": "2018-07-25T08:29:59+08:00", "clientid": "raspberrypi", "humidity": 37.98, "pressure": 1016.98, "windgen": 0.21, "solargen": 0.43}
        gcp_on_publish

1.  On your local development machine, create a subscription for your IoT Core
    registry's telemetry topic, by executing:

        gcloud pubsub subscriptions create my-device-events-sub --topic=my-device-events

1.  Verify that your telemetry data is streaming to Cloud Pub/Sub, by executing: 

        gcloud pubsub subscriptions pull my-device-events-sub --limit 100 --auto-ack

    You should see message payloads similar to:

        {"temperature": 36.62, "timestamp": "2018-07-25T08:42:10+08:00", "clientid": "raspberrypi", "humidity": 38.44, "pressure": 1017.05, "windgen": 0.1, "solargen": 1.2}   │ 151338809303544 │ deviceId=my-device

Now your Arduino and Pi are streaming telemetry data through Cloud IoT Core to
Pub/Sub. You should see the sensor readings change if you expose the solar panel
to more, or less light. The wind generator (DC motor) will start generating
power, as you turn the rotor.

## Next

In [part 2][part2] of this tutorial, you will use Cloud Dataflow with a
Python streaming pipeline to process this data stream, store it in Google
BigQuery, explore the data with a Cloud Datalab Jupyter Notebook, and visualize
it using Google Data Studio.
