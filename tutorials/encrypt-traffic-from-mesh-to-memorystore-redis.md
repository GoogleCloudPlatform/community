---
title: Seamlessly encrypt traffic from any apps in your Mesh to Memorystore (redis)
description: Use Anthos Service Mesh to seamlessly encrypt traffic between any apps and Memorystore (redis)
author: mathieu-benoit
tags: istio, service-mesh, kubernetes, gke, redis, memorystore, security, asm
date_published: 2022-08-29
---

Mathieu Benoit | DevRel Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Anthos Service Mesh (ASM), a managed Istio implementation, can [improve your security posture](https://cloud.google.com/service-mesh/docs/security/anthos-service-mesh-security-best-practices) for your Kubernetes clusters and your apps. Istio aims to bring [as much value to users out of the box](https://istio.io/latest/blog/2021/zero-config-istio/) without any configuration at all. ASM, on top of that, simplifies all the management of both the control plane and the data plane and the integration with monitoring and logging. Without any compromise, your apps in your Mesh will benefit from advanced features like traffic encryption, logging, tracing, etc. without updating the code of your apps.

In this article, we will show how easy and seamless it is to encrypt traffic from any apps in your Mesh to Memorystore (redis).

## Objectives

*   Create a Google Kubernetes Engine (GKE) cluster
*   Deploy the Online Boutique sample apps with an in-cluster redis database
*   Provision a Memorystore (redis) instance allowing only in-transit encryption
*   Connect the Online Boutique sample apps to the Memorystore (redis) instance
*   Install the managed Anthos Service Mesh (ASM) on this cluster
*   Configure the TLS origination from the Mesh to the Memorystore (redis) instance
*   Verify that the Online Boutique sample apps is successfully communicating over TLS with the Memorystore (redis) instance

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Kubernetes Engine](https://cloud.google.com/kubernetes-engine/pricing)
*   [Anthos Service Mesh](https://cloud.google.com/service-mesh/pricing)
*   [Memorystore (redis)](https://cloud.google.com/memorystore/docs/redis/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

This guide assumes that you have owner IAM permissions for your Google Cloud project. In production, you do not require owner permission.

1.  [Select or create a Google Cloud project](https://console.cloud.google.com/projectselector2).

1.  [Verify that billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project) for your project.

## Set up your environment

Initialize the common variables used throughout this tutorial:
```
PROJECT_ID=FIXME
REGION=us-east4
ZONE=us-east4-a
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='get(projectNumber)')
```

To avoid repeating the `--project` in the commands throughout this tutorial, let's set the current project:
```
gcloud config set project ${PROJECT_ID}
```

## Enable the required APIs in your project

Enable the required APIs in your project:
```
gcloud services enable \
    redis.googleapis.com \
    mesh.googleapis.com
```

## Create a GKE cluster

Create a GKE cluster:
```
CLUSTER=redis-tls-tutorial
gcloud container clusters create ${CLUSTER} \
    --zone ${ZONE} \
    --machine-type=e2-standard-4 \
    --num-nodes 4 \
    --workload-pool ${PROJECT_ID}.svc.id.goog \
    --labels mesh_id=proj-${PROJECT_NUMBER} \
    --network default
```

## Deploy the Online Boutique sample apps

Create a dedicated `Namespace`:
```
NAMESPACE=onlineboutique
kubectl create ns ${NAMESPACE}
```

Deploy the Online Boutique sample apps:
```
kubectl apply \
    -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml \
    -n ${NAMESPACE}
```

After all the apps are successfully deployed, you could navigate to the Online Boutique website by clicking on the link below:
```
echo -n "http://" && kubectl get svc frontend-external -n ${NAMESPACE} -o json | jq -r '.status.loadBalancer.ingress[0].ip'
```

## Provision a Memorystore (redis) instance allowing only in-transit encryption

Provision the Memorystore (redis) instance allowing only in-transit encryption:
```
REDIS_NAME=redis-tls-tutorial
gcloud redis instances create ${REDIS_NAME} \
    --size 1 \
    --region ${REGION} \
    --zone ${ZONE} \
    --redis-version redis_6_x \
    --network default \
    --transit-encryption-mode SERVER_AUTHENTICATION
```

Notes:
- You can connect to a Memorystore (redis) instance from GKE clusters that are in the same region and use the same network as your instance.
- You cannot connect to a Memorystore (redis) instance from a GKE cluster without VPC-native/IP aliasing enabled.
- In-transit encryption is only available at creation time of your Memorystore (redis) instance. The Certificate Authority is valid for 10 years, [rotation every 5 years](https://cloud.google.com/memorystore/docs/redis/in-transit-encryption#certificate_authority_rotation).

Wait for the Memorystore (redis) instance to be succesfully provisioned and get the connection information of the Memorystore (redis) instance just provisioned, we will need these information in a following section:
```
REDIS_IP=$(gcloud redis instances describe ${REDIS_NAME} \
    --region ${REGION} \
    --format 'get(host)')
REDIS_PORT=$(gcloud redis instances describe ${REDIS_NAME} \
    --region ${REGION} \
    --format 'get(port)')
gcloud redis instances describe ${REDIS_NAME} \
    --region ${REGION} \
    --format 'get(serverCaCerts[0].cert)' > redis-cert.pem
```

## Connect the Online Boutique sample apps to the Memorystore (redis) instance

Update the `cartservice`'s environment variables to point to the Memorystore (redis) instance:
```
kubectl set env deployment/cartservice REDIS_ADDR=${REDIS_IP}:${REDIS_PORT} \
    -n ${NAMESPACE}
```

Remove the default in-cluster `redis` database you won't use anymore:
```
kubectl delete service redis-cart \
    -n ${NAMESPACE}
kubectl delete deployment redis-cart \
    -n ${NAMESPACE}
```

Navigate to the Online Boutique website by clicking on the link below:
```
echo -n "http://" && kubectl get svc frontend-external -n ${NAMESPACE} -o json | jq -r '.status.loadBalancer.ingress[0].ip'
```

You should have a `HTTP Status: 500 Internal Server Error` page at this point. This is expected since we haven't yet set up the TLS communication between `cartservice` and the Memorystore (redis) instance. With the next sections, we will leverage ASM and Istio in order to accomplish this part.

## Install the managed ASM on this cluster

Register your cluster to a [Fleet](https://cloud.google.com/anthos/fleet-management/docs/fleet-concepts):
```
gcloud container fleet memberships register ${CLUSTER} \
    --gke-cluster ${ZONE}/${CLUSTER} \
    --enable-workload-identity
```

Enable ASM in your [Fleet](https://cloud.google.com/anthos/fleet-management/docs/fleet-concepts):
```
gcloud container fleet mesh enable
```

Enable the ASM automatic control plane management to let Google apply the recommended configuration of ASM:
```
gcloud container fleet mesh update \
    --control-plane automatic \
    --memberships ${CLUSTER}
```

## Configure the TLS origination from the Mesh to the Memorystore (redis) instance

Create a `Secret` with the Certificate Authority generated previously:
```
kubectl create secret generic redis-cert \
    --from-file redis-cert.pem \
    -n ${NAMESPACE}
```

Annotate the `cartservice` deployment to mount the `redis-cert` secret via its `istio-proxy` sidecar:
```
kubectl patch deployment cartservice \
    -n ${NAMESPACE} \
    -p '{"spec": {"template":{"metadata":{"annotations":{"sidecar.istio.io/userVolumeMount":"[{\"name\":\"redis-cert\", \"mountPath\":\"/etc/certs\", \"readonly\":true}]"}}}} }'
kubectl patch deployment cartservice \
    -n ${NAMESPACE} \
    -p '{"spec": {"template":{"metadata":{"annotations":{"sidecar.istio.io/userVolume":"[{\"name\":\"redis-cert\", \"secret\":{\"secretName\":\"redis-cert\"}}]"}}}} }'
```

From there we could create `ServiceEntry` and `DestinationRule` allowing to expose this external endpoint in the mesh with a TLS origination setup:
```
INTERNAL_HOST=redis.memorystore-redis
cat <<EOF | kubectl apply -n ${NAMESPACE} -f -
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
cat <<EOF | kubectl apply -n ${NAMESPACE} -f -
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
kubectl label namespace ${NAMESPACE} istio-injection=enabled
```

Wait for ASM to be properly installed on your cluster, FIXME:
```
gcloud container fleet mesh describe
```

Restart the `cartservice` app in order to inject the Istio/ASM sidecar proxies and configs we just deployed previously:
```
kubectl rollout restart deployment cartservice \
    -n ${NAMESPACE}
```

Navigate to the Online Boutique website by clicking on the link below:
```
echo -n "http://" && kubectl get svc frontend-external -n ${NAMESPACE} -o json | jq -r '.status.loadBalancer.ingress[0].ip'
```

You should now see the Online Boutique website working successfully again, now connected to the Memorystore (redis) instance.

## Cleaning up

To avoid incurring charges to your Google Cloud account, you can delete the resources used in this tutorial.

Unregister the GKE cluster from the [Fleet](https://cloud.google.com/anthos/fleet-management/docs/fleet-concepts):
```
gcloud container fleet memberships unregister ${CLUSTER} \
    --project=${PROJECT_ID} \
    --gke-cluster=${ZONE}/${CLUSTER}
```

Delete the GKE cluster:
```
gcloud container clusters delete ${CLUSTER} \
    --zone ${ZONE}
```

Delete the Memorystore (redis) instance:
```
gcloud redis instances delete ${REDIS_NAME}
```

## What's next

- Watch this [Anthos Service Mesh value over Istio OSS episode on YouTube](https://youtu.be/C1y_Ix3ws68).
- Learn more about [ASM security best practices](https://cloud.google.com/service-mesh/docs/security/anthos-service-mesh-security-best-practices).
- Learn more about [Strengthen your app's security with ASM and Anthos Config Management](https://cloud.google.com/service-mesh/docs/strengthen-app-security).