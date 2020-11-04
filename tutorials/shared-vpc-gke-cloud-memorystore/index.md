---
title: Connecting GKE workloads to services in different Google Cloud projects using Shared VPC
description: Learn how to configure Shared VPC to connect your applications deployed in GKE to resources managed in different Google Cloud projects.
author: soeirosantos
tags: networking, gcp, compute engine, vm, cloud memorystore, google kubernetes engine, private service access
date_published: 2020-11-05
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you configure Shared VPC and connect two service projects. One service project contains a GKE cluster, and the other project contains managed
services that are accessible from applications deployed to the GKE cluster.

The following image provides an overview:

![](https://storage.googleapis.com/gcp-community/tutorials/shared-vpc-gke-cloud-memorystore/gke_shared_vpc.png)

## Before you begin

* For this tutorial you'll need three [Google Cloud projects](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects) to configure the Shared VPC and the service projects. To make cleanup easiest, create new projects for this tutorial, so you can delete the projects when you're done. For details, see the "Cleaning up" section at the end of the tutorial.

    * Create three [GCP Projects](https://console.cloud.google.com/cloud-resource-manager)
    * [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your projects

* Make sure you have the [required administrative roles](https://cloud.google.com/vpc/docs/shared-vpc#iam_roles_required_for_shared_vpc) to configure Shared VPC. The required IAM roles are: 

    * **Organization Admin** (`resourcemanager.organizationAdmin`)
    * **Shared VPC Admin** (`compute.xpnAdmin and resourcemanager.projectIamAdmin`)
    * **Service Project Admin** (`compute.networkUser`)

    Check the [Shared VPC IAM section](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc) for more details about the purpose of these roles.

* For the commands in this tutorial you'll use the `gcloud` command-line tool. To install the Google Cloud SDK, which includes the `gcloud` tool, follow 
[these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Cloud Memorystore](https://cloud.google.com/memorystore)
*   [Compute Engine](https://cloud.google.com/compute)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Configure the Shared VPC

We are going to refer to the host project using the environment variable `SHARED_VPC_PROJECT` and to the two service projects using the `SERVICE_PROJECT` and `GKE_CLUSTER_PROJECT` environment variables.

1. Let's start defining the environment variables for our projects and GCP region.

    ```bash
    export SHARED_VPC_PROJECT=your-project-name-1
    export GKE_CLUSTER_PROJECT=your-project-name-2
    export SERVICE_PROJECT=your-project-name-3
    export GCP_REGION=us-central1
    ```

1. Enable the `container.googleapis.com` Service API for the host project and the service project used for the GKE cluster, and the `compute.googleapis.com` API for the other service project.

    ```bash
    gcloud services enable container.googleapis.com --project $SHARED_VPC_PROJECT

    gcloud services enable container.googleapis.com --project $GKE_CLUSTER_PROJECT

    gcloud services enable compute.googleapis.com --project $SERVICE_PROJECT
    ```

1. Create a VPC network in the `SHARED_VPC_PROJECT` project and subnets to be used by the service projects. We will also add secondary ranges for the pods and services that will be used by the GKE cluster located in the `GKE_CLUSTER_PROJECT` project.

    Note that the region and ranges used here are arbitrary. You can use what works best for you.

    ```bash
    gcloud compute networks create shared-net \
        --subnet-mode custom \
        --project $SHARED_VPC_PROJECT

    gcloud compute networks subnets create k8s-subnet \
        --network shared-net \
        --range 10.0.4.0/22 \
        --region $GCP_REGION \
        --secondary-range k8s-services=10.0.32.0/20,k8s-pods=10.4.0.0/14 \
        --project $SHARED_VPC_PROJECT

    gcloud compute networks subnets create service-subnet \
        --network shared-net \
        --range 172.16.4.0/22 \
        --region $GCP_REGION \
        --project $SHARED_VPC_PROJECT
    ```

1. Now enable the Shared VPC and associate the service projects.

    ```bash
    gcloud compute shared-vpc enable $SHARED_VPC_PROJECT

    gcloud compute shared-vpc associated-projects add $GKE_CLUSTER_PROJECT \
        --host-project $SHARED_VPC_PROJECT

    gcloud compute shared-vpc associated-projects add $SERVICE_PROJECT \
        --host-project $SHARED_VPC_PROJECT
    ```

1. Verify the service projects configuration

    ```bash
    gcloud compute shared-vpc get-host-project $GKE_CLUSTER_PROJECT

    gcloud compute shared-vpc get-host-project $SERVICE_PROJECT
    ```

## Authorize the Service Projects in the Shared VPC

Now we are going to configure an IAM member from a service project to access only specific subnets in the host project. It provides a granular way to define `Service Project Admins` by granting them the `compute.networkUser` role for only the subnets they really need access to.

1. Let's review the members of the service projects and get the name of the service accounts we'll use in the next steps.

    ```bash
    gcloud projects get-iam-policy $GKE_CLUSTER_PROJECT

    bindings:
    - members:
      - serviceAccount:service-48977974920@compute-system.iam.gserviceaccount.com
      role: roles/compute.serviceAgent
    - members:
      - serviceAccount:service-48977974920@container-engine-robot.iam.gserviceaccount.com
      role: roles/container.serviceAgent
    - members:
      - serviceAccount:48977974920-compute@developer.gserviceaccount.com
      - serviceAccount:48977974920@cloudservices.gserviceaccount.com
      - serviceAccount:service-48977974920@containerregistry.iam.gserviceaccount.com
      role: roles/editor

    gcloud projects get-iam-policy $SERVICE_PROJECT

    bindings:
    - members:
      - serviceAccount:service-507534582923@compute-system.iam.gserviceaccount.com
      role: roles/compute.serviceAgent
    - members:
      - serviceAccount:507534582923-compute@developer.gserviceaccount.com
      - serviceAccount:507534582923@cloudservices.gserviceaccount.com
      role: roles/editor
    ```

1. Let's also review the IAM policies for the subnets in the `SHARED_VPC_PROJECT` and retrieve the `etag` values. We will use them to update the policies.

    ```bash
    gcloud compute networks subnets get-iam-policy k8s-subnet \
        --region $GCP_REGION \
        --project $SHARED_VPC_PROJECT
    etag: ACAB

    gcloud compute networks subnets get-iam-policy service-subnet \
        --region $GCP_REGION \
        --project $SHARED_VPC_PROJECT
    etag: ACAB
    ```

1. Create the following file with the service accounts from the `GKE_CLUSTER_PROJECT` project.

    ```yaml
    # k8s-subnet-policy.yaml
    bindings:
    - members:
      - serviceAccount:48977974920@cloudservices.gserviceaccount.com
      - serviceAccount:service-48977974920@container-engine-robot.iam.gserviceaccount.com
      role: roles/compute.networkUser
    etag: ACAB
    ```

1. Update the policy to bind the members to the `k8s-subnet` subnet.

    ```bash
    gcloud compute networks subnets set-iam-policy k8s-subnet \
        k8s-subnet-policy.yaml \
        --region $GCP_REGION \
        --project $SHARED_VPC_PROJECT
    ```

1. Create the following file with the service accounts from the `SERVICE_PROJECT` project.

    ```yaml
    # service-subnet-policy.yaml
    bindings:
    - members:
      - serviceAccount:507534582923@cloudservices.gserviceaccount.com
      role: roles/compute.networkUser
    etag: ACAB
    ```

1. Update the policy to bind the members to the `service-subnet` subnet.

    ```bash
    gcloud compute networks subnets set-iam-policy service-subnet \
        service-subnet-policy.yaml \
        --region $GCP_REGION \
        --project $SHARED_VPC_PROJECT
    ```

1. Finally add the GKE service account from the `GKE_CLUSTER_PROJECT` project to the host project with the `roles/container.hostServiceAgentUser` role.

    ```bash
    gcloud projects add-iam-policy-binding $SHARED_VPC_PROJECT \
      --member serviceAccount:service-48977974920@container-engine-robot.iam.gserviceaccount.com \
      --role roles/container.hostServiceAgentUser
    ```

1. Let's check the GKE cluster usable subnets and validate the configuration we have done.

    ```bash
    gcloud container subnets list-usable \
        --network-project $SHARED_VPC_PROJECT \
        --project $GKE_CLUSTER_PROJECT
    ```

## Connecting to a Cloud Memorystore instance

Our Shared VPC is configured and the service projects are authorized to manage their subnets in the Shared VPC. Now we are ready to spin up some resources and play around to validate our network connectivity.

1. Create a GKE Cluster.

    ```bash
    gcloud container clusters create gke-cluster \
        --zone=$GCP_REGION-a \
        --enable-ip-alias \
        --network projects/$SHARED_VPC_PROJECT/global/networks/shared-net \
        --subnetwork projects/$SHARED_VPC_PROJECT/regions/$GCP_REGION/subnetworks/k8s-subnet \
        --cluster-secondary-range-name k8s-pods \
        --services-secondary-range-name k8s-services \
        --project $GKE_CLUSTER_PROJECT
    ```

1. We want to create a Cloud Memorystore instance in the `SERVICE_PROJECT` that should be reachable from the GKE cluster. But before moving forward we need to establish a [private service access](https://cloud.google.com/vpc/docs/configure-private-services-access#shared_vpc_scenario) connection in the `SHARED_VPC_PROJECT`. 

    Check the [Cloud Memorystore docs](https://cloud.google.com/memorystore/docs/redis/creating-managing-instances#creating_a_redis_instance_on_a_shared_vpc_network_from_a_service_project) for more details about these steps.

    ```bash
    gcloud services enable servicenetworking.googleapis.com --project $SHARED_VPC_PROJECT

    gcloud beta compute addresses create \
    memorystore-pvt-svc --global --prefix-length=24 \
    --description "memorystore private service range" --network shared-net \
    --purpose vpc_peering --project $SHARED_VPC_PROJECT

    gcloud services vpc-peerings connect \
    --service servicenetworking.googleapis.com --ranges memorystore-pvt-svc \
    --network shared-net --project $SHARED_VPC_PROJECT
    ```

1. Enable the necessary APIs and create the Cloud Memorystore instance.

    ```bash
    gcloud services enable redis.googleapis.com --project $SERVICE_PROJECT
    gcloud services enable servicenetworking.googleapis.com --project $SERVICE_PROJECT

    gcloud redis instances create my-redis --size 5 --region $GCP_REGION \
    --network=projects/$SHARED_VPC_PROJECT/global/networks/shared-net \
    --connect-mode=private-service-access --project $SERVICE_PROJECT
    ```

1. Verify that the instance was created in the Shared VPC and retrieve the instance IP to use in the next step.

    ```bash
    gcloud redis instances list --region $GCP_REGION --project $SERVICE_PROJECT
    ```

    Let's check if we can access this Redis instance from within the cluster.

    ```bash
    gcloud container clusters get-credentials gke-cluster --zone $GCP_REGION-a --project $GKE_CLUSTER_PROJECT

    kubectl run -it --rm --image gcr.io/google_containers/redis:v1 r2 --restart=Never -- sh

    redis-cli -h 10.192.163.3 info

    redis-benchmark -c 100 -n 100000 -d 1024 -r 100000 -t PING,SET,GET,INCR,LPUSH,RPUSH,LPOP,RPOP,SADD,SPOP,MSET -h 10.192.163.3
    ```

## Connecting to a Compute Engine instance

1. Now let's see if we can access a service running inside a VM instance. Start creating a VM:

    ```bash
    gcloud compute instances create my-instance --zone $GCP_REGION-a \
    --subnet projects/$SHARED_VPC_PROJECT/regions/$GCP_REGION/subnetworks/service-subnet \
    --project $SERVICE_PROJECT

    ```

1. We can try to ssh (heads up, this won't work).

    ```bash
    gcloud compute ssh my-instance \
        --zone $GCP_REGION-a \
        --project $SERVICE_PROJECT
    ```

1. You'll notice that we can't access the VM using ssh. We need to add a firewall rule in the Shared VPC to enable ssh access.

    ```bash
    gcloud compute firewall-rules create shared-net-ssh \
        --network shared-net \
        --direction INGRESS \
        --allow tcp:22,icmp \
        --project $SHARED_VPC_PROJECT
    ```

    Try to connect again with the same `gcloud compute ssh` command above. It should work.

1. From inside the `my-instance` VM run the following command and exit.

    ```bash
    sudo apt install -y nginx
    ```

1. Retrieve the internal IP for the instance just created. You should have only one instance in this project.

    ```bash
    gcloud compute instances list --project $SERVICE_PROJECT
    ```

1. Let's try to access this VM from the GKE cluster (it should hang and fail).

    ```
    kubectl run -it --rm --image busybox bb8 --restart=Never

    wget -qO- 172.16.4.3 # vm internal IP
    ```

    Note that the wget command hangs and wouldn't return.

1. To enable ingress access from the GKE cluster to the Compute Engine instance created in the `service-subnet` subnet add the following firewall rule for the k8s pod, service and nodes ranges.

    ```bash
    gcloud compute firewall-rules create k8s-access \
        --network shared-net \
        --allow tcp,udp \
        --direction INGRESS \
        --source-ranges 10.0.4.0/22,10.4.0.0/14,10.0.32.0/20
        --project $SHARED_VPC_PROJECT
    ```

    Run the previous step again and you should see the `Welcome to nginx!` page response.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, using the Google Cloud Console, perform the following actions:

1. On the `GKE_CLUSTER_PROJECT` delete the [GKE Cluster](https://console.cloud.google.com/kubernetes/list).
1. On the `SERVICE_PROJECT` delete the [Compute Engine instance](https://console.cloud.google.com/compute/instances).
1. Detach the two service projects on the [Shared VPC page](https://console.cloud.google.com/networking/xpn/details) of the `SHARED_VPC_PROJECT` project.
1. Disable the Shared VPC on the [Shared VPC page](https://console.cloud.google.com/networking/xpn/details) of the `SHARED_VPC_PROJECT` project.
1. Shut-down the three projects using the [Cloud Resource Manager](https://console.cloud.google.com/cloud-resource-manager).

## What next

- Learn more about [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc).
- Learn more about how to [Configure a GKE Cluster with Shared VPC](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-shared-vpc).
- Learn more about [Cloud Memorystore networking](https://cloud.google.com/memorystore/docs/redis/networking).
- Learn more about [Private Service Access](https://cloud.google.com/vpc/docs/configure-private-services-access).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
