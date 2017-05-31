---
title: Deploying Envoy with a Python Flask webapp and Google Container Engine
description: Learn how to use Envoy in Google Container Engine as a foundation for adding resilience and observability to a microservice-based application
author: flynn
tags: microservices, Container Engine, Envoy, Flask, Python
date_published: 2017-05-30
---

One of the recurring problems with using microservices is managing communications. Your clients need to be able to speak to your services, and in most cases services need to speak amongst themselves. When things go wrong, the system as a whole needs to be resilient, so that it degrades gracefully instead of catastrophically, but it also needs to be observable so that you can figure out what's wrong.

A useful pattern is to enlist a proxy, like [Envoy](https://lyft.github.io/envoy/) to help [make your application more resilient and observable](https://www.datawire.io/guide/traffic/getting-started-lyft-envoy-microservices-resilience/). Envoy can be a bit daunting to set up, so this tutorial will walk you through deploying a Python Flask webapp with Envoy on Google Container Engine.

## The Application

Our application is a super simple REST-based user service: it can create users, read information about a user, and process simple logins. Even a trivial application like this involves several real-world concerns, though:

* It requires persistent storage.
* It will let us explore scaling the different pieces of the application.
* It will let us explore Envoy at the edge, where the user’s client talks to our application, and
* It will let us explore Envoy internally, brokering communications between the various parts of the application.

Envoy runs as a sidecar, so it's language-agnostic. For this tutorial, we’ll use Python and Flask -- they're simple and because I like Python. We’ll use PostgreSQL for persistence – it has good Python support, and it’s easy to get running both locally and in the cloud. And of course, running on Google Container Engine means managing everything with Kubernetes.

## Setting Up

### Google Container Engine

You'll need a Google Cloud Platform account for this, so that you can set up a Google Container Engine cluster -- just visit the [Google Cloud Platform Console](https://console.cloud.google.com/kubernetes) and use the UI to create a new cluster. Picking the defaults should be fine for our purposes.

### Kubernetes

You'll need `kubectl`, the Kubernetes CLI, to work with Google Container Engine. On a Mac you can use `brew install kubernetes-cli`; else you'll need to follow the [Kubernetes installation intructions](https://kubernetes.io/docs/user-guide/prereqs/).

### Docker

Google Compute Engine runs code from Docker images, so you'll need the Docker CLI, `docker`. [Docker Community Edition](https://www.docker.com/community-edition) is fine if you're just getting started (again, on a Mac, the easy way is `brew install docker`).

### The Application

Everything we'll use in this demo is in GitHub at

<https://github.com/datawire/envoy-steps>

Clone that and `cd` into it -- you should see `README.md` and directories named `postgres`, `usersvc`, etc. Each of the directories contains a service to be deployed, and can be brought up or down independently with

```
sh up.sh $service
```

or

```
sh down.sh $service
```

Obviously I’d prefer to simply include everything you need here in this article, but between Python code, Kubernetes configs, docs, etc, there’s just too much. So we’ll just hit the highlights here, and you can look at all the details in your clone of the repo.

## The Docker Registry

Since Kubernetes needs to pull Docker images to run in its containers, we'll need to push the Docker images we use in this article to some Docker registry that Google Container Engine can access. `gcr.io`, `dockerhub`, whatever -- any will work for this now, although for production use you might want to minimize traffic across boundaries as a cost-reduction effort.

Whatever you have set up, you'll need to push to the correct registry, and you'll need to use the correct registry when telling Kubernetes where to go for images. Unfortunately, `kubectl` doesn't have a provision for parameterizing the YAML files we're using to tell it what to do. We'll dealt with this annoyance by just using a script to set everything up for us:

```
sh prep.sh registry-info
```

where `registry-info` is the appropriate prefix for the `docker push` command -- e.g., I use the `dwflynn` DockerHub organization as my scratchpad, so I'll do

```
sh prep.sh dwflynn
```

I could use Datawire's public repository under `gcr.io` with

```
sh prep.sh gcr.io/datawireio
```

Obviously you'll need to have permissions to push to whatever you use here! Once `prep.sh` finishes, though, all the configuration files we use will be updated with the correct image names.

If you need to, you can use

```
sh clean.sh
```

to clean everything up and start over.

## Database Matters

We just need a single database table to store all our user information. We'll start by writing the Flask app to check at boot time and create our table if it doesn’t exist, relying on Postgres itself to prevent duplicate tables. (This is best suited for a single Postgres instance, but that's OK for now.)

So all we really need is a way to spin up a Postgres server in our Kubernetes cluster. We can just use the Postgres 9.6 Docker image published on DockerHub to make this easy. The relevant config file is `postgres/deployment.yaml`, which includes in its spec section the specifics of the image we’ll use:

```
spec:
  containers:
  - name: postgres
    image: postgres:9.6
```

We also need to expose the Postgres service within our cluster. That’s defined in `postgres/service.yaml` with highlights:

```
spec:
  type: ClusterIP
  ports:
  - name: postgres
    port: 5432
  selector:
    service: postgres
```

Note that this service is type `ClusterIP`, so that it can be seen only within the cluster.

To start the database, just run

```
bash up.sh postgres
```

Once that’s done, then `kubectl get pods` should show a `postgres` pod running:

```
NAME                       READY  STATUS   RESTARTS AGE
postgres-1385931004-p3szz  1/1    Running  0        5s
```

and `kubectl get services` should show its service:

```
NAME      CLUSTER-IP     EXTERNAL-IP  PORT(S)   AGE
postgres  10.107.246.55  <none>       5432/TCP  5s
```

At this point we have a running Postgres server, reachable from anywhere in the cluster at `postgres:5432`.

## The Flask App

Our Flask app just responds to `PUT` requests to create users, and `GET` requests to read users and respond to health checks. You can see it in full in the GitHub repo. It's very simple: the only real gotcha is that Flask, by default, will listen only on the loopback address, which will prevent any connections from outside the Flask app’s container. We fix that by telling it to explicitly listen on `0.0.0.0` instead, so that we can actually speak to it from elsewhere (whether from in the cluster or outside).

To deploy it in Kubernetes, we’ll need a Docker image that contains our app. We’ll build this on top of the `lyft/envoy` image, since we’re headed for Envoy later; thus our Dockerfile (sans comments) ends up looking like this:

```
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
```

We’ll build a Docker image from that, push it to `${DOCKER_REGISTRY}/usersvc:step1`, then fire up a Kubernetes deployment and service with it. The deployment, in `usersvc/deployment.yaml`, looks almost the same as the one for `postgres`, just with a different image name:

```
spec:
  containers:
  - name: usersvc
    image: usersvc:step1
```

Likewise, `usersvc/service.yaml` is almost the same as its `postgres` sibling, but we’re using type `LoadBalancer` to indicate that we want the service exposed to users outside the cluster:

```
spec:
  type: LoadBalancer
  ports:
  - name: usersvc
    port: 5000
    targetPort: 5000
  selector:
    service: usersvc
```

Starting with `LoadBalancer` may seem odd — after all, we want to use Envoy to do load balancing, right? It's good to walk before running, though: our first test will be to talk to our service *without* Envoy, and for that we need to expose the port to the outside world.

To build the Docker image and start the `usersvc`, you can run

```
bash up.sh usersvc
```

which will build the Docker image, push it so that Google Container Engine can see it, and then launch the new `usersvc` deployment. At this point, `kubectl get pods` should show both a `usersvc` pod and a `postgres` pod running:

```
NAME                       READY  STATUS   RESTARTS AGE
postgres-1385931004-p3szz  1/1    Running  0        5m
usersvc-1941676296-kmglv   1/1    Running  0        5s
```

## First Test!

And now the moment of truth: let’s see if it works *without* Envoy before moving on! This will require us to get the IP address and mapped port number for our `usersvc` service. Since we’re using Google Container Engine, we'll use the following monstrosity to get a neatly-formed URL to the load balancer created for the `usersvc`:

```
USERSVC_IP=$(kubectl get svc usersvc -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
USERSVC_PORT=$(kubectl get svc usersvc -o jsonpath='{.spec.ports[0].port}')
USERSVC_URL="http://${USERSVC_IP}:${USERSVC_PORT}"
```

(This is one of the things that may change depending on your cluster type. On Minikube, you'll need `minikube service --url`; on AWS, you'll need `...ingress[0].hostname`. Other cluster providers may be different still. You can always start by reading the output of `kubectl describe service usersvc` to get a sense of what's up.)

Given the URL, let’s start with a basic health check using `curl` *from the host system*, reaching into the cluster to the `usersvc`, which in turn is talking within the cluster to `postgres`:

```
curl ${USERSVC_URL}/user/health
```

If all goes well, the health check should give you something like

```
{
  "hostname": "usersvc-1941676296-kmglv",
  "msg": "user health check OK",
  "ok": true,
  "resolvedname": "172.17.0.10"
}
```

Next up we'll try saving and retrieving a user:

```
curl -X PUT -H "Content-Type: application/json" \
     -d '{ "fullname": "Alice", "password": "alicerules" }' \
     ${USERSVC_URL}/user/alice
```

This should return a user record for Alice, including her UUID but not her password:

```
{
  "fullname": "Alice",
  "hostname": "usersvc-1941676296-kmglv",
  "ok": true,
  "resolvedname": "172.17.0.10",
  "uuid": "44FD5687B15B4AF78753E33E6A2B033B"
}
```

Repeating this for Bob should be much the same:

```
curl -X PUT -H "Content-Type: application/json" \
     -d '{ "fullname": "Bob", "password": "bobrules" }' \
     ${USERSVC_URL}/user/bob
```

Naturally, Bob should have a different UUID:

```
{
  "fullname": "Bob",
  "hostname": "usersvc-1941676296-kmglv",
  "ok": true,
  "resolvedname": "172.17.0.10",
  "uuid": "72C77A08942D4EADA61B6A0713C1624F"
}
```

Finally, we'll check reading both users back (again, minus passwords!) with

```
curl ${USERSVC_URL}/user/alice
curl ${USERSVC_URL}/user/bob
```

## Enter Envoy

Once all of that is working (whew!), it’s time to stick Envoy in front of everything, so it can manage routing when we start scaling the front end. This usually involves two layers of Envoys, not one:

* First, we have an "edge Envoy" running all by itself somewhere, to give the rest of the world a single point of ingress. Incoming connections from outside come to the edge Envoy, and it decides where they go internally.
   * Adding a little more functionality in this layer gets us a proper [API Gateway](http://getambassador.io/). We'll do everything by hand here, though, to really see how it all works.
* Second, each instance of a service has an "service Envoy" running alongside it, as a separate process next to the service itself. These keep an eye on their services, and remember what’s running and what’s not.
* All the Envoys form a mesh, and share routing information amongst themselves.
* Interservice calls can (and usually will) go through the Envoy mesh as well, though we won't really get into this in this article.

Only the edge Envoy is actually required, but with the full mesh, the service Envoys can do health monitoring and such, and let the mesh know if it’s pointless to try to contact a down service. Also, Envoy’s statistics gathering works best with the full mesh (more on that in a separate article, though).

The edge Envoy and the service Envoys run the same code, but have separate configurations. We’ll start with the edge Envoy, running it as a Kubernetes service in its own container, built with the following Dockerfile:

```
FROM lyft/envoy:latest
RUN apt-get update && apt-get -q install -y
    curl
    dnsutils
COPY envoy.json /etc/envoy.json
CMD /usr/local/bin/envoy -c /etc/envoy.json
```

which is to say, we take `lyft/envoy:latest`, copy in our edge Envoy config, and start Envoy running.

### Envoy Configuration

Envoy is configured with a JSON dictionary that primarily describes *listeners* and *clusters*. We won't get too far into the details here, but basically, a *listener* tells Envoy an *address* on which it should listen, and a set of *filters* with which Envoy should process what it hears. A *cluster* tells Envoy about one or more *hosts* to which Envoy can proxy incoming requests.

The two big complicating factors are:

* Filters can – and usually do – have their own configuration, which is often more complex than the listener’s configuration!
* Clusters get tangled up with load balancing and external things like DNS.

Since we're working with HTTP proxying here, we'll be using the `http_connection_manager` filter. It knows how to parse HTTP headers and figure out which Envoy cluster should handle a given connection, for both HTTP/1.1 and HTTP/2. The filter configuration for `http_connection_manager` is a dictionary with quite a few options, but at the moment, the most critical one for our purposes is the `virtual_hosts` array, which defines how exactly the filter will make routing decisions. Each element in the array is another dictionary containing the following attributes:

* `name`: a human-readable name for this service
* `domains`: an array of DNS-style domain names, one of which must match the domain name in the URL for this `virtual_host` to match (or '*' to match any domain)
* `routes`: an array of route dictionaries (see below)

Each route dictionary needs to include at minimum:

* `prefix`: the URL path prefix for this route
* `cluster`: the Envoy cluster to handle this request
* `timeout_ms`: the timeout for giving up if something goes wrong

We'll set up a single `listener` for our edge Envoy:

```
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
],
```

This tells Envoy to listen for any connection on TCP port 80, and use the `http_connection_manager` to handle incoming requests. We won't reproduce the entire filter configuration here, but here's how to set up its `virtual_hosts` to get our edge Envoy to proxy any URL starting with `/user` to our `usersvc`:

```
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

Note that we use `domains [“*”]` to indicate that we don’t much care which host is being requested, and also note that we can always add more routes if needed.

We still need to define the `usersvc` cluster referenced in the `virtual_hosts` section above. We do this in the `cluster_manager` configuration section, which is also a dictionary and also has one critical component, called `clusters`. Its value is also an array of dictionaries:

* `name`: a human-readable name for this cluster
* `type`: how will Envoy know which hosts are up?
* `lb_type`: how will Envoy handle load balancing?
* `hosts`: an array of URLs defining the hosts in the cluster (usually `tcp://` URLs).

The possible `type` values:

* `static`: every host is listed in the `cluster` definition
* `strict_dns`: Envoy monitors DNS, and every matching A record will be assumed valid
* `logical_dns`: Envoy uses the DNS to add hosts, but will not discard them if they’re no longer returned by DNS (we won't cover this in this article, but think round-robin DNS with hundreds of hosts)
* `sds`: Envoy will use an external REST service to find cluster members

And the possible `lb_type` values are:

* `round_robin`: cycle over all healthy hosts, in order
* `weighted_least_request`: select two random healthy hosts and pick the one with the fewest requests (this is O(1), where scanning all healthy hosts would be O(n), and Lyft claims that research indicates that the O(1) algorithm “is nearly as good” as the full scan)
* `random`: just pick a random host

Here's how to put it all together for the `usersvc` cluster:

```
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

We're using `strict_dns`, which means that we’re relying on every instance of the `usersvc` appearing in the DNS. Hopefully this will work for us -- we'll find out when we test!

As usual, it's a single command to start the edge Envoy running:

```
bash up.sh edge-envoy
```

Sadly we can’t really test anything yet, since the edge Envoy is going to try to talk to service Envoys that aren’t running yet -- so let's get them going.

## App Changes for Envoy

Once the edge Envoy is running, we need to switch our Flask app to use an service Envoy. We'll keep things simple for now, and just run the service Envoy as a separate process in the Flask app's container. That means that we needn’t change the database at all, but we do need a few tweaks to the Flask app:

* We need to have the Dockerfile copy in the Envoy config file.
* We need to have the `entrypoint.sh` script start the service Envoy as well as the Flask app.
* While we’re at it, we'll switch back to having Flask listen only on the loopback interface, and
* We’ll switch the service to type `ClusterIP` instead `LoadBalancer`.

This will give us a running Envoy through which we can talk to the Flask app — but also, that Envoy will be the *only* way to talk to the Flask app. Trying to talk directly will be blocked in the network layer.

The service Envoy’s config, while we’re at it, is very similar to the edge Envoy’s. The `listeners` section is identical, and the `clusters` section nearly so:

```
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

Since the edge Envoy proxies only to localhost, we can use a static single-member cluster.

All the changes to the Flask side of the world can be found in the `usersvc2` directory, which is literally a copy of the `usersvc` directory with the changes above applied (and it tags its image `usersvc:step2` instead of `usersvc:step1`). We need to drop the old `usersvc` and bring up the new one:

```
bash down.sh usersvc
bash up.sh usersvc2
```

## Second Test!

Once all that is done, it's time to repeat our monstrosity from before to get the URL of the edge Envoy:


```
ENVOY_IP=$(kubectl get svc edge-envoy -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
ENVOY_PORT=$(kubectl get svc edge-envoy -o jsonpath='{.spec.ports[0].port}')
ENVOY_URL="http://${ENVOY_IP}:${ENVOY_PORT}"
```

and then voilà! we can retrieve Alice and Bob from before:

```
curl $ENVOY_URL/user/alice
curl $ENVOY_URL/user/bob
```

Note, though, that we’re using the `edge-envoy` service here, not the `usersvc`! This means that we are indeed talking through the Envoy mesh -- and in fact, if you try talking directly to `usersvc`, it will fail. That’s part of how we can be sure that Envoy is doing its job.

## Scaling the Flask App

Envoy is meant to gracefully handle scaling services. Let’s see how well it handles that by bringing up a few more instances of our Flask app:

```
kubectl scale --replicas=3 deployment/usersvc
```

Once that’s done, `kubectl get pods` should show more `usersvc` instances running:

```
NAME                         READY STATUS   RESTARTS  AGE
edge-envoy-2874730579-7vrp4  1/1   Running  0         3m
postgres-1385931004-p3szz    1/1   Running  0         5m
usersvc-2016583945-h7hqz     1/1   Running  0         6s
usersvc-2016583945-hxvrn     1/1   Running  0         6s
usersvc-2016583945-pzq2x     1/1   Running  0         3m
```

and we should be able to see `curl` getting routed to multiple hosts. Try

```
curl $ENVOY_URL/user/health
```

multiple times, and look at the returned `hostname` element. We should see it cycling across our three `usersvc` nodes.

But... it’s not. What’s going on here?

Remember that we’re running Envoy in `strict_dns` mode, so a good first check would be to look at the DNS. The easy way to do this is to run `nslookup` from inside the cluster, say on one of the `usersvc` pods:

```
kubectl exec usersvc-2016583945-h7hqz /usr/bin/nslookup usersvc
```

(You'll need to use one of your actual pod names when you run this! Simply pasting the line above is extremely unlikely to work.)

Sure enough, only one address comes back — so Envoy’s DNS-based service discovery simply isn’t going to work. Envoy can’t round-robin among three service instances if it never hears about two of them.

## The Service Discovery Service

What’s happening is that Kubernetes puts each *service* into its DNS, but it doesn’t put each *service endpoint* into its DNS — and Envoy needs to know about the endpoints in order to load-balance. Kubernetes does know the service endpoints for each service, of course, and Envoy knows how to query a REST service for discovery information... so we can make this work with a simple Python shim that bridges from the Envoy “Service Discovery Service” (SDS) to the Kubernetes API.

A simple SDS is in the `usersvc-sds` directory. It’s pretty straightforward: Envoy asks it for service information, it uses the `requests` Python module to query the Kubernetes endpoints API, and finally it reformats the results and returns them to Envoy. The most surprising bit might be the token it reads at the start: Kubernetes is polite enough to install an authentication token on every container it starts, precisely so that this sort of thing is possible.

We'll also need to modify the edge Envoy’s config slightly: rather than using `strict_dns` mode, we need `sds` mode. That, in turn, means that we have to define an `sds` cluster (which uses DNS to locate its server at the moment — we may have to tackle that later, too, as we scale the SDS out!):

```
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

Look carefully and you'll see that the `sds` cluster is not defined inside the `clusters` dictionary, but as a peer of `clusters`. Its value, though, is a cluster definition. Once the `sds` cluster is defined, you can use `"type": "sds"` in a service cluster definition, and delete any `hosts` array for that cluster.

The `edge-envoy2` directory has everything set up for an edge Envoy running this configuration. So we can start the SDS, then down the old edge Envoy and fire up the new:

```
bash up.sh usersvc-sds
bash down.sh edge-envoy
bash up.sh edge-envoy2
```

Sadly, you'll have to reset the `ENVOY_URL` when you do this:

```
ENVOY_IP=$(kubectl get svc edge-envoy -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
ENVOY_PORT=$(kubectl get svc edge-envoy -o jsonpath='{.spec.ports[0].port}')
ENVOY_URL="http://${ENVOY_IP}:${ENVOY_PORT}"
```

and repeating our health check now really should show you round-robining around the hosts.
Of course, asking for the details of user Alice or Bob should always give the same results, no matter which host does the database lookup:

```
curl $ENVOY_URL/user/alice
```

Repeat that a few times: the host information should change, but the user information should not.

## Summary

At this point everything is working, including using Envoy to handle round-robining traffic between our several Flask apps. We can use `kubectl scale` to easily change the number of instances of Flask apps we’re running, and we have a platform to build on for resilience and observability. Overall, Envoy makes for a pretty promising way to add a lot of flexibility without a lot of pain.
