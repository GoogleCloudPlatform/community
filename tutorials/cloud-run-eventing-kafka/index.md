---
title: Serverless Eventings with Cloud Run on Anthos, Knative Evetnings and Apache Kafka from Confluent&copy;
description: Create a simple event driven application for currency exchange rate traking using Cloud Run on Anthos, Knative Eventing, Apache Kafka, and AlphaVantage
author: thejaysmith
tags: Serverless, Eventing, Cloud Run, Kafka, Knative
date_published: 2019-11-04
---

* Jason "Jay" Smith | Customer Engineer Specialist | Google Cloud

## Using Google Cloud Run with Knative Eventing and Confluent Cloud

[Cloud Run](https://cloud.google.com/run/ "Cloud Run") is a Google Cloud Platform offering built on the [Knative Serving](https://knative.dev/docs/serving/ "Knative Serving") APIs. This brought a lot of serverless practices to Kubernetes, allowing developers to focus on code while the operators focus on the infrastructure.

Developers are allowed to containerize their applications and deploy them into the cloud without worrying about configuring networking, machine types, etc. By default, Cloud Run listens to HTTP and HTTPS traffic. In a world of event streaming, we need to concern ourselves with other types of event sources.

One popular tool for handling event streaming in a scalable manner is [Apache Kafka](https://kafka.apache.org). Google Cloud has a fully managed Kafka solution through our SaaS partner [Confluent](https://confluent.io).

For this demo, we will be using [Confluent Cloud](https://www.confluent.io/confluent-cloud/) as well as [AlphaVantage](https://www.alphavantage.co/). Both offer a free tier solution so using them won't cost anything additionally within the scope of this demo. I would recommend destroying your cluster afterwards to prevent paying for anything after the fact.

In `kafka-cr-eventing/scripts` you will see `setup.sh`. If you want to do this the easy way, simply run the following commands and follow the prompts. BUT FIRST, let's setup an account with AlphaVantage [here](https://www.alphavantage.co/support/#api-key) to get a free API Key as well as signing up for Confluent Cloud as seen [here](https://confluent.cloud/signup).

***I would also recommend running this script in Cloud Shell vs running it on your own machine as it will attempt to install GoLang.***

This script will do a few things for you. First it will check to see if [GoLang 1.13.1](https://golang.org/doc/go1.13), [Google Cloud SDK](https://cloud.google.com/sdk/), and [Confluent Cloud CLI](https://docs.confluent.io/current/cloud/cli/install.html) if these aren't already installed.

It will then enable different Google Cloud APIs, install a GKE cluster, prepare that cluster for Cloud Run, and deploy an app that collects currency exchange information.

So let's execute the script below. **Note:** *I encourage reading through the script to see what it actually does*

``` bash
export CLUSTER_NAME="kafka-events" #You can change this to whatever you want"
chmod +x setup.sh
./setup.sh
```

Once the script is done, let's take the next step. Give it about a minute of two from the cronjob to run. Open a tab in your terminal and run this command. 

``` bash
ccloud kafka topic consume cloudevents #Note, you may need to login with 'ccloud login`
```

You will leave this running and it will show you events being written to your Kafka topic. Now let's run `kubectl get pods` and you should see something like this.

```bash
currency-app-l6g6g-deployment-5d679fcf5c-mnvjh    2/2     Running   0          62s
event-display-hbrjj-deployment-79f85796d9-n4ftd   2/2     Running   0          5s
kafka-source-9mmvw-78cf98d4c4-g4pmm               1/1     Running   0          10s
```

Take the event-display-xxxxx-deployment-xxx-xxxx pods and let's check the logs. 

```bash
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
```

Under **Data** you should see something like `MTA4LjU5MDAwMDAw`. Yours may look a little different. CloudEvents are in Base64 so let's decode it.

```bash
$ echo `echo MTA4LjU5MDAwMDAw | base64 --decode`
108.59000000
```

This should be your exchange rate and if you look at your ccloud tab in terminal, it should match the consumed message. Congratulations, you have now created a simple streaming event serverless application.

Now we will teardown what we built using our cleanup script. ***Running this script will delete whatever cluster is assigned to the bash variable `$CLUSTER_NAME`. Be sure that you only assign the cluster that you created for this demo.

```  bash
export CLUSTER_NAME="YOUR CLUSTER"
export CONFLUENT_ID=$(ccloud kafka cluster list | grep "*" | cut -c4-14)
cd kafka-cr-eventing/scripts
chmod +x cleanup.sh
./cleanup.sh
```

You are now good to go!
[EOF]
