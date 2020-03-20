---
title: Running a Cloud MQTT bridge in Kubernetes
description: Bridge MQTT messages between a cluster and Cloud IoT Core with Mosquitto.
author: ptone
tags: Kubernetes, iot, Internet of Things, cloud iot core
date_published: 2019-07-12
---

Preston Holmes | Solution Architect | Google

## Introduction

This tutorial demonstrates how to deploy the [Mosquitto](https://mosquitto.org/) MQTT broker to
[Kubernetes](https://kubernetes.io/) using the broker's bridge feature to map a specific [MQTT](http://mqtt.org/)
topic namespace to [Cloud IoT Core](https://cloud.google.com/iot-core/).

## Setup

### Clone the tutorial repository

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community/tutorials/kube-mqtt

### Prerequisite: Kubernetes cluster

This tutorial assumes that you have a running Kubernetes cluster. This can be a cluster created through
[Minikube](https://kubernetes.io/docs/tutorials/hello-minikube/),
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/), or other means. For the tutorial, you can also use 
Kubernetes Engine clusters; however, the context of this solution is based on non-cloud clusters in Edge environments.

You will also need a recent `kubectl` command-line interface (version 1.14 or greater) with
[kustomize integration](https://kubernetes.io/blog/2019/03/25/kubernetes-1-14-release-announcement/). If you have an older 
version of `kubectl`, install version 1.14 or greater from the
[Kubernetes website](https://kubernetes.io/docs/tasks/tools/install-kubectl/). Ensure that `kubectl` is configured to 
communicate with your cluster.

### Setting up the cloud environment

1.  Create a project in the [GCP Console](https://console.cloud.google.com).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

In this tutorial, you can run commands from [Cloud Shell](https://cloud.google.com/shell) or locally. If you choose to run 
commands locally, you must install the [Cloud SDK](https://cloud.google.com/sdk).

#### Set environment variables

In this tutorial, you may open multiple shell tabs or sessions. Set these environment variables in each session, replacing 
`[PROJECT-ID]` with your project ID:

    # The project should already be set in Cloud Shell.
    gcloud config set project [PROJECT-ID]
	
    export PROJECT=$(gcloud config list project --format "value(core.project)" )
    export REGION=us-central1
    export REGISTRY=gadgets
    export DEVICE=bridge
		
#### Enable APIs
	
    gcloud services enable \
    cloudiot.googleapis.com \
    container.googleapis.com \
    containerregistry.googleapis.com \
    pubsub.googleapis.com \
    cloudbuild.googleapis.com
		
## Build the bridge manager container

For Mosquitto, you will use the default published container from Docker. Note that you will need another container in the
deployment that manages the credentials that allow the bridge to connect to Google Cloud Platform (GCP).

    cd refresher-container
    gcloud builds submit --tag gcr.io/$PROJECT/refresher .

## Create cloud resources

### Create the device keys

The following commands create a public/private keypair; only transmit the public key, and store the private key on the 
device.

    cd ../bridge
    openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem
    openssl ec -in ec_private.pem -pubout -out ec_public.pem

### Create IoT Core resources

The following commands create the required IoT Core resources:

    gcloud pubsub topics create device-events
    gcloud pubsub subscriptions create debug --topic device-events
    
    gcloud iot registries create $REGISTRY \
    --region=$REGION \
    --event-notification-config topic=device-events
    
    gcloud iot devices create $DEVICE \
    --region $REGION \
    --registry $REGISTRY \
    --public-key path=ec_public.pem,type=es256-pem

This creates an IoT Core device called `bridge` that you will use to authenticate the bridge to IoT Core.

The Cloud Pud/Sub topics are used to verify that data is bridged to the cloud correctly.

## Deploy the bridge to Kubernetes

### Update project-specific settings

Get the specific address for the bridge manager container:

    gcloud container images describe gcr.io/$PROJECT/refresher --format="value(image_summary.fully_qualified_digest)"

In the repository file `bridge/project-image.yaml`, add the output from the previous command as `image`.

If running the Kubernetes cluster outside the GCP project, make the images public:

    gsutil iam ch allUsers:objectViewer gs://artifacts.$PROJECT.appspot.com

Note that this will make the container registry for the project public.

In production environments, you would provision the cluster with the required
[image pull secrets](http://docs.heptio.com/content/private-registries/pr-gcr.html).

Edit the `PROJECT_ID` value in `device-config.yaml`.

### Deploy

You use the built-in version of [kustomize](https://kustomize.io/) in recent `kubectl` versions to deploy the
solution to Kubernetes.

Make sure that you are in the base directory for this tutorial: `community/tutorials/kube-mqtt`. More about the deployment 
is explained in the following section. For now, deploy the workload with this command:
	
    kubectl apply -k bridge/

## Understanding the bridge deployment

This section explains some crucial parts of the deployment.
	
### Use of kustomize

The layout of this project uses a base folder that contains default resources, including YAML files for a deployment with
two containers and a service, as well as a kustomize-generated configmap.

The bridge folder in the repository acts as an overlay, which does the following:

 - merges the device private key file into a configmap defined in the base
 - patches a container image with a project-specific address
 - adds project-specific environment variables

By keeping these more variable parts in an overlay, the base can be managed centrally and shared among several different 
variants. For example, when following this tutorial, you only need to change the project ID in the `device-config.yaml` 
file, but you might use different registries or device ID values if you changed those variables.

### Using a pod combining a third-party image with a project custom image

The deployment defined in the base defines a pod that combines a stock Mosquitto image with a custom manager sidecar. This 
pod demonstrates some interesting Kubernetes capabilities:

- The different containers in the pod use a shared volume where the manager writes a configuration file that is read by the
  Mosquitto container.
- The pod has `shareProcessNamespace` enabled so that the refreshing the managing container can restart a process in the 
  stock container. This is done because the `remote_password` configuration value is an expiring JWT token, according
  to the authentication design of IoT Core.

### The bridge configuration

In the template for the Mosquitto configuration is a section that contains directives on how to bridge the MQTT topics.  
For details, see the [Mosquitto documentation](https://mosquitto.org/man/mosquitto-conf-5.html). 

The topic routing takes this form:

    topic pattern [[[ out | in | both ] qos-level] local-prefix remote-prefix]

In the configuration template, a prefix of `gcp/` is used for any topic connected to IoT Core.

For `out` topics—those going from the bridge to the cloud—different routes are used for exact versus pattern matches:

    topic "" out 1 gcp/events /devices/CONFIG_DEVICE_ID/events
    topic "" out 1 gcp/state /devices/CONFIG_DEVICE_ID/state
    topic # out 1 gcp/events/ /devices/CONFIG_DEVICE_ID/events/

A similar duplication is used for cloud topics that the bridge subscribes to:

    topic "" in 1 gcp/config /devices/CONFIG_DEVICE_ID/config
    topic "" in 1 gcp/commands /devices/CONFIG_DEVICE_ID/commands
    topic # in 1 gcp/commands/ /devices/CONFIG_DEVICE_ID/commands/

## Test the bridge

### Check that the bridge deployed

    kubectl wait --for=condition=Ready pod -l "app=iot-core-bridge"
    kubectl logs -f -l "app=iot-core-bridge" -c mosquitto

You may choose to keep the log open in a dedicated terminal, or close it after verifying that there are no errors.

### Build the image for a cluster-based MQTT client

This tutorial assumes that the broker will be used inside the context of the cluster, as well as potentially by external 
local devices. For demonstration purposes, you will use a simple MQTT command-line client.

    cd client
    gcloud builds submit --tag gcr.io/$PROJECT/mqtt-client .

### Run a couple of instances of the client

You will start multiple terminal window sessions for these next steps. Remember to set the environment variables 
in each session, as described in the "Set environment variables" section above. In Cloud Shell, you can open a new terminal 
tab by clicking the **Add Cloud Shell session** button (labeled with the **+** icon).

Run the first client, client-a:

    kubectl run client-a --rm -i --tty --image gcr.io/$PROJECT/mqtt-client --generator=run-pod/v1 -- /bin/sh
	
In another shell session, run the second client, client-b:

    kubectl run client-b --rm -i --tty --image gcr.io/$PROJECT/mqtt-client --generator=run-pod/v1 -- /bin/sh

### Local broker communication

In this pattern, clients can communicate on unbridged broker topics in a conventional way.

![local communication diagram](https://storage.googleapis.com/gcp-community/tutorials/kube-mqtt/local.png)

Note that the client can use the cluster local service name (`mqtt-bridge`) as the hostname.

In client-b, subscribe to a local-only topic:

    sub -h mqtt-bridge -t "test/topic" -v

In client-a, publish to this topic:

    pub -h mqtt-bridge -m hello -t test/topic -d

You should see the message relayed by the broker.

### Send bridged telemetry to the Cloud

![cloud telemetry diagram](https://storage.googleapis.com/gcp-community/tutorials/kube-mqtt/telemetry.png)

In client-a, publish to the bridged event topic:

    pub -h mqtt-bridge -m hello -t gcp/events -d
	
Verify that the bridged message was published to the cloud in another terminal. (Reminder: Set the environment variables
in this terminal as described in the setup instructions.)

    gcloud pubsub subscriptions pull debug --auto-ack --limit=100 
	
### Send commands from the cloud to cluster-local clients

![Commands from cloud diagram](https://storage.googleapis.com/gcp-community/tutorials/kube-mqtt/command.png)

In both client windows, subscribe to bridged IoT commands topic:

    sub -h mqtt-bridge -t "gcp/commands/#" -v

Publish a command with the IoT Core API:

    gcloud iot devices commands send --region=us-central1 \
    --registry=$REGISTRY \
    --device=$DEVICE \
    --command-data=hey \
    --subfolder=yoyo

You should see the command arrive at both clients.

### Connecting a local MQTT client

If instead you want to connect a client outside the cluster, you can forward the MQTT port:

    kubectl port-forward svc/mqtt-bridge 1883:1883

Depending on the Kubernetes setup, you may choose to expose the MQTT service externally.

## Cleanup and next steps

Use `kustomize` to delete the resources in Kubernetes:

    kubectl delete -k bridge/
	
To delete the cloud resources, delete the tutorial cloud project.

Some areas this pattern can be extended:

 - Integrate the bridge with the IoT Core [gateway](https://cloud.google.com/iot/docs/how-tos/gateways/) feature.
 - Add a form of device-local authentication with a custom Mosquitto authentication layer.
 - Add local Transport Layer Security (TLS) to the MQTT broker.
