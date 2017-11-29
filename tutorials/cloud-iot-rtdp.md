# Real time Data Processing With Google Cloud IoT
This repository contains sample code for Real time Data Processing With Google Cloud IoT solution. Sample MQTT client generates simulated data and submits them to Cloud IoT Core. Cloud Functions and Cloud Dataflow receive data through Cloud Pub/Sub.

![Architecture](cloud-iot-rtdp/arch.png)

## Prerequisites
- Git
- Google Cloud SDK
- Java 1.8 or later
- Apache Maven 3.3.x or later

All commands in following steps are assumed to be executed under "community/tutorials/cloud-iot-rtdp" directory.

## Enable APIs
Enable following APIs from Google Cloud Console.
- Cloud IoT Core
- Cloud Functions
- Cloud Dataflow

## Create a Cloud Storage bucket and set environment variables.
1. Create a Cloud Storage bucket and a temporary folder.
2. Set environment variables. Corresponding resources are created in later steps.
```bash
% export PROJECT=<GCP Project ID>
% export BUCKET=<Cloud Storage Bucket Name>
% export REGISTRY=<Cloud IoT Core Registry ID>
% export TOPIC=<Cloud Pub/Sub Topic Name>
```

## Configure Cloud IoT Core
1. Open Cloud Pub/Sub console and create a new topic.
2. Move to Cloud IoT Core console and click create device registry.
3. Enter Registry ID, select a region and choose the Pub/Sub topic created in step 1.
4. Execute a script to register devices in the device registry.
```bash
% bin/register.sh
```

## Deploy a function to Cloud Functions
Execute following commands to deploy a function to Cloud Functions.

```bash
% cd function

% gcloud beta functions deploy iot --stage-bucket $BUCKET --trigger-topic $TOPIC
/ [1 files][  292.0 B/  292.0 B]
Operation completed over 1 objects/292.0 B.
Deploying function (may take a while - up to 2 minutes)...done.
availableMemoryMb: 256
entryPoint: iot
eventTrigger:
```

## Deploy a streaming application to Cloud Dataflow
Build and submit a streaming job by executing following commands.

```bash
% cd bin

% ./job.sh
[INFO] Scanning for projects...
[INFO]                                                                        
...
```

## Generate simulated temperature and coordinates data
Execute an MQTT client to generate simulated temperature and coordinates data.

```bash
% cd bin

% ./run.sh
[INFO] Scanning for projects...
[INFO]                                                                        
...
```

## Validation
1. Confirm a function is processing temperature data by clicking "View logs" menu in Cloud Functions console.
2. Confirm a streaming Dataflow job processes and loads data into BigQuery by clicking the Job ID in Cloud Dataflow console.
3. Execute a following query from BigQuery console and confirm data is stored in "temp_sensor" table.
```sql
SELECT count(*) FROM [<Project ID>:iotds.temp_sensor]
```

## License
 Copyright 2017 Google Inc. All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS-IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the License for the specific language governing permissions and limitations under the License.

This is not an official Google product.
