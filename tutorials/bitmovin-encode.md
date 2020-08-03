---
title: Deploy bitmovin encoding on Google Cloud 
description: This tutorial walks you through the process of installing bitmovin's video encoding product into Google Cloud.
author: bitmovin
tags: bitmovin,  video,   encoding,   scale
date_published: 2020-08-05
---

This document explains how to set up Bitmovin Encoder in a customer GCP infrastructure so that Bitmovin platform can run encoders by using GCE API.

## 1. Pre-requisites
+ Google Cloud Platform(GCP) account is created.
+ Project is added and Google Compute Engine(GCE) API is enabled in the project.

## 2. Create Service account
+ Create a service account with ‘Compute Admin’ permissions. This is needed for the compute related permissions on the Infrastructure side like starting/stopping instances. See [1] for GCP console link to create a service account.
+ Create a key for the service account and download the JSON file containing the private key. Following information will be needed from the json file. This is needed to create an InfrastructureId on the Bitmovin platform which can then be used to run encodings on a customer's GCE infrastructure.

    1. project_id
    1. private_key
    1. client_email

## 3. Set Up Mandatory Firewall rules
These are the basic firewall rules without which starting an encoding will fail.

Please go to https://console.cloud.google.com/networking/firewalls/list?organizationId=YourOrganizationId&project=YourProjectId and click CREATE FIREWALL RULE to create firewall rules.

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name      | encoder-service | 
| Description      | For communication with the service that manages the encoding      | 
| Logs | Off                        | 
| Network | default                 | 
| Priority | 1000                   | 
| Direction | Ingress               | 
| Action on match | Allow           | 
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

repeat for:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | session-manager-external               | 
| Description | For communication with the service that manages the encoding instances               | 

and for:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | session-manager-external               | 
| Description | For communication with the service that manages the encoding instances               | 

and for:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | default-allow           | 
| Description | For incoming commands (i.e. pulling and starting docker containers)             | 

and for:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | default-allow-internal             | 
| Description | For communication between the session manager VM instance and its instance manager VM instances    | 

## 4. Set Up Firewall rules for Live Streams
Additional firewall rules are required to be set up for encoding RTMP, SRT and Zixi live streams. 

**Firewall rules that are necessary to run RTMP live streams** 

If you intend to run RTMP live streams, please create a firewall rule with the following settings:





| Field   |   Value to set |
| ------------- |:-------------:| 
| Name | rtmp-listener  |
|Description    |For RTMP live streams  |
|Logs  |Off  |
|Network  |default  |
|Priority |1000 |
|Direction | Ingress |
|Action on match| Allow|
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

**Firewall rules that are necessary to run SRT live streams**

If you intend to run SRT live streams, please create a firewall rule with the following settings:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | srt-listener               | 
| Description |  For SRT live streams                | 
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

**Firewall rules that are necessary to run Zixi live streams**

If you intend to run Zixi live streams, please create a firewall rule with the following settings:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | zixi-listener               | 
| Description |  For Zixi live streams                | 
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

## 5. Create Infrastructure
This step involves executing Bitmovin infrastructure API [3] for adding a GCP account.

https://bitmovin.com/docs/encoding/api-reference/sections/infrastructure#/Encoding/PostEncodingInfrastructureGce

Using the add GCE Account API, use the following json and replace the respective serviceAccountEmail, privateKey and projectId values with values from your GCP service account:
 
    {  
    "name": "Name of the resource",   
    "description": "Description of the resource",
    "customData": "string",
    "serviceAccountEmail": "bitmovin-connect-account@my-gcp-project.iam.gserviceaccount.com",
    "privateKey": "-----BEGIN PRIVATE KEY-----\nLoads\nOf\nStuff\nThats\nAll\nSecret\n-----END PRIVATE KEY-----\n",
    "projectId": "my-gcp-project"
    }


Note: The serviceAccountEmail, privateKey and projectId values can be retrieved from the json file in step (2) . serviceAccountEmail = client_email in (2).
## 6. Request access to MIs  
The Bitmovin platform uses private machine images (MIs) for encoder instances in GCE. Ask your Bitmovin technical contact with your GCP service account details so that your account is whitelisted to access these MIs.

## 7. Run Encoding Jobs
Just like using Bitmovin managed encoding service, use Bitmovin API client SDKs to submit encoding jobs similarly. The only difference is that you should specify the new infrastructure instead of public cloud regions. Here is a Python snippet demonstrating this.

    infra_id = ‘122c1111-9273-4d5f-a3fb-36100e90c709’ # Infrastructure object created
    infra_region = CloudRegion.GOOGLE_EUROPE_WEST_1# GCP region of the GPP-connect setup
    infrastructure = Infrastructure(infra_id, infra_region)
    encoding = Encoding(name='gcp connect encoding',
                        cloud_region=CloudRegion.EXTERNAL,
                        infrastructure=infrastructure,
                        encoder_version='STABLE')

## GCP Resource Quotas
If you want to run several encodings in parallel, then the default quota limits may not be sufficient. In that case, you will have to request limit increases for the following quotas in your Region(s):

| Quota name        | Limit to request           | 
| ------------- |:-------------:| 
| In-use IP addresses | (max. # of encodings) * (max # of instances per encoding)              | 
| CPUs | (max # of encodings) * 8  ) |
| Preemptible CPUs | (max # of encodings) * (max # of instances per encoding) * 8 ) |
| Persistent Disk SSD (GB) | max. # of encodings * 0.5 + (# instances * # encodings) * 0.05  |

assuming: 8 core instances. If your use case requires instances with a different number of cores, *contact bitmovin*

The maximum number of instances needed depends on the maximum number of parallel encodings running multiplied by the maximum number of instances needed for one encoding. The number of instances used by one encoding varies depending on the input file size and the number and data rate of the encoder Representations.

Generally, it cannot hurt to multiply the expected limit calculated for your current situation by 2, to have some margin in case you need to ramp up.

To view/edit your quotas, please go to [2]

## 9. References
[1] https://console.cloud.google.com/iam-admin/serviceaccounts?project=<YourProjectId>

[2] https://console.cloud.google.com/iam-admin/quotas?project=<YourProjectId>&service=compute.googleapis.com

[3] https://bitmovin.com/docs/encoding/api-reference/sections/infrastructure#/Encoding/PostEncodingInfrastructureGce


