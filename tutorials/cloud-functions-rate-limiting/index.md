
---
title: Rate limiting Serverless with Redis and VPC Connector
description: Use rate limiting techiques with serverless functions.
author: ptone
tags: Cloud Functions, Cloud Firestore, serverless, redis, VPC
date_published: 2019-05-31
---

Preston Holmes | Solution Architect | Google

## Introduction

This tutorial demonstrates several rate limiting techniques from an [accompanying concept paper - temporary internal link](https://go/rate-limiting-patterns). Specifically you will learn how to use private networking and [Redis](https://redis.io/) to synchronized global rate limiting state to otherwise stateless serverless functions.

## Objectives

* Use [Serverless VPC Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) to connect functions to [Redis](https://redis.io/) in private VPC network.
* Use Node + [Redis](https://redis.io/) based rate limiting library in a Cloud function to limit function invocations.
* Use these technique to limit function invocations by IP address of the caller.
* Combine rate limiting with a [Redis](https://redis.io/) based counter to provide a high speed counter implementation for [Cloud Firestore](https://cloud.google.com/firestore/).

## Setup

1.  Create a project in the [GCP Console][console].
	- Note if you want to use an existing project, the last part will use Firestore, which can not be changed or combined with Datastore once configured per project.
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Use [Cloud Shell][shell] or install the [Google Cloud SDK][sdk].


[console]: https://console.cloud.google.com/
[shell]: https://cloud.google.com/shell/
[sdk]: https://cloud.google.com/sdk/


Set up your environment:

```
# this is automatic in Cloud Shell
gcloud config set project [ your project id ]

export REGION=us-central1
export GOOGLE_CLOUD_PROJECT=$(gcloud config list project --format "value(core.project)" )
```

Enable APIs, this may take a moment:

```
gcloud services enable \
cloudfunctions.googleapis.com \
compute.googleapis.com \
servicenetworking.googleapis.com \
vpcaccess.googleapis.com
```

Clone the tutorial code:

```
# TODO note draft tutorial location to be updated
git clone https://github.com/ptone/community.git
cd community
git checkout rate-limiting
cd tutorials/cloud-functions-rate-limiting
```

## Create a Network and VPC connector

For this tutorial you will create a dedicated VPC network and an associated serverless connector. You use the VPC Serverless connector to allow a Serverless function to reach a Redis service on a private IP address, as Redis is not designed to be exposed to public internet.

Create the network:

```
export NETWORK=rate-limiting-demo

gcloud compute networks create $NETWORK 

```

Create the VPC connector:

```
gcloud compute networks subnets update ${NETWORK} --region ${REGION} --enable-private-ip-google-access

gcloud beta compute networks vpc-access connectors create functions-connector \
--network ${NETWORK} \
--region ${REGION} \
--range 10.8.0.0/28
```

### Set Permissions 

Your project's Cloud Functions service account needs appropriate permissions in order for your function to use a Serverless VPC Access connector. You only need to grant these permissions once per project. Alternate console instructions are [here](https://cloud.google.com/functions/docs/connecting-vpc#setting_up_permissions).

```
export AGENT=service-$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")@gcf-admin-robot.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$AGENT --role roles/viewer

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$AGENT --role roles/compute.networkUser
```


## Create a Redis server

[Redis](https://redis.io/) provides very low latency KV storage, along with a number of basic data structures and operations that make it one fo the more preferred backing stores for rate-limiting implementations.

Google Cloud offers a fully managed Redis service in the form of [Cloud Memorystore](https://cloud.google.com/memorystore/), which allows for large and highly available memory pools. This tutorial will use a small container based instance as an alternative to quickly set up a demo-capable Redis Service.

```
gcloud beta compute instances create-with-container redis \
--zone=${REGION}-a \
--machine-type=g1-small \
--no-address \
--container-image=redis \
--container-restart-policy=always \
--subnet=${NETWORK} \
--scopes=https://www.googleapis.com/auth/devstorage.read_only
```
Note: Container VMs are configured to use a Google Docker Hub mirror, so this instance does not need any public internet access.

## Get the IP address of the Redis service

Capture the private IP address of the Redis service into an environment variable for subsequent steps:

```
export REDIS_HOST=$(gcloud compute instances describe redis --format='value(networkInterfaces[0].networkIP)' --zone=${REGION}-a)
```

## Deploy basic rate limiting function

Deploy a cloud function that uses basic rate limiting.

```
cd ./basic-rate/

gcloud beta functions deploy basicRateDemo \
  --runtime nodejs10 \
  --trigger-http \
  --source ./build  \
  --set-env-vars=REDIS_HOST=${REDIS_HOST} \
  --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector \
  --region ${REGION}
```

The flags in the gcloud command:

- Deploy a function named `basicRateDemo`
- Using the node 10 runtime
- triggered by HTTP requests
- From the Typescript transpiled JS src code
- Set a runtime env var to the Redis svc IP
- Connected to VPC
- in target region

This function uses a Redis backed [rate limiting library](https://www.npmjs.com/package/redis-rate-limiter) for Node. You use an environment variable to connect a Redis client in [global scope](https://cloud.google.com/functions/docs/concepts/exec#function_scope_versus_global_scope) to make the function more efficient:

```
const redisAddress = env.get('REDIS_HOST', '127.0.0.1');

const client = redis.createClient(6379, redisAddress, { enable_offline_queue: true })
```

This Redis client is then used to create a rate limiter which defines a global rate limit for all functions of 10 requests per second associated with a limiting key of `basicRate`:

```
    const limit = rateLimiter.create({
        redis: client,
        key: function (requestObj: any) { return 'basicRate' },
        rate: '10/second'
    })
```

Then for each function invocation, the limit is checked, and if over limit a 429 HTTP response is returned:

```
    limit(req, function (err: Error, rate: any) {
        if (err) {
            console.warn('Rate limiting not available');
            // fail open
            res.send("OK\n");
        } else {
            if (rate.over) {
                console.error('Over the limit!');
                res.send(429);
            } else {
                res.send("OK\n");
            }
        }
    });
```

## Generate load for the function

Now that the function is deployed, you will test that it is enforcing limits as intended.

For this you will use a load generating tool called [Bombardier](https://github.com/codesenberg/bombardier).

`go get -u github.com/codesenberg/bombardier`

If you are not in Cloud Shell or do not have golang installed, you can download the tool from the [releases page](https://github.com/codesenberg/bombardier/releases).



### Get URL of func

```
export URL=$(gcloud functions describe basicRateDemo --format='value(httpsTrigger.url)')
```

### Call the function

Use the Bombardier tool to call the function at a rate of 12 requests per second for 5 seconds:

`bombardier -r 12 -d 5s $URL`

You should see output that looks something like:

```
Done!
Statistics        Avg      Stdev        Max
  Reqs/sec        12.69       5.30      23.19
  Latency       99.43ms    62.81ms   362.91ms
  HTTP codes:
    1xx - 0, 2xx - 46, 3xx - 0, 4xx - 17, 5xx - 0
    others - 0
  Throughput:    17.04KB/s
```

Note that the 2xx vs 4xx responses may change if you run this several times, as requests are delayed and buffered in the Cloud Functions infrastructure during function cold start, which results in an apparent rate of > 12QPS to the function and hence a higher 429 response rate.

You can try changing the rate to see that the ratio of 4xx responses increases as you increase the rate.

## IP Rate Demo

Deploy a function which limits by IP address:

```
cd ../ip-limit/

gcloud beta functions deploy IPRateDemo \
  --runtime nodejs10 \
  --trigger-http \
  --source ./build  \
  --set-env-vars=REDIS_HOST=${REDIS_HOST} \
  --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector \
  --region ${REGION}
```

This is similar to the first function, except that it uses the source IP address from the request object as the rate limiting key.

```
    const limit = rateLimiter.create({
        redis: client,
        key: function (requestObj: any) { return requestObj.ip },
        rate: '10/second'
    }); 
```


In order to prove this is working as intended, you will need to install Bombardier into a second location (e.g. if you are using Cloud Shell, either create a temporary VM, or use your developer workstation).

From each of these locations, run this command at the same time:

```
export URL=$(gcloud functions describe IPRateDemo --format='value(httpsTrigger.url)')

bombardier -r 8 -d 30s $URL
```

You should see that each location should get nearly all 2xx responses back, even though the total request load to the function would be 2 x 8 = 16 QPS which is > 10.

## Firestore Counter

In this section, you will combine a rate limiter with a Redis backed counter to provide a Firestore persisted high-speed counter.

In Cloud Firestore, you can only update a single document about once per second, which might be too low for some high-traffic applications. One solution to this problem is to [distribute the counter](https://firebase.google.com/docs/firestore/solutions/counters) update load to different document shards and sum them when a total is needed.

In this approach you will use a high speed Redis counter to increment a value at a very high rate and combine this with a rate limiter that controls how often that value is written to Firestore for application visibility.

![](images/counter.png)

Deploy the function:

```
cd ../firestore-counter/

gcloud beta functions deploy counterLimit \
  --runtime nodejs10 \
  --trigger-http \
  --source ./build  \
  --set-env-vars=REDIS_HOST=${REDIS_HOST} \
  --vpc-connector projects/${GOOGLE_CLOUD_PROJECT}/locations/${REGION}/connectors/functions-connector \
  --region ${REGION}
```

Now you want to open the [Cloud Firestore console](https://console.cloud.google.com/firestore/data) and create a database in Firestore **Native Mode**. Choose the same region as where you are deploying your functions (North America by default).

```
export URL=$(gcloud functions describe counterLimit --format='value(httpsTrigger.url)')
bombardier -r 500 -d 20s $URL
```

You may need to reload the Firestore console page to see the counter document, but while the `counter` document is visible in the `demo` collection, you should see the value increase in large increments every several seconds.

## Cleanup

The simplest way to clean up the tutorial is to delete a project you created just for this tutorial. Alternatively, the following compound command will delete resources created in this tutorial with the exception of Firestore, which can not be deleted once created in a project.

```
gcloud functions delete basicRateDemo --quiet && \
gcloud functions delete IPRateDemo --quiet && \
gcloud functions delete counterLimit --quiet && \
gcloud beta compute instances delete redis --zone=${REGION}-a --quiet && \
gcloud beta compute networks vpc-access connectors create functions-connector --quiet && \
gcloud compute networks delete $NETWORK --quiet
```