---
title: Use surge upgrades to decrease disruptions from GKE node upgrades
description: Run a sample application and measure its error rate to learn how surge upgrades reduce disruption caused by GKE node upgrades.
author: tamasr
tags: GKE, upgrade, node, surge upgrade
date_published: 2020-02-12
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial demonstrates how Google Kubernetes Engine (GKE) helps with reducing disruption of the workloads during node
upgrades with [surge upgrades](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades#surge). In this 
tutorial, you build a demonstration application that uses a resource pool with a limited number of resources per node. You 
then deploy this application to a GKE cluster and start a client that generates load on the system. Finally, you upgrade the
node pool with and without surge upgrades and measure the error rate on the client side.

## Objectives

* Run a demonstration application that serves HTTP requests. Processing of each request requires access to a resource. Each
  node of the cluster has access only to a limited number of resources. If there are no available resources left, the server 
  returns an error.
* Test the application with lower and higher load and observe how error rate increases as the server runs out of resources.
* Upgrade the nodes without surge upgrades. Observe how the temporary loss of capacity causes increased error rates.
* Upgrade the nodes using surge upgrades. Observe how error rates decrease because of the additional capacity
  provided by the surge node.

## Before you begin

We recommend that you use
[Cloud Shell](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_a_use)
to run the commands in this tutorial. As an alternative, you can use your own workstation to run commands locally, in which
case you would need to install the
[required tools](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app#option_b_use_command-line_tools_locally).

This tutorial requires a Google Cloud project. You can use an existing project or 
[create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

This tutorial follows the
[Deploying a containerized web application](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app) tutorial.
We recommend that you complete the previous tutorial before starting this one. If you didn't complete the
[Deploying a containerized web application](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app) 
tutorial and would like to immediately start this tutorial, then you can run the following commands to create a cluster with
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
for this tutorial is estimated to be less than $0.10. For details, see
[VM instances pricing](https://cloud.google.com/compute/vm-instance-pricing).

## Modify hello-app to work with resources

In this section, you modify the `hello-app` source code to use a limited resource and provide health signals based on resource availability.

If you don't want to edit the source code manually, you can download the updated version of
[`main.go`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/gke-less-disruptive-node-upgrades/main.go)
and overwrite your local copy with it:

```shell
$ curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/main.go -O
```

### Add a resource pool implementation

To extend the application with the use of a limited resource, you introduce an emulated resource pool. In response 
to each request, the application attempts to allocate a resource from the pool. If there are no available resources, then
the application returns an error. If the allocation is successful, then the application performs some work, and then it 
releases the resource back to the pool.

Add the resource pool and implement related operations:

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

Change the callback function that serves requests:

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

Health signals based on resource availability help the load balancer to route traffic only to pods that have available 
resources.

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

Register the `healthz` function under `main()`:

[embedmd]:# (main.go /\tserver.HandleFunc\("\/healthz", healthz\)/)
```go
	server.HandleFunc("/healthz", healthz)
```

### Deploy the modified application

Since you are done with source code changes, you can build, push, and deploy the new image.

1.  Set a variable for your project ID, replacing `[PROJECT_ID]` with your project ID:

        export PROJECT_ID=[PROJECT_ID]

1.  Build the new image:

        docker build -t gcr.io/${PROJECT_ID}/hello-app:v2-surge .
	
1.  Push the new image:

        docker push gcr.io/${PROJECT_ID}/hello-app:v2-surge

1.  Update the deployment to use the new image:

        kubectl set image deployment/hello-web hello-app=gcr.io/${PROJECT_ID}/hello-app:v2-surge

### Verify the modified application

Verify that the server can respond to requests and whether the health check reports the application being healthy. 

1.  Get information about the service:

        kubectl get service hello-web
	
    The output should look like this:
    
        NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
        hello-web   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   1d
	
1.  Verify that the server can respond to requests:

        curl http://35.238.176.215
	
    The output should look like this:
    
        [2020-01-14 15:05:28.902724343 +0000 UTC] Hello, world!

1.  Check the health of the application:

        curl http://35.238.176.215/healthz
	
    The response should be `Ok`.

## Generate load and measure error rate

After verifying that the application can respond, you can start sending traffic to your server. As a first step, you  
use a single pod to demonstrate when the system can and cannot serve requests successfully.

### Run tests with a single pod

#### Ensure that the deployment is running with a single replica

1.  Scale the deployment to 1 replica:

        kubectl scale --replicas=1 deployment/hello-web
	
    Output:
    
        deployment.extensions/hello-web scaled

1.  Get information about the single pod:

        $ kubectl get pods
	
    Output:
    
        NAME                            READY   STATUS    RESTARTS   AGE
        hello-web-85c7446cc6-zfpvc   1/1     Running   0          10m

#### Download shell scripts

Download two small shell scripts, one to generate load and another to measure error rate:

```shell
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/generate_load.sh -O
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/print_error_rate.sh -O
chmod u+x generate_load.sh print_error_rate.sh
```

#### Send traffic to the pod

Now you can start sending traffic with a given frequency, measured in queries per second (QPS). 

1.  Get information about the service:

        kubectl get service hello-web
	
    The output should look like this:
    
        NAME           TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
        hello-web   LoadBalancer   10.12.5.60   35.238.176.215   80:32309/TCP   25d

1.  Set variables for the IP address and number of queries per second:

        export IP=35.238.176.215
        export QPS=40

1.  Run the `generate_load` script, which uses `curl` to send traffic and sends the responses to a file for further
    processing:

        ./generate_load.sh $IP $QPS 2>&1

1.  Check the error rate with the `print_error_rate.sh` script, which calculates error rates based on the number of errors:

        watch ./print_error_rate.sh


#### Content of the `generate_load` script

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

#### Content of the `print_error_rate` script

[embedmd]:# (print_error_rate.sh)
```sh
#!/bin/bash

TOTAL=$(cat output | wc -l); ERROR1=$(grep "Error" output |  wc -l)
RATE=$((ERROR1 * 100 / TOTAL))
echo "Error rate: $ERROR1/$TOTAL (${RATE}%)"
```

#### Test the failure case

Test the failure case by sending more traffic than a single pod can serve.

1.  Stop the `generate_load` script by pressing Ctrl+C.

1.  Reset the error rate statistics by deleting the output file:

        rm output

1.  Set the `QPS` variable to a higher value to increase the number of queries per second:

        export QPS=60

1.  Run the script with the new value:

        ./generate_load.sh $IP $QPS 2>&1

1.  Check the error rate, which should be greater:

        ./print_error_rate.sh
	
    You should see output like the following:
    
        Error rate: 190/1080 (17%)

### Run tests with more replicas

The previous section demonstrated how a single server handles the load. By scaling up the application and increasing the 
load on it, you can see how the system behaves when load balancing becomes relevant. 

The following section describes how to make a series of changes to the configuration in the 
`hello_server_with_resource_pool.yaml` file, but you can apply all of the changes in one step by running the following two
commands:

```shell
curl https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/gke-less-disruptive-node-upgrades/hello_server_with_resource_pool.yaml -O
kubectl replace -f hello_server_with_resource_pool.yaml
```

#### Add more replicas, configure pod anti-affinity, readiness probe

You can change the number of replicas to 3 in the `spec` section of the `hello_server_with_resource_pool.yaml` file:

```yaml
spec:
  replicas: 3 
  selector:
    matchLabels:
      app: hello-web
```

To ensure that each replica is scheduled on a different node, use
[pod anti-affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/), as configured in this section of 
the `hello_server_with_resource_pool.yaml` file: 

[embedmd]:# (hello_server_with_resource_pool.yaml /^.*# Pod anti affinity config START/ /# Pod anti affinity config END/)
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
```

To ensure that requests are routed to replicas that have capacity available, use
[readiness probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-readiness-probes), as configured in this section of the `hello_server_with_resource_pool.yaml` file:

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

For this sample application, the addition of the readiness probe does not improve the availability noticeably, since 
both the generated load and processing of each request are fairly deterministic and close enough to being evenly distributed
among nodes. In a different situation, the role of the readiness probe could be more significant. Also, the right number of 
replicas and the signal when a pod would be considered healthy would require careful optimization to match the incoming 
traffic.

#### Generate traffic that the system can handle

One pod has a resource pool of size 50 and ~1 second processing time. The health checks consider a pod healthy only if the 
node pool is less than 90% utilized (has less than 45 resources in use). This gives a total of ~3x45 = 135 QPS load that
the system can handle. Use 120 QPS for this test.

1.  Set the number of queries per second:

        export QPS=120
	
1.  Run the `generate_load` script:

        ./generate_load.sh $IP $QPS 2>&1

    You probably see some errors in this case, although the rate should be relatively low. In spite of the replication and
    health checks, there might be requests already in transit when a replica runs out of resources, so the load balancer 
    won’t be able to prevent the requests from being rejected by the pod.

1.  Check the error rate:

        ./print_error_rate.sh

    You probably see some errors in this case, although the rate should be relatively low. For example, 
    the output may look something like this:
    
        Error rate: 190/18960 (1%)
    
    In spite of the replication and health checks, there might be requests already in transit when a replica runs out of 
    resources, so the load balancer won’t be able to prevent the requests from being rejected by the pod.
    
#### Demonstrate the failure case with a higher traffic rate

As demonstration for the failure case, you can increase QPS to 160.

1.  Set the number of queries per second:

        export QPS=160
	
1.  Run the `generate_load` script:

        ./generate_load.sh $IP $QPS 2>&1

1.  Check the error rate:

        ./print_error_rate.sh
	
    The error rate should have increased, with output like the following:

        Error rate: 1901/11840 (16%)

## Test the impact of upgrades on application availability

This section demonstrates how the loss of capacity may hurt the service during a node upgrade if there is no extra 
capacity made available in the form of surge nodes. Before surge upgrades were introduced, every upgrade of a node pool
involved the temporary loss of a single node, because every node had to be recreated with a new image with the new version. 

Some users were increasing the size of the node pool by one before upgrades and then restoring the size after a 
successful upgrade. However, this is error-prone manual work. Surge upgrades makes it possible to do this automatically and
reliably.

### Upgrade the node pool without surge nodes

In this section of the tutorial, you open multiple terminals. Where it is relevant, the commands are labeled. 
For example, the following precedes commands that you enter in the first terminal that you open: "In **terminal 1**:" 

1.  To begin without surge upgrades, make sure that your node pool has zero surge nodes configured:

        $ gcloud beta container node-pools update default-pool --max-surge-upgrade=0 --max-unavailable-upgrade=1 --cluster=hello-cluster

1.  Clear the output file from earlier runs and start watching the error rate.

    In **terminal 1**: 

        rm output
        watch ./print_error_rate.sh

1.  Watch the state of the nodes and pods to follow the upgrade process closely.

    In **terminal 2**:

        watch 'kubectl get nodes,pods -o wide'

1.  Start sending traffic.

    In **terminal 3**:

        export QPS=120
        ./generate_load.sh $IP $QPS 2>&1

1.  Find a lower minor version and then start an upgrade.

    In **terminal 4**:
    
        V=$(gcloud container node-pools  describe default-pool --cluster=hello-cluster | grep version | sed -E "s/version: 1\.([^\.]+)\..*/\1/" | tr -d '\n');  V=$((V-1)); echo "1.$V"
        gcloud container clusters upgrade hello-cluster --cluster-version=$V --node-pool=default-pool

    This operation may take 10-15 minutes to complete.

    Note on `cluster-version` used: It is not possible to upgrade nodes to a higher version than the master, but it is 
    possible to downgrade them. In this example, you most likely started with a cluster that had nodes already on the master 
    version. In that case, you can pick any lower version (minor or patch) to perform a downgrade. In the next section, you 
    can bring the nodes back to their original version with an upgrade.

    Notice that the pod on the first node to be updated gets evicted and remains unschedulable while GKE is re-creating the
    node (since there is no node available to schedule the pod on). This reduces the capacity of the entire cluster and 
    leads to a higher error rate (~20% instead of ~1% in your earlier tests with the same traffic). The same happens with 
    subsequent nodes, as well (that is, the evicted pod remains unschedulable until the node upgrade finishes and the node 
    becomes ready).

    When the upgrade is complete, you should see a higher error rate in **terminal 1**, like the following:

        Error rate: 25690/97080 (26%)

### Upgrade the node pool with surge nodes

With surge upgrades, you can upgrade nodes so that the node pool doesn’t lose any capacity. 

1.  Configure the node pool:

        gcloud beta container node-pools update default-pool --max-surge-upgrade=1 --max-unavailable-upgrade=0 --cluster=hello-cluster
	
1.  Clear the output from earlier runs and watch the error rate.

    In **terminal 1**:

        rm output
        watch ./print_error_rate.sh

1.  Watch the state of the nodes and pods to follow the upgrade process.

    In **terminal 2**:

        watch 'kubectl get nodes,pods -o wide'

1.  Start sending traffic:

    In **terminal 3**:

        export QPS=120
        ./generate_load.sh $IP $QPS 2>&1

1.  Find the master version and start an upgrade.

    In **terminal 4**:

        V=$(gcloud container clusters describe hello-cluster | grep "version:" | sed "s/version: //")
        gcloud container clusters upgrade hello-cluster --cluster-version=$V --node-pool=default-pool

    This operation may take 10-15 minutes to complete.

    Note on `cluster-version`: In the first command, you can use version of your master.

    When the upgrade is complete, you should see a lower error rate in **terminal 1**, like the following:

        Error rate: 3386/81956 (4%)

Notice that the pods remain in the running state while GKE is bringing up and registering a new node. Also notice that the 
error rate was still higher than the one we saw when there was no upgrade running. This points out an important detail that 
the *pods still need to be moved from one node to another*. Although we have sufficient compute capacity to schedule an
evicted pod, stopping and starting it up again takes time, which causes disruption. 

The error rate can be reduced further by increasing the number of replicas, so workload can be served even if a pod is
restarted. Also, you can declare the number of pods required to serve requests using
[PodDisruptionBudget (PDB)](https://kubernetes.io/docs/tasks/run-application/configure-pdb/). With a pod disruption budget, 
you can cover more failure cases. For example, in the case of an involuntary disruption (like a node error), pod eviction 
won't start until the ongoing disruption is over (for example, the failed node is repaired), so restarting the pod won't 
cause the number of replicas to be lower than required by PDB.

## Conclusion

Kubernetes node upgrades are disruptive because they cause pods to be moved and restarted. This is a key factor that may 
reduce the availability of an application if there is not sufficient compute capacity to get pods that were evicted due to 
an upgrade scheduled immediately, so pods may remain unscheduled and unable to serve traffic. GKE surge upgrades solve this
problem by bringing up additional (surge) nodes, so insufficient compute capacity cannot cause disruption. Other factors, 
such as the time it takes to restart a pod, can still contribute to disruption.

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the 
resources that you created.

Deleting the cluster removes all resources used in this demo:

    gcloud container clusters delete hello-cluster
