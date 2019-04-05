---
title: Load-testing an IoT application using GCP and Locust
description: Simulate the load from a population of devices to understand performance, scalability, and costs of GCP services.
author: csgcp
tags: iot, functions, internet of things
date_published: 2019-02-06
---

This tutorial describes load-testing an Internet of Things (IoT) application using Google Cloud Platform (GCP) and Locust.

A simple IoT application is included for the tutorial. The IoT application consists of a GCP Cloud Function and 100 simulated devices exchanging messages over MQTT using Cloud IoT Core.

The tutorial walks through all of the steps to create a running load test. The estimated time to perform the tutorial is 1-2 hours. 

No coding is required to complete the tutorial. You can build on the code to target your own IoT application or evaluate architecture/design choices.

## Objectives

* Simulate a load from a large number of IoT devices
* Monitor the IoT application in real time
* Understand the performance and costs of an IoT application

## Before you begin

To complete the steps in this tutorial, you need a GCP account. If you don't have a GCP account, go to the [GCP Console](https://cloud.google.com/console) and click **Create account**.

You also need the following on your local workstation:

* [gcloud](https://cloud.google.com/sdk/install)  
* kubectl (`gcloud components install kubectl`)  
* [Docker Desktop](https://www.docker.com/get-started)  
* the ability to run bash shell scripts  

## Costs

The driver (Locust) will incur GCP charges for the following:

* Compute Engine: Google Kubernetes Engine (GKE) nodes

The target (sample IoT application) will incur GCP charges for the following:

* Cloud IoT Core
* Cloud Functions

## Understanding the architecture

This diagram shows the relationship between the load test driver and the target:

![LTK architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/load-testing-iot-using-gcp-and-locust/ltk_architecture.png)

This diagram shows how the driver maps into GCP, using GKE, Kubernetes, and Docker:

![LTK GCP mapping diagram](https://storage.googleapis.com/gcp-community/tutorials/load-testing-iot-using-gcp-and-locust/ltk_gcp_mapping.png)

## Clone the repository

For the purposes of this tutorial, clone the `community` repository to your local machine.

    git clone https://github.com/GoogleCloudPlatform/community.git

If you use SSH keys to access GitHub, use the SSH equivalent:

    git clone git@github.com:GoogleCloudPlatform/community.git

This will create a directory named `community` in your current directory.

Within the `community` directory, the load testing toolkit (LTK) code is in the `tutorials/load-testing-iot-using-gcp-and-locust` directory.

Later, you will create a `.env` file in this directory along with a `devicelist.csv` file.

## Create the GCP projects

Two GCP projects should be created for this tutorial: `my-ltk-driver` and `my-ltk-target`.

To create the projects, do the following:

1. Log into the GCP Console.
2. Click the project selector in the upper-left corner of the GCP Console.
3. Click **New Project**.
4. Specify the project name (`my-ltk-driver` or `my-ltk-target`).
5. Note the project ID assigned by GCP. This is located under the project name field. Project IDs must be globally unique across all GCP customers, so if a project name is in use, GCP appends a numeric value to the project name.
6. Click **Create**.

Repeat this procedure twice: once for the `my-ltk-driver` project and once for the`my-ltk-target` project.

Two projects are recommended so you can see cost information separately for the driver and target. 

## Create the device registry

Create a device registry in the `my-ltk-target` project.

From the GCP console, do the following:

1. Ensure that the project is set to `my-ltk-target`.
2. Click the **Navigation menu** button in the upper-left corner of the GCP Console, and select Cloud IoT Core.
3. Enable the Cloud IoT Core API (if prompted).
4. Select **Create a device registry**.
5. Specify a registry ID (`my-ltk-registry`).
6. Specify a region for the registry (for example, `us-central1`).
7. Deselect HTTP as a protocol. Only MQTT is used in this tutorial.
8. For the default telemetry topic, click **Select a Cloud Pub/Sub topic**, click **Create a topic**,
   and then specify `defaultTelemetry`. Ignore any spaces between the trailing slash in the prepopulated topic
   name and your text input. 
9. Click **Create** to create the Cloud Pub/Sub topic.
10. Accept the defaults for the other registry settings.
11. Click **Create** to create the registry.

## Deploy the sample IoT application

The sample IoT application is a Cloud Function named `echoAppCF`.

When a device publishes a message, the IoT application receives the message and sends a response.

To deploy the Cloud Function, enter the following commmands from the `echoappCF` directory in the repository root:

    gcloud config set project my-ltk-target-123456
    gcloud functions deploy echoAppCF --source=. --trigger-topic defaultTelemetry --runtime nodejs8

If you are prompted to enable the `cloudfunctions.googleapis.com` API, confirm yes.

## Enable the Kubernetes Engine API

The Kubernetes Engine API needs to be enabled so that a GKE cluster can be created for the driver. 

To enable the Kubernetes Engine API:

1. Log into the GCP Console.
2. Set the project to `my-ltk-driver`.
3. Select **Kubernetes Engine > Clusters**.
4. Confirm the prompt to enable the API

This needs to be done once in the lifetime of the project.

## Enable Docker authentication to GCP

Docker needs to be able to authenticate to GCP so that it can push the master and worker images to the Google Container Registry.

Enable Docker authentication from your local workstation:

    gcloud auth configure-docker

This needs to be done once from your local workstation.


## Prepare the .env file

The GitHub repository includes a `.sample.env` file in the repository root directory. Copy this file to `.env`, and popluate the environment variables.

|Environment variable|Purpose|Example setting|
|---|---|---|
|`LTK_ROOT`|The full path name of the LTK root directory on your workstation.|`/Users/user1/repos/community/tutorials/load-testing-iot-using-gcp-and-locust`|
|`LTK_NUM_LOCUST_WORKERS`|The number of Kubernetes pods to use for the Locust workers. The device population (defined in `devicelist.csv`) will be sharded automatically between the worker pods. Generally, you want to make sure each worker does not simulate too many devices. This can cause CPU/memory pressure and thread-switching issues. For the tutorial, set this to 2. It can be increased/decreased later.|`2`|
|`LTK_DRIVER_PROJECT_ID`|The GCP project ID for the driver. The GKE cluster will be created under this project.|`my-ltk-driver-123456`|
|`LTK_DRIVER_ZONE`|The GCP zone for the driver. The GKE cluster's nodes will be created in this zone. You can get a list of available zones with the command `gcloud compute zones list`.|`us-west1-a`|
|`LTK_TARGET_PROJECT_ID`|The GCP project ID for the target (the IoT application and devices).|`my-ltk-target-123456`|
|`LTK_TARGET_REGION`|The GCP region where the device registry is located.|`us-central1`|
|`LTK_TARGET_REGISTRY_ID`|The GCP IoT registry ID.|`my-ltk-registry`|


## Set the shell environment

Before the scripts in this tutorial can be executed, you need to set the shell's environment variables.

Change directory to the repository root, and then enter the following sequence of commands:

    set -a
    . .env

The first command tells the shell to export automatically any environment variables that are subsequently set.

The second command sets the shell environment variables to the values defined in the `.env` file.

To verify the shell's environment is set correctly, you can use the `env` commmand as follows:

    env | grep LTK_

You should see the variables defined in the `.env` file.

**Note**: If you change the `.env` file, you need to repeat the `. .env` command to reload the updated enviroment variables into the shell.

## Create the test devices

Change directory to the repo root, then:

    scripts/createDevices.sh 1 100

The script does the following:

* Creates 100 devices in your GCP device registry. The devices are named LTK00001 through LTK00100.
* Appends the device IDs and private keys to a file named `devicelist.csv` in the repository root. The credentials are used by the Locust workers so the simulated devices can authenticate to Cloud IoT Core.

The devices are reused across multiple tests. They are deleted when you run the `deleteDevices` script.

## Set up the test

When you want to run a test, use the `setupTest` script to set up everything needed to start a test in Locust.

The script relies on the environment settings (from `.env`) to prepare all of the test resources (Docker images, Kubernetes pods, Kubernetes cluster, and so on).

To run the setUpTest script, `cd` to the repository root, and then run this command:

    scripts/setupTest.sh

The script will take several minutes to run, and it will produce a lot of output. At the end, you should see a message similar to the following:

    LTK: Test setup complete, visit http://[xx.xx.xx.xx]:8089 to launch a test.

`[xx.xx.xx.xx]` will be replaced by the IP address of the Locust UI (from the Kubernetes load balancer service, `kubectl get svc`).

At this point, no test is running, but everything is in place to start a test in the Locust UI (next step).

## Start the test

To start a test, open a browser tab and navigate to the URL provided by `setupTest`. You should see the Locust UI.

Specify the number of users (devices) and the hatch rate, then click the **Start Swarming** button.

Make a note of the time when you started the test.


## Monitor the test

While a test is running, there are several places you can look to monitor activity.

### Locust

#### Statistics

* "MQTT connect" and "MQTT subscribe" #requests ramp up to number of devices, with no failures
* "echo receive" #requests begin to increase
* May occasionally see "echo timeout" failures (Cloud Function does not receive payload)

#### Charts

* RPS ramps up as users (devices) are hatched
* Relatively high response times in beginning as Cloud Function containers cold start
* Number of users (devices) increase steadily up to total number of users (devices)

#### Failures

* Shows additional detail for failures such as echo timeouts (stackdriver logs can be searched for these payloads)

### GCP console: Target project

#### Cloud Functions

* Metrics: invocations/second, execution times, memory usage

#### APIs and services

* Dashboard > Cloud Functions API > Quotas 
* Dashboard > Cloud IOT API > Quotas 

#### Stackdriver

*   Cloud Function logs: You can see evidence of payloads being received by the Cloud Function. For example:

        *** received LTK00079 0x7fe0eed6bfd0 payload 848 at 154844836552332


### GCP console: Driver project
  
#### Kubernetes Engine 

* Clusters > ltk-driver > Nodes (When you select the node, you can see CPU usage and other metrics for the node.)

#### Stackdriver

*   GKE container logs: You can see evidence of payloads being sent by the devices. For example:

        *** TASK publishing LTK00089 0x7fe0eedae8d0 payload 1126 at 154844864295812

## Stop the test

When you are satisfied that enough data has been observed and collected, you can stop the test.

To stop a test, in the Locust UI, click the **Stop** button.

Make a note of the time when you stopped the test.

## Clean up

To avoid GCP charges for the driver cluster, you can delete the cluster (and perform other related post-test cleanup activities) with the `teardownTest` script:

    scripts/teadownTest.sh

The target project requires no cleanup; the project will not incur charges because the devices and Cloud Function are unused when no driver is running.

## Analyze the results

The GitHub repository includes a `harvestData` script to perform a basic data collection and analysis for the sample IoT application. The script provides two outputs:

* Frequency distribution of driver-mearured response times
* Frequency distribution of cloud function execution times

The frequency distributions are bucketed to 100 millisecond intervals.

To run the `harvestData` script, from the repository root directory:

    scripts/harvestData.sh RUN_DIR_NAME START_TIME END_TIME

* `RUN_DIR_NAME` is the name of directory in $LTK_ROOT/runs to use for the harvested data (will be created if needed).
* `START_TIME` is the start time of the test (beginnning of harvest window)
* `END_TIME` is the end time of the test (end of harvest window)

`START_TIME` and `END_TIME` are in UTC time in the format shown in this example:

    scripts/harvestData.sh 100t1 2019-01-04T20:00:00Z 2019-01-04T21:00:00Z

The frequency distributions are useful for getting a sense of where performance is clustered and for seeing outliers.

Another possible use for the distributions is for evaluating architectural or implementation changes. For example, adding a database call to the Cloud Function, or changing the Cloud Function implementation language. Configuation changes also can be evaluated, such as a change in the Cloud Function memory allocation.

## Investigating errors

If you make a change to the code in the tutorial, in some cases you might see setupTest get stuck at the point where it is "waiting for pod to enter running status". If this happens, one way to diagnose the error is to do the following:

1.  Open another terminal window.
2.  Enter the command:

        kubectl get all

3.  Look at the status of the pod. For example, if the status is ImagePullBackOff, you can get additional details as 
    follows:

        kubectl describe pod/locust-master-5d9cd9d647-bhgkl
        kubectl describe pod/locust-worker-0

In other cases, it may be helpful to look in the Stackdriver logs for the driver (GKE container logs) and target (Cloud 
Function logs, Cloud IoT Device logs).

In the GKE container logs for the `my-ltk-driver` project, you can see the device range used by each worker pod by using the filter "sharded device".

## Understanding costs

The load test kit can be used to estimate deployment costs for an IoT solution.

The suggested approach for cost evaluation is to do the following:

1.  Plan and run a test.

    Make sure you know what you want to evaluate and do a dry run of a test to make sure everything is ready.
    Decide how many devices to use and the duration of the test. A reasonable duration is one hour.

2.  Run the test.

3.  Check billing in GCP console.

    Currently it takes 72 hours for charges to appear in the GCP Billing console.

    After 72 hours, do the following:  
    1.  Go into Billing in the GCP console.
    2.  Select the billing account.
    3.  Select the project (driver or target).
    4.  Under Time Range, select Pick a Date and speficy the date of the test.
    5.  Under Group By, select Product (if more detail is needed, select SKU).
    6.  You should see a breakdown of costs.  

4.  Estimate costs for 24x7 operation with N devices.

    The cost data for one hour, with 100 devices for example, could be used to estimate the cost
    for 10,000 devices operating 24x7.

    For example, if the one-hour test with 100 devices costs $1 on the target side, the monthly cost
    could be estimated as 1 * 100 * 720 = $72,000 (1 dollar * 100 times the size of the test population * 720 hours in a 30-day month).

**Note**: Raw billing data is available in [BigQuery](https://cloud.google.com/billing/docs/how-to/export-data-bigquery).

## Scaling up the number of devices

1.  Create the additional devices using the `createDevices` script.

    The script is "additive", so the new devices are appended to the existing `devicelist.csv`.

    For example, if the `devicelist.csv` contains 1 through 100 (the range used for the tutorial),
    to add 100 more devices, you can use the command:

        scripts/createDevices.sh 101 200

    This command adds the serial numbers 101 through 200 (deviceIds LTK00101 through LTK00200).

2.  (optional) Update the `.env` file.

    When more devices are added, it may be necessary to increase the number of Locust workers.

    *   Increase LTK_NUM_LOCUST_WORKERS if the additional devices could cause excessive devices on a single worker
        (based on CPU/memory/thread usage).

    When specifying LTK_NUM_LOCUST_WORKERS, you need to make sure your GCP Compute Engine quotas allow the specified
    number of nodes. The `setupTest` script will create a GKE cluster with LTK_NUM_LOCUST_WORKERS+1 nodes. The podspec
    for the workers uses antiaffinity, so each worker is placed in a different node and the master is in its own node.
    The main quota limits are on number of CPUs and number of IN_USE_ADDRESSES (one address is
    required per cluster node). There are quotas at the project and region levels.

        gcloud compute project-info describe --project my-ltk-driver | grep -C 1 IN_USE_ADDRESSES
        gcloud compute regions describe europe-west3 | grep -C 1 IN_USE_ADDRESSES
        gcloud compute project-info describe --project my-ltk-driver | grep -C 1 CPU
        gcloud compute regions describe europe-west3 | grep -C 1 CPU

    If there is insufficient quota in one region, you can try another. A listing of regions and zones is available
    with this command:

        gcloud compute zones list
    
    More information about Compute Engine quotas is available [here](https://cloud.google.com/compute/quotas).

3.  Run `setupTest`.

    This will rebuild the master and worker Docker images with the added-to `devicelist.csv`.

4.  Start a test in Locust.

    Starting a test in the Locust UI causes the workers to shard the `devicelist.csv`. The sharding calculate
    the portion of the csv (the "block" of devices) a worker is using. The block offset into the csv is
    determined by the worker pod's host name, which includes an ordinal (integer 1 to n) uniquely identifying
    the pod in the replica set. The ordinal is available because the podspec uses the StatefulSet pod type.

## Load-testing your IoT application

Load-testing your IoT application requires software development in Python. 

The Python code will simulate the "over-the-network" behavior of your device population. This allows you to evaluate the 
performance, scalability, and cost of your IoT application's backend services accessed over an IPv4/IPv6 network.

### Planning

* Understand the questions that you want to answer with a load test.

* Decide the device behaviors you want to simulate. It's easiest to start with a relatively simple behavior, where it's
easy to build/process the payloads sent over the network.

* Decide how you will evaluate success and failure of the device behaviors. These translate into Locust events you need to
place in the Python code in `locustfile.py`. The easiest cases are when there is a request/response, where the response (or
timeout) would indicate when a failure occurs.

* Understand what data you need to evalaute the results. Long tests with many devices can create very large amounts of data
to collect and analyze. In cases where harvesting data is impractical, monitoring capabilities built into the GCP console 
can be used.

### Code repository 

You can duplicate LTK into your own git repository. This way, you can push changes, create branches, and control access.
Forking Google's community tutorials is not recommended for custom development work.

To duplicate LTK into your own Github repository, do the following:

1.  Perform the steps under "Clone the `community` repository" earlier in this document.

2.  Move or copy the LTK directory to a new location outside of `community/tutorials`:

    ```
    cd community/tutorials
    mv load-testing-iot-using-gcp-and-locust ~/my-ltk
    ```

3.  Initialize the LTK directory as a repository:

    ```
    cd ~/my-ltk
    git init
    ```

4.  Go to GitHub and create a repository in your GitHub account.

5.  Make your new repository the origin:

    ```
    git remote add origin https://github.com/<your Github userId>/<your Github repo name>.git (HTTPS)
    or
    git remote add origin git@github.com:<your Github userId>/<your Github repo name>.git (SSH)
    ```

6.  Push the code to the new repository:

    ```
    git add .
    git commit -m "first commit"
    git push -u origin master
    ```

**Note**: Be sure to save your `.env` and `devicelist.csv` files if you re-create a repository or need to use them with a 
different branch.

### Code

Implement the device behaviors in `locustfile.py`. Generally, this involves the following:

* a Locust "task" for the behavior
* the `on_*` event handlers called by the Paho client (if using MQTT)
* calling `events.request_success.fire` and `events.request_failure.fire` to record the success/failure of a device behvaior

### Test

While developing device behaviors, it is easiest to test the behaviors locally. 

This can be done by [installing Locust](https://docs.locust.io/en/stable/installation.html) locally and running Locust
headless in command-line mode as follows (from the repository root):

    set -a
    . .env
    PROJECT_ID=$LTK_TARGET_PROJECT_ID
    REGION=$LTK_TARGET_REGION
    REGISTRY_ID=$LTK_TARGET_REGISTRY_ID
    locust --no-web -c 1 -r 1 --only-summary

Python 2.7 is required for Locust 0.9.0

Locust 0.9.0 is required for support of the Locust API needed for assigning device IDs to simulated devices

If the above instructions install a downlevel version, see [this post on Stack Overflow](https://stackoverflow.com/questions/49439587/locust-io-setup-teardown-not-executed).

### Deployment

Changes can be deployed by running the `setupTest` script. The script will create new Dockerfiles with the updated `locustfile.py`.
