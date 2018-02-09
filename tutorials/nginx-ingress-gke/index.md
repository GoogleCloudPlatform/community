# Ingress with NGINX controller on Google Kubernetes Engine

This guide explains how to deploy the [NGINX Ingress
Controller](https://github.com/kubernetes/ingress-nginx) on Google Kubernetes
Engine. 

In Kubernetes,
[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
allows external users and client applications access to HTTP services.  Ingress
consists of two components. 
[Ingress Resource](https://kubernetes.io/docs/concepts/services-networking/ingress/#the-ingress-resource)
is a collection of rules for the inbound traffic to reach Services.  These are
Layer 7 (L7) rules that allow hostnames (and optionally paths) to be directed to
specific Services in Kubernetes.  The second component is the
[Ingress Controller](https://kubernetes.io/docs/concepts/services-networking/ingress/#ingress-controllers)
which acts upon the rules set by the Ingress Resource, typically via an HTTP or
L7 load balancer.  It is vital that both pieces are properly configured to route
traffic from an  outside client to a Kubernetes Service.  

NGINX is a popular choice for an Ingress Controller for a variety of features:

-  [Websocket](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/websocket),
   which allows you to load balance Websocket applications.
-  [SSL Services](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/ssl-services),
   which allows you to load balance HTTPS applications.
-  [Rewrites](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/rewrites),
   which allows you to rewrite the URI of a request before sending it to the
   application.
-  [Session Persistence](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/session-persistence)
   (NGINX Plus only), which guarantees that all the requests from the same
   client are always passed to the same backend container.
-  [Support for JWTs](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/jwt)
   (NGINX Plus only), which allows NGINX Plus to authenticate requests by
   validating JSON Web Tokens (JWTs).

The following diagram shows the architecture described above:

<img src="https://github.com/ameer00/community/blob/master/tutorials/nginx-ingress-gke/Nginx%20Ingress%20on%20GCP%20-%20Fig%2002.png" width="65%">

This tutorial illustrates how to set up a
[Deployment in Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
with an Ingress Resource using NGINX as the Ingress Controller to route/load
balance traffic from external clients to the Deployment.  This tutorial explains how to accomplish the following:

-  Create a Kubernetes Deployment
-  Deploy NGINX Ingress Controller via [Helm](https://github.com/kubernetes/helm/blob/master/docs/install.md)
-  Set up an Ingress Resource object for the Deployment

## Objectives

-  Deploy a simple Kubernetes web _application_ Deployment 
-  Deploy _NGINX Ingress Controller_ using the stable helm [chart](https://github.com/kubernetes/charts/tree/master/stable/nginx-ingress)
-  Deploy an _Ingress Resource_ for the _application_ that uses _NGINX Ingress_ as the controller
-  Test NGINX Ingress functionality by accessing the Google Cloud L4 (TCP/UDP) Load Balancer
   frontend IP and ensure it can access the web application

## Costs

This tutorial uses billable components of Cloud Platform, including:

-  Kubernetes Engine
-  Google Cloud Load Balancing

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to
generate a cost estimate based on your projected usage.

## Before You Begin

1. Create or select a GCP project.  
   [GO TO THE PROJECTS PAGE](https://console.cloud.google.com/project)
   
1. Enable billing for your project.  
	[ENABLE BILLING](https://support.google.com/cloud/answer/6293499#enable-billing)

1. Enable the Kubernetes Engine API.  
	[ENABLE APIs](https://console.cloud.google.com/flows/enableapi?apiid=container,cloudresourcemanager.googleapis.com)

## Set up your environment

In this section you configure the infrastructure and identities required to
complete the tutorial.

### Create a Kubernetes Engine cluster using Cloud Shell

1. You can use Cloud Shell to complete this tutorial. To use Cloud Shell, perform the following steps:  
	[OPEN A NEW CLOUD SHELL SESSION](https://console.cloud.google.com/?cloudshell=true)

1. Set your project's default compute zone and create a cluster by running the following commands:  
  
        gcloud config set compute/zone us-central1-f  
        gcloud container clusters create nginx-tutorial --num-nodes=2
	
1.  Ensure you have [Helm](https://github.com/kubernetes/helm/blob/master/docs/install.md) installed in Cloud Shell as well as Tiller (the server side component for helm installed on the Kubernetes cluster in the `kube-system` namespace).  
        
1. From the Cloud Shell, clone the following repo, which contains the
files for this tutorial:
    
    	git clone https://github.com/ameer00/nginx-ingress-gke 
    	cd nginx-ingress-gke

## Deploy an application in Kubernetes Engine

You can deploy a simple web based application from the Google Cloud
Repository, courtesy of
[Kubernetes Up and Running repo](https://github.com/kubernetes-up-and-running/kuard).
 You use this application as the backend for the Ingress.

From the Cloud Shell, run the following command:  
  
```
kubectl apply -f kuard-app.yaml
```

```
service "kuard" created
deployment "kuard" created
```

Verify that your Deployment is running three replicated Pods and the Service is exposed by running the following commands:

```
kubectl get deployments kuard
```

```
NAME      DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
kuard     3         3         3            3           1m
```

```
kubectl get pods
```

```
NAME                     READY     STATUS    RESTARTS   AGE
kuard-2740446302-03p3b   1/1       Running   0          1m
kuard-2740446302-6k65c   1/1       Running   0          1m
kuard-2740446302-wbj3g   1/1       Running   0          1m
```

```
kubectl get service kuard
```

```
NAME      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
kuard     ClusterIP   10.7.253.136   <none>        80/TCP    8s
```

## Deploying the NGINX Ingress Controller via Helm

Kubernetes platform allows for administrators to bring their own Ingress
Controllers instead of using the cloud provider's built-in offering. 

The NGINX controller, deployed as a Service, must be exposed for external
access.  This is done using Service `type: LoadBalancer` on the NGINX controller
service.  On Kubernetes Engine, this creates a Google Cloud Network (TCP/IP) Load Balancer with NGINX
controller Service as a backend.  Google Cloud also creates the appropriate
firewall rules within the Service's VPC to allow web HTTP(S) traffic to the load
balancer frontend IP address.  Here is a basic flow of the NGINX ingress
solution on Kubernetes Engine.

### NGINX Ingress Controller on Kubernetes Engine

<img src="https://github.com/ameer00/community/blob/master/tutorials/nginx-ingress-gke/Nginx%20Ingress%20on%20GCP%20-%20Fig%2002.png" width="65%">

From the Cloud Shell, deploy an NGINX controller Deployment and Service by running the following command:  

```
helm install --name nginx-ingress stable/nginx-ingress
```

In the ouput under `RESOURCES`, you should see the following:

```
==> v1/Service
NAME                           TYPE          CLUSTER-IP    EXTERNAL-IP  PORT(S)                     AGE
nginx-ingress-controller       LoadBalancer  10.7.248.226  <pending>    80:30890/TCP,443:30258/TCP  1s
nginx-ingress-default-backend  ClusterIP     10.7.245.75   <none>       80/TCP                      1s
```

Wait a few moments while the GCP L4 Load Balancer gets deployed.  Confirm that the `nginx-ingress-controller` Service has been deployed and that you have an external IP address associated with the service.  Run the following command:

```
kubectl get service nginx-ingress-controller
```
	
```	
NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)                      AGE
nginx-ingress-controller   LoadBalancer   10.7.248.226   35.226.162.176   80:30890/TCP,443:30258/TCP   3m
```

Notice the second service, _nginx-ingress-default-backend_.  The default
backend is a Service which handles all URL paths and hosts the NGINX controller
doesn't understand (i.e., all the requests that are not mapped with an Ingress
Resource). The default backend exposes two URLs:  

-  `/healthz` that returns 200
-  `/` that returns 404


## Configure Ingress Resource to use NGINX Ingress Controller

An Ingress Resource object is a collection of L7 rules for routing inbound traffic to Kubernetes Services.  Multiple rules can be defined in one Ingress Resource or they can be split up into multiple Ingress Resource manifests. The Ingress Resource also determines which controller to utilize to serve traffic.  This can be set with an annotation, `kubernetes.io/ingress.class`, in the metadata section of the Ingress Resource.  For the NGINX controller, use the value `nginx` as shown below:

	 annotations: kubernetes.io/ingress.class: nginx


On Kubernetes Engine, if no annotation is defined under the metadata section, the
Ingress Resource uses the GCP GCLB L7 load balancer to serve traffic.  This
method can also be forced by setting the annotation's value to `gce`as shown below:

	annotations: kubernetes.io/ingress.class: gce

You can verify the annotation by viewing the _ingress-resource.yaml_ file and check the annotations under the metadata section as shown below:

	cat ingress-resource.yaml

The manifest file contains the following configuration:

	apiVersion: extensions/v1beta1
	kind: Ingress
	metadata:
	  name: ingress-resource
	  annotations:
	    kubernetes.io/ingress.class: nginx
	spec:
	  rules:
	  - http:
	      paths:
	      - path: /
		backend:
		  serviceName: kuard
		  servicePort: 80

The `kind: Ingress` dictates it is an Ingress Resource object.  This Ingress Resource defines an inbound L7 rule for path / to service kuard on port 80.

From the Cloud Shell, run the following command:  
  
	kubectl apply -f ingress-resource.yaml

Verify that Ingress Resource has been created.  Please note that the IP address
for the Ingress Resource will not be defined right away (wait a few moments for the `ADDRESS` field to get populated):  
  
```
kubectl get ingress ingress-resource  
```

```
NAME               HOSTS     ADDRESS   PORTS     AGE  
ingress-resource   *                   80        `
```


### Test Ingress and default backend

You should now be able to access the web application by going to the EXTERNAL-IP
address of the NGINX ingress controller (from the output of the `kubectl get service nginx-ingress-controller` above).  

![image](https://github.com/ameer00/community/blob/master/tutorials/nginx-ingress-gke/Kuard-ingress.png)

To check if the _default-backend_ service is working properly, access any path (other than
the default path `/` defined in the Ingress Resource) and ensure you receive a 404
message.  For example: 

	http://external-ip-of-ingress-controller]/test

You should get the following message:
  
	404 page not found 

## Clean Up

From the Cloud Shell, run the following commands:  

Delete the _Ingress Resource_ object.

```  
kubectl delete -f ingress-resource.yaml
```

```
ingress "demo-ingress" deleted
```

Delete the _NGINX Ingress_ helm chart.

```
helm delete nginx-ingress
```

```
release "nginx-ingress" deleted
```

Delete the app.
```
kubectl delete -f kuard-app.yaml
```

```
service "kuard" deleted
deployment "kuard" deleted
```

Check no Deployments, Pods, or Ingresses exist on the cluster by running the following commands:  

```
kubectl get deployments  
```

```
No resources found.
```

```
kubectl get pods
```

```
No resources found.
```

```
kubectl get ingress
```

```
No resources found.
```

Delete the Kubernetes Engine cluster by running the following command:  

```
gcloud container clusters delete nginx-tutorial  
```

```
The following clusters will be deleted.
 - [nginx-tutorial] in [us-central1-f]

	Do you want to continue (Y/n)?  y

	Deleting cluster nginx-tutorial...done.
	Deleted [https://container.googleapis.com/v1/projects/ameer-1/zones/us-central1-f/clusters/nginx-tutorial].
```

To delete the git repo, simply remove the directory by running the following command:    
  
	cd ..  
	rm -rf nginx-ingress-gke/
