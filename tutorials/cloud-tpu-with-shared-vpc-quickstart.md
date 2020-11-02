---
title: Cloud TPUs with Shared VPC
description: Learn how to use Cloud TPUs with Shared VPC.
author: bernieongewe
tags: Cloud TPU, Shared VPC, XPN
date_published: 2020-10-30
---

Bernie Ongewe | Technical Solutions Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>


This tutorial is an adaptation of the [Cloud TPU quickstart](https://cloud.google.com/tpu/docs/quickstart).

As with the original quickstart, this tutorial introduces you to using Cloud TPUs to run [MNIST](https://developers.google.com/machine-learning/glossary/#MNIST),
a canonical dataset of hand-written digits that is often used to test new machine-learning approaches.

This adaptation is intended for users deploying under common networking constraints. This tutorial demonstrates the workflow for using AI
Platform Notebooks to train models using Cloud TPUs in a [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc) environment with 
[VPC Service Controls](https://cloud.google.com/vpc-service-controls). 

For a more detailed exploration of Cloud TPUs, work through the [colabs](https://cloud.google.com/tpu/docs/colabs) and
[tutorials](https://cloud.google.com/tpu/docs/tutorials).

## Differences from the original Cloud TPU quickstart

* The `ctpu up` command used in the original [Cloud TPU quickstart](https://cloud.google.com/tpu/docs/quickstart) doesn't allow you to create a TPU in a subnet 
  shared from a host project. This tutorial discusses some common production network considerations and uses the `gcloud beta compute tpus create` command to 
  prepare the TPU. For more information, see [Connecting TPUs with Shared VPC Networks](https://cloud.google.com/tpu/docs/shared-vpc-networks).

* This tutorial uses [AI Platform Notebooks](https://cloud.google.com/ai-platform/notebooks/docs/introduction) to launch the training job.

* This tutorial discusses VPC-SC changes needed to access the `gs://tfds-data/` storage bucket from within a service perimeter.

## Before you begin

Before starting this tutorial, check that your Google Cloud project is set up according to the instructions in
[Set up an account and a Cloud TPU project](https://cloud.google.com/tpu/docs/setup-gcp-account).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* Compute Engine
* Cloud TPU
* Cloud Storage

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Networking requirements

### Shared VPC requirements

**Note**: The setup in this section might already have been completed by your organization's Google Cloud administrator who provided you with access to an 
assigned Shared network.

1.  Become familiar with [Shared VPC concepts](https://cloud.google.com/vpc/docs/shared-vpc#concepts_and_terminology).

1.  [Enable a host project](https://cloud.google.com/vpc/docs/provisioning-shared-vpc#enable-shared-vpc-host) that contains one or more
    [Shared VPC networks](https://cloud.google.com/vpc/docs/shared-vpc#shared_vpc_networks).
    
    This must be done by a [Shared VPC administrator](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc).
    
1.  [Attach one or more service projects](https://cloud.google.com/vpc/docs/provisioning-shared-vpc#create-shared) to your Shared VPC network.

    This must be done by a [Shared VPC administrator](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc).
    
1.  Create a [VPC network](https://cloud.google.com/vpc/docs/vpc) in the host project.

    This is the network in which the TPU will be created.

### VPC Service Control requirements

The training instance requires access to the `gs://tfds-data/` public Cloud Storage bucket. If the test network is within a service perimeter, your 
organization's administrator should implement rules that allow access to this public bucket.

Errors such as the one below when training the model indicate that the egress requirement has not been met:

    tensorflow.python.framework.errors_impl.PermissionDeniedError: Error executing an HTTP request: HTTP response code 403 with body '{
      "error": {
        "code": 403,
        "message": "Request is prohibited by organization's policy. vpcServiceControlsUniqueIdentifier: 8e042d53afb67532",
        "errors": [
          {
            "message": "Request is prohibited by organization's policy. vpcServiceControlsUniqueIdentifier: 8e042d53afb67532",
            "domain": "global",
            "reason": "vpcServiceControls"
          }
        ]    
      }
    }
    '
             when reading metadata of gs://tfds-data/dataset_info/mnist/3.0.1

## Set up the project and Cloud Storage bucket

This section provides information on setting up Cloud Storage and a Compute Engine virtual machine (VM).

**Important**: Set up your Compute Engine VM, your Cloud TPU node, and your Cloud Storage bucket in the same region and zone to reduce network latency and 
network costs.

1.  Open [Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

1.  Create a variable for your project ID:

        export PROJECT_ID=[YOUR_PROJECT_ID]

1.  Configure the `gcloud` command-line tool to use the project where you want to create Cloud TPUs:

        gcloud config set project $PROJECT_ID

1.  Create a Cloud Storage bucket:

        gsutil mb -p ${PROJECT_ID} -c standard -l us-central1 -b on gs://[YOUR_BUCKET_NAME]

    Replace `[YOUR_BUCKET_NAME]` with the name you want to assign to your bucket.

    This Cloud Storage bucket stores the data you use to train your model and the training results.

## Set up VPC Peering

Review [Connecting TPUs with Shared VPC networks](https://cloud.google.com/tpu/docs/shared-vpc-networks).

### Configure private service access

[Private services access](https://cloud.google.com/vpc/docs/private-access-options#service-networking) is used to create a 
[VPC peering](https://cloud.google.com/vpc/docs/using-vpc-peering) between your network and the Cloud TPU service network. Before you use TPUs with Shared VPCs,
you need to [establish a private service access connection for the network](https://cloud.google.com/vpc/docs/configure-private-services-access).

1.  Get the project ID for your Shared VPC host project, and then configure `gcloud` with your project ID:

        gcloud config set project [YOUR_NETWORK_HOST_PROJECT_ID]

    You can get the project ID from the [Cloud Console](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects).

1.  Enable the Service Networking API:

        gcloud services enable servicenetworking.googleapis.com

    You can also enable the [Service Networking API](https://console.cloud.google.com/apis/library/servicenetworking.googleapis.com) with the Cloud Console.

1.  Allocate a reserved address range for use by Service Networking:

        gcloud compute addresses create SN-RANGE-1 --global\
        --addresses=10.110.0.0 \
        --prefix-length=16 \
        --purpose=VPC_PEERING \
        --network=<your-host-network>
        
    The `prefix-length` must be 24 or less.

1.  Establish a private service access connection:

        gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --ranges=SN-RANGE-1 --network=[YOUR_HOST_NETWORK]

1.  Check whether a private services access connection has been established for the network:

        gcloud services vpc-peerings list --network=[YOUR_NETWORK_NAME]
        
    If a private services access connection has been established for the network, then you can start using TPUs with the Shared VPC.

## Create TPUs

The TPU and notebook TensorFlow versions must be aligned. This tutorial uses version 2.3 for both.

Create a TPU:

    gcloud beta compute tpus create tpu-quickstart --zone [YOUR_ZONE] --network [YOUR_HOST_NETWORK] --use-service-networking --version 2.3
       
The command above creates a TPU called `tpu-quickstart`.

The `use-service-networking` flag enables the creation of TPUs that can connect to Shared VPC networks.

If you are using Shared VPC networks, the network field _must_ include the host project ID or host project number and the network name following this pattern: 

`projects/my-host-project-id/global/networks/my-network`

For information about what Google Cloud zones Cloud TPUs are available in, see [TPU types and zones](https://cloud.google.com/tpu/docs/regions).

## Get information about a TPU

You can get the details of a TPU node through TPU API requests:

    gcloud compute tpus describe tpu-quickstart --zone [YOUR_ZONE]

The response body contains information about an instance of a TPU node, including the CIDR block.

You can get a list of TPUs through TPU API requests:

    gcloud compute tpus list tpu-quickstart --zone [YOUR_ZONE]

## Create an AI Platform Notebooks instance with custom properties

1.  Go to the [AI Platform Notebooks page](https://console.cloud.google.com/ai-platform/notebooks/instances) in the Cloud Console.

1.  Click **New instance**, and then select **Customize instance**.

1.  On the **New notebook instance** page, provide the following information for your new instance:
    - **Instance name**: Provide a name for your new instance.
    - **Region**: Select the same region as the Cloud TPU previously created. 
    - **Zone**: Select the same zone as the Cloud TPU previously created.
    - **Environment**: Select **Tensorflow Enterprise 2.3**.
    - **Machine type**: Select the number of CPUs and amount of RAM for your new instance. AI Platform Notebooks provides monthly cost estimates for each 
      machine type that you select.

1.  Expand the **Networking** section.
1.  Select **Networks shared with me**.
1.  In the **Network** menu, select the shared network that you previously configured.
1.  In the Subnetwork menu, select the subnetwork previously configured.
1.  To grant access to a specific service account, click the **Access to JupyterLab** menu, select **Other service account**, and then fill out the 
    **Service account** field.
 
    This service account must also be granted a `Storage Object User` role on the `gs://[BUCKET_NAME]` training bucket you previously created.

1.  Click **Create**.

AI Platform Notebooks creates a new instance based on your specified properties. An **Open JupyterLab** link becomes active when it's ready to use.

## Start the training job

1.  Click the **Open JupyterLab** link when it becomes available, and then click the **Terminal** tile in the notebooks launcher dialog.

1.  From a terminal session, install the [TensorFlow Model Optimization Toolkit](https://www.tensorflow.org/model_optimization):

        pip3 install tensorflow_model_optimization

1.  Change directory to the example code directory:

        cd ~/tutorials/models/official/vision/image_classification

1.  Update `PYTHONPATH:`

        export PYTHONPATH="$PYTHONPATH:/home/jupyter/tutorials/models"

1.  Set environment variables, replacing `[BUCKET_NAME]` with your Cloud Storage bucket.

        export STORAGE_BUCKET=gs://[BUCKET_NAME]
        export TPU_NAME=tpu-quickstart
        export MODEL_DIR=$STORAGE_BUCKET/mnist
        DATA_DIR=$STORAGE_BUCKET/data
        export PYTHONPATH="$PYTHONPATH:/usr/share/models"

1.  Train the model:

        python3 mnist_main.py \
          --tpu=$TPU_NAME \
          --model_dir=$MODEL_DIR \
          --data_dir=$DATA_DIR \
          --train_epochs=10 \
          --distribution_strategy=tpu \
          --download

## Clean up

1.  Go to the [AI Platform Notebooks instances page](https://console.cloud.google.com/ai-platform/notebooks/instances) to delete the notebook instance.
1.  Delete the Cloud TPU

        gcloud beta compute tpus delete tpu-quickstart --zone [YOUR_ZONE]
