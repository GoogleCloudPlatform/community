---
title: Routing traffic by JSON Web Token claims with Istio
description: Using claims in JSON Web Tokens to route requests with Istio.
author: halvards
tags: Google Kubernetes Engine, GKE, Istio, JWT, Identity Platform
date_published: 2020-08-03
---

Halvard Skogsrud | Solutions Architect | Google

# Routing traffic by JSON Web Token claims with Istio

This tutorial and sample code shows how Istio can route end user traffic based
on claims in JSON Web Tokens (JWTs). The tutorial uses Identity Platform, but
it can be adapted to work with other identity providers.

<walkthrough-alt>

If you like, you can take the interactive version of this tutorial, which runs
in the Cloud Console:

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://ssh.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2FGoogleCloudPlatform%2Fcommunity.git&cloudshell_working_dir=tutorials%2Fclaims-routing-istio&cloudshell_tutorial=index.md)

</walkthrough-alt>

## Introduction

Exposing new features to a subset of your end users can be an effective way to
get feedback on new product features before making them available to all of
your users. The subset of end users could for instance be employees in your
company, or it could be users who opt in to use the new beta features. We call
this subset of users 'beta users' in the rest of this tutorial.

If you deploy a new version of your app with the beta features alongside
the existing version of your app, you need to route requests from beta users to
the new version. To do this, you first need to identify users, for instance by
asking them to sign in. Next, you need to determine which users are beta users.

Looking up this information from your app's database can be difficult, since
request routing decisions are typically made at the edge of your environment.
You may not want to expose your app's database in this part of your network.

[Identity Platform](https://cloud.google.com/identity-platform/) allows you to
configure
[custom claims](https://cloud.google.com/identity-platform/docs/how-to-configure-custom-claims)
on your end users. Identity Platform inserts these custom claims into the
[ID tokens](https://firebase.google.com/docs/auth/admin/manage-sessions)
it issues. Identity Platform ID tokens are
[JSON Web Tokens (JWTs)](https://jwt.io/). You can use custom claims to
identify beta users, and then you can parse the ID tokens at the entry point to
your environment and route requests from beta users to the new version of your
app.

In this tutorial you deploy two versions of a sample app in a Google Kubernetes
Engine (GKE) cluster. The two versions are deployed in separate Kubernetes
namespaces. Istio provides both
[security](https://istio.io/docs/concepts/security/) and
[traffic management](https://istio.io/docs/concepts/traffic-management/)
features. This means we can use Istio to first authenticate and authorize
requests, and then route requests to the correct app version.

You configure Istio to authenticate and authorize requests at the
[ingress gateway](https://istio.io/docs/concepts/traffic-management/#gateways).
This ensures that requests to URL paths starting with `/api/` include ID
tokens issued by Identity Platform in your Google Cloud project.

Istio doesn't support routing by JWT claims out of the box, so you add an
[Envoy filter](https://istio.io/docs/reference/config/networking/envoy-filter/)
that parses the JWT, extracts the beta user claim, and adds a header called
`X-App-Version` with the value of the claim to the incoming request. This
allows the Istio
[virtual service](https://istio.io/docs/concepts/traffic-management/#virtual-services)
to route the request based on the header value. To protect against malicious
users adding the `X-App-Version` header to the request, the Envoy filter first
removes any existing values of the header.

The diagram below shows the resources you create in this tutorial. The
`jwtparse` Envoy filter uses source code provided by the `jwtparse-lua` config
map. The pods of the `istio-ingressgateway` deployment execute the Envoy filter
source code. The `app-vs` virtual service routes requests based on the header
added by the Envoy filter.

![Architecture diagram](https://raw.githubusercontent.com/GoogleCloudPlatform/community/claims-routing-istio/tutorials/claims-routing-istio/architecture.svg "Architecture diagram")

In this diagram, blue heptagons represent Kubernetes resources, and round gray
icons represent Istio
[custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/).

The request routing approach used in this tutorial bears some similarities to
[canary testing](https://cloud.google.com/solutions/application-deployment-and-testing-strategies#canary_test_pattern),
however the goal is different. With canary testing you typically evaluate a
new deployment of the app against a baseline to ensure that the new deployment
is operating at least as well as the previous deployment.

## Objectives

-   Create a GKE cluster.
-   Create an Istio installation manifest.
-   Configure Identity Platform.
-   Create a Cloud IAM service account and a custom role that provides
    permissions to create and update Identity Platform user custom claims.
-   Build a container image for the sample app.
-   Apply manifests to the GKE cluster to:
    *   deploy the stable version of the sample app to the `stable` namespace;
    *   deploy the beta version of the sample app to the `beta` namespace;
    *   install Istio components;
    *   set up Istio authentication and authorization; and
    *   configure Istio routing based on JWT custom claims.
-   Verify the solution.
-   Explore the solution (optional).

## Costs

This tutorial uses the following billable components of Google Cloud:

-   [Cloud Build](https://cloud.google.com/cloud-build/pricing)
-   [Cloud Logging](https://cloud.google.com/stackdriver/pricing)
-   [Container Registry](https://cloud.google.com/container-registry/pricing)
-   [GKE](https://cloud.google.com/kubernetes-engine/pricing)
-   [Identity Platform](https://cloud.google.com/identity-platform/pricing)

To generate a cost estimate based on your projected usage, use the
[pricing calculator](https://cloud.google.com/products/calculator).
New Google Cloud users might be eligible for a free trial.

When you finish this tutorial, you can avoid continued billing by deleting the
resources you created. For more information, see [Cleaning up](#cleaning-up).

## Before you begin

<!-- {% setvar project_id "YOUR_PROJECT_ID" %} -->

1.  <walkthrough-project-billing-setup></walkthrough-project-billing-setup>

    <walkthrough-alt>

    [Sign in](https://accounts.google.com/Login) to your Google Account.

    If you don't already have one,
    [sign up for a new account](https://accounts.google.com/SignUp).

2.  In the Cloud Console, on the project selector page, select or create a Cloud
    project.

    Note: If you don't plan to keep the resources that you create in this
    procedure, create a project instead of selecting an existing project. After
    you finish these steps, you can delete the project, removing all resources
    associated with the project.

    [Go to the project selector page](https://console.cloud.google.com/projectselector2/home/dashboard)

3.  Make sure that billing is enabled for your Google Cloud project.
    [Learn how to confirm billing is enabled for your project.](https://cloud.google.com/billing/docs/how-to/modify-project)

4.  In the Cloud Console, go to Cloud Shell and clone the repository containing
    the sample code.

    [Go to Cloud Shell](https://ssh.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2FGoogleCloudPlatform%2Fcommunity.git&cloudshell_working_dir=tutorials%2Fclaims-routing-istio)

    At the bottom of the screen, click **Confirm** to clone the Git repo into
    your Cloud Shell.

    At the bottom of the Cloud Console, a Cloud Shell session opens and
    displays a command-line prompt. Cloud Shell is a shell environment with the
    Cloud SDK already installed, including the `gcloud` command-line tool, and
    with values already set for your current project. It can take a few seconds
    for the session to initialize. You use Cloud Shell to run all the commands
    in this tutorial.

</walkthrough-alt>

2.  In Cloud Shell, set the Google Cloud project you want to use for this
    tutorial:

    ```bash
    gcloud config set core/project {{project-id}}
    ```

    <walkthrough-alt>

    where `{{project-id}}` is your project ID.

    </walkthrough-alt>

3.  Enable the Google Cloud, Cloud Build, and GKE APIs:

    ```bash
    gcloud services enable \
        cloudapis.googleapis.com \
        cloudbuild.googleapis.com \
        container.googleapis.com
    ```

4.  Define `gcloud` command-line tool default for the Compute Engine region and
    zone that you want to use for this tutorial:

    ```bash
    gcloud config set compute/region us-central1
    gcloud config set compute/zone us-central1-f
    ```

    You can
    [choose a different region and zone](https://cloud.google.com/compute/docs/regions-zones)
    for this tutorial if you like.

## Creating the GKE cluster

1.  Create a GKE cluster with Workload Identity:

    ```bash
    gcloud beta container clusters create claims-routing \
        --enable-ip-alias \
        --enable-stackdriver-kubernetes \
        --machine-type e2-standard-2 \
        --num-nodes 4 \
        --release-channel regular \
        --workload-pool $GOOGLE_CLOUD_PROJECT.svc.id.goog
    ```

2.  Grant the `cluster-admin` Kubernetes role to your Google account. You need
    this to install Istio:

    ```bash
    kubectl create clusterrolebinding cluster-admin-binding \
        --clusterrole cluster-admin \
        --user $(gcloud config get-value core/account)
    ```

## Creating the Istio installation manifest

1.  Define the version of Istio you install:

    ```bash
    ISTIO_VERSION=1.6.6
    ```

2.  Download the
    [`istioctl` command-line tool](https://istio.io/docs/setup/install/istioctl/):

    ```bash
    gsutil -m cp gs://istio-release/releases/$ISTIO_VERSION/istioctl-$ISTIO_VERSION-linux-amd64.tar.gz - | tar zx
    ```

3.  Install Istio base components:

    ```bash
    ./istioctl install \
        --set profile=empty \
        --set components.base.enabled=true
    ```

4.  Generate an Istio installation manifest based on the operator manifest:

    ```bash
    ./istioctl manifest generate \
        --filename manifests/istio/operator/istio-operator.yaml \
        > manifests/istio/base/generated-manifest.yaml
    ```

    You do not apply the generated manifest yet, as you create patches for the
    resources in the manifest in the following sections.

    <walkthrough-editor-select-line
        filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/operator/istio-operator.yaml"
        startLine="15" startCharacterOffset="0"
        endLine="15" endCharacterOffset="0"
        text="Open istio-operator.yaml">
    </walkthrough-editor-select-line>

    <walkthrough-alt>

    `manifests/istio/operator/istio-operator.yaml`:

    [embedmd]:# (manifests/istio/operator/istio-operator.yaml yaml /apiVersion/ /- enabled: true/)
    ```yaml
    apiVersion: install.istio.io/v1alpha1
    kind: IstioOperator
    spec:
      profile: empty
      components:
        base:
          enabled: true
        pilot:
          enabled: true
        ingressGateways:
        - enabled: true
    ```

    </walkthrough-alt>

## Reserving a public IP address

1.  Reserve a public IP address for use with the Istio ingress gateway:

    ```bash
    export EXTERNAL_IP=$(gcloud compute addresses create claims-routing \
        --region $(gcloud config get-value compute/region) \
        --format 'value(address)')
    ```

2.  Display the reserved IP address. You need this later.

    ```bash
    echo $EXTERNAL_IP
    ```

3.  Create [JSON Patch](https://tools.ietf.org/html/rfc6902) files that you
    use to customize the Kubernetes manifests with values containing your
    project ID and reserved IP address:

    ```bash
    find . -name '*.jsonpatch' | xargs -I{} -t sh -c 'envsubst < {} > {}.yaml'
    ```

**Note:** In this tutorial you access the service by using an IP address, and
by using unencrypted HTTP. For a production environment, we recommend you do
both of the following:

-   Create a DNS A record for your domain name and set its value to the public
    IP address you reserved for the Istio ingress gateway. If you're following
    this tutorial, replace `$EXTERNAL_IP` with the domain name of the DNS A
    record. If you use Cloud DNS, follow the
    [Cloud DNS quickstart](https://cloud.google.com/dns/docs/quickstart#create_a_new_record).
    If you use another provider, refer to their documentation.
-   Enable HTTPS. You can do this using
    [Let's Encrypt and cert-manager](https://istio.io/docs/tasks/traffic-management/ingress/ingress-certmgr/).

## Enabling Identity Platform

In this section you enable Identity Platform in your project.
If you like, you can complete this tutorial using Firebase Authentication in
place of Identity Platform. To do so, you use the Firebase Authentication pages
in the Firebase Console instead of the Identity Platform pages in the Cloud
Console.

1.  Go to the **Identity Platform Marketplace** page in the Cloud Console.

    [Go to the Identity Platform Marketplace page](https://console.cloud.google.com/marketplace/details/google-cloud-platform/customer-identity)

2.  Click **Enable Identity Platform**. The Identity Providers page appears in
    the Cloud Console.

## Configuring email sign-in

1.  Go to the **Identity Providers** page in the Cloud Console.

    [Go to the Identity Providers page](https://console.cloud.google.com/customer-identity/providers)

2.  Click **Add A Provider**.

3.  Select **Email/Password** from the list of providers.

4.  Toggle the **Enabled** switch to **On**.

5.  Clear **Allow passwordless login**.

6.  Under **Authorized Domains** on the right-hand side of the screen, click
    **Add domain**. This opens the **Add authorized domain** dialog.

7.  In the **Domain** box, enter the IP address you reserved in the previous
    section (_`$EXTERNAL_IP`_).

8.  Click **Add**. This closes the dialog. The IP address you entered appears
    in the **Authorized Domains** table.

9.  Click **Save**.

## Creating a test user

1.  Go to the Identity Platform **Users** page in the Cloud Console.

    [Go to the Identity Platform Users page](https://console.cloud.google.com/customer-identity/users)

2.  Click **Add user**. This opens the **Add user** dialog.

3.  In the **Email** box, enter the email address of an end user. For testing,
    this email address doesn't have to be real. For this tutorial, use
    `user@example.com`.

4.  In the **Password** box, enter a password for the test user. Remember this
    password, because you need it later.

5.  Click **Add**. This closes the dialog. The new user appears in the
    **Users** table.

## Configuring the sample app

1.  Go to the Identity Platform **Users** page in the Cloud Console.

    [Go to the Identity Platform Users page](https://console.cloud.google.com/customer-identity/users)

2.  Click the **Application setup details** link on the right-hand side of the
    window. This opens the **Configure your application** dialog.

3.  Highlight and copy the value of **apiKey** to your clipboard.

4.  Click **Close**.

5.  In Cloud Shell, create an environment variable to store the value of
    **apiKey** from the **Configure your application** dialog:

    ```bash
    export AUTH_APIKEY=[YOUR_API_KEY]
    ```

6.  Create an environment variable for **authDomain**:

    ```bash
    export AUTH_DOMAIN=$GOOGLE_CLOUD_PROJECT.firebaseapp.com
    ```

7.  Substitute the Identity Platform variables in the JavaScript config file:

    ```bash
    envsubst < app/static/config.tmpl.js > app/static/config.js
    ```

## Configuring Identity and Access Management

1.  In Cloud Shell, create a Cloud Identity and Access Management (IAM) service
    account:

    ```bash
    gcloud iam service-accounts create claims-routing \
        --display-name "Claims-based Istio routing tutorial service account"
    ```

    The sample app uses this service account to access the Identity Platform
    API.

2.  Create a custom Cloud IAM role that provides
    [permissions](https://cloud.google.com/identity-platform/docs/access-control)
    required by this sample app to get and update end user accounts using the
    [`accounts` resource](https://cloud.google.com/identity-platform/docs/reference/rest/v1#rest-resource-v1accounts)
    in the Identity Platform API:

    ```bash
    gcloud iam roles create identityPlatformUserUpdater \
        --description "Get and update end user custom claims using the Identity Platform API" \
        --permissions "firebaseauth.configs.get,firebaseauth.users.get,firebaseauth.users.update" \
        --project $GOOGLE_CLOUD_PROJECT \
        --stage ALPHA \
        --title "Identity Platform End User Updater"
    ```

    You can use the predefined Cloud IAM role
    [`roles/identityplatform.admin`](https://cloud.google.com/iam/docs/understanding-roles#identityplatform.admin)
    instead of creating a custom role, but the predefined role grants
    additional permissions that are not required in this tutorial.

3.  Grant the custom Cloud IAM role to the Cloud IAM service account you
    created:

    ```bash
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member serviceAccount:claims-routing@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
        --role projects/$GOOGLE_CLOUD_PROJECT/roles/identityPlatformUserUpdater
    ```

    **Note:** If you use the Identity Platform
    [multi-tenancy feature](https://cloud.google.com/identity-platform/docs/multi-tenancy)
    in your own environment, grant the `roles/identityplatform.admin`
    predefined role instead of the custom role.

4.  Bind the Cloud IAM service account to Kubernetes service accounts called
    `app` in the `beta` and `stable` namespaces using
    [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity):

    ```bash
    for NS in beta stable ; do \
        gcloud iam service-accounts add-iam-policy-binding \
            claims-routing@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --member "serviceAccount:$GOOGLE_CLOUD_PROJECT.svc.id.goog[$NS/app]" \
            --role roles/iam.workloadIdentityUser
    done
    ```

## Building the sample app

1.  Build the sample app using
    [Cloud Build](https://cloud.google.com/cloud-build)
    and publish the container image to
    [Container Registry](https://cloud.google.com/container-registry). Capture
    the image digest in an environment variable:

    ```bash
    export IMAGE_DIGEST=$(gcloud builds submit ./app \
        --tag gcr.io/$GOOGLE_CLOUD_PROJECT/example.com/claims-routing/cmd/app \
        --format='value(results.images[0].digest)' \
        | tee /dev/stderr | tail -n1)
    ```

    This command uses the `tee` command-line tool to send a copy of the output
    to `stderr`. This allows you to see the build log in your terminal, while
    capturing the image digest from `stdout` in the `IMAGE_DIGEST` environment
    variable.

2.  Populate the [`kustomize`](https://github.com/kubernetes-sigs/kustomize)
    [image tag transformer](https://kubectl.docs.kubernetes.io/pages/reference/kustomize.html#images)
    to replace the image name placeholder `app-image` with the image name and
    digest from the previous step:

    ```bash
    envsubst < manifests/app/kustomization.tmpl.yaml \
        > manifests/app/kustomization.yaml
    ```

    <walkthrough-editor-select-line
        filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/app/kustomization.tmpl.yaml"
        startLine="15" startCharacterOffset="0"
        endLine="15" endCharacterOffset="0"
        text="Open kustomization.tmpl.yaml">
    </walkthrough-editor-select-line>

    <walkthrough-alt>

    `manifests/app/kustomization.tmpl.yaml`:

    [embedmd]:# (manifests/app/kustomization.tmpl.yaml yaml /apiVersion/ /claims-routing\/cmd\/app/)
    ```yaml
    apiVersion: kustomize.config.k8s.io/v1beta1
    kind: Kustomization
    bases:
    - beta
    - stable
    images:
    - digest: $IMAGE_DIGEST
      name: app-image
      newName: gcr.io/$GOOGLE_CLOUD_PROJECT/example.com/claims-routing/cmd/app
    ```

    </walkthrough-alt>

    **Note:** If you have installed the `kustomize` command-line tool, you can
    rename `manifests/app/kustomization.tmpl.yaml` to
    `manifests/app/kustomization.yaml` and use the `kustomize edit set image`
    command instead of the `envsubst` command above.

In this tutorial you use the same container image for both the `beta` and
`stable` versions of the sample app. You use a
[feature toggle](https://martinfowler.com/bliki/FeatureToggle.html)
to enable additional functionality in the `beta` version. You provide this
feature toggle using a Kubernetes ConfigMap resource.

In your own environment, if you want to use a different image for `beta` and
`stable`, you can update the `kustomization.yaml` files in `manifests/app/beta`
and `manifests/app/stable` with different image digests.

## Applying the manifests

1.  Download the third-party dependencies for the Lua Envoy filter:

    ```bash
    ./manifests/istio/route/get-deps.sh
    ```

2.  Apply the manifests to create the Kubernetes resources:

    ```bash
    kubectl apply --kustomize ./manifests
    ```

    `kustomize` orders resource creation to handle dependencies. For instance,
    it creates a namespace before creating resources in that namespace.

3.  Wait for the Istio deployments to be ready:

    ```bash
    for DEPLOY in istio-ingressgateway istiod ; do \
        kubectl rollout status deploy $DEPLOY -n istio-system
    done
    ```

4.  Wait for the sample app deployments to be ready:

    ```bash
    for NS in beta stable ; do \
        kubectl rollout status deploy app -n $NS
    done
    ```

## Verifying the solution

1.  Open a browser window to the address `http://$EXTERNAL_IP`, where
    `$EXTERNAL_IP` is the IP address you reserved for the Istio ingress gateway
    in the section [Reserve a public IP address](#reserve-a-public-ip-address).
    You should see a sign-in form.

2.  Sign in as the test user you created in the section
    [Creating a test user](#creating-a-test-user). You see the sample app home
    page.

3.  Click **Update your preferences**. You should see the **User Preferences**
    form.

4.  Select **Use the beta version**.

5.  Click **Save**. You see a notice saying that your preferences have been
    saved.

6.  Click on the **home page** link. You see the beta version of the home page.

7.  Click **Get answer** to try the beta feature.

## Exploring the solution (optional)

This optional section explores the solution in greater detail.

### Sample app endpoints

The sample app provides the following endpoints:

-   `/`: The app home page.
-   `/signin`: The sign in form
-   `/prefs`: The preferences form where end users can opt into the beta
    version.
-   `/api/user`: Retrieves (for HTTP GET requests) and updates (POST requests)
    user preferences requests.

The beta version of the app provides these additional endpoints:

-   `/beta`: The beta version of the app home page.
-   `/api/beta`: New functionality for beta users.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/pkg/server/server.go"
    startLine="27" startCharacterOffset="0"
    endLine="27" endCharacterOffset="0"
    text="Open server.go">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/pkg/server/server.go`:

[embedmd]:# (app/pkg/server/server.go go /\thttp.HandleFunc\(\"\/api\/user\"/ /handlers\.Index\)/)
```go
	http.HandleFunc("/api/user", userHandler.Claims)
	if config.Is("BETA") {
		http.HandleFunc("/api/beta", api.Beta)
	}

	// public URL paths
	http.Handle("/static/", http.StripPrefix("/static/",
		http.FileServer(http.Dir(config.StaticPath()))))
	http.HandleFunc("/prefs", handlers.Prefs)
	http.HandleFunc("/signin", handlers.SignIn)
	http.HandleFunc("/healthz", handlers.Health)
	if config.Is("BETA") {
		http.HandleFunc("/beta", handlers.Beta)
	}
	http.HandleFunc("/", handlers.Index)
```

</walkthrough-alt>

### Istio authentication and authorization

In this tutorial, Istio enforces authentication and authorization at the
ingress gateway.

The
[`RequestAuthentication`](https://istio.io/latest/docs/reference/config/security/request_authentication/)
resource parses
[bearer tokens](https://istio.io/latest/docs/reference/config/security/jwt/)
on incoming requests.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/auth/requestauthentication.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open requestauthentication.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/auth/requestauthentication.yaml`:

[embedmd]:# (manifests/istio/auth/requestauthentication.yaml yaml /apiVersion/ /forwardOriginalToken: false/)
```yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: app
spec:
  selector:
    matchLabels:
      istio: ingressgateway
  jwtRules:
  - issuer: https://securetoken.google.com/$GOOGLE_CLOUD_PROJECT
    jwksUri: https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com
    outputPayloadToHeader: x-jwt-payload
    forwardOriginalToken: false
```

</walkthrough-alt>

The `forwardOriginalToken: false` field means Istio removes the signed JWT
before forwarding the request to the app. The `outputPayloadToHeader` field
specifies the name of a header that Istio inserts before forwarding the request
to the app. This header contains the payload part of the JWT. This allows the
app to read user information from the JWT payload without requiring access to
the signed JWT.

The `AuthorizationPolicy` resource enforces authorization for endpoints where
the URL path starts with `/api/`.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/auth/authorizationpolicy.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open authorizationpolicy.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/auth/authorizationpolicy.yaml`:

[embedmd]:# (manifests/istio/auth/authorizationpolicy.yaml yaml /apiVersion/ /notPaths:\n        - \/api\/\*/)
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: app
spec:
  action: ALLOW
  selector:
    matchLabels:
      istio: ingressgateway
  rules:
  - to:
    - operation:
        paths:
        - /api/*
    when:
    - key: request.auth.claims[aud]
      values:
      - $GOOGLE_CLOUD_PROJECT
    - key: request.auth.claims[iss]
      values:
      - https://securetoken.google.com/$GOOGLE_CLOUD_PROJECT
  - to:
    - operation:
        notPaths:
        - /api/*
```

</walkthrough-alt>

### Adding the Envoy filter source code to the Istio ingress gateway

A patch to the `istio-ingressgateway` Kubernetes deployment mounts the Lua
source code files used by the Envoy filter on the path `/opt/jwtparse`.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/istio-ingressgateway-patch.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open istio-ingressgateway-patch.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/route/istio-ingressgateway-patch.yaml`:

[embedmd]:# (manifests/istio/route/istio-ingressgateway-patch.yaml yaml /apiVersion/ /name: jwtparse-lua/)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: istio-ingressgateway
spec:
  template:
    spec:
      containers:
      - name: istio-proxy
        volumeMounts:
        - mountPath: /opt/jwtparse
          name: jwtparse
      volumes:
      - name: jwtparse
        configMap:
          name: jwtparse-lua
```

</walkthrough-alt>

The patch mounts the Lua source code from files in a Kubernetes config map. In
this tutorial you use a `kustomize`
[`configMapGenerator`](https://kubectl.docs.kubernetes.io/pages/reference/kustomize.html#configmapgenerator)
to create the config map.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/kustomization.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open route/kustomization.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/route/kustomization.yaml`:

[embedmd]:# (manifests/istio/route/kustomization.yaml yaml /apiVersion/ /- virtualservice\.yaml/)
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
- ../base
configMapGenerator:
- name: jwtparse-lua
  files:
  - basexx.lua
  - json.lua
  - jwtparse.lua
namespace: istio-system
patchesStrategicMerge:
- istio-ingressgateway-patch.yaml
resources:
- envoyfilter.yaml
- gateway.yaml
- virtualservice.yaml
```

</walkthrough-alt>

### Envoy filter

The Envoy Lua filter is added to the filter chain before the `envoy.router`
filter. This means the filter executes before any routing rules specified by
Istio virtual services. The filter contains inline code that adds Lua files in
the `/opt/jwtparse` directory to the Lua runtime package path.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/envoyfilter.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open envoyfilter.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/route/envoyfilter.yaml`:

[embedmd]:# (manifests/istio/route/envoyfilter.yaml yaml /apiVersion/ /require\(\"jwtparse\"\)/)
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: jwtparse
spec:
  workloadSelector:
    labels:
      istio: ingressgateway
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
      listener:
        filterChain:
          filter:
            name: envoy.http_connection_manager
            subFilter:
              name: envoy.router
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.lua
        typed_config:
          "@type": type.googleapis.com/envoy.config.filter.http.lua.v2.Lua
          inlineCode: |-
            -- Add source code files to package path
            package.path = package.path .. ";/opt/jwtparse/?.lua"
            -- JWT parse filter for gateway outbound requests
            require("jwtparse")
```

</walkthrough-alt>

The inline code then loads the `jwtparse` package.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/jwtparse.lua"
    startLine="38" startCharacterOffset="0"
    endLine="38" endCharacterOffset="0"
    text="Open jwtparse.lua">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/route/jwtparse.lua`:

[embedmd]:# (manifests/istio/route/jwtparse.lua lua /-- Lua Envoy filter/ /version_claim\)\nend/)
```lua
-- Lua Envoy filter to extract JWT claims and add them as additional request
-- headers. This filter does the following:
--
-- 1. Removes any existing X-App-Version request headers.
-- 2. Extracts the Bearer JSON Web Token (JWT) from the Authorization header.
-- 3. If there is no JWT in the Authorization header, looks for a JWT payload
--    (the second part of a JWT) in the X-Jwt-Payload header.
-- 4. base64url decodes the token payload.
-- 5. Gets the custom `version` claim from the base64url-decoded token payload.
-- 6. Adds the version claim as a header called X-App-Version to the request.
--
-- References:
-- https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/lua_filter
-- http://www.lua.org/manual/5.1/manual.html

local basexx = require("basexx")
local json = require("json")

local app_version_header = "x-app-version"
local jwt_payload_header = "x-jwt-payload"

function envoy_on_request(handle)
    handle:logDebug("JWT parse filter")
    handle:headers():remove(app_version_header)
    local authorization = handle:headers():get("authorization")
    if not authorization then
        handle:logDebug("No Authorization header in request.")
    end
    local jwt_payload_enc = handle:headers():get(jwt_payload_header)
    if authorization then
        jwt_payload_enc = string.match(authorization, "Bearer .+%.(.+)%..*")
    end
    if not jwt_payload_enc then
        handle:logWarn("No valid Bearer JWT in the Authorization header, " ..
            "and no JWT payload in the X-Jwt-Payload header.")
        return
    end
    local jwt_payload = basexx.from_url64(jwt_payload_enc)
    if not jwt_payload then
        handle:logErr("Could not base64url decode payload from Bearer JWT.")
        return
    end
    local status, version_claim = pcall(
        function() return json.decode(jwt_payload)["version"] end
    )
    if not status then
        handle:logErr("Could not parse base64url decoded JWT payload as " ..
            "valid JSON: " .. jwt_payload)
        return
    end
    if not version_claim then
        handle:logWarn("No version claim in the JWT payload.")
        return
    end
    handle:logDebug("Adding header: " ..
        app_version_header .. "=" .. version_claim)
    handle:headers():replace(app_version_header, version_claim)
end
```

</walkthrough-alt>

The file `jwtparse_test.lua` contains unit tests for the Lua code.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/jwtparse_test.lua"
    startLine="14" startCharacterOffset="0"
    endLine="14" endCharacterOffset="0"
    text="Open jwtparse_test.lua">
</walkthrough-editor-select-line>

<walkthrough-alt>

Here is a sample test from `manifests/istio/route/jwtparse_test.lua`:

[embedmd]:# (manifests/istio/route/jwtparse_test.lua lua /function TestJwtParse\.test_shouldSetAppVersionHeaderFromBearerToken/ /end/)
```lua
function TestJwtParse.test_shouldSetAppVersionHeaderFromBearerToken()
    local handle = fakeRequestHandle("Bearer " .. token_with_version_claim_beta, nil, nil)
    envoy_on_request(handle)
    lu.assertEquals(handle:headers():get(app_version_header), "beta")
end
```

</walkthrough-alt>

### Request routing

The Istio `VirtualService` resource routes end user requests that contain a
`X-App-Version` header with a value of `beta`, and requests to the URL path
`/beta`, to the sample app in the `beta` namespaces. It routes all other
requests to the sample app in the `stable` namespace.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/manifests/istio/route/virtualservice.yaml"
    startLine="15" startCharacterOffset="0"
    endLine="15" endCharacterOffset="0"
    text="Open virtualservice.yaml">
</walkthrough-editor-select-line>

<walkthrough-alt>

`manifests/istio/route/virtualservice.yaml`:

[embedmd]:# (manifests/istio/route/virtualservice.yaml yaml /apiVersion/ /app\.stable\.svc\.cluster\.local/)
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app-vs
spec:
  gateways:
  - ingressgateway
  hosts:
  - '*'
  http:
  - name: route-beta-app
    match:
    - uri:
        prefix: /beta
    route:
    - destination:
        host: app.beta.svc.cluster.local
  - name: route-beta-api
    match:
    - headers:
        x-app-version:
          exact: beta
    route:
    - destination:
        host: app.beta.svc.cluster.local
  - name: route-stable
    route:
    - destination:
        host: app.stable.svc.cluster.local
```

</walkthrough-alt>

Instead of deploying to different namespaces, you can choose to deploy multiple
versions of an app in the same namespace. In that case you can use Istio
[`DestinationRule`](https://istio.io/latest/docs/reference/config/networking/destination-rule/)
resources and the `subset` attribute in your `VirtualService` resource to route
to the different versions of your app.
Using separate namespaces affords better segregation via
[Kubernetes role-based access control (RBAC)](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
but with the additional overhead of managing another namespace.

### Libraries used by the sample app

The sample app uses the following libraries:

-   Go [Identity Platform Admin SDK](https://cloud.google.com/identity-platform/docs/install-admin-sdk#go).
    The app uses this library on the server side to communicate with the
    [Identity Platform REST API](https://cloud.google.com/identity-platform/docs/use-rest-api).
    This library is also known as the
    [Firebase Admin SDK](https://firebase.google.com/docs/auth/admin).

    <walkthrough-alt>

    Below is a code snippet showing how the app uses the
    [`GetUser`](https://pkg.go.dev/firebase.google.com/go/v4/auth?tab=doc#Client.GetUser)
    and
    [`SetCustomUserClaims`](https://pkg.go.dev/firebase.google.com/go/v4/auth?tab=doc#Client.SetCustomUserClaims)
    methods from the Identity Platform Admin SDK to update user custom claims.

    `app/pkg/claims/claims.go`:

    [embedmd]:# (app/pkg/claims/claims.go go /\/\/ AddClaim/ /return nil\n}/)
    ```go
    // AddClaim adds the provided claim to the user specified by the uid parameter.
    // If the user already has the claim, the value is replaced with the provided
    // value argument. All other existing custom claims are retained.
    // Concurrent updates of multiple claims for the same user are not safe.
    func (c *Client) AddClaim(ctx context.Context, uid, claim, value string) error {
    	user, err := c.auth.GetUser(ctx, uid)
    	if err != nil {
    		return err
    	}
    	customClaims := user.CustomClaims
    	if customClaims == nil || len(customClaims) == 0 {
    		customClaims = map[string]interface{}{}
    	}
    	customClaims[claim] = value
    	err = c.auth.SetCustomUserClaims(ctx, uid, customClaims)
    	if err != nil {
    		return err
    	}
    	return nil
    }
    ```

    </walkthrough-alt>

-   [Identity Platform Client SDK](https://cloud.google.com/identity-platform/docs/quickstart-email-password).
    The app uses this library on the client side to inspect Identity Platform
    ID tokens and to react to changes in end user authentication state.
    This library is also known as the
    [Firebase Authentication SDK](https://firebase.google.com/docs/web/setup).

-   [FirebaseUI Auth](https://github.com/firebase/firebaseui-web).
    The app uses this library on the client side to manage the sign-in flow.

### Server-side app logic tests

The test code in the `app/pkg/claims` directory show an example of how you can
test your server-side app logic when using the Go version of the
[Identity Platform Admin SDK](https://cloud.google.com/identity-platform/docs/install-admin-sdk#go)
(also known as the
[Firebase Admin SDK](https://firebase.google.com/docs/auth/admin)).

The
[`Client` struct](https://pkg.go.dev/firebase.google.com/go/v4/auth?tab=doc#Client)
in the `firebase.google.com/go/v4/auth` package has a large surface area with
many methods. In the `claims` package of the app, we define an interface that
contains only the methods our app needs from the `auth.Client` struct.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/pkg/claims/client.go"
    startLine="36" startCharacterOffset="0"
    endLine="36" endCharacterOffset="0"
    text="Open client.go">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/pkg/claims/client.go`:

[embedmd]:# (app/pkg/claims/client.go go /type authClient interface/ /\n}/)
```go
type authClient interface {
	VerifyIDToken(ctx context.Context, idToken string) (*auth.Token, error)
	GetUser(ctx context.Context, uid string) (*auth.UserRecord, error)
	SetCustomUserClaims(ctx context.Context, uid string, customClaims map[string]interface{}) error
}
```

</walkthrough-alt>

In the `claims` package, we also define a `fakeAuthClient` struct that
implements the `authClient` interface. This is a
[test double](https://martinfowler.com/bliki/TestDouble.html) that doesn't call
the
[Identity Platform REST API](https://cloud.google.com/identity-platform/docs/use-rest-api).

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/pkg/claims/client_test.go"
    startLine="34" startCharacterOffset="0"
    endLine="34" endCharacterOffset="0"
    text="Open client_test.go">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/pkg/claims/client_test.go`:

[embedmd]:# (app/pkg/claims/client_test.go go /type fakeAuthClient struct/ /return nil\n}/)
```go
type fakeAuthClient struct {
	users map[string]*auth.UserRecord
}

var _ authClient = &fakeAuthClient{}

// VerifyIDToken fake implementation doesn't verify the JWT signature, it just
// decodes and unmarshalls the payload.
func (t *fakeAuthClient) VerifyIDToken(_ context.Context, idToken string) (*auth.Token, error) {
	jwtPayload := strings.Split(idToken, ".")[1]
	decodedPayload, err := base64.RawURLEncoding.DecodeString(jwtPayload)
	if err != nil {
		return nil, err
	}
	var token auth.Token
	err = json.Unmarshal(decodedPayload, &token)
	if err != nil {
		return nil, err
	}
	// https://github.com/firebase/firebase-admin-go/blob/v4.0.0/auth/token_verifier.go#L291
	token.UID = token.Subject
	return &token, nil
}

// GetUser fake implementation returns a auth.UserRecord that only contains the CustomClaims
// property, since this is all that's needed. The map is copied to prevent false positives and
// false negatives in unit testing.
func (t *fakeAuthClient) GetUser(_ context.Context, uid string) (*auth.UserRecord, error) {
	customClaimsCopy := map[string]interface{}{}
	for k, v := range t.users[uid].CustomClaims {
		customClaimsCopy[k] = v
	}
	return &auth.UserRecord{
		CustomClaims: customClaimsCopy,
	}, nil
}

func (t *fakeAuthClient) SetCustomUserClaims(_ context.Context, uid string, customClaims map[string]interface{}) error {
	t.users[uid].CustomClaims = customClaims
	return nil
}
```

</walkthrough-alt>

The `GetClaim` method from the sample app below calls the
[`GetUser` method](https://pkg.go.dev/firebase.google.com/go/v4/auth?tab=doc#Client.GetUser)
from the Identity Platform Admin SDK. The `GetUser` method from the SDK calls
the Identity Platform REST API, but the `fakeAuthClient` implementation of the
`GetUser` method (seen above) instead looks up the user from its in-memory map.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/pkg/claims/claims.go"
    startLine="25" startCharacterOffset="0"
    endLine="25" endCharacterOffset="0"
    text="Open claims.go">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/pkg/claims/claims.go`:

[embedmd]:# (app/pkg/claims/claims.go go /func \(c \*Client\) GetClaim\(/ /value\), nil\n}/)
```go
func (c *Client) GetClaim(ctx context.Context, uid, claim string) (string, error) {
	user, err := c.auth.GetUser(ctx, uid)
	if err != nil {
		return "", err
	}
	value, exists := user.CustomClaims[claim]
	if !exists {
		return "", nil
	}
	return fmt.Sprintf("%v", value), nil
}
```

</walkthrough-alt>

In the unit tests for `GetClaim`, we use the `fakeAuthClient`.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/pkg/claims/claims_test.go"
    startLine="44" startCharacterOffset="0"
    endLine="44" endCharacterOffset="0"
    text="Open claims_test.go">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/pkg/claims/claims_test.go`:

[embedmd]:# (app/pkg/claims/claims_test.go go /func TestClient_GetClaim\(/ /wantClaim\)\n	}\n}/)
```go
func TestClient_GetClaim(t *testing.T) {
	uid := "foo"
	c := &Client{
		auth: &fakeAuthClient{
			users: map[string]*auth.UserRecord{
				uid: {
					CustomClaims: map[string]interface{}{
						"version": "beta",
					},
				},
			},
		},
	}
	claim, err := c.GetClaim(context.Background(), uid, "version")
	if err != nil {
		t.Error(err)
		return
	}
	wantClaim := "beta"
	if claim != wantClaim {
		t.Errorf("got = %v, want = %v", claim, wantClaim)
	}
}
```

</walkthrough-alt>

### Client-side app logic tests

The contents of the `app/test` directory shows how you can test your
client-side app logic when using the
[Identity Platform Client SDK](https://cloud.google.com/identity-platform/docs/quickstart-email-password)
(also known as the
[Firebase Authentication SDK](https://firebase.google.com/docs/web/setup)).

These tests are
[subcutaneous tests](https://martinfowler.com/bliki/SubcutaneousTest.html)
that verify the user interface behavior without requiring you to run the app or
a web browser.

The tests directly invoke the observer functions that the app code registers
for authentication state change events, such as
[`onAuthStateChanged`](https://firebase.google.com/docs/reference/js/firebase.auth.Auth#onauthstatechanged)
and
[`onIdTokenChanged`](https://firebase.google.com/docs/reference/js/firebase.auth.Auth#onidtokenchanged).

This code snippet shows how the app registered an observer function to the
`onIdTokenChanged` event.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/static/prefs.js"
    startLine="78" startCharacterOffset="0"
    endLine="78" endCharacterOffset="0"
    text="Open prefs.js">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/test/prefs.js`:

[embedmd]:# (app/static/prefs.js js /  firebase\.auth\(\)\.onIdTokenChanged/ /user\);\n  }\);/)
```js
  firebase.auth().onIdTokenChanged(async (user) => {
    if (!user) {
      return;
    }
    await ClaimsRoutingApp.prefs.updateHomePageLink(user);
    await ClaimsRoutingApp.prefs.getPrefs(user);
    ClaimsRoutingApp.prefs.enablePrefsForm(user);
  });
```

</walkthrough-alt>

The `firebase` test double saves a reference to the observer function that
the app code registers.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/test/fakes.js"
    startLine="79" startCharacterOffset="0"
    endLine="79" endCharacterOffset="0"
    text="Open fakes.js">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/test/fakes.js`:

[embedmd]:# (app/test/fakes.js js /\/\*\*\n \* Creates a `firebase`/ /auth\: \(\) => auth,\n  };\n}/)
```js
/**
 * Creates a `firebase` test double that saves observer function references to
 * the provided context object (e.g., tap.context), so we can invoke them
 * directly in tests by accessing the same context object.
 * @param {object} context The test context
 * @return {firebase.auth.Auth}
 */
export function firebase(context = {}) {
  const auth = {};
  auth.onAuthStateChanged = (fn) => {
    context.onAuthStateChanged = fn;
  };
  auth.onIdTokenChanged = (fn) => {
    context.onIdTokenChanged = fn;
  };
  auth.signOut = () => {
    auth.signedOut = true;
  };
  return {
    auth: () => auth,
  };
}
```

</walkthrough-alt>

This test invokes the registered observer function via the test `context`
object.

<walkthrough-editor-select-line
    filePath="cloudshell_open/community/tutorials/claims-routing-istio/app/test/prefs_test.js"
    startLine="85" startCharacterOffset="0"
    endLine="85" endCharacterOffset="0"
    text="Open prefs_test.js">
</walkthrough-editor-select-line>

<walkthrough-alt>

`app/test/prefs_test.js`:

[embedmd]:# (app/test/prefs_test.js js /t\.test\(\'should update form to reflect beta/ /checked\);\n  t\.end\(\);\n}\);/)
```js
t.test('should update form to reflect beta user custom claims', async (t) => {
  // get handy `window` and `document` references
  const window = t.context.dom.window;
  const document = window.document;

  // directly invoke firebase event handler with beta user
  await t.context.onIdTokenChanged(fake.user({version: 'beta'}));

  t.ok(document.getElementById('version_beta').checked);
  t.end();
});
```

</walkthrough-alt>

## Troubleshooting

If you run into problems with this tutorial, we recommend that you review these
documents:

-   [Identity Platform error codes](https://cloud.google.com/identity-platform/docs/error-codes)
-   [GKE troubleshooting](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)
-   [Istio operations common problems](https://istio.io/docs/ops/common-problems/)
-   [Troubleshooting Kubernetes clusters](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/)

## Cleaning up

To avoid incurring continuing charges to your Google Cloud Platform account for
the resources used in this tutorial you can either delete the project or delete
the individual resources.

### Deleting the project

**Caution:**  Deleting a project has the following effects:

-   **Everything in the project is deleted.** If you used an existing project
    for this tutorial, when you delete it, you also delete any other work
    you've done in the project.
-   **Custom project IDs are lost.** When you created this project, you might
    have created a custom project ID that you want to use in the future. To
    preserve the URLs that use the project ID, such as an `appspot.com` URL,
    delete selected resources inside the project instead of deleting the whole
    project.

In Cloud Shell, run this command to delete the project:

```bash
echo $GOOGLE_CLOUD_PROJECT
gcloud projects delete $GOOGLE_CLOUD_PROJECT
```

### Deleting the resources

If you want to keep the Google Cloud project you used in this tutorial, delete
the individual resources:

1.  In Cloud Shell, delete the GKE cluster:

    ```bash
    gcloud container clusters delete claims-routing --async --quiet
    ```

2.  Remove the Cloud IAM role grant for the service account you used in
    this tutorial:

    ```bash
    gcloud projects remove-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
        --member serviceAccount:claims-routing@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
        --role projects/$GOOGLE_CLOUD_PROJECT/roles/identityPlatformUserUpdater
    ```

3. Remove the Workload Identity policy bindings for the service account you
    used in this tutorial:

    ```bash
    for NS in beta stable ; do \
        gcloud iam service-accounts remove-iam-policy-binding \
            claims-routing@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
            --member "serviceAccount:$GOOGLE_CLOUD_PROJECT.svc.id.goog[$NS/app]" \
            --role roles/iam.workloadIdentityUser
    done
    ```

4.  Delete the Cloud IAM service account:

    ```bash
    gcloud iam service-accounts delete --quiet \
        claims-routing@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com
    ```

5.  Release the reserved public IPv4 address:

    ```bash
    gcloud compute addresses delete claims-routing --quiet
    ```

6.  Delete the sample app container image:

    ```bash
    gcloud container images list-tags \
        gcr.io/$GOOGLE_CLOUD_PROJECT/example.com/claims-routing/cmd/app \
        --format 'value(digest)' | xargs -I {} gcloud container images \
        delete --force-delete-tags --quiet \
        gcr.io/$GOOGLE_CLOUD_PROJECT/example.com/claims-routing/cmd/app@sha256:{}
    ```

7.  Delete the test user:

    -   Go to the Identity Platform **Users** page in the Cloud Console.

        [Go to the Identity Platform Users page](https://console.cloud.google.com/customer-identity/users)

    -   Find the test user `user@example.com` and click the **Delete** icon.
        This opens a dialog.

    -   In the dialog, click **Delete**. The dialog closes.

8.  Disable the identity provider:

    -   Go to the **Identity Providers** page in the Cloud Console.

        [Go to the Identity Providers page](https://console.cloud.google.com/customer-identity/providers)

    -   Find the **Email / Password** identity provider and toggle the
        **Enabled** switch to **Off**. This opens a confirmation dialog.

    -   In the dialog, click **Confirm**. The dialog closes.

## What's next

-   Read more about
    [configuring custom claims on end users](https://cloud.google.com/identity-platform/docs/how-to-configure-custom-claims)
    in Identity Platform.
-   Learn how to
    [authenticate end users of Cloud Run for Anthos services using Istio and Identity Platform](https://cloud.google.com/solutions/authenticating-cloud-run-on-gke-end-users-using-istio-and-identity-platform).
-   Learn how to
    [authorize access to Cloud Run for Anthos services using Istio](https://cloud.google.com/solutions/authorizing-access-to-cloud-run-on-gke-services-using-istio).
-   Read about how to use
    [Identity Platform multi-tenancy](https://cloud.google.com/identity-platform/docs/multi-tenancy)
    to create unique silos of users and configurations within a single Identity
    Platform project.
-   Discover how to
    [use Identity Platform identities with Identity-Aware Proxy](https://cloud.google.com/iap/docs/external-identities).
-   Explore other
    [Identity Platform how-to guides](https://cloud.google.com/identity-platform/docs/how-to).
-   Try out other Google Cloud features for yourself. Have a look at our
    [tutorials](https://cloud.google.com/docs/tutorials).
