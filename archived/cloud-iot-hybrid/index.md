---
title: Using IoT Core as scalable ingest for hybrid projects
description: Use the scale and security of Google Cloud for ingest with on-premises IoT applications.
author: ptone
tags: IoT Core, Hybrid, Networking
date_published: 2018-05-30
---

Preston Holmes | Solution Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to use [IoT Core](https://cloud.google.com/iot) and
[Pub/Sub](https://cloud.google.com/pubsub/) to provide a secure and scalable ingest layer, combined with a small relay 
service over private networking to an on-premises IoT solution.

## Objectives

- Configure IoT Core and Pub/Sub as a fully managed ingest system
- Configure a stand-in for on-premises MQTT service on Compute Engine
- Create a small, scalable relay service that pulls messages from Pub/Sub

**Figure 1.** *Architecture diagram for tutorial components*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/architecture.png)


## Before you begin

This tutorial assumes you already have a Google Cloud Platform account set up and have completed the
[IoT Core quickstart](https://cloud.google.com/iot/docs/quickstart).


## Costs

This tutorial uses billable components of Google Cloud, including the following:

- IoT Core
- Pub/Sub
- Compute Engine

This tutorial should not generate any usage that would not be covered by the [free tier](https://cloud.google.com/free/), 
but you can use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on 
your projected production usage.

## Introduction

The idea of using fully managed scaling services is common for developers looking to distribute content. A content delivery
network ([CDN](https://en.wikipedia.org/wiki/Content_delivery_network)) is often used to provide scale between the content 
origin and many globally distributed consumers.

**Figure 2.** *CDN pattern*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/CDN.png)

Many IoT-related projects begin with a simple MQTT broker created inside premises (on-premises) corporate infrastructure to 
simplify installation while still allowing internal access. Internal apps use data arriving on this broker, along with 
access to other on-premises systems to build business-facing IoT applications. There are many reasons why a company may
prefer to pursue hybrid development. For example, hybrid development may make it easier to assess or control costs or
control data access.

Taking this initial MQTT broker and exposing it externally to production scales of device traffic may pose many challenges 
to a strictly on-premises development, including the following:

 - Increasing reliability of the network available to devices.
 - Allowing many devices to connect concurrently (MQTT is a stateful connection).
 - Keeping the MQTT broker up and running reliably.
 - Keeping the connection between devices and the cloud secure, while not exposing other on-premises network services.

 These requirements resemble that of a CDN, but in reverse.

**Figure 3.** *Global Ingest*
![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-hybrid/ingest-relay.png) 

Let's quickly set up up an implementation of a solution that uses Google's fully managed services and scale it to address 
some of these concerns while allowing the primary application to still be developed on-premises.

## Set up the environment

If you do not already have a development environment set up with [gcloud](https://cloud.google.com/sdk/downloads), it is
recommended that you use [Cloud Shell](https://cloud.google.com/shell/docs/) for any command line instructions.

Set the name of the IoT Core settings you are using to environment variables:

    export CLOUD_REGION=us-central1
    export CLOUD_ZONE=us-central1-c
    export GCLOUD_PROJECT=$(gcloud config list project --format "value(core.project)")
    export IOT_TOPIC=[the Cloud Pub/Sub topic ID you set up with your IoT Core registry; the short ID, not the full path]

Though Cloud Shell has the Go language runtime pre-installed, you will need some other libraries. Install them with this
command:

    go get cloud.google.com/go/pubsub cloud.google.com/go/compute/metadata github.com/eclipse/paho.mqtt.golang

Clone the repository associated with the community tutorials:

    git clone https://github.com/GoogleCloudPlatform/community.git

## Create the on-premises broker

You will use the project private networking as a stand-in for a proper
hybrid [Cloud Interconnect](https://cloud.google.com/network-connectivity/docs/interconnect/) setup.

Start by creating a VM to represent the on-premises broker instance. This will be running a basic version of
[RabbitMQ](https://www.rabbitmq.com/).

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

For the purpose of this tutorial, you want to be able to quickly demonstrate some of the hybrid nature of this pattern. So, 
you are going to expose this VM to the internet but will only relay data to it over the instance private IP address, 
simulating the private network link in the above architecture diagram.

To allow you to connect to this broker to verify traffic flow, allow connections to it with a firewall rule:

    gcloud compute firewall-rules create mqtt --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:1883 --source-ranges=0.0.0.0/0

## Set up the relay

For the relay to receive messages from IoT Core and Pub/Sub, it will need a dedicated subscription:

    gcloud pubsub subscriptions create relay --topic $IOT_TOPIC

The relay demonstrated here is built with [Go](https://golang.org/). The Cloud Shell environment recommended above should 
already have the tools needed to build the relay. The source for the relay is compact and simple:

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

The goal of the relay is to efficiently pull messages from Cloud Pub/Sub and then re-publish to the on-prem MQTT broker. It 
takes advantage of [asynchronous pull](https://cloud.google.com/pubsub/docs/pull#asynchronous-pull) of Cloud Pub/Sub 
(sometimes called *streaming pull*), which uses
[streaming gRPC](https://grpc.io/docs/guides/concepts.html#server-streaming-rpc) messages to reduce latency and increase 
throughput.

Create a VM to run as the relay:

    gcloud compute instances create telemetry-relay \
    --zone=$CLOUD_ZONE \
    --machine-type=g1-small

To build the relay:

    cd community/tutorials/cloud-iot-hybrid/go-relay
    bash install.sh

If you have not used SSH from Cloud Shell, you may be prompted to create a local SSH key.

This script builds the binary, installs it on the relay VM, and starts it as a relay service.

## Verifying traffic flow

You can use an MQTT client to connect to the stand-in for the on-premises broker. This represents some part of the
on-premises IoT application. One simple browser-based tool you can use in Chrome is
[MQTTLens](https://chrome.google.com/webstore/detail/mqttlens/hemojaaeigabkbcookmlgmdigohjobjm).

Use the public IP address of the `on-prem-rabbit` instance, along with a username of `user` and password of `abc123` to 
connect.

Create a subscription to an MQTT topic of `sample`.

Now you can use one of the [IoT Core quickstart samples](https://cloud.google.com/iot/docs/quickstart) to send test messages
to this topic: `/devices/${deviceId}/events/sample`

You can also quickly emulate this by publishing directly to the Cloud Pub/Sub topic directly with a `subFolder` attribute.

    gcloud pubsub topics publish $IOT_TOPIC --attribute=subFolder=sample --message "hello"

The relay republishes this to the corresponding MQTT topic on the on-premises broker over the private network, in this case
using the project-level private network DNS to lookup `on-prem-rabbit` host. (Refer to the architecture figure above for a 
refresher of the data flow.)

## Next steps

This relay service could be adapted in a number of ways:

- Scaled out to consume more messages in parallel from Pub/Sub, perhaps deployed to
  [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/).
- Use rate limiting to protect the on-premises broker from overload, using the Cloud Pub/Sub subscription as a _surge tank_.

You might also consider having the relay pulling from Pub/Sub and writing more directly to alternate services
on-premises, instead of through an on-premises MQTT broker. However, by relaying MQTT, it lets the on-premises development 
proceed if MQTT was already built into the solution, or if a looser coupling is wanted.


## Cleaning up

1.  Remove the relay subscription (this will not destroy the topic):

        gcloud pubsub subscriptions delete relay

1.  Delete the on-premises broker stand-in:

        gcloud compute instances delete --zone $CLOUD_ZONE on-prem-rabbit

1.  Delete the relay VM:

        gcloud compute instances delete --zone $CLOUD_ZONE telemetry-relay
