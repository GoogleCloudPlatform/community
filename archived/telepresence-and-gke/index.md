---
title: Develop Go microservices on Google Kubernetes Engine with Telepresence
description: A cloud development environment powered by GKE and Telepresence.
author: peteroneilljr
tags: golang, gke
date_published: 2021-03-19
---

Peter ONeill | Developer Advocate | Ambassador Labs

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Kubernetes, microservices, and cloud-native architectures have quickly become the new standard for software development. These technologies promise faster, more
efficient processes for development teams, but the truth is that the learning curve is often very steep, especially for application developers. In the transition
from the monolith to microservices, the techniques that once worked so well for application developers——such as local development and debugging——become nearly 
impossible with new application architectures, and often it’s up to the application developers to find solutions. First, developers must learn how to change
their development processes. Then, they have to find the right tools for the job. The whole process can become daunting very quickly. 

One of the more common cloud-native development workflows looks like this:

1.  Package code as a container.
1.  Push the container to Google Container Registry.
1.  Deploy the changes.
1.  Wait for continuous integration to run to see the changes live.

This workflow seems to work for large, infrequent changes; but for small, fast changes it introduces a lot of wait time. You should be able to see the results 
of your changes immediately. 

In this tutorial, you'll set up a local development environment for a Go microservice in Google Kubernetes Engine (GKE). Instead of waiting through the
old-fashioned development workflow, you'll use [Telepresence](http://www.getambassador.io/products/telepresence/), an open source Cloud Native Computing
Foundation project, to see the results of your change right away. 

## Set up your sample application with the Go microservice

For this example, you'll make code changes to the Go microservice running between the frontend Java service and a backend datastore. You'll start by deploying a 
sample microservice application consisting of 3 services:

* **VeryLargeJavaService**: A memory-intensive service written in Java that generates the frontend graphics and web pages for the application.
* **VeryLargeDataStore**: A large datastore service that contains the sample data for the Edgey Corp store.
* **DataProcessingService**: A Go service that manages requests for information between the two services.

**Note**: We've called these *VeryLarge* services to emphasize the fact that your local environment may not have enough CPU and RAM, or you may just not want to
pay for all that extra overhead. But don't worry: the sample app used in this tutorial is actually quite small.

![](https://storage.googleapis.com/gcp-community/tutorials/telepresence-and-gke/0_7J_48_5o8juPX5E6.png)

In this architecture diagram, requests from users are routed through an ingress controller to your services. For simplicity's sake, this tutorial skips the step
of [deploying an ingress controller](https://www.getambassador.io/docs/latest/topics/install/install-ambassador-oss/#kubernetes-yaml). If you're ready to use 
Telepresence in your own setup and need a simple way to set up an ingress controller, we recommend checking out the
[Ambassador Edge Stack](https://www.getambassador.io/products/edge-stack/), which you can configure with the
[K8s Initializer](https://app.getambassador.io/initializer).

Start by deploying the sample application to a GKE cluster:

    kubectl apply -f https://raw.githubusercontent.com/datawire/edgey-corp-go/main/k8s-config/edgey-corp-web-app-no-mapping.yaml

## Configure your local development environment to work with the Go microservice

You'll need to grab all of the code for your local development environment so that you can edit the `DataProcessingService` service. As shown in the architecture
diagram, the `DataProcessingService` service is dependent on a connection to both the `VeryLargeJavaService` service and the `VeryLargeDataStore` service. So, in 
order to make a change to this service, you'll need to exchange data with these other services, too.

1.  Clone the repository for this application from GitHub:

        git clone https://github.com/datawire/edgey-corp-go.git

1.  Go to the `DataProcessingService` directory:

        cd edgey-corp-go/DataProcessingService

1.  Start the Go server:

        go build main.go && ./main

1.  See your service running:

        10:23:41 app | Welcome to the DataProcessingGoService!

1.  In another terminal window, check to see that the service is returning `"blue"`:

        curl localhost:3000/color

## Use Telepresence to connect your environment to the GKE cluster

[Telepresence](https://www.getambassador.io/use-case/local-kubernetes-development/) creates a bidirectional network connection between your local development
environment and the Kubernetes cluster to facilitate Kubernetes development.

1.  Download Telepresence (~60MB):

    - macOS:

          sudo curl -fL https://app.getambassador.io/download/tel2/darwin/amd64/latest/telepresence -o /usr/local/bin/telepresence

    - Linux:

          sudo curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o /usr/local/bin/telepresence

1.  Make the binary executable:

        sudo chmod a+x /usr/loca/bin/telepresence

1.  Test Telepresence by connecting to the remote cluster:

        telepresence connect

1.  Send a request to the Kubernetes API server:

        curl -ik https://kubernetes.default.svc.cluster.local


    The output should look something like this:
    
        HTTP/1.1 401 Unauthorized
        Cache-Control: no-cache, private
        Content-Type: application/json
        Www-Authenticate: Basic realm="kubernetes-master"
        Date: Tue, 09 Feb 2021 23:21:51 GMT

You've configured Telepresence. Telepresence is intercepting requests that you make to the Kubernetes API server, and routing over its direct connection to GKE.

## Intercept connections to your local Go service

An intercept is a routing rule for Telepresence. You can create an intercept to route traffic intended for `DataProcessingService` in the cluster and instead 
route all of the traffic to the *local* version of `DataProcessingService` running on port 3000.

1.  Create the intercept:

        telepresence intercept dataprocessingservice — port 3000

1.  Access the the sample application directly with Telepresence by going to `http://verylargejavaservice:8080`.

    Telepresence intercepts network requests intended for GKE and routes them appropriately.
    
1.  Make some updates to the Go microservice:

    1.  Open the `edgey-corp-go/DataProcessingService/main.go` file in an editor.
    1.  Change the value of the `color` variable from `blue` to `orange`.
    1.  Save the file.
    1.  Stop the previous server instance and start it again:

            go build main.go && ./main

1.  Refresh your browser to check that the color has changed from blue to orange.

That's it! Using Telepresence, you quickly went from editing your local Go service to testing these change with the application as a whole. When you compare it
to the original process of building and deploying after every change, you can see how much time you can save, especially as you make more complex changes or run 
even larger services.

## Learn more about Telepresence

In this tutorial, you learned how to use Telepresence to rapidly iterate on a Go microservice running in Kubernetes. Now, instead of waiting for slow local 
development processes, you can iterate quickly with an instant feedback loop and a productive cloud-native development environment.

If you want to learn more about Telepresence, check out the following resources:

* Read the [documentation](https://www.getambassador.io/docs/latest/telepresence/quick-start/qs-go/).
* Watch the [demonstration video](https://www.youtube.com/watch?v=W_a3aErN3NU).
* Read more about [intercepts](https://www.getambassador.io/docs/latest/telepresence/howtos/intercepts/#intercepts).
* Learn about [preview URLs](https://www.getambassador.io/docs/pre-release/telepresence/howtos/preview-urls/#collaboration-with-preview-urls) for easy 
  collaboration with teammates.
* Join the [Telepresense Slack channel](https://d6e.co/slack) to connect with the Telepresence community.
