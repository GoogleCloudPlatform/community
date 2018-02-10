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
	
	
## Install Helm in Cloud Shell

If you already have Helm client and Tiller installed on your cluster, you can skip to the next section.

__Helm__ is a tool that streamlines installing and managing Kubernetes applications and resources. Think of it like apt/yum/homebrew for Kubernetes.  Use of helm charts is recommended since they are maintained and typically kept up-to-date by the Kubernetes community. 

-  Helm has two parts: a client (`helm`) and a server (`tiller`)
-  `Tiller` runs inside of your Kubernetes cluster, and manages releases (installations) of your [helm charts](https://github.com/kubernetes/helm/blob/master/docs/charts.md).
-  `Helm` runs on your laptop, CI/CD, or in our case, the Cloud Shell.
 
You can install the `helm` client in Cloud Shell using the following commands:

```
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh
```

```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  6640  100  6640    0     0  25824      0 --:--:-- --:--:-- --:--:-- 25836
```

```
chmod 700 get_helm.sh
./get_helm.sh
```

The script above fetches the latest version of `helm` client and installs it locally in Cloud Shell.

```
Downloading https://kubernetes-helm.storage.googleapis.com/helm-v2.8.1-linux-amd64.tar.gz
Preparing to install into /usr/local/bin
helm installed into /usr/local/bin/helm
Run 'helm init' to configure helm.
```

Run the following command to install the server side tiller to the Kubernetes cluster.

```
helm init
```

The output below confirms tiller is running.

```
Creating /home/ameer00/.helm
Creating /home/ameer00/.helm/repository
Creating /home/ameer00/.helm/repository/cache
Creating /home/ameer00/.helm/repository/local
Creating /home/ameer00/.helm/plugins
Creating /home/ameer00/.helm/starters
Creating /home/ameer00/.helm/cache/archive
Creating /home/ameer00/.helm/repository/repositories.yaml
Adding stable repo with URL: https://kubernetes-charts.storage.googleapis.com
Adding local repo with URL: http://127.0.0.1:8879/charts
$HELM_HOME has been configured at /home/ameer00/.helm.

Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.
Happy Helming!
```

You can also confirm that `tiller` is running by checking for the `tiller_deploy` Deployment in the `kube-system` namespace.  Run the following command:

```
kubectl get deployments -n kube-system
```

The output should have a `tiller_deploy` Deployment as shown below:

```
NAME                    DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
event-exporter-v0.1.7   1         1         1            1           13m
heapster-v1.4.3         1         1         1            1           13m
kube-dns                2         2         2            2           13m
kube-dns-autoscaler     1         1         1            1           13m
kubernetes-dashboard    1         1         1            1           13m
l7-default-backend      1         1         1            1           13m
tiller-deploy           1         1         1            1           4m
```

## Deploy an application in Kubernetes Engine

You can deploy a simple web based application from the Google Cloud
Repository.  You use this application as the backend for the Ingress.

From the Cloud Shell, run the following command:  
  
```
kubectl run hello-app --image=gcr.io/google-samples/hello-app:1.0 --port=8080
```

```
deployment "hello-app" created
```

Expose the `hello-app` Deployment as a Service by running the following command:

```
kubectl expose deployment hello-app
```

```
service "hello-app" exposed
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

Lets create a simple Ingress Resource YAML file which uses the NGINX Ingress Controller and has one path rule defined by typing the following commands:

```
cat > ingress-resource.yaml << EOF
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: ingress-resource
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - http:
      paths:
      - path: /hello
        backend:
          serviceName: hello-app
          servicePort: 8080
EOF
```

The `kind: Ingress` dictates it is an Ingress Resource object.  This Ingress Resource defines an inbound L7 rule for path `/hello` to service `hello-app` on port 8080.

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

You should now be able to access the web application by going to the __EXTERNAL-IP/hello__
address of the NGINX ingress controller (from the output of the `kubectl get service nginx-ingress-controller` above). 

	http://external-ip-of-ingress-controller]/hello

![image](https://github.com/ameer00/community/blob/master/tutorials/nginx-ingress-gke/hello-app.png)

To check if the _default-backend_ service is working properly, access any path (other than
the path `/hello` defined in the Ingress Resource) and ensure you receive a 404
message.  For example: 

	http://external-ip-of-ingress-controller]/test

You should get the following message:

![image](https://github.com/ameer00/community/blob/master/tutorials/nginx-ingress-gke/default-backend.png)
  
  
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
helm del --purge nginx-ingress
```

```
release "nginx-ingress" deleted
```

Delete the app.
```
kubectl delete service hello-app
kubectl delete deployment hello-app
```

```
service "hello-app" deleted
deployment "hello-app" deleted
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

Delete the `ingress_resource.yaml` file by running the following command:    
 
	rm ingress-resource.yaml
