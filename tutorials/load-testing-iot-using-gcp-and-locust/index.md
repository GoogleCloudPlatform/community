

Load testing an IOT Application Using GCP and Locust
====================================================

This tutorial shows a way to load test an Internet-of-Things (IOT) application using Google Cloud Platform (GCP) and Locust.

A simple IOT application is included for the tutorial. The IOT application consists of a single backend service (a GCP cloud function) and 100 devices (using GCP IOT Core).

The tutorial walks through all the steps to run a load test. The estimated time to perform the tutorial is 1-2 hours.

You can customize the code to target your own IOT application.



# Objectives

* Simulate a load from a large number of IOT devices
* Monitor the IOT application in real-time
* Understand the performance and costs of an IOT application

# Before You Begin

To complete the steps in this tutorial, you need:

1. A GCP account

If you don't have a GCP account, visit https://cloud.google.com/console and click "Create account".

2. On your local workstation:

a. clone of the LTK repository (https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/load-test-iot-locust)  
b. gcloud (https://cloud.google.com/sdk/install)  
c. kubectl (`gcloud components install kubectl`)  
d. Docker Desktop (https://www.docker.com/get-started)  
e. The ability to run bash shell scripts  




# Costs

The driver (Locust) will incur GCP charges for:

* Compute engine - Google Kubernetes Engine (GKE) nodes

The target (sample IOT application) will incur GCP charges for:

* IOT Core
* Cloud functions

# Understanding the Architetcure

This diagram shows the relationship between the load test "driver" and the "target".

![ltk_architecture.png](https://github.com/csgcp/blob/master/ltk_architecture.png)

This diagram shows how the driver maps into GCP, using GKE, Kubernetes, and Docker.

![ltk_gcp_mapping.png](https://github.com/csgcp/blob/master/ltk_gcp_mapping.png)


# Create the GCP Projects

Two GCP projects are created for this tutorial - `my-ltk-driver` and `my-ltk-target`.

To create the `my-ltk-driver` project:

1. Log onto the GCP console
2. Click on the project drop-down at the upper left
3. Click on "New Proect"
4. Specify the project name (`my-ltk-driver` or `my-ltk-target`)
5. *Note the project ID assigned by GCP* - This is located under the project name field. Project IDs must be globally unique across all GCP customers, so if a project name is in use, GCP appends a numeric value to the project name.
6. Click "Create"

Repeat this procedure twice - once for the `my-ltk-driver` project, and once for the`my-ltk-target` project.

Two projects are recommended, so you can see cost/billing information separately for the driver and target. 


# Create the Device Registry

For the purposes of this tutorial, create a device registry in the `my-ltk-target` project.

From the GCP console:

1. Ensure the project is set to `my-ltk-target`
2. Click the pancake icon in the top left, and select IOT Core 
3. Enable the IOT Core API (if prompted)
4. Select "Create a device registry"
5. Specify a registry ID (`my-ltk-registry`)
6. Specify a region for the registry (us-central1)
7. Deselect HTTP as a protocol (only MQTT will be used in the tutorial)
8. For default telemetry topic, click "Select a Cloud Pub/Sub topic" then "Create a topic", then specify `defaultTelemetry` for the topic. Ignore any spaces between the trailing slash in the prepopulated topic name and your text input. 
9. Click "Create" to create the Pub/Sub topic
10. Accept the defaults for the other registry settings
11. Click "Create" to create the registry


# Deploy the Sample IOT Application

The sample IOT application is a cloud function named `echoAppCF`.

When a device publishes a message, the IOT application receives the message and sends a response.

To deploy the cloud function, enter the following commmands from the `echoappCF` directory in the repo root:

```
gcloud config set project my-ltk-target-123456
gcloud functions deploy echoAppCF --source=. --trigger-topic defaultTelemetry --runtime nodejs8
```

If you are prompted to enable the `cloudfunctions.googleapis.com` API, confirm yes.


# Enable the Kubernetes Engine API

The Kubernetes Engine API needs to be enabled, so a GKE cluster can be created for the driver. 

To enable the Kubernetes Engine API:

1. Log on to the GCP console
2. Set the project to `my-ltk-driver`
3. Select Kubernetes Engine > Clusters
4. Confirm the prompt to enable the API

This needs to be done once in the lifetime of the project.


# Enable Docker authentication to GCP

Docker needs to be able to authenticate to GCP, so it can push the master and worker images to the Google Container Registry (GCR).

To enable Docker authentication from your local workstation:

```
gcloud auth configure-docker
```

This needs to be done once from your local workstation.


# Prepare the .env File

The github repository includes a .sample.env file in the respository root directory. Copy this file to .env, and popluate the environment variables.

|Environment Variable|Purpose|Example Setting|
|---|---|---|
|LTK_ROOT|The full path name of the LTK root directory on your workstation.|/Users/user1/repos/ltk|
|LTK_NUM_LOCUST_WORKERS|The number of Kubernetes pods to use for the Locust workers. The device population (defined in devicelist.csv) will be sharded automatically between the worker pods. Generally, you want to make sure each worker does not simulate too many devices. This can cause memory pressure and thread-switching issues in the underlying operating system process. As a starting point, set this to 2. It can be increased/decrease later.|2|
|LTK_NUM_GKE_NODES|The number of GKE nodes (Google Compute Engine VMs) used to run the worker pods. Generally, you want to make sure the pods do not consume an excesssive amount of CPU and memory in the VMs. Normally this would be set to the number of worker pods. As a starting point, set this to 2. It can be increased/decrease later.|2|
|LTK_DRIVER_PROJECT_ID|The GCP project ID for the driver. The GKE cluster will be created under this project.|my-ltk-driver-123456|
|LTK_DRIVER_ZONE|The GCP zone for the driver. The GKE cluster's nodes will be created in this zone. You can get a list of available zones with the command `gcloud compute zones list`.|us-west1-a|
|LTK_TARGET_PROJECT_ID|The GCP project ID for the target (the IOT application and devices).|my-ltk-target-123456|
|LTK_TARGET_REGION|The GCP region where the device registry is located.|us-central1|
|LTK_TARGET_REGISTRY_ID|The GCP IOT registry ID.|my-ltk-registry|


# Set the Shell Environment

Before the scripts in this tutorial can be executed, you need to set the shell's environment variables.

Change directory to the repo root, then enter the following sequence of commands

```
set -a
. .env
```

The first command tells the shell to export automatically any environment variables that are subsequently set.

The second command sets the shell environment variables to the values defined in the .env file.

To verify the shell's environment is set correctly, you can use the `env` commmand as follows:

```
env | grep LTK_
```

You should see the variables defined in the .env file.

**WARNING:** If you change the .env file, you need to repeat the `. .env` command to reload the updated enviroment variables into the shell.


# Create the Test Devices

Change directory to the repo root, then:

`scripts/createDevices.sh 1 100`

The script:

1. Creates 100 devices in your GCP device registry. The devices are named LTK00001 through LTK00100.
2. Appends the device IDs and private keys to a file named `devicelist.csv` in the repository root. The credentials are used by the Locust workers so the simulated devices can authenticate to GCP IOT Core.

The devices are reused across multiple tests. They are deletd when you run the `deleteDevices` script.



# Set Up the Test

When you want to run a test, use the `setupTest` script to set up everything needed to start a test in Locust.

The script relies on the environment settings (from .env) to prepare all the test resources (docker images, kubernetes pods, kubernetes cluster, etc).

To run the setUpTest script, cd to the repo root, then:

`scripts/setupTest.sh`

The script will take several minutes to run, and it will produce a lot of output. At the end, youn should see a message similar to the following:

```
LTK: Test setup complete, visit http://xx.xx.xx.xx:8089 to launch a test.
```

xx.xx.xx.xx is the IP address of the Locust UI (from the Kubernetes load balancer service - `kubectl get svc`).

At this point, no test is running, but everything is in place to start a test in the Locust UI (next step).


# Start the Test

To start a test, open a browser tab and navigate to the URL provided by `setupTest`. You should see the Locust UI.

Specify the number of users (devices) and the hatch rate, then click the "Start Swarming" button.

Make a note of the time you started the test.


# Monitor the Test

While a test is running, there are several places you can look to monitor activity.

## Locust

### Statistics

* "MQTT connect" and "MQTT subscribe" #requests ramp up to number of devices, with no failures
* "echo receive" #requests begin to increase
* May occasionally see "echo timeout" failures (cloud function does not receive payload)

### Charts

* RPS ramps up as users (devices) are hatched
* Relatively high response times in beginning as CF containers cold start
* Number of users (devices) increase steadily up to total number of users (devices)

### Failures

* Shows additional detail for failures such as echo timeouts (stackdriver logs can be searched for these payloads)

## GCP console - Target project

### Cloud Functions

* Metrics - invocations/second, execution times, memory usage

### APIs and Services

* Dashboard > Cloud Functions API > Quotas 
* Dashboard > Cloud IOT API > Quotas 

### Stackdriver

* Cloud Function logs - can see evidence of payloads being received by the CF, for example:
```
     *** received LTK00079 0x7fe0eed6bfd0 payload 848 at 154844836552332
```

## GCP console - Driver project
  
### Kubernetes Engine 

* Clusters > ltk-driver > Nodes (when you select the node, you can see CPU usage and other metrics for the node)

### Stackdriver

* GKE container logs - can see evidence of payloads being sent by the devices, for example:
```
    *** TASK publishing LTK00089 0x7fe0eedae8d0 payload 1126 at 154844864295812
```


# Stop the Test

When you are satisfied enough data has been observed and collected, you can stop the test.

To stop a test, in the Locust UI, click the "Stop" button.

Make a note of the time you stopped the test.


# Clean Up

To avoid GCP charges for the driver cluster, you can delete the cluster (and perform other related post-test cleanup activities) with the `teardwonTest` script.
```
scripts/teadownTest.sh
```

The target project requires no cleanup - the project will not incur charges because the devices and cloud function are unused when no driver is running.



# Analyze the Results

The github repo includes a `harvetData` script to perform a basic data collection and analysis for the sample IOT application. The script provides two outputs:

* Frequency distribution of driver-mearured response times
* Frequency distribution of cloud function execution times

The frequency distributions are bucketed to 100 millisecond intervals.

To run the `harvestData` script, from the repo root directory:

```
scripts/harvestData.sh RUN_DIR_NAME START_TIME END_TIME
```

Where
**RUN_DIR_NAME** is the name of directory in $LTK_ROOT/runs to use for the harvested data (will be created if needed).
**START_TIME** is the start time of the test (beginnning of harvest window)
**END_TIME** is the end time of the test (end of harvest window)

START_TIME and END_TIME are in UTC time in the format shown below.

For example
```
scripts/harvestData.sh 100t1 2019-01-04T20:00:00Z 2019-01-04T21:00:00Z
```

The frequency distributions are useful for getting a sense of where performance is clustered and for seeing outliers.

Another possible use for the distributions is for evaluating architectural or implementation changes. For example, adding a database call to the cloud function, or changing the cloud function implementation language. Configuation changes also can be evaluated - for example, the cloud funciton memory allocation.


# Investigating Errors

If you make a change to the code in the tutorial, in some cases you might see setupTest get stuck at the point where it is "waiting for pod to enter running status". If this happens, one way to diagnose the error is to:

1. Open another terminal window
2. Enter the command
```
kubectl get all
```
3. Look at the status of the pod. For example, if the status is ImagePullBackOff, you can get additional details as follows:
```
kubectl describe
```

In other cases, it may be helpful to look in the Stackdriver logs for the driver (GKE container logs) and target (Cloud Function logs, Cloud IOT Device logs).

In the GKE container logs for the `my-ltk-driver` project, you can see the device range used by each worker pod by using the filter "sharded device".


# Understanding Costs

The load test kit can be used to estimate deployment costs for an IOT solution.

The suggested approach for cost evaluation is:


1. Plan and run a test

Make sure you know what you want to evaluate and do a dry run of a test to make sure everything is ready. Decide how many devices to use and the duration of the test. A reasonable duration is one hour.

2. Run the test

3. Check billing in GCP console

Currently it takes 72 hours for charges to appear in the GCP Billing console.

After 72 hours:  
a. Go into Billing in the GCP console  
b. Select the billing account  
c. Select the project (driver or target)  
d. Under Time Range, select Pick a Date and speficy the date of the test  
e. Under Group By, select Product (if more detail is needed, select SKU)  
f. You should see a breakdown of costs  

4. Calculate costs for 24x7 operation with N devices

The cost data for one hour, with 100 devices for example, could be used to calculate the cost for 10,000 devices operating 24x7.

For example, if the one-hour test with 100 devices costs $1 on the target side, the monthly cost can be estimated as 1 * 100 * 720 = $72,000.

Note: Raw billing data is available in BigQuery
https://cloud.google.com/billing/docs/how-to/export-data-bigquery



# Scaling up the Number of Devices

To scale up the number of devices:

1. Create the additional devices using the `createDevices` script

The script is "additive", so the new devices are appended to the existing devicelist.csv.

You need to decide the serial number range for the new devices. For example, if the devicelist.csv contains 1 through 100 (the range used for the tutorial), to add 100 more devices, you can use the command:
```
scripts/createDevices.sh 101 200
```
This command adds the serial numbers 101 through 200 (deviceIds LTK00101 through LTK00200).

2. Update the .env file (optional)

When more devices are added, it may be necessary to increase the number of Locust workers and GKE nodes.

**LTK_NUM_LOCUST_WORKERS** 

Increase LTK_NUM_LOCUST_WORKERS if the additional devices could cause excessive devices on a single worker (based on CPU/memory/thread usage).

**LTK_NUM_GKE_NODES** 

Increase LTK_NUM_GKE_NODES to match LTK_NUM_LOCUST_WORKERS.

**Quota Limits**

When specifying LTK_NUM_GKE_NODES, you need to make sure your GCP compute engine quotas allow the specified number of nodes. The main quota limits are on number of CPUs and number of IN_USE_ADDRESSES (one address is required per cluster node). 

There are quotas at the project and region levels.

```
gcloud compute project-info describe --project my-ltk-driver | grep -C 1 IN_USE_ADDRESSES
gcloud compute regions describe europe-west3 | grep -C 1 IN_USE_ADDRESSES
gcloud compute project-info describe --project my-ltk-driver | grep -C 1 CPU
gcloud compute regions describe europe-west3 | grep -C 1 CPU
```

If there is insufficient quota in one region, you can try another. A listing of regions and zones is available with:
```
gcloud compute zones list
```

3. Run `setupTest`

This will rebuild the master and worker docker images with the added-to `devicelist.csv`.

4. Start a test in Locust

Starting a test in the Locust UI causes the workers to shard the `devicelist.csv`. The sharding calculate the portion of the csv (the "block" of devices) a worker is using. The block offset into the csv is determined by the worker pod's host name, which includes an ordinal (integer 1 to n) uniquely identifying the pod in the replica set. The ordinal is available because the podspec uses the StatefulSet pod type.


# Re-cloning the repo

If you need to re-clone the repository to get a clean copy of the code, you can transfer the `.env` file and `devicelist.csv` to bring over the same environment settings and existing devices.


# Targeting Your IOT Application

Targeting your IOT application requires software development in Python. 

The Python code will simulate the "over-the-network" behavior of your device population. This allows you to evaluate the performance/scalability/cost of your IOT application's backend services accessed over an IPv4/IPv6 network.

1. Planning

* Understand the questions you want to answer with a load test.

* Decide the device behaviors you want to simulate. It's easiest to start with a relatively simple behavior, where it's easy to build/process the payloads sent over the network.

* Decide how you will evaluate success and failure of the device behaviors. These translate into Locust events you need to place in the Python code in `locustfile.py`. The easiest cases are when there is a request/response, where the response (or timeout) would indicate when a failure occurs.

* Understand the data you need to evalaute the results. Long tests with many devices can create very large amounts of data to collect and analyze. In cases where harvesting data is impractical, monitoring capabilities built into the GCP console can be used.


2. Code

Implement the device behaviors in `locustfile.py`. Generally, this involves:

* a Locust "task" for the behavior
* the on_* event handlers called by the Paho client (if using MQTT)
* calling `events.request_success.fire` and `events.request_failure.fire` to record the success/failure of a device behvaior

3. Test

While developing device behaviors, it is easiest to test the behaviors locally. 

This can be done by installing Locust locally and running Locust headless in command line mode as follows (from the repo root):

```
set -a
. .env
PROJECT_ID=$LTK_TARGET_PROJECT_ID
REGION=$LTK_TARGET_REGION
REGISTRY_ID=$LTK_TARGET_REGISTRY_ID
locust --no-web -c 1 -r 1 --only-summary
```

Note:
* Python 2.7 is required for Locust 0.9.0
* Locust 0.9.0 is required for support of the Locust API needed for assigning device IDs to simulated devices

https://docs.locust.io/en/stable/installation.html

If the above instructions install a downlevel version, see
https://stackoverflow.com/questions/49439587/locust-io-setup-teardown-not-executed


4. Deployment

Changes can be deployed by running the `setupTest` script. The script will create new Dockerfiles with the updated `locustfile.py`.




