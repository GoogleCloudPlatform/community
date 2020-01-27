---
title: GKE: Less disruptive node upgrades using Surge Upgrade
description: Learn how Surge Upgrade reduces disruption caused by node upgrades through updating the nodes while running a sample application.
author: tamasr
tags: GKE, Upgrade, Node, Surge Upgrade
date_published: 2020-01-24
---

# Overview

This is a hands on tutorial and demo that demonstrates how GKE helps with reducing disruption of the workloads during node upgrades with the help of Surge Upgrade feature. We will build a demo application that uses some kind of a limited resource (like a connection pool to backend system, which we will emulate only). Then we deploy this application to a GKE cluster and start a client that puts load on the system. Then we’ll upgrade the node pool with and without surge upgrade and measure the error rate on the client side.

# Objectives

* Run a simple demo application that serves HTTP requests. Processing of each request requires access to a resource. Each node of the cluster has access only to a limted pool of resources. If there's no available resources left, the server returns an error.
* Test the application with lower and higher load and observe how error rate increases as the server runs out of resources.
* Upgrade the nodes without using Surge Upgrade. Observe how the temporary loss of capacity causes increased error rates.
* Upgrade the nodes using Surge Upgrade. Observe how error rates remain significantly lower due to the additional capacity provided by the surge node.

# Before you begin

This tutorial builds on top of [Deploying a containerized web application tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app). Please complete that tutorial before starting this one.

# Costs

You will create a GKE cluster for this demo with 3 g1-small VMs. See [VM Instances Pricing](https://cloud.google.com/compute/vm-instance-pricing) for pricing details. The total cost of the demo should be significantly less than $0.1.

# How to make node upgrades less disruptive

## 1. Modify hello-app to work with resources

TODO: add instructions how to just copy the source files over.

### A) Add a resource pool implementation

To extend the application with the use of a limited resource, first you introduce an (emulated) resource pool. In response to each request the application attempts to allocate a resource from the pool. If there is no available resources then the application returns an error. If the allocation is successful, then the application performs some work, then it releases the resource back to the pool.

First add the resource pool and implement related operations.

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

Then change the callback function that serves requests:


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

### B) Implement health signals based on resource availability

This will help the load balancer to route traffic only to pods that have available resources.

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

You also have to register the healthz function under main().

[embedmd]:# (main.go /\tserver.HandleFunc\("\/healthz", healthz\)/)
```go
	server.HandleFunc("/healthz", healthz)
```

### C) Deploy the modified application and verify it

Since you are done with code changes, you can build the application and push it.

```shell
export PROJECT_ID=<your-project-id>
docker build -t gcr.io/${PROJECT_ID}/hello-app:v2-surge .
docker push gcr.io/${PROJECT_ID}/hello-app:v2-surge
```

Once you have the new image pushed, you can update the deployment to use the new image.

```shell
kubectl set image deployment/hello-server hello-app=hello-app:v2-surge
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

Now you can start sending traffic with given frequency. Let’s measure the load in Queries Per Second (QPS) and send the responses received into a file for further processing.

```shell
$ export QPS=40
$ while true; do for N in $(seq 1 $QPS) ; do curl -sS http://35.238.176.215/ >> output 2>&1 &  done; sleep 1; done
```

Checking statistics of the lines in the output file, you can see the error rate.

```shell
$ watch 'TOTAL=$(cat output | wc -l); ERROR1=$(grep "Error" output |  wc -l); RATE=$((ERROR1 * 100 / TOTAL)); echo "Error rate: $ERROR1/$TOTAL (${RATE}%)"; '
```

Anytime you want to "reset statistics” you can just delete the output file.


### B) Add more replicas, configure pod anti affinity, readiness probe and test again

## 3. Test the impact of upgrades on application availability

### A. Upgrade node pool without surge nodes

### B. Upgrade node pool with surge nodes

# Conclusion and follow up steps

# Cleaning up
