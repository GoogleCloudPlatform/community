---
title: Running a Cloud MQTT bridge in Kubernetes
description: Bridge MQTT messages between cluster and Cloud IoT Core with Mosquitto
author: ptone
tags: Kubernetes, iot, iot core
date_published: 2019-07-01
---

Preston Holmes | Solution Architect | Google

<!-- diagram sources: https://docs.google.com/presentation/d/1p2srfYUkqnXIKR4zGj099PIKOzz1RRi28eOcgIch1tc/edit#slide=id.p -->

## Introduction

This tutorial demonstrates how to deploy [Mosquitto](https://mosquitto.org/) in [Kubernetes](https://kubernetes.io/) using a bridge feature to map a specific [MQTT](http://mqtt.org/) topic namespace to Google Cloud IoT Core.

![architecture](image/architecture.png)

## Setup

#### TODO git clone ....

### Kubernetes Cluster

It is assumed you have have running Kubernetes cluster, with working `kubectl` command.

This can be via [Minikube](https://kubernetes.io/docs/tutorials/hello-minikube/), [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/), etc.

### Setting up the cloud environment

#### TODO Use Cloud Shell

	gcloud config set project <project-id>
	
	export PROJECT=$(gcloud config list project --format "value(core.project)" )
	export REGION=us-central1
	export REGISTRY=gadgets
	export DEVICE=bridge
	
	gcloud services enable \
	cloudiot.googleapis.com \
	container.googleapis.com \
	containerregistry.googleapis.com \
	pubsub.googleapis.com \
	cloudbuild.googleapis.com

## Build the bridge manager container

For Mosquitto we will use the default published container. But we need another container in the deployment which manages the credentials that allow the bridge to connect to Google Cloud.

	cd refresher-container
	gcloud builds submit --tag gcr.io/$PROJECT/refresher .

## Create Cloud resources:

### Create the device keys

	cd ../bridge
	openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem
	openssl ec -in ec_private.pem -pubout -out ec_public.pem

### Create IoT Core resources

	gcloud pubsub topics create device-events
	gcloud pubsub subscriptions create debug --topic device-events
	
	gcloud iot registries create $REGISTRY \
	--region=$REGION \
	--event-notification-config topic=device-events
	
	gcloud iot devices create $DEVICE \
	--region $REGION \
	--registry $REGISTRY \
	--public-key path=ec_public.pem,type=es256-pem



## Deploy the bridge

### Update project specific settings

Get the specific address for the bridge manager container:

	gcloud container images describe gcr.io/$PROJECT/refresher --format="value(image_summary.fully_qualified_digest)"


add this as the image address in  `bridge/project-image.yaml`.

If running the kubernetes cluster outside the project, make the built images public:

	gsutil iam ch allUsers:objectViewer gs://artifacts.$PROJECT.appspot.com

Edit PROJECT_ID value in `device-config.yaml`

### Deploy

	# make sure you are in the base directory for this tutorial
	cd ..
	kubectl apply -k bridge/
	
#### TODO - explain parts of the deployment:

 - shared pod process space
 - config file re-write and restart
 	- config reload does not reload remote_password
 - kustomize overlay and configmaps
 - bridge mappings

Bridged Topics:

	topic "" out 1 gcp/events /devices/CONFIG_DEVICE_ID/events
	topic "" out 1 gcp/state /devices/CONFIG_DEVICE_ID/state
	topic # out 1 gcp/events/ /devices/CONFIG_DEVICE_ID/events/
	topic "" in 1 gcp/config /devices/CONFIG_DEVICE_ID/config
	topic "" in 1 gcp/commands /devices/CONFIG_DEVICE_ID/commands
	topic # in 1 gcp/commands/ /devices/CONFIG_DEVICE_ID/commands/

### Check that the bridge deployed

	kubectl wait --for=condition=Ready pod -l "app=iot-core-bridge"
	kubectl logs -f -l "app=iot-core-bridge" -c mosquitto

## Using a cluster based MQTT client

### Build the client image

	cd client
	gcloud builds submit --tag gcr.io/$PROJECT/mqtt-client .

### Run a couple clients

You will want to start a couple terminal windows for each of these next steps

	kubectl run client-a --rm -i --tty --image gcr.io/$PROJECT/mqtt-client --generator=run-pod/v1 -- /bin/sh
	
And in another window:

	kubectl run client-b --rm -i --tty --image gcr.io/$PROJECT/mqtt-client --generator=run-pod/v1 -- /bin/sh

Note that the client can use the cluster local service name (mqtt-bridge) as the hostname.

In client "b" subscribe to a local only topic:

	sub -h mqtt-bridge -t "test/topic" -v

In client "a" publish to this topic:

	pub -h mqtt-bridge -m hello -t test/topic -d

In client "a" publish to the bridged event topic:

	pub -h mqtt-bridge -m hello -t gcp/events -d
	
Verify the bridged message was published to cloud:

	gcloud pubsub subscriptions pull debug --auto-ack --limit=100 

In both clients, subscribe to bridged IoT commands:

	sub -h mqtt-bridge -t "gcp/commands/#" -v

Publish a command via IoT Core:

	gcloud iot devices commands send --region=us-central1 \
	--registry=$REGISTRY \
	--device=$DEVICE \
	--command-data=hey \
	--subfolder=yoyo

You should see the command arrive at both clients.


### To connect a local MQTT client

If instead you want to connect a client local to the machine where you are running the `kubectl` commands, you can forward the MQTT port:

	kubectl port-forward svc/mqtt-bridge 1883:1883

## Cleanup and Next Steps

	kubectl delete -k bridge/
	
Delete the cloud project

