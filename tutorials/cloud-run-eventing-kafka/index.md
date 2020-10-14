---
title: Serverless eventing with Cloud Run on Anthos with Knative Eventing and Apache Kafka
description: Create a simple event-driven application for currency exchange rate tracking.
author: thejaysmith
tags: Serverless, Eventing, Cloud Run, Kafka, Knative
date_published: 2019-11-27
---

Jason "Jay" Smith | Customer Engineer Specialist | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[Cloud Run](https://cloud.google.com/run/ "Cloud Run") is a Google Cloud offering built on the
[Knative Serving](https://knative.dev/docs/serving/) APIs, which brings serverless practices to Kubernetes, allowing 
developers to focus on code while operators focus on the infrastructure.

Developers can containerize their applications and deploy them to the cloud without worrying about configuring networking,
machine types, and so on. By default, Cloud Run listens to HTTP and HTTPS traffic. In a world of event streaming, we need to
concern ourselves with other types of event sources, too.

One popular tool for handling event streaming in a scalable manner is [Apache Kafka](https://kafka.apache.org). Google Cloud 
has a fully managed Kafka solution through our SaaS partner [Confluent](https://confluent.io).

For this demonstration, we use [Confluent Cloud](https://www.confluent.io/confluent-cloud/) and
[AlphaVantage](https://www.alphavantage.co/). Both offer a free-tier solution, so using them for this demonstration won't
incur additional charges. We recommend deleting your cluster after you have finished with this tutorial, to prevent 
incurring charges.

## Before you begin

1. Set up an account with [AlphaVantage](https://www.alphavantage.co/support/#api-key) to get a free API key.
1. Sign up for [Confluent Cloud](https://confluent.cloud/signup).

## Run the setup script

The `kafka-cr-eventing/scripts` folder contains the `setup.sh` setup script for this demonstration. 

We recommend that you run this script in [Cloud Shell](https://cloud.google.com/shell/), rather than running it on
your local machine.

The setup installs [GoLang 1.13.1](https://golang.org/doc/go1.13), [Google Cloud SDK](https://cloud.google.com/sdk/), and 
[Confluent Cloud CLI](https://docs.confluent.io/current/cloud/cli/install.html) if they aren't already installed. The setup 
script then enables some Google Cloud APIs, installs a GKE cluster, prepares that cluster for Cloud Run, and deploys an app 
that collects currency exchange information.

We encourage you to read through the script for the details of what it does.

To execute the script, run the following commands (replacing `[your_AlphaVantage_API_key]` with the API key value):

```bash
export CLUSTER_NAME="kafka-events" #You can change this to whatever you want.
export AV_KEY="[your_AlphaVantage_API_key]"
chmod +x setup.sh
./setup.sh
```

Wait for a couple of minutes for all of the steps in the script to finish.

## Use the simple streaming event serverless application

1.  After the script has finished, open a tab in your terminal and run this command:

        ccloud kafka topic consume cloudevents
        
    **Note**: You may need to log in with `ccloud login`.

    You will leave this running, and it will show you events being written to your Kafka topic.
    
1.  Run this command:

        kubectl get pods
        
    You should see something like this:

        currency-app-l6g6g-deployment-5d679fcf5c-mnvjh    2/2     Running   0          62s
        event-display-hbrjj-deployment-79f85796d9-n4ftd   2/2     Running   0          5s
        kafka-source-9mmvw-78cf98d4c4-g4pmm               1/1     Running   0          10s

1.  Check the logs for the `event-display-xxxxx-deployment-xxx-xxxx` pods:

        $ kubectl logs event-display-hbrjj-deployment-79f85796d9-n4ftd -c user-container
        ☁️  cloudevents.Event
        Validation: valid
        Context Attributes,
          specversion: 0.2
          type: dev.knative.kafka.event
          source: /apis/v1/namespaces/default/kafkasources/kafka-source#cloudevents
          id: partition:1/offset:11
          time: 2019-11-04T21:11:55.111Z
          contenttype: application/json
        Extensions,
          key:
        Data,
          "MTA4LjU5MDAwMDAw"
        ☁️  cloudevents.Event
        Validation: valid
        Context Attributes,
          specversion: 0.2
          type: dev.knative.kafka.event
          source: /apis/v1/namespaces/default/kafkasources/kafka-source#cloudevents
          id: partition:3/offset:7
          time: 2019-11-04T21:12:02.879Z
          contenttype: application/json
        Extensions,
          key:
        Data,
          "MTA4LjU5MDAwMDAw"

    Under `Data` you should see something like `MTA4LjU5MDAwMDAw`. Yours may look a little different. 
    
1.  Cloud events are encoded in base64, so let's decode it:
    
        $ echo `echo MTA4LjU5MDAwMDAw | base64 --decode`
        108.59000000

    This is your exchange rate. Look at your ccloud tab in the terminal, to check that it matches the consumed message. 
    
Congratulations, you have now created a simple streaming event serverless application.

## Cleaning up

Now, it's time to clean up what you built using the cleanup script.

Running this script will delete whatever cluster is assigned to the bash variable `$CLUSTER_NAME`. Be sure that you only 
assign the cluster that you created for this demo.

```  bash
export CLUSTER_NAME="YOUR CLUSTER"
export CONFLUENT_ID=$(ccloud kafka cluster list | grep "*" | cut -c4-14)
cd kafka-cr-eventing/scripts
chmod +x cleanup.sh
./cleanup.sh
```

You are now good to go!
