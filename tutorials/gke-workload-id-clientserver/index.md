---
title: Using Kubernetes Workload identity for client-server auth
description: Demonstrates the use of authorized HTTP clients and server middleware to make the use of Kubernetes workload identity more transparent.
author: ptone
tags: Kubernetes, identity
date_published: 2019-07-11
---

Preston Holmes | Solution Architect | Google

## Introduction

Kubernetes service accounts have been the primary mechanism of identity in Kubernetes clusters.  They have been usable with Kubernetes RBAC to control authorization to the Kubernetes API Server. Historically, these have been globally scoped credentials, and subject to relatively high replay risk.

With Kubernetes 1.12, service account credentials can now be exposed to workloads with a specific audience applied. The feature is called [Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection).

Service account tokens are exposed as signed [JWT](https://jwt.io) tokens. The private keys that sign these tokens are specific to the cluster. In GKE, when workload identity is enabled, the corresponding public keys are published at a URL that can be derived from the issuer field in the token conforming to the [OIDC discovery standard](https://openid.net/specs/openid-connect-discovery-1_0.html).

In order to make the use of this identity system easier for application developers, the mechanism can be made more transparent to both the client and the server. On the client, a derived authorized HTTP client can be used that automatically injects the service account token in all outgoing HTTP requests. On the server side, authorization middleware can use OIDC discovery and the cluster's public key to verify the request, before passing on the the business logic of the function/handler. This tutorial demonstrates the use of these conveniences in both golang (and soon Python).

## Setup

### Setting up the cloud environment
1.  Create a project in the [GCP Console][console].
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Use [Cloud Shell][shell] or install the [Google Cloud SDK][sdk].

### Clone the tutorial Repo
#### TODO update to prod

	git clone https://github.com/ptone/community.git
	cd community
	git checkout workload-id
	cd tutorials/gke-workload-id-clientserver

Set these environment variables in each shell you use:
	
	# the project should already be set in cloud shell
	gcloud config set project [your project]
	export PROJECT=$(gcloud config list project --format "value(core.project)" )
	export CLUSTER=workload-id
	export ZONE=us-central1-a
	gcloud config set compute/zone $ZONE
	gcloud config set compute/region us-central1
	
	
[console]: https://console.cloud.google.com/
[shell]: https://cloud.google.com/shell/
[sdk]: https://cloud.google.com/sdk/

## Set up the cluster

	gcloud beta container clusters create $CLUSTER \
	   --identity-namespace=$PROJECT.svc.id.goog

You will also need a recent `kubectl` command (>=1.14) with [kustomize integration](https://kubernetes.io/blog/2019/03/25/kubernetes-1-14-release-announcement/). If not, install it from [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/). Ensure that Kubectl is configured to talk to your cluster.

## Build and deploy the server container

### Build the container

	cd server
	gcloud builds submit --tag gcr.io/${PROJECT}/auth-server .

### get server auth configuration

	export ISSUER="https://container.googleapis.com/v1/projects/${PROJECT}/locations/${ZONE}/clusters/${CLUSTER}"
	
### Deploy the server via cloud run

**CAVEAT: Cloud Run offers a convenient way of deploying services with HTTPS, but also offers its own authorization system that is not currently compatible with GKE workload identities. This pattern can be used anywhere a HTTPS service can be deployed, but setting up HTTPS on a VM is substantially more involved (see https://cloud-tutorial.dev)**

	gcloud beta run deploy --image gcr.io/ptone-kf/auth-server --allow-unauthenticated --platform managed auth-server --set-env-vars='ID_ISSUER=${ISSUER},JWT_AUDIENCE=${SERVICE_URL}'
	
### Get the service URL and Verify authorization

	export SERVICE_URL=$(gcloud beta run services describe auth-server --platform managed --format='value(status.address.url)')
	curl $SERVICE_URL
	# returns public API
	curl $SERVICE_URL/private
	# should get 401 - Unauthorized

## Deploy the client to the cluster

### Build the client:


	gcloud builds submit --tag gcr.io/${PROJECT}/auth-server ./client

### Configure the client

#### TODO move to envsubst ?

Update the values for the image to gcr.io/${PROJECT}/auth-server and SERVICE_ENDPOINT and audience to the $SERVICE_URL

### Deploy the client

	kubectl create -k client/

### Observe the client logs

	kubectl logs -f auth-client -n id-namespace

You should see both the public and private API responses in the logs

### Delete the client

	kubectl delete -k client/





