---
title: Integrating Sigfox IoT network with Google Cloud
description: Install and configure the integration between the Sigfox LPWAN IoT network service and Google Cloud.
author: lepistom
tags: IoT, Internet of things, Sigfox, LPWAN
date_published: 2020-04-20
---

Markku Lepisto | Solutions Architect | Google Cloud

## Objectives

This document describes how to install and configure the integration between the [Sigfox](https://www.sigfox.com/) [LPWAN](https://en.wikipedia.org/wiki/LPWAN) IoT network service and [Google Cloud](https://cloud.google.com).

The main functionalities demonstrated are the following:

- Ingest of data from Sigfox devices
- Forwarding of data to [Cloud Pub/Sub](https://cloud.google.com/pubsub/) for processing with Google Cloud services
- Sigfox device configuration management
- Sigfox network service message logging

The integration is implemented as a set of [Cloud Functions](https://cloud.google.com/functions/) that are registered as [callback functions](https://build.sigfox.com/backend-callbacks-and-api) in the Sigfox backend system. The Cloud Functions are called when devices send data or the Sigfox network sends service messages. Device configurations are stored in [Cloud Firestore](https://cloud.google.com/firestore/) and logs in [Cloud Logging](https://cloud.google.com/logging/).

The implementation is designed to be:

- Stateless
- Event-driven
- Scalable
- Low-cost

## Architecture diagram

**Figure 1.** Integration architecture

[archdiag]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/architecture.png
![architecture diagram][archdiag]

## Costs

This tutorial uses the following billable components of Google Cloud:

- Cloud Functions
- Cloud Pub/Sub
- Cloud Firestore

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Before you begin

This tutorial assumes you already have a [Google Cloud](https://console.cloud.google.com/freetrial) account set up.

This tutorial assumes you already have a [Sigfox backend account](https://support.sigfox.com/docs/backend-user-helpbook) and that you have [activated device(s)](https://support.sigfox.com/docs/sigfox-activate:-when-and-how-to-use-it) within your account.

Ensure that you can see messages sent by your device in your [Sigfox backend](https://backend.sigfox.com/), in **Device > Messages**.

**Figure 2.** Sigfox messages example

[messages]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/messages.png
![messages example][messages]

If you can see messages sent by your device, you can proceed to the next step.

## Creating a Google Cloud project

1. Go to the [Cloud Console](https://console.cloud.google.com).
1. Click the project selector in the upper-left corner and select **New Project**.
1. Give the project a name and click **Create**.
1. Click the project selector again and select your new project.
1. Open the menu **APIs & Services > Library**.
1. Search for and activate the following APIs, or ensure that they are already active:
    * Cloud Functions API
    * Cloud Pub/Sub API
    * Cloud Firestore API

## Deploying the callback Cloud Functions

### Prerequisites

1. On your local development machine, install the following tools:
    * [Google Cloud SDK](https://cloud.google.com/sdk/install) (gcloud command line tool)
    * git
    * python3
    * pip
    * curl
    * docker

1. Configure `gcloud` to use your new Google Cloud project:

        $ gcloud init

1. Create a Pub/Sub topic for your Sigfox device data:

        $ gcloud pubsub topics create sigfox-data

    In this case, the integration will forward the messages sent by your devices through the
    Sigfox backend to the Cloud Pub/Sub topic `sigfox-data`.

1. Optionally, create a Pub/Sub subscription for monitoring messages in the above topic:

        $ gcloud pubsub subscriptions create sigfox-data-sub --topic sigfox-data

1. Clone the GitHub repository associated with the community tutorials:

        $ git clone https://github.com/GoogleCloudPlatform/community.git

1. Change to the tutorial directory:

        $ cd community/tutorials/sigfox-gw

1. Create a new Python 3 virtual environment:

        $ python3 -m venv venv

1. Activate the virtual environment:

        $ source venv/bin/activate

1. Install the required python modules:

        (venv) $ pip3 install -r requirements.txt

1. Change to the `cf` directory:

        (venv) $ cd cf

    The Cloud Functions have a hidden configuration file: `.env.yaml` in the same
    directory (`sigfox-gw/cf`). The configuration parameters are read by the Cloud
    Functions when the functions are deployed. If you update the configuration file,
    you have to re-deploy the Cloud Functions to activate the new configuration.
    See the next steps on how to deploy (or re-deploy) the Cloud Functions.

1. Edit the file `.env.yaml` with a text editor. For example:

        (venv) $ vi .env.yaml

1. **Mandatory**: Change the value of `HTTP_USER` and `HTTP_PASSWORD` to your unique values. You will later use these values in the Sigfox backend Callback configurations. The Cloud Functions use Basic Authentication over HTTPS, to authenticate the Sigfox backend.

1. Deploy the two integration Cloud Functions with the following commands. Set the value of `--region` to the Cloud Functions region where you wish to store and process your data. You can select 'y' if the tool asks you 'Allow unauthenticated invocations of new function?'. The functions use HTTP Basic authentication to authenticate Sigfox backend when it calls the functions.

        (venv) $ gcloud functions deploy --region asia-northeast1 --runtime python37 --env-vars-file .env.yaml --trigger-http callback_data

        (venv) $ gcloud functions deploy --region asia-northeast1 --runtime python37 --env-vars-file .env.yaml --trigger-http callback_service

    The `callback_data` Cloud Function implements the Sigfox backend callbacks for
    receiving all data payloads, as well as responding to device configuration
    downlink calls. In the Sigfox backend, it will be used for the `BIDIR` and
    `DATA_ADVANCED` callbacks.

    The `callback_service` Cloud Function implements receiving Sigfox network
    event, error, and other control plane information messages and logging them with
    Cloud Logging. In the Sigfox backend, it will be used for the `STATUS`,
    `ACKNOWLEDGE`, and `ERROR` callbacks.

    After the deployment has finished, write down the URL for both of the deployed
    Cloud Functions.

    Example command output that shows the HTTPS Trigger URL:

        httpsTrigger:
          url: https://asia-northeast1-project.cloudfunctions.net/callback_data

    The URLs for the integration Functions are formatted as follows:

    https://region-projectname.cloudfunctions.net/callback_data

    https://region-projectname.cloudfunctions.net/callback_service

1. Navigate to the Cloud Functions web console at [https://console.cloud.google.com/functions](https://console.cloud.google.com/functions) and verify that the two Cloud Functions have been deployed:

**Figure 3.** Verifying Cloud Functions

[verify-cf]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/verify-cf.png
![verifying cloud functions][verify-cf]

## Enabling Sigfox backend API access

The integration uses Sigfox backend API V2 to automate managing the callbacks' configuration. In order to use the callback management script, you have to first create an API user. Execute the following steps:

1. Log in to the [Sigfox backend](https://backend.sigfox.com/).
1. Follow the steps in the [Sigfox API credential creation](https://support.sigfox.com/docs/api-credential-creation) document to create a new API user with the following profile: **DEVICE MANAGER [W]**.
1. Write down your Sigfox API user's **Login** and **Password** strings.
1. Click the **Device Type** menu.
1. Click the name of the device type you wish to use for this integration.
1. Write down your device type's **Id** string. It should be listed as the first value in your **Device Type > Information** page.

## Configuring Sigfox backend callbacks

### Generating the Sigfox API V2 Python client

The integration uses the Sigfox API V2 to automate configuring the callbacks. In order to generate the Python client library
for the latest version of the API, execute the following commands:

1.  On your local development machine, if you are still in the `cf` directory, change the directory back to the
    integration's main directory (`sigfox-gw`):

        (venv) $ cd ..

1.  Check that you have docker running:

        (venv) $ docker ps

    If Docker is running, you see an output similar to the following:

        CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
        
    If you get an error message, start the docker daemon on your local development machine.

1.  Next, you generate the Python client libraries from the [Sigfox API definition](https://support.sigfox.com/api/apidocs).
    To do this, you compile and use a specific version of
    [swagger-codegen](https://github.com/swagger-api/swagger-codegen). Execute the following command to set up an 
    environment variable for the swagger-codegen version tag to be used:

        (venv) $ generator_version=3.0.11

1.  The following command uses docker to download the
    [swaggerapi/swagger-codegen-cli-v3](https://hub.docker.com/r/swaggerapi/swagger-codegen-cli-v3) image and then use the 
    code generator's specific version to generate a Python client library from the Sigfox API definition:

        (venv) $  docker run --rm -v $(pwd):/local swaggerapi/swagger-codegen-cli-v3:$generator_version generate -i https://support.sigfox.com/api/apidocs -l python -o /local/out/python-$generator_version

1.  After the generation process completes, copy the generated swagger_client to the working directory:

        (venv) $ cp -r out/python-3.0.11/swagger_client .


### Configuring the callback management script

The integration has a Python script for managing the Sigfox backend callbacks' configuration. The script uses the Sigfox API credentials for authentication with the Sigfox backend, using HTTPS Basic Authentication. Execute the following steps to configure the callbacks:

1. Edit the script's configuration file, with for example:

        (venv) $ vi sigfox-api.ini

1. Set the value of `api_username` to your Sigfox API user **Login** string.
1. Set the value of `api_password` to your Sigfox API user **Password** string.
1. Set the value of `id` to your Sigfox device type **Id** string.
1. Set the value of `cf_data` to your `callback_data` Cloud Function Trigger URL. Example: `https://region-project.cloudfunctions.net/callback_data`
1. Set the value of `cf_data` to your `callback_service` Cloud Function Trigger URL. Example: `https://region-project.cloudfunctions.net/callback_service`
1. Set the value of `cf_username` to the value of the `HTTP_USER` parameter in `sigfox-gw/cf/.env.yaml`.
1. Set the value of `cf_password` to the value of the `HTTP_PASSWORD` parameter in `sigfox-gw/cf/.env.yaml`.

### Listing Sigfox backend callbacks

1. Execute the following command to see the available options:

        (venv) $ python3 sigfox-api.py -h

1. Execute the following command to list any callbacks currently configured for your Device Type:

        (venv) $ python3 sigfox-api.py --callbacks list

    If you already have some callbacks configured for the Device Type, the command will output
    the callbacks' details as well as a summary similar to this:

        {Details of all your configured callbacks}
        ...
        {total number of} Callbacks configured for Device Type: {your device type name}

    Or if you do not have any callbacks configured yet, the script will output:

        0 Callbacks configured for Device Type: {your Device Type name}


### Creating Sigfox backend callbacks

1. Execute the following command to create the 5 callbacks for the Google Cloud integration:

        (venv) $ python3 sigfox-api.py --callbacks create

    The script's output should be similar to this:

        Creating 5 callbacks.
        Done creating 5 Callbacks for Device Type: <your Device Type name>
        Enabling Downlink for BIDIR Callback
        Downlink enabled.

1. Verify the callbacks:

        (venv) $ python3 sigfox-api.py --callbacks list

    The command should output the details of all of your callbacks for this Device Type,
    including the 5 callbacks that point to your integration Cloud Functions.

1. If any of the callbacks or their values are incorrect, you can do either of the following to re-configure them:

    - Using the [Sigfox backend](https://backend.sigfox.com) console, navigate to
      **Device Type [YOUR_DEVICE_TYPE] > Callbacks**, click **Edit**, and delete
      individual callbacks.

    - Edit the script's configuration file `sigfox-api.ini` and fix any incorrect values:

            (venv) $ vi sigfox-api.ini

      Then delete *all* callbacks configured for this device type:

            (venv) $ python3 sigfox-api.py --callbacks delete-all

      **Note**: this command deletes *all* of the callbacks registered for the device type,
      including any callbacks that you may have configured manually earlier. The device
      type ID for the action is configured in `sigfox-api.ini`, as the value for the parameter
      `id`.

      Then re-execute the script to create the callbacks with the corrected values:

            (venv) $ python3 sigfox-api.py --callbacks create


## Verifying the callbacks in the Sigfox backend console

1. Navigate in the [Sigfox backend](https://backend.sigfox.com) console to **Device Type [YOUR-DEVICE-TYPE] > Callbacks**.
1. Verify that your **Callbacks** screen looks similar to this. Note that the **Downlink** button should be activated (filled in black circle) for the `BIDIR` callback:

**Figure 4.** Verifying Sigfox callbacks

[verify-callbacks]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/verify-callbacks.png
![verifying callbacks][verify-callbacks]

## Configuring Firestore for device configuration management

The integration uses the Cloud Firestore database service for storing Sigfox device configurations. In Sigfox, individual devices are grouped under device types. All devices in the same device type are expected to have the same behavior, and the same configuration. For this reason, the default behavior of the integration is to have one, shared device configuration per device type.

To configure Firestore for your integration, execute the following steps:

1.  Navigate to the Google Cloud Firestore console at [https://console.cloud.google.com/firestore](https://console.cloud.google.com/firestore)
2.  If this is the first time using Firestore in this project, you will see the following options:

**Figure 5.** Firestore options

[ds-options]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/ds-options.png
![Firestore options][ds-options]

3.  Choose the Datastore mode option.
4.  Select the geographic location where you wish to host Firestore and store your device configuration data. Choose the location nearest to the Google Cloud region where you deployed your Cloud Functions, and click **Create Database**.
5.  In the Firestore Datastore mode console, click **Create Entity**.
6.  Set the value of **Kind** to `deviceType`.
7.  Set the value of **Key identifier** to **Custom name**.
8.  Set the value of **Custom name** to your Sigfox device type name.
9.  Click **Properties > Add Property**.
10. Set the new property name as `config`.
11. Set the **Value** as your device configuration's 16-character hexadecimal string. The configuration hexadecimal string must be 8 bytes (exactly 16 characters). The configuration value is specific to each device and use case. To learn more, refer to the Sigfox [Downlink information](https://support.sigfox.com/docs/downlink-information) document.
12. Deselect the **Index this property** checkbox.
13. Click **Done**.
14. Click **Create** to save the entity. Verify that you now have a configuration entity in Firestore, with your Sigfox device type as the name. Refer to the below example:

**Figure 6.** Firestore example

[ds-example]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/ds-example.png
![Firestore example][ds-example]

# Testing the integration

## Sending data from a Sigfox device

The integration should now be configured in both Google Cloud Functions and the Sigfox backend.

Verify the `callback_data` Cloud Function with the following steps:

1.  On your development machine console, check that you have a Cloud Pub/Sub subscription, subscribed to the Pub/Sub Topic that your Cloud Functions use. Execute the following command:

        $ gcloud pubsub subscriptions list

    You should see an output similar to this:

        ...
        name: projects/[YOUR-PROJECT]/subscriptions/sigfox-data-sub
        ...
        topic: projects/[YOUR-PROJECT]/topics/sigfox-data

     Note the name of the subscription: `sigfox-data-sub`.

2.  Open both the Sigfox backend and Google Cloud Functions web console pages.
3.  (This step is dependent on the Sigfox device.) Send a data payload from your Sigfox device.
4.  Verify that you can see the new message in the Sigfox backend **Device > Messages** page, as below:

    **Figure 7.** Sigfox messages example

    [messages 2]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/messages2.png
    ![messages example][messages 2]

    If your Sigfox backend can receive the message, the up arrow will first be grayed out.
    If the Cloud Function `callback_data` was triggered successfully, and the function replied
    as expected, the arrow will turn green.

5.  Verify that the message payload was forwarded to your Cloud Pub/Sub topic. On your development machine, execute the 
    following command:

        (venv) $ gcloud pubsub subscriptions pull sigfox-data-sub --limit 100 --auto-ack

    You may need to execute the command a few times to fetch the new messages.

    The command should return an output similar to this:

        {"deviceType": "<your Device Type>", "device": "<your device ID>", "time": "1544325853",
        "data": "000102030405060708090a0b", "seqNumber": "27", "ack": "false"}

    The value of `data` should match the **Data / Decoding** output in your Sigfox
    backend **Device > Messages** history for this message.

6.  Verify that you can see the integration logs in Cloud Logging. On the Cloud Function's details page, click the **View Logs** button to open Cloud Logging for the `callback_data` function.

7.  Find the entries for `Received Sigfox message` and any entries below that. Click the entries to expand their view. You should see something similar to the following:

    **Figure 8.** Cloud Logging

    [logging]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/logging.png
    ![stackdriver logging][logging]

    The first time the Cloud Function executes, the platform creates its runtime environment and the
    execution time is longer. This is called a _cold start_ for Cloud Functions. Subsequent executions will
    be faster. Here, you can verify that the Cloud Function was triggered, received the device payload, and
    as seen in the next log entry, forwarded the payload to the Cloud Pub/Sub topic. The Pub/Sub topic is
    the integration point for consuming the Sigfox data in real time for your specific business solutions.

8.  Verify that your `DATA_ADVANCED` callback is also working, by finding a second function execution
    after the first one. The `DATA_ADVANCED` callback is a feature in the Sigfox backend to send
    additional metadata. The `DATA_ADVANCED` callback is triggered up to 30 seconds after the initial
    payload is sent, after the Sigfox network has verified that all base stations have received the
    payload from your device. Sigfox will calculate additional information such as signal strength,
    and optionally the device location with the Sigfox Atlas positioning service. These are available
    as additional metadata in the second, `DATA_ADVANCED` payload. If your `DATA_ADVANCED` callback
    was triggered, you can see a second invocation for the `callback_data` Cloud Function, and
    Cloud Logging entries similar to this:

        2019-01-08 06:34:41.248 GMT callback_data
        Received Sigfox message:
        {
            'deviceType': '<device type>', 'device': '<Device ID>', 'time': '1546929254',
            'data': 'd609912345603f0f8004223c', 'seqNumber': '424', 'lqi': 'Good',
            'fixedLat': '0.0', 'fixedLng': '0.0','operatorName': 'SIGFOX_Singapore_Unabiz',
            'countryCode': '702', 'computedLocation': {'lat': 1.2763981, 'lng': 103.7973329,
            'radius': 2447, 'source': 2, 'status': 1}
        }

    Here you can see that with the `DATA_ADVANCED` callback, the device payload is the same as in the first
    invocation, but there is more metadata such as the `lqi` radio link quality indicator and the computed
    device location with Sigfox Atlas. If you do not need this additional metadata from your devices, you
    can disable the optional `DATA_ADVANCED` callback in your Sigfox backend. However, in many cases it's
    good to process and store the first payload immediately upon receipt, and update your data store later
    on with the additional information from the `DATA_ADVANCED` callback.

## Requesting downlink configurations from a device

In Sigfox, devices must request downlink messages from the network. They do this by setting a specific flag when 
transmitting a payload. In this integration, the callback responsible for handling the downlink requests is the 
`callback_data` Cloud Function. The function checks whether the incoming request has the downlink request flag `ack` set to 
`True`. If it is, the function queries the Firestore database, using the Device Type value as the query key, and fetches 
the value of the `config` attribute in Firestore. The function then checks that the value is a maximum of 8 bytes long, as 
in the Sigfox specifications; if it is, the function returns the `config` value to Sigfox backend in its response. The 
Sigfox backend then sends the configuration downlink to the device.

**Figure 9.** Downlink sequence diagram

[downlink-sequence]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/downlink-sequence.svg
![downlink sequence][downlink-sequence]

Execute the following steps to verify the downlink functionality:

1.  Transmit a downlink request message from your Sigfox device.
2.  (This step is device-specific.) If possible, verify or output any received downlink configuration payloads
    with your device-side code.
3.  (This step is device-specific.) In the Sigfox backend, in **Device > Messages**, verify that you have
    received a message that requests a downlink. It should have two arrows, one pointing up, and one pointing
    down. The down arrow signifies the downlink request and shows its success. A green down arrow signifies
    that the callback function successfully returned a device type configuration payload. See below for an
    example:

**Figure 10.** Downlink request with a successful response

[downlink]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/downlink.png
![downlink request][downlink]

4.  Verify that you can see a similar log entry in Cloud Logging for the Cloud Function `callback_data`:

        2019-01-08 06:34:16.422 GMT callback_data
        Sending downlink message: {"<device ID>": {"downlinkData": "3030303030303030"}}
        {
         insertId:  "000000-c51e451b-8ce7-40af-1111-31123454a5256"
         labels: {…}
         logName:  "projects/project/logs/cloudfunctions.googleapis.com%2Fcloud-functions"
         receiveTimestamp:  "2019-01-08T06:34:22.0246Z"
         resource: {…}
         severity:  "INFO"
         textPayload:  "Sending downlink message: {"<device ID>": {"downlinkData": "3030303030303030"}}"
         timestamp:  "2019-01-08T06:34:16.422Z"
         trace:  "projects/project/traces/203297f46e451e991ddb11111c6"
        }

    In the log entry you can verify that your device ID is listed in the beginning of the JSON entry and that
    the value of `downlinkData` is the same HEX string as you have in Firestore for this device type.

    From now on, you can update the device type configuration value in Firestore, either manually using the
    Firestore console, or programmatically using the Google Cloud Firestore client libraries.


## Verifying service messages

Verify that you can receive service messages from the Sigfox backend by executing the following steps.

You should execute these steps only after executing the downlink tests in the previous section. You may not have any service
messages from Sigfox backend until you send a downlink response to your device. The downlink response will generate a 
subsequent `downlinkAck` service message.

1.  In the Cloud Functions console, click the `callback_service` function.
2.  Verify that you can see successful invocations, indicated by a blue line:

**Figure 11.** Service message invocation

[cf-service]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/cf-service.png
![service message invocation][cf-service]

3.  Click the **View Logs** button and find an entry similar to this:

        2019-01-08 06:34:49.307 GMT callback_service
        Received Sigfox service message: {'device': '<device ID>', 'infoCode': '0', 'infoMessage': 'Acked',
        'downlinkAck': 'true', 'downlinkOverusage': 'false'}
        {
         insertId:  "000000-000000-1111-44e6-a333-ds7sdsa"
         labels: {…}
         logName:  "projects/project/logs/cloudfunctions.googleapis.com%2Fcloud-functions"
         receiveTimestamp:  "2019-01-08T06:34:55.624Z"
         resource: {…}
         severity:  "INFO"
         textPayload:  "Received Sigfox service message: {'device': '<device ID>', 'infoCode': '0', 'infoMessage': 'Acked',         'downlinkAck': 'true', 'downlinkOverusage': 'false'}"
         timestamp:  "2019-01-08T06:34:49.307Z"
         trace:  "projects/project/traces/97db5c23e664c16c1234567831a"
        }

Here you can see the following:

- The function `callback_service` was invoked.
- The log entry shows `Received Sigfox service message` for your device ID.
- The value of `downlinkAck` is `true`, indicating that the device has received the configuration payload.

Congratulations! You have now installed and verified the integration of Sigfox with Google Cloud.

## Cleaning up

### Deleting Sigfox backend callback configurations

If the Google Cloud integration callbacks are the only ones configured in your Sigfox backend for this device type, you can
use a script to delete them all:

1. On your local development machine, execute the following:

        (venv) $ python sigfox-api.py --callbacks delete-all

**Note**: This command deletes *all* callbacks registered for the device type, including any callbacks that you may have configured manually earlier.

If you have other callbacks for other use cases configured for this device type, use the [Sigfox backend](https://backend.sigfox.com/) **Device Type > Callbacks** console to delete the five callbacks configured for this integration. You can identify the integration callbacks from the URLs that point to your Cloud Functions.

### Deleting the Google Cloud project

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

**Caution**: Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain available.

To delete a project, do the following:

1. In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

**Figure 12.** Deleting the project

[delete-project]: https://storage.googleapis.com/gcp-community/tutorials/sigfox-gw/delete-project.png
![deleting the project][delete-project]


## What's next

- Stay tuned for an upcoming tutorial on using the Sigfox [Sens'it Discovery V3](https://www.sensit.io/) device with this integration and learning how to encode and decode its binary data and configuration payloads, as well as store the data in real-time in Cloud BigQuery.
- Learn more about [IoT on Google Cloud](https://cloud.google.com/solutions/iot/).
- Learn more about [Big data analytics on Google Cloud](https://cloud.google.com/solutions/big-data/), to turn your IoT data into actionable insights
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
