---
title: Using IoT Core as Scalable Ingest for Hybrid Projects
description: Use the scale and security of Google Cloud for ingest with on prem IoT applications.
author: ptone
tags: Cloud IoT Core, Hybrid, Networking
date_published: 2018-05-30
---

Preston Holmes | Solution Architect | Google

This tutorial demonstrates how to use [Cloud IoT Core](https://cloud.google.com/iot) and [Cloud Pub/Sub](https://cloud.google.com/pubsub/) to provide a secure and scalable ingest layer, combined with a small relay service over private networking to an on-prem IoT solution.

## Objectives

- Configure IoT Core and Pubsub as a fully managed ingest system
- Configure a stand-in for on-prem MQTT service on Compute Engine
- Create a small, scalable relay service that pulls messages from Cloud Pubsub

**Figure 1.** *Architecture diagram for tutorial components*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/architecture.png)


## Before you begin

This tutorial assumes you already have a Google Cloud Platform account set up and have completed the IoT Core [quickstart](https://cloud.google.com/iot/docs/quickstart).


## Costs

This tutorial uses billable components of GCP, including:

- Cloud IoT Core
- Cloud Pub/Sub
- Compute Engine

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected production usage.

## Introduction

The idea of using fully managed scaling services is common for developers looking to distribute content. A content delivery network ([CDN](https://en.wikipedia.org/wiki/Content_delivery_network)) is often used to provide scale between the content origin, and many globally distributed consumers.

**Figure 2.** *CDN pattern*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/CDN.png)

Many IoT related projects begin with a simple MQTT broker created inside premises (on-prem) corporate infrastructure to simplify installation while still allowing internal access. Internal apps use data arriving on this broker, along with access to other on-prem systems to build business facing IoT applications. There are many reasons why a company may prefer to pursue hybrid development. For example, hybrid development may make it easier to assess or control costs, can control data access, and so on.

Taking this initial MQTT broker and exposing it externally to production scales of device traffic may pose many challenges to a strictly on-prem development, including:

 - Increasing reliability of the network available to devices.
 - Allowing many devices to connect concurrently (MQTT is a stateful connection).
 - Keeping the MQTT broker up and running reliably.
 - Keeping the connection between devices and the cloud secure, while not exposing other on-prem network services.

 These requirements resemble that of a CDN, but in reverse.

**Figure 3.** *Global Ingest*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/ingest-relay.png) 

Let's quickly setup up an implementation of a solution that uses Google's fully managed services and scale it to address some of these concerns while allowing the primary application to still be developed on-prem.

## Set up the environment

If you do not already have a development environment set up with [gcloud](https://cloud.google.com/sdk/downloads), it is recommended that you use [Cloud Shell](https://cloud.google.com/shell/docs/) for any command line instructions.

Set the name of the Cloud IoT Core settings you are using to environment variables:

```sh
export CLOUD_REGION=us-central1
export CLOUD_ZONE=us-central1-c
export GCLOUD_PROJECT=$(gcloud config list project --format "value(core.project)")
export IOT_TOPIC=<the Cloud Pub/Sub topic id you have set up with your IoT Core registry this is just short id, not full path)>
```

While Cloud Shell has the golang runtime pre-installed, we will need a couple other libraries, install them with:

```sh
go get cloud.google.com/go/pubsub cloud.google.com/go/compute/metadata github.com/eclipse/paho.mqtt.golang
```

Finally clone the repo associated with the community tutorials:

```sh
git clone https://github.com/GoogleCloudPlatform/community.git
```

## Create the "on-prem" broker

You will use the project private networking as a stand-in for a proper hybrid [Google Cloud Interconnect](https://cloud.google.com/interconnect/) setup.


Start by creating a VM to represent the on prem broker instance. This will be running a basic version of [RabbitMQ](https://www.rabbitmq.com/).

```sh
gcloud beta compute instances create-with-container on-prem-rabbit \
--zone=$CLOUD_ZONE \
--machine-type=g1-small \
--boot-disk-size=10GB \
--boot-disk-type=pd-standard \
--boot-disk-device-name=on-prem-rabbit \
--container-image=cyrilix/rabbitmq-mqtt \
--container-restart-policy=always \
--labels=container-vm=cos-stable-66-10452-89-0 \
--container-env=RABBITMQ_DEFAULT_USER=user,RABBITMQ_DEFAULT_PASS=abc123
```

For the purpose of this tutorial, you want to be able to quickly demonstrate some of the hybrid nature of this pattern. As such, you are going to expose this VM to the internet but will only relay data to it over the instance private IP address, simulating the private network link in the above architecture diagram.

To allow you to connect to this broker to verify traffic flow, allow connections to it with a firewall rule:


```sh
gcloud compute firewall-rules create mqtt --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:1883 --source-ranges=0.0.0.0/0
```

## Set up the relay

In order for the relay to receive message from IoT Core and Pub/Sub, it will need a dedicated subscription:

```sh
gcloud pubsub subscriptions create relay --topic $IOT_TOPIC
```

The relay demonstrated here is built with [golang](https://golang.org/). The Cloud Shell environment recommended above should already have the tools needed to build the relay. The source for the relay is compact and simple:

[embedmd]:# (go-relay/main.go /package/ $)
```go
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"cloud.google.com/go/compute/metadata"
	"cloud.google.com/go/pubsub"
	MQTT "github.com/eclipse/paho.mqtt.golang"
)

//define a function for the default message handler
var f MQTT.MessageHandler = func(client MQTT.Client, msg MQTT.Message) {
	fmt.Printf("TOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
}

func main() {
	//create a ClientOptions struct setting the broker address, clientid, turn
	//off trace output and set the default message handler
	opts := MQTT.NewClientOptions().AddBroker("tcp://on-prem-rabbit:1883")
	opts.SetClientID("go-simple")
	opts.SetUsername("user")
	opts.SetPassword("abc123")
	opts.SetDefaultPublishHandler(f)

	//create and start a client using the above ClientOptions
	c := MQTT.NewClient(opts)
	if token := c.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	ctx := context.Background()
	var err error
	proj := os.Getenv("GOOGLE_CLOUD_PROJECT")
	if proj == "" {
		proj, err = metadata.ProjectID()
		if err != nil {
			fmt.Fprintf(os.Stderr, "GOOGLE_CLOUD_PROJECT environment variable must be set.\n")
			os.Exit(1)
		}
	}
	client, err := pubsub.NewClient(ctx, proj)
	if err != nil {
		log.Fatalf("Could not create pubsub Client: %v", err)
	}
	sub := client.Subscription("relay")
	// use async pull to get messages from devices
	err = sub.Receive(ctx, func(ctx context.Context, msg *pubsub.Message) {
		fmt.Printf("Got message: %q\n", string(msg.Data))
		fmt.Println(msg.Attributes["subFolder"])
		// publish the message to the corresponding MQTT topic in the target broker
		token := c.Publish(msg.Attributes["subFolder"], 0, false, msg.Data)
		go func(pubsource *pubsub.Message, token MQTT.Token) {
			token.Wait()
			fmt.Printf("confirmed %s\n", "message id")
			msg.Ack()
		}(msg, token)
	})

	if err != nil {
		log.Fatal(err)
	}

	c.Disconnect(250)
}
```

The goal of the relay is to efficiently pull messages from Cloud Pub/Sub, and then re-publish to the on-prem MQTT broker. It takes advantage of [asynchronous pull](https://cloud.google.com/pubsub/docs/pull#asynchronous-pull) of Cloud Pubsub (sometimes called streaming pull) which uses [streaming gRPC](https://grpc.io/docs/guides/concepts.html#server-streaming-rpc) messages to reduce latency and increase throughput.

Create a VM to run as the relay:

```sh
gcloud compute instances create telemetry-relay \
--zone=$CLOUD_ZONE \
--machine-type=g1-small
```

To build the relay:

```sh
cd community/tutorials/cloud-iot-hybrid/go-relay
bash install.sh
```

_Note: if you have not used ssh from Cloud Shell, you may be prompted to create a local SSH key._

This script will build the binary, install it on the relay VM, and start it as a relay service.

## Verifying traffic flow

You can now use an MQTT client to connect to the stand-in for the on-prem broker. This would represent some part of the on-prem IoT application. One simple browser based tool you can use in Chrome is [MQTTLens](https://chrome.google.com/webstore/detail/mqttlens/hemojaaeigabkbcookmlgmdigohjobjm?hl=en).

Use the public IP address of the `on-prem-rabbit` instance, along with a username of `user` and password of `abc123` to connect.

Create a subscription to an MQTT topic of `sample`.

Now you can use one of the [IoT Core quickstart samples](https://cloud.google.com/iot/docs/quickstart) to send test messages to the topic of: 

`/devices/${deviceId}/events/sample`

You can also quickly emulate this by publishing directly to the Cloud Pub/Sub topic directly with a `subFolder` attribute.

```sh
gcloud pubsub topics publish $IOT_TOPIC --attribute=subFolder=sample --message "hello"
```

The relay republishes this to the corresponding MQTT topic on the on-prem broker over the private network, in this case using the project-level private network DNS to lookup `on-prem-rabbit` host. (refer to the architecture figure above for a refresher of the data flow)

## Next steps

This relay service could be adapted in a number of ways:

- Scaled out to consume more messages in parallel from PubSub - perhaps deployed to [Kubernetes Engine](https://cloud.google.com/kubernetes-engine/).
- Use rate limiting to protect the on-prem broker from overload, using the PubSub subscription as a "surge tank".

You might also consider having the relay pulling from Pubsub and writing more directly to alternate services on-prem, instead of through an on-prem MQTT broker. However by relaying MQTT, it lets the on-prem development proceed if MQTT was already built into the solution, or if a looser coupling is wanted.


## Cleaning up

```sh
# Remove the relay subscription - this will not destroy the topic
gcloud pubsub subscriptions delete relay

# Delete the on-prem broker stand-in
gcloud compute instances delete --zone $CLOUD_ZONE on-prem-rabbit

# Delete the relay VM
gcloud compute instances delete --zone $CLOUD_ZONE telemetry-relay
```


