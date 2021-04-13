---
title: Label resources automatically based on Cloud Asset Inventory real-time notifications
description: Learn how to trigger actions automatically based on Cloud Asset Inventory real-time notifications.
author: kylgoog
tags: asset-inventory,cloud-asset-inventory,labeling
date_published: 2021-03-30
---

KaYun Lam | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Asset Inventory](https://cloud.google.com/asset-inventory) allows the setup of
[real-time notifications](https://cloud.google.com/asset-inventory/docs/monitoring-asset-changes) when asset configuration changes occur. This is convenient when
a set of common tasks needs to be done upon resource creation or modification, which is a common scenario for governance of cloud resources in enterprises.  

In this tutorial, labels are automatically applied for Compute Engine VM instances, Google Kubernetes Engine (GKE) clusters, Cloud SQL instances, and Cloud 
Storage buckets upon creation of these assets across any projects in the selected folder or organization. You set up a Cloud Pub/Sub topic to get real-time 
updates on changes to configurations for any of these assets. You then deploy a Cloud Function to perform the labeling of resources automatically using the 
resource names in near real time.  This example is useful if more fine-grained visibility is needed on
[Google Cloud Billing reports](https://cloud.google.com/billing/docs/how-to/reports) or
[Cloud Billing export to BigQuery](https://cloud.google.com/billing/docs/how-to/export-data-bigquery), in which the data can be
[filtered by labels](https://cloud.google.com/billing/docs/how-to/bq-examples#query-with-labels).

![Diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-asset-inventory-auto-label-resources/cloud-asset-inventory-auto-label-resources.png)

To complete this tutorial, you need IAM permissions at the organization or folder level. This tutorial requires a basic understanding of using shell commands.
To customize Cloud Functions to automatically perform actions other than automatic labeling, you need some basic programming ability.

## Resources to be automatically labeled

The following Google Cloud resources are automatically labeled in this tutorial: 

* **Compute Engine VM**: Labels are applied to newly created virtual machine (VM) instances.
* **GKE cluster**: Cluster labels are applied to newly created GKE clusters. The labels are
  [propagated down to the individual resources](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-managing-labels#about_labeling_clusters).
* **Cloud Storage bucket**: Labels are applied to newly created buckets.
* **Cloud SQL instance**: Labels are applied to newly created Cloud SQL instances.

All of the labeling operations are done while preserving the other labels that are already set, such as labels that are specified during creation.

If a label with the exact same key already exists—for example, because the label was specified manually with the exact same key during asset creation—then the
code in this tutorial overrides that existing label value.

## Costs

The labeling mechanism in this tutorial uses the following billable components of Google Cloud:

* [Cloud Asset Inventory](https://cloud.google.com/asset-inventory/pricing)
* [Pub/Sub](https://cloud.google.com/pubsub/pricing)
* [Cloud Functions](https://cloud.google.com/functions/pricing)

The labeling function in this tutorial monitors changes to configurations for the following billable components of Google Cloud:

* [Cloud Engine](https://cloud.google.com/compute/vm-instance-pricing)
* [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/pricing)
* [Cloud Storage](https://cloud.google.com/storage/pricing)
* [Cloud SQL](https://cloud.google.com/sql/pricing)

You can choose to use a Compute Engine VM instance of the smallest machine type (`f1-micro`) to minimize the cost for testing, and you can delete resources after
the testing. Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

To host the resources in this tutorial, you must set up a Google Cloud project with billing enabled. This tutorial uses Cloud Shell to run shell commands.

1.  Use the Cloud Console to [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project) to host the 
    Pub/Sub and Cloud Functions resources in this tutorial. Choose a billing account to enable billing for the project. Note the project ID; you use it in a 
    later step.

1. In the Cloud Console, [activate Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell#launching_from_the_console).

## Set up the auto-labeling system

### Set the organization ID environment variable

1.  Set the `ORGANIZATION_ID` environment variable, using the Google Cloud project ID as input:

        ORGANIZATION_ID=$(gcloud projects get-ancestors ${GOOGLE_CLOUD_PROJECT} --format="csv[no-heading](id,type)" | grep ",organization$" | cut -d"," -f1 )

1.  Check the organization ID numerical value:

        echo ORGANIZATION_ID=${ORGANIZATION_ID}

### (Optional) Determine the folder under which to monitor the asset changes

You can use the mechanism in this tutorial to automatically label resources created in any projects in a specified organization or in any projects in a specified
folder. 

You can ignore this section if you want to monitor asset changes across the organization. You only need to use the instructions in this section if 
you want monitor asset changes in a specified folder.

1.  Set your folder ID to the folder that you want to monitor:

        FOLDER_ID=[NUMERIC_FOLDER_ID_VALUE]

1.  Create a new folder under which the project resources are to be monitored:

        gcloud organizations add-iam-policy-binding ${ORGANIZATION_ID} --member="user:$(gcloud config get-value account)" --role="roles/resourcemanager.folderCreator"

        FOLDER_ID=$( gcloud resource-manager folders create --display-name="auto-label-folder" --organization=${ORGANIZATION_ID} --format="value('name')" | cut -d"/" -f2 )

1.  Check the folder ID:

        echo FOLDER_ID=${FOLDER_ID}

### Set the variables for the project hosting the Pub/Sub and the Cloud Functions resources

1.  Set your project ID to the project you want to use to host the Pub/Sub and the Cloud Functions resources:

        PROJECT_ID=[ALPHANUMERIC_PROJECT_ID]

    If you have already selected the project that you want to use, you can instead use the setting from the Cloud Shell `gcloud` environment:
    
        PROJECT_ID=$(gcloud config get-value project)

1.  Confirm that the `PROJECT_ID` alphanumeric value is set correctly:

        echo PROJECT_ID=${PROJECT_ID}

1.  Retrieve the project number, using the project ID as input:

        PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(project_number)")
        
1.  Confirm that the `PROJECT_NUMBER` value is set correctly:

        echo PROJECT_NUMBER=${PROJECT_NUMBER}

### Create the service account for the Cloud Function

1.  Create a service account to be used by the Cloud Function that sets the Compute Engine VM labels:

        SERVICE_ACCOUNT_PROJECT_ID=${PROJECT_ID}

        GCF_SERVICE_ACCOUNT_NAME="resource-labeler-sa"
        gcloud iam service-accounts create "${GCF_SERVICE_ACCOUNT_NAME}" --project ${SERVICE_ACCOUNT_PROJECT_ID}
        GCF_SERVICE_ACCOUNT="${GCF_SERVICE_ACCOUNT_NAME}@${SERVICE_ACCOUNT_PROJECT_ID}.iam.gserviceaccount.com"

        echo GCF_SERVICE_ACCOUNT="${GCF_SERVICE_ACCOUNT}"

    **Note**: The service account must be created in the same project as the function that it's attached to. For more information, see
    [this page](https://cloud.google.com/functions/docs/securing/function-identity#per-function_identity).


### Create the IAM role to be used by the service account for the Cloud Function

1.  Assign yourself the permission to create organization roles, if you do not already have it:

        gcloud organizations add-iam-policy-binding ${ORGANIZATION_ID} --member="user:$(gcloud config get-value account)" --role="roles/iam.organizationRoleAdmin"

1.  Create the custom role at the organization level:

        PERMISSIONS="compute.instances.get,compute.instances.setLabels,container.clusters.get,container.clusters.update,storage.buckets.get,storage.buckets.update,cloudsql.instances.get,cloudsql.instances.update"
        gcloud iam roles create ResourceLabelerRole --organization=${ORGANIZATION_ID} --title "Resource Labeler Role" --permissions "${PERMISSIONS}" --stage GA

**Note**: If you need to update the role with more permissions, you do so with a similar syntax:

    gcloud iam roles update ResourceLabelerRole --organization=${ORGANIZATION_ID} --title "Resource Labeler Role" --permissions "${PERMISSIONS}" --stage GA

### Add the IAM policy bindings needed on the service account and the folder or organization

1.  Retrieve your own username from the environment:

        MEMBER="user:$(gcloud config get-value account)"

    If a separation of duty is required (that is, someone else will be setting up the Pub/Sub and Cloud Functions resources), then you can set this manually:
    
        MEMBER="user:username@example.com"

1.  Service Account IAM bindings: Give the `MEMBER` user permission to use the service account in order to deploy the Cloud Function:

        gcloud iam service-accounts add-iam-policy-binding "${GCF_SERVICE_ACCOUNT}" --member="${MEMBER}" --role="roles/iam.serviceAccountUser" --project "${SERVICE_ACCOUNT_PROJECT_ID}"

1.  Give the `MEMBER` user permission to create the asset feed, using one or the other of the following sets of commands, depending on whether you want
    to monitor at the organization level or the folder level:

    -   Organization-level IAM bindings:

            gcloud organizations add-iam-policy-binding ${ORGANIZATION_ID} --member="${MEMBER}" --role="roles/cloudasset.owner"
            gcloud organizations add-iam-policy-binding ${ORGANIZATION_ID} --member="serviceAccount:${GCF_SERVICE_ACCOUNT}" --role="organizations/${ORGANIZATION_ID}/roles/ResourceLabelerRole"

    -   Folder-level IAM bindings on the folder under which the assets (such as Compute Engine VMs) are to be monitored:

            gcloud resource-manager folders add-iam-policy-binding ${FOLDER_ID} --member="${MEMBER}" --role="roles/cloudasset.owner"
            gcloud resource-manager folders add-iam-policy-binding ${FOLDER_ID} --member="serviceAccount:${GCF_SERVICE_ACCOUNT}" --role="organizations/${ORGANIZATION_ID}/roles/ResourceLabelerRole"

### Enable the APIs in the project issuing the Asset APIs, hosting the Pub/Sub and Cloud Functions resources

Enable the required Google Cloud APIs.

1.  Enable the APIs for the labeling pipeline:

        gcloud services enable cloudasset.googleapis.com pubsub.googleapis.com cloudfunctions.googleapis.com cloudbuild.googleapis.com --project ${PROJECT_ID}

1.  Enable the APIs for the monitored services for simplicity of the function code on the labeling actions:

        gcloud services enable compute.googleapis.com container.googleapis.com storage.googleapis.com sqladmin.googleapis.com --project ${PROJECT_ID}

### Add the IAM policy bindings on the project hosting the Pub/Sub and Cloud Functions resources

These commands add the project-level IAM bindings that allow the execution of the subsequent steps by the `MEMBER` user (yourself or another designated user).

    # for creating the Pub/Sub topic and managing IAM permissions on the Pub/Sub topic
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="${MEMBER}" --role="roles/pubsub.admin"
    
    # for creating the asset feed
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="${MEMBER}" --role="roles/serviceusage.serviceUsageConsumer"
    
    # for creating the Cloud Function
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="${MEMBER}" --role="roles/cloudfunctions.developer"

    # for deploying the Cloud Function package
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="${MEMBER}" --role="roles/storage.objectCreator"

### Create the Pub/Sub topic

**Note**: If the steps in this section are to be done by a different person due to separation of duties, make sure that the `PROJECT_ID`, `PROJECT_NUMBER`, and 
`ORGANIZATION_ID` variables are set, as described in the preliminary procedures of this tutorial.

1.  Give a name for the Pub/Sub topic:

        TOPIC_NAME="asset-changes"

1.  Create the Pub/Sub topic:

        gcloud pubsub topics create "${TOPIC_NAME}" --project ${PROJECT_ID}

### Allow the Cloud Asset Inventory built-in service account to publish to the Pub/Sub topic

    gcloud beta services identity create --service=cloudasset.googleapis.com --project=${PROJECT_ID}

    gcloud pubsub topics add-iam-policy-binding "${TOPIC_NAME}" --member "serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-cloudasset.iam.gserviceaccount.com" --role roles/pubsub.publisher --project ${PROJECT_ID}

### Create an asset feed for the organization or folder

1.  Specify the four asset types to monitor:

        ASSET_TYPES="compute.googleapis.com/Instance,container.googleapis.com/Cluster,sqladmin.googleapis.com/Instance,storage.googleapis.com/Bucket"

    For a complete list of asset types that you can monitor, see [Supported asset types](https://cloud.google.com/asset-inventory/docs/supported-asset-types). 

1.  Create the feed.

    -   For the entire organization:

            gcloud asset feeds create "feed-resources-${ORGANIZATION_ID}" --organization="${ORGANIZATION_ID}" --content-type=resource --asset-types="${ASSET_TYPES}" --pubsub-topic="projects/${PROJECT_ID}/topics/${TOPIC_NAME}" --billing-project ${PROJECT_ID}

    -   For a folder:

            gcloud asset feeds create "feed-resources-${FOLDER_ID}" --folder="${FOLDER_ID}" --content-type=resource --asset-types="${ASSET_TYPES}" --pubsub-topic="projects/${PROJECT_ID}/topics/${TOPIC_NAME}" --billing-project ${PROJECT_ID}

1.  Confirm the feed creation.

    -   For the entire organization:

            gcloud asset feeds list --organization ${ORGANIZATION_ID} --format="flattened(feeds[].name)" --billing-project ${PROJECT_ID}
          
    -   For a folder:
    
            gcloud asset feeds list --folder ${FOLDER_ID} --format="flattened(feeds[].name)" --billing-project ${PROJECT_ID}

### Deploy the Cloud Function that processes the Cloud Asset Inventory real-time notifications

The [GitHub repository for this tutorial](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/cloud-asset-inventory-auto-label-resources/cloud-function-auto-resource-labeler/)
includes the complete working source code of the Cloud Function for the tutorial, which you can use as a reference as you customize it for your use case.

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the directory containing the Cloud Functions code:

        cd community/tutorials/cloud-asset-inventory-auto-label-resources/cloud-function-auto-resource-labeler

1.  Confirm that you still have the correct variables for the deployment:

        echo PROJECT_ID=${PROJECT_ID}
        echo GCF_SERVICE_ACCOUNT="${GCF_SERVICE_ACCOUNT}"
        echo TOPIC_NAME=${TOPIC_NAME}

1.  Deploy the function:

        gcloud functions deploy auto_resource_labeler --runtime python38 --trigger-topic "${TOPIC_NAME}" --service-account="${GCF_SERVICE_ACCOUNT}" --project ${PROJECT_ID} --retry

## Test the labeling triggered by Cloud Asset Inventory real-time notifications

Now you can test the creation of the resources under your organization (or folder) to observe the labeling in action.

It may take a few minutes for the labels to be effective.

* Compute Engine VM instances are labeled when transitioning into the `PROVISIONING` state.
* GKE clusters are labeled when transitioning into the `RUNNING` state.
* Cloud Storage buckets are labeled when coming from `priorAssetState=DOES_NOT_EXIST`.
* Cloud SQL instances are labeled when transitioning into the `RUNNABLE` state.

## Limitations and known issues

Notifications are only sent upon changes on the resource or policy metadata of the resource. Any existing resources (such as existing VM instances) that are
already deployed are not acted upon by this solution. You can perform a separate exercise to have the same actions on those existing resources.

GKE Autopilot Clusters generate Compute Engine instance notifications that can't be processed by the Cloud Function. This results in 404 errors when trying to
retrieve the existing labels. The current sample code handles by exiting gracefully when encountering any 404 errors.

## Cleaning up

You can revert changes made throughout the tutorial.

### Delete the feed

1.  Confirm the feed ID.

    -   For an organization:
    
            gcloud asset feeds list --organization ${ORGANIZATION_ID} --format="flattened(feeds[].name)" 
          
    -   For a folder:

            gcloud asset feeds list --folder ${FOLDER_ID} --format="flattened(feeds[].name)"

    The feed ID is the portion of the feed name after `.*/feeds/${FEED_ID}`.

1.  Set the right feed for the variables:

        FEED_ID=feed-resources-

    Be aware of any existing feeds in your organization that you may not want to interfere with.

1.  Delete the feed.

    -   For an organization:
    
            gcloud asset feeds delete ${FEED_ID} --organization ${ORGANIZATION_ID}
         
    -   For a folder:

            gcloud asset feeds delete ${FEED_ID} --folder ${FOLDER_ID}

### Delete the project

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project hosting the Pub/Sub and Cloud
Functions resources.

Deleting a project has the following consequences:

* If you used an existing project, you will also delete any other work that you have done in the project.
* You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the
  project instead.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

### Delete other resources

Finally, you can delete any other resources (such as Compute Engine VM instances) that you created for testing the labeling.

## What's next

* For more information, see [Monitoring asset changes](https://cloud.google.com/asset-inventory/docs/monitoring-asset-changes).
