---
title: Using Kubernetes Workload Identity for client-server authorization
description: Demonstrates the use of authorized HTTP clients and server middleware to make the use of Kubernetes Workload Identity more transparent.
author: ptone
tags: Kubernetes, identity
date_published: 2020-02-14
---

Preston Holmes | Solution Architect | Google

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

## Before you begin

We recommend that you run all commands in this tutorial in [Cloud Shell](https://cloud.google.com/shell/), 
the command-line interface built into the Cloud Console, which includes current versions of packages such as `kubectl` and
`envsubst`.

If you choose instead to use the [Google Cloud SDK](https://cloud.google.com/sdk/), then you need to install the SDK and the
[`kubectl`]((https://kubernetes.io/docs/tasks/tools/install-kubectl/)) and `envsubst` packages. This tutorial requires 
`kubectl` version 1.14 and later with
[kustomize integration](https://kubernetes.io/blog/2019/03/25/kubernetes-1-14-release-announcement/).

You can check your `kubectl` version with this command:  

    kubectl version

## Setup

In this section, you create a project, download the tutorial files, and create a GKE cluster.

1.  Create a project in the [Cloud Console](https://console.cloud.google.com/).
1.  [Enable billing for your project](https://cloud.google.com/billing/docs/how-to/modify-project).
1.  Clone the repository that contains the tutorial files, set up a branch, and navigate to the tutorial directory:

        git clone https://github.com/GoogleCloudPlatform/community.git
        cd community
        git checkout workload-id
        cd tutorials/gke-workload-id-clientserver

1.  (Only required if you are *not* using Cloud Shell) Set the project ID by replacing `[YOUR_PROJECT_ID]` with your
    [project ID](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects) in this
    command:

        gcloud config set project [YOUR_PROJECT_ID]

    You can skip setting the project variable if you're using Cloud Shell because Cloud Shell will already have this value
    set for the current project.

1.  Set environment variables:
	
        export PROJECT=$(gcloud config list project --format "value(core.project)" )
        export CLUSTER=workload-id
        export ZONE=us-central1-a
        gcloud config set compute/zone $ZONE
        gcloud config set compute/region us-central1

1.  Create the cluster:

        gcloud beta container clusters create $CLUSTER \
            --identity-namespace=$PROJECT.svc.id.goog

    The `identity-namespace` flag is part of the enablement of the Workload Identity feature. Currently only the single, 
    project-level namespace is supported.

    Creation of the cluster can take several minutes.

1.  Retrieve the cluster credentials:

        gcloud container clusters get-credentials $CLUSTER

## Build and deploy the test server

The test server in this sample is a simple HTTP service that exposes endpoints with and without middleware that enforces
header-based request authentication.

1.  Build the container:

        gcloud builds submit --tag gcr.io/${PROJECT}/auth-server ./server

1.  Configure the server authorization:

        export ISSUER="https://container.googleapis.com/v1/projects/${PROJECT}/locations/${ZONE}/clusters/${CLUSTER}"

    The issuer is an OIDC identity provider that the server trusts, in this case a specific cluster.

1.  Deploy the server with Cloud Run:

        gcloud run deploy --image gcr.io/${PROJECT}/auth-server --allow-unauthenticated --platform managed auth-server --set-env-vars="ID_ISSUER=${ISSUER},JWT_AUDIENCE=TBD"

    Cloud Run offers a convenient way of deploying services with HTTPS, and it also offers its own authorization system that
    is covered in a later section of this tutorial. In this first case, you simply use Cloud Run as a quick way to deploy a
    service external to the cluster that can represent any HTTPS service running on the network.

    By setting the flag `--allow-unauthenticated`, you are requesting that the service be exposed publicly by the Cloud Run
    service. However, there is middleware inside the container that will demonstrate authentication using the cluster-issued
    workload identity.

1.  Get the service URL:

        export SERVICE_URL=$(gcloud run services describe auth-server --platform managed --format='value(status.address.url)')
	
1.  Verify authorization of the base path:

        curl $SERVICE_URL

    The output should be the following:

        {"msg": "hello-exposed"}

    This base path returns a message that is not guarded by any authorization middleware in the service.
    
1.  Verify authorization of the `private` endpoint:

        curl $SERVICE_URL/private
	
    The output should be `401 - Unauthorized`, because the `private` endpoint checks for an authorization
    header and validates the request with it.

1.  Redeploy the server, now that you know the service URL:

        gcloud run deploy --image gcr.io/${PROJECT}/auth-server --allow-unauthenticated --platform managed auth-server --set-env-vars="ID_ISSUER=${ISSUER},JWT_AUDIENCE=${SERVICE_URL}"

### Understanding the authorization middleware

The authorization middleware in this sample is in the `server/auth.go` file. It uses the
[`go-oidc` package](https://github.com/coreos/go-oidc).

This package and middleware perform the following steps:

1.  Uses the `ID_ISSUER` environment variable to retrieve the issuer's public keys through
    [OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata). GKE publishes the public 
    keys at a public URL (`jwks_uri` link in the discovery document at `https://[issuer]/.well-known/openid-configuration`).
1.  Verifies that the token has not expired.
1.  Verifies that the signature on the [JSON Web Token (JWT)](https://jwt.io) sent as a header by the workload was signed by
    the retrieved issuer's public key.
1.  Verifies that the `aud` (audience) claim inside the JWT payload matches the service URL set as
    the `JWT_AUDIENCE` environment variable.

The authorization middleware does *not* perform any authorization actions based on which workload identity has been 
verified—only 1) that it is a valid identity issued by a trusted issuer and 2) that the token was generated for use with 
this target service. The `aud` claim helps to prevent the risk of replay attacks where the same token can be used to 
authenticate against a different service.

## Deploy the client to the cluster

Because Workload Identity is available to a running workload, it is not easily demonstrated with a local `curl` command. 
Instead, in this tutorial, you deploy a simple workload that loops and makes HTTP requests to the server.

The workload makes a set of requests to the exposed and guarded paths on the server. It creates two different HTTP clients 
to make these requests. One is authenticated with the cluster-issued projected service account token, and the other is 
authenticated with the Google-issued Google Cloud IAM service account ID token.

1.  Build the client:

        gcloud builds submit --tag gcr.io/${PROJECT}/auth-client ./client

1.  Configure the client:

        cat client/k-project/project-details-template.yaml | envsubst > client/k-project/project-details.yaml 

    This command uses kustomize to create a project-specific overlay variant of the client Kubernetes resource YAML file.
    For information about why we recommend that you capture these variables in an overlay, instead of modifying the
    Kubernetes YAML file dynamically as part of the `apply` operation, see
    [this explanation](https://github.com/kubernetes-sigs/kustomize/blob/master/docs/eschewedFeatures.md#unstructured-edits).

    The base resources in the configuration are the following:

    * A namespace: `id-namespace`
    * A service account: `gke-sa`
    * A client configuration map
    * A test client pod

1.  Create the client resources in the cluster:

        kubectl create -k client/k-project/
	
1.  Observe the client logs:

        kubectl logs -f auth-client -n id-namespace

    Under `##### Projected token client`, you should see both the exposed and guarded API responses in the logs.

    The guarded response is only returned if the middleware succeeds in validating the JWT as configured above.
    
1.  Press Ctrl-C to stop logging.

### Understanding the projected service account token

In the `k-project/project-details.yaml` file is a pod overlay that includes the following:

    serviceAccountName: gke-sa
    volumes:
    - name: client-token
      projected:
        sources:
        - serviceAccountToken:
            path: gke-sa
            expirationSeconds: 600
            audience: https://auth-server-[hash]-uc.a.run.app

The `serviceAccountName` value specifies which Kubernetes service account the pod runs as.

The `projected:serviceAccountTokens` includes details that expose a signed JWT at a given path, for a specific 
audience.

The same Kubernetes service account can be projected multiple times, each for a different audience.

This line in the `main.go` file rereads this secret whenever it has expired and injects the value as an
`Authorization` header in the form `Authorization: Bearer [JWT_VALUE]`:

    authTransport, err := transport.NewBearerAuthWithRefreshRoundTripper("", cfg.TokenPath, http.DefaultTransport)

## Using Cloud Run Invoker IAM authorization with Workload Identity

Cloud Run offers a [built-in authorization feature](https://cloud.google.com/run/docs/securing/managing-access) that acts as
an alternative to the authorization middleware used in the previous sections of this tutorial. 

When the Cloud Run Invoker IAM feature is employed, the Cloud Run service performs the following checks:

- Is the JWT in an `Authorization` header issued (signed) by `https://accounts.google.com`?
- Is the token un-expired?
- Does the audience claim in the token match the target service?
- Is the `sub` (subject), or principal, of the request a member of the service's IAM invoker role?

The last check—against the service's IAM invoker role—is an additional authorization check not present in the middleware 
discussed in previous sections of this tutorial, and it checks specific service accounts against a list or Google Group 
membership.

If all of these checks pass, then the request is passed on to the Cloud Run service. The code in the container now no
longer needs to implement any authorization middleware.

### Remove the `allow-unauthenticated` option for the Cloud Run service

Cloud Run services are secure by default. There is a special member, `allUsers`, which can be added to the list of invokers, 
which will allow any request to reach the service.

1.  Remove this option:

        gcloud run services remove-iam-policy-binding --role=roles/run.invoker --member allUsers auth-server

    It may take a minute or more for this change in policy to propagate.
    
1.  Attempt to reach the "exposed" base path:

        curl $SERVICE_URL

    You should receive a `403` response.

### Create a service account to associate with Workload Identity

A key use of GKE Workload Identity is to provide a Kubernetes service account with a way to act as a Google Cloud service 
account for accessing Google APIs.

1.  Create the Google Cloud service account in the project:

        gcloud iam service-accounts create gke-gsa

1.  Allow workloads running as the `gke-sa` Kubernetes service account in the `id-namespace` to generate tokens for this
    service account:

        gcloud iam service-accounts add-iam-policy-binding \
            --role roles/iam.serviceAccountTokenCreator \
            --member "serviceAccount:${PROJECT}.svc.id.goog[id-namespace/gke-sa]" \
            gke-gsa@$PROJECT.iam.gserviceaccount.com

    Note that this permission applies to a combination of a project, a namespace, and a service account ID. It will apply
    to any cluster that contains a matching namespace and service account in the project.

1.  Annotate the namespace so that GKE knows that it can make use of the permission that you just granted:

        kubectl annotate serviceaccount \
            --namespace id-namespace \
            gke-sa \
        iam.gke.io/gcp-service-account=gke-gsa@$PROJECT.iam.gserviceaccount.com

Now, the Kubernetes workload has the ability to get credentials and act as the Google Cloud service account.

It can get access these credentials from the metadata server, which most Google Cloud client libraries will do 
transparently. It allows the workload to access both OAuth 2.0 access tokens, as well as the OIDC ID token for the 
associated Google service account.

### Reconfigure the client to use the Google-issued identity

The `main.go` client program contains a switch statement that builds an authenticated HTTP client using the credential 
provided by the metadata server. In this section, you change an environment variable and then update the client 
configuration.

1.  In the `client/k-project/project-details.yaml` file, change the value of an environment variable from
    `IDENTITY: cluster` to `IDENTITY: google` and save the change.

1.  Update the client configuration:

        kubectl delete configmap client-config -n id-namespace
        kubectl delete pod auth-client -n id-namespace
        kubectl apply -k client/k-project

### Add the Google Cloud service account to the invoker policy

Add the associated Google Cloud service account to the invoker policy for the Cloud Run service:

    gcloud run services add-iam-policy-binding --role=roles/run.invoker --member serviceAccount:gke-gsa@$PROJECT.iam.gserviceaccount.com auth-server

In the client workload configured to use the Google-issued identity, the HTTP client does not use the projected token
as the header, but instead reads an ID token from the metadata server at this URL: `http://metadata/computeMetadata/v1/instance/service-accounts/default/identity`

To specify the audience, a query string is used: `?format=full&audience=[URL_of_target_service]`

The response includes a Google-issued ID token for the associated Google Cloud service account, not the cluster-issued 
Kubernetes service account as was done above.

Because this is a Google-issued token, it can be checked against the Cloud Run invoker policy.

### Check client access

After letting the permissions propagate for a moment, check the output of the client:

    kubectl logs -f auth-client -n id-namespace

This time, you should see log lines under `##### mapped GCP SvcAccnt via Metadata server`.

The "exposed" path is reachable. This is the path that the service is exposing without middleware. However, as you saw 
in a previous section, this path is being guarded by Cloud Run. Since you are seeing a response, it means that the token 
that the workload retrieved from the metadata server is passing the validation check by Cloud Run.

You won't see a successful response to the `private` endpoint because it is guarded twice: once by Cloud Run and
IAM, and once by the authorization middleware in the service that is still configured to check that the token was issued by 
the cluster. You can't have a single token "dual issued". The server example here is being used to demonstrate several
scenarios. 

Another scenario that is possible, but not illustrated here, is using Google-issued ID tokens (those with an issuer of
`https://accounts.google.com`) and verifying them yourself in middleware, using one of the libraries provided by Google. 
For information, see
[Authenticate with a backend server](https://developers.google.com/identity/sign-in/web/backend-auth).

## Cleaning up

1.  Delete the client:

        kubectl delete -k client/

1.  Delete the cluster:

        gcloud beta container clusters delete $CLUSTER

1.  Delete the Cloud Run service:

        gcloud run services delete auth-server
