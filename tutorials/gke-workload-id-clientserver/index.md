---
title: Using Kubernetes Workload Identity for client-server authentication
description: Demonstrates the use of authorized HTTP clients and server middleware to make the use of Kubernetes Workload Identity more transparent.
author: ptone
tags: Kubernetes, identity
date_published: 2020-02-14
---

Preston Holmes | Solution Architect | Google

## Introduction

Kubernetes service accounts have been the primary mechanism of identity in Kubernetes clusters. They have been usable with 
Kubernetes (role-based access control) RBAC to control authorization to the Kubernetes API server. Historically, these have 
been globally scoped credentials, and subject to relatively high replay risk and not usable outside the context of the
cluster.

With Kubernetes 1.12 and later, service account credentials can be exposed to workloads with a specific audience applied,
using the
[Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection) feature.

A service account token is exposed as a signed [JSON Web Token (JWT)](https://en.wikipedia.org/wiki/JSON_Web_Token). The
private keys that sign these tokens are specific to the cluster. In 
[Google Kubernetes Engine (GKE)]((https://cloud.google.com/kubernetes-engine/)), when 
[Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) is enabled, the 
corresponding public keys are published at a URL that can be derived from the issuer field in the token conforming to the 
[OpenID Connect (OIDC) Discovery standard](https://openid.net/specs/openid-connect-discovery-1_0.html).

In GKE, the Workload Identity feature allows these identities to also be associated with 
[Cloud IAM service accounts](https://cloud.google.com/iam/docs/service-accounts). This allows a pod running as a Kubernetes 
service account to act as the associated service account for authorized access to Google APIs and to services that verify 
identity based on GCP-specific OIDC.

To make the use of this identity system easier for application developers, the mechanism can be made more transparent to 
both the client and the server. On the client side, a derived authorized HTTP client can be used that automatically injects
the service account token into all outgoing HTTP requests. On the server side, authorization middleware can use OIDC 
discovery and the cluster's public key to verify the request, before passing on the the business logic of the 
function/handler. This tutorial demonstrates the use of these conveniences in the Go programming language.

## Objectives

1. Set up a GKE cluster with Workload Identity.
1. Use Service Account Token Volume Projection to provide a cluster-issued OIDC ID token to a workload.
1. Use the cluster-specific public keys to verify the workload's ID token in a remote service.
1. Associate Workload Identity and namespace with a Google service account.
1. Retrieve credentials from the Google service account through Workload Identity association.
1. Use the Google-issued ID token to call a Cloud Run service behind IAM invoker authorization.

## Setup

We recommend that you run all commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell/), 
the command-line interface built into the Cloud Console, which includes current versions of packages such as `kubectl` and
`envsubst`.

If you choose instead to use the [Google Cloud SDK](https://cloud.google.com/sdk/), then you need to install the SDK and the
[`kubectl`]((https://kubernetes.io/docs/tasks/tools/install-kubectl/)) and `envsubst` packages. This tutorial requires 
`kubectl` version 1.14 and later with
[kustomize integration](https://kubernetes.io/blog/2019/03/25/kubernetes-1-14-release-announcement/).

You can check your `kubectl` version with this command:  

    kubectl version

### Set up the project

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).

### Get the tutorial files

Clone the repository, set up a branch, and navigate to the tutorial directory:

    git clone https://github.com/GoogleCloudPlatform/community.git
    cd community
    git checkout workload-id
    cd tutorials/gke-workload-id-clientserver

### Set environment variables

Use the following commands to set environment variables in each shell that you use. You can skip setting the project 
variable if you're using Cloud Shell, since Cloud Shell will already have this value set for the current project.
	
    # the project should already be set in Cloud Shell
    gcloud config set project [YOUR_PROJECT_ID]
    export PROJECT=$(gcloud config list project --format "value(core.project)" )
    export CLUSTER=workload-id
    export ZONE=us-central1-a
    gcloud config set compute/zone $ZONE
    gcloud config set compute/region us-central1

### Create the cluster

The following command creates the cluster:

    gcloud beta container clusters create $CLUSTER \
        --identity-namespace=$PROJECT.svc.id.goog

The `identity-namespace` flag is part of the enablement of the Workload Identity feature. Currently only the single, 
project-level namespace is supported.

Creation of the cluster can take several minutes.

### Retrieve the cluster credentials

The following command gets the cluster credentials:

    gcloud container clusters get-credentials $CLUSTER

## Build and deploy the test server

The test server in this sample is a simple golang HTTP service that exposes endpoints with and without middleware that enforce header-based request authentication.

### Build the container

	gcloud builds submit --tag gcr.io/${PROJECT}/auth-server ./server

### Configure the server authorization

	export ISSUER="https://container.googleapis.com/v1/projects/${PROJECT}/locations/${ZONE}/clusters/${CLUSTER}"

The issuer is OIDC Identity Provider the server trusts, in this case a specific cluster.

### Deploy the server via Cloud Run

**NOTE: Cloud Run offers a convenient way of deploying services with HTTPS, and also offers its own authorization system that will be covered below. In this first case you are simply using it as a quick way to deploy a service external to the cluster that can represent any HTTPS service running on the network.**

By setting the flag `--allow-unauthenticated` you are requesting that the service be exposed publicly by the Cloud Run service. However, there is middleware inside the container that will demonstrate authentication using the cluster-issued workload identity.

	gcloud run deploy --image gcr.io/${PROJECT}/auth-server --allow-unauthenticated --platform managed auth-server --set-env-vars="ID_ISSUER=${ISSUER},JWT_AUDIENCE=TBD"
	
### Get the service URL and Verify authorization

	export SERVICE_URL=$(gcloud run services describe auth-server --platform managed --format='value(status.address.url)')
	curl $SERVICE_URL

This should return:

  	{"msg": "hello-exposed"}

This base path returns a msg that is not guarded by any auth middleware in the service.

		curl $SERVICE_URL/private

_should get 401 - Unauthorized_

The private endpoint checks for a auth header and validates.

### Understanding the auth middleware.

The auth middleware in this sample is in the `server/auth.go` file. It uses the `github.com/coreos/go-oidc` package.

This package and middleware perform the following steps:

1. Uses the `ID_ISSUER` env var to retrieve the issuer's public keys via [OIDC discovery standard](https://openid.net/specs/openid-connect-discovery-1_0.html). GKE publishes the public keys at a public URL (jwks_uri link in the discovery doc at [issuer] + '/.well-known/openid-configuration').
1. Verifies that the token has not expired
1. Verifies the signature on the [JWT](https://jwt.io) token sent as a header by the workload as being signed by the retrieved issuer's public key.
1. Verifies the `aud` claim inside the JWT payload matches the service URL set as `JWT_AUDIENCE` env var

The auth middleware does NOT perform any authorization actions based on which workload identity has been verified, only that it is a valid identity issued by a trusted issuer, and that the token was generated for use with this target service (the `aud` helps prevent the risk of replay attacks where the same token can be used to authenticate against a different service).

### Redeploy server

Because the `aud` claim is key to the verification processes, and because you did not know the service URL until you had first deployed the service, there was no value set for the `JWT_AUDIENCE` env var. With this value now known, redeploy the service with the updated env var: 

	gcloud run deploy --image gcr.io/${PROJECT}/auth-server --allow-unauthenticated --platform managed auth-server --set-env-vars="ID_ISSUER=${ISSUER},JWT_AUDIENCE=${SERVICE_URL}"

## Deploy the client to the cluster

Because workload identity is available to a running workload, it is not easily demonstrated with a local `CURL` command. Instead - you will deploy a simple workload that loops and makes HTTP requests to the server.

### Build the client:

		gcloud builds submit --tag gcr.io/${PROJECT}/auth-client ./client

### Configure the client

This next step uses Kustomize to create a project specific overlay variant of the client kubernetes resource yaml:

		cat client/k-project/project-details-template.yaml | envsubst > client/k-project/project-details.yaml 

See [this explanation](https://github.com/kubernetes-sigs/kustomize/blob/master/docs/eschewedFeatures.md#unstructured-edits) of why you want to capture these variables into an overlay, instead of modifying the Kubernetes yaml dynamically as part of the apply.

The base resources are:

* A namespace: `id-namespace`
* A service account: `gke-sa`
* A client config map
* A test-client pod

Create the client resources in the cluster:

		kubectl create -k client/k-project/

The workload makes a set of requests to the 'exposed' and 'guarded' paths on the server. It creates two different HTTP clients to make these requests.

One is authenticated with the cluster-issued projected service account token, and the other is authenticated with the Google-issued GCP-IAM Service Account id-token which will be discussed below.

### Understanding the projected service account token

If you look at the `k-project/project-details.yaml` you will see a pod overlay which includes:

  serviceAccountName: gke-sa
  volumes:
  - name: client-token
    projected:
      sources:
      - serviceAccountToken:
          path: gke-sa
          expirationSeconds: 600
          audience: https://auth-server-[hash]-uc.a.run.app

The `serviceAccountName` specifies which Kubernetes Service Account the pod runs as.

The `projected:serviceAccountTokens` includes details that expose a signed JWT token at a given path, for a specific audience.

The same Kubernetes service account can be projected multiple times, each for a different audience.

The client line:

  	authTransport, err := transport.NewBearerAuthWithRefreshRoundTripper("", cfg.TokenPath, http.DefaultTransport)

Will re-read this secret whenever it has expired, and inject the value as a `Authorization` header in the form of:

		Authorization: Bearer [JWT value]


### Observe the client logs

		kubectl logs -f auth-client -n id-namespace

Look for the lines under `##### Projected token client`

You should see both the exposed and guarded API responses in the logs.

The guarded response is only returned if the middleware succeeds in validating the JWT token as configured above. Use `ctrl-c` to stop logging.

## Using Cloud Run IAM invoker authorization with workload identity

Cloud Run offers a built in auth feature that acts as an alternative to the auth middleware used above. When this is employed, the Cloud Run service performs the following checks:

1. Is the JWT in an Authorization header issued (signed) by https://accounts.google.com?
1. Is the token un-expired?
1. Does the audience claim in the token match the target service?
1. Is the `sub` (subject), or principal, of the request a member of the Service's IAM "invoker" role?

That last step is an additional authorization check not present in the middleware above, and checks specific service accounts against a list or Google Group membership.

If all these checks pass, then the request is passed on to the Cloud Run Service. The code in the Docker container now no longer needs to implement any auth middleware.

### Remove the "allow-unauthenticated" option for the Cloud Run service

Cloud Run services are actually secure by default. There is a special member called 'allUsers' which can be added to the list of invokers which will allow any request to reach the service.

  	gcloud run services remove-iam-policy-binding --role=roles/run.invoker --member allUsers auth-server

It may take a **minute** or so for this change in policy to propagate, but if you now try to reach the "exposed" base path, you will see a 403 response:

		curl $SERVICE_URL

### Create a Service account to associate with workload identity (a GKE Google Service Account):

A key use of GKE workload identity - is to provide Kubernetes service accounts a way to act as a GCP service account for accessing Google APIs. The first step is to create the GCP Service account in the project:

  	gcloud iam service-accounts create gke-gsa

Allow workloads running as the 'gke-sa' kubernetes service account in the 'id-namespace' to generate tokens for this service account.

	gcloud iam service-accounts add-iam-policy-binding \
		--role roles/iam.serviceAccountTokenCreator \
		--member "serviceAccount:${PROJECT}.svc.id.goog[id-namespace/gke-sa]" \
		gke-gsa@$PROJECT.iam.gserviceaccount.com

Note that this permission applies to a project + namespace + service-account-id, it will apply to any cluster that contains a matching namespace and service-account in the project.

Now you need to annotate the namespace so that GKE knows it can make use of the permission you just granted.

	kubectl annotate serviceaccount \
		--namespace id-namespace \
		gke-sa \
	iam.gke.io/gcp-service-account=gke-gsa@$PROJECT.iam.gserviceaccount.com

Now the kubernetes workload has the ability to get credentials and 'act-as' the GCP service account.

It can get access these credentials from the metadata server, which most Cloud client libraries will do transparently. It allows the workload to access both Oauth2 access tokens, as well as the OIDC id-token for the associated Google Service Account.

### Reconfigure the client to use the Google-issued identity

In the file `client/k-project/project-details.yaml` change the value of an environment variable from:

		IDENTITY: cluster

to:

		IDENTITY: google

You can see in the client program a switch statement that builds an authenticated HTTP client using a mechanism using the credential provided by the metadata server.

Update the client configuration after saving the change:

	kubectl delete configmap client-config -n id-namespace
	kubectl delete pod auth-client -n id-namespace
	kubectl apply -k client/k-project

### Add the associated GCP service-account to the invoker policy for the Cloud Run Service

		gcloud run services add-iam-policy-binding --role=roles/run.invoker --member serviceAccount:gke-gsa@$PROJECT.iam.gserviceaccount.com auth-server

In the client workload configured to use the Google-issued identity, the HTTP client does not use the projected token as the header, but instead reads an id-token from the metadataserver made available at:

`http://metadata/computeMetadata/v1/instance/service-accounts/default/identity`

To specify the audience, a query-string is used: `?format=full&audience=[URL of target service]`

The response includes a Google issued id-token for the associated GCP service account, not the cluster-issued kubernetes service account as was done above.

Because this is a Google issued token, it can be checked against Cloud Run's invoker policy.

### Check client access

After letting the permissions propagate for a second - check the output of the client:

		kubectl logs -f auth-client -n id-namespace

This time you will see log lines under: `##### mapped GCP SvcAccnt via Metadata server`

You will see that the "exposed" path is reachable. This is the path the service is exposing without middleware. However as you saw above, it is being guarded by Cloud Run. Since you are seeing a response, it means that the token the workload retrieved from the metadata server is passing the validation check by Cloud Run.

You won't see a successful response to the /private endpoint, as this is now being "doubled guarded". Once by Cloud Run and IAM, and once by the auth middleware in the service that is still configured to check that the token was issued by the cluster. You can't have a single token "dual issued". The server example here is being used to demonstrate several scenarios. 

Also, a scenario that is possible, but not illustrated here, is using the Google issued id-tokens (those with an issuer of https://accounts.google.com) and verify them yourself in auth middleware, using on of Googles provided libraries, see https://developers.google.com/identity/sign-in/web/backend-auth.

## Cleaning Up

### Delete the client

		kubectl delete -k client/

### Delete the cluster

		gcloud beta container clusters delete $CLUSTER

### Delete the Cloud Run Service

		gcloud run services delete auth-server





