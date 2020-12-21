---
title: Ingress with NGINX controller on Google Kubernetes Engine
description: Learn how to deploy the NGINX Ingress Controller on Google Kubernetes Engine using Helm.
author: ameer00
tags: Google Kubernetes Engine, Kubernetes, Ingress, NGINX, NGINX Ingress Controller, Helm
date_published: 2018-02-12
---

Ameer Abbas | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

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

- [Websocket](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/websocket),
  which allows you to load balance Websocket applications.
- [SSL Services](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/ssl-services),
  which allows you to load balance HTTPS applications.
- [Rewrites](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/rewrites),
  which allows you to rewrite the URI of a request before sending it to the
  application.
- [Session Persistence](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/session-persistence)
  (NGINX Plus only), which guarantees that all the requests from the same
  client are always passed to the same backend container.
- [Support for JWTs](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/jwt)
  (NGINX Plus only), which allows NGINX Plus to authenticate requests by
  validating JSON Web Tokens (JWTs).

The following diagram shows the architecture described above:

![image](https://storage.googleapis.com/gcp-community/tutorials/nginx-ingress-gke/Nginx%20Ingress%20on%20GCP%20-%20Fig%2001.png)

This tutorial illustrates how to set up a
[Deployment in Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
with an Ingress Resource using NGINX as the Ingress Controller to route/load
balance traffic from external clients to the Deployment.  This tutorial explains how to accomplish the following:

-  Create a Kubernetes Deployment
-  Deploy NGINX Ingress Controller via [Helm](https://helm.sh/)
-  Set up an Ingress Resource object for the Deployment

## Objectives

-  Deploy a simple Kubernetes web _application_ Deployment
-  Deploy _NGINX Ingress Controller_ using the stable helm [chart](https://github.com/kubernetes/charts/tree/master/stable/nginx-ingress)
-  Deploy an _Ingress Resource_ for the _application_ that uses _NGINX Ingress_ as the controller
-  Test NGINX Ingress functionality by accessing the Google Cloud L4 (TCP/UDP) Load Balancer
   frontend IP and ensure it can access the web application

## Costs

This tutorial uses billable components of Google Cloud, including:

-  Google Kubernetes Engine
-  Cloud Load Balancing

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to
generate a cost estimate based on your projected usage.

## Before you begin

1.  Create or select a Google Cloud project.
    [GO TO THE PROJECTS PAGE](https://console.cloud.google.com/project)

1.  Enable billing for your project.
	  [ENABLE BILLING](https://support.google.com/cloud/answer/6293499#enable-billing)

1.  Enable the Kubernetes Engine API.
	  [ENABLE APIs](https://console.cloud.google.com/flows/enableapi?apiid=container,cloudresourcemanager.googleapis.com)

## Set up your environment

In this section you configure the infrastructure and identities required to
complete the tutorial.

### Create a Google Kubernetes Engine cluster using Cloud Shell

1.  You can use Cloud Shell to complete this tutorial. To use Cloud Shell, perform the following steps:

	  [OPEN A NEW CLOUD SHELL SESSION](https://console.cloud.google.com/?cloudshell=true)

1.  Set your project's default compute zone and create a cluster by running the following commands:

        gcloud config set compute/zone us-central1-f
        gcloud container clusters create nginx-tutorial --num-nodes=2


## Verify Helm in Cloud Shell

Helm is a tool that streamlines installing and managing Kubernetes applications and resources. Think of it like 
apt/yum/homebrew for Kubernetes. Use of Helm charts is recommended, because they are maintained and typically kept
up to date by the Kubernetes community.

Helm v3 comes pre-installed in Cloud Shell.

1. Verify the version of Helm client in Cloud Shell by running the following command:

        helm version

        _Output (Do not copy)_
        version.BuildInfo{Version:"v3.2.1", GitCommit:"fe51cd1e31e6a202cba7dead9552a6d418ded79a", GitTreeState:"clean", GoVersion:"go1.13.10"}

Ensure that the version is `v3.x.y`. 

You can install the `helm` client in Cloud Shell by following the instructions [here](https://helm.sh/docs/intro/install/).

## Deploy an application in Google Kubernetes Engine

You can deploy a simple web based application from the Google Cloud
Repository. You use this application as the backend for the Ingress.

From the Cloud Shell, run the following command:

    kubectl create deployment hello-app --image=gcr.io/google-samples/hello-app:1.0

This gives the following output:

    deployment.apps/hello-app created

Expose the `hello-app` Deployment as a Service by running the following command:

    kubectl expose deployment hello-app --port=8080 --target-port=8080

This gives the following output:

    service/hello-app exposed

## Deploying the NGINX Ingress Controller with Helm

Kubernetes platform allows for administrators to bring their own Ingress
Controllers instead of using the cloud provider's built-in offering.

The NGINX controller, deployed as a Service, must be exposed for external
access. This is done using Service `type: LoadBalancer` on the NGINX controller
service. On Google Kubernetes Engine, this creates a Google Cloud Network (TCP/IP) Load Balancer with NGINX
controller Service as a backend.  Google Cloud also creates the appropriate
firewall rules within the Service's VPC to allow web HTTP(S) traffic to the load
balancer frontend IP address. Here is a basic flow of the NGINX ingress
solution on Google Kubernetes Engine.

### NGINX Ingress Controller on Google Kubernetes Engine

![image](https://storage.googleapis.com/gcp-community/tutorials/nginx-ingress-gke/Nginx%20Ingress%20on%20GCP%20-%20Fig%2002.png)

#### Deploy NGINX Ingress Controller

Before you deploy the NGINX Ingress helm chart to the GKE cluster, add the `nginx-stable` helm repository in Cloud Shell by running the following commands.

        helm repo add nginx-stable https://helm.nginx.com/stable
        helm repo update

Deploy an NGINX controller Deployment and Service by running the following command:

    helm install nginx-ingress nginx-stable/nginx-ingress

Verify the `nginx-ingress-controller` Deployment and Service is deployed to the GKE cluster.

    kubectl get deployment nginx-ingress-nginx-ingress
    kubectl get service nginx-ingress-nginx-ingress

    _Output (Do not copy)_
    # Deployment
    NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
    nginx-ingress-nginx-ingress   1/1     1            1           131m

    # Service
    NAME                          TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
    nginx-ingress-nginx-ingress   LoadBalancer   10.7.250.75   <pending>     80:31875/TCP,443:30172/TCP   132m 

Wait a few moments while the Google Cloud L4 Load Balancer gets deployed. Confirm that the `nginx-ingress-nginx-ingress` Service has been deployed and that you have an external IP address associated with the service.  Run the following command (note that you may have to run this command a few times until an `EXTERNAL-IP` value is present):

    kubectl get service nginx-ingress-nginx-ingress

You should see the following:

    NAME                          TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
    nginx-ingress-nginx-ingress   LoadBalancer   10.7.250.75   34.70.255.61  80:31875/TCP,443:30172/TCP   132m

Export the `EXTERNAL-IP` of the NGINX ingress controller in a variable to be used later.

    export NGINX_INGRESS_IP=$(kubectl get service nginx-ingress-nginx-ingress -ojson | jq -r '.status.loadBalancer.ingress[].ip')

Ensure you have the correct IP Address value stored in the `$NGINX_INGRESS_IP` variable.

    echo $NGINX_INGRESS_IP

    _Output (Do not copy)_
    34.70.255.61

> Note that your IP Address may be different than the one shown above.

## Configure Ingress Resource to use NGINX Ingress Controller

An Ingress Resource object is a collection of L7 rules for routing inbound traffic to Kubernetes Services. Multiple rules can be defined in one Ingress Resource or they can be split up into multiple Ingress Resource manifests. The Ingress Resource also determines which controller to utilize to serve traffic.  This can be set with an annotation, `kubernetes.io/ingress.class`, in the metadata section of the Ingress Resource.  For the NGINX controller, use the value `nginx` as shown below:

    annotations: kubernetes.io/ingress.class: nginx

On Google Kubernetes Engine, if no annotation is defined under the metadata section, the
Ingress Resource uses the Google Cloud GCLB L7 load balancer to serve traffic. This
method can also be forced by setting the annotation's value to `gce`as shown below:

    annotations: kubernetes.io/ingress.class: gce

Deploying multiple Ingress controllers of different types (for example, both `nginx` and `gce`) and not specifying a class
annotation will result in all controllers fighting to satisfy the Ingress, and all of them racing to update Ingress
status field in confusing ways. For more information, see
[Multipe Ingress controllers](https://kubernetes.github.io/ingress-nginx/user-guide/multiple-ingress/).

Let's create a simple Ingress Resource YAML file which uses the NGINX Ingress Controller and has one path rule defined by typing the following commands:

    cat <<EOF > ingress-resource.yaml
    apiVersion: networking.k8s.io/v1beta1
    kind: Ingress
    metadata:
      name: ingress-resource
      annotations:
        kubernetes.io/ingress.class: "nginx"
        nginx.ingress.kubernetes.io/ssl-redirect: "false"
    spec:
      rules:
      - host: ${NGINX_INGRESS_IP}.xip.io
        http:
          paths:
          - backend:
              serviceName: hello-app
              servicePort: 8080
            path: /hello
    EOF


The `kind: Ingress` dictates it is an Ingress Resource object.  This Ingress Resource defines an inbound L7 rule for path `/hello` to service `hello-app` on port 8080.

From the Cloud Shell, run the following command:

    kubectl apply -f ingress-resource.yaml

Verify that Ingress Resource has been created. Note that the IP address
for the Ingress Resource will not be defined right away (wait a few moments for the `ADDRESS` field to get populated):

    kubectl get ingress ingress-resource

You should see the following:

    NAME               HOSTS                ADDRESS       PORTS   AGE
    ingress-resource   34.70.255.61.xip.io  34.70.255.61  80      111m

Note the `HOSTS` value in the output is set to a FQDN using xip.io domain. This host resolves the hostname with the form of `<IP ADDRESS>.xio.io` to `<IP ADDRESS>`. NGINX Ingress controller requires you to use a DNS name in the `host` spec in the `Ingress` resource. For the purpose of this tutorial, you use the xip.io service. In production, you can replace the `host` spec in the `Ingress` resource with you real FQDN for the Service.

### Test Ingress

You should now be able to access the web application by going to the __EXTERNAL-IP/hello__
address of the NGINX ingress controller (from the output of the `kubectl get service nginx-ingress-nginx-ingress` above).

	  http://external-ip-of-ingress-controller/hello

![image](https://storage.googleapis.com/gcp-community/tutorials/nginx-ingress-gke/hello-app.png)

You can also access the `hello-app` using the curl command in Cloud Shell.

    curl http://$NGINX_INGRESS_IP.xip.io/hello

The output should look like the following.

    Hello, world!
    Version: 1.0.0
    Hostname: hello-app-5f85f64f6c-rfzkn    

## Clean up

From the Cloud Shell, run the following commands:

1.  Delete the _Ingress Resource_ object:

        kubectl delete -f ingress-resource.yaml

    You should see the following:

        ingress.extensions "ingress-resource" deleted

2.  Delete the _NGINX Ingress_ helm chart:

        helm del nginx-ingress

    You should see the following:

        release "nginx-ingress" uninstalled

3.  Delete the app:

        kubectl delete service hello-app
        kubectl delete deployment hello-app

    You should see the following:

        service "hello-app" deleted
        deployment.extensions "hello-app" deleted

4.  Delete the Google Kubernetes Engine cluster by running the following command:

        gcloud container clusters delete nginx-tutorial

    You should see the following:

        The following clusters will be deleted.
        - [nginx-tutorial] in [us-central1-f]
        
            Do you want to continue (Y/n)?  y

            Deleting cluster nginx-tutorial...done.
            Deleted [https://container.googleapis.com/v1/projects/ameer-1/zones/us-central1-f/clusters/nginx-tutorial].

5.  Delete the `ingress_resource.yaml` file by running the following command:

        rm ingress-resource.yaml
