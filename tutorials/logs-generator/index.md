---
title: Generating large volumes of logs with Python on GKE to Cloud Pub/Sub 
description: Learn to generate large volume of logs from GKE to Cloud Pub/Sub using Locust in Python.
author: arieljassan
tags: GKE, Cloud Pub/Sub, Locust, Python
date_published: 2020-04-05
---


This tutorial describes how to create a GKE (Google Kubernetes Engine) cluster, deploy a Python application that generates logs using the "Faker" library, and simulates load with the Python library "Locust". By the end of the tutorial you will also be able to monitor the cluster utilization from the Kubernetes Engine dashboardin Stackdriver and the arrival of the messages to Pub/Sub in the Cloud Console.

This tutorial assumes you already own a project in GCP and that you have the gcloud SDK already installed in your environment. To install gcloud SDK, see [Installing Google Cloud SDK](https://cloud.google.com/sdk/install)

## Objectives

- Create a GKE cluster and a Cloud Pub/Sub topic.
- Create Docker containers for the application logic and for the Locust master and workers.
- Create Service Accounts with permissions to deploy Docker containers from Cloud Build in GKE and to publish to Cloud Pub/Sub.
- Deploy the containers to GKE.
- Monitor GKE cluster an Cloud Pub/Sub topic utilization.

## Costs

You may incur costs in GKE, Compute Engine, Cloud Build, Cloud Storage, and Networking. Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimation based on your projected usage.

## Reference architecture

The following diagram shows the architecture components of the solution.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/architecture.png)

1. The Kubernetes deployment 'locust-master' is responsible for coordinating the Locust threads as defined by the end user.
1. The Kubernetes deployment 'locust-worker' creates http requests to trigger the generation of logs by the 'webapp' containers.
1. The Kubernetes deployment 'webapp' is responsible for generating dictionary-like logs, which are published to a Pub/Sub topic.
1. Cloud Pub/Sub is the sink of the logs generation process. The Pub/Sub topic captures the logs sent the 'webapp' containers. 
1. Stackdriver Monitoring samples the usage of the GKE cluster and summarizes the information in the Kubernetes Dashboard in Stackdriver.
1. The landing page of the Pub/Sub API shows the number of API requests and operations per second for the topic.

In addition to the components above, there are two Kubernetes services deployed as part of the solution:
- The load balancer service 'locust-master' handles the requests from the end user.
- The Cluster IP service 'webapp-cip' servers as the interface between the Locust testing environment and the web application.

## Before you begin
Clone the Google Cloud Community repository and cd into the directory.
    
        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community/tutorials/logs-generator    

## Enable relevant APIs
Run the following gcloud commands in the console to enable APIs for GKE, Google Container Registry, Cloud Pub/Sub, Stackdriver, and Cloud Build. It may take a few minutes to enable them. 
    
        gcloud services enable \
            container.googleapis.com \
            containerregistry.googleapis.com \
            pubsub.googleapis.com \
            stackdriver.googleapis.com \
            cloudbuild.googleapis.com 
    
## Set environment variables
Run the following comands in the console to set environment variables. Make sure to replace the values for PROJECT_ID, TOPIC_NAME, and CLUSTER_NAME.
    
        REGION=us-central1
        ZONE=$REGION-c
        PROJECT_ID=[YOUR_PROJECT_ID]
        TOPIC_NAME=[YOUR_PUBSUB_TOPIC_NAME]
        SUBSCRIPTION_NAME=[YOUR_PUBSUB_SUBSCRIPTION_NAME]
        CLUSTER_NAME=[YOUR_GKE_CLUSTER_NAME]
        gcloud config set compute/zone $ZONE
        gcloud config set project $PROJECT_ID
	
## Create a Service Account with permissions to access Container Registry
Run the commands below to create a Service Account with permissions to read from Cloud Storage buckets, where Container Registry stores container images. This Service Account will be assigned to GKE nodes at the time of the creation of the cluster.

        # Create Service Account.
        SA_NAME=gke-node-service-account
        gcloud iam service-accounts create $SA_NAME \
            --display-name "user generated service account for GKE nodes"
        
        # Add to the Service Account permissions to read from Cloud Storage.
        SA_FULL_NAME=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member serviceAccount:$SA_FULL_NAME \
            --role "roles/storage.objectViewer" 
        
## Create a GKE Cluster 
Run the following command to create a GKE cluster with 5 nodes of the machine type n1-standard-4 with binding to the Service Account generated it the previous step. The command enables autoscaling up to 10 nodes and Horizontal Pod Autoscaling.

        gcloud beta container clusters create \
            --project=$PROJECT_ID \
            --region=$REGION \
            --node-locations=$ZONE \
            --enable-ip-alias \
            --image-type="COS" \
            --num-nodes=5 \
            --machine-type=n1-standard-4 \
            --enable-stackdriver-kubernetes \
            --metadata disable-legacy-endpoints=false \
            --service-account "$SA_FULL_NAME"  \
            --enable-autoscaling  --min-nodes=0 --max-nodes=10 \
            --addons "HorizontalPodAutoscaling"  \
             $CLUSTER_NAME

## Create a Cloud Pub/Sub topic and subscription
Run the following commands to create a topic and a subscription with the names set in the environment variables:
    
        gcloud pubsub topics create $TOPIC_NAME
        gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
          --topic=$TOPIC_NAME 

## Edit in the web application the project id and Pub/Sub topic name
Run the following commands to set PROJECT_ID and TOPIC_NAME in the web application file.
    
        sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" webapp-docker-image/webapp/app.py
        sed -i -e "s/YOUR_TOPIC_NAME/$TOPIC_NAME/" webapp-docker-image/webapp/app.py

## Build the Locust and web application containers
Run the following commands to create Docker container images in Cloud Build based on the code in the directories `locust-docker-image` and `webapp-docker-image`:
     
        gcloud builds submit --tag gcr.io/$PROJECT_ID/locust-tasks:latest locust-docker-image
        gcloud builds submit --tag gcr.io/$PROJECT_ID/webapp:latest webapp-docker-image
    
## Edit in the Kubernetes files the project id
Run the commands below to set the values of PROJECT_ID in the Kubernetes deployment files:
    
        sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/locust-master-controller.yaml
        sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/locust-worker-controller.yaml 
        sed -i -e "s/YOUR_PROJECT_ID/$PROJECT_ID/" kubernetes-config/webapp-controller.yaml

## Create a Service Account to be deployed in the Docker containers 
Run the commands below to create a Service Account and upload the Service Account key as a Kubernetes secret.

        # Create Service Account.
        SA_NAME=publisher-service-account
        gcloud iam service-accounts create $SA_NAME \
            --display-name "service account for publishing to Pub/Sub"
        
        # Add to the Service Account permissions to publish to Pub/Sub. 
        SA_FULL_NAME=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member serviceAccount:$SA_FULL_NAME \
            --role "roles/pubsub.publisher" 
    
        # Create a Service Account key and a Kubernetes Secret.
        CRED_FILE=/tmp/creds/$SA_FULL_NAME
        gcloud iam service-accounts keys create $CRED_FILE \
            --iam-account=$SA_FULL_NAME --project=$PROJECT_ID
        kubectl create secret generic pubsub-key --from-file=key.json=$CRED_FILE
    
        # Delete the Service Account key.
        rm $CRED_FILE


## Create deployments and sevices
Run the following commands to create the deployments for the web application, Locust master and workers, and the services:
    
        kubectl apply -f kubernetes-config/locust-master-controller.yaml
        kubectl apply -f kubernetes-config/locust-worker-controller.yaml
        kubectl apply -f kubernetes-config/locust-master-service.yaml
        kubectl apply -f kubernetes-config/webapp-controller.yaml
        kubectl apply -f kubernetes-config/webapp-cip.yaml
    
    
## Do port-forward to get connect from port 8888
Run the command below to do port-forwarding of the port 8089 to port 8888. If you are on Cloud Shell, click on 'web preview' button, and click on 'Preview on port 8888'. If you don't see port 8888, click on 'Change port' and find port '8888'.
![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/cloud_shell_port_forwarding.png)

        kubectl port-forward -n default "$(kubectl get pods -l app=locust-master \
            -o jsonpath='{.items..metadata.name}')" 8888:8089
    

## Run a test from the Locust UI from your browser
In the web browser showing the Locust interface, enter the value 100 in 'Number of users to simulate' and 100 in 'Hatch rate'. Keep the value in the field 'Host' as is and click on 'Start swarming'.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/locust_ui_1.png)

Once the test started, you can find some statistics in Locust as below.
![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/locust_ui_2.png)

## Monitor GKE Cluster Utilization
You can check the utilization of you GKE cluster in the Kubenetes Monitoring dashboard following this path:
Menu > Monitoring > Dashboards > Kubernetes Engine

Or clicking on [this link ot the Kubernetes Engine dashboard](https://pantheon.corp.google.com/monitoring/dashboards/resourceList/kubernetes)

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/kubernetes_stackdriver.png)

## Monitor Pub/Sub API requests
Validate that the number of requests from the Locust UI are similar to those in Pub/Sub API in Stackdriver. Follow the following path:
Menu > Monitoring > Dashboards > Cloud Pub/Sub
or clicking on [in this link](https://pantheon.corp.google.com/monitoring/dashboards/resourceList/pubsub_topic) and clicking on the topic.

![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/pubsub_stackdriver.png)

## Extensions to this lab

### Resize your deployments and GKE cluster
One the most important benefits of GKE and containerized applications is that you can scale as needed. You can use this tutorial to generate a larger number of logs per second to simulate high loads. To ahieve that, you can adjust the number of pods of the deployments with the following commands:

        kubectl scale deployment locust-worker --replicas 10
        kubectl scale deployment webapp --replicas 10

Make sure to keep always the deployment of `locust-master` to one replica. 

You can also resize your GKE cluster using the command below. 
    
        gcloud container clusters resize $CLUSTER_NAME --node-pool default \
            --num-nodes [NUMBER_OF_NODES]

### Try out Cloud Run
You can also use Cloud Run to run the 'webapp' containers to allow for automatic resizing the number of containers. You read about Cloud Run [here](https://cloud.google.com/run).


## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud Platform account for the resources used in this tutorial is to delete the project you created.

To delete the project, follow the steps below:
1. In the Cloud Platform Console, [go to the Projects page](https://console.cloud.google.com/iam-admin/projects).

1. In the project list, select the project you want to delete and click **Delete project**.
![N|Solid](https://storage.googleapis.com/gcp-community/tutorials/logs-generator/images/img_delete_project.png) 
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.
 
## What's next

- Try out other Google Cloud Platform features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials). 
