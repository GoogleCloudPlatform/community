---
title: Setting up LoRa Server on Google Cloud Platform
description: This tutorial describes how to setup LoRa Server, an open-source LoRaWAN network-server, on Google Cloud Platform.
author: brocaar
tags: LoRa Server, LoRaWAN, IoT, Cloud IoT Core
date_published: 2018-12-20
---

This tutorial describes the steps needed to set up the [LoRa Server project](https://www.loraserver.io/)
on [Google Cloud Platform](https://cloud.google.com/). The following
Google Cloud Platform (GCP) services are used:

* [Cloud IoT Core](https://cloud.google.com/iot-core/) is used to connect
  your LoRa gateways with GCP.
* [Cloud Pub/Sub](https://cloud.google.com/pubsub/) is used for messaging
  between GCP components and LoRa Server services.
* [Cloud Functions](https://cloud.google.com/functions/) is used to handle
  downlink LoRa gateway communication (calling the Cloud IoT Core API on
  downlink Pub/Sub messages).
* [Cloud SQL](https://cloud.google.com/sql/) is used as hosted PostgreSQL
  database solution.
* [Cloud Memorystore](https://cloud.google.com/memorystore/) is used as
  hosted Redis solution.
* [Compute Engine](https://cloud.google.com/compute/) is used for running
  a VM instance.

## Assumptions

* In this tutorial we will assume that the
  [LoRa Gateway Bridge](https://www.loraserver.io/lora-gateway-bridge/)
  component will be installed on the gateway. We will also assume that
  [LoRa Server](https://www.loraserver.io/loraserver/) and
  [LoRa App Server](https://www.loraserver.io/lora-app-server/) will be
  installed on a single Compute Engine VM, to simplify this tutorial.
* The example project ID used in this tutorial will be `lora-server-tutorial`. You should
  substitute this with your own project ID in the tutorial steps.
* The LoRaWAN region used in this tutorial will be `eu868`. You should substitute
  this with your own region in the examples.

## Requirements

* Google Cloud Platform account. You can create one [here](https://cloud.google.com/).
* LoRa gateway.
* LoRaWAN device.

## Create GCP project

After logging in to the GCP Console, create a new project. For this tutorial
we will name the project `LoRa Server tutorial` with an example ID of
`lora-server-tutorial`. After creating the project, make sure it is selected
before continuing with the next steps.

## Gateway connectivity

The [LoRa Gateway Bridge](https://www.loraserver.io/lora-gateway-bridge/)(referred to as simply Gateway in this tutorial) will use the
[Cloud IoT Core](https://cloud.google.com/iot-core/) MQTT broker to ingest
LoRa gateway events into GCP. This removes the requirement
to host your own MQTT broker and increases the reliability and scalability of the system.

### Create device registry

In order to connect your LoRa gateway with [Cloud IoT Core](https://cloud.google.com/iot-core/), go to the **IoT Core** service in the GCP
Console and **create a new device registry** in the **Device registries** box.

This registry will contain all your gateways for a given region. When you
are planning to support multiple LoRaWAN regions, it is a good practice to
create separate registries (not covered in this tutorial).

In this tutorial, we are going to create a registry for EU868 gateways, so we choose
the Registry ID `eu868-gateways`. Select the region which is closest
to you and select **MQTT** as the protocol. The **HTTP** protocol will not be used.

Under **Default telemetry topic** create a new topic. We will call this
`eu868-gateway-events`. Click **Create**.

### Create LoRa gateway certificate

In order to authenticate the LoRa gateway with the Cloud IoT Core MQTT bridge,
you need to generate a certificate. You can do this using the following
commands:

    ssh-keygen -t rsa -b 4096 -f private-key.pem
    openssl rsa -in private-key.pem -pubout -outform PEM -out public-key.pem

Do **not** set a passphrase!

### Add device (LoRa gateway)

To add your first LoRa gateway to the just created device registry, click
the **Create device** button.

As **Device ID**, enter your Gateway ID prefixed with `gw-`. For example, if your
Gateway ID equals to `0102030405060708`, then enter `gw-0102030405060708`.
The `gw-` prefix is needed because a Cloud IoT Core ID must start with a letter, which is not
always the case for a LoRa gateway ID.

Each Cloud IoT Core device (LoRa gateway) will authenticate using its own certificate.
Select **RS256** as **Public key format** and paste the public-key content in the box.
This is the content of `public-key.pem` which was created in the previous step.
Click **Create**.

### Configure LoRa Gateway Bridge

As there are different ways to install the
[LoRa Gateway Bridge](https://www.loraserver.io/lora-gateway-bridge/)
on your gateway, only the configuration is covered here. For installation instructions,
please refer to [LoRa Gateway Bridge gateway installation & configuration](https://www.loraserver.io/lora-gateway-bridge/install/gateway/).

To configure a LoRa Gateway Bridge to forward its data to Cloud IoT, you need update the `lora-gateway-bridge.toml`
[Configuration file](https://www.loraserver.io/lora-gateway-bridge/install/config/).

A minimal configuration example:

    [backend.mqtt]
    marshaler="protobuf"

      [backend.mqtt.auth]
      type="gcp_cloud_iot_core"

        [backend.mqtt.auth.gcp_cloud_iot_core]
        server="ssl://mqtt.googleapis.com:8883"
        device_id="gw-0102030405060708"
        project_id="lora-server-tutorial"
        cloud_region="europe-west1"
        registry_id="eu868-gateways"
        jwt_key_file="/path/to/private-key.pem"

In short:

* This will configure the `protobuf` marshaler (either `protobuf` or `json` must be configured)
* This will configure the Google Cloud IoT Core MQTT authentication
* This will configure the GCP project ID, cloud-region and registry ID

Note that `jwt_key_file` must point to the private-key file generated in the
previous step.

After applying the above configuration changes on the gateway (using your own `device_id`,
`project_id`, `cloud_region` and `jwt_key_file`), validate that LoRa Gateway Bridge
is able to connect with the Cloud IoT Core MQTT bridge. The log output should
look like this when your gateway receives an uplink message from your LoRaWAN device:

    INFO[0000] starting LoRa Gateway Bridge                  docs="https://www.loraserver.io/lora-gateway-bridge/" version=2.6.0
    INFO[0000] gateway: starting gateway udp listener        addr="0.0.0.0:1700"
    INFO[0000] mqtt: connected to mqtt broker
    INFO[0007] mqtt: subscribing to topic                    qos=0 topic="/devices/gw-0102030405060708/commands/#"
    INFO[0045] mqtt: publishing message                      qos=0 topic=/devices/gw-0102030405060708/events/up

Your gateway is now communicating succesfully with the Cloud IoT Core MQTT bridge!

### Create downlink Pub/Sub topic

Instead of using MQTT directly, the [LoRa Server](https://www.loraserver.io/loraserver/) will use
[Cloud Pub/Sub](https://cloud.google.com/pubsub/)
for receiving data from and sending data to your gateways.

In the GCP Console, navigate to **Pub/Sub > Topics**. You will see the topic
that was created when you created the device registry. LoRa Server will
subscribe to this topic to receive data (events) from your gateway.

For sending data back to your gateways, we will create a new topic. Click **Create Topic**, and enter `eu868-gateway-commands` as the name.

### Create downlink Cloud Function

In the previous step, you created a topic for sending downlink commands
to your gateways. In order to connect this Pub/Sub topic with your
Cloud IoT Core device-registry, you must create a [Cloud Function](https://cloud.google.com/functions/)
which will subscribe to the downlink Pub/Sub topic and will forward these
commands to your LoRa gateway.

In the GCP Console, navigate to **Cloud Functions**. Then click **Create function**.
As **Name** we will use `eu868-gateway-commands`. Because the only thing this function
does is calling a Cloud API, `128 MB` for **Memory allocated** should be fine.

Select **Cloud Pub/Sub** as **trigger** and select `eu868-gateway-commands` as
the **topic**.

Select **Inline editor** for entering the source-code and select the **Node.js 8**
runtime. The **Function to execute** is called `sendMessage`. Copy and paste
the scripts below for the `index.js` and `package.json` files. Adjust the
`index.js` configuration to match your `REGION`, `PROJECT_ID` and `REGISTRY_ID`.
**Note:** it is recommended to also click **More** and select your region
from the dropdown list. Then click **Create**.

#### `index.js`

```js
'use strict';

const {google} = require('googleapis');

// configuration options
const REGION = 'europe-west1';
const PROJECT_ID = 'lora-server-tutorial';
const REGISTRY_ID = 'eu868-gateways';


let client = null;
const API_VERSION = 'v1';
const DISCOVERY_API = 'https://cloudiot.googleapis.com/$discovery/rest';


// getClient returns the GCP API client.
// Note: after the first initialization, the client will be cached.
function getClient (cb) {
  if (client !== null) {
    cb(client);
    return;
  }

  google.auth.getClient({scopes: ['https://www.googleapis.com/auth/cloud-platform']}).then((authClient => {
    google.options({
      auth: authClient
    });

    const discoveryUrl = `${DISCOVERY_API}?version=${API_VERSION}`;
    google.discoverAPI(discoveryUrl).then((c, err) => {
      if (err) {
        console.log('Error during API discovery', err);
        return undefined;
      }
      client = c;
      cb(client);
    });
  }));
}


// sendMessage forwards the Pub/Sub message to the given device.
exports.sendMessage = (event, context, callback) => {
  const deviceId = event.attributes.deviceId;
  const subFolder = event.attributes.subFolder;
  const data = event.data;

  getClient((client) => {
    const parentName = `projects/${PROJECT_ID}/locations/${REGION}`;
    const registryName = `${parentName}/registries/${REGISTRY_ID}`;
    const request = {
      name: `${registryName}/devices/${deviceId}`,
      binaryData: data,
      subfolder: subFolder
    };

    console.log("start call sendCommandToDevice");
    client.projects.locations.registries.devices.sendCommandToDevice(request, (err, data) => {
      if (err) {
        console.log("Could not send command:", request, "Message:", err);
        callback(new Error(err));
      } else {
        callback();
      }
    });
  });
};
```

#### `package.json`

```json
{
  "name": "gateway-commands",
  "version": "2.0.0",
  "dependencies": {
    "@google-cloud/pubsub": "0.20.1",
    "googleapis": "34.0.0"
  }
}
```

## Set up databases

### Create Redis datastore

In the GCP Console, navigate to **Memorystore** (which provides a managed
Redis datastore) and click **Create instance**.

You can assign any name to this instance. Make sure that you also select your
**Region**. Click **Create** to create the Redis instance.

### Create PostgreSQL databases

In the GCP Console, navigate to **SQL** (which provides managed PostgreSQL
database instances) and click **Create instance**.

Select **PostgreSQL** and click **Next**. You can assign any name to this
instance. Again, make sure to also select your **Region** from the dropdown.

Configure the **Configuration options** to your needs (the smallest instance
is already sufficient for testing). An important option to configure is
**Authorize networks**. To allow access from *any* IP address, enter
`0.0.0.0/0`. It is recommended to update this later to only the IP
address of your server (covered in the next steps). Then click **Create**.

#### Create users

Click on the created database instance and click the **Users** tab.
Create two users:

* `loraserver_ns`
* `loraserver_as`

#### Create databases

Click the **Databases** tab. Create the following databases:

* `loraserver_ns`
* `loraserver_as`

#### Enable trgm extension

In the PostgreSQL instance **Overview** tab, click **Connect using Cloud Shell**
and when the `gcloud sql connect ...` command is shown in the console,
press Enter. It will prompt you for the `postgres` user password (which you
configured on creating the PostgreSQL instance).

Then execute the following SQL commands:

    -- change to the LoRa App Server database
    \c loraserver_as

    -- enable the pq_trgm extension
    -- (this is needed to facilitate the search feature)
    create extension pg_trgm;

    -- exit psql
    \q


You can close the Cloud Shell.

## Install LoRa Server

When you have succesfully completed the previous steps, then your gateway is
connected to the Cloud IoT Core MQTT bridge, all the LoRa (App) Server 
requirements are set up and is it time to install [LoRa Server](https://www.loraserver.io/loraserver/) and
[LoRa App Server](https://www.loraserver.io/lora-app-server/).

### Create a VM instance

In the GCP Console, navigate to **Compute Engine > VM instances** and click
on **Create**.

Again, the name of the instance doesn't matter but make sure you select the
correct **Region**. The smallest **Machine type** is sufficient to test with. For this tutorial we will use the default
**Boot disk** (Debian 9).

Under **Identity and API access**, select **Allow full access to all Cloud APIs**
under the **Access scopes** options.

When all is configured, click **Create**.

### Configure firewall

In order to expose the LoRa App Server web interface, we need to open port
`8080` (the default LoRa App Server port) to the public.

Click on the created instance to go to the instance details. Under
**Network interfaces** click **View details**. In the left navigation
menu click **Firewall rules** and then on **Create firewall rule**.
Enter the following details:

* **Name:** can be any name
* **Targets:** `All instances in the network`
* **Source IP ranges:** `0.0.0.0/0`
* **Protocols and ports > TCP:** `8080`

Then click **Create**.

### Compute Engine service account roles

As the Compute Engine instance (created in the previous step) needs to
be able to subscribe to the Pub/Sub data, we must give the
**Compute Engine default service account** the required role.

In the GCP Console, navigate to **IAM & admin**. Then edit the **Compute Engine
default service account**. Click **Add another role** and add the following roles:

* `Pub/Sub Publisher`
* `Pub/Sub Subscriber`

### Log in to VM instance

You will find the public IP address of the created VM instance under
**Compute Engine > VM instances**. Use the SSH web-client provided by the GCP Console, or the gcloud ssh command to connect to the VM.

### Configure the LoRa Server repository

Execute the following commands in the VM's shell to add the LoRa Server repository to your VM instance:

    # add required packages
    sudo apt install apt-transport-https dirmngr

    # import LoRa Server key
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1CE2AFD36DBCCA00

    # add the repository to apt configuration
    sudo echo "deb https://artifacts.loraserver.io/packages/2.x/deb stable main" | sudo tee /etc/apt/sources.list.d/loraserver.list

    # update the package cache
    sudo apt update


### Install LoRa Server

Execute the following command in the VM's shell to install the LoRa Server service:

    sudo apt install loraserver


#### Configure LoRa Server

The LoRa Server configuration file is located at
`/etc/loraserver/loraserver.toml`. Below you will find two (minimal but working)
configuration examples. Please refer to the LoRa Server
[Configuration](https://www.loraserver.io/loraserver/install/config/) documentation for all the
available options.

**Important:** Because there might be a high latency between the Pub/Sub and
Cloud Function components — especially with a low message rate — the `rx1_delay`
value is set to 3 in the examples below.

You need to replace the following values:

* **[PASSWORD]** with the `loraserver_ns` PostgreSQL user password
* **[POSTGRESQL_IP]** with the **Primary IP address** of the created PostgreSQL instance
* **[REDIS_IP]** with the **IP address** of the created Redis instance

##### EU868 configuration example

    [postgresql]
    dsn="postgres://loraserver_ns:[PASSWORD]@[POSTGRESQL_IP]/loraserver_ns?sslmode=disable"

    [redis]
    url="redis://[REDIS_IP]:6379"

    [network_server]
    net_id="000000"

      [network_server.band]
      name="EU_863_870"

      [network_server.network_settings]
      rx1_delay=3

      [network_server.gateway.stats]
      create_gateway_on_stats=true
      timezone="UTC"

      [network_server.gateway.backend]
      type="gcp_pub_sub"

        [network_server.gateway.backend.gcp_pub_sub]
        project_id="lora-server-tutorial"
        uplink_topic_name="eu868-gateway-events"
        downlink_topic_name="eu868-gateway-commands"


##### US915 configuration example

    [postgresql]
    dsn="postgres://loraserver_ns:[PASSWORD]@[POSTGRESQL_IP]/loraserver_ns?sslmode=disable"

    [redis]
    url="redis://[REDIS_IP]:6379"

    [network_server]
    net_id="000000"

      [network_server.band]
      name="US_902_928"

      [network_server.network_settings]
      rx1_delay=3
      enabled_uplink_channels=[0, 1, 2, 3, 4, 5, 6, 7]

      [network_server.gateway.stats]
      create_gateway_on_stats=true
      timezone="UTC"

      [network_server.gateway.backend]
      type="gcp_pub_sub"

        [network_server.gateway.backend.gcp_pub_sub]
        project_id="lora-server-tutorial"
        uplink_topic_name="eu868-gateway-events"
        downlink_topic_name="eu868-gateway-commands"


To test the configuration for errors, you can execute the following command:

    sudo loraserver


This should output something like the following:

    INFO[0000] setup redis connection pool                   url="redis://10.0.0.3:6379"
    INFO[0000] connecting to postgresql
    INFO[0000] gateway/gcp_pub_sub: setting up client
    INFO[0000] gateway/gcp_pub_sub: setup downlink topic     topic=eu868-gateway-commands
    INFO[0001] gateway/gcp_pub_sub: setup uplink topic       topic=eu868-gateway-events
    INFO[0002] gateway/gcp_pub_sub: check if uplink subscription exists  subscription=eu868-gateway-events-loraserver
    INFO[0002] gateway/gcp_pub_sub: create uplink subscription  subscription=eu868-gateway-events-loraserver
    INFO[0005] applying database migrations
    INFO[0006] migrations applied                            count=19
    INFO[0006] starting api server                           bind="0.0.0.0:8000" ca-cert= tls-cert= tls-key=

If all is well, then you can start the service in the background using:

    sudo systemctl start loraserver
    sudo systemctl enable loraserver


### Install LoRa App Server

When you have completed all previous steps, then it is time to install the
last component, [LoRa App Server](https://www.loraserver.io/lora-app-server/). This is the
application-server that provides a web interface for device management and
will publish application data to a Pub/Sub topic.

#### Create Pub/Sub topic

In the GCP Console, navigate to **Pub/Sub > Topics**. Then click
**Create topic** to create a topic named `lora-app-server`.

#### Install LoRa App Server

SSH to the VM and execute the following command to install LoRa App Server:

    sudo apt install lora-app-server


#### Configure LoRa App Server

The LoRa App Server configuration file is located at
`/etc/lora-app-server/lora-app-server.toml`. Below you will find a minimal
but working configuration example. Please refer to the LoRa App Server
[Configuration](/lora-app-server/install/config/) documentation for all the
available options.

You need to replace the following values:

* **[PASSWORD]** with the `loraserver_as` PostgreSQL user password
* **[POSTGRESQL_IP]** with the **Primary IP address** of the created PostgreSQL instance
* **[REDIS_IP]** with the **IP address** of the created Redis instance
* **[JWT_SECRET]** with your own random JWT secret (e.g. the output of `openssl rand -base64 32`)

##### Configuration example

    [postgresql]
    dsn="postgres://loraserver_as:[PASSWORD]@[POSTGRESQL_IP]/loraserver_as?sslmode=disable"

    [redis]
    url="redis://[REDIS_IP]:6379"

    [application_server]

      [application_server.integration]
      backend="gcp_pub_sub"

      [application_server.integration.gcp_pub_sub]
      project_id="lora-server-tutorial"
      topic_name="lora-app-server"

      [application_server.external_api]
      bind="0.0.0.0:8080"
      tls_cert="/etc/lora-app-server/certs/http.pem"
      tls_key="/etc/lora-app-server/certs/http-key.pem"
      jwt_secret="[JWT_SECRET]"


To test if there are no errors, you can execute the following command:

    sudo lora-app-server


This should output something like the following:

    INFO[0000] setup redis connection pool                   url="redis://10.0.0.3:6379"
    INFO[0000] connecting to postgresql
    INFO[0000] gateway/gcp_pub_sub: setting up client
    INFO[0000] gateway/gcp_pub_sub: setup downlink topic     topic=eu868-gateway-commands
    INFO[0001] gateway/gcp_pub_sub: setup uplink topic       topic=eu868-gateway-events
    INFO[0002] gateway/gcp_pub_sub: check if uplink subscription exists  subscription=eu868-gateway-events-loraserver
    INFO[0002] gateway/gcp_pub_sub: create uplink subscription  subscription=eu868-gateway-events-loraserver
    INFO[0005] applying database migrations
    INFO[0006] migrations applied                            count=19
    INFO[0006] starting api server                           bind="0.0.0.0:8000" ca-cert= tls-cert= tls-key=

If all is well, then you can start the service in the background using these commands:

    sudo systemctl start lora-app-server
    sudo systemctl enable lora-app-server


## Using the LoRa (App) Server

### Set up your first gateway and device

To get started with LoRa (App) Server, please follow the
[First gateway and device](https://www.loraserver.io/guides/first-gateway-device/)
guide. It explains how to log in to the web-interface and add your first
gateway and device.

### Integrate your applications

In the LoRa App Server step, you have created a Pub/Sub topic named
`lora-app-server`. This will be the topic used by LoRa Server for publishing
device events and to which your application(s) need to subscribe in order to
receive LoRaWAN device data.

For more information about Cloud Pub/Sub, please refer to the following pages:

* [Cloud Pub/Sub product page](https://cloud.google.com/pubsub/)
* [Cloud Pub/Sub documentation](https://cloud.google.com/pubsub/docs/)
* [Cloud Pub/Sub Quickstarts](https://cloud.google.com/pubsub/docs/quickstarts)

