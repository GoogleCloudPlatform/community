---
title: Authorizing end users in Cloud Run with Pomerium
description: Learn how to deploy Pomerium to Cloud Run and use it to protect other endpoints with authorization headers.
author: travisgroth,desimone
tags: Cloud Run, Pomerium
date_published: 2020-09-01
---

Travis Groth and Bobby DeSimone | Pomerium

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This guide covers how to deploy Pomerium to Cloud Run, providing end-user authentication and authorization to other endpoints. The resulting configuration
permits users with `@gmail.com` addresses to access an instance of `httpbin.org` hosted on Cloud Run.

[Pomerium](https://www.pomerium.com) is an open source identity-aware proxy that enables secure access to internal applications. Pomerium provides a standardized
interface to add access control to applications regardless of whether the application itself has authorization or authentication built in. Pomerium provides a 
gateway for requests and can be used in situations where you'd typically consider using a VPN.

Unlike [Cloud IAP](https://cloud.google.com/iap), Pomerium supports non-Google identity providers. You can also run Pomerium outside Google Cloud (such as on 
other cloud providers and on-premises) and still use it to route or authorize traffic to Google Cloud targets such as Cloud Run or Cloud Functions.

This guide assumes that you have editor access to a Google Cloud project that can be used for isolated testing and a DNS zone that you are able to control.
DNS does not need to be inside Google Cloud for the example to work.

## How it works

![Architecture](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/architecture.png)

Services on [Cloud Run](https://cloud.google.com/run) and [Cloud Functions](https://cloud.google.com/functions) can be restricted to only permit access with a 
properly signed [identity token](https://cloud.google.com/run/docs/authenticating/service-to-service). This allows requests from other services running on
Google Cloud or elsewhere to be securely authorized despite the endpoints being public.

Browsers are not able to add these identity tokens to the `Authorization` header, so a proxy is required to authenticate end users to your Cloud Run service.
Pomerium can perform this role by generating compatible tokens on behalf of end users and then acting as a proxy for their requests.

You perform the following steps:

- Add an IAM policy delegating `roles/run.invoker` permissions to a service account.
- Run Pomerium with access to a key for the corresponding service account.
- Publish DNS records for each protected application pointing to Pomerium.
- Configure Pomerium with an appropriate policy and `enable_google_cloud_serverless_authentication`.

The protected application delegates trust to a Google Cloud service account, which Pomerium runs as, and Pomerium performs user-based authorization for each
route. This turns Pomerium into a bridge between a user-centric and a service-centric authorization model.

## Setup

To deploy Pomerium to Cloud Run, a [special image](https://console.cloud.google.com/gcr/images/pomerium-io/GLOBAL/pomerium) is available at
`gcr.io/pomerium-io/pomerium:[VERSION]-cloudrun`. It allows sourcing configuration from Google Cloud Secret Manager, and it sets some defaults for Cloud Run to 
keep configuration minimal. This example uses it to store identity provider credentials. Pomerium's
[authorization policy](https://www.pomerium.com/reference/#policy) contains no secrets, so you can place it directly in an
[environment variable](https://www.pomerium.io/reference/#configuration-settings).

The [Dockerfile for this setup for Cloud Run](https://github.com/pomerium/pomerium/blob/master/.github/Dockerfile-cloudrun) is based on the Dockerfile in
[vals-entrypoint](https://github.com/pomerium/vals-entrypoint).

This image depends on a configuration file present at `/pomerium/config.yaml`, and can source it from Google Cloud Secret Manager. To do so, set
`VALS_FILES=[secretref]:/pomerium/config.yaml` and set any other [Pomerium environment variables](https://www.pomerium.io/reference/#configuration-settings) 
directly or with an additional `secretref`.

The `secretref` format for Google Cloud Secret Manager is `ref+gcpsecrets://PROJECT/SECRET(#/key])`.

### Identity provider credentials and secrets in `config.yaml`

Set up Pomerium's [`config.yaml`](https://www.pomerium.com/reference/#shared-settings) to contain your identity provider credentials and secrets:

    # config.yaml
    authenticate_service_url: https://authn.cloudrun.pomerium.com
    shared_secret: XXXXXX
    cookie_secret: XXXXXX
    idp_provider: "google"
    idp_client_id: XXXXXX
    idp_client_secret: "XXXXXX"

### Subdomain and e-mail domain in `policy.template.yaml`

Substitute `cloudrun.pomerium.com` for your own subdomain and your e-mail domain if appropriate:

    # policy.template.yaml
    # see https://www.pomerium.com/reference/#policy
    - from: https://hello.cloudrun.pomerium.com
      to: ${HELLO_URL}
      allowed_domains:
        - gmail.com
      enable_google_cloud_serverless_authentication: true
    - from: https://httpbin.cloudrun.pomerium.com
      to: https://httpbin.org
      pass_identity_headers: true
      allowed_domains:
        - gmail.com

## Deployment

This section includes the commands to configure and deploy Pomerium.

1.  Ensure that you have set a default project:

        gcloud config set default-project MYTESTPROJECT

1.  Set up your environment:

        # Install gcloud beta
        gcloud components install beta

        # Capture current project number
        PROJECT=$(gcloud projects describe $(gcloud config get-value project) --format='get(projectNumber)')

1.  Deploy your protected application:

        gcloud run deploy hello --image=gcr.io/cloudrun/hello --region us-central1 --platform managed --no-allow-unauthenticated

1.  Set the IAM policy:

        gcloud run services add-iam-policy-binding hello --platform managed --region us-central1 \
            --member=serviceAccount:${PROJECT}-compute@developer.gserviceaccount.com \
            --role=roles/run.invoker

1.  Rewrite the policy file with a unique `hello` service URL:

        HELLO_URL=$(gcloud run services describe hello --platform managed --region us-central1 --format 'value(status.address.url)') envsubst <policy.template.yaml >policy.yaml

1.  Install your base configuration in a Google Cloud secret:

        gcloud secrets create --data-file config.yaml pomerium-config --replication-policy automatic

1.  Grant the default compute account access to the secret:

        gcloud secrets add-iam-policy-binding pomerium-config \
            --member=serviceAccount:${PROJECT}-compute@developer.gserviceaccount.com \
            --role=roles/secretmanager.secretAccessor

1.  Deploy Pomerium with policy and configuration references:

        gcloud run deploy pomerium --region us-central1 --platform managed --allow-unauthenticated --max-instances 1 \
            --image=gcr.io/pomerium-io/pomerium:latest-cloudrun \
            --set-env-vars VALS_FILES="/pomerium/config.yaml:ref+gcpsecrets://${PROJECT}/pomerium-config" \
            --set-env-vars POLICY=$(base64 policy.yaml)

## DNS

Pomerium and end users need known hostnames to interact with. To provide this, set up
[Custom Domain Mappings](https://cloud.google.com/run/docs/mapping-custom-domains) for each service.

### Service names

Names to map to each Cloud Run service:

| Cloud Run service | DNS name                             |
| ----------------- | ------------------------------------ |
| `hello`           | `hello-direct.cloudrun.pomerium.com` |
| `pomerium`        | `hello.cloudrun.pomerium.com`        |
| `pomerium`        | `authn.cloudrun.pomerium.com`        |
| `pomerium`        | `httpbin.cloudrun.pomerium.com`      |

 Substitute `cloudrun.pomerium.com` as appropriate.

### Example commands

```bash
    # Set domain mappings for the protected routes and authenticate
    gcloud beta run domain-mappings --platform managed --region us-central1 create --service=hello --domain hello-direct.cloudrun.pomerium.com
    gcloud beta run domain-mappings --platform managed --region us-central1 create --service=pomerium --domain hello.cloudrun.pomerium.com
    gcloud beta run domain-mappings --platform managed --region us-central1 create --service=pomerium --domain authn.cloudrun.pomerium.com
    gcloud beta run domain-mappings --platform managed --region us-central1 create --service=pomerium --domain httpbin.cloudrun.pomerium.com

    # Retrieve the records for configuration in your DNS provider
    gcloud beta run domain-mappings describe --domain hello-direct.cloudrun.pomerium.com --platform managed --region us-central1 --format='get (status.resourceRecords)'
    gcloud beta run domain-mappings describe --domain hello.cloudrun.pomerium.com --platform managed --region us-central1 --format='get (status.resourceRecords)'
    gcloud beta run domain-mappings describe --domain authn.cloudrun.pomerium.com --platform managed --region us-central1 --format='get (status.resourceRecords)'
    gcloud beta run domain-mappings describe --domain httpbin.cloudrun.pomerium.io --platform managed --region us-central1 --format='get (status.resourceRecords)'
```

## Results

### Overview

You should see two applications deployed: The `hello` app is your protected app, and `pomerium` is... Pomerium!

![Cloud Run overview](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/cloudrun-overview.png)

Pomerium allows unauthenticated access, but `hello` does not.

Here are the domain mappings set up:

![Cloud Run domains](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/cloudrun-domains.png)

### Direct access

Verify that you can't access the main application directly by visiting
`https://hello-direct.cloudrun.pomerium.com`.

![Hello Direct Access](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/hello-direct.png)

You should see a 403 error, because you don't have the proper credentials.

### Authenticated access

1.  Go to `https://hello.cloudrun.pomerium.com`.

    You should see a sign-in page:
    
    ![Hello sign-in](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/hello-signin.png)

1.  Enter your credentials at the sign-in page.

    After you enter your credentials, you should see a hello page:

    ![Hello](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/hello-success.png)

### Applications not running on Google Cloud

If your target application is not running on Google Cloud, you can also perform your own header validation.

1.  Go to `https://httpbin.cloudrun.pomerium.com`.

    You should see your identity header set:

    ![Hello](https://storage.googleapis.com/gcp-community/tutorials/cloud-run-with-pomerium-for-end-user-access/headers.png)

See [getting user's identity](https://www.pomerium.com/docs/topics/getting-users-identity.html) for details on using this header.

## What's next

Learn more about Pomerium:

  - [Pomerium home](https://www.pomerium.com)

  - [Pomerium documentation](https://www.pomerium.com/docs/)

  - [Pomerium solution guides](https://www.pomerium.com/guides/)

  - [Pomerium Cloud Run guide](https://www.pomerium.com/guides/cloud-run.html)
