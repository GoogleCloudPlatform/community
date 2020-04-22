---
title: Using Sigfox Sens'it with Google Cloud
description: Set up the Sigfox Sens'it Discovery V3 device as a dev kit, and use it with Google Cloud.
author: lepistom
tags: IoT, Internet of Things, Sigfox, LPWAN
date_published: 2020-04-22
---

Markku Lepisto | Solutions Architect | Google Cloud

## Objectives

This document describes how to start using your [Sigfox](https://www.sigfox.com/) [Sens'it Discovery V3](https://sensit.io)
device and connect it to [Google Cloud](https://cloud.google.com), with step-by-step instructions on how to
use Google Cloud services for real-time sensor data ingestion, processing, and analytics, as well as device configuration management.

The main functionalities demonstrated are the following:

- Sens'it device activation and registration as a dev kit
- Configuration for integration of Sigfox with Google Cloud
- Binary sensor data ingestion, parsing, and storage in a data warehouse
- Binary device configuration encoding, decoding, and management

![sensit and gcp](https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/sensit-gcp.jpg)

## Architecture diagram

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/architecture.svg)

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- Cloud Functions
- Cloud Pub/Sub
- Cloud Firestore
- BigQuery

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/),
but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based
on your projected production usage.

## Before you begin

This tutorial assumes that you already have a [Google Cloud account](https://console.cloud.google.com/freetrial) set up.

## Create a GCP project

1. Go to the [Cloud Console](https://console.cloud.google.com).
1. Click the project selector in the upper-left corner and select **New Project**.
1. Give the project a name and click **Create**.
1. Click the project selector again and select your new project.
1. Open the menu **APIs & Services > Library**.
1. Search for and activate the following APIs, or ensure that they are already active:
    * Cloud Functions API
    * Cloud Pub/Sub API
    * Cloud Firestore API
    * Cloud BigQuery API

## Activate your Sens'it device

Sens'it devices come with a Sigfox subscription. You must first activate the device, create a Sigfox account, and associate
the device in your account. You can activate the device using either a web portal or a mobile app. The next sections get you
started with both options.

You must be located in a [Sigfox network coverage area](https://www.sigfox.com/en/coverage) when you activate the device.

### Option 1: Activate Sens'it using the web interface

To activate the Sens'it device using the web portal, execute the following steps:

#### Step 1:

Navigate to the [sensit.io web portal](https://sensit.io) and click **Launch App**.

[acti1]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/acti1.png
![activation part 1][acti1]

#### Step 2:

Click **Activate my Sens'it**.

[acti2]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/acti2.png
![activation part 2][acti2]

#### Step 3:

Find the device ID printed on the back of the device, and enter it in the input field.

[acti3]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/acti3.png
![activation part 3][acti3]

#### Step 4:

Follow the rest of the steps of the web wizard to activate your device and register it in your sensit.io account.

### Option 2: Activate Sens'it using the mobile app

Alternatively, you can install the Sigfox Sens'it Discovery mobile app and use it to activate your device. The app is available in the [Google Play store](https://play.google.com/store/apps/details?id=com.sensitio&hl=en_US) for Android and [App Store](https://play.google.com/store/apps/details?id=com.sensitio&hl=en_US) for iOS.

To activate the Sens'it device using the mobile app, execute the following steps:

#### Step 1:

Install and open the Sens'it Discovery mobile app.

#### Step 2:

Click **Add a Sens'it**.

[app1]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/app1.png
![app part 1][app1]

#### Step 3:

Scan the QR code printed on the back of the device. If the scanning does not work, enter the ID manually using the link on the bottom of the screen.

[app2]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/app2.png
![app part 2][app2]

#### Step 4:

Confirm the scanned device ID and follow the rest of the steps to activate your device and register it in your sensit.io account.

[app3]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/app3.png
![app part 3][app3]

## Register your Sens'it as a dev kit

After you have activated your device, it should be visible in your [sensit.io](https://sensit.io) web portal. To use the
device with the [Sigfox backend](https://backend.sigfox.com) system and integrate with upstream platforms like Google Cloud, 
you need to register the device as a dev kit (development kit).

Execute the following steps to register your Sens'it as a dev kit:

1.  Follow all the steps in [this document](https://storage.sbg.cloud.ovh.net/v1/AUTH_669d7dfced0b44518cb186841d7cbd75/dev_medias/build/4059ae1jm2231vw/sensit-3-devkit-activation.pdf).

    Ensure that you enter a valid email address so that you can finalize the registration process.

1.  Wait for a few hours while Sigfox registers your new account in the Sigfox backend and communicates with the device
    to transfer it to your backend account. The delay is due to the Sigfox radio network periodically communicating
    with newly registered devices. You will receive an email after the process has finished.

## Configure the integration of Sigfox with Google Cloud

Now that you have your Sens'it device associated with your Sigfox backend, you can integrate it with Google Cloud for 
processing sensor data and managing the device configuration.

To integrate your Sigfox backend with Google Cloud, execute all the steps in the
[Sigfox and Google Cloud integration guide](https://cloud.google.com/community/tutorials/sigfox-gw). The integration guide 
helps you set up Cloud Functions for receiving data and service messages from Sigfox, Cloud Pub/Sub for ingesting the data
as a real-time stream, and Cloud Datastore for managing device group configurations.

Before you start following the integration guide, read these tips, which will help with steps in the integration guide:

-   To transmit a message from your Sens'it device, double-press the button.
-   To request a downlink message, press the button in a short-short-long sequence.
-   In the "Configuring Datastore for device configuration management" section, you can use the following hexadecimal string
    for the initial configuration value: `46003f0f8004223c`. This hexadecimal string is a valid Sens'it configuration
    payload, which corresponds with the following values:

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

To learn more about the device configuration parameters, see
[Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf).

After you have completed the [Sigfox - Google Cloud integration guide](https://cloud.google.com/community/tutorials/sigfox-gw),
continue with the following sections in this tutorial.

## Streaming data into BigQuery

The integration between Sigfox and Google Cloud publishes the device data to a Cloud Pub/Sub topic. To enable long-term 
storage and analytics for actionable insights, a best practice is to write the data to a data warehouse. This section shows 
how you can stream the data in real-time to [BigQuery](https://cloud.google.com/bigquery/), using a Cloud Function that is
triggered by the Sens'it payloads in Pub/Sub. The Sigfox backend forwards the data payloads as-is. The payloads are
binary-encoded. The Cloud Function parses the data payloads using the Sens'it V3 payload specification before writing them 
to BigQuery. This way, the data is usable in the data warehouse as standard columns and rows, using SQL queries.

### Create the dataset and table in BigQuery

To host the data in BigQuery, you create a dataset and a table. The table is implemented as a wide, sparse table:
wide, meaning that each data payload value available in the
[Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf)
has its own column; and sparse, meaning that if a payload packet does not have a value for a certain column, the value is
simply not stored for that row.

Execute the following steps on your local development machine to create the BigQuery dataset and table:

1.  Go to the directory for this tutorial in the Google Cloud Community repository:

        $ cd [your local path]/community/tutorials/sigfox-sensit

    If you do not have a copy of the repository, you can clone it on your machine with this command:

        $ git clone https://github.com/GoogleCloudPlatform/community.git

1.  Deactivate any Python virtual environment that you may still have active from previous steps:

        $ deactivate

1.  Create a new Python 3 virtual environment in the `sigfox-sensit` directory:

        $ python3 -m venv venv

    Python scripts that you execute locally require Python 3.

1.  Activate the virtual environment:

        $ source venv/bin/activate

1.  Install the required Python modules:

        (venv) $ pip3 install -r requirements.txt

1.  Create the BigQuery dataset:

        (venv) $ bq --location=asia-northeast1 mk sigfox

    The default value of the dataset to host Sigfox Sens'it data in BigQuery is `sigfox`, but you can change
    it if necessary. Also, change the value of `--location` to the
    [BigQuery region](https://cloud.google.com/bigquery/docs/locations) where you want to store your Sens'it data.

    The command should return an output similar to this:

        Dataset 'your-project:sigfox' successfully created.

1.  Create the BigQuery table:

        (venv) $ bq --location=asia-northeast1 mk --table your-project:sigfox.sensit ./bq_sensit_table_schema.json

    The command uses the table schema JSON file in the same working directory.

    Change `your-region` to your Google Cloud region, and change `your-project` to the Google Cloud project where
    you are hosting the Sigfox - Google Cloud integration. If necessary, you can also change the values of the BigQuery 
    dataset name (default value: `sigfox`) and table name (default value: `sensit`).

    The command should return an output similar to this:

        Table 'your-project:sigfox.sensit' successfully created.

### Deploy the `pubsub_bigquery` Cloud Function

The Sens'it payloads published in Pub/Sub are binary-encoded. Additionally, the payload hexadecimal string can either
contain a 4-byte sensor data structure or a 4-byte sensor data structure plus an 8-byte device configuration structure.

To make the data easily usable later, the function that consumes the payloads from Pub/Sub first parses the binary
data into normal key/value pairs and writes them in BigQuery in rows and columns. The function uses streaming writes to
BigQuery, in effect having your data warehouse updated in real-time.

Additionally, the function checks that the payload in Pub/Sub is from a Sens'it device by checking whether a `deviceType` attribute is present and whether that value matches the one assigned to your Sens'it devices. The default value is `SIGFOX_DevKit_1`. In most cases, the default value is the one assigned to Sens'it devices. If the Sigfox backend assigns a different device type name for your devices, you can configure the value in `sigfox-sensit/cf/.env.yaml`.

Execute the following steps on your local development machine:

1.  Go to the `cf` directory:

        (venv) $ cd cf

1.  Edit the Cloud Function environment variable configuration file:

        (venv) $ vi .env.yaml

    The file has the following default configuration parameters:

        BIGQUERY_DATASET: sigfox
        BIGQUERY_TABLE: sensit
        DEVICE_TYPE: SIGFOX_DevKit_1

    If you created the BigQuery dataset or table with a different name, update the corresponding configuration values in
    this file. Additionally, ensure that the value for `DEVICE_TYPE` matches the device type for your Sens'it device in
    your Sigfox backend account.

1.  Deploy the Cloud Function by executing the following command. Change the value of `region` to your preferred
    region, and the value of `trigger-resource` to the name of your Pub/Sub topic that the Sigfox integration uses.

        (venv) $ gcloud functions deploy --region asia-northeast1 pubsub_bigquery --runtime python37 --env-vars-file .env.yaml --trigger-event=google.pubsub.topic.publish --trigger-resource=sigfox-data

    You can select 'y' for the prompt `Allow unauthenticated invocations of new function [pubsub_bigquery]?`. The command should return an output similar to this:

        updateTime: [timestamp]
        versionId: [increment]

## Sending sensor data

### Transmit data from the device

The Sens'it V3 device has five different sensor modes. Each mode transmits different sensor readings with a different,
mode-specific data payload binary encoding scheme. To learn more about the data payloads, see
the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf).

To change the device mode, long-press the button. Keep the button pressed until the light ring around the button changes
to a different color. The colors match the mode icons printed on the device front panel:

| button color | sensor mode |
|--------------|-------------|
| green        | temperature |
| yellow       | light       |
| light blue   | door        |
| dark blue    | vibration   |
| purple       | magnet      |


To transmit sensor readings, double-press the button. The device transmits sensor readings matching the current mode. The
device blinks the light rapidly in three bursts to indicate that it's transmitting. The sensor data is transmitted three
times, with frequency hopping, to increase the likelihood of Sigfox base stations receiving the transmission. If the ring
is red, the device radio cannot transmit data at the moment. In that case, wait a moment and try again.

Note that in Sigfox, the maximum number of data uplink transmissions is 140 messages per device per day. The Sens'it
device's built-in firmware has a configuration parameter `Message period` for specifying the transmission interval. See
the [Sens'it Discovery Payload Structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf)
document and the "Updating Sens'it device configuration" section below for more information.

### Monitoring data transmission end to end

To verify that your device has sent the payload, do the following:

#### Step 1:

In the [Sigfox backend](https://backend.sigfox.com), verify that you can see the new messages in **Device > Messages**.

[messages]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/messages.png
![device messages][messages]

#### Step 2:

In the [Cloud Functions console](http://console.cloud.google.com/functions), select the `callback_data` function and select
its Logs. This function was created when you followed the
[Sigfox - Google Cloud integration guide](https://cloud.google.com/community/tutorials/sigfox-gw) earlier. Verify that you 
can see the new messages in Cloud Logging for the function. This function receives the messages from Sigfox backend 
and forwards them to Pub/Sub.

**Example Cloud Logging for the `callback_data` function:**

    Received Sigfox message:
    {
      'deviceType': 'SIGFOX_DevKit_1',
      'device': '[device ID]',
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

#### Step 3:

In the Cloud Functions portal, select the `pubsub_bigquery` function and select its Logs. Verify that the function was triggered by the new messages in Pub/Sub and that the function wrote the data to BigQuery.

**Example Cloud Logging for the `pubsub_bigquery` function:**

Receiving the binary payload message from Pub/Sub:

    Data JSON:
    {
      "deviceType": "SIGFOX_DevKit_1",
      "device": "[device ID]",
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

Writing the parsed values to BigQuery:

    BQ Row:
    [('[device ID]', '2019-01-24T04:42:27+00:00', 'b6098880', '2732',
    3.8000000000000003, 1, False, 24.0, 64.0, None, None, None, None, None, None,
    'Limit', '0.0', '0.0', 'SIGFOX_Singapore_Unabiz', '702', {'lat': 1.123,
    'lng': 103.123, 'radius': 4557, 'source': 2, 'status': 1})]

The binary hexadecimal value for `data` has been parsed to separate values.

## Querying sensor data in BigQuery

### Verifying the dataset and table schema

Open the [BigQuery console](https://console.cloud.google.com/bigquery), expand the entries under your project name, and click the table name. The default names for the dataset and table are `sigfox` and `sensit`, respectively.

**BigQuery dataset and table**

[bq1]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/bq1.png
![dataset and table][bq1]

**Sensit table schema**

[bq2]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/bq2.png
![sensit table schema][bq2]

The table schema matches the parsed structure of the Sens'it V3 payload. The sensor values are transmitted by the device,
depending on the currently active mode. The additional values such as `computedLocation` are delivered by the Sigfox network
with the optional `DATA_ADVANCED` callback messages.

You can view additional table information with the **Details** tab, and see a preview of any entries in the table with
the **Preview** tab.

### Querying the Sens'it data with SQL

#### Step 1:

Click the Query editor text entry area and copy and paste the following example SQL query.

    SELECT * FROM `[your-project].[sigfox].[sensit]` ORDER BY time DESC LIMIT 20

This example SQL query selects the latest 20 messages sent by your Sens'it. Replace `[your-project]` with the name of your
Google Cloud project, `[sigfox]` with your dataset name, and `[sensit]` with your table name.


#### Step 2:

Click **Run** to execute the query.

The query should return an output similar to this:

[bq3]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/bq3.png
![sql query results][bq3]

 You can scroll the output horizontally to view the results for all the columns.

To learn more about using BigQuery for analytics, refer to the [BigQuery documentation](https://cloud.google.com/bigquery/docs/).

## Using the Sens'it V3 payload parser utility

The maximum payload sizes in Sigfox are 12 bytes for data uplink and 8 bytes for downlink messages. The Sens'it V3 device
has several sensors and user-configurable device settings. To send all of the relevant sensor data and receive configuration
updates, the device uses an efficient
[binary encoding scheme](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf). Using the scheme,
the device can transmit the currently active sensor readings with just 4 bytes, and accept updated device configuration sets
with 8 bytes. Furthermore, the sensor data payload is flexible, with a structure that depends on the currently active device
mode. The payload contains a `Mode` flag, which indicates which structure the rest of the payload is encoded with.

When the device transmits data, Sigfox receives the data as the original 4-byte binary frame. The Sigfox backend user
interface displays the payload as an 8-character hexadecimal string, with 2 characters per byte.

The Sigfox - Google Cloud integration forwards these hexadecimal payload strings as-is through Cloud Functions to Pub/Sub. 
In this tutorial, the `pubsub_bigquery` function is responsible for decoding the binary hexadecimal string to normal
key/value pairs before writing them to columns and rows in BigQuery.

In addition to the Cloud Function, this tutorial also includes a command-line utility to help encode and decode the Sens'it
V3 payloads. The tool supports both sensor data and device configuration payloads.

### Decoding sensor data

To decode the hexadecimal data payloads sent by the device, execute the following steps on your local development machine:

1.  If you are still in the `cf` directory, ensure that you still have the Python virtual environment active and go to
    the `sigfox-sensit` directory:

        (venv) $ cd ..

1.  Double-press the Sens'it button to trigger transmitting sensor readings.
1.  Use the [Sigfox backend](https://backend.sigfox.com), [Cloud Functions](https://cloud.google.com/functions) Logs,
    or [BigQuery](https://cloud.google.com/bigquery) SQL queries, to find the payload string sent by your Sens'it device.
    Example payload string: `ae098c7d`.
1.  Run the parser utility with the `-h` flag to see its options:

        (venv) $ python3 sensit-parser.py -h

1.  Use the following command to parse your Sens'it payload string; replace the payload string in the command with your
    payload string:

        (venv) $ python3 sensit-parser.py --parser-mode decode-data --hex-string ae098c7d

    The command should return an output similar to this. Note that you can see how the parser decodes the 8 bits for each of
    the 4 bytes, and displays the values:

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

You can use this utility to easily debug the data sent by your Sens'it device. You can also use the
[Sens'it V3 payload structure](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf) and
the `sensit-parser.py` code as examples for designing your device-specific binary payloads with Sigfox. The parser
uses the Python [`construct` module](https://pypi.org/project/construct/) for implementing the payload structure in a declarative manner.

## Updating Sens'it device configurations

### Decoding device configurations

By default, the Sens'it V3 device transmits its current configuration once per day. You can identify those payload strings
by their greater length. The sensor telemetry data uplink payloads are 4 bytes, or 8 hexadecimal characters. The
data + configuration payloads are 4 + 8 = 12 bytes, or 24 hexadecimal characters. Example payload: `9e09a58306003f0f8004223c`.

To decode the configuration payloads sent by the device, execute the following steps:

#### Step 1:

Trigger the device to send its data + configuration payload, by pressing the button in the following sequence:
short-short-long press. Fun fact: short-short-long corresponds with the letter 'u', in
[Morse code](https://en.wikipedia.org/wiki/Morse_code) for "Update device configuration".

After pressing the sequence, the device light should display three bursts, signifying the three radio transmissions
(TX) for the message. Followed by the ring remaining blinking for up to 20 seconds or more. This blinking signifies
that the device is waiting for the Sigfox downlink message reception window.

After transmitting the downlink request message, the device waits for 20 seconds, and then opens the radio in
receiving (RX) mode for a 25 seconds window. The backend system (Google Cloud) must return the device configuration
to the Sigfox backend during the 20 second sleep time, and Sigfox must transmit the configuration to the device during
the 25 second window.

The device sets a flag `ack: True`, to mark the message as a "Downlink requested" message. The payload in this case
is the 4-byte sensor readings structure, followed by the 8-byte device current configuration structure. For more
information, see the [downlink sequence diagram](https://cloud.google.com/community/tutorials/sigfox-gw#requesting-downlink-configurations-from-a-device) in the integration guide.

#### Step 2:

Verify that the device has requested a downlink message, using the Sigfox Backend > Device > Messages console.

**Downlink message requested**

[dl1]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/dl1.png
![downlink requested][dl1]

**Downlink response received successfully**

[dl2]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/dl2.png
![downlink response received][dl2]

#### Step 3:

Copy the message string and use the parser to decode it. Replace the hexadecimal string value with your value:

    (venv) $ python3 sensit-parser.py --parser-mode decode-data --hex-string b609867d06003f0f8004223c

The command should return an output similar to this:

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

This way, you can debug both the sensor values and the current device configurations.

### Encoding device configurations

To update the device configurations, you can use the same parser utility. The utility can generate an editable
configuration file from the configuration payload.

To edit the device configuration, execute the following commands:

1.  Execute the parser with the same HEX value as above, and add the switch --out-file, as follows:

        (venv) $ python3 sensit-parser.py --parser-mode decode-data --hex-string b609867d06003f0f8004223c --out-file config.ini

    The command should return an output similar to this:

        Config file written to: config.ini

1.  Edit the generated current configurations file with your favorite editor. Refer to the
    [Sens'it V3 payload specification](https://ask.sigfox.com/storage/attachments/585-sensit-3-discovery-payload.pdf)
    for details on the parameters and their values. For example, you could change `MESSAGE_PERIOD = 1` (transmit data
    every hour) to: `MESSAGE_PERIOD = 0` (transmit data every 10 minutes).

        (venv) $ vi config.ini

1.  Run the parser in encoding mode, to get a hexadecimal string from your updated configuration file:

        (venv) $ python3 sensit-parser.py --parser-mode encode-config --in-file config.ini

    The command should return your new Sens'it configuration string similar to this:

        Reading config from input file: config.ini

        Config HEX: 46003f0f8004223c

### Updating the configuration in Firestore and sending it with downlink

#### Step 1:

Copy the new Config hexadecimal value and store it in [Cloud Firestore](https://console.cloud.google.com/firestore). The
string should be the new value for the property named: `config`, for the kind: `deviceType`. Device Type should match the
one for Sens'it in your Sigfox backend.

[ds]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/ds-update.png
![updating config in datastore][ds]

#### Step 2:

Press Done, and then Save, to save the new value.

#### Step 3:

To send the updated configurations to the device, trigger a new downlink request message by pressing the short-short-long
button sequence on your Sens'it device. Monitor the messages in Sigfox Backend and Cloud Functions Logs for the function
`callback_data`. You can use the filter box in Cloud Logging, to filter for the string `downlink`.

[log]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-sensit/log-filter.png
![filtering logs][log]

If successful, you should see a log entry similar to this:

    Sending downlink message: {"[device ID]": {"downlinkData": "[your new configuration string]"}}

Congratulations! You are now able to use all of the functionality of your Sens'it it device with GCP, and start
analyzing its sensor data with BigQuery.

## Cleaning up

### Deleting Sigfox backend callback configurations

If the Google Cloud integration callbacks are the only ones configured in your Sigfox backend for this device type, you can 
use a script to delete them all:

On your local development machine, execute the following:

    (venv) $ python3 sigfox-api.py --callbacks delete-all

**Important**: this command deletes *all* callbacks registered for the device type, including any callbacks that you may
have configured manually earlier.

If you have other callbacks for other use cases configured for this device type, use
the [Sigfox backend](https://backend.sigfox.com/) **Device Type > Callbacks** console to delete the 5 callbacks configured
for this integration. You can identify the integration callbacks from the URLs that point to your Cloud Functions.

### Delete the Google Cloud project

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

**Caution**: Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
an `appspot.com` URL, remain available.

To delete a project, do the following:

1. In the GCP Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

[delete-project]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png
![deleting the project][delete-project]

## What's next

- Learn more about [IoT on Google Cloud](https://cloud.google.com/solutions/iot/)
- Learn more about [big data analytics on Google Cloud](https://cloud.google.com/solutions/big-data/), to turn your IoT data into actionable insights
- Learn more about the [BigQuery](https://cloud.google.com/bigquery/) data warehouse for analytics
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
