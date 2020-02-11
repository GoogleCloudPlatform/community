---
title: Use surge upgrades to decrease disruptions from GKE node upgrades
description: Learn how surge upgrades reduce disruption caused by node upgrades by updating the nodes while running a sample application and measuring its error rate.
author: tamasr
tags: GKE, upgrade, node, surge upgrade
date_published: 2020-02-12
---

This tutorial demonstrates how Google Kubernetes Engine (GKE) helps with reducing disruption of the workloads during node
upgrades with [surge upgrades](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades#surge). In this 
tutorial, you build a demonstration application that uses a resource pool with a limited number of resources per node. You 
then deploy this application to a GKE cluster and start a client that generates load on the system. Finally, you upgrade the
node pool with and without surge upgrades and measure the error rate on the client side.

## Objectives

* Run a demonstration application that serves HTTP requests. Processing of each request requires access to a resource. Each
  node of the cluster has access only to a limted number of resources. If there's no available resources left, the server 
  returns an error.
* Test the application with lower and higher load and observe how error rate increases as the server runs out of resources.
* Upgrade the nodes without surge upgrades. Observe how the temporary loss of capacity causes increased error rates.
* Upgrade the nodes using surge upgrades. Observe how error rates remain significantly lower due to the additional capacity
  provided by the surge node.

## Before you begin

We recommend that you use 
[Cloud Shell](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_a_use_google_cloud_shell) 
to run the commands in this tutorial. As an alternative, you can use your own workstation to run commands locally. in which
case you would need to install the
[required tools](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_b_use_command-line_tools_locally).

This tutorial requires a Google Cloud project. You can use an existing project or 
[create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

This tutorial follows the
[Deploying a containerized web application](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app) tutorial.
We recommended that you complete the previous tutorial before starting this one.

If you didn't complete the
[Deploying a containerized web application](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app) 
tutorial and would like to immediately start this tutorial, you can run the following commands to create a cluster with
the `hello-app` application running on it:

1.  Clone the repository and navigate to the app directory:

        git clone https://github.com/GoogleCloudPlatform/kubernetes-engine-samples
        cd kubernetes-engine-samples/hello-app

1.  Set a variable for the
    [project ID](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects)
    by replacing `[PROJECT_ID]` with your project ID in this command:

        export PROJECT_ID=[PROJECT_ID]
        
1.  Build and push the image:

        docker build -t gcr.io/${PROJECT_ID}/hello-app:v1 .
        gcloud auth configure-docker
        docker push gcr.io/${PROJECT_ID}/hello-app:v1

1.  Create a cluster

        gcloud config set project $PROJECT_ID
        gcloud config set compute/zone us-central1-a
        gcloud container clusters create hello-cluster --machine-type=g1-small --num-nodes=3
	
1.  Deploy and expose the application:

        gcloud container clusters get-credentials hello-cluster
        kubectl create deployment hello-web --image=gcr.io/${PROJECT_ID}/hello-app:v1
        kubectl expose deployment hello-web --type=LoadBalancer --port 80 --target-port 8080

## Costs

In this tutorial, you create a GKE cluster with 3 g1-small virtual machine instances. The total cost of the resources used
during for this tutorial is estimated to be less than $0.10. For details, see
[VM instances pricing](https://cloud.google.com/compute/vm-instance-pricing).

## Modify hello-app to work with resources

In this section, you modify the `hello-app` source code.

If you don't want to edit the source code manually, you can download the updated version of `main.go` and overwrite your 
local copy with it.

```shell
$ curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/main.go -O
```

### Add a resource pool implementation

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

### Implement health signals based on resource availability

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

### Deploy the modified application and verify it

Since you are done with code changes, you can build the image and push it.

```shell
export PROJECT_ID=<your-project-id>
docker build -t gcr.io/${PROJECT_ID}/hello-app:v2-surge .
docker push gcr.io/${PROJECT_ID}/hello-app:v2-surge
```

Once you have the new image pushed, you can update the deployment to use the new image.

```shell
kubectl set image deployment/hello-web hello-app=gcr.io/${PROJECT_ID}/hello-app:v2-surge
```

As verification check if the server can respond to requests and if the health check reports the application being healthy. You can print the external IP as below in case you need it.

```shell
$ kubectl get service hello-web
NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
hello-web   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   1d
$ 
$ curl http://35.238.176.215
[2020-01-14 15:05:28.902724343 +0000 UTC] Hello, world!
$ 
$ curl http://35.238.176.215/healthz
Ok
```

## Generate load and measure error rate

You can start sending traffic to your server. As a first step, you will use a single pod to demonstrate when the system can and when it cannot serve requests successfully.

### Run tests with a single pod

First, ensure the deployment is running with a single replica:

```shell
$ kubectl scale --replicas=1 deployment/hello-web
deployment.extensions/hello-web scaled
$ 
$ kubectl get pods
NAME                            READY   STATUS    RESTARTS   AGE
hello-web-85c7446cc6-zfpvc   1/1     Running   0          10m
```

Next, download two small shell scripts: one to generate load and another to measure error rate.

```shell
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/generate_load.sh -O
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/print_error_rate.sh -O
chmod u+x generate_load.sh print_error_rate.sh
```

Now you can start sending traffic with given frequency. Let’s measure the load in Queries Per Second (QPS) and send the responses received into a file for further processing.

```shell
$ kubectl get service hello-web
NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
hello-web   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   25d
$ export IP=35.238.176.215
$ export QPS=40
$ ./generate_load.sh $IP $QPS 2>&1
```

The above script is simply using curl to send traffic.

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

To check error rates you can run:

```shell
$ watch ./print_error_rate.sh
```

The above script calculates error rates based on the number of errors 

[embedmd]:# (print_error_rate.sh)
```sh
#!/bin/bash

TOTAL=$(cat output | wc -l); ERROR1=$(grep "Error" output |  wc -l)
RATE=$((ERROR1 * 100 / TOTAL))
echo "Error rate: $ERROR1/$TOTAL (${RATE}%)"
```

Anytime you want to "reset statistics” you can just delete the output file.

You can test now the failure case, when the load cannot be served by a single pod.

```shell
# first stop generate_load.sh by Ctrl+C
$ rm output
$ export QPS=60
$ ./generate_load.sh $IP $QPS 2>&1
```

There should be an increased error rate.

```shell
$ ./print_error_rate.sh
Error rate: 190/1080 (17%)
```

### Add more replicas, configure pod anti affinity, readiness probe

The previous step demonstrated how a single server handles the load. By scaling up the application and increasing the load on it, you can see how the system behaves, when load balancing becomes relevant. 

The changes below can be applied in one step running the below commands.

```shell
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/hello_server_with_resource_pool.yaml -O
kubectl replace -f hello_server_with_resource_pool.yaml
```

You can change the number of replicas to three. To ensure each replica is scheduled on a different node, you can configure [pod anti affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/) as well.

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
                - hello-web
            topologyKey: kubernetes.io/hostname
      # Pod anti affinity config END
      containers:
      - image: gcr.io/<YOUR_PROJECT_ID>/hello-app:v2-surge
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

To ensure requests are routed to replicas that have capacity available, you need to configure [readiness probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-readiness-probes).

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

Note: Using this sample application the addition of the readiness probe does not improve the availability noticeably, since both the generated load and processing of each request is fairly deterministic and close enough to be evenly distributed among nodes. In a different situation the role of the readiness probe could be more significant. Also the right number of replicas and the signal when a pod would be considered healthy would require carefully optimization to match the incoming traffic.

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

## Test the impact of upgrades on application availability

This section is to demonstrate how the loss of capacity may hurt the service during a node upgrade if there is no extra capacity made available in the form of surge nodes. Before Surge Upgrade was introduced every upgrade of a node pool involved the temporary loss of a single node, since every node had to be recreated with a new image with the new version. Some customers were increasing the size of the node pool by one before upgrades then restored the size after successful upgrade, however this is error prone manual work. Surge Upgrade makes it possible to do this automatically and reliably.

### Upgrade node pool without surge nodes

In this section of the tutorial you will need to open multiple terminals. Where it is relevant, the commands will be marked. For example before a command that needs to run in the first terminal you opened, there is a marker: **(TERMINAL-1)**

You can start with the case without surge node. Make sure your node pool has zero surge nodes configured.

```shell
$ gcloud beta container node-pools update default-pool --max-surge-upgrade=0 --max-unavailable-upgrade=1 --cluster=hello-cluster
```

You can now clear the output file you got from earlier runs and start watching the error rate. **(TERMINAL-1)**

```shell
$ rm output
$
$ watch ./print_error_rate.sh
```

In a separate terminal **(TERMINAL-2)** you can watch the state of the nodes and pods to follow the upgrade process closely.

```shell
$ watch 'kubectl get nodes,pods -o wide'
```

You can start sending some load now. **(TERMINAL-3)**

```shell
$ export QPS=120
$ ./generate_load.sh $IP $QPS 2>&1
```

Then you can start an upgrade **(TERMINAL-4)**. **Warning:** this operation may take 10-15 minutes to complete.

```shell
# find a lower minor version
$ V=$(gcloud container node-pools  describe default-pool --cluster=hello-cluster | grep version | sed -E "s/version: 1\.([^\.]+)\..*/\1/" | tr -d '\n');  V=$((V-1)); echo "1.$V"
$ gcloud container clusters upgrade hello-cluster --cluster-version=$V --node-pool=default-pool
```

Note on cluster-version used. It is not possible to upgrade nodes to a higher version than the master, but it is possible to downgrade them. In this example you (most likely) started with a cluster that had nodes already on the master version. In that case you can pick any lower version (minor or patch) to perform a downgrade. In the next step you can bring the nodes back to their original version with an upgrade.

Notice that the pod on the first node to be updated gets evicted and remains unschedulable while GKE is recreating the node (since there is no node available to schedule the pod on). This reduces the capacity of the entire cluster and it leads to higher error rate. (~20% instead of earlier ~1% in your tests with the same QPS.) The same happens with subsequent nodes as well (i.e. the evicted pod remains unschedulable until the node upgrade finishes and the node becomes READY).

At the end of the upgrade you should see high error rate **(TERMINAL-1)**. Something like:

```shell
Error rate: 25690/97080 (26%)
```

### Upgrade node pool with surge nodes

In this section of the tutorial, again you will need to open multiple terminals. Where it is relevant, the commands will be marked. For example before a command that needs to run in the first terminal you opened, there is a marker: **(TERMINAL-1)**

With surge upgrades it is possible to upgrade nodes in a way when the node pool won’t lose any capacity by setting maxUnavailble to 0 and maxSurge to greater than 0.

```shell
$ gcloud beta container node-pools update default-pool --max-surge-upgrade=1 --max-unavailable-upgrade=0 --cluster=hello-cluster
```

You can clear the output you got from earlier runs and watch the error rate. **(TERMINAL-1)**

```shell
$ rm output
$
$ watch ./print_error_rate.sh
```

In a separate terminal **(TERMINAL-2)** you can watch the state of the nodes and pods again to follow the upgrade process.

```shell
$ watch 'kubectl get nodes,pods -o wide'
```

You can start sending some load again. **(TERMINAL-3)**

```shell
$ export QPS=120
$ ./generate_load.sh $IP $QPS 2>&1
```

Then you can start an upgrade **(TERMINAL-4)**. **Warning:** this operation may take 10-15 minutes to complete.

```shell
# find the master version
$ V=$(gcloud container clusters describe hello-cluster | grep "version:" | sed "s/version: //")
$ gcloud container clusters upgrade hello-cluster --cluster-version=$V --node-pool=default-pool
```

Note on cluster-version. You can select here the version of your master. For more see the note on cluster-version at the previous section

There should be a significantly lower error rate measured for this upgrade. **(TERMINAL-1)**

```shell
Error rate: 3386/81956 (4%)
```

Notice that how pods remain in running state while GKE is bringing up and registering the new node.
Also notice that the error rate was still higher than the one we saw when there was no upgrade running. This points out an important detail that the **pods still need to be moved from one node to another**. Although we have sufficient compute capacity to schedule an evicted pod, stopping and starting it up again takes time, which causes disruption. 

The error rate can be reduced further by increasing the number of replicas, so workload can be served even if a pod is restarted. Also you can declare the number of pods required to serve requests using [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) (PDB). With PDBs you can cover more failure cases. For example in case of an involuntary disruption (like a node error) pod eviction won't start until the ongoing disruption is over (like the failed node is repaired), so restarting the pod won't cause the number of replicas to be lower than required by PDB.


## Conclusion

Kubernetes node upgrades are disruptive since they cause pods to be moved and restarted. One key factor that may reduce the availability of an applications if there is no sufficient compute capacity to get pods, which were evicted due to an upgrade, scheduled immediately, so pods may remain unscheduled and unable to serve traffic. GKE Surge Upgrade solves this problem by bringing up additional (surge) nodes, so insufficient compute capacity cannot cause disruption. Other factors, for example the time it takes to restart a pod would still contribute to disruption.


## Cleaning up

Deleting the cluster removes all resources used in this demo.

```shell
$ gcloud container clusters delete hello-cluster
```
