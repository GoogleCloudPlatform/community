---
title: Getting started with IoT Core Embedded C SDK
description: Learn how to connect to IoT Core and send commands and telemetry from the device with the Embedded C SDK.
author: galz10
tags: Internet of Things, ESP32, ESP-IDF
date_published: 2020-07-31
---

This tutorial shows how to use the IoT Core Embedded C library. In this tutorial, you create an IoT Core project that receives telemetry data from a 
microcontroller and turns an LED on and off. To follow this tutorial, you don't need previous experience with IoT Core.

[IoT Core](https://cloud.google.com/iot/docs/concepts/overview) is a set of tools to connect, process, store, and analyze data both at the edge and in the cloud.
Cloud IoT consists of the device management API for creating and managing logical collections of devices and the protocol bridge that adapts device-friendly 
protocols ([MQTT](https://cloud.google.com/iot/docs/how-tos/mqtt-bridge) or [HTTP](https://cloud.google.com/iot/docs/how-tos/http-bridge)) to scalable Google 
infrastructure.

This tutorial uses the Espressif Systems ESP32, an inexpensive microcontroller with WiFi and Bluetooth capabilities. The ESP32 communicates with IoT Core 
using Wifi and will send telemetry data using the MQTT protocol. The application will also read the internal temperature sensor to send telemetry data to the 
device's subscription topic.

## Objectives

 - Install the ESP-IDF (Espressif IoT Development Framework).
 - Create a project on IoT Core.
 - Connect an ESP32 device to IoT Core.
 - Publish telemetry data from the device.
 - Receive commands on the device.

## Before you begin

The ESP-IDF (IoT Development Framework) is the SDK for Espressif chips. In this section, you install dependencies for the ESP-IDF, install the ESP-IDF itself, 
set up the ESP32 device, and connect it to IoT Core.

### Install dependencies for ESP-IDF

You need to have the following for ESP-IDF to work properly:

 - Python 3.5 or higher
 - Git
 - CMake
 - ninja

If you don't have these dependencies, you can use the following to install them:

**macOS**

```bash
brew install python
brew install git
pip install ninja
pip install cmake
```

**Windows**

- Python: https://www.python.org/downloads/windows/
- Git: https://git-scm.com/download/win
- ninja: https://github.com/ninja-build/ninja/releases
- CMake: https://cmake.org/download/


### Install and configure ESP-IDF

When all of the dependencies are installed, download and configure ESP-IDF:

1.  Download the [ESP-IDF](https://marketplace.visualstudio.com/items?itemName=espressif.esp-idf-extension) extension for Visual Studio Code.
1.  Select your git and python version.
1.  Select the location where you want to download ESP-IDF.
1.  Click the download button to download the ESP-IDF tools.
1.  Run the tool check to verify your installation.

    If the tool check verification succeeds, you’re ready to continue.

1.  When ESP-IDF is completely installed, try the `hello-world` example to see if everything is working properly. 
1.  Put the command to initialize ESP-IDF into an alias in your `$HOME/.profile` file (or in `$HOME/.bash_profile` if you don't have a profile dotfile):

        ```bash
        alias get_idf='. $HOME/esp/esp-idf/export.sh'
        ```

    With this alias, you can just call `get_idf` to initialize ESP-IDF.

For troubleshooting information, see the [Get Started](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/) page of the ESP-IDF 
documentation.

### Set up the ESP32 device

To run this example, you need an LED and two wires to connect it to the ESP32 microcontroller board. If the LED is tolerant of the same voltage as the board 
(typically 3.3V or 5V), then you can connect the LED directly to the board. If not, then use a
[resistor in series with the LED](http://www.resistorguide.com/resistor-for-led/).

### Set up your device registry

Before connecting to Google Cloud, you need to create device authentication credentials and a device registry to contain your devices.

To set up your Google Cloud project, you can use the `gcloud` command-line interface, or you can use the graphical user interface in the
[Cloud Console](https://console.cloud.google.com/). This tutorial uses `gcloud`.

1.  Download and install the [Cloud SDK](https://cloud.google.com/sdk).  
1.  Generate elliptic curve (EC) device credentials for authenticating the device when it’s trying to connect with the cloud:

        ```bash
        openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem openssl ec -in ec_private.pem -pubout -out ec_public.pem 
        ```
     You'll need to know where these files are later, so make sure that they’re saved somewhere you can access.
     
1.  Make sure that `gcloud` is up to date:

        gcloud components update
        
1.  Create a Pub/Sub topic and subscription used for storing telemetry:

        gcloud pubsub topics create temperature
        gcloud pubsub subscriptions create data --topic=temperature

1.  Create a device registry and add a device to the registry:

        gcloud iot registries create esp-test --region=us-central1 --event-notification-config=topic=temperature
        gcloud iot devices create test-dev --region=us-central1 --registry=esp-test --public-key path=ec_public.pem,type=es256

### Clone the mqtt example

You will need to clone the repository to get the example code. In your terminal, go to a location you want to store the cloned repo and run the following command:

```bash
git clone https://github.com/espressif/esp-google-iot --recurse-submodules
```

Recurse submodules is important because you will need the IoT Core Embedded C SDK which is included in the repository as a submodule.

## Connect an ESP32 device to IoT Core

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

## Publish telemetry data from the ESP32 device to IoT Core

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

## Send commands from IoT Core to the ESP32 device

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

## Run the sample

**To connect to Cloud:**

1. Use menu configuration with `make`

```c
cd /examples/main/ make menuconfig
```

1. Set up your WiFi and LED gpio pin , navigate to example configuration

![Wifi Setup](https://storage.googleapis.com/gcp-community/tutorials/embedded-c-getting-started/wifisetup.gif)

1. Set up your Google Cloud project information, navigate to component configuration and then to IoT Core Configuration

![Cloud Project Setup](https://storage.googleapis.com/gcp-community/tutorials/embedded-c-getting-started/CloudSetup.gif)

1. Locate your ec_private.pem file and copy its contents into the private.pem file in the certs folder located at examples/main/certs
1. Run `idf.py build` to build sources into firmware
1. Run `idf.py -p /dev/cu.usbserial-1440 flash` passing the path to your tty device to flash the firmware onto the device
1. Run `idf.py -p /dev/cu.usbserial-1440 monitor` passing the path to your tty device to monitor the device output

If you make changes to the code, you will need to rebuild the program again before calling flash

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

![Send Command](https://storage.googleapis.com/gcp-community/tutorials/embedded-c-getting-started/command.jpg)

**To view telemetry data:**

1. Navigate to your registry
1. Click on the PubSub topic
1. Click on the PubSub subscription
1. Click on view message at the top and pull your messages

![Blinky](https://storage.googleapis.com/gcp-community/tutorials/embedded-c-getting-started/device.jpg)

## Next steps

Now that you've got the basics down and you can connect to IoT Core, you can add your own spin on this project. Try replacing the LED with a relay to control a 
power outlet or connect a sensor to measure and analyze environmental data.
