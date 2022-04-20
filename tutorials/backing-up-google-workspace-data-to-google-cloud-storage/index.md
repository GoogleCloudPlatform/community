---
title: Backing up Google Workspace data to Google Cloud Storage with CubeBackup
description: Learn how to set up a backup solution for your Google Workspace domain, backing up data to a Google Cloud Storage bucket.
author: jerrywjh
tags: google workspace, google cloud, cubebackup 
date_published: 2022-04-28
---

Jerry Wang | co-founder | CubeBackup

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial describes how to set up a backup solution using [CubeBackup](https://www.cubebackup.com) to automatically backup Google Workspace data in your organization to your own Google Cloud Storage bucket. This tutorial is for Google Workspace administrators, security operators, and Google Workspace partners.

To use this tutorial, you need basic knowledge of Google Compute Engine, Google Cloud Storage and CubeBackup.

It is always important to make backups of your Google Workspace business data. Although Google’s cloud service is very reliable, it cannot protect against data loss caused by accidental or deliberate human error, like mistaken deletions, incorrect data hand-off from former employees, or even disgruntled insiders or malicious hackers. A reliable backup and restore solution like CubeBackup can act as a life-line when faced with this kind of data loss.

CubeBackup is a self-hosted application for Google Workspace.  Deploying CubeBackup on Google Cloud Platform offers an efficient, stable, and resilient backup for your Google Workspace business data. See [CubeBackup's website](https://cubebackup.com) for more information.

<img src="./google-workspace-backup-diagram.png" alt="Architecture diagram" style="width:80%">


## Objectives

* Launch CubeBackup on a Google Cloud Compute Engine VM instance.
* Create a service account for CubeBackup.
* Create a Google Cloud Storage bucket to store the backup data.
* Configure CubeBackup and start the backup.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*  [Compute Engine](https://cloud.google.com/compute)

For organizations with more than 100 employees, an **e2-standard-2** VM instance with 8GB RAM is recommended for running the backup service.

*  [Cloud Storage](https://cloud.google.com/storage)

The pricing for Google Cloud Storage varies depending on the storage class and the location of your bucket. Considering both the data storage cost and the data processing cost, the **Coldline Storage** class is recommended for storing your Google Workspace backups.

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a Google Cloud cost estimate based of your projected usage.


In addtion to the cost of Google Cloud, you also need to pay for the license of CubeBackup. CubeBackup is licensed on a per-user basis:  
*   *$5/user/year* for Google Workspace Business/Enterprise organizations.
*   *$2/user/year* for Google Workspace Education/Nonprofit organizations.
*   An unlimited 14-day trial of CubeBackup is available to all new users.


## Before you begin

1.  Create a new Google Cloud project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).


## Deploy CubeBackup on Google Cloud using Google Cloud Image

As a Google Workspace backup solution, CubeBackup is available on the [Google Cloud Marketplace](https://cloud.google.com/marketplace). Using the CubeBackup virtual machine images on the marketplace, you can easily launch a CubeBackup instance with only a few clicks.

1. Search for “CubeBackup” in the Google Cloud Marketplace. You will see 3 results: *CubeBackup for Linux*, *CubeBackup for Windows*, and *CubeBackup for Docker*. Click whichever image you desire.
1. On the CubeBackup image page, click **LAUNCH**.  
   Google APIs, like *Compute Engine API*, *Cloud Deployment Manager V2 API*,and *Cloud Runtime Configuration API*, are required to deploy a VM from Marketplace. If prompted with the *Required APIs* dialog, click **ENABLE** to proceed. 

1. On the CubeBackup deployment page, configure the *Deployment name*, *Zone*, *Machine type*, and *Boot Disk size* for your VM.  
    * Please select the Zone which is closest to your organization, or in accordance with the data policy of your organization or country.
    * CubeBackup requires no less than 4 GB of memory (8GB is strongly recommended) and 100GB for the boot disk.
    * If you’d like to access the web console from the Internet, please be sure to allow HTTP and HTTPS traffic in the Firewall section.
   ![Deploy on compute engine](./compute-engine-vm.png) 
1.  When all parameters have been properly set, click **DEPLOY** to start the VM instance. The deployment process may take one or two minutes to complete.
1.  Once the CubeBackup image is successfully deployed and the new VM is running, the CubeBackup service will have been installed and automatically started. After creating a Google Cloud Storage bucket, you can click **VISIT THE SITE** to start the initial configuration of CubeBackup.

##  Create a Google Cloud Storage bucket for the backup data

When CubeBackup has been successfully deployed on the Compute Engine VM, you can start to create a Google Cloud Storage bucket to store the backup data.

1. In your Google Cloud Console, Select **STORAGE** > **Cloud Storage** > **Browser** from the navigation menu.
1. Click **CREATE BUCKET** on the *Cloud Storage Browser* page.
1. In the *Create a bucket* page, enter a valid name for the bucket and click **CONTINUE**.
1. Choose a location type for the bucket (*Region* or *Multi-region* is recommended), and select a location for the bucket, then click **CONTINUE**.  
You should select the location based on the security & privacy policy of your organization. For example, for EU organizations, you may need to select a European data center to be in accordance with GDPR.  If possible, try to choose the same location as your Compute Engine VM.
1. Choose a default storage class for the backup data (*Coldline* is recommended), then click **CONTINUE**.   
The pricing of Google Cloud Storage varies depending on location and storage class. Please see [Cloud Storage Pricing](https://cloud.google.com/storage/pricing) for more information. 
1. Choose *Uniform* as the Access control type, and click **CONTINUE**.  
1. Leave other options as default, then click **CREATE**.

CubeBackup itself has object versioning and data encryption functions, so there is no need to enable the *Object versioning*, *Retention policy*, or *Data Encryption* for this bucket. Otherwise, this may result in unnecessary file duplication and extra costs. 


## Initial configuration for Google Workspace backup through CubeBackup console

1. Open the initial configuration wizard.  
After launching the CubeBackup Compute Engine VM and creating the Cloud Storage bucket, you can open the CubeBackup console by visiting *http://\<ComputeEngineVM-IP\>* from your web browser. Follow the configuration wizard to complete the initial configuration of CubeBackup.
 
1. Choose the Google Cloud Storage bucket to store the backup data.  
In the “Set up data storage location” step, choose *Google Cloud storage* as the Storage type, and leave the Data Index path as it is. Enter the name of the bucket you just created, then click **Next**. 
           <img src="./step2google.png" alt="set up backup location"  style="width: 70%"> 
1. Create a Google Service account.  
In step 3 in the wizard, you must supply the service account key file, along with the Google Workspace domain name and domain administrator. But first, you need to enable necessary APIs in your project:

    *  Open the *API Library* page by selecting **APIs & services** > **Library** from the navigation menu.
    *  Search for **Google Drive API**, then on the *Google Drive API* page, click **ENABLE**.
    *  Return to the *API Library* page and follow the same steps to enable **Google Calendar API**, **Gmail API**, **Admin SDK API**, and **Google People API**.

    Next, you will need to create a Google Service account:

    *  Select **IAM & Admin** > **Service Accounts** in the navigation menu.
    *  Click **+CREATE SERVICE ACCOUNT**.
    *  In the “Service account details” step, enter a name for the service account (*e.g., cubebackup*) and click **CREATE AND CONTINUE**.
    *  In the second step, select “Basic” > “Owner” (or “Project” > “Owner”) as the Role, then click **CONTINUE**.
    *  Click **DONE** directly in the “Grant users access to this service account” step.
    *  On the Service accounts page, click the email of the service account you just created. This should take you to the Service account details page.
    *  Select the **KEYS** tab of the service account.
    *  Click **ADD KEY** > **Create new key**.
    *  Select **JSON** as the key type, then click **CREATE**.
    *  Close the dialog that pops up and save the generated JSON key file locally.
 
    Now, return to the CubeBackup configuration wizard, click the **Choose File** button and select the service account JSON key file just generated. After the Google Workspace domain name, the domain administrator, and the service account key file are all set, click **Next**.
           <img src="./step3.png" alt="domain and service account"  style="width: 70%"> 

1.  Authorize domain-wide access to the service account.
 
The newly created service account needs to be authorized to access your Google Workspace data through Google APIs. 
*  Sign in to the [Google Admin console](https://admin.google.com/) using a domain administrator account.
*  Select **Security** > **Access and data control** > **API controls** from the main menu.
*  Click **MANAGE DOMAIN WIDE DELEGATION** in the *Domain wide delegation* section.
*  In the *Domain-wide Delegation* page, click **Add new**.
*  In the **Client ID** field, paste the Client ID copied from the step 4 of the configuration wizard.
*  In the **OAuth Scopes** field, copy and paste the following scopes, then Click **AUTHORIZE**.

        https://www.googleapis.com/auth/admin.directory.domain.readonly,
        https://www.googleapis.com/auth/admin.directory.user.readonly,
        https://www.googleapis.com/auth/admin.directory.orgunit.readonly,
        https://mail.google.com/,
        https://www.googleapis.com/auth/drive,
        https://www.googleapis.com/auth/calendar,
        https://www.googleapis.com/auth/contacts, 
        https://sites.google.com/feeds/
 
 
The service account has now been authorized to make API calls in your domain.  In the CubeBackup configuration wizard Step 4, click the Next button to see if all changes have been successful.  Please note that Google Workspace domain-wide authorization may need some time to propagate, so if any error message pops up, please retry after a few minutes.












## Tutorial body

Break the tutorial body into as many sections and subsections as needed, with concise headings.

### Use short numbered lists for procedures

Use numbered lists of steps for procedures. Each action that the reader must take should be its own step. Start each step with the action, such as *Click*, 
*Run*, or *Enter*.

Keep procedures to 7 steps or less, if possible. If a procedure is longer than 7 steps, consider how it might be separated into sub-procedures, each in its
own subsection.

### Provide context, but don't overdo the screenshots

Provide context and explain what's going on.

Use screenshots only when they help the reader. Don't provide a screenshot for every step.

Help the reader to recognize what success looks like along the way. For example, describing the result of a step helps the reader to feel like they're doing
it right and helps them know things are working so far.

## Cleaning up

Tell the reader how to shut down what they built to avoid incurring further costs.

### Example: Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

Tell the reader what they should read or watch next if they're interested in learning more.

### Example: What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
