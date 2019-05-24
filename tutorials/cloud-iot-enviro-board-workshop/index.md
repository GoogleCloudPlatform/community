---
title: Sensor data collection and ad-hoc analytics
description: Deployment of an end-to-end setup from Environmental Sensor Board through Google Cloud IoT Core to BigQuery. Last conduct data visualization and analytics through Google Sheets
author: chwa
tags: IoT, Internet of Things, Environmental Sensor Board, Raspberry Pi, Google Sheets
date_published: 2019-06-10
---
## Introduction
In this tutorial you use [Environmental Sensor Board](https://coral.withgoogle.com/products/environmental) to connect to [Cloud IoT Core](https://cloud.google.com/iot-core/) and stream sensor data to [Cloud Pub/Sub](https://cloud.google.com/pubsub/). You use [Cloud Functions](https://cloud.google.com/functions/) to collect and process the sensor data from Pub/Sub and store them in [BigQuery](https://cloud.google.com/bigquery/). [Google Sheets](https://docs.google.com/spreadsheets) is use for doing analytics on the sensor data in BigQuery and send command messages to the Sensor Board using the [IoT Core Commands API](https://cloud.google.com/iot/docs/how-tos/commands).

## Architecture
Architectural overview of solution setup
![high level overview](images/architecture.png)

## Objectives
- Provisioning of the Environmental Sensor Board
- Setup Cloud Functions for sensor data processing
- Setup BigQuery for data storage
- Setup Google Sheet to integrate with BigQuery and IoT Core

## Prerequisite
- [Environmental Sensor Board](https://coral.withgoogle.com/products/environmental)
- Raspberry Pi with [Raspbian](https://www.raspberrypi.org/downloads/) and connected to the internet
- This tutorial assumes that you already have a [GCP account](https://console.cloud.google.com/freetrial) set up.
- An user account linked to G Suite Business or Enterprise or Education for access the Google Sheets - BigQuery connector feature.

## Costs
This tutorial uses billable components of GCP, including the following:
* [Cloud IoT Core](https://cloud.google.com/iot/pricing)
* [Cloud Pub/Sub](https://cloud.google.com/pubsub/pricing)
* [Cloud Functions](https://cloud.google.com/functions/pricing)
* [BigQuery](https://cloud.google.com/bigquery/pricing)

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate
a cost estimate based on your projected production usage.

## Create a GCP project
1. Go to the [GCP Console](https://console.cloud.google.com).
1. Click the project selector in the upper-left corner and select **New Project**.
1. Give the project a name and click **Create**.
1. Click the project selector again and select your new project.
1. Open the menu **APIs & Services > Library**.
1. Search for and activate the following APIs, or ensure that they are already active:
    - Cloud Functions API
    - Cloud Pub/Sub API
    - Cloud BigQuery API

## Provision the Sensor Board
Attach the Sensor Board to the 40-pin header of your Raspberry Pi and power on your board.
### Install the Environmental Sensor Board library and driver
Commands are run in a Raspberry Pi shell.
```bash
echo "deb https://packages.cloud.google.com/apt coral-cloud-stable main" | sudo tee /etc/apt/sources.list.d/coral-cloud.list

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

sudo apt update

sudo apt upgrade

sudo apt install python3-coral-enviro
```
Reboot your board
```bash
sudo shutdown -r now
```
### Check out the tutorial source code on your board
```bash
cd ~

git clone https://github.com/kingman/enviro-workshop.git
```
### Get the public key of the secure element of your sensor board
```bash
cd /usr/lib/python3/dist-packages/coral/cloudiot

python3 ecc608_pubkey.py
```
Copy the public key which is used at later stage when creating device identity in cloud.

## Provision device identity on GCP
For device to communicate with IoT Core, the device identity needs to be created in IoT Core. Following commands are run in [Cloud Shell](https://cloud.google.com/shell/docs/features).

###  Check out the tutorial source code on Cloud Shell
1. In the GCP Console, [open Cloud Shell](http://console.cloud.google.com/?cloudshell=true)
1. Clone the source code repository:

```bash
cd ~

git clone https://github.com/kingman/enviro-workshop.git
```
### Set the environment variables
```bash
cd ~/enviro-workshop/cloud-setup
```
In the file: `set_env_variables.sh` replace the values for `EVENT_TOPIC`,`REGISTRY_ID` and `DEVICE_ID` with id:s of your choice.

**Note** Replace the whole string after the `=` sign. The `<` and `>` brackets should be replaced as well.  
Name must be between 3 and 255 characters
Name must start with a letter, and contain only the following characters: letters, numbers, dashes (-), periods (.), underscores (\_), tildes (~), percents (%) or plus signs (+).

Set the environment variables:
```bash
source set_env_variables.sh
```
### Create Pub/Sub topic
```bash
gcloud pubsub topics create $EVENT_TOPIC
```
### Create IoT Core registry
```bash
gcloud iot registries create $REGISTRY_ID \
--region $REGION \
--event-notification-config=topic=$EVENT_TOPIC
```
### Create the public key file of the sensor board
Create a file named `device_pub_key.pem` with the public key that were printed out earlier in the **Get the public key...** step.
```bash
cd ~/enviro-workshop/cloud-setup

touch device_pub_key.pem
```
Use a text editor to get the public key string into the file. Content starts with `-----BEGIN PUBLIC KEY-----` and ends with `-----END PUBLIC KEY-----`
### Create IoT Core device
Create the sensor board identity in the newly created IoT Core registry with Sensor Board public key. In Cloud Shell run:
```bash
gcloud iot devices create $DEVICE_ID \
--region=$REGION \
--registry=$REGISTRY_ID \
--public-key=path=device_pub_key.pem,type=es256
```

## Verify the data ingestion setup
You have now all the building blocks set up and integrated for ingestion of data from the Sensor Board to GCP. In this section you verify end-to-end integration between the Sensor board and Cloud Pub/Sub.
### Create event topic subscription
In Cloud Shell run:
```bash
gcloud pubsub subscriptions create verify-event \
--topic=$EVENT_TOPIC
```
### Configure Raspberry Pi
Configure Raspberry Pi to send sensor data to IoT Core
In Raspberry Pi shell open the cloud config file: `~/enviro-workshop/enviro-device/cloud_config.ini` and replace the place holders `<project-id>`, `<registry-id>` and `<device-id>` with the actual values for the Cloud IoT Core environment setup in earlier step.

### Download the CA-certificate
In Raspberry Pi shell run:
```bash
cd ~/enviro-workshop/enviro-device/

wget https://pki.goog/roots.pem
```
### Run the streaming script
In Raspberry Pi shell run:
```bash
cd ~/enviro-workshop/enviro-device/

python3 enviro_demo.py --upload_delay 10
```
Let the script run for 20 second before stop it by press `ctrl-c`
### Verify sensor data in Pub/Sub
Pull message from Pub/Sub subscription. In Cloud Shell run:
```bash
gcloud pubsub subscriptions pull verify-event --auto-ack
```
Verify you get the messages from the Sensor Board

## Setup the Cloud Function for process sensor data
### Set environment variable for BigQuery dataset and table
Choose name for your BigQuery dataset and table where the sensor data will be stored, and export them as environment variables. In Cloud Shell run:
```bash
export DATASET=<replace_with_your_dataset_name>

export TABLE=<replace_with_your_table_name>
```
### Deploy Cloud Function
In Cloud Shell run:
```bash
cd ~/enviro-workshop/functions

gcloud functions deploy enviro \
--set-env-vars DATASET=${DATASET},\
TABLE=${TABLE} \
--region ${REGION} \
--trigger-topic ${EVENT_TOPIC} \
--runtime nodejs8 \
--memory 128mb
```
## Setup data storage
Create the dataset and table in BigQuery.
In Cloud Shell run:
```bash
cd ~/enviro-workshop/bq

bq mk $DATASET

bq mk ${DATASET}.${TABLE} schema.json
```
## Start the sensor data stream
You can control the interval of sensor data is sent to Cloud by setting the `upload_delay` parameter. In Raspberry Pi shell run:
```bash
cd ~/enviro-workshop/enviro-device/

python3 enviro_demo.py --upload_delay 15
```
## View sensor data in BigQuery
Open the [BigQuery console](http://console.cloud.google.com/bigquery),
paste following query into the **Query editor** and press **Run**. Replace the place holders `<PROJECT_ID>`, `<DATASET>`, and `<TABLE>` with your environment values.
```sql
SELECT * FROM `<PROJECT_ID>.<DATASET>.<TABLE>`
ORDER BY time DESC
LIMIT 20
```
Verify a table with sensor data is returned.
Discontinue the sensor data streaming from the Raspberry Pi shell by press **Ctrl**+**c**

## Data analytics and device control
### Google Sheets setup
Open the [sample sheet](https://docs.google.com/spreadsheets/d/1LI07utVbiuonjZfn2ORWmC0kC5_OYc7CYw3vZF1aEuo) and make a copy of it. **File** > **Make a copy...** and input a name for the copy and click **OK**
#### Configure OAuth2
1. Get the Oauth2 callback url for the script. Click **IoT** > **OAuth Configuration** and Copy the Authorized redirect URI shown in the menu.
1. Go to the [API Credentials page](https://console.cloud.google.com/apis/credentials)
1. Click **Create credentials** > **OAuth client ID**
1. Choose **Web application**
1. Give the credential an identifiable name
1. Paste the URI from the sheet into the **Authorized redirect URIs** input field
1. Click **Create**
1. Copy the **client ID** and **client secret** value back into the sheet **OAuth Configuration** input
1. Click **Save** and wait for the **config saved!** response before **Close** the menu.

#### Configure IoT Core
1. Click **IoT** > **IoT Core Configuration**
1. Fill in values of your GCP **project**, IoT Core **region** and **registry**
1. Click **Save** and wait for the **config saved!** response before **Close** the menu.

### Load devices
1. Click **IoT** > **Load Devices** and first time the sidebar opens.
1. Click **Authorize** link in the sidebar and follow through the authorization follow to allow the script to access the IoT Core API on your behalf.
1. When the OAuth2 flow is successful a new tab is opened with message: **Success! You can close this tab.**
1. Close the tab.
1. Click **IoT** > **Load Devices** once again and verify your device name gets populated under the devices column
1. Click on the check box next to the device name cell to select it.

### Setup BigQuery connector
1. Click **Data** > **Data Connectors** > **BigQuery**
1. Choose you GCP project from the dropdown list and click **Write query**
1. Paste following query into the editor and Replace the place holders `<PROJECT_ID>`, `<DATASET>`, and `<TABLE>` with your BigQuery setup values.
```sql
SELECT * FROM `<PROJECT_ID>.<DATASET>.<TABLE>`
WHERE time > TIMESTAMP(CURRENT_DATE())
AND device_id = @DEVICE_ID
ORDER BY time
```
1. Add a new parameter. Click **Parameters** > **Add**. Fill in `DEVICE_ID` for **Name** and `Sheet1!C2` for **Cell reference**. Click **Add**
1. Click **Insert result**

### Send command to your board
1. In cell under the **Command** cell write write a simple text,
1. Send command by click **IoT** > **Send command to device**.
1. Verify you get an `Device is not connected` error message if your board is disconnected.
1. In Raspberry Pi reconnect the sensor board by running: `python3 enviro_demo.py`
1. Click **IoT** > **Send command to device** to resend the message.
1. Verify the message gets displayed on the Sensor Board display.

### Analytics in Google Sheets
- Create time series graph over the sensor data
- Derive moving time average value from raw sensor data
- Create recurring job that [auto loads](https://gsuiteupdates.googleblog.com/2019/02/refresh-bigquery-data-sheets.html) the data from BigQuery
- Create function that monitors the sensor values and automatically sends commands when configure threshold values are breached.

## Cleaning up
To avoid incurring charges to your Google Cloud Platform account for the resources used in this tutorial:
### Delete the project
The easiest way to eliminate billing is to delete the project you created for the tutorial.
To delete the project:
1. In the Cloud Platform Console, go to the Projects page. [GO TO THE PROJECTS PAGE](https://console.cloud.google.com/iam-admin/projects)
1. In the project list, select the project you want to delete and click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

## Next steps
- Learn more about [Google Cloud IoT](https://cloud.google.com/solutions/iot/)
- Learn more about [Microcontrollers and real-time analytics](https://cloud.google.com/community/tutorials/ardu-pi-serial-part-1)
- Learn more about [Streaming into BigQuery](https://cloud.google.com/solutions/streaming-data-from-cloud-storage-into-bigquery-using-cloud-functions)
- Learn more about [Asynchronous patterns for Cloud Functions](https://cloud.google.com/community/tutorials/cloud-functions-async)
