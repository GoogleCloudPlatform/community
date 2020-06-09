---
title: Getting Started with IoT Core Embedded C SDK.
description: Learn how to connect to IoT Core and send commands/telemetry from the device on the Embedded C SDK.
author: Galz10
tags: IoT,Google Cloud, Internet of Things, ESP32, ESP-IDF, IoT Core
date_published: 2020-08-02
---
This tutorial shows how to use the IoT Core Embedded C library and will take you through the steps of creating a IoT Core project which will receive telemetry data from an ESP32 microcontroller and will be able to turn on and off an LED. Follow this tutorial to configure Cloud IoT Core and run the mqtt-example on your ESP32.
Objectives

 - Install ESP-IDF
 - Create a project on IoT Core
 - Connect ESP32 to IoT Core
 - Publish Telemetry Data from device
 - Receive Commands on the device

## Before you begin

### ESP-IDF Setup

Before we can setup IoT Core we must get ESP-IDF, which is the SDK for Espressif chips. If you can download the [ESP-IDF](https://marketplace.visualstudio.com/items?itemName=espressif.esp-idf-extension) extension for Visual Studio Code, make sure you have all dependencies because if you don’t you will get errors and will need to redownload ESP-IDF.
You’ll need to have the following for ESP-IDF to work properly:

 - Python 3.5 or higher
 - Git
 - Cmake
 - Ninja

If you don't have these dependencies, you can install them using :

**For Mac :**

```bash
brew install python
brew install git
pip install ninja
pip install cmake
```

**For Windows :**

Python : https://www.python.org/downloads/windows/
Git : https://git-scm.com/download/win
ninja : https://github.com/ninja-build/ninja/releases
cmake : https://cmake.org/download/

Once you have all dependencies installed, configure ESP-IDF.

1. Select your git and python version
1. Select the location you want to download ESP-IDF
1. Click the download button to download the ESP-IDF tools
1. Run the tool check to verify your installation

If the tool check verification succeeds, you’re ready to continue.

Once ESP-IDF is completely installed, try out the hello-world example to see if everything is working properly, I suggest putting the command to initialize ESP-IDF into an alias:

```bash
alias get_idf='. $HOME/esp/esp-idf/export.sh'
```

in your $HOME/.profile file so you can just call get_idf. If you don't have a profile dotfile, then put the code above in $HOME/.bash_profile.
For more troubleshooting steps, see the [getting started](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/) page of the ESP-IDF.

### ESP32 Setup

We will be using the Espressif Systems ESP32 (ESP32), which is an inexpensive and easy to source microcontroller with WiFi and Bluetooth capabilities. To run this example, you will need an LED and two wires to connect it to the board if the LED is tolerant of the same voltage as the board(typically 3.3v or 5v) if it can’t then you should use a resistor in series with the [LEDS](http://www.resistorguide.com/resistor-for-led/).

The ESP32 will communicate with IoT Core using Wifi and will send telemetry data using the MQTT protocol, we will also read the internal temperature sensor to send telemetry data to the device's subscription topic.

To get the internal temperature we will use the `temprature_sens_read function`. To correctly set the function you must give a forward declaration for the function:

```c
#ifdef __cplusplus

extern "C" {
  #endif

uint8_t temprature_sens_read();

#ifdef __cplusplus
}
#endif
```

### IoT Core

If you’ve never used IoT Core, don’t worry, the steps below will get you setup to transmit telemetry data to the cloud but before we can do that lets talk about IoT Core and its components. IoT Core is a complete set of tools to connect, process, store, and analyze data both at the edge and in the cloud. Google Cloud IoT consists of the device management API for creating and managing logical collections of devices and the protocol bridge which adapts device-friendly protocols (MQTT or HTTP) to scalable Google infrastructure.

Now that we have a little bit of information about IoT Core lets set it up.

To learn more about the protocols for [IoT Core](https://cloud.google.com/iot/docs/), read the [MQTT](https://cloud.google.com/iot/docs/how-tos/mqtt-bridge) and [HTTP](https://cloud.google.com/iot/docs/how-tos/http-bridge) documentation.

### Setting up your device registry

Before connecting to Google Cloud you need to create device authentication credentials and a device registry to contain your devices.

There are two ways you can set up your project on Google Cloud IoT, you can use the Cloud SDK (gcloud) or using the UI in the [Google Cloud Console](https://console.cloud.google.com/) This guide will go through setting the project up using gcloud. After you have downloaded the [Cloud SDK](https://cloud.google.com/sdk).

**To set up your device registry :**
1. Generate Elliptic Curve (EC) device credentials for authenticating the device when it’s
trying to connect with the cloud, You will need to know where these files are later so make sure they’re saved somewhere you can access.

```bash
openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem openssl ec -in ec_private.pem -pubout -out ec_public.pem
```

1. Make sure your gcloud is up to date. gcloud components update
1. Create a PubSub topic and subscription used for storing telemetry .

```c
gcloud pubsub topics create temperature
gcloud pubsub subscriptions create data --topic=temperature
```

1. Create a device registry and add a device to the registry .

```c
gcloud iot registries create esp-test --region=us-central1 --event-notification-config=topic=temperature gcloud iot devices create test-dev --region=us-central1 --registry=esp-test \ --public-key path=ec_public.pem,type=es256
```

### Cloning mqtt example

You will need to clone the repo to get the example code. In your terminal, go to a location you want to store the cloned repo and run the following command:

```bash
git clone https://github.com/espressif/esp-google-iot --recurse-submodules
```

Recurse submodules is important because you will need the IoT Core Embedded C SDK which is included in the repository as a submodule.

## Connecting an ESP32 to Cloud IoT Core

The mqtt_task function sets up the parameters needed to connect to the cloud. It uses the private key created earlier in `iotc_connect_private_key_data`. The data is applied to create the jwt to connect to IoT Core, as highlighted in the following code.

```c
iotc_crypto_key_data_t iotc_connect_private_key_data;
iotc_connect_private_key_data.crypto_key_signature_algorithm = IOTC_CRYPTO_KEY_SIGNATURE_ALGORITHM_ES256;
iotc_connect_private_key_data.crypto_key_union_type = IOTC_CRYPTO_KEY_UNION_TYPE_PEM; iotc_connect_private_key_data.crypto_key_union.key_pem.key = (char *) ec_pv_key_start;
```

With the private key as data, you can initialize iotc by calling `iotc_inilialize` and checking that there’s no error. If everything is working properly you're ready to create the jwt and finally connect to IoT Core.

To connect our ESP32 to Cloud IoT Core use `iotc_connect` which is from the IoT Core Embedded C SDK. The function takes multiple parameters you need to provide the following:

 - Username (usually null)
 - Password ( jwt )
 - Client_id ( device path)
 - Connection_timeout
 - keepalive_timeout
 - Client_callback

```c
static void mqtt_task(void *pvParameters) {
iotc_crypto_key_data_t iotc_connect_private_key_data;
iotc_connect_private_key_data.crypto_key_signature_algorithm = IOTC_CRYPTO_KEY_SIGNATURE_ALGORITHM_ES256;
iotc_connect_private_key_data.crypto_key_union_type = IOTC_CRYPTO_KEY_UNION_TYPE_PEM;
iotc_connect_private_key_data.crypto_key_union.key_pem.key = (char *) ec_pv_key_start;
const iotc_state_t error_init = iotc_initialize();

if (IOTC_STATE_OK != error_init) {
  printf(" iotc failed to initialize, error: %d\n", error_init); vTaskDelete(NULL);
  }
iotc_context = iotc_create_context();

if (IOTC_INVALID_CONTEXT_HANDLE >= iotc_context) {
  printf(" iotc failed to create context, error: %d\n", -iotc_context);
  vTaskDelete(NULL);
  }

const uint16_t connection_timeout = 0;
const uint16_t keepalive_timeout = 20;
char jwt[IOTC_JWT_SIZE] = {0};
size_t bytes_written = 0;
iotc_state_t state = iotc_create_iotcore_jwt( CONFIG_GIOT_PROJECT_ID, 3600, &iotc_connect_private_key_data, jwt, IOTC_JWT_SIZE, &bytes_written);

if (IOTC_STATE_OK != state) {
  printf("iotc_create_iotcore_jwt returned with error: %ul", state); vTaskDelete(NULL);
}

char *device_path = NULL;
asprintf(&device_path, DEVICE_PATH, CONFIG_GIOT_PROJECT_ID, CONFIG_GIOT_LOCATION, CONFIG_GIOT_REGISTRY_ID, CONFIG_GIOT_DEVICE_ID);
iotc_connect(iotc_context, NULL, jwt, device_path, connection_timeout, keepalive_timeout, &on_connection_state_changed);
free(device_path);
iotc_events_process_blocking();
iotc_delete_context(iotc_context);
iotc_shutdown();
vTaskDelete(NULL);
}
```

If you have any questions on what each function does the [IoT Device SDK](https://googlecloudplatform.github.io/iot-device-sdk-embedded-c/api/html/d9/d22/iotc_8h.html) docs is a great resource.

After successfully connecting to the cloud you will need to subscribe to configuration and command topic of the device. You do this by calling `iotc_subscribe` function, and you must include :

 - Topic command ( includes topic and device id )
 - QoS
 - Callback function

## Publish Telemetry Data from ESP32 to Cloud IoT Core

To publish telemetry to IoT Core we use `iotc_publish` which must include the topic name, message and QoS inorder to send the message.

The code below sets up the topic from the device id and event topic and then publishes the message.
You can find this code in the mqtt-example.c file on line 35.

```c
void publish_telemetry_event(iotc_context_handle_t context_handle, iotc_timed_task_handle_t timed_task, void *user_data) {
char *publish_topic = NULL;

asprintf(&publish_topic, PUBLISH_TOPIC_EVENT, CONFIG_GIOT_DEVICE_ID);

char *publish_message = NULL; asprintf(&publish_message, TEMPERATURE_DATA, MIN_TEMP + rand() % 10);

ESP_LOGI(TAG, "publishing msg \"%s\" to topic: \"%s\"\n", publish_message, publish_topic);

iotc_publish(context_handle, publish_topic, publish_message, iotc_example_qos,NULL,NULL);
free(publish_topic); free(publish_message);
}
```

## Sending Commands from Cloud IoT Core to ESP32
The callback function is invoked when the device receives a message from the cloud. This is where the code turns the led on and off based on incoming messages.You can find this code in the mqtt-example.c file on line 50.

```c
void iotc_mqttlogic_subscribe_callback(iotc_context_handle_t in_context_handle, iotc_sub_call_type_t call_type, const iotc_sub_call_params_t *const params, iotc_state_t state, void *user_data) {

    char *sub_message = (char *)malloc(params->message.temporary_payload_data_length + 1);

    memcpy(sub_message, params->message.temporary_payload_data, params->message.temporary_payload_data_length);

    sub_message[params->message.temporary_payload_data_length] = '\0';

    ESP_LOGI(TAG, "Delegate Message Payload: %s", sub_message);

    if (strcmp(subscribe_topic_command, params->message.topic) == 0)
    {
        gpio_pad_select_gpio(BLINK_GPIO);
        /* Set the GPIO as a push/pull output */
        gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);

        int value;
        sscanf(sub_message, "light: %d", &value);
        ESP_LOGI(TAG, "value: %d\n", value);
        if (value == 1)
        {
            ESP_LOGI(TAG, "ON");
            gpio_set_level(BLINK_GPIO, 1);
        }
        else if (value == 0)
        {
            gpio_set_level(BLINK_GPIO, 0);
        }
    }
    free(sub_message);
}
```

## Running the Sample

**To Connect to Cloud:**

1. Use menu configuration with `make`

```c
cd /examples/main/ make menuconfig
```

1. Set up your WiFi and LED gpio pin , navigate to example configuration

![Wifi Setup](https://github.com/galz10/community/blob/gal/tutorials/embedded-c-getting-started/wifisetup.gif)

1. Set up your Google Cloud Project information, navigate to component configuration and then to IoT Core Configuration

![Cloud Project Setup](https://github.com/galz10/community/blob/gal/tutorials/embedded-c-getting-started/CloudSetup.gif)

1. Locate your ec_private.pem file and copy its contents into the private.pem file in the certs folder located at examples/main/certs
1. Run `idf.py build` to build sources into firmware
1. Run `idf.py -p /dev/cu.usbserial-1440 flash` passing the path to your tty device to flash the firmware onto the device
1. Run `idf.py -p /dev/cu.usbserial-1440 monitor` passing the path to your tty device to monitor the device output

Note: if you make changes to the code, you will need to rebuild the program again before calling flash

You should now see your device connecting to your registry on IoT Core. After the device connects, you can send commands from IoT Core or view the data that is being submitted by the device.

If you want to exit the serial monitor use Ctrl + ]

**To send commands:**

1. Navigate to your registry and then to the device
1. Click on the send command button at the top
1. Send the following commands

```c
light:1 for light on
light:0 for light off
```

Note: if the board you're using has the GPIO pin set to pulldown, setting this value to 1 will turn the light off.

![Send Command](https://github.com/galz10/community/blob/gal/tutorials/embedded-c-getting-started/command.jpg)

**To view telemetry data:**

1. Navigate to your registry
1. Click on the PubSub topic
1. Click on the PubSub subscription
1. Click on view message at the top and pull your messages

![Blinky](https://github.com/galz10/community/blob/gal/tutorials/embedded-c-getting-started/device.jpg)

## Next Steps

Now that you've got the basics down and you can connect to IoT Core, you can add your own spin on this project, try replacing the LED with a relay to control a power outlet or can connect a sensor to measure and analyze environmental data.
