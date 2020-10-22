---
title: Cloud TPU with Shared VPC
description: Learn how to use Cloud TPU with Shared VPC.
author: bernieongewe
tags: Cloud TPU Shared VPC XPN
date_published: 2020-10-26
---

This tutorial is an adaptation of the [Cloud TPU quickstart](https://cloud.google.com/tpu/docs/quickstart).

As with the original quickstart, this tutorial introduces you to using Cloud TPU to run [MNIST](https://developers.google.com/machine-learning/glossary/#MNIST),
a canonical dataset of hand-written digits that is often used to test new machine-learning approaches.

This adaptation is intended for users deploying under common networking constraints. The intent is to familiarize the audience with the workflow for using AI
Platform Notebooks to train models using Cloud TPU in a [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc) environment with 
[VPC Service Controls](https://cloud.google.com/vpc-service-controls). 

For a more detailed exploration of Cloud TPU, work through the [colabs](https://cloud.google.com/tpu/docs/colabs) and
[tutorials](https://cloud.google.com/tpu/docs/tutorials).

## Motivation and updates

* The `ctpu up` command referenced in [Cloud TPU quickstart](https://cloud.google.com/tpu/docs/quickstart) doesn't allow you to create a TPU in subnet shared from a host project. Instead we discuss some common production network considerations and use `gcloud beta compute tpus create` referenced in [Connecting TPUs with Shared VPC Networks](https://cloud.google.com/tpu/docs/shared-vpc-networks) to prepare the TPU
* This document also encourages the reader to use [AI Platform Notebooks](https://cloud.google.com/ai-platform/notebooks/docs/introduction) to launch the training job
* We also  briefly discuss  VPC-SC changes needed to access the `gs://tfds-data/` storage bucket from within a service perimeter

## Before you begin

Before starting this tutorial, check that your Google Cloud project is correctly set up. For more information, see [Set up an account and a Cloud TPU project](https://cloud.google.com/tpu/docs/setup-gcp-account).

This tutorial uses billable components of Google Cloud, including:

* Compute Engine
* Cloud TPU
* Cloud Storage


## Networking Requirements

### Shared VPC requirements

**NOTE: If you are using this document, this section will likely already be completed by your organization's GCP admin and provided you with access to your assigned Shared network**

1. Configure the `gcloud` with your GCP project.
1. Get familiar with [Shared VPC concepts](https://cloud.google.com/vpc/docs/shared-vpc#concepts_and_terminology).
1. [Enable a host project](https://cloud.google.com/vpc/docs/provisioning-shared-vpc#enable-shared-vpc-host) that contains one or more [Shared VPC networks](https://cloud.google.com/vpc/docs/shared-vpc#shared_vpc_networks). This must be done by a [Shared VPC admin](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc).
1. [Attach one or more service projects](https://cloud.google.com/vpc/docs/provisioning-shared-vpc#create-shared) to your Shared VPC network. This must be done by a [Shared VPC admin](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc).
1. Create a [VPC network](https://cloud.google.com/vpc/docs/vpc) in the host project. This is the network in which the TPU will be created


### VPC Service Control Requirements

The training instance requires access to the  `gs://tfds-data/` public bucket. If the test network is within a service perimeter, the your organization's admin should implement rules that allows access to this public bucket.

Errors such as the one below when training the model indicate that the egress requirement has not been met;

~~~
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
~~~


### Pricing

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.


## Set up project and storage bucket

This section provides information on setting up Cloud Storage storage and a Compute Engine VM.
Important: Set up your Compute Engine VM, your Cloud TPU node and your Cloud Storage bucket in the same region/zone to reduce network latency and network costs.

**Important:** Set up your Compute Engine VM, your Cloud TPU node and your Cloud Storage bucket in the same region/zone to reduce network latency and network costs.

1. Open a [Cloud Shell](https://console.cloud.google.com/?cloudshell=true&_ga=2.188548904.1482537891.1600707660-917451211.1600110531) window

1. Create a variable for your project's ID:

~~~
export PROJECT_ID=<project-id>
~~~

3.  Configure `gcloud` command-line tool to use the project where you want to create Cloud TPU.

~~~
gcloud config set project $PROJECT_ID
~~~

4. Create a Cloud Storage bucket using the following command:

**Note:** In the following command, replace bucket-name with the name you want to assign to your bucket.

~~~
gsutil mb -p ${PROJECT_ID} -c standard -l us-central1 -b on gs://<bucket-name>
~~~

This Cloud Storage bucket stores the data you use to train your model and the training results.


## Set up VPC Peering

Review [Connecting TPUs with Shared VPC Networks](https://cloud.google.com/tpu/docs/shared-vpc-networks)

### Configure Private Service Access

[Private Services Access](https://cloud.google.com/vpc/docs/private-access-options#service-networking) is used to create a [VPC peering](https://cloud.google.com/vpc/docs/using-vpc-peering) between your network and the Cloud TPU service network. Before you use TPUs with Shared VPCs, you need to [establish a private service access connection for the network](https://cloud.google.com/vpc/docs/configure-private-services-access).

Get the project ID for your Shared VPC host project, and then configure the gcloud command with your project ID as shown below:

~~~
 gcloud config set project <your-network-host-project-id>
~~~

You can get the project ID from the [Google Cloud console](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects).

Enable the Service Networking API using the following gcloud command.

~~~
gcloud services enable servicenetworking.googleapis.com
~~~

You can also enable the [Service Networking API](https://console.cloud.google.com/apis/library/servicenetworking.googleapis.com?q=servicenetworking&_ga=2.83749014.1482537891.1600707660-917451211.1600110531) from the Google Cloud Console.

Allocate a reserved address range for use by Service Networking. The prefix-length needs to be 24 or less. For example:

~~~
     gcloud compute addresses create SN-RANGE-1 --global\
    --addresses=10.110.0.0 \
    --prefix-length=16 \
    --purpose=VPC_PEERING \
    --network=<your-host-network>
~~~

Establish a private service access connection.

~~~
  gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --ranges=SN-RANGE-1 --network=<your-host-network>
~~~

Check if a Private Services Access connection has been established for the network. If it's already established, you can start using TPUs with the Shared VPC.

Verify Private Services Access
Check whether a Private Services Access connection has been established for your network by running following command:

~~~
gcloud services vpc-peerings list --network=<network-name>
~~~


## Create TPUs

**NOTE:** The TPU and notebook Tensorflow version must be aligned. This tutorial uses version 2.3 for both


* You can create Cloud TPUs through the gcloud CLI. The command below creates a TPU called `tpu-quickstart`
~~~
gcloud beta compute tpus create tpu-quickstart --zone <zone> --network <host-network> --use-service-networking --version 2.3
~~~

* You need to set use-service-networking to true so you can create Cloud TPUs that can connect to Shared VPC networks.
* **NOTE:If you are using Shared VPC networks, the network field MUST include the host project ID or host project number and the network name following the pattern** `projects/my-host-project-id/global/networks/my-network`
* For information about what GCP zones support Cloud TPUs, see [available zones](https://cloud.google.com/tpu/docs/regions).

## Get information about a TPU
You can get the details of a TPU node through TPU API requests:

~~~
gcloud compute tpus describe tpu-quickstart --zone <zone>
~~~

The response body contains information about an instance of a TPU Node, including the cidrBlock.

### List TPUs
You can get a list of Cloud TPUs through TPU API requests:

~~~
gcloud compute tpus list tpu-quickstart --zone <zone>
~~~


## Create an AI Platform Notebooks instance with custom properties

1. Go to the [AI Platform Notebooks page](https://console.cloud.google.com/ai-platform/notebooks/instances?_ga=2.120530696.1482537891.1600707660-917451211.1600110531) in the Google Cloud Console.

1. Click **New Instance**, and then select **Customize instance**.

1. On the New notebook instance page, provide the following information for your new instance:
 - **Instance name** - provide a name for your new instance.
 - **Region** - select the same region as the Cloud TPU previously created. 
 - **Zone** - Select the same zone as the Cloud TPU previously created.
 - Environment - select **Tensorflow Enterprise 2.3**.
 - **Machine type** - select the number of CPUs and amount of RAM for your new instance. AI Platform Notebooks provides monthly cost estimates for each machine type that you select.

1. Expand the Networking section.
 - Select **Networks shared with me**.
 - On the Network menu, select the shared network that you want previously configured.
 - On the Subnetwork menu, select the subnetwork previously configured.
 - To grant access to a specific service account, click the **Access to JupyterLab** menu, and select **Other service account**. Then fill out the Service account field. Learn more about service accounts.
**NOTE: This service account must also be granted a `Storage Object User` role on the `gs://<bucket-name>` training bucket your previously created**

Click **Create**.

AI Platform Notebooks creates a new instance based on your specified properties. An **Open JupyterLab** link becomes active when it's ready to use.


## Start Training Job

1. Click the **Open JupyterLab** link when it becomes available then click the **Terminal** tile in the notebooks' launcher dialog

1. From a terminal session, install the [TensorFlow Model Optimization Toolkit](https://www.tensorflow.org/model_optimization)
~~~
pip3 install tensorflow_model_optimization
~~~

1. `cd` to  into the example code directory
~~~
cd ~/tutorials/models/official/vision/image_classification
~~~

1. Update `PYTHONPATH`
~~~
export PYTHONPATH="$PYTHONPATH:/home/jupyter/tutorials/models"
~~~

1. set up environment variables, replacing <bucket-name> with your storage bucket.
~~~
export STORAGE_BUCKET=gs://<bucket-name>
export TPU_NAME=tpu-quickstart
export MODEL_DIR=$STORAGE_BUCKET/mnist
DATA_DIR=$STORAGE_BUCKET/data
export PYTHONPATH="$PYTHONPATH:/usr/share/models"
~~~

1. Train the model
~~~
python3 mnist_main.py \
  --tpu=$TPU_NAME \
  --model_dir=$MODEL_DIR \
  --data_dir=$DATA_DIR \
  --train_epochs=10 \
  --distribution_strategy=tpu \
  --download
~~~


## Clean Up

1. Visit the [AI Platform Notebooks](https://console.cloud.google.com/ai-platform/notebooks/instances?_ga=2.120530696.1482537891.1600707660-917451211.1600110531) dialog to delete the Notebook instance
2. Delete the Cloud TPU
~~~
gcloud beta compute tpus delete tpu-quickstart --zone <zone>
~~~
