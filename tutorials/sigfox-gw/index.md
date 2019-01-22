---
title: Integrating Sigfox IoT Network with Google Cloud
description: Install and configure the integration between the Sigfox LPWAN IoT network service, and Google Cloud Platform.
author: lepistom
tags: IoT, Internet of Things, Sigfox, LPWAN
date_published: 2019-01-31
---

Markku Lepisto | Solutions Architect | Google Cloud

## Objectives

This document describes how to install and configure the integration between the [Sigfox](https://www.sigfox.com/) [LPWAN](https://en.wikipedia.org/wiki/LPWAN) IoT network service, and [Google Cloud Platform](https://cloud.google.com).

The main functionalities demonstrated are:

- Sigfox devices data ingest and forward to [Cloud Pub/Sub](https://cloud.google.com/pubsub/) for subsequent processing with GCP services
- Sigfox device configuration management
- Sigfox network service message logging

The integration is implemented as a set of [Cloud Functions](https://cloud.google.com/functions/) that are registered as [Callback functions](https://build.sigfox.com/backend-callbacks-and-api) in the Sigfox backend system. The Functions are called when devices send data, or the Sigfox network sends service messages. Device configurations are stored in [Cloud Datastore](https://cloud.google.com/datastore/) and logs in [Stackdriver Logging](https://cloud.google.com/logging/).

The implementation is designed to be:

- Stateless
- Event-driven
- Scalable
- Low cost

## Architecture Diagram
**Figure 1.** *Integration architecture*

[archdiag]: img/architecture.png
![architecture diagram][archdiag]

## Costs

This tutorial uses billable components of GCP, including:

- Cloud Functions
- Cloud Pub/Sub
- Cloud Datastore

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Before you begin

This tutorial assumes you already have a [Cloud Platform](https://console.cloud.google.com/freetrial) account set up.

This tutorial assumes you already have a [Sigfox backend account](https://support.sigfox.com/docs/backend-user-helpbook) and that you have [activated device(s)](https://support.sigfox.com/docs/sigfox-activate:-when-and-how-to-use-it) within your account.

Ensure that you can see Messages sent by your device in your [Sigfox backend](https://backend.sigfox.com/)  > Device > Messages

**Figure 2.** _Sigfox messages example_

[messages]: img/messages.png
![messages example][messages]

If you can see messages sent by your device, you can proceed to the next step.

## Creating a Google Cloud Platform Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com).
1. Open the Projects pulldown menu in the menu bar on the top and select 'New Project'.
1. Give the project a name and create it.
1. Switch to your newly created project with the Projects pull-down menu.
1. Open the menu > APIs & Services > Library.
1. Search for and activate the following APIs, or ensure that they are already active:
    1. Cloud Functions API
    1. Cloud Pub/Sub API
    1. Cloud Datastore API

## Deploying the Callback Cloud Functions

### Pre-requisites

1. On your local development machine, install the following tools:
    1. [Google Cloud SDK](https://cloud.google.com/sdk/install) (gcloud command line tool)
    1. git
    1. python
    1. pip
    1. virtualenv
    2. curl
1. Configure gcloud to use your new GCP project with:
```
$ gcloud init
```
1. Create a Pub/Sub topic for your Sigfox device data with e.g:
```
$ gcloud pubsub topics create sigfox-data
```
In this case, the integration will forward the messages sent by your devices via the Sigfox backend, to the Cloud Pub/Sub topic: sigfox-data.
1. Optionally, create a Pub/Sub subscription for monitoring messages in the above topic:
```
$ gcloud pubsub subscriptions create sigfox-data-sub --topic sigfox-data
```
1. Clone the GitHub repository associated with the community tutorials:
```
$ git clone https://github.com/GoogleCloudPlatform/community.git
```
1. Change to the tutorial directory with:
```
$ cd community/tutorials/sigfox-gw
```
1. Create a new python virtual environment with:
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
1. Change to the 'cf' directory with:
```
(venv) $ cd cf
```
The Cloud Functions have a hidden configuration file: .env.yaml in the same directory (sigfox-gw/cf). The configuration parameters are read by the Cloud Functions when the functions are deployed. If you update the configuration file, you have to re-deploy the Cloud Functions to activate the new configuration. See the next steps on how to deploy (or re-deploy) the Cloud Functions.
1. Edit the file .env.yaml with your favorite text editor, for example:
```
(venv) $ vi .env.yaml
```
1. **Mandatory** change the value of HTTP_USER and HTTP_PASSWORD to your unique values. You will later use these values in the Sigfox backend Callback configurations. The Cloud Functions use Basic Authentication over HTTPS, to authenticate the Sigfox backend.
1. Deploy the two integration Cloud Functions with the following commands. Note: set the value of --region to the Cloud Functions region where you wish to store and process your data.
```
(venv) $ gcloud beta functions deploy --region asia-northeast1 --runtime python37 --env-vars-file .env.yaml --trigger-http callback_data
```
```
(venv) $ gcloud beta functions deploy --region asia-northeast1 --runtime python37 --env-vars-file .env.yaml --trigger-http callback_service
```
    The callback_data Cloud Function implements the Sigfox backend Callbacks for receiving all data payloads, as well as responding to device configuration downlink calls. In the Sigfox backend, it will be used for the BIDIR and DATA_ADVANCED callbacks.

    The callback_service Cloud Function implements receiving Sigfox network event, error and other control plane information messages and logging them with Stackdriver Logging. In the Sigfox backend, it will be used for the STATUS, ACKNOWLEDGE and ERROR callbacks.

    After the deployment has finished, write down the URL for both of the deployed Cloud Functions.

    Example command output that shows the HTTPS Trigger URL:
    ```
    httpsTrigger:
      url: https://asia-northeast1-project.cloudfunctions.net/callback_data
    ```
    The URLs for the integration Functions are formatted as follows:

    https://region-projectname.cloudfunctions.net/callback_data

    https://region-projectname.cloudfunctions.net/callback_service

1. Navigate to the Cloud Functions web console at: [https://console.cloud.google.com/functions](https://console.cloud.google.com/functions) and verify that the two Cloud Functions have been deployed:

**Figure 3.** _Verifying Cloud Functions_

[verify-cf]: img/verify-cf.png
![verifying cloud functions][verify-cf]

## Enabling Sigfox backend API Access

The integration uses Sigfox backend API V2 to automate managing the Callbacks' configuration. In order to use the callback management script, you have to first create an API user. Execute the following steps:

1. Login to the [Sigfox backend](https://backend.sigfox.com/).
1. Follow the steps in the [Sigfox API credential creation](https://support.sigfox.com/docs/api-credential-creation) document to create a new API user with the following profile: **DEVICE MANAGER [W]**.
1. Write down your Sigfox API user's 'Login' and 'Password' strings.
1. Click the Device Type menu.
1. Click the Name of the Device Type you wish to use for this integration.
1. Write down your Device Type's 'Id' string. It should be listed as the first value in your Device Type > Information page.

## Configuring Sigfox Backend Callbacks

### Generating the Sigfox API V2 Python Client
The integration uses the Sigfox API V2 to automate configuring the Callbacks. In order to generate the Python client library for the latest version of the API, execute the following commands:

1. On your local development machine, if you are still in the 'cf' directory, change the directory back to the integration's main directory (sigfox-gw) with:
```
(venv) $ cd ..
```
1. Generate a Python client library from the Sigfox API V2 definition, with:
```
curl -X POST -H "content-type:application/json" -d '{"swaggerUrl":"https://support.sigfox.com/api/apidocs"}' https://generator.swagger.io/api/gen/clients/python
```
3. The command will output a URL to download the generated client library. Copy the URL and download the file with a command similar to this:
```
(venv) $ curl -o python_client.zip https://generator.swagger.io/api/gen/download/<your-unique-string>
```
5. Unzip the downloaded client library with:
```
(venv) $ unzip python_client.zip
```
7. Copy the swagger_client to the working directory with:
```
(venv) $ cp -r python-client/swagger_client .
```

### Configuring the Callbacks Management Script

The integration has a python script for managing the Sigfox backend Callbacks' configuration. The script uses the Sigfox API credentials for authentication with Sigfox backend, using HTTPS Basic Authentication. Execute the following steps to configure the Callbacks:

1. Edit the script's configuration file, with for example:
```
(venv) $ vi sigfox-api.ini
```
1. Set the value of 'api_username' to your Sigfox API user 'Login'.
1. Set the value of 'api_password' to your Sigfox API user 'Password'.
1. Set the value of 'id' to your Sigfox Device Type 'Id'.
1. Set the value of 'cf_data' to your 'callback_data' Cloud Function Trigger URL. Example: https://region-project.cloudfunctions.net/callback_data
1. Set the value of 'cf_data' to your 'callback_service' Cloud Function Trigger URL. Example: https://region-project.cloudfunctions.net/callback_service
1. Set the value of 'cf_username' to the value of sigfox-gw/cf/.env.yaml parameter: 'HTTP_USER'.
1. Set the value of 'cf_password' to the value of sigfox-gw/cf/.env.yaml parameter: 'HTTP_PASSWORD'.

### Listing Sigfox Backend Callbacks
1. Execute the following command to see the available options:
```
(venv) $ python sigfox-api.py -h
```
1. Execute the following command to list any Callbacks currently configured for your Device Type:
```
(venv) $ python sigfox-api.py --callbacks list
```
    If you already have some Callbacks configured for the Device Type, the command will output the Callbacks' details as well as a summary similar to this:
```
<Details of all your configured Callbacks>
...
<total number of> Callbacks configured for Device Type: <your Device Type name>
```
    Or if you do not have any Callbacks configured yet, the script will output:
```
0 Callbacks configured for Device Type: <your Device Type name>
```

### Creating Sigfox Backend Callbacks
1. Execute the following command to create the 5 Callbacks for the Google Cloud integration:
```
(venv) $ python sigfox-api.py --callbacks create
```

    The script's output should be similar to this:
    ```
    Creating 5 callbacks.
    Done creating 5 Callbacks for Device Type: <your Device Type name>
    Enabling Downlink for BIDIR Callback
    Downlink enabled.
    ```

1. Verify the Callbacks by executing:
```
(venv) $ python sigfox-api.py --callbacks list
```
    The command should output the details of all your Callbacks for this Device Type, including the 5 Callbacks that point to your integration Cloud Functions. 

1. If any of the Callbacks or their values are incorrect, you can do any of the following steps to re-configure them:
    1. Using the [Sigfox backend](https://backend.sigfox.com) console:
        1. Navigate to the console > Device Type <your device type> > Callbacks, and click Edit
        1. Delete individual Callbacks with the console > Device Type > Callbacks page

        Or alternatively:

    1. Using the script
        1. Edit the script's configuration file sigfox-api.ini and fix any incorrect values, with:
        ```
        (venv) $ vi sigfox-api.ini
        ```
        1. Delete **all** Callbacks configured for this Device Type, with:
        ```
        (venv) $ python sigfox-api.py --callbacks delete-all
        ```
        **Note**: this command deletes **all** the callbacks registered for the Device Type, including any Callbacks that you may have configured manually earlier. The Device Type ID for the action is configured in sigfox-api.ini, as the value for the parameter 'id'.
        1. Re-execute the script to create the Callbacks with the corrected values, with:
        ```
        (venv) $ python sigfox-api.py --callbacks create
        ```

## Verifying the Callbacks in the Sigfox Backend Console

1. Navigate to the [Sigfox backend](https://backend.sigfox.com) console > Device Type <your device type> > Callbacks
1. Verify that your Callbacks screen looks similar to this. Note that the Downlink button should be activated (filled in black circle) for the BIDIR Callback:

**Figure 4.** _Verifying Sigfox Callbacks_

[verify-callbacks]: img/verify-callbacks.png
![verifying callbacks][verify-callbacks]

## Configuring Datastore for Device Configuration Management

The Integration uses the Cloud Datastore database service for storing Sigfox device configurations. In Sigfox, individual devices are grouped under Device Types. All devices in the same Device Type are expected to have the same behaviour, and the same configuration. For this reason, the default behaviour of the Integration is to have one, shared device configuration per Device Type.

To configure Datastore for your Integration, execute the following steps:

1. Navigate to the Google Cloud Datastore console at: [https://console.cloud.google.com/datastore](https://console.cloud.google.com/datastore).
1. If this is the first time using Datastore in this project, you will see the following options:

**Figure 5.** _Datastore Options_

[ds-options]: img/ds-options.png
![datastore options][ds-options]

1. Choose the Cloud Datastore option.
1. Select the geographic location where you wish to host Datastore and store your Device configuration data. Choose the location nearest to the GCP region where you deployed your Cloud Functions, and click 'Create Database'.

**Figure 6.** _Select Datastore region_

[ds-region]: img/ds-region.png
![datastore region][ds-region]

1. In the Datastore console, click 'Create Entity'
1. Set the value of 'Kind' to: deviceType
1. Set the value of 'Key identifier' to: Custom name
1. Set the value of 'Custom name' to: &lt;your Sigfox Device Type name>
1. Click Properties > Add Property.
1. Set the New property 'Name' as: config
1. Set the 'Value' as: &lt;your device configuration 16 characters long hexadecimal string>.
_Note - the configuration HEX string must be 8 bytes long, i.e exactly 16 characters. The configuration value is device and use case specific. To learn more, refer to the Sigfox [Downlink Information](https://support.sigfox.com/docs/downlink-information) document._
1. Unselect the 'Index this property' check box
1. Click 'Done'.
1. Click 'Create' to save the entity. Verify that you now have a configuration entity in Datastore, with your Sigfox Device Type as the name. Refer to the below example:

**Figure 7.** _Datastore example_

[ds-example]: img/ds-example.png
![datastore example][ds-example]

# Testing the Integration

## Sending Data from a Sigfox Device
The Integration should now be configured in both Google Cloud Functions, and Sigfox backend.

Verify the _callback_data_ Cloud Function with the following steps:

1. On your development machine console, check that you have a Cloud Pub/Sub subscription, subscribed to the Pub/Sub Topic that your Cloud Functions use. Execute the following command:
```
$ gcloud pubsub subscriptions list
```
    You should see an output similar to this:
    ```
    ...
    name: projects/<your-project>/subscriptions/sigfox-data-sub
    ...
    topic: projects/<your-project>/topics/sigfox-data
    ```
     Note the name of the subscription. Here it is: 'sigfox-data-sub'.

1. Open both the Sigfox backend and Google Cloud Functions web console pages.
1. _NOTE - this step is Sigfox device dependent:_ Send a data payload from your Sigfox device.
1. Verify that you can see the new message in the Sigfox backend > Device > Messages page, as below:

**Figure 8.** _Sigfox messages example_

[messages 2]: img/messages2.png
![messages example][messages 2]

Note - if your Sigfox backend can receive the message, the 'up arrow' will first be greyed out. If the GCP Cloud Function _callback_data_ was triggered successfully, and the function replied as expected, the arrow will turn green.

1. Verify that the message payload was forwarded to your Cloud Pub/Sub topic. On your development machine, execute the following command:
```
(venv) $ gcloud pubsub subscriptions pull sigfox-data-sub --limit 100 --auto-ack
```

    Note - you may have to execute the command a few times, to fetch the new messages.

    The command should return an output similar to this:
```
{"deviceType": "<your Device Type>", "device": "<your device ID>", "time": "1544325853",
"data": "000102030405060708090a0b", "seqNumber": "27", "ack": "false"}
```
The value of 'data' should match the Data / Decoding output in your Sigfox backend > Device > Messages history for this message.

1. Verify that you can see the Integration logs in Stackdriver Logging. On the Cloud Function's details page, click the 'View Logs' button to open Stackdriver Logging for the _callback_data_ function.

1. Find the entries for 'Received Sigfox message' and any entries below that. Click the entries to expand their view. You should see something similar to:

**Figure 9.** _Stackdriver Logging_

[logging]: img/logging.png
![stackdriver logging][logging]

Note - the first time the Cloud Function executes, the platform creates its runtime environment and the execution time is longer. This is called a 'cold start' for Cloud Functions. Subsequent executions will be faster. Here, you can verify that the Cloud Function was triggered, received the device payload, and as seen in the next log entry, forwarded the payload to the Cloud Pub/Sub topic. The Pub/Sub topic is the integration point for consuming the Sigfox data in real-time for your specific business solutions.

1. Verify that your Data Advanced Callback is also working, by finding a second function execution after the first one. The Data Advanced Callback is a functionality in the Sigfox backend to send additional metadata. The Data Advanced Callback is triggered up to 30 seconds after the initial payload is sent, after the Sigfox network has verified that all base stations have received the payload from your device. Sigfox will calculate additional information such as signal strength, and optionally the device location with the Sigfox Atlas positioning service. These are available as additional metadata in the second, Data Advanced payload. If your Data Advanced Callback was triggered, you can see a second invocation for the _callback_data_ Cloud Function, and Stackdriver Logging entries similar to this:
```
2019-01-08 06:34:41.248 GMT callback_data
Received Sigfox message:
{
    'deviceType': '<device type>', 'device': '<Device ID>', 'time': '1546929254',
    'data': 'd609912345603f0f8004223c', 'seqNumber': '424', 'lqi': 'Good',
    'fixedLat': '0.0', 'fixedLng': '0.0','operatorName': 'SIGFOX_Singapore_Unabiz',
    'countryCode': '702', 'computedLocation': {'lat': 1.2763981, 'lng': 103.7973329,
    'radius': 2447, 'source': 2, 'status': 1}
}
```

Here we can see that with the Data Advanced callback, the device payload is the same as in the first invocation, but we have more metadata such as the 'lqi' radio link quality indicator, and the computed device location with Sigfox Atlas. If you do not need this additional metadata from your devices, you can disable the optional DATA_ADVANCED Callback in your Sigfox backend. However, in many cases it's good to process and store the first payload immediately upon reception, and update your data store later on with the additional information from the Data Advanced Callback.

## Requesting Downlink Configurations from a Device

In Sigfox, devices have to request Downlink messages from the network. They do this by setting a specific flag when transmitting a payload. In this integration, the Callback responsible for handling the Downlink requests is the _callback_data_ Cloud Function. The function checks if the incoming request has the Downlink request flag "ack" set to True. If it is, the function will query the Datastore database, using the Device Type value as the query key, and fetches the value of the _config_ attribute in Datastore. The function then checks that the value is maximum 8 bytes long as in the Sigfox specifications, and if it is, the function will return the config value to Sigfox backend in its response. Sigfox backend will then send the configuration downlink to the device.

**Figure 10.** _Downlink sequence diagram_

[downlink-sequence]: img/downlink-sequence.svg
![downlink sequence][downlink-sequence]

Execute the following steps to verify the Downlink functionality:

1. Transmit a Downlink request message from your Sigfox device.
_Note: this step and the next one are device specific._
1. If possible, verify or output any received Downlink config payload with your device side code
1. In the Sigfox backend > Device > Messages, verify that you have received a message which requests a Downlink. It should have two arrows, one pointing up, and one pointing down. The down arrow signifies the Downlink request, and shows its success. A green down arrow signifies that the Callback function successfully returned a Device Type configuration payload. See below for an example:

**Figure 11.** _Downlink request with a successful response_

[downlink]: img/downlink.png
![downlink request][downlink]

1.  Verify that you can see a similar log entry in the Stackdriver Logging, for the Cloud Function _callback_data:_
```
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
```

In the log entry you can verify that:

- _&lt;your device ID>_ is listed in the beginning of the JSON entry, and that the
- Value of 'downlinkData' is the same HEX string as you have in Datastore for this Device Type.

From now on you can update the Device Type configuration value in Datastore, either manually using the Datastore console, or programmatically using the Google Cloud Datastore client libraries.


## Verifying Service Messages

Verify that you can receive Service messages from Sigfox backend, by executing the following steps. Note - you should execute these steps only after executing the Downlink tests in the previous section. You may not have any Service messages from Sigfox backend, until you send a Downlink response to your device. The Downlink response will generate a subsequent 'downlinkAck' service message.

1. In the Cloud Functions console, click the _callback_service_ function.
1. Verify that you can see successful invocations, indicated by a blue line:

**Figure 12.** _Service message invocation_

[cf-service]: img/cf-service.png
![service message invocation][cf-service]

1.  Click the 'View Logs' button and find an entry similar to this:
```
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
 textPayload:  "Received Sigfox service message: {'device': '<device ID>', 'infoCode': '0', 'infoMessage': 'Acked', 'downlinkAck': 'true', 'downlinkOverusage': 'false'}"
 timestamp:  "2019-01-08T06:34:49.307Z"
 trace:  "projects/project/traces/97db5c23e664c16c1234567831a"
}
```

Here you can see that the:

- Function _callback_service_ was invoked
- The log entry shows: "Received Sigfox service message" for &lt;your device ID>
- The value of 'downlinkAck' is 'true', indicating that the device has received the configuration payload

Congratulations! You have now installed and verified the Sigfox-GCP Integration.

## Cleaning up

### Deleting Sigfox Backend Callback Configurations

If the Google Cloud integration Callbacks are the only ones configured in your Sigfox backend for this Device Type, you can use a script to delete them all.

1. On your local development machine, execute the following:
```
(venv) $ python sigfox-api.py --callbacks delete-all
```

**Note**: this command deletes **all** callbacks registered for the Device Type, including any Callbacks that you may have configured manually earlier.

If you have other Callbacks for other use cases configured for this Device Type, use the [Sigfox backend](https://backend.sigfox.com/) > Device Type > Callbacks console to delete the 5 Callbacks configured for this integration. You can identify the integration Callbacks from the URLs that point to your Cloud Functions.

### Deleting Google Cloud Platform Project

To avoid incurring charges to your Google Cloud Platform account for the resources used in this tutorial:

1. **Warning:** Deleting a project has the following consequences:
    - If you used an existing project, you'll also delete any other work you've done in the project.
    - You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the project instead. This step ensures that URLs that use the project ID, such as an **appspot.com** URL, remain available.
1. In the GCP Console, go to the [Projects page.](https://console.cloud.google.com/iam-admin/projects)
1. In the project list, select the project you want to delete and click **Delete project**.

**Figure 13.** _Deleting the project_

[delete-project]: img/delete-project.png
![deleting the project][delete-project]

In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Stay tuned for an upcoming tutorial on using the Sigfox [Sens'it Discovery V3](https://www.sensit.io/) device with this integration, and learning how to encode and decode its binary data and configuration payloads, as well as store the data in real-time in Cloud BigQuery.
- Learn more about [IoT on Google Cloud Platform](https://cloud.google.com/solutions/iot/).
- Learn more about [Big Data analytics on Google Cloud Platform](https://cloud.google.com/solutions/big-data/), to turn your IoT data into actionable insights
- Try out other Google Cloud Platform features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
