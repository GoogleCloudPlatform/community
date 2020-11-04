---
title: Connecting GKE workloads to services in different Google Cloud projects using Shared VPC
description: Learn how to configure Shared VPC to connect your applications deployed in GKE to resources managed in different Google Cloud projects.
author: soeirosantos
tags: networking, gcp, compute engine, vm, cloud memorystore, google kubernetes engine, private service access
date_published: 2020-11-05
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you configure Shared VPC and connect two service projects. One service project contains a GKE cluster, and the other service project contains 
managed services that are accessible from applications deployed to the GKE cluster.

The following image provides an overview:

![](https://storage.googleapis.com/gcp-community/tutorials/shared-vpc-gke-cloud-memorystore/gke_shared_vpc.png)

## Before you begin

For this tutorial, you need three [Google Cloud projects](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects) to configure
the Shared VPC network and the service projects. To make cleanup easiest, create new projects for this tutorial, so you can delete the projects when you're done.
For details, see the "Cleaning up" section at the end of the tutorial.

1.  Create three [Google Cloud projects](https://console.cloud.google.com/cloud-resource-manager).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your projects.
1.  Make sure that you have the [required administrative roles](https://cloud.google.com/vpc/docs/shared-vpc#iam_roles_required_for_shared_vpc) to configure 
    Shared VPC: 

    * **Organization Admin**: `resourcemanager.organizationAdmin`
    * **Shared VPC Admin**: `compute.xpnAdmin` and `resourcemanager.projectIamAdmin`
    * **Service Project Admin**: `compute.networkUser`

    For more information about the purposes of these roles, see the
    [Shared VPC IAM documentation](https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc).

1.  For the commands in this tutorial, you use the `gcloud` command-line interface. To install the Cloud SDK, which includes the `gcloud` tool, follow
    [these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
*   [Memorystore](https://cloud.google.com/memorystore)
*   [Compute Engine](https://cloud.google.com/compute)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Configure the Shared VPC network

This tutorial refers to the host project using the environment variable `SHARED_VPC_PROJECT`, and to the two service projects using the `SERVICE_PROJECT` and 
`GKE_CLUSTER_PROJECT` environment variables.

1.  Define the environment variables for your projects and Google Cloud region:

        export SHARED_VPC_PROJECT=your-project-name-1
        export GKE_CLUSTER_PROJECT=your-project-name-2
        export SERVICE_PROJECT=your-project-name-3
        export GCP_REGION=us-central1

1.  Enable the `container.googleapis.com` service API for the host project and the service project used for the GKE cluster, and the `compute.googleapis.com` API
    for the other service project:

        gcloud services enable container.googleapis.com --project $SHARED_VPC_PROJECT

        gcloud services enable container.googleapis.com --project $GKE_CLUSTER_PROJECT

        gcloud services enable compute.googleapis.com --project $SERVICE_PROJECT

1.  Create a VPC network in the `SHARED_VPC_PROJECT` project and subnets to be used by the service projects:

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
    
    This also adds secondary ranges for the pods and services that are used by the GKE cluster in the `GKE_CLUSTER_PROJECT` project.

    The region and ranges used here are arbitrary. You can use what works best for you.

1.  Enable the Shared VPC network and associate the service projects:

        gcloud compute shared-vpc enable $SHARED_VPC_PROJECT

        gcloud compute shared-vpc associated-projects add $GKE_CLUSTER_PROJECT \
            --host-project $SHARED_VPC_PROJECT

        gcloud compute shared-vpc associated-projects add $SERVICE_PROJECT \
            --host-project $SHARED_VPC_PROJECT

1. Verify the service project configuration:

        gcloud compute shared-vpc get-host-project $GKE_CLUSTER_PROJECT

        gcloud compute shared-vpc get-host-project $SERVICE_PROJECT

## Authorize the service projects in the Shared VPC network

In this section, you configure an IAM member from a service project to access only specific subnets in the host project. This provides a granular way to define 
service project admins by granting them the `compute.networkUser` role for only the subnets that they really need access to.

1.  Review the members of the `GKE_CLUSTER_PROJECT` project and get the name of the service account that you'll use in later steps:

        gcloud projects get-iam-policy $GKE_CLUSTER_PROJECT
        
    The output should look something like this:

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
          
1.  Review the members of the `SERVICE_PROJECT` project and get the name of the service account that you'll use in later steps:
      
        gcloud projects get-iam-policy $SERVICE_PROJECT

    The output should look something like this:

        bindings:
        - members:
          - serviceAccount:service-507534582923@compute-system.iam.gserviceaccount.com
          role: roles/compute.serviceAgent
        - members:
          - serviceAccount:507534582923-compute@developer.gserviceaccount.com
          - serviceAccount:507534582923@cloudservices.gserviceaccount.com
          role: roles/editor

1.  Review the IAM policies for the subnets in the `SHARED_VPC_PROJECT` and retrieve the `etag` values. You use these values in a later step to update the 
    policies.

        gcloud compute networks subnets get-iam-policy k8s-subnet \
            --region $GCP_REGION \
            --project $SHARED_VPC_PROJECT
        etag: ACAB

        gcloud compute networks subnets get-iam-policy service-subnet \
            --region $GCP_REGION \
            --project $SHARED_VPC_PROJECT
        etag: ACAB

1.  Create a `k8s-subnet-policy.yaml` file with the service accounts from the `GKE_CLUSTER_PROJECT` project:

        # k8s-subnet-policy.yaml
        bindings:
        - members:
          - serviceAccount:48977974920@cloudservices.gserviceaccount.com
          - serviceAccount:service-48977974920@container-engine-robot.iam.gserviceaccount.com
          role: roles/compute.networkUser
        etag: ACAB

1.  Update the policy to bind the members to the `k8s-subnet` subnet:

        gcloud compute networks subnets set-iam-policy k8s-subnet \
            k8s-subnet-policy.yaml \
            --region $GCP_REGION \
            --project $SHARED_VPC_PROJECT

1. Create a `service-subnet-policy.yaml` file with the service accounts from the `SERVICE_PROJECT` project:

        # service-subnet-policy.yaml
        bindings:
        - members:
          - serviceAccount:507534582923@cloudservices.gserviceaccount.com
          role: roles/compute.networkUser
        etag: ACAB

1.  Update the policy to bind the members to the `service-subnet` subnet:

        gcloud compute networks subnets set-iam-policy service-subnet \
            service-subnet-policy.yaml \
            --region $GCP_REGION \
            --project $SHARED_VPC_PROJECT

1.  Add the GKE service account from the `GKE_CLUSTER_PROJECT` project to the host project with the `roles/container.hostServiceAgentUser` role:

        gcloud projects add-iam-policy-binding $SHARED_VPC_PROJECT \
          --member serviceAccount:service-48977974920@container-engine-robot.iam.gserviceaccount.com \
          --role roles/container.hostServiceAgentUser

1.  Check the GKE cluster usable subnets and validate the configuration that you have done:

        gcloud container subnets list-usable \
            --network-project $SHARED_VPC_PROJECT \
            --project $GKE_CLUSTER_PROJECT

Your Shared VPC network is configured and the service projects are authorized to manage their subnets in the Shared VPC network.

## Connect to a Memorystore instance

In this section, you start some resources and play around to validate your network connectivity.

1.  Create a GKE cluster:

        gcloud container clusters create gke-cluster \
            --zone=$GCP_REGION-a \
            --enable-ip-alias \
            --network projects/$SHARED_VPC_PROJECT/global/networks/shared-net \
            --subnetwork projects/$SHARED_VPC_PROJECT/regions/$GCP_REGION/subnetworks/k8s-subnet \
            --cluster-secondary-range-name k8s-pods \
            --services-secondary-range-name k8s-services \
            --project $GKE_CLUSTER_PROJECT

1.  Before you create a Memorystore instance in the `SERVICE_PROJECT` project that is reachable from the GKE cluster, you need to establish a
    [private service access](https://cloud.google.com/vpc/docs/configure-private-services-access#shared_vpc_scenario) connection in the `SHARED_VPC_PROJECT`
    project. 

    Check the
    [Memorystore documentation](https://cloud.google.com/memorystore/docs/redis/creating-managing-instances#creating_a_redis_instance_on_a_shared_vpc_network_from_a_service_project) for more details about these steps.

        gcloud services enable servicenetworking.googleapis.com --project $SHARED_VPC_PROJECT

        gcloud beta compute addresses create \
        memorystore-pvt-svc --global --prefix-length=24 \
        --description "memorystore private service range" --network shared-net \
        --purpose vpc_peering --project $SHARED_VPC_PROJECT

        gcloud services vpc-peerings connect \
        --service servicenetworking.googleapis.com --ranges memorystore-pvt-svc \
        --network shared-net --project $SHARED_VPC_PROJECT

1.  Enable the necessary APIs and create the Memorystore instance:

        gcloud services enable redis.googleapis.com --project $SERVICE_PROJECT
        gcloud services enable servicenetworking.googleapis.com --project $SERVICE_PROJECT

        gcloud redis instances create my-redis --size 5 --region $GCP_REGION \
        --network=projects/$SHARED_VPC_PROJECT/global/networks/shared-net \
        --connect-mode=private-service-access --project $SERVICE_PROJECT

1.  Verify that the instance was created in the Shared VPC network, and retrieve the instance IP to use in a later step:

        gcloud redis instances list --region $GCP_REGION --project $SERVICE_PROJECT

1.  Check whether you can access this Redis instance from within the cluster:

        gcloud container clusters get-credentials gke-cluster --zone $GCP_REGION-a --project $GKE_CLUSTER_PROJECT

        kubectl run -it --rm --image gcr.io/google_containers/redis:v1 r2 --restart=Never -- sh

        redis-cli -h 10.192.163.3 info

        redis-benchmark -c 100 -n 100000 -d 1024 -r 100000 -t PING,SET,GET,INCR,LPUSH,RPUSH,LPOP,RPOP,SADD,SPOP,MSET -h 10.192.163.3

## Connect to a Compute Engine instance

In this section, you access a service running inside a Compute Engine VM instance.

1.  Create a VM instance:

        gcloud compute instances create my-instance --zone $GCP_REGION-a \
        --subnet projects/$SHARED_VPC_PROJECT/regions/$GCP_REGION/subnetworks/service-subnet \
        --project $SERVICE_PROJECT

1.  Try to connect to the instance using SSH (which won't work yet):

        gcloud compute ssh my-instance \
            --zone $GCP_REGION-a \
            --project $SERVICE_PROJECT
            
    You can't access the VM instance with SSH yet. 

1.  Add a firewall rule in the Shared VPC network to enable SSH access:

        gcloud compute firewall-rules create shared-net-ssh \
            --network shared-net \
            --direction INGRESS \
            --allow tcp:22,icmp \
            --project $SHARED_VPC_PROJECT

1.  Try again to connect to the instance using SSH (which should work this time):

        gcloud compute ssh my-instance \
            --zone $GCP_REGION-a \
            --project $SERVICE_PROJECT
            
1.  From inside the `my-instance` VM instance, run the following command to install the Nginx server and exit:

        sudo apt install -y nginx

1.  Retrieve the internal IP address for the instance just created:

        gcloud compute instances list --project $SERVICE_PROJECT
        
    You should have only only instance in this project.

1. Try to access this VM from the GKE cluster:

        kubectl run -it --rm --image busybox bb8 --restart=Never

        wget -qO- 172.16.4.3 # vm internal IP

    The `wget` command should hang and not return.

1.  To enable ingress access from the GKE cluster to the Compute Engine instance created in the `service-subnet` subnet, add the following firewall rule for the 
    k8s pod, service, and nodes ranges.

        gcloud compute firewall-rules create k8s-access \
            --network shared-net \
            --allow tcp,udp \
            --direction INGRESS \
            --source-ranges 10.0.4.0/22,10.4.0.0/14,10.0.32.0/20
            --project $SHARED_VPC_PROJECT

1. Try again to access the VM from the GKE cluster:

        kubectl run -it --rm --image busybox bb8 --restart=Never

        wget -qO- 172.16.4.3 # vm internal IP
        
    This time, you should see the `Welcome to nginx!` page response.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, perform the following actions in the Cloud Console:

1. In the `GKE_CLUSTER_PROJECT` project, delete the [GKE cluster](https://console.cloud.google.com/kubernetes/list).
1. In the `SERVICE_PROJECT` project, delete the [Compute Engine instance](https://console.cloud.google.com/compute/instances).
1. Detach the two service projects on the [Shared VPC page](https://console.cloud.google.com/networking/xpn/details) of the Shared VPC project.
1. Disable the Shared VPC network on the [Shared VPC page](https://console.cloud.google.com/networking/xpn/details) of the Shared VPC project.
1. Shut down the three projects using the [Resource Manager](https://console.cloud.google.com/cloud-resource-manager).

## What next

- Learn more about [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc).
- Learn more about [how to configure a GKE cluster with Shared VPC](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-shared-vpc).
- Learn more about [Memorystore networking](https://cloud.google.com/memorystore/docs/redis/networking).
- Learn more about [private service access](https://cloud.google.com/vpc/docs/configure-private-services-access).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
