---
title: Develop Golang Microservices on GKE with Telepresence
description: A cloud development environment powered by GKE and Telepresence
author: datawire
tags: kubernetes, gke, telepresence
date_published: 2021-03-03
---
Kubernetes, microservices, and cloud native architectures have quickly become the new standard for software development. These technologies promise faster, more efficient processes for development teams, but the truth is the learning curve is often very steep, especially for application developers. In the transition from the monolith to microservices, the techniques that once worked so well for application developers - local development, debugging, etc. become nearly impossible with new application architectures and oftentimes, it’s up to the application developers to find solutions. First, developers must learn how to change their development processes. Then, they have to find the right tools for the job. The whole process can become daunting very quickly. 

One of the more common cloud native development workflows looks like this: 
Package code as a container 
Push the container to the Google Container Registry 
Deploy the changes
Wait for CI to run to see them live 
This workflow seems to work for larger, infrequent changes, but for small, fast changes it introduces a lot of wait time. You should be able to see the results of your changes immediately. 

In this tutorial, we'll set up a local development environment for a Golang microservice in GKE . Instead of waiting through the old fashioned development workflow, we'll use [Telepresence](http://www.getambassador.io/products/telepresence/), an open source Cloud Native Computing Foundation project, to see the results of our change right away. Let’s get started! 

## Step 1: Set up our Sample Application with the Go microservice

For our example, we'll make code changes to the Go Microservice running between the front-end Java service and a backend datastore. We'll start by deploying a sample microservice application consisting of 3 services:
* **VeryLargeJavaService**: A memory-intensive service written in Java that generates the front-end graphics and web pages for our application
* **DataProcessingService**: A Golang service that manages requests for information between the two services.
* **VeryLargeDataStore**: A large datastore service that contains the sample data for our Edgey Corp store.
Note: We've called these VeryLarge services to emphasize the fact that your local environment may not have enough CPU and RAM, or you may just not want to pay for all that extra overhead. But don't worry this sample app is actually pretty small.
![](https://cdn-images-1.medium.com/max/3200/0*7J_48_5o8juPX5E6)
In this architecture diagram, you'll notice that requests from users are routed through an ingress controller to our services. For simplicity's sake, we'll skip the step of [deploying an ingress controller](https://www.getambassador.io/docs/latest/topics/install/install-ambassador-oss/#kubernetes-yaml) in this tutorial. If you're ready to use Telepresence in your own setup and need a simple way to set up an ingress controller, we recommend checking out the [Ambassador Edge Stack](https://www.getambassador.io/products/edge-stack/) which can be easily configured with the [K8s Initializer](https://app.getambassador.io/initializer).
Let's start off by deploying the sample application to a GKE cluster:
	```sh
	kubectl apply -f [https://raw.githubusercontent.com/datawire/edgey-corp-go/main/k8s-config/edgey-corp-web-app-no-mapping.yaml](https://raw.githubusercontent.com/datawire/edgey-corp-go/main/k8s-config/edgey-corp-web-app-no-mapping.yaml)
	```
## Step 2: Configure your local development environment to work with the Go Microservice

We'll need to grab all the code for our local development environment so that we can edit the `DataProcessingService` service. As shown in the architecture diagram, the `DataProcessingService` is dependent on a connection to both  `VeryLargeJavaService` and the `VeryLargeDataStore`, so in order to make a change to this service, we'll need to exchange data with these other services as well. Let's get started!
1. Clone the repository for this application from GitHub.
   `git clone [https://github.com/datawire/edgey-corp-go.git](https://github.com/datawire/edgey-corp-go.git)`
2. Change directories into the DataProcessingService
   `cd edgey-corp-go/DataProcessingService`
3. Start the Go server:
   go build main.go && ./main
4. See your service running!
   `10:23:41 app | Welcome to the DataProcessingGoService!`
5. In another terminal window, curl localhost:3000/color to see that the service is returning blue.
	```sh
	$ curl localhost:3000/color
	"blue"
	```
## Step 3: Use Telepresence to connect our environment to the GKE cluster

Telepresence creates a bidirectional network connection between your local development and the Kubernetes cluster to enable [fast, efficient Kubernetes development](https://www.getambassador.io/use-case/local-kubernetes-development/).
1. Download Telepresence (~60MB):
	```sh
	# Mac OS X
	sudo curl -fL [https://app.getambassador.io/download/tel2/darwin/amd64/latest/telepresence](https://app.getambassador.io/download/tel2/darwin/amd64/latest/telepresence) -o /usr/local/bin/telepresence
	#Linux
	sudo curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o /usr/local/bin/telepresence
	```
2. Make the binary executable
   `$ sudo chmod a+x /usr/loca/bin/telepresence`
3. Test Telepresence by connecting to the remote cluster
   `$ telepresence connect`
4. Send a request to the Kubernetes API server:
	```sh
	$ curl -ik [https://kubernetes.default.svc.cluster.local](https://kubernetes.default.svc.cluster.local)
	HTTP/1.1 401 Unauthorized
	Cache-Control: no-cache, private
	Content-Type: application/json
	Www-Authenticate: Basic realm="kubernetes-master"
	Date: Tue, 09 Feb 2021 23:21:51 GMT
   ```

Great! You've successfully configured Telepresence. Now Telepresence is intercepting requests you're making to the Kubernetes API server, and routing over its direct connection to GKE.

## Step 4: Intercept connections to your local Golang Service

An intercept is a routing rule for Telepresence. We can create an intercept to route traffic intended for the `DataProcessingService` in the cluster and instead route all of the traffic to the *local* version of the `DataProcessingService` running on port 3000.

1. Create the intercept
   telepresence intercept dataprocessingservice — port 3000
2. Access the the sample application directly with Telepresence. Visit [http://verylargejavaservice:8080](http://verylargejavaservice:8080). Again, Telepresence is intercepting network requests intended for GKE and routes them appropriately.
3. Next, let's make some updates to our Go microservice. Open edgey-corp-go/DataProcessingService/main.go and change the value of the color variable from blue to orange. Save the file, stop the previous server instance and start it again with go build main.go && ./main.
4. Refresh your browser and see how the color has changed from blue to orange!

That's it! Using Telepresence we quickly went from editing our local Go service to testing these change with the application as a whole. When you compare it to the original process of building and deploying after every change, it's very easy to see how much time you can save especially as we make more complex changes or run even larger services.

## Learn More about Telepresence

Today, we've learned how to use Telepresence to rapidly iterate on a Golang microservice running in Kubernetes. Now, instead of waiting for slow local development processes, we can iterate quickly with an instant feedback loop and a productive cloud native development environment.
If you want to learn more about Telepresence, check out the following resources:
* [Read the docs](https://www.getambassador.io/docs/latest/telepresence/quick-start/qs-go/)
* Watch the [demo video](https://www.youtube.com/watch?v=W_a3aErN3NU)
* Read more about [Intercepts](https://www.getambassador.io/docs/latest/telepresence/howtos/intercepts/#intercepts)
* Learn about [Preview URLs](https://www.getambassador.io/docs/pre-release/telepresence/howtos/preview-urls/#collaboration-with-preview-urls) for easy collaboration with teammates
* [Join our Slack channel](https://d6e.co/slack) to connect with the Telepresence community


