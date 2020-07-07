---
title: Deploying a private Godoc server on Kubernetes
description: Learn how to set up a private Godoc server on Google Kubernetes Engine.
author: richarddli
tags: microservices, Kubernetes Engine, Golang, Ambassador
date_published: 2020-07-05
---

# Deploying a private Godoc server on Kubernetes

Go has emerged as an incredibly popular language in the cloud-native ecosystem. Go is a popular choice for both microservices as well as cloud-native infrastructure such as Kubernetes. Go includes a documentation generator, Godoc, that generates HTML documentation from Go source. Godoc powers https://pkg.go.dev/ which hosts public documentation of Go source libraries (including [Godoc itself](https://pkg.go.dev/golang.org/x/tools/cmd/godoc?tab=doc)). 

According to the [2019 Go Developer Survey](https://blog.golang.org/survey2019-results), 85% of Go Developers don’t actually run their own internal documentation server. We hope that this statistic does not actually indicate a lack of documentation!

In this tutorial, we'll walk through how to deploy a private Godoc service on Google Kubernetes Engine.

## Technologies used

* [Kubernetes](https://kubernetes.io)
* [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/)
* [Ambassador Edge Stack](https://www.getambassador.io)
* [Godoc Service](https://github.com/ambassadorlabs/godoc-service)

### Setting up your local environment

To set up your computer, you'll need to install a few basic components.

First, install the `gcloud` and `kubectl` command line tools. Follow the instructions at [https://cloud.google.com/sdk/downloads](https://cloud.google.com/sdk/downloads) to download and install the Cloud SDK. Then, ensure that `kubectl` is installed:

```
% sudo gcloud components update kubectl
```

### Setting up Kubernetes in Google Kubernetes Engine

Setting up a production-ready Kubernetes cluster can be fairly complex, so we're going to use Google Kubernetes Engine in our example. If you already have a Kubernetes cluster handy, you can skip this section.

To set up a Kubernetes cluster in Google Kubernetes Engine, go to
[https://console.cloud.google.com](https://console.cloud.google.com), choose the Google Kubernetes Engine option from the menu, and then **Create a cluster**.

The following `gcloud` command will create a small cluster in the us-central1-c region:

```
gcloud beta container --project "xxx" clusters create "cluster-1" --zone "us-central1-c" --no-enable-basic-auth --cluster-version "1.14.10-gke.36" --machine-type "n1-standard-1" --image-type "COS" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --num-nodes "3" --enable-stackdriver-kubernetes --enable-ip-alias --network "projects/datawireio/global/networks/default" --subnetwork "projects/datawireio/regions/us-central1/subnetworks/default" --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0
```

Finally, we can authenticate to our cluster:

```
% gcloud container clusters get-credentials CLUSTER_NAME
% gcloud auth application-default login
```

## Deploying the Godoc Service

We're going to deploy the [Ambassador Edge Stack](https://www.getambassador.io) as our ingress controller. The Ambassador Edge Stack is an [ingress controller](https://www.getambassador.io/learn/kubernetes-glossary/ingress-controller/) and API Gateway built on Envoy Proxy, and includes a free OpenID Connect integration that can be integrated with Google for Single Sign-On. In this architecture, requests will first arrive at Ambassador, which will pass on only authenticated requests to our Godoc service.

The Godoc service is a simple service that consists of 150 lines of Go that integrates the Godoc binary with Kubernetes and GitHub. The source code for the service is available at https://github.com/ambassadorlabs/godoc-service. 

### Set up Ambassador Edge Stack

We're going to start by installing the Ambassador Edge Stack. You can install AES with a Helm chart, YAML, or the command line installer. For simplicity, we’re just going to use the command-line install, which will automatically provision a TLS certificate and a domain for us. Download the edgectl client and install Ambassador Edge Stack with the `edgectl install` command:

```
$ edgectl install

Installing the Ambassador Edge Stack

Please enter an email address for us to notify you before your TLS certificate
and domain name expire. In order to acquire the TLS certificate, we share this
email with Let’s Encrypt.
Email address [test@example.com]:

========================================================================
Beginning Ambassador Edge Stack Installation
-> Finding repositories and chart versions
-> Installing Ambassador Edge Stack 1.5.3
-> Checking the AES pod deployment
-> Provisioning a cloud load balancer
-> Your Ambassador Edge Stack installation's address is 35.237.148.241
-> Checking that Ambassador Edge Stack is responding to ACME challenge
-> Automatically configuring TLS
-> Acquiring DNS name objective-nash-360.edgestack.me
-> Obtaining a TLS certificate from Let's Encrypt
-> TLS configured successfully

Ambassador Edge Stack Installation Complete!
========================================================================

Congratulations! You've successfully installed the Ambassador Edge Stack in
your Kubernetes cluster. You can find it at your custom URL:
https://objective-nash-360.edgestack.me/
```

The install process automatically provisions a certificate from Let’s Encrypt, and the management UI should appear in your browser. If it doesn’t, you can also use `edgectl login $URL` as well. 

### Set up Godoc service

We’ll now configure the Godoc service. The service is configured using a Kubernetes secret.

1. Get a GitHub [personal access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) which has access to your repositories. Click on Settings, then Developer Settings, and then Personal Access Tokens. Generate a token with full control of private repositories.

2. Create a Kubernetes secret that stores the GitHub token, along with the GitHub repositories that you want to document. In the example below, we’re publishing documentation on Ambassador and the godoc-service:

   ```
   kubectl create secret generic godoc-service-config --from-literal=githubToken=YOUR_GITHUB_TOKEN --from-literal=githubRepos="ambassadorlabs/godoc-service;datawire/ambassador"
   ```

### Deploy Godoc service

If you’re familiar with Kubernetes, you probably know that deploying source into Kubernetes requires a bunch of steps: building the container, pushing to a Docker Registry, deploying the container with the right Kubernetes manifest onto Kubernetes, and then registering a route with your ingress to the Kubernetes service. 

Ambassador Edge Stack supports a special resource, the Project resource, that does this workflow automatically by leveraging [Kaniko](https://github.com/GoogleContainerTools/kaniko) to do an in-cluster Docker build and push to a private OCI-compliant registry based on Docker registry. This “Micro CD” pipeline can thus deploy code from GitHub straight into Kubernetes so that users can get to [Version 0](http://getambassador.io/learn/kubernetes-glossary/version-0/) quickly. 

We’re going to use this feature to deploy the Godoc service.

1. Enable the Micro CD pipeline: kubectl apply -f https://www.getambassador.io/yaml/projects.yaml

2. Create a Project CRD and configuration. Use the same GitHub personal access token you previously created, and make sure the host matches your actual edgestack.me domain.

    ```
    ---
    apiVersion: getambassador.io/v2
    kind: Project
    metadata:
    name: documentation
    namespace: default
    spec:
    host:  YOUR_DOMAIN_HERE.edgestack.me
    prefix: /doc/
    githubRepo: ambassadorlabs/godoc-service
    githubToken: YOUR_GITHUB_TOKEN
    ```

### That's it!

Ambassador will clone the GitHub repository, build the container for the service, and deploy the container into a Kubernetes pod. This process will take a few minutes; you can follow the build process along on the Projects tab of the UI.

Once the build is complete, visit https://YOUR_DOMAIN.edgestack.me/doc/ in your browser and see your Go documentation.

### Next steps
Ambassador Edge Stack integrates with many different identity providers over OpenID Connect for Single Sign-On including [Google's IDP](https://www.getambassador.io/docs/latest/howtos/sso/google/). Deploy an authentication `Filter` and `FilterPolicy` to ensure only people in your organization have access to your documentation server.

Unless you want to stick with the edgestack.me domain, you’ll also want to create a new Host that maps to a hostname in your DNS. Edge Stack will automatically provision a certificate from Let’s Encrypt as soon as you set up the new Host. For more details, see the Host CRD documentation.

Happy coding in Go!
