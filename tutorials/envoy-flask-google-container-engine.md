---
title: Deploying Envoy with a Python Flask webapp and Google Kubernetes Engine
description: Learn how to use Envoy in Google Kubernetes Engine as a foundation for adding resilience and observability to a microservices-based application.
author: flynn
tags: microservices, Kubernetes Engine, Envoy, Flask, Python
date_published: 2017-06-28
---

One of the recurring problems with using microservices is managing communications. Your clients must be able to speak to your services, and in most cases services need to speak among themselves. When things go wrong, the system as a whole needs to be resilient, so it degrades gracefully instead of catastrophically. It also must be observable so you can figure out what's wrong.

A useful pattern is to enlist a proxy, like [Envoy](https://lyft.github.io/envoy/), to help [make your application more resilient and observable](https://www.datawire.io/guide/traffic/getting-started-lyft-envoy-microservices-resilience/). Envoy can be a bit daunting to set up, so this tutorial walks you through deploying a Python Flask webapp with Envoy on Google Kubernetes Engine.

## The application

The application is a simple REST-based user service. It can create, fetch, and delete users. Even such a trivial application involves several real-world concerns:

* It requires persistent storage.
* It lets you explore scaling the different pieces of the application.
* It lets you explore Envoy at the edge, where the user’s client talks to your application.
* It lets you explore Envoy internally, brokering communications between the various parts of the application.

Envoy runs as a sidecar, so it's language-agnostic. For this tutorial, the REST service uses Python and Flask, with PostgreSQL for persistence, all of which play nicely together. And of course, running on Kubernetes Engine means managing everything with Kubernetes.

## Before you begin

### Kubernetes Engine

You need a Google Cloud Platform account to set up a Kubernetes Engine cluster. Visit the [Google Cloud Platform Console](https://console.cloud.google.com/kubernetes) and use the UI to create a new cluster. Picking the defaults should be fine for this tutorial.

### Kubernetes

You need `kubectl`, the Kubernetes command-line interface, to work with Kubernetes Engine. On macOS you can use
`brew install kubernetes-cli`. Otherwise, follow the
[Kubernetes installation intructions](https://kubernetes.io/docs/tasks/tools/install-kubectl/).

### Docker

Kubernetes Engine runs code from Docker images, so you need the Docker command-line interface, `docker`, to build your own 
images. [Docker Community Edition](https://www.docker.com/community-edition) is fine if you're just getting started.
(Again, on macOS, the easy way is to run `brew install docker`.)

### The application

Everything you use in this tutorial is in [Datawire's `envoy-steps` repository](https://github.com/datawire/envoy-steps).

1. Clone that repository and `cd` into your clone:

        git clone https://github.com/datawire/envoy-steps.git
        cd envoy-steps

1. In your `envoy-steps` directory, you should see `README.md` and directories named `postgres`, `usersvc`, and so on. Each 
of those directories contains a service to be deployed, and each can be brought up or down independently with

        sh up.sh $service

    or

        sh down.sh $service

Between Python code, Kubernetes configs, docs, and so on, there’s too much to include everything in one document. This
tutorial just covers the highlights, and you can look at all the details in your clone of the repo.

## The Docker registry

Because Kubernetes needs to pull Docker images to run in its containers, you must push the Docker images used in this article to a Docker registry that Kubernetes Engine can access. For example, `gcr.io` or `dockerhub` will work fine, but for production use you might want to minimize traffic across boundaries as a cost-reduction effort.

Whatever you set up, you need to push to the correct registry, and you need to use the correct registry when telling Kubernetes where to go for images. Unfortunately, `kubectl` doesn't have a provision for parameterizing the YAML files it uses to figure out what to do, so `envoy-steps` contains scripts to set things up correctly.

1. Run the following command:

        sh prep.sh [REGISTRY_INFO]

      where `[REGISTRY_INFO]` is the appropriate prefix for the `docker push` command. For example, if you want to use the `example` organization in DockerHub, run:

        sh prep.sh example

      To use the `example` repository under `gcr.io`, run:

        sh prep.sh gcr.io/example

      You need to have permissions to push to whatever you use. When `prep.sh` finishes, all the configuration files will be updated with the correct image names.

1. You can use the following command to clean everything up and start over, if needed:

        sh clean.sh

## Database matters

The Flask app uses PostgreSQL for its storage. For now, it checks at every startup to make sure that its single table exists, relying on Postgres to prevent duplicate tables. This approach is best suited for a single Postgres instance, but that's OK for now. 

All you need for PostgreSQL is to spin up the server in your Kubernetes cluster. Postgres publishes a prebuilt Docker image for Postgres 9.6 on DockerHub, which makes this very easy. The relevant config file is `postgres/deployment.yaml`, and its `spec` section declares the image to use:

```yaml
spec:
  containers:
  - name: postgres
    image: postgres:9.6
```

You also need to use a Kubernetes `service` to expose the PostgreSQL port within the cluster, so that the Flask app can talk to the database. That’s defined in `postgres/service.yaml` with highlights:

```yaml
spec:
  type: ClusterIP
  ports:
  - name: postgres
    port: 5432
  selector:
    service: postgres
```

Note that this service is type `ClusterIP`, so that it can be seen only within the cluster.

1. To start the database, run:

        sh up.sh postgres

1. Run `kubectl get pods`, which should show a `postgres` pod running:

        NAME                       READY  STATUS   RESTARTS AGE
        postgres-1385931004-p3szz  1/1    Running  0        5s

1. Run `kubectl get services`, which should show its service:

        NAME      CLUSTER-IP     EXTERNAL-IP  PORT(S)   AGE
        postgres  10.107.246.55  <none>       5432/TCP  5s

At this point the Postgres server is running, reachable from anywhere in the cluster at `postgres:5432`.

## The Flask app

The Flask app is a simple user-management service. It responds to `PUT` requests to create users, and to `GET` requests to read users and respond to health checks. Each user has a UUID, a `username`, a `fullname`, and a `password`. The UUID is auto-generated, and the `password` is never returned on fetch.

You can see the app in full in the GitHub repo. It's very simple; the only real gotcha is that if you don't explicitly tell Flask to listen on '0.0.0.0', it will default to listening on the loopback address, and you won't be able to talk to it from elsewhere in the cluster. 

Building a Flask app into a Docker image is relatively straightforward. The biggest question is which image to use as a base, but if you already know you're going to be using Envoy later, the easiest thing is just to base the image on the `lyft/envoy` image. So the Dockerfile (without comments) looks like this:

    FROM lyft/envoy:latest
    RUN apt-get update && apt-get -q install -y
        curl
        python-pip
        dnsutils
    WORKDIR /application
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY service.py .
    COPY entrypoint.sh .
    RUN chmod +x entrypoint.sh
    ENTRYPOINT [ "./entrypoint.sh" ]

To get the Flask app going in Kubernetes, you need to:

- Build the Docker image.
- Push it to `usersvc:step1` in your chosen Docker registry.
- Set up a Kubernetes deployment and service with it.

The deployment, in `usersvc/deployment.yaml`, looks almost the same as the one for `postgres`, just with a different image name:

```yaml
spec:
  containers:
  - name: usersvc
    image: usersvc:step1
```

Likewise, `usersvc/service.yaml` is almost the same as its `postgres` sibling, but it uses type `LoadBalancer` to indicate that the service should be exposed to users outside the cluster:

```yaml
spec:
  type: LoadBalancer
  ports:
  - name: usersvc
    port: 5000
    targetPort: 5000
  selector:
    service: usersvc
```

Starting with `LoadBalancer` may seem odd. After all, the goal is to use Envoy to do load balancing. It's good to walk before running, though, so the first test will be to talk to the Flask app without Envoy, and for that, the port needs to be open to the outside world.

1. Run `up.sh` script to build and push the Docker image, then start the `usersvc`:

        sh up.sh usersvc

1. Run `kubectl get pods`, which should show both a `usersvc` pod and a `postgres` pod running:

        NAME                       READY  STATUS   RESTARTS AGE
        postgres-1385931004-p3szz  1/1    Running  0        5m
        usersvc-1941676296-kmglv   1/1    Running  0        5s

## First test

First things first: make sure it works without Envoy before moving on. You need the IP address and mapped port number for the `usersvc` service. 

1. Using Kubernetes Engine, the following will build a neatly-formed URL to the load balancer created for the `usersvc`:

        USERSVC_IP=$(kubectl get svc usersvc -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        USERSVC_PORT=$(kubectl get svc usersvc -o jsonpath='{.spec.ports[0].port}')
        USERSVC_URL="http://${USERSVC_IP}:${USERSVC_PORT}"

      This might change depending on your cluster type. On Minikube, you'll need `minikube service --url`; on AWS, you'll need `...ingress[0].hostname`. Other cluster providers may be different still. You can always start by reading the output of `kubectl describe service usersvc` to get a sense of what's up.

1. Given the URL, you can try a basic health check using `curl` *from the host system*, reaching into the cluster to the `usersvc`, which in turn is talking within the cluster to `postgres`:

        curl ${USERSVC_URL}/user/health

      If all goes well, the health check should give you something like:

       {
         "hostname": "usersvc-1941676296-kmglv",
         "msg": "user health check OK",
         "ok": true,
         "resolvedname": "172.17.0.10"
       }

1. Try saving and retrieving a user:

        curl -X PUT -H "Content-Type: application/json" \
            -d '{ "fullname": "Alice", "password": "alicerules" }' \
            ${USERSVC_URL}/user/alice

      This should return a user record for Alice, including her UUID but not her password:

         {
           "fullname": "Alice",
           "hostname": "usersvc-1941676296-kmglv",
           "ok": true,
           "resolvedname": "172.17.0.10",
           "uuid": "44FD5687B15B4AF78753E33E6A2B033B"
         }

1. Repeating this for Bob should be much the same:

         curl -X PUT -H "Content-Type: application/json" \
              -d '{ "fullname": "Bob", "password": "bobrules" }' \
              ${USERSVC_URL}/user/bob

      Naturally, Bob should have a different UUID:

         {
           "fullname": "Bob",
           "hostname": "usersvc-1941676296-kmglv",
           "ok": true,
           "resolvedname": "172.17.0.10",
           "uuid": "72C77A08942D4EADA61B6A0713C1624F"
         }
            
1. Finally, you can try reading both users back (again, minus passwords) with

        curl ${USERSVC_URL}/user/alice
        curl ${USERSVC_URL}/user/bob

## Enter Envoy

Now it’s time to put Envoy in front of everything, so it can manage routing when you start scaling the front end. Production use usually involves two layers of Envoys, not one:

* The _edge_ Envoy runs by itself somewhere, to give the rest of the world a single point of ingress. Incoming connections from outside come to the edge Envoy, and it decides where they go internally.
    * Adding a little more functionality in this layer provides a proper [API Gateway](http://getambassador.io/). This tutorial will keep things simple, doing everything by hand so you can see how it all works.
* Each instance of a service has a _service Envoy_ running alongside it, as a separate process.
    * The multiple Envoys form a mesh, sharing routing information and providing uniform statistics and logging.

Only the edge Envoy is actually required, and really taking advantage of the Envoy mesh requires an article of its own. This tutorial covers deploying both edge and service Envoys for the Flask app, to show how to configure the simplest case.

The edge Envoy and the service Envoys run the same code, but have separate configurations. The edge Envoy, running as a Kubernetes service in its own container, can be built with the following Dockerfile:

    FROM lyft/envoy:latest
    RUN apt-get update && apt-get -q install -y
        curl
        dnsutils
    COPY envoy.json /etc/envoy.json
    CMD /usr/local/bin/envoy -c /etc/envoy.json

Which is to say: take `lyft/envoy:latest`, copy in our edge Envoy config, and start Envoy running.

### Envoy configuration

You configure Envoy with a JSON dictionary that primarily describes _listeners_ and _clusters_. 

* A _listener_ tells Envoy an _address_ on which it should listen and a set of _filters_ with which Envoy should process what it hears.
* A _cluster_ tells Envoy about one or more _hosts_ to which Envoy can proxy incoming requests.

The two big complicating factors are:

* Filters can (and usually do) have their own configuration, which is often more complex than the listener’s configuration.
* Clusters get tangled up with load balancing and external things like DNS.

The `http_connection_manager` filter handles HTTP proxying. It knows how to parse HTTP headers and figure out which Envoy cluster should handle a given connection, for both HTTP/1.1 and HTTP/2. The filter configuration for `http_connection_manager` is a dictionary with quite a few options, but the most critical one for basic proxying is the `virtual_hosts` array, which defines how requests will be routed. Each element in the array is another dictionary containing the following attributes:

* `name`: A human-readable name for the service.
* `domains`: An array of DNS-style domain names, one of which must match the domain name in the URL for the `virtual_host` to match (or `"*"` to match any domain).
* `routes`: An array of route dictionaries (see below).

Each route dictionary needs to include, at a minimum:

* `prefix`: The URL path prefix for this route.
* `cluster`: The Envoy cluster to handle this request.
* `timeout_ms`: The timeout for giving up if something goes wrong.

The Flask app requires only a single `listener` for your edge Envoy:

```py
"listeners": [
  {
    "address": "tcp://0.0.0.0:80",
    "filters": [
      {
        "type": "read",
        "name": "http_connection_manager",
        "config": { . . . }
      }
    ]
  }
]
```

This tells Envoy to listen for any connection on TCP port 80, and use the `http_connection_manager` to handle incoming requests. You can see the whole filter configuration in `edge-envoy/envoy.json`, but here's how to set up its `virtual_hosts` to get the edge Envoy to proxy any URL starting with `/user` to the `usersvc`:

```py
"virtual_hosts": [
  {
    "name": "service",
    "domains": [ "*" ],
    "routes": [
      {
        "timeout_ms": 0,
        "prefix": "/user",
        "cluster": “usersvc"
      }
    ]
  }
]
```

Note `domains [“*”]` indicates that the host being requested doesn't matter. Also note that you can always add more routes if needed.

Envoy also needs a definition for the `usersvc` cluster referenced in the `virtual_hosts` section above. You do this in the `cluster_manager` configuration section, which is also a dictionary and also has one critical component, called `clusters`. Its value is also an array of dictionaries:

* `name`: A human-readable name for this cluster.
* `type`: How will Envoy know which hosts are up?
* `lb_type`: How will Envoy handle load balancing?
* `hosts`: An array of URLs defining the hosts in the cluster (usually `tcp://` URLs).

The possible `type` values:

* `static`: Every host is listed in the `cluster` definition.
* `strict_dns`: Envoy monitors DNS, and every matching A record will be assumed valid.
* `logical_dns`: Envoy uses the DNS to add hosts, but will not discard them if they’re no longer returned by DNS (imagine round-robin DNS with hundreds of hosts).
* `sds`: Envoy will use an external REST service to find cluster members.

And the possible `lb_type` values are:

* `round_robin`: Cycle over all healthy hosts, in order.
* `weighted_least_request`: Select two random healthy hosts and pick the one with the fewest requests (this is O(1), where scanning all healthy hosts would be O(n), and Lyft claims that research indicates that the O(1) algorithm “is nearly as good” as the full scan).
* `random`: Just pick a random host.

Here's how to put it all together for the `usersvc` cluster:

```py
"clusters": [
  {
    "name": “usersvc”,
    "type": "strict_dns",
    "lb_type": "round_robin",
    "hosts": [
      {
        "url": “tcp://usersvc:80”
      }
    ]
  }
]
```

Note the `type: strict_dns` there -- for this to work, every instance of the `usersvc` must appear in the DNS. This clearly will require some testing!

As usual, it's a single command to start the edge Envoy running.

Run the following command:

    sh up.sh edge-envoy

You won't be able to easily test this yet, since the edge Envoy would try to talk to service Envoys that aren’t running yet. But they will be after the next step.

## App changes for Envoy

After the edge Envoy is running, you need to switch the Flask app to use a service Envoy. To keep things simple, the service Envoy runs as a separate process in the Flask app's container. You don't need to change the database for this to work, but you need to make a few tweaks to the Flask app:

* The Dockerfile needs to copy in the Envoy config file.
* `entrypoint.sh` needs to start the service Envoy as well as the Flask app.
* Flask can go back to listening only on the loopback interface.
* Finally, the `usersvc` can use type `ClusterIP` instead `LoadBalancer`.

This gives you a running Envoy, through which you can talk to the Flask app. This Envoy will be the only way to talk to the Flask app. Trying to talk directly is blocked in the network layer.

The service Envoy’s config is very similar to the edge Envoy’s. The `listeners` section is identical, and the `clusters` section nearly so:

```py
"clusters": [
  {
    "name": “usersvc”,
    "type": "static",
    "lb_type": "round_robin",
    "hosts": [
      {
        "url": “tcp://127.0.0.1:80”
      }
    ]
  }
]
```

Because the edge Envoy proxies only to `localhost`, it's easiest to use a static, single-member cluster.

All the changes to the Flask side of the world can be found in the `usersvc2` directory, which is a copy of the `usersvc` directory with the previous changes applied (and it tags its image `usersvc:step2` instead of `usersvc:step1`). You need to drop the old `usersvc` and bring up the new one.

Run the following commands:

    sh down.sh usersvc
    sh up.sh usersvc2

## Second test

1. What that is done, it's time to repeat the following step to get the URL of the edge Envoy:

        ENVOY_IP=$(kubectl get svc edge-envoy -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        ENVOY_PORT=$(kubectl get svc edge-envoy -o jsonpath='{.spec.ports[0].port}')
        ENVOY_URL="http://${ENVOY_IP}:${ENVOY_PORT}"

1. Try retrieving Alice and Bob like before:

        curl $ENVOY_URL/user/alice
        curl $ENVOY_URL/user/bob

Note that `$ENVOY_URL` uses the `edge-envoy` service, not the `usersvc`. This means that you're  talking through the Envoy mesh. In fact, if you try talking directly to `usersvc`, it will fail. That’s part of how to be sure that Envoy is doing its job.

## Scaling the Flask app

Envoy is meant to gracefully handle scaling services, so bringing up a few more instances of the Flask app is probably a good test to see how well it handles that.

1. Run the following command:

        kubectl scale --replicas=3 deployment/usersvc

1. When that’s done, `kubectl get pods` should show more `usersvc` instances running:

        NAME                         READY STATUS   RESTARTS  AGE
        edge-envoy-2874730579-7vrp4  1/1   Running  0         3m
        postgres-1385931004-p3szz    1/1   Running  0         5m
        usersvc-2016583945-h7hqz     1/1   Running  0         6s
        usersvc-2016583945-hxvrn     1/1   Running  0         6s
        usersvc-2016583945-pzq2x     1/1   Running  0         3m

1. You should be able to verify that `curl` requests get routed to multiple hosts. Run:

        curl $ENVOY_URL/user/health

      multiple times, and look at the returned `hostname` element. It should cycle across the three `usersvc` nodes. But it doesn't. What’s going on here?

      Remember that the edge Envoy is running in `strict_dns` mode, so a good first check would be to look at the DNS. 
      
1. Run `nslookup` from inside the cluster, say on one of the `usersvc` pods:

        kubectl exec usersvc-2016583945-h7hqz /usr/bin/nslookup usersvc

      You'll need to use one of your pod names when you run this command.

Sure enough, only one address comes back, so Envoy’s DNS-based service discovery simply isn’t going to work. Envoy can’t round-robin among three service instances if it never hears about two of them.

## The Service Discovery service

The problem is that Kubernetes puts **services** into its DNS, not **service endpoints**. Envoy needs to know about the endpoints in order to load balance. Kubernetes does know the service endpoints for each service and Envoy knows how to query a REST service for discovery information. So it's possible to make this work with a simple Python shim that bridges from the Envoy Service Discovery Service (SDS) to the Kubernetes API.

The `usersvc-sds` directory contains a simple SDS:

* Envoy uses a `GET` request to ask for service information.
* The SDS uses the Python `requests` module to query the Kubernetes endpoints API.
* It then reformats the results and returns them to Envoy.

The most surprising bit might be the token that the SDS reads when it starts. Kubernetes requires the token for access control, but it's polite enough to install it on every container it starts, precisely so that this sort of thing is possible.

The edge Envoy's config needs to change slightly. Rather than using `strict_dns` mode, you need `sds` mode. That means defining an `sds` cluster. Here's the one for the `usersvc-sds`:

```py
"cluster_manager": {
  "sds": {
    "cluster": {
      "name": "usersvc-sds",
      "connect_timeout_ms": 250,
      "type": "strict_dns",
      "lb_type": "round_robin",
      "hosts": [
        {
          "url": "tcp://usersvc-sds:5000"
        }
      ]
    },
    "refresh_delay_ms": 15000
  },
  "clusters": [
    {
      "name": "usersvc",
      "connect_timeout_ms": 250,
      "type": "sds",
      "service_name": "usersvc",
      "lb_type": "round_robin",
      "features": "http2"
    }
  ]
}
```

Look carefully and you'll see that the `sds` cluster is not defined inside the `clusters` dictionary, but as a peer of `clusters`. Its value is a cluster definition. Also note that the `sds` cluster uses `strict_dns` and thus relies on the DNS being sane for the `usersvc-sds` itself. There are use cases where this won't be OK, but they're beyond the scope of this tutorial.

After the `sds` cluster is defined, you can use `"type": "sds"` in a service cluster definition, and delete any `hosts` array for that cluster, as shown above for the new `usersvc` cluster.

The `edge-envoy2` directory has everything set up for an edge Envoy running this configuration. To get it all going, start the SDS running, then down the old edge Envoy and fire up the new.

1. Run the following commands:

        sh up.sh usersvc-sds
        sh down.sh edge-envoy
        sh up.sh edge-envoy2

1. You need to reset the `ENVOY_URL` when you do this:

        ENVOY_IP=$(kubectl get svc edge-envoy -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        ENVOY_PORT=$(kubectl get svc edge-envoy -o jsonpath='{.spec.ports[0].port}')
        ENVOY_URL="http://${ENVOY_IP}:${ENVOY_PORT}"

      In a production setup, you'd leave the Kubernetes `service` for the edge Envoy in place to avoid needing to do this. The scripting here is deliberately very simple, though, so `down.sh` makes sure that nothing is left behind.

1. When the new Envoy is running, repeating the health check really should show you round-robining around the hosts. Of course, asking for the details of user Alice or Bob should always give the same results, no matter which host does the database lookup.

        curl $ENVOY_URL/user/alice

Repeat that a few times: the host information should change, but the user information should not.

## Summary

At this point everything is working, including using Envoy to handle round-robining of traffic between your several Flask apps. You can use `kubectl scale` to change the number of instances of Flask apps you're running, and you have a platform to build on for resilience and observability. Overall, Envoy makes for a pretty promising way to add a lot of flexibility without a lot of pain.
