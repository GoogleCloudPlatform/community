---
title: Ingress with NGINX controller on Google Kubernetes Engine
description: Learn how to deploy the NGINX Ingress Controller on Google Kubernetes Engine using Helm.
author: ameer00
tags: Google Kubernetes Engine, Kubernetes, Ingress, NGINX, NGINX Ingress Controller, Helm
date_published: 2018-02-12
---

Ameer Abbas | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This guide explains how to deploy the
[NGINX Ingress Controller](https://github.com/kubernetes/ingress-nginx) on Google Kubernetes Engine.

In Kubernetes,
[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
allows external users and client applications access to HTTP services. Ingress consists of two components.
[Ingress Resource](https://kubernetes.io/docs/concepts/services-networking/ingress/#the-ingress-resource)
is a collection of rules for the inbound traffic to reach Services. These are
Layer 7 (L7) rules that allow hostnames (and optionally paths) to be directed to
specific Services in Kubernetes. The second component is the
[Ingress Controller](https://kubernetes.io/docs/concepts/services-networking/ingress/#ingress-controllers)
which acts upon the rules set by the Ingress Resource, typically through an HTTP or
L7 load balancer. It is vital that both pieces are properly configured to route
traffic from an outside client to a Kubernetes Service.

NGINX is a popular choice for an Ingress Controller for a variety of features:

- [WebSocket](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/websocket),
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
with an Ingress Resource using NGINX as the Ingress Controller to route and load-balance traffic from external clients to the Deployment.

This tutorial explains how to accomplish the following:

- Create a Kubernetes Deployment.
- Deploy NGINX Ingress Controller with [Helm](https://helm.sh/).
- Set up an Ingress Resource object for the Deployment.

## Objectives

- Deploy a simple Kubernetes web _application_ Deployment.
- Deploy _NGINX Ingress Controller_ using the stable Helm [chart](https://github.com/kubernetes/ingress-nginx/tree/master/charts/ingress-nginx).
- Deploy an _Ingress Resource_ for the _application_ that uses _NGINX Ingress_ as the controller.
- Test NGINX Ingress functionality by accessing the Google Cloud L4 (TCP/UDP) load balancer
  frontend IP address and ensure that it can access the web application.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

- Google Kubernetes Engine
- Cloud Load Balancing

Use the [pricing calculator](https://cloud.google.com/products/calculator) to
generate a cost estimate based on your projected usage.

## Before you begin

1.  [Create or select a Google Cloud project.](https://console.cloud.google.com/project)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

1.  [Enable the Google Kubernetes Engine API.](https://console.cloud.google.com/flows/enableapi?apiid=container,cloudresourcemanager.googleapis.com)

## Set up your environment

1.  [Open a new Cloud Shell session.](https://console.cloud.google.com/?cloudshell=true)

1.  Set your project's default Compute Engine zone and create a Google Kubernetes Engine cluster:

        gcloud config set compute/zone us-central1-f
        gcloud container clusters create nginx-tutorial --num-nodes=2

## Verify Helm in Cloud Shell

Helm is a tool that streamlines installing and managing Kubernetes applications and resources. Think of it like
apt, yum, or homebrew for Kubernetes. The use of Helm charts is recommended, because they are maintained and typically kept
up to date by the Kubernetes community.

Helm 3 comes pre-installed in Cloud Shell.

Verify the version of the Helm client in Cloud Shell:

    helm version

The output should look like this:

    version.BuildInfo{Version:"v3.2.1", GitCommit:"fe51cd1e31e6a202cba7dead9552a6d418ded79a", GitTreeState:"clean", GoVersion:"go1.13.10"}

Ensure that the version is `v3.x.y`.

You can install the `helm` client in Cloud Shell by following the instructions [here](https://helm.sh/docs/intro/install/).

## Deploy an application in Google Kubernetes Engine

You can deploy a simple web-based application from the Google Cloud
repository. You use this application as the backend for the Ingress.

1.  From Cloud Shell, run the following command:

        kubectl create deployment hello-app --image=gcr.io/google-samples/hello-app:1.0

    This gives the following output:

        deployment.apps/hello-app created

1.  Expose the `hello-app` Deployment as a Service:

        kubectl expose deployment hello-app --port=8080 --target-port=8080

    This gives the following output:

        service/hello-app exposed

## Deploying the NGINX Ingress Controller with Helm

Kubernetes allows administrators to bring their own Ingress
Controllers instead of using the cloud provider's built-in offering.

The NGINX controller, deployed as a Service, must be exposed for external
access. This is done using Service `type: LoadBalancer` on the NGINX controller
service. On Google Kubernetes Engine, this creates a Google Cloud Network (TCP/IP) load balancer with NGINX
controller Service as a backend. Google Cloud also creates the appropriate
firewall rules within the Service's VPC network to allow web HTTP(S) traffic to the load
balancer frontend IP address.

Here is a basic flow of the NGINX ingress solution on Google Kubernetes Engine.

### NGINX Ingress Controller on Google Kubernetes Engine

![image](https://storage.googleapis.com/gcp-community/tutorials/nginx-ingress-gke/Nginx%20Ingress%20on%20GCP%20-%20Fig%2002.png)

#### Deploy NGINX Ingress Controller

1.  Before you deploy the NGINX Ingress Helm chart to the GKE cluster, add the `nginx-stable` Helm repository in Cloud Shell:

        helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
        helm repo update

1.  Deploy an NGINX controller Deployment and Service by running the following command:

        helm install nginx-ingress ingress-nginx/ingress-nginx

1.  Verify that the `nginx-ingress-controller` Deployment and Service are deployed to the GKE cluster:

        kubectl get deployment nginx-ingress-nginx-ingress
        kubectl get service nginx-ingress-nginx-ingress

    The output should look like this:

        # Deployment
        NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
        nginx-ingress-nginx-ingress   1/1     1            1           131m

        # Service
        NAME                          TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
        nginx-ingress-nginx-ingress   LoadBalancer   10.7.250.75   <pending>     80:31875/TCP,443:30172/TCP   132m

1.  Wait a few moments while the Google Cloud L4 load balancer gets deployed, and then confirm that the `nginx-ingress-nginx-ingress` Service has been deployed
    and that you have an external IP address associated with the service:

        kubectl get service nginx-ingress-nginx-ingress

    You may need to run this command a few times until an `EXTERNAL-IP` value is present.

    You should see the following:

        NAME                          TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
        nginx-ingress-nginx-ingress   LoadBalancer   10.7.250.75   34.70.255.61  80:31875/TCP,443:30172/TCP   132m

1.  Export the `EXTERNAL-IP` of the NGINX ingress controller in a variable to be used later:

        export NGINX_INGRESS_IP=$(kubectl get service nginx-ingress-nginx-ingress -ojson | jq -r '.status.loadBalancer.ingress[].ip')

1.  Ensure that you have the correct IP address value stored in the `$NGINX_INGRESS_IP` variable:

        echo $NGINX_INGRESS_IP

    The output should look like this, though the IP address may differ:

        34.70.255.61

## Configure Ingress Resource to use NGINX Ingress Controller

An Ingress Resource object is a collection of L7 rules for routing inbound traffic to Kubernetes Services. Multiple rules can be defined in one Ingress Resource,
or they can be split up into multiple Ingress Resource manifests. The Ingress Resource also determines which controller to use to serve traffic. This can be set
with an annotation, `kubernetes.io/ingress.class`, in the metadata section of the Ingress Resource. For the NGINX controller, use the value `nginx`:

    annotations: kubernetes.io/ingress.class: nginx

On Google Kubernetes Engine, if no annotation is defined under the metadata section, the
Ingress Resource uses the Google Cloud GCLB L7 load balancer to serve traffic. This
method can also be forced by setting the annotation's value to `gce`:

    annotations: kubernetes.io/ingress.class: gce

Deploying multiple Ingress controllers of different types (for example, both `nginx` and `gce`) and not specifying a class
annotation will result in all controllers fighting to satisfy the Ingress, and all of them racing to update the Ingress
status field in confusing ways. For more information, see
[Multipe Ingress controllers](https://kubernetes.github.io/ingress-nginx/user-guide/multiple-ingress/).

1.  Create a simple Ingress Resource YAML file that uses the NGINX Ingress Controller and has one path rule defined:

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
          - host: ${NGINX_INGRESS_IP}.nip.io
            http:
              paths:
              - backend:
                  serviceName: hello-app
                  servicePort: 8080
                path: /hello
        EOF

    The `kind: Ingress` line dictates that this is an Ingress Resource object. This Ingress Resource defines an inbound L7 rule for path `/hello` to service
    `hello-app` on port 8080.

1.  Apply the configuration:

        kubectl apply -f ingress-resource.yaml

1.  Verify that Ingress Resource has been created:

        kubectl get ingress ingress-resource

    The IP address for the Ingress Resource will not be defined right away, so you may need to wait a few moments for the `ADDRESS` field to get populated.

    The output should look like the following:

        NAME               HOSTS                ADDRESS       PORTS   AGE
        ingress-resource   34.70.255.61.nip.io  34.70.255.61  80      111m

    Note the `HOSTS` value in the output is set to a FQDN using nip.io domain. This host resolves the hostname with the form of `[IP_ADDRESS].nip.io` to
    `[IP_ADDRESS]`. NGINX Ingress Controller requires you to use a DNS name in the `host` specification in the `Ingress` resource. For the purpose of this
    tutorial, you use the nip.io service. In production, you can replace the `host` specification in the `Ingress` resource with you real FQDN for the Service.

### Test Ingress

You should now be able to access the web application by going to the `$NGINX_INGRESS_IP.nip.io/hello`.

    http://$NGINX_INGRESS_IP.nip.io/hello

![image](https://storage.googleapis.com/gcp-community/tutorials/nginx-ingress-gke/hello-app-v1.png)

You can also access the `hello-app` using the `curl` command in Cloud Shell.

    curl http://$NGINX_INGRESS_IP.nip.io/hello

The output should look like the following.

    Hello, world!
    Version: 1.0.0
    Hostname: hello-app-7bfb5ff469-q5wpr

## Clean up

From Cloud Shell, run the following commands:

1.  Delete the Ingress Resource object:

        kubectl delete -f ingress-resource.yaml

    You should see the following:

        ingress.extensions "ingress-resource" deleted

1.  Delete the NGINX Ingress Helm chart:

        helm del nginx-ingress

    You should see the following:

        release "nginx-ingress" uninstalled

1.  Delete the app:

        kubectl delete service hello-app
        kubectl delete deployment hello-app

    You should see the following:

        service "hello-app" deleted
        deployment.extensions "hello-app" deleted

1.  Delete the Google Kubernetes Engine cluster:

        gcloud container clusters delete nginx-tutorial

    You should see the following:

        The following clusters will be deleted.
        - [nginx-tutorial] in [us-central1-f]

            Do you want to continue (Y/n)?  y

            Deleting cluster nginx-tutorial...done.
            Deleted [https://container.googleapis.com/v1/projects/ameer-1/zones/us-central1-f/clusters/nginx-tutorial].

1.  Delete the `ingress_resource.yaml` file:

        rm ingress-resource.yaml
