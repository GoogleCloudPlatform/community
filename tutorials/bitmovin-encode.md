---
title: Deploy Bitmovin Encoding on Compute Engine 
description: This tutorial walks you through the process of installing Bitmovin Video Encoding on Google Cloud.
author: Adrian-in-Aus
tags: bitmovin, video, encoding, scale
date_published: 2020-08-07
---

This document explains how to set up Bitmovin Encoding on Google Cloud infrastructure so that the Bitmovin platform can run encoders using the Compute Engine 
API.

## Prerequisites

* [Google Cloud account](https://cloud.google.com/billing/docs/how-to/manage-billing-account)
* [Google Cloud project created](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
* [Compute Engine API enabled](https://console.cloud.google.com/apis/library/compute.googleapis.com)

## Create service account

1.  [Create a service account](https://console.cloud.google.com/iam-admin/serviceaccounts) with ‘Compute Admin’ permissions. This is needed for the compute related permissions on the Infrastructure side like
    starting/stopping instances. 
    
1.  Create a key for the service account and download the JSON file containing the private key. Following information will be needed from the json file. This is 
    needed to create an InfrastructureId on the Bitmovin platform which can then be used to run encodings on a customer's GCE infrastructure.

    * project_id
    * private_key
    * client_email

## 3. Set up mandatory firewall rules

These are the basic firewall rules without which starting an encoding will fail.

Go to the [Firewall page](https://console.cloud.google.com/networking/firewalls/list) in the Cloud Console and click **Create firewall rule**.

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

## Set Up Firewall rules for live streams

Additional firewall rules are required to be set up for encoding RTMP, SRT and Zixi live streams. 

### Firewall rules necessary for RTMP live streams 

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

### Firewall rules necessary for SRT live streams

If you intend to run SRT live streams, please create a firewall rule with the following settings:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | srt-listener               | 
| Description |  For SRT live streams                | 
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

### Firewall rules necessary for Zixi live streams

If you intend to run Zixi live streams, please create a firewall rule with the following settings:

| Field        | Value to set           | 
| ------------- |:-------------:| 
| Name | zixi-listener               | 
| Description |  For Zixi live streams                | 
| Targets | All instances in the network                  | 
| Source filters | *contact bitmovin for details*         | 
| Protocols and ports | *contact bitmovin for details*    | 

## Create infrastructure

This step involves executing the
[Bitmovin infrastructure API](https://bitmovin.com/docs/encoding/api-reference/sections/infrastructure#/Encoding/PostEncodingInfrastructureGce) for adding a
Google Cloud account.

Using the add GCE Account API, use the following json and replace the respective serviceAccountEmail, privateKey and projectId values with values from your GCP service account:
 
    {  
    "name": "Name of the resource",   
    "description": "Description of the resource",
    "customData": "string",
    "serviceAccountEmail": "bitmovin-connect-account@my-gcp-project.iam.gserviceaccount.com",
    "privateKey": "-----BEGIN PRIVATE KEY-----\nLoads\nOf\nStuff\nThats\nAll\nSecret\n-----END PRIVATE KEY-----\n",
    "projectId": "my-gcp-project"
    }


The serviceAccountEmail, privateKey and projectId values can be retrieved from the json file in step (2) . serviceAccountEmail = client_email in (2).

## Request access to machine images

The Bitmovin platform uses private machine images (MIs) for encoder instances in GCE. Ask your Bitmovin technical contact with your GCP service account details 
so that your account is whitelisted to access these MIs.

## Run encoding jobs

Just like using Bitmovin managed encoding service, use Bitmovin API client SDKs to submit encoding jobs similarly. The only difference is that you should specify
the new infrastructure instead of public cloud regions. Here is a Python snippet demonstrating this.

    infra_id = ‘122c1111-9273-4d5f-a3fb-36100e90c709’ # Infrastructure object created
    infra_region = CloudRegion.GOOGLE_EUROPE_WEST_1# GCP region of the GPP-connect setup
    infrastructure = Infrastructure(infra_id, infra_region)
    encoding = Encoding(name='gcp connect encoding',
                        cloud_region=CloudRegion.EXTERNAL,
                        infrastructure=infrastructure,
                        encoder_version='STABLE')

## Google Cloud resource quotas

If you want to run several encodings in parallel, then the default quota limits may not be sufficient. In that case, you will have to request limit increases for
the following quotas in your Region(s):

| Quota name        | Limit to request           | 
| ------------- |:-------------:| 
| In-use IP addresses | (max. # of encodings) * (max # of instances per encoding)              | 
| CPUs | (max # of encodings) * 8  ) |
| Preemptible CPUs | (max # of encodings) * (max # of instances per encoding) * 8 ) |
| Persistent Disk SSD (GB) | max. # of encodings * 0.5 + (# instances * # encodings) * 0.05  |

assuming: 8 core instances. If your use case requires instances with a different number of cores, *contact bitmovin*

The maximum number of instances needed depends on the maximum number of parallel encodings running multiplied by the maximum number of instances needed for one encoding. The number of instances used by one encoding varies depending on the input file size and the number and data rate of the encoder Representations.

Generally, it cannot hurt to multiply the expected limit calculated for your current situation by 2, to have some margin in case you need to ramp up.

To view/edit your quotas, go to the [Quotas page](https://console.cloud.google.com/iam-admin/quotas) in the Cloud Console.
