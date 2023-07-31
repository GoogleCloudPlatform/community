---
title: Generate a large volume of logs with Python on GKE to Pub/Sub
description: Learn to generate a large volume of logs from GKE to Pub/Sub using Locust in Python.
author: arieljassan
tags: GKE, Locust, Python
date_published: 2020-06-08
---

Ariel Jassan | Data Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

One of the challenges of building scalable data-intensive applications is the ability to create tests that are 
representative enough to simulate the scale of the system in production. To overcome this challenge, you need tools to 
generate custom test data at a large scale. This tutorial makes that process easier with scripts and architecture to 
simulate logs published to Pub/Sub. Pub/Sub allows ingestion of high volumes of data in real time, which you can then use in
data sinks and other systems. 

This tutorial describes how to create a GKE (Google Kubernetes Engine) cluster, deploy a Python application that generates 
logs using the Faker library, and simulate load with the Python library Locust. 

By the end of the tutorial, you'll be able to monitor the cluster utilization from the Kubernetes Engine dashboard in 
Cloud Monitoring and the arrival of the messages to Pub/Sub in the Cloud Console.

This tutorial assumes that you already have a project in Google Cloud and that you have the Cloud SDK installed in your
environment. To install the Cloud SDK, see [Installing the Cloud SDK](https://cloud.google.com/sdk/install).

## Objectives

- Create a GKE cluster and a Pub/Sub topic.
- Create Docker containers for the application logic and for the Locust master and workers.
- Create service accounts with permissions to deploy Docker containers from Cloud Build on GKE and to publish to Pub/Sub.
- Deploy the containers to GKE.
- Monitor GKE cluster and Pub/Sub topic utilization.

## Costs

You may incur costs in GKE, Compute Engine, Cloud Build, Cloud Storage, and networking. Use the
[Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimation based on your projected 
usage.

## Reference architecture

The following diagram shows the architecture components of the solution.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/architecture.png)

1. The Kubernetes deployment `locust-master` is responsible for coordinating the Locust threads as defined by the end user.
1. The Kubernetes deployment `locust-worker` creates HTTP requests to trigger the generation of logs by the `webapp`
   containers.
1. The Kubernetes deployment `webapp` is responsible for generating dictionary-like logs, which are published to a Pub/Sub 
   topic.
1. Cloud Pub/Sub is the sink of the log generation process. The Pub/Sub topic captures the logs sent by the `webapp`
   containers. 
1. Cloud Monitoring samples the usage of the GKE cluster and summarizes the information in the Kubernetes Dashboard in 
   Cloud Monitoring.
1. The landing page of the Pub/Sub API shows the number of API requests and operations per second for the topic.

In addition to the components above, there are two Kubernetes services deployed as part of the solution:

- The load balancer service `locust-master` handles the requests from the end user.
- The cluster IP service `webapp-cip` serves as the interface between the Locust testing environment and the web 
  application.

## Before you begin

Clone the Google Cloud Community repository and go to the directory:
    
    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community/tutorials/generate-logs-scale    

## Enable relevant APIs

Run the following commands in the Cloud Console to enable APIs for GKE, Container Registry, Pub/Sub, Cloud Monitoring, and 
Cloud Build. 
    
        gcloud services enable \
            container.googleapis.com \
            containerregistry.googleapis.com \
            pubsub.googleapis.com \
            stackdriver.googleapis.com \
            cloudbuild.googleapis.com 

It may take a few minutes for the APIs to be enabled.

## Set environment variables

Run the following commands in the Cloud Console to set environment variables. Replace the values for `PROJECT_ID`, 
`TOPIC_NAME`, `SUBSCRIPTION_NAME`, and `CLUSTER_NAME`.
    
    REGION=us-central1
    ZONE=$REGION-c
    PROJECT_ID=[YOUR_PROJECT_ID]
    TOPIC_NAME=[YOUR_PUBSUB_TOPIC_NAME]
    SUBSCRIPTION_NAME=[YOUR_PUBSUB_SUBSCRIPTION_NAME]
    CLUSTER_NAME=[YOUR_GKE_CLUSTER_NAME]
    gcloud config set compute/zone $ZONE
    gcloud config set project $PROJECT_ID
	
## Create a service account with permissions to access Container Registry

Run the following commands to create a service account with permissions to read from Cloud Storage buckets, where Container 
Registry stores container images.

    # Create service account.
    SA_NAME=gke-node-service-account
    gcloud iam service-accounts create $SA_NAME \
        --display-name "user generated service account for GKE nodes"
        
    # Add to the service account permissions to read from Cloud Storage.
    SA_FULL_NAME=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member serviceAccount:$SA_FULL_NAME \
        --role "roles/storage.objectViewer" 
        
## Create a GKE cluster

Run the following command to create a GKE cluster with 5 nodes of the machine type `n1-standard-4` with binding to the
service account. The command enables autoscaling up to 10 nodes and Horizontal Pod Autoscaling.

    gcloud beta container clusters create \
        --project=$PROJECT_ID \
        --region=$REGION \
        --node-locations=$ZONE \
        --enable-ip-alias \
        --num-nodes=5 \
        --machine-type=n1-standard-4 \
        --enable-stackdriver-kubernetes \
        --metadata disable-legacy-endpoints=false \
        --service-account "$SA_FULL_NAME"  \
        --enable-autoscaling  --min-nodes=0 --max-nodes=10 \
        --addons "HorizontalPodAutoscaling"  \
         $CLUSTER_NAME

## Create a Pub/Sub topic and subscription

Run the following commands to create a topic and a subscription with the names set in the environment variables:
    
    gcloud pubsub topics create $TOPIC_NAME
    gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
      --topic=$TOPIC_NAME 

## Edit the project ID and Pub/Sub topic name in the web application

Run the following commands to set `PROJECT_ID` and `TOPIC_NAME` in the web application file.
    
    sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" webapp-docker-image/webapp/app.py
    sed -i -e "s/YOUR_TOPIC_NAME/$TOPIC_NAME/" webapp-docker-image/webapp/app.py

## Build the Locust and web application containers

Run the following commands to create Docker container images in Cloud Build based on the code in the directories
`locust-docker-image` and `webapp-docker-image`:
     
    gcloud builds submit --tag gcr.io/$PROJECT_ID/locust-tasks:latest locust-docker-image
    gcloud builds submit --tag gcr.io/$PROJECT_ID/webapp:latest webapp-docker-image
    
## Edit the project ID in the Kubernetes files 

Run the commands below to set `PROJECT_ID` in the Kubernetes deployment files:
    
    sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/locust-master-controller.yaml
    sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/locust-worker-controller.yaml 
    sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/webapp-controller.yaml

## Create a service account to be deployed in the Docker containers

Run the commands below to create a service account and upload the service account key as a Kubernetes secret.

    # Create service account.
    SA_NAME=publisher-service-account
    gcloud iam service-accounts create $SA_NAME \
        --display-name "service account for publishing to Pub/Sub"
        
    # Add to the service account permissions to publish to Pub/Sub. 
    SA_FULL_NAME=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member serviceAccount:$SA_FULL_NAME \
        --role "roles/pubsub.publisher" 
    
    # Create a service account key and a Kubernetes Secret.
    CRED_FILE=/tmp/creds/$SA_FULL_NAME
    gcloud iam service-accounts keys create $CRED_FILE \
        --iam-account=$SA_FULL_NAME --project=$PROJECT_ID
    kubectl create secret generic pubsub-key --from-file=key.json=$CRED_FILE
    
    # Delete the service account key.
    rm $CRED_FILE

## Create deployments and sevices

Run the following commands to create the deployments for the web application, Locust master and workers, and the services:
    
    kubectl apply -f kubernetes-config/locust-master-controller.yaml
    kubectl apply -f kubernetes-config/locust-worker-controller.yaml
    kubectl apply -f kubernetes-config/locust-master-service.yaml
    kubectl apply -f kubernetes-config/webapp-controller.yaml
    kubectl apply -f kubernetes-config/webapp-cip.yaml
    
## Use port forwarding to connect from port 8888

Run the following command to forward port 8089 to port 8888:

    kubectl port-forward -n default "$(kubectl get pods -l app=locust-master \
        -o jsonpath='{.items..metadata.name}')" 8888:8089
    
In Cloud Shell, click **Web preview**, and then click **Preview on port 8888**. If you don't see port 8888, click
**Change port** and find port 8888.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/cloud_shell_port_forwarding.png)

## Run a test from the Locust web interface

In a web browser showing the Locust interface, enter the value `100` in **Number of users to simulate** and `100` in 
**Hatch rate**. Click **Start swarming**.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/locust_ui_1.png)

After the test starts, you can see statistics in Locust, as shown in the following screenshot:

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/locust_ui_2.png)

## Monitor GKE cluster utilization

To check the utilization of you GKE cluster in the Kubernetes Monitoring dashboard, go to 
**Menu > Monitoring > Dashboards > Kubernetes Engine**.

[Go to the Kubernetes Engine dashboard.](https://console.cloud.google.com/monitoring/dashboards/resourceList/kubernetes)

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/kubernetes_stackdriver.png)

## Monitor Pub/Sub API requests

Validate that the number of requests from the Locust interface are similar to those in Pub/Sub API in Cloud Monitoring. 

To see the monitoring information about the Pub/Sub topic go to **Menu > Monitoring > Dashboards > Pub/Sub** and click the 
topic name.

[Go to the **Monitoring workspaces** page.](http://console.cloud.google.com/monitoring/dashboards/resourceList/pubsub_topic).

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/pubsub_stackdriver.png)

## Extensions to this tutorial

### Resize your deployments and GKE cluster

One the most important benefits of GKE and containerized applications is that they can scale up and down as needed. To 
simulate high loads, use the following commands to generate a larger number of logs per second by adjusting the number of 
pods of the deployments:

    kubectl scale deployment locust-worker --replicas 10
    kubectl scale deployment webapp --replicas 10

Keep the deployment of `locust-master` to one replica. 

You can also resize your GKE cluster with this command: 
    
    gcloud container clusters resize $CLUSTER_NAME --node-pool default \
        --num-nodes [NUMBER_OF_NODES]

### Try out Cloud Run

You can also use [Cloud Run](https://cloud.google.com/run) to run the `webapp` containers to allow for automatic resizing of
the number of containers.

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete
the project you created.

To delete the project, do the following:

1.  In the Cloud Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1.  In the project list, select the project you want to delete and click **Delete project**.

    ![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/generate-logs-scale/img_delete_project.png) 
    
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.
 
## What's next

- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials). 
