---
title: Using Sigfox Sensit with GCP
description: Setup the Sigfox Sens'it Discovery V3 device as a devkit, and use it with Google Cloud Platform.
author: lepistom
tags: IoT, Internet of Things, Sigfox, LPWAN
date_published: 2019-02-21
---

Markku Lepisto | Solutions Architect | Google Cloud

## Objectives

This document describes how to start using your [Sigfox](https://www.sigfox.com/) [Sens'it Discovery V3](https://sensit.io) device and connect it to [Google Cloud Platform](https://cloud.google.com). With step by step instructions on how to use Google Cloud services for real-time sensor data ingestion, processing and analytics, as well as device configuration management.

The main functionalities demonstrated are the following:

- Sens'it device activation and registration as a devkit
- Sigfox - Google Cloud integration configuration
- Binary sensor data ingestion, parsing and storage in a data warehouse
- Binary device configuration encoding, decoding and management

**Figure 1.** Sigfox Sens'it Discovery V3

[sensit]: img/sensit-gcp.jpg
![sensit and gcp][sensit]

## Architecture Diagram

**Figure 2.** End to end architecture

[archdiag]: img/architecture.svg
![architecture diagram][archdiag]

## Costs

This tutorial uses billable components of GCP, including:

- Cloud Functions
- Cloud Pub/Sub
- Cloud Datastore
- Cloud BigQuery

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Before you begin

This tutorial assumes you already have a [Cloud Platform](https://console.cloud.google.com/freetrial) account set up.

## Creating a Google Cloud Platform Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com).
1. Open the Projects pulldown menu in the menu bar on the top and select 'New Project'.
1. Give the project a name and create it.
1. Switch to your newly created project with the Projects pull-down menu.
1. Open the menu > APIs & Services > Library.
1. Search for and activate the following APIs, or ensure that they are already active:
    1.  Cloud Functions API
    1.  Cloud Pub/Sub API
    1.  Cloud Datastore API
    1.  Cloud BigQuery API

## Activating Your Sens'it Device

Sens'it devices come with a Sigfox subscription. You have to first activate the device, create a Sigfox account, and associate the device in your account. You can activate the device using either a web portal, or a mobile app. The next chapters get you started with both options. _Note: you must be located in a Sigfox [network coverage area](https://www.sigfox.com/en/coverage), when you activate the device._

### Option 1: Activating Sens'it Using the Web Interface

To activate the Sens'it device using the web portal, execute the following steps:

1. Navigate to the [sensit.io web portal](https://sensit.io) and click 'Launch App'.

**Figure 3.** Sensit.io web portal

[acti1]: img/acti1.png
![activation part 1][acti1]

1. Click 'Activate my Sens'it'.

**Figure 4.** Activating the Sens'it device

[acti2]: img/acti2.png
![activation part 2][acti2]

1. Find the device ID printed on the back of the device, and enter it in the input field.

**Figure 5.** Entering the Sens'it ID

[acti3]: img/acti3.png
![activation part 3][acti3]

1. Follow the rest of the steps of the web wizard, to activate your device and register it in your sensit.io account.

### Option 2: Activating Sens'it Using the Mobile App

Alternatively, you can install the Sigfox Sens'it Discovery mobile app and use it to activate your device. The app is available in the [Google Play store](https://play.google.com/store/apps/details?id=com.sensitio&hl=en_US) for Android and [App Store](https://play.google.com/store/apps/details?id=com.sensitio&hl=en_US) for iOS devices.

To activate the Sens'it device using the mobile app, execute the following steps:

1. Install and open the Sens'it Discovery app on your Android or iOS device.
1. Click 'Add a Sens'it'.

**Figure 6.** Adding a Sens'it with the mobile app

[app1]: img/app1.png
![app part 1][app1]

1. Scan the QR code printed on the back of the device. If the scanning does not work, enter the ID manually using the link on the bottom of the screen.

**Figure 7.** Scanning the device QR code

[app2]: img/app2.png
![app part 2][app2]

1. Confirm the scanned device ID and follow the rest of the steps to activate your device and register it in your sensit.io account.

**Figure 8.** Confirming the scanned device ID

[app3]: img/app3.png
![app part 3][app3]

## Registering Your Sens'it as a Devkit

After you have activated your device, it should be visible in your [sensit.io](https://sensit.io) web portal. In order to use the device with the [Sigfox Backend](https://backend.sigfox.com) system, and integrate with upstream platforms like Google Cloud, you need to register the device as a devkit.

Execute the following steps to register your Sens'it as a devkit:

1. Follow all the steps in [this document](https://storage.sbg1.cloud.ovh.net/v1/AUTH_669d7dfced0b44518cb186841d7cbd75/dev_medias/build/4059ae1jm2231vw/sensit-3-devkit-activation.pdf). _Note: ensure that you enter a valid email address so that you can finalize the registration process._
1. Wait for a few hours while Sigfox registers your new account in the Sigfox Backend, and communicates with the device to transfer it to your Backend account. The time delay is due to the Sigfox radio network periodically communicating with newly registered devices. You will receive an email once the process has finished.

## Configuring the Sigfox-GCP Integration

Now that you have your Sens'it device associated with your Sigfox Backend, you can integrate it with Google Cloud Platform for processing sensor data, and managing the device configuration.

To integrate your Sigfox Backend with Google Cloud, execute all the steps in the [Sigfox-GCP Integration guide](https://cloud.google.com/community/tutorials/sigfox-gw). **NOTE** - before you start following the linked document, read the tips below. The Integration guide will help you set up Cloud Functions for receiving data and service messages from Sigfox, Cloud Pub/Sub for ingesting the data as a real-time stream, and Cloud Datastore for managing device group configurations.

Tips:

- To transmit a message from your Sens'it device, double-click the button.
- To request a downlink message, press the button in a 'short-short-long' sequence.
- In the chapter _'*Configuring Datastore for Device Configuration Management*'_, you can use the following hexadecimal string for the initial configuration value: `46003f0f8004223c`

The above HEX string is a valid Sens'it configuration payload, which corresponds with the following values:

```
MESSAGE_PERIOD = 1
MAGNET_MODE_FLAG = False
VIBRATION_MODE_FLAG = False
DOOR_MODE_FLAG = False
LIGHT_MODE_FLAG = True
TEMP_MODE_FLAG = True
STANDBY_MODE_FLAG = False
B1_SPARE = 0
TEMPERATURE_LOW_THRESHOLD = 0
B2_SPARE = 0
TEMPERATURE_HIGH_THRESHOLD = 63
HUMIDITY_LOW_THRESHOLD = 0
HUMIDITY_HIGH_THRESHOLD = 15
LIMITATION_FLAG = True
BRIGHTNESS_THRESHOLD = 0
VIBRATION_ACCELERATION_THRESHOLD = 4
B6_SPARE = 0
VIBRATION_BLANK_TIME = 2
VIBRATION_DEBOUNCE_COUNT = 2
RESET_BIT = 0
DOOR_OPEN_THRESHOLD = 7
DOOR_CLOSE_THRESHOLD = 4
```

To learn more about the device configuration parameters, you can refer to the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) document.

After you have completed the [Sigfox-GCP Integration guide](https://cloud.google.com/community/tutorials/sigfox-gw), continue with the following chapters in this tutorial.

## Streaming Data into Google BigQuery

The Sigfox-GCP integration publishes the device data to a Cloud Pub/Sub topic. To enable long-term storage and analytics for actionable insights, a best practice is to write the data to a data warehouse. This chapter shows how you can stream the data in real-time to [Google BigQuery](https://cloud.google.com/bigquery/), using a Cloud Function that is triggered by the Sens'it payloads in Pub/Sub. Sigfox Backend forwards the data payloads as-is. The payloads are binary encoded. The Cloud Function will parse the data payloads using the Sens'it V3 payload specification before writing them to BigQuery. This way, the data will be easily usable in the data warehouse as standard columns and rows, using SQL queries.

### Creating the Dataset and Table in BigQuery

To host the data in BigQuery, you will create a dataset, and a table. The table is implemented as a wide, sparse table. Wide, meaning that each data payload value available in the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) has its own column. And sparse, meaning that if a payload packet does not have a value for a certain column, the value is simply not stored for that row.

Execute the following steps on your local development machine to create the BigQuery dataset and table:

1. Change the directory back to the Google Cloud Platform community repository, and the directory for this tutorial:

```
$ cd <your local path>/community/tutorials/sigfox-sensit
```

Note: if you do not have a copy of the repository, you can clone it on your machine with:

```
$ git clone https://github.com/GoogleCloudPlatform/community.git
```

1. Change to the directory for this tutorial with:

```
$ cd community/tutorials/sigfox-sensit
```

1. Deactivate any python virtual environment that you may still have active from the previous steps, with:

```
$ deactivate
```

1. Create a new python virtual environment in the sigfox-sensit directory. Note that the python scripts that you execute locally require python 2.7:

```
$ virtualenv venv
```

1. Activate the virtual environment with:

```
$ source venv/bin/activate
```

1. Install the required python modules with:

```
(venv) $ pip install -r requirements.txt
```

1. Create the BigQuery dataset by executing the following command, using the `bq` command line tool. Note: the default value of the dataset to host Sigfox Sens'it data in BigQuery is: `sigfox`, but you can change it if necessary. Also change the value of `--location` to the [BigQuery region](https://cloud.google.com/bigquery/docs/locations) where you wish to store your Sens'it data.

```
(venv) $ bq --location=asia-northeast1 mk sigfox
```

The command should return an output similar to this:

```
Dataset 'your-project:sigfox' successfully created.
```

1.  Create the BigQuery table by executing the following command. The command uses the table schema JSON file in the same working directory.

Note: in the below command, change `your-region` to your GCP region, and change `your-project` to the GCP project where you are hosting the Sigfox-GCP integration. If necessary, you can also change the values of the BigQuery dataset name (default value: `sigfox`) and table name (default value: `sensit`).

```
(venv) $ bq --location=asia-northeast1 mk --table your-project:sigfox.sensit ./bq_sensit_table_schema.json
```

The command should return an output similar to this:

```
Table 'your-project:sigfox.sensit' successfully created.
```

### Deploying the pubsub_bigquery Cloud Function

The Sens'it payloads published in Pub/Sub are binary encoded. Additionally, the payload HEX string can either contain an 4 bytes long sensor data structure, or the 4 bytes sensor data structure plus an 8 bytes long device configuration structure.

To make the data easily usable later on, the function that consumes the payloads from Pub/Sub will first parse the binary data into normal key/value pairs, and then write them in BigQuery in rows and columns. The function uses streaming writes to BigQuery, in effect having your data warehouse updated in real-time.

Additionally, the function checks that the payload in Pub/Sub is from a Sens'it device. It does it by checking if a `deviceType` attribute is present, and then that the value matches the one assigned to your Sens'it devices. The default value is: `SIGFOX_DevKit_1`. In most cases the default value is the one assigned to Sens'it devices. But if the Sigfox Backend assigns a different device type name for your devices, the value can be configured in `sigfox-sensit/cf/.env.yaml`.

Execute the following steps on your local development machine:

1. Change to the 'cf' directory with:

```
(venv) $ cd cf
```

1. Edit the Cloud Function's environment variables configuration file, by executing for example:

```
(venv) $ vi .env.yaml
```

The file has the following default configuration parameters:

```
BIGQUERY_DATASET: sigfox
BIGQUERY_TABLE: sensit
DEVICE_TYPE: SIGFOX_DevKit_1
```

If you created the BigQuery dataset or table with a different name, update the corresponding configuration values in this file. Additionally, ensure that the value for DEVICE_TYPE matches the Device Type for your Sens'it device in your Sigfox Backend account.

1. Deploy the Cloud Function by executing the following command. Note: change the value of `region` to your preferred region, and the value of `trigger-resource` to the name of your Pub/Sub topic that the Sigfox integration uses. Note: the function is implemented in python 3 but its runtime environment is in the Google Cloud Functions service. You do not need python 3 on your local development environment for this tutorial.

```
(venv) $ gcloud beta functions deploy --region asia-northeast1 pubsub_bigquery --runtime python37 --env-vars-file .env.yaml --trigger-event=google.pubsub.topic.publish --trigger-resource=sigfox-data
```

The command should return an output similar to this:

```
updateTime: <timestamp>'
versionId: '<increment>'
```

## Sending Sensor Data

### Transmitting Data from the Device

The Sens'it V3 device has 5 different sensor modes. Each mode transmits different sensor readings with a different, mode-specific data payload binary encoding scheme. To learn more about the data payloads, refer to the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf).

To change the device mode, long-press the button. Keep the button pressed down until the light ring around the button changes to a different color. The colors match the mode icons printed on the device front panel:

<table>
  <tr>
   <td><strong>Button Color</strong>
   </td>
   <td><strong>Sensor Mode</strong>
   </td>
  </tr>
  <tr>
   <td>Green
   </td>
   <td>Temperature
   </td>
  </tr>
  <tr>
   <td>Yellow
   </td>
   <td>Light
   </td>
  </tr>
  <tr>
   <td>Light blue
   </td>
   <td>Door
   </td>
  </tr>
  <tr>
   <td>Dark blue
   </td>
   <td>Vibration
   </td>
  </tr>
  <tr>
   <td>Purple
   </td>
   <td>Magnet
   </td>
  </tr>
</table>

To transmit sensor readings, double click the button. The device will transmit sensor readings matching the current mode. The device will blink the light rapidly in three bursts, to indicate that it's transmitting. The sensor data is transmitted three times, with frequency hopping, to increase the likelihood of Sigfox base stations receiving the transmission. If the ring lights up in red color, it means that the device radio cannot transmit data at the moment. In that case, wait a moment and try again.

Note that in Sigfox, the maximum number of data uplink transmissions is 140 messages per device per day. The Sens'it device's built-in firmware has a configuration parameter `Message period` for specifying the transmission interval. Refer to the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) document and the 'Updating Sens'it Device Configurations' chapter below for more information.

### Monitoring the Data Transmission End to End

To verify that your device has sent the payload, you can use the following user interfaces:

1. In your [Sigfox Backend](https://backend.sigfox.com), select your Device > Messages, and verify that you can see the new messages.

**Figure 9.** Device messages

[messages]: img/messages.png
![device messages][messages]

1. In the [Cloud Functions console](http://console.cloud.google.com/functions), select the 'callback_data' function and select its Logs. This function was created when you followed the [Sigfox-GCP Integration guide](https://cloud.google.com/community/tutorials/sigfox-gw) earlier. Verify that you can see the new messages in Stackdriver Logging for the function. This function receives the messages from Sigfox Backend and forwards them to Cloud Pub/Sub.

**Example Stackdriver Logging for function: callback_data:**

```
Received Sigfox message:
{
  'deviceType': 'SIGFOX_DevKit_1',
  'device': '<device ID>',
  'time': '1548304947',
  'data': 'b6098880',
  'seqNumber': '2732',
  'lqi': 'Limit',
  'fixedLat': '0.0',
  'fixedLng': '0.0',
  'operatorName': 'SIGFOX_Singapore_Unabiz',
  'countryCode': '702',
  'computedLocation': {
    'lat': 1.123,
    'lng': 103.123,
    'radius': 4557,
    'source': 2,
    'status': 1
  }
}
```

1. In the Cloud Functions portal, select the 'pubsub_bigquery' function and select its Logs. Verify that the function was triggered by the new messages in Pub/Sub and that the function wrote the data to BigQuery.

**Example Stackdriver Logging for function: pubsub_bigquery:**

Receiving the binary payload message from Pub/Sub:

```
Data JSON:
{
  "deviceType": "SIGFOX_DevKit_1",
  "device": "<device ID>",
  "time": "1548304947",
  "data": "b6098880",
  "seqNumber": "2732",
  "lqi": "Limit",
  "fixedLat": "0.0",
  "fixedLng": "0.0",
  "operatorName": "SIGFOX_Singapore_Unabiz",
  "countryCode": "702",
  "computedLocation": {
    "lat": 1.123,
    "lng": 103.123,
    "radius": 4557,
    "source": 2,
    "status": 1
  }
}
```

Writing the parsed values to BigQuery. Note here that the binary hexadecimal value for `data` has been parsed to separate values:

```
BQ Row:
[('<device ID>', '2019-01-24T04:42:27+00:00', 'b6098880', '2732',
3.8000000000000003, 1, False, 24.0, 64.0, None, None, None, None, None, None,
'Limit', '0.0', '0.0', 'SIGFOX_Singapore_Unabiz', '702', {'lat': 1.123,
'lng': 103.123, 'radius': 4557, 'source': 2, 'status': 1})]
```

## Querying Sensor Data in BigQuery

### Verifying the Dataset and Table Schema

Open the [Google BigQuery console](https://console.cloud.google.com/bigquery), expand the entries under <your project name> and click on the table name. The default names for the dataset and table are `sigfox`, and `sensit`, respectively.

**Figure 10.** BigQuery dataset and table

[bq1]: img/bq1.png
![dataset and table][bq1]

**Figure 11.** Sensit table schema

[bq2]: img/bq2.png
![sensit table schema][bq2]

The table schema matches the parsed structure of the Sens'it V3 payload. The sensor values will be transmitted by the device, depending on the currently active mode. The additional values such as `computedLocation` are delivered by the Sigfox network with the optional DATA_ADVANCED Callback messages.

You can view additional table information with the Details tab, and see a preview of any entries in the table with the Preview tab.

### Querying the Sens'it Data with SQL

1. Click the Query editor text entry area, copy & paste the following example SQL query.

Example SQL query - select the latest 20 messages sent by your Sens'it. Replace `your-project` with the name of your GCP project, `sigfox` with your dataset name, and `sensit` with your table name:

```
SELECT * FROM `your-project.sigfox.sensit` ORDER BY time DESC LIMIT 20
```

1. Click Run to execute the query. The query should return an output similar to this. You can scroll the output horizontally to view the results for all the columns:

**Figure 12.** SQL query results

[bq3]: img/bq3.png
![sql query results][bq3]

To learn more about using BigQuery for analytics, refer to the [Google BigQuery documentation](https://cloud.google.com/bigquery/docs/).

## Using Sens'it V3 Payload Parser Utility

The maximum payload sizes in Sigfox are 12 bytes for data uplink, and 8 bytes for downlink messages. The Sens'it V3 device has several sensors, and user-configurable device settings.  In order to send all the relevant sensor data, and receive configuration updates, the device utilizes an efficient [binary encoding scheme](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf). Using the scheme, the device can transmit the currently active sensor readings with just 4 bytes, and accept updated device configuration sets with 8 bytes. Furthermore, the sensor data payload is flexible, with a structure that depends on the currently active device mode. The payload contains a `Mode` flag which indicates which structure the rest of the payload is encoded with.

When the device transmits data, Sigfox receives the data as the original 4 bytes binary frame. The Sigfox Backend user interface displays the payload as an 8 characters long hexadecimal string, with two characters per byte.

The Sigfox-GCP integration forwards these hexadecimal payload strings as-is through Cloud Functions to Cloud Pub/Sub. In this tutorial, the function called `pubsub_bigquery` is responsible for parsing, or decoding the binary hexadecimal string to normal key/value pairs, before writing them to columns and rows in BigQuery.

In addition to the Cloud Function, this tutorial also includes a command line utility to help encode and decode the Sens'it V3 payloads. The tool supports both sensor data, and device configuration payloads.

### Decoding Sensor Data

To decode the hexadecimal data payloads sent by the device, execute the following steps on your local development machine:

1.  If you are still in the `cf` directory, change back to the `sigfox-sensit` directory with the following command. Also ensure that you still have the Python virtual environment active:

```
(venv) $ cd ..
```

1. Double click the Sens'it button to trigger transmitting sensor readings.
1. Use the [Sigfox Backend](https://backend.sigfox.com), [Cloud Functions](https://cloud.google.com/functions) Logs, or [BigQuery](https://cloud.google.com/bigquery) SQL queries, to find the payload string sent by your Sens'it device. Example payload string: `ae098c7d`
1. Execute the parser utility with the -h flag to see its options:

```
(venv) $ python sensit-parser.py -h
```

1. Execute the following command to parse your Sens'it payload string. Replace the payload string in the command with <your payload string>:

```
(venv) $ python sensit-parser.py --parser-mode decode-data --hex-string ae098c7d
```

The command should return an output similar to this. Note that you can see how the parser decodes the 8 bits for each of the 4 bytes, and displays the values:

```
Data HEX:   ae098c7d

Bit:        76543210
            --------
Byte0:  ae  10101110
Byte1:  09  00001001
Byte2:  8c  10001100
Byte3:  7d  01111101

Container:
    battery_level = 21
    reserved = 6
    mode = 1
    button_alert_flag = False
    temperature_msb = 1
    temperature_lsb = 140
    humidity = 125

{'battery_level': 3.75, 'humidity': 62.5, 'mode': 1, 'temperature': 24.5, 'button_alert_flag': False}
```

You can use this utility to easily debug the data sent by your Sens'it device. You can also use the [Sens'it V3 payload structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) and the `sensit-parser.py` code as examples for designing your device-specific binary payloads with Sigfox. The parser leverages the Python ['construct' module](https://pypi.org/project/construct/) for implementing the payload structure in a declarative manner.

## Updating Sens'it Device Configurations

### Decoding Device Configurations

By default, the Sens'it V3 device transmits its current configuration once per day. You can identify those payload strings with their longer length. The sensor telemetry data uplink payloads are 4 bytes, or 8 hexadecimal characters. The data + configuration payloads are 4 + 8 = 12 bytes, or 24 hexadecimal characters. Example payload: `9e09a58306003f0f8004223c`. To decode the configuration payloads sent by the device, execute the following steps:

1.  Trigger the device to send its data + configuration payload, by pressing the button in the following sequence: short-short-long press. Fun fact: short-short-long corresponds with the letter 'u', in [Morse code](https://en.wikipedia.org/wiki/Morse_code) for: 'Update device configuration'.

After pressing the sequence, the device light should display three bursts, signifying the three radio transmissions (TX) for the message. Followed by the ring remaining blinking for up to 20 seconds or more. This blinking signifies that the device is waiting for the Sigfox downlink message reception window.

After transmitting the downlink request message, the device waits for 20 seconds, and then opens the radio in receiving (RX) mode for a 25 seconds window. The backend system (Google Cloud) has to return the device configuration to Sigfox Backend during the 20 second sleep time, and Sigfox has to transmit the configuration to the device during the 25 second window.

The device sets a flag `ack: True`, to mark the message as a 'Downlink requested' message. The payload in this case is the 4 bytes sensor readings structure, followed by the 8 bytes device current configuration structure. For more information, please refer to the [Downlink sequence diagram](https://cloud.google.com/community/tutorials/sigfox-gw#requesting-downlink-configurations-from-a-device) in the integration guide.

1. Verify that the device has requested a downlink message, using the Sigfox Backend > Device > Messages console.

**Figure 13.** Downlink message requested

[dl1]: img/dl1.png
![downlink requested][dl1]

**Figure 14.** Downlink response received successfully

[dl2]: img/dl2.png
![downlink response received][dl2]

1. Copy the message string and use the parser to decode it. Replace the hex-string value with your value:

```
(venv) $ python sensit-parser.py --parser-mode decode-data --hex-string b609867d06003f0f8004223c
```

The command should return an output similar to this:

```
Data HEX:   b609867d
... sensor data details ...

Config HEX: 06003f0f8004223c

Bit:        76543210
            --------
Byte0:  06  00000110
... byte values ...
Byte7:  3c  00111100

MESSAGE_PERIOD = 0
... configuration parameter values ...
DOOR_CLOSE_THRESHOLD = 4
```

This way, you can debug both the sensor values, as well as the current device configurations.

### Encoding Device Configurations

To update the device configurations, you can use the same parser utility. The utility supports generating an editable configuration file from the configuration payload. To edit the device configuration, execute the following commands:

1. Execute the parser with the same HEX value as above, and add the switch --out-file, as follows:

```
(venv) $ python sensit-parser.py --parser-mode decode-data --hex-string b609867d06003f0f8004223c --out-file config.ini
```

The command should return an output similar to this:

```
Config file written to: config.ini
```

1. Edit the generated current configurations file with your favorite editor. Refer to the [Sens'it V3 payload specification](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) for details on the parameters and their values. For example, you could change `MESSAGE_PERIOD = 1` (transmit data every hour) to: `MESSAGE_PERIOD = 0` (transmit data every 10 minutes).

```
(venv) $ vi config.ini
```

1. Execute the parser in encoding mode, to get a hexadecimal string from your updated configuration file:

```
(venv) $ python sensit-parser.py --parser-mode encode-config --in-file config.ini
```

The command should return your new Sens'it configuration string similar to this:

```
Reading config from input file: config.ini

Config HEX: 46003f0f8004223c
```

### Updating the Configuration in Datastore and Sending it Downlink

1. Copy the new Config HEX value and store it in [Cloud Datastore](https://console.cloud.google.com/datastore). The string should be the new value for the property named: `config`, for the kind: `deviceType`. Device Type should match the one for Sens'it in your Sigfox Backend.

**Figure 15.** Updating device configuration in Datastore

[ds]: img/ds-update.png
![updating config in datastore][ds]

1. Press Done, and then Save, to save the new value.
1. To send the updated configurations to the device, trigger a new downlink request message by pressing the short-short-long button sequence on your Sens'it device. Monitor the messages in Sigfox Backend and Cloud Functions Logs for the function: `callback_data`. You can use the filter box in Stackdriver Logging, to filter for the string: `downlink`:

**Figure 16.** Filtering Stackdriver logs

[log]: img/log-filter.png
![filtering logs][log]

If successful, you should see a log entry similar to this:

```
Sending downlink message: {"<device ID>": {"downlinkData": "<your new configuration string>"}}
```

Congratulations! You are now able to use all the functionality of your Sens'it it device with Google Cloud, and start analyzing its sensor data with Google BigQuery.


## Cleaning up

### Deleting Sigfox Backend Callback Configurations

If the Google Cloud integration Callbacks are the only ones configured in your Sigfox Backend for this Device Type, you can use a script to delete them all

1. On your local development machine, execute the following:

```
(venv) $ python sigfox-api.py --callbacks delete-all
```

**Note**: this command deletes *all* callbacks registered for the Device Type, including any Callbacks that you may have configured manually earlier.

If you have other Callbacks for other use cases configured for this Device Type, use the [Sigfox Backend](https://backend.sigfox.com/) > Device Type > Callbacks console to delete the 5 Callbacks configured for this integration. You can identify the integration Callbacks from the URLs that point to your Cloud Functions.

### Deleting the Google Cloud Platform project

To avoid incurring charges to your GCP account for the resources used in this tutorial, you can delete the project.

**Caution**: Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain available.

To delete a project, do the following:

1. In the GCP Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

**Figure 17.** Deleting the project

[delete-project]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png
![deleting the project][delete-project]

## What's next

- Learn more about [IoT on Google Cloud Platform](https://cloud.google.com/solutions/iot/)
- Learn more about [Big Data analytics on Google Cloud Platform](https://cloud.google.com/solutions/big-data/), to turn your IoT data into actionable insights
- Learn more about the [Google BigQuery](https://cloud.google.com/bigquery/) data warehouse for analytics
- Try out other Google Cloud Platform features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
