## Set the environment variables
Set your GCP project, replace `[PROJECT_ID]` with your project id:
```bash
gcloud config set project [PROJECT_ID]
```
<walkthrough-editor-open-file filePath="community/tutorials/cloud-iot-enviro-board-workshop/cloud-setup/set_env_variables.sh"
text="Open set environment variables script">
</walkthrough-editor-open-file>
In the script file replace the values for `EVENT_TOPIC`,`REGISTRY_ID` and `DEVICE_ID` with id:s of your choice, and save the file.

**Note** Replace the whole string after the `=` sign. The `<` and `>` brackets should be replaced as well.  
Name must be between 3 and 255 characters
Name must start with a letter, and contain only the following characters: letters, numbers, dashes (-), periods (.), underscores (\_), tildes (~), percents (%) or plus signs (+).

Set the environment variables:
```bash
cd ~/community/tutorials/cloud-iot-enviro-board-workshop/cloud-setup

source set_env_variables.sh
```
## Create Pub/Sub topic
```bash
gcloud pubsub topics create $EVENT_TOPIC
```
## Create IoT Core registry
```bash
gcloud iot registries create $REGISTRY_ID \
--region $REGION \
--event-notification-config=topic=$EVENT_TOPIC
```
## Create the public key file of the sensor board
Create a file named `device_pub_key.pem` with the public key that were printed out earlier in the **Get the public key...** step.
```bash
cd ~/community/tutorials/cloud-iot-enviro-board-workshop/cloud-setup

touch device_pub_key.pem
```
<walkthrough-editor-open-file filePath="community/tutorials/cloud-iot-enviro-board-workshop/cloud-setup/device_pub_key.pem" text="Open public key file">
</walkthrough-editor-open-file>
### Store the Sensor Board public key
Paste the public key in the file and save the change. Content starts with `-----BEGIN PUBLIC KEY-----` and ends with `-----END PUBLIC KEY-----`
## Create IoT Core device
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
### Start sensor data stream on Raspberry Pi
Now you can go back to the workshop guide and finish follow steps before continue to next step Cloud Shell.
- Configure Raspberry Pi
- Download the CA-certificate
- Run the streaming script
## Verify sensor data in Pub/Sub
Pull message from Pub/Sub subscription. In Cloud Shell run:
```bash
gcloud pubsub subscriptions pull verify-event --auto-ack
```
Verify you get the messages from the Sensor Board

## Set environment variable for BigQuery dataset and table
Choose name for your BigQuery dataset and table where the sensor data will be stored, and export them as environment variables. In Cloud Shell run:
```bash
export DATASET=<replace_with_your_dataset_name>
```
and
```bash
export TABLE=<replace_with_your_table_name>
```
## Deploy Cloud Function for process sensor data
In Cloud Shell run:
```bash
cd ~/community/tutorials/cloud-iot-enviro-board-workshop/functions
```
and
```bash
gcloud functions deploy enviro \
--set-env-vars=DATASET=${DATASET},TABLE=${TABLE} \
--region ${REGION} \
--trigger-topic ${EVENT_TOPIC} \
--runtime nodejs8 \
--memory 128mb
```
Wait until function is deployed.
## Setup data storage
Create the dataset and table in BigQuery.
In Cloud Shell run:
```bash
cd ~/community/tutorials/cloud-iot-enviro-board-workshop/bq
```
Create dataset:
```bash
bq mk $DATASET
```
Create table:
```bash
bq mk ${DATASET}.${TABLE} schema.json
```
## GCP setup done
Now is all the components set up on GCP and ready to receive sensor data from Raspberry Pi.
Continue with the workshop guide from **Start the sensor data stream** step.
