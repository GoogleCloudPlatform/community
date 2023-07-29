---
title: Deploy a private GoDoc server on Google Kubernetes Engine
description: Learn how to set up a private GoDoc server on Google Kubernetes Engine.
author: richarddli
tags: microservices, Golang, Ambassador
date_published: 2020-07-20
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Go has emerged as an incredibly popular language in the cloud-native ecosystem. Go is a popular choice for both microservices and cloud-native infrastructure
such as [Kubernetes](https://kubernetes.io). Go includes a documentation generator, GoDoc, that generates HTML documentation from Go source code. GoDoc powers
[pkg.go.dev](https://pkg.go.dev/), which hosts public documentation of Go source libraries, including
[GoDoc itself](https://pkg.go.dev/golang.org/x/tools/cmd/godoc?tab=doc). 

According to the [2019 Go Developer Survey](https://blog.golang.org/survey2019-results), 85% of Go developers don’t actually run their own internal documentation 
server. We hope that this statistic doesn't actually indicate a lack of documentation!

This tutorial shows you how to deploy a private [GoDoc service](https://github.com/ambassadorlabs/godoc-service) on
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/), using [Ambassador Edge Stack](https://www.getambassador.io).

## Set up your local environment

To set up your computer, you install the `gcloud` and `kubectl` command-line tools.

1.  Follow [the instructions to download and install the Cloud SDK](https://cloud.google.com/sdk/downloads), which includes the `gcloud` command-line tool.
1.  Ensure that `kubectl` is installed and updated:

        sudo gcloud components update kubectl

## Set up a Kubernetes cluster in Google Kubernetes Engine

Setting up a production-ready Kubernetes cluster can be fairly complex, so this tutorial uses Google Kubernetes Engine. If you already have a Kubernetes cluster 
available, you can skip this section.

1.  Create a cluster using one of the following options:

    - Use the **Create cluster** button in the [Cloud Console](https://console.cloud.google.com/kubernetes).
    - Use a `gcloud` command like the following, which creates a small cluster in the `us-central1-c` region:

        ```
        gcloud beta container --project "xxx" clusters create "cluster-1" --zone "us-central1-c" --no-enable-basic-auth --cluster-version "1.14.10-gke.36" --machine-type "n1-standard-1" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --num-nodes "3" --enable-stackdriver-kubernetes --enable-ip-alias --network "projects/datawireio/global/networks/default" --subnetwork "projects/datawireio/regions/us-central1/subnetworks/default" --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0
        ```

1.  Authenticate to your cluster:

        gcloud container clusters get-credentials CLUSTER_NAME
        gcloud auth application-default login

## Deploy the GoDoc service

In this section, you deploy the [Ambassador Edge Stack](https://www.getambassador.io) as your ingress controller. Ambassador Edge Stack is an
[ingress controller](https://www.getambassador.io/learn/kubernetes-glossary/ingress-controller/) and API Gateway built on Envoy Proxy. It includes a free OpenID
Connect integration that can be integrated with Google for single sign-on. In this architecture, requests first arrive at Ambassador, which passes only 
authenticated requests on to your GoDoc service.

The GoDoc service consists of 150 lines of Go that integrates the `godoc` binary with Kubernetes and GitHub. The source code for the service is available in the 
[godoc-service repository on GitHub](https://github.com/ambassadorlabs/godoc-service). 

### Set up Ambassador Edge Stack

You can install Ambassador Edge Stack with a Helm chart, YAML, or the command-line installer. This tutorial uses the command-line installer, which automatically 
provisions a TLS certificate and a domain for you.

1.  Download the `edgectl` client and install Ambassador Edge Stack the following command:

        edgectl install

1.  Follow the on-screen instructions to continue the installation.

When the installation is complete, you should see the following:
    
    Ambassador Edge Stack Installation Complete!
    ========================================================================
        
    Congratulations! You've successfully installed the Ambassador Edge Stack in
    your Kubernetes cluster. You can find it at your custom URL:
    https://objective-nash-360.edgestack.me/

The installation process automatically provisions a certificate from Let’s Encrypt, and the management UI should appear in your browser. If it doesn’t, you
can use the command `edgectl login $URL`. 

### Set up the GoDoc service

In this section, you configure the GoDoc service with a Kubernetes secret.

1.  Get a GitHub [personal access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) with 
    full control of your private repositories.

1.  Create a Kubernetes secret that stores the GitHub token, along with the GitHub repositories that you want to document. The example below shows publishing 
    documentation on Ambassador and the godoc-service:

        kubectl create secret generic godoc-service-config --from-literal=githubToken=YOUR_GITHUB_TOKEN --from-literal=githubRepos="ambassadorlabs/godoc-service;datawire/ambassador"

### Deploy the GoDoc service

If you’re familiar with Kubernetes, you probably know that deploying source code into Kubernetes requires a bunch of steps: building the container, pushing to a 
Docker registry, deploying the container with the right Kubernetes manifest onto Kubernetes, and then registering a route with your ingress to the Kubernetes 
service. 

Ambassador Edge Stack uses a special resource, the Project resource, that does this workflow automatically by using
[Kaniko](https://github.com/GoogleContainerTools/kaniko) to do an in-cluster Docker build and push to a private OCI-compliant registry based on Docker registry.
This micro-CD pipeline can thus deploy code from GitHub straight into Kubernetes so that you can get to
[Version 0](http://getambassador.io/learn/kubernetes-glossary/version-0/) quickly. 

In this section, you use this feature to deploy the GoDoc service.

1.  Enable the micro-CD pipeline:

        kubectl apply -f https://www.getambassador.io/yaml/projects.yaml

1.  Create a Project CRD and configuration. Use the same GitHub personal access token that you previously created, and make sure that the host matches your 
    actual edgestack.me domain.

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

Ambassador clones the GitHub repository, builds the container for the service, and deploys the container into a Kubernetes pod. This process will take a few 
minutes; you can follow the build process in the **Projects** tab of the Ambassador user interface.

When the build is complete, visit https://YOUR_DOMAIN.edgestack.me/doc/ in your browser to see your Go documentation.

## Next steps

Ambassador Edge Stack integrates with many different identity providers over OpenID Connect for single sign-on, including
[Google's IDP](https://www.getambassador.io/docs/latest/howtos/sso/google/). Deploy an authentication `Filter` and `FilterPolicy` to ensure that only people in 
your organization have access to your documentation server.

Unless you want to keep using the `edgestack.me` domain, you’ll also want to create a new Host that maps to a hostname in your DNS. Edge Stack automatically 
provisions a certificate from Let’s Encrypt as soon as you set up the new Host. For more details, see the Host CRD documentation.

Happy coding in Go!
