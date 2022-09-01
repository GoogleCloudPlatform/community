---
title: Using Cloud Storage with a JFrog Artifactory filestore
description: Learn how to use Cloud Storage for a filestore managed by a JFrog Artifactory universal repository manager.
author: jfrogtw
tags: Cloud Storage
date_published: 2018-09-24
---

Gianni Truzzi | JFrog

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial describes how to use Cloud Storage for a filestore managed
by the JFrog [Artifactory universal repository manager](https://jfrog.com/artifactory/).
When the procedure is complete, all artifacts pushed to Artifactory will be
stored in Cloud Storage, and all artifacts retrieved through Artifactory will be
drawn from Cloud Storage.

Using Cloud Storage for your Artifactory filestore provides a secure, scalable
binary repository that is stored remotely and with redundancy, aiding swift data
recovery from a local disaster.

## Objectives

To move your Artifactory filestore to Cloud Storage, execute the following
steps:

* Ready Cloud Storage
* Ready Artifactory
* Configure Artifactory to use Cloud Storage
* Migrate your filestore to Cloud Storage

## Before you begin

This tutorial assumes you already have a Google Cloud account and
have completed the Cloud Storage [quickstart documentation](https://cloud.google.com/storage/docs/introduction#quickstarts).

You also need to have a licensed copy of JFrog Artifactory Enterprise Edition.
v4.6 or later, and have completed the Artifactory [installation procedure](https://www.jfrog.com/confluence/display/RTF/Installing+Artifactory).

## Costs

This tutorial uses billable components of Google Cloud, including Cloud Storage.

You can use the [Pricing Calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected production usage.

## Setting up Artifactory to use Cloud Storage

### Step 1: Ready Cloud Storage

Acquire the keys necessary for Cloud Storage and Artifactory interoperability,
and create a Cloud Storage [Bucket](https://cloud.google.com/storage/docs/buckets)
to hold your binary repository data.

#### Acquire interoperable storage access keys

The API for [Cloud Storage interoperability](https://cloud.google.com/storage/docs/interoperability)
uses HMAC authentication and lets Cloud Storage interoperate with tools written
for cloud storage systems.

To use Cloud Storage with Artifactory, [turn on the Cloud Storage Interoperability API](https://support.google.com/cloud/answer/6158841).
This API is enabled per project member, not per project. Each member can set a
default project and maintain their own access keys.

Once the API is enabled, [use the Cloud Storage console to obtain your access key and access secret](https://console.cloud.google.com/projectselector/storage/).
You will use these values for the corresponding parameters in Artifactory when
you configure it to use Cloud Storage:


| Cloud Storage Value | Description |
| --- | --- |
| _access key_ | This Cloud Storage account value will be used as the Artifactory parameter __identity__.  |
| _access secret_ | This Cloud Storage account value will be used as the Artifactory parameter __credential__. |

#### Create a storage bucket in Cloud Storage

Use the Cloud Storage Browser to [create a storage bucket in Cloud Storage](https://cloud.google.com/storage/docs/creating-buckets),
as the place where artifacts will be stored.

### Step 2: Ready Artifactory

You must prepare Artifactory before assigning Cloud Storage as your filestore.
The procedure you use depends on whether it is a new or existing installation of
Artifactory.

#### Option A: Install Artifactory

If you have not yet installed Artifactory Enterprise Edition v4.6 or newer, do
so now. Perform a standard [installation](https://www.jfrog.com/confluence/display/RTF/Installing+Artifactory)
using the default settings.

#### Option B: Existing Artifactory installation
If you have an installed version of Artifactory, perform these steps:

* **Backup your current filestore:** Just in case something goes wrong, we
  recommend backing up your current filestore. To preserve your current
  filestore as a safety measure, perform a [complete system  backup](https://www.jfrog.com/confluence/display/RTF5X/Managing+Backups#ManagingBackups-CompleteSystemBackup)
  of Artifactory.
* **Make sure your version of Artifactory supports Cloud Storage:** If your
  version of Artifactory is __not__ Enterprise Edition v4.6 or newer, you must
  perform a standard [upgrade](https://www.jfrog.com/confluence/display/RTF/Upgrading+Artifactory)
  using your current settings.
*  **Stop Artifactory:** Shut down Artifactory. It should not be running for the
remaining steps.

#### Confirm your enterprise license key

To use Artifactory's support for Cloud Storage, you must have an enterprise
license for your Artifactory installation. Make sure your
`$ARTIFACTORY_HOME/etc/artifactory.lic` file contains your enterprise license
key.

### Step 3: Configure Artifactory to use Cloud Storage

Artifactory offers flexible filestore management through the `binarystore.xml`
configuration file located in the `$ARTIFACTORY_HOME/etc` folder. By modifying
this file you can implement a variety of different binary storage
configurations.

To configure Artifactory to use a Cloud Storage object storage provider, you
need to specify **`google-storage`** as the binary provider in the configuration
file. You will also need to provde the name of the bucket to use, and the
interoperability storage keys.

Add [this example XML](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/artifactory-gcs-setup/binarystore-example.xml)
into the `binarystore.xml` file to setup a default chain that uses
**`google-storage`** as the binary provider:

You should use the interoperability values from your Cloud Storage account
(as described in Step 1) for __identity__ and __credential__.  The name of the
bucket you created in Cloud Storage should be used as the __bucketName__.

#### Other parameters

The full set of parameters available for the **`google-storage`** binary
provider offer other options that may be useful.

Artifactory uses the JetS3t framework to access Cloud Storage. Some of the
parameters below are used to set the corresponding value in the framework. For
more details, please refer to the [JetS3t Configuration Guide](http://www.jets3t.org/toolkit/configuration.html).

| Parameter | Description |
| --- | --- |
| __testConnection__ | Default: true. When true, the Artifactory uploads and downloads a file when starting up to verify that the connection to the cloud storage provider is fully functional. |
| __multiPartLimit__ | Default: 100,000,000 bytes. File size threshold over which file uploads are chunked and multi-threaded. |
| __identity__ | Your cloud storage provider identity. |
| __credential__ | Your cloud storage provider authentication credential. |
| __bucketName__ | Your globally unique bucket name on Cloud Storage. |
| __path__ | The relative path to your files within the bucket |
| __proxyIdentity__ __proxyCredential__ __proxyPort__ __proxyHost__ | Corresponding parameters if you are accessing the cloud storage provider through a proxy server. |
| __port__ | Default: 80. The port number through which you want to access Cloud Storage. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
| __endpoint__ | Default: _commondatastorage.googleapis.com_. The Cloud Storage hostname. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
| __httpsOnly__ | Default: false. Set to true if you only want to access Cloud Storage through a secure https connection. |
| __httpsPort__ | Default: 443. The port number through which you want to access Cloud Storage securely through https. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
| __bucketExists__ | Default: false. Only available on _google-storage_. When true, it indicates to the binary provider that a bucket already exists in Google Cloud Storage and therefore does not need to be created. |

For more information, see the Artifactory User's Guide topic [Configuring the Filestore](https://www.jfrog.com/confluence/display/RTF5X/Configuring+the+Filestore#ConfiguringtheFilestore-GoogleStorage,S3andS3OldBinaryProviders).

### Step 4: Migrate your filestore to Cloud Storage

To migrate your filestore, execute the following steps:

* Copy the `$ARTIFACTORY_HOME/data/filestore` directory to your Cloud Storage
    bucket.
* Start Artifactory
