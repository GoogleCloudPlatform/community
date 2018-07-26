
This tutorial describes how to use Google Cloud Storage (GCS) for a filestore managed by the JFrog Artifactory universal binary repository manager. When the procedure is complete, all artifacts pushed to Artifactory will be stored in GCS, and all artifacts retrieved through Artifactory will be drawn from GCS.

Using GCS for your Artifactory filestore provides a secure, scalable binary repository that is stored remotely and with redundancy, aiding swift data recovery from a local disaster.

 
## Objectives
To move your Artifactory filestore to GCS, you need to execute the following steps:
* Ready Google Cloud Storage
* Ready Artifactory
* Configure Artifactory to use GCS
* Migrate your filestore to GCS

## Before You Begin

This tutorial assumes you already have a GCS account and have completed the Google Cloud Storage [quickstart documentation](https://cloud.google.com/storage/docs/quickstarts).

You also need to have a licensed copy of JFrog Artifactory Enterprise Edition. v4.6 or later, and have completed the Artifactory [installation procedure](https://www.jfrog.com/confluence/display/RTF/Installing+Artifactory).


## Costs

This tutorial uses billable components of GCP, including:

- Google Cloud Storage

You can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.


## Setting up Artifactory to Use GCS


### Step 1: Ready Google Cloud Storage

You must have a Google Cloud Storage account, with a [Bucket](https://cloud.google.com/storage/docs/key-terms#buckets) created to hold your binary repository data.

#### Acquire interoperable storage access keys

The API for [Google Cloud Storage Interoperability](https://cloud.google.com/storage/docs/interoperability) uses HMAC authentication and lets GCS interoperate with tools written for  cloud storage systems. 

To use GCS, you need to turn on this API and use interoperability access details of the current user in GCS. This API is enabled per project member, not per project. Each member can set a default project and maintain their own access keys. 

You can obtain your access key parameters through your Google GCS account console. You will use these values for the corresponding parameters in Artifactory when you configure it to use GCS:


 | GCS Value | Description |
 | --- | --- |
 | _access key_ | This GCS account value will be used as the Artifactory parameter __identity__.  |
 | _access secret_ | This GCS account value will be used as the Artifactory parameter __credential__. |


#### Create a storage bucket in GCS
Use the Cloud Storage Browser to [create a storage bucket in GCS](https://cloud.google.com/storage/docs/creating-buckets), as the place where artifacts will be stored.

### Step 2: Ready Artifactory

You must prepare Artifactory before assigning GCS as your filestore. The procedure you use depends on whether it is a new or existing installation of Artifactory.

#### Option A: Install Artifactory
If you have not yet installed Artifactory Enterprise Edition v4.6 or newer, do so now. Perform a standard [installation](https://www.jfrog.com/confluence/display/RTF/Installing+Artifactory) using the default settings.

#### Option B: Existing Artifactory installation
If you have an installed version of Artifactory, perform these steps:
##### Backup your current filestore

Just in case something goes wrong, we recommend backing up your current filestore. To preserve your current filestore as a safety measure, perform a [complete system  backup](https://www.jfrog.com/confluence/display/RTF5X/Managing+Backups#ManagingBackups-CompleteSystemBackup) of Artifactory.

##### Make sure your version of Artifactory supports GCS
If your version of Artifactory is __not__ Enterprise Edition v4.6 or newer, you must perform a standard [upgrade](https://www.jfrog.com/confluence/display/RTF/Upgrading+Artifactory) using your current settings.


#### Stop Artifactory

Shut down Artifactory. It should not be running for the remaining steps.

#### Confirm your enterprise license key

To use Artifactory's support for GCS, you must have an enterprise license for your Artifactory installation. Make sure your `$ARTIFACTORY_HOME/etc/artifactory.lic` file contains your enterprise license key.


### Step 3: Configure Artifactory to use GCS

Artifactory offers flexible filestore management through the _`binarystore.xml`_ configuration file located in the _`$ARTIFACTORY_HOME/etc`_ folder. By modifying this file you can implement a variety of different binary storage configurations.

To configure Artifactory to use a GCS object storage provider, you need to specify **`google-storage`** as the binary provider in the configuration file. You will also need to provde the name of the bucket to use, and the interoperability storage keys.

The following XML snippet shows the default chain that uses **`google-storage`** as the binary provider:

```xml
<config version="v1">
    <chain>
       <provider id="cache-fs" type="cache-fs">
           <provider id="eventual" type="eventual">
               <provider id="retry" type="retry">
                   <provider id="google-storage" type="google-storage"/>
               </provider>
           </provider>
       </provider>
   </chain>
  
<!-- Here is an example configuration part for the google-storage: -->
    <provider id="google-storage" type="google-storage">
       <endpoint>commondatastorage.googleapis.com</endpoint>
        <bucketName><NAME></bucketName> 
       <identity>XXXXXX</identity>
       <credential>XXXXXXX</credential>
    </provider>
</config>
```
You should use the interoperability values from your GCS account (as described in Step 1) for __identity__ and __credential__.  The name of the bucket you created in GCS should be used as the __bucketName__.

#### Other parameters
The full set of parameters available for the **`google-storage`** binary provider offer other options that may be useful.

Artifactory uses the JetS3t framework to access GCS. Some of the parameters below are used to set the corresponding value in the framework. For more details, please refer to the [JetS3t Configuration Guide](http://www.jets3t.org/toolkit/configuration.html).



 | Parameter | Description |
 | --- | --- |
 | __testConnection__ | Default: true<br/>When true, the Artifactory uploads and downloads a file when starting up to verify that the connection to the cloud storage provider is fully functional. |
 | __multiPartLimit__ | Default: 100,000,000 bytes <br/>File size threshold over which file uploads are chunked and multi-threaded. |
 | __identity__ | Your cloud storage provider identity. |
 | __credential__ | Your cloud storage provider authentication credential. |
 | __bucketName__ | <span>Your globally unique bucket name on GCS.</span> |
 | __path__ | The relative path to your files within the bucket |
| __proxyIdentity__ __proxyCredential__ __proxyPort__ __proxyHost__ | Corresponding parameters if you are accessing the cloud storage provider through a proxy server. | 
 | __port__ | Default: 80 <br/>The port number through which you want to access GCS. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
 | __endpoint__ | Default: commondatastorage.googleapis.com. <br/>The GCS hostname. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
 | __httpsOnly__ | Default: false. <br/>Set to true if you only want to access GCS through a secure https connection. |
 | __httpsPort__ | Default: 443 <br/>The port number through which you want to access GCS securely through https. You should only use the default value unless you need to contact a different endpoint for testing purposes. |
 | __bucketExists__ | Default: false. Only available on _google-storage_. <br/>When true, it indicates to the binary provider that a bucket already exists in Google Cloud Storage and therefore does not need to be created. |
 
For more information, see the Artifactory User's Guide topic [Configuring the Filestore](/confluence/display/RTF5X/Configuring+the+Filestore#ConfiguringtheFilestore-GoogleStorage,S3andS3OldBinaryProviders).



### Step 4: Migrate your filestore to GCS

To migrate your filestore, you need to execute the following steps:

* Copy the `$ARTIFACTORY_HOME/data/filestore` directory to your GCS bucket .
* Start Artifactory

<!--stackedit_data:
eyJoaXN0b3J5IjpbMTY4ODY3MTk5MywyNDQyNzQ0NzEsLTE3ND
cxMDMwNTIsNzI4NjM0Mjc1LC03MzM5NTY1MzAsMTE5NTg3NDY4
MiwxNTcxODczOTM3LDEyNjA2NTI3MzksLTExMTI5NzU3NDcsMj
Q0NDQ2MjkzLC00ODMzMjQwMzEsLTgxMTE0NzU4NSwxODUzMTUw
Mjg2XX0=
-->