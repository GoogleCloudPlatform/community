---
title: Seamlessly encrypt traffic from any apps in your Mesh to Memorystore (redis)
description: FIXME
author: mathieu-benoit
tags: istio, service-mesh, kubernetes, gke, redis, memorystore, security, asm
date_published: 2022-08-24
---

Mathieu Benoit | DevRel Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Anthos Service Mesh (ASM), a managed Istio implementation, can [improve your security posture](https://cloud.google.com/service-mesh/docs/security/anthos-service-mesh-security-best-practices) for your Kubernetes clusters and your apps. Istio aims to bring [as much value to users out of the box](https://istio.io/latest/blog/2021/zero-config-istio/) without any configuration at all. ASM, on top of that, simplifies all the management of both the control plane and the data plane and the integration with monitoring and logging. Without any compromise, your apps in your Mesh will benefit from advanced features like traffic encryption, logging, tracing, etc. without updating the code of your apps.

In this article, we will show how easy and seamless it is to encrypt traffic from any apps in your Mesh to Memorystore (redis).

## Objectives

*   Create a Google Kubernetes Engine (GKE) cluster and register it to a Fleet
*   Deploy the Online Boutique sample apps with an in-cluster redis database
*   Install the managed Anthos Service Mesh (ASM) on this cluster
*   Provision a Memorystore (redis) instance allowing only in-transit encryption
*   Connect the Online Boutique sample apps to the Memorystore (redis) instance
*   Configure the TLS origination from the Mesh to the Memorystore (redis) instance
*   Verify that the Online Boutique sample apps is successfully communicating over TLS with the Memorystore (redis) instance

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Kubernetes Engine](https://cloud.google.com/kubernetes-engine/pricing)
*   [Anthos Service Mesh](https://cloud.google.com/service-mesh/pricing)
*   [Memorystore (redis)](https://cloud.google.com/memorystore/docs/redis/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

Give a numbered sequence of procedural steps that the reader must take to set up their environment before getting into the main tutorial.

Don't assume anything about the reader's environment. You can include simple installation instructions of only a few steps, but provide links to installation
instructions for anything more complex.

### Example: Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1.  Create an account with the BigQuery free tier. See
    [this video from Google](https://www.youtube.com/watch?v=w4mzE--sprY&list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq&index=2) for detailed instructions.
1.  Create a Google Cloud project in the [Cloud console](https://console.cloud.google.com/).
1.  Install [DBeaver Community for Windows](https://dbeaver.io/download/).

## Tutorial body

### Initialize the variables used throughout this tutorial:

Run:
```
project=FIXME
region=us-east4
zone=us-east4-a
gcloud config set project $project
```

### Enable the required APIs in your project

Run:
```
gcloud services enable \
    redis.googleapis.com \
    mesh.googleapis.com
```

### Create a GKE cluster and register it to a Fleet

Create a GKE cluster:
```
gcloud container clusters create $clusterName \
    --workload-pool=$project.svc.id.goog \
    --zone $zone
```

### Deploy the Online Boutique sample apps

Create a dedicated `Namespace`:
```
ONLINE_BOUTIQUE_NAMESPACE=onlineboutique
kubectl create ns $ONLINE_BOUTIQUE_NAMESPACE
```

Deploy the Online Boutique sample appss:
```
kubectl apply \
    -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml \
    -n $ONLINE_BOUTIQUE_NAMESPACE
```

After all the apps are successfully deployed, you could navigate to the Online Boutique website by clicking on the link below:
```
echo -e ''
```

### Install the managed ASM on this cluster

Enable ASM in your Fleet:
```
gcloud container fleet mesh enable
```

Enable the ASM automatic control plane management to let Google apply the recommended configuration of ASM:
```
gcloud container fleet mesh update \
    --control-plane automatic \
    --memberships ${CLUSTER}
```

### Provision a Memorystore (redis) instance allowing only in-transit encryption

Run:
```
REDIS_NAME=redis-tls
gcloud redis instances create $REDIS_NAME \
    --size=1 \
    --region=$REGION \
    --zone=$ZONE \
    --redis-version=redis_6_x \
    --transit-encryption-mode=SERVER_AUTHENTICATION
```

Wait for the Memorystore (redis) instance to be succesfully provisioned:
```
gcloud redis instances describe $REDIS_NAME \
    --region=$GKE_REGION
```

Get the connection information of the Memorystore (redis) instance just provisioned, we will need these information in a following section:
```
REDIS_IP=$(gcloud redis instances describe $REDIS_NAME \
    --region=$GKE_REGION \
    --format='get(host)')
REDIS_PORT=$(gcloud redis instances describe $REDIS_NAME \
    --region=$GKE_REGION \
    --format='get(port)')
gcloud redis instances describe $REDIS_NAME \
    --region=$GKE_REGION \
    --format='get(serverCaCerts[0].cert)' > redis-cert.pem
```

### Connect the Online Boutique sample apps to the Memorystore (redis) instance

Remove the default in-cluster `redis` database we won't use anymore:
```
kubectl delete service redis-cart \
    -n ONLINE_BOUTIQUE_NAMESPACE
kubectl delete deployment redis-cart \
    -n ONLINE_BOUTIQUE_NAMESPACE 
```



### Configure the TLS origination from the Mesh to the Memorystore (redis) instance

Create a Secret with the Certificate Authority generated previously:
```
kubectl create secret generic redis-cert \
    --from-file=redis-cert.pem \
    -n $ONLINE_BOUTIQUE_NAMESPACE
```

From there we could create `ServiceEntry` and `DestinationRule` allowing to expose this external endpoint in the mesh with a TLS origination setup:
```
INTERNAL_HOST=redis.memorystore-redis
cat <<EOF | kubectl apply -n $ONLINE_BOUTIQUE_NAMESPACE -f -
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-redis
spec:
  hosts:
  - ${INTERNAL_HOST}
  addresses:
  - ${REDIS_IP}/32
  endpoints:
  - address: ${REDIS_IP}
  location: MESH_EXTERNAL
  resolution: STATIC
  ports:
  - number: ${REDIS_PORT}
    name: tcp-redis
    protocol: TCP
EOF
cat <<EOF | kubectl apply -n $ONLINE_BOUTIQUE_NAMESPACE -f -
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: external-redis
spec:
  exportTo:
  - '.'
  host: ${INTERNAL_HOST}
  trafficPolicy:
    tls:
      mode: SIMPLE
      caCertificates: /etc/certs/redis-cert.pem
EOF
```

Inject the Istio/ASM sidecar proxies in the Online Boutique `Namespace`:
```
kubectl label namespace $ONLINE_BOUTIQUE_NAMESPACE istio-injection=enabled istio.io/rev- --overwrite
```

Restart the `cartservice` app in order to inject the Istio/ASM sidecar proxies and configs we just deployed previously:
```
kubectl rollout restart deployment cartservice \
    -n $ONLINE_BOUTIQUE_NAMESPACE
```

## Cleaning up

Tell the reader how to shut down what they built to avoid incurring further costs.

### Example: Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
