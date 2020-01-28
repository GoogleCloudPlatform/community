---
title: GKE - Less disruptive node upgrades using Surge Upgrade
description: Try how Surge Upgrade reduces disruption caused by node upgrades by updating the nodes while running a sample application and measuring its error rate.
author: tamasr
tags: GKE, Upgrade, Node, Surge Upgrade
date_published: 2020-01-24
---

<!-- toc -->

- [Overview](#overview)
- [Objectives](#objectives)
- [Before you begin](#before-you-begin)
- [Costs](#costs)
- [How to make node upgrades less disruptive](#how-to-make-node-upgrades-less-disruptive)
  * [1. Modify hello-app to work with resources](#1-modify-hello-app-to-work-with-resources)
    + [A) Add a resource pool implementation](#a-add-a-resource-pool-implementation)
    + [B) Implement health signals based on resource availability](#b-implement-health-signals-based-on-resource-availability)
    + [C) Deploy the modified application and verify it](#c-deploy-the-modified-application-and-verify-it)
  * [2. Generate load and measure error rate](#2-generate-load-and-measure-error-rate)
    + [A) Run tests with a single pod](#a-run-tests-with-a-single-pod)
    + [B) Add more replicas, configure pod anti affinity, readiness probe](#b-add-more-replicas-configure-pod-anti-affinity-readiness-probe)
  * [3. Test the impact of upgrades on application availability](#3-test-the-impact-of-upgrades-on-application-availability)
    + [A. Upgrade node pool without surge nodes](#a-upgrade-node-pool-without-surge-nodes)
    + [B. Upgrade node pool with surge nodes](#b-upgrade-node-pool-with-surge-nodes)
- [Conclusion](#conclusion)
- [Cleaning up](#cleaning-up)

<!-- tocstop -->

# Overview

This tutorial demonstrates how GKE helps with reducing disruption of the workloads during node upgrades with [Surge Upgrade](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades#surge) feature. You will build a demo application that uses a resource pool with limited number of resources per node. Then you deploy this application to a GKE cluster and start a client that generates load on the system. Finally you will upgrade the node pool with and without surge upgrade and measure the error rate on the client side.

# Objectives

* Run a demo application that serves HTTP requests. Processing of each request requires access to a resource. Each node of the cluster has access only to a limted number of resources. If there's no available resources left, the server returns an error.
* Test the application with lower and higher load and observe how error rate increases as the server runs out of resources.
* Upgrade the nodes without using Surge Upgrade. Observe how the temporary loss of capacity causes increased error rates.
* Upgrade the nodes using Surge Upgrade. Observe how error rates remain significantly lower due to the additional capacity provided by the surge node.

# Before you begin

## Prerequisite

This tutorial builds on top of [Deploying a containerized web application tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app). It is recommended to complete it starting on this one.

If you didn't complete the above tutorial and would like to start this one, you can just clone the repository, so you can rebuild and push images.

```shell
git clone https://github.com/GoogleCloudPlatform/kubernetes-engine-samples
```

## Where to run your terminal

Similar to [Deploying a containerized web application tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app) you can complete this tutorial using [Google Cloud Shell](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_a_use_google_cloud_shell). This is the recommended option. 

As an alternative you can use your own workstation. In this case you will need to install the [required tools](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_b_use_command-line_tools_locally) to be able to perform the steps below.

# Costs

You will create a GKE cluster for this demo with 3 g1-small VMs. See [VM Instances Pricing](https://cloud.google.com/compute/vm-instance-pricing) for pricing details. The total cost of the demo should be less than $0.1.

# How to make node upgrades less disruptive

## 1. Modify hello-app to work with resources

If you don't want to edit the source code manually, you can download the updated version of main.go and overwrite your local copy with it.

```shell
$ curl https://raw.githubusercontent.com/tamasr/community/master/tutorials/gke-less-disruptive-node-upgrades/main.go -O
```

### A) Add a resource pool implementation

To extend the application with the use of a limited resource, first you introduce an (emulated) resource pool. In response to each request the application attempts to allocate a resource from the pool. If there is no available resources then the application returns an error. If the allocation is successful, then the application performs some work, then it releases the resource back to the pool.

First add the resource pool and implement related operations.

<details>
<summary>Expand source code</summary>

[embedmd]:# (main.go /\/\/ Start of resource pool code./ /\/\/ End of resource pool code./)
```go
// Start of resource pool code.

const resourcePoolSize = 50

type resourcePool struct {
	mtx       sync.Mutex
	allocated int
}

var pool resourcePool

func (p *resourcePool) alloc() bool {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	if p.allocated < resourcePoolSize*0.9 {
		p.allocated++
		return true
	}
	return false
}

func (p *resourcePool) release() {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	p.allocated--
}

func (p *resourcePool) hasResources() bool {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	return p.allocated < resourcePoolSize
}

// End of resource pool code.
```
</details>

Then change the callback function that serves requests:

<details>
<summary>Expand source code</summary>

[embedmd]:# (main.go /\tlog.Printf\("Serving request:/ /fmt.Fprintf\(w,.*$/) 
```go
	log.Printf("Serving request: %s", r.URL.Path)
	if !pool.alloc() {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("503 - Error due to tight resource constraints in the pool!\n"))
		return
	} else {
		defer pool.release()
	}
	// Make response take longer to emulate some processing is happening.
	time.Sleep(950 * time.Millisecond)

	fmt.Fprintf(w, "[%v] Hello, world!\n", time.Now())
```
</details>

### B) Implement health signals based on resource availability

This will help the load balancer to route traffic only to pods that have available resources.

<details>
<summary>Expand source code</summary>

[embedmd]:# (main.go /\/\/ Start of healthz code./ /\/\/ End of healthz code./)
```go
// Start of healthz code.

func healthz(w http.ResponseWriter, r *http.Request) {
	// Log to make it simple to validate if healt checks are happening.
	log.Printf("Serving healthcheck: %s", r.URL.Path)
	if pool.hasResources() {
		fmt.Fprintf(w, "Ok\n")
		return
	}

	w.WriteHeader(http.StatusServiceUnavailable)
	w.Write([]byte("503 - Error due to tight resource constraints in the pool!"))
}

// End of healthz code.
```
</details>

You also have to register the healthz function under main().

<details>
<summary>Expand source code</summary>

[embedmd]:# (main.go /\tserver.HandleFunc\("\/healthz", healthz\)/)
```go
	server.HandleFunc("/healthz", healthz)
```
</details>

### C) Deploy the modified application and verify it

Since you are done with code changes, you can build the image and push it.

```shell
export PROJECT_ID=<your-project-id>
docker build -t gcr.io/${PROJECT_ID}/hello-app:v2-surge .
docker push gcr.io/${PROJECT_ID}/hello-app:v2-surge
```

Once you have the new image pushed, you can update the deployment to use the new image.

```shell
kubectl set image deployment/hello-server hello-app=gcr.io/${PROJECT_ID}/hello-app:v2-surge
```

As verification check if the server can respond to requests and if the health check reports the application being healthy. You can print the external IP as below in case you need it.

```shell
$ kubectl get service hello-server
NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
hello-server   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   1d
$ 
$ curl http://35.238.176.215
[2020-01-14 15:05:28.902724343 +0000 UTC] Hello, world!
$ 
$ curl http://35.238.176.215/healthz
Ok
```

## 2. Generate load and measure error rate

You can start sending traffic to your server. As a first step, you will use a single pod to demonstrate when the system can and when it cannot serve requests successfully.

### A) Run tests with a single pod

First, ensure the deployment is running with a single replica:

```shell
$ kubectl scale --replicas=1 deployment/hello-server
deployment.extensions/hello-server scaled
$ 
$ kubectl get pods
NAME                            READY   STATUS    RESTARTS   AGE
hello-server-85c7446cc6-zfpvc   1/1     Running   0          10m
```

Next, download two small shell scripts: one to generate load and another to measure error rate.

```shell
curl https://raw.githubusercontent.com/tamasr/community/master/tutorials/gke-less-disruptive-node-upgrades/generate_load.sh -O
curl https://raw.githubusercontent.com/tamasr/community/master/tutorials/gke-less-disruptive-node-upgrades/print_error_rate.sh -O
```

Now you can start sending traffic with given frequency. Let’s measure the load in Queries Per Second (QPS) and send the responses received into a file for further processing.

```shell
$ kubectl get service hello-server
NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
hello-server   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   25d
$ export IP=35.238.176.215
$ export QPS=40
$ ./generate_load.sh $IP $QPS 2>&1
```

The above script is simply using curl to send traffic.

<details>
<summary>Expand script</summary>

[embedmd]:# (generate_load.sh)
```sh
#!/bin/bash

# Usage:
#  generate_load.sh <IP> <QPS>_
#
# Sends QPS number of HTTP requests every second to http://<IP>/ URL.
# Saves the responses into the current directory to a file named "output".

IP=$1
QPS=$2

while true
  do for N in $(seq 1 $QPS)
    do curl -sS http://${IP}/ >> output &
    done
  sleep 1
done
```
</details>

To check error rates you can run:

```shell
$ watch ./print_error_rate.sh
```

The above script calculates error rates based on the number of errors 

<details>
<summary>Expand script</summary>

[embedmd]:# (print_error_rate.sh)
```sh
#!/bin/bash

TOTAL=$(cat output | wc -l); ERROR1=$(grep "Error" output |  wc -l)
RATE=$((ERROR1 * 100 / TOTAL))
echo "Error rate: $ERROR1/$TOTAL (${RATE}%)"
```
</details>

Anytime you want to "reset statistics” you can just delete the output file.

You can test now the failure case, when the load cannot be served by a single pod.

```shell
$ rm output
$ export QPS=60
$ ./generate_load.sh $IP $QPS 2>&1
```

There should be an increased error rate.

```shell
$ ./print_error_rate.sh
Error rate: 190/1080 (17%)
```

### B) Add more replicas, configure pod anti affinity, readiness probe

The changes below can be applied in one step by running

```shell
kubectl replace -f hello_server_with_resource_pool.yaml
```

The previous step demonstrated how a single server handles the load. By scaling up the application and increasing the load on it, you can see how the system behaves, when load balancing becomes relevant. 

You can change the number of replicas to three. To ensure each replica is scheduled on a different node, you can configure [pod anti affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/) as well.

<details>
<summary>Expand yaml fragment</summary>

[embedmd]:# (hello_server_with_resource_pool.yaml /^.*# Pod anti affinity config START/ /# Readiness probe config END/)
```yaml
      # Pod anti affinity config START
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - hello-server
            topologyKey: kubernetes.io/hostname
      # Pod anti affinity config END
      containers:
      - image: gcr.io/tamasr-gke-dev/hello-app:v2-surge
        name: hello-app
        # Readiness probe config START
        readinessProbe:
          failureThreshold: 1 
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 1
          periodSeconds: 1
          successThreshold: 1
          timeoutSeconds: 1
        # Readiness probe config END
```
</details>

To ensure requests are routed to replicas that have capacity available, you need to configure [readiness probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-readiness-probes).

<details>
<summary>Expand yaml fragment</summary>

[embedmd]:# (hello_server_with_resource_pool.yaml /^.*# Readiness probe config START/ /# Readiness probe config END/)
```yaml
        # Readiness probe config START
        readinessProbe:
          failureThreshold: 1 
          httpGet:
            path: /healthz
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 1
          periodSeconds: 1
          successThreshold: 1
          timeoutSeconds: 1
        # Readiness probe config END
```
</details>

*Note: Using this sample application the addition of the readiness probe does not improve the availability noticeably, since both the generated load and processing of each request is fairly deterministic and close enough to be evenly distributed among nodes. In a different situation the role of the readiness probe could be more significant. Also the right number of replicas and the signal when a pod would be considered healthy would require carefully optimization to match the incoming traffic.*

Now generate load the system can handle. One pod has a resource pool with the size of 50 and close to 1 second processing time. Also our health checks consider a pod healthy only if the node pool is less than 90% utilized (has less than 45 resources in use). This gives us a total of ~3x45 = 135 QPS load the system can handle. 120 QPS will be the choice for this test.

```shell
$ export QPS=120
$ ./generate_load.sh $IP $QPS 2>&1
```

It is likely that you see some errors in this case, although the rate should be relatively low. In spite of our efforts with replication and health checks there might be requests already in flight at the time a replica runs out of resources, so the load balancer won’t be able to prevent the requests from being rejected by the pod.

```shell
$ ./print_error_rate.sh
Error rate: 190/18960 (1%)
```

As demonstration for the failure case, you can increase QPS to 160.

```shell
$ export QPS=160
$ ./generate_load.sh $IP $QPS 2>&1
```

The error rate increased:

```shell
$ ./print_error_rate.sh
Error rate: 1901/11840 (16%)
```

## 3. Test the impact of upgrades on application availability

This section is to demonstrate how the loss of capacity may hurt the service during a node upgrade if there is no extra capacity made available in the form of surge nodes. Before Surge Upgrade was introduced every upgrade of a node pool involved the temporary loss of a single node, since every node had to be recreated with a new image with the new version. Some customers were increasing the size of the node pool by one before upgrades then restored the size after successful upgrade, however this is error prone manual work. Surge Upgrade makes it possible to do this automatically and reliably.

### A. Upgrade node pool without surge nodes

You can start with the case without surge node. Make sure your node pool has zero surge nodes configured.

```shell
$ gcloud beta container node-pools update default-pool --max-surge-upgrade=0 --max-unavailable-upgrade=1 --cluster=standard-cluster-1
Updating node pool default-pool...done.                                        
Updated [https://container.googleapis.com/v1beta1/projects/tamasr-gke-dev/zones/us-central1-a/clusters/standard-cluster-1/nodePools/default-pool].
```

You can now clear the output file you got from earlier runs and start watching the error rate.

```shell
$ rm output
$
$ watch ./print_error_rate.sh
```

In a separate terminal you can watch the state of the nodes and pods to follow the upgrade process closely.

```shell
$ watch 'kubectl get nodes,pods'
```

You can start sending some load now.

```shell
$ export QPS=120
$ ./generate_load.sh $IP $QPS 2>&1
```

Then you can start an upgrade (in another terminal).

```shell
$ gcloud container clusters upgrade standard-cluster-1 --cluster-version=1.13 --node-pool=default-pool
```

*Note on cluster-version used. It is not possible to upgrade nodes to a higher version than the master, but it is possible to downgrade them. In this example you (most likely) started with a cluster that had nodes already on the master version. In that case you can pick a lower version (minor or patch) to perform a downgrade. In the next step you can bring the nodes back to their original version with an upgrade.*

Notice that the pod on the first node to be updated gets evicted and remains unschedulable while GKE is recreating the node (since there is no node available to schedule the pod on). This reduces the capacity of the entire cluster and it leads to higher error rate. (~20% instead of earlier ~1% in your tests with the same QPS.) The same happens with subsequent nodes as well (i.e. the evicted pod remains unschedulable until the node upgrade finishes and the node becomes READY).

At the end of the upgrade you should see high error rate. Something like:

```shell
Error rate: 25690/97080 (26%)
```

### B. Upgrade node pool with surge nodes

With surge upgrades it is possible to upgrade nodes in a way when the node pool won’t lose any capacity by setting maxUnavailble to 0 and maxSurge to greater than 0.

```shell
$ gcloud beta container node-pools update default-pool --max-surge-upgrade=1 --max-unavailable-upgrade=0 --cluster=standard-cluster-1
Updating node pool default-pool...done.                                        
Updated [https://container.googleapis.com/v1beta1/projects/tamasr-gke-dev/zones/us-central1-a/clusters/standard-cluster-1/nodePools/default-pool].
```

You can clear the output you got from earlier runs and watch the error rate.

```shell
$ rm output
$
$ watch ./print_error_rate.sh
```

In a separate terminal you can watch the state of the nodes and pods again to follow the upgrade process.

```shell
$ watch 'kubectl get nodes,pods'
```

You can start sending some load again.

```shell
$ export QPS=120
$ ./generate_load.sh $IP $QPS 2>&1
```

Then you can start an upgrade (in another terminal).

```shell
$ gcloud container clusters upgrade standard-cluster-1 --cluster-version=1.14 --node-pool=default-pool
```

*Note on cluster-version. You can select here the version of your master. For more see the note on cluster-version at the previous section*

There should be a significantly lower error rate measured for this upgrade.

```shell
Error rate: 3386/81956 (4%)
```

Notice that how pods remain in running state while GKE is bringing up and registering the new node.
Also notice that the error rate was still higher than the one we saw when there was no upgrade running. This points out an important detail that the **pods still need to be moved from one node to another**. Although we have sufficient compute capacity to schedule an evicted pod, stopping and starting it up again takes time, which causes disruption. 

The error rate can be reduced further by increasing the number of replicas, so workload can be served even if a pod is restarted. Also you can declare the number of pods required to serve requests using [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) (PDB). With PDBs you can cover more failure cases. For example in case of an involuntary disruption (like a node error) pod eviction won't start unless the minimum number of pods declared by PDB can be maintained.


# Conclusion

Kubernetes node upgrades are disruptive since they cause pods to be moved and restarted. One key factor that may reduce the availability of an applications if there is no sufficient compute capacity to get pods, which were evicted due to an upgrade, scheduled immediately, so pods may remain unscheduled and unable to serve traffic. GKE Surge Upgrade solves this problem by bringing up additional (surge) nodes, so insufficient compute capacity cannot cause disruption. Other factors, for example the time it takes to restart a pod would still contribute to disruption.


# Cleaning up

Deleting the cluster removes all resources used in this demo.

```shell
$ gcloud container clusters delete standard-cluster-1
```

