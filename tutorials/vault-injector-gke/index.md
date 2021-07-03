---
title: Injecting secrets into Google Kubernetes Engine Pods using HashiCorp Vault and Google Cloud Auth Method
description: Learn how to inject secrets in applications running in Google Kubernetes Engine (GKE) with the HashCorp Vault Agent Injector.
author: soeirosantos
tags: gcp, gke, google kubernetes engine, workload identity, cloud-native security, devsecops, secrets management, hashicorp vault, vault agent injector
date_published: 2021-07-03
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, we are going to use the [Agent Sidecar Injector](https://www.vaultproject.io/docs/platform/k8s/injector) to read secrets from [HashiCorp Vault](https://www.vaultproject.io/) and inject into Pods running in Google Kubernetes Engine. For this, we are going to use the [Google Cloud Auth method](https://www.vaultproject.io/docs/auth/gcp) with a trust relationship configured based on the [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) to authenticate with Vault.

This tutorial emulates a common use case where we have an external Vault server providing secrets management as a service to multiple clients and applications running in different platforms and environments. And, in this case, we want to connect our workloads running in GKE to this Vault server to read secrets.

## Before you begin

For this tutorial, you need a [Google Cloud project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new one, or select a project that you have already created.

1. Create a [Google Cloud project](https://console.cloud.google.com/cloud-resource-manager).
1. [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your project.
1. For the commands in this tutorial, you use the `gcloud` command-line interface. To install the Cloud SDK, which includes the `gcloud` tool, follow [these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).
1. To install the Vault Agent Injector we'll use the Helm CLI. Check [this doc](https://helm.sh/docs/intro/install/) to install Helm.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
* [Cloud Compute Engine](https://cloud.google.com/compute)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Spin up a Vault server in dev mode

In this first section, we'll use a Google Compute Engine VM to start a [Vault server in dev mode](https://www.vaultproject.io/docs/concepts/dev-server) for experimentation. There is nothing really special with this choice, we just wanted to simulate a situation where the Vault server is external to our Kubernetes cluster and a VM is quick and convenient. Keep in mind to never run a "dev" mode server in production.

1. Let's get started by defining some variables that we will use during the tutorial.

    ```shell
    gcp_project=your-project-name
    cluster_name=your-cluster-name
    cluster_region=us-east1

    gcloud config set project $gcp_project
    ```

1. Execute the following commands to create a file named `startup-script.sh` with the instructions to download and run Vault in dev mode. This file is going to run during the [VM startup](https://cloud.google.com/compute/docs/instances/startup-scripts).

    ```shell
    cat << EOF > startup-script.sh
    #!/bin/bash

    set -e

    wget https://releases.hashicorp.com/vault/1.7.3/vault_1.7.3_linux_amd64.zip
    sudo apt install unzip -y
    unzip vault_1.7.3_linux_amd64.zip

    ./vault server -dev -dev-root-token-id="root" \
        -dev-listen-address="0.0.0.0:8200"  &
    EOF

    chmod +x startup-script.sh
    ```
    
1. Now [create a VM instance](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create) using the startup script to spin up a Vault server.

    ```shell
    gcloud compute instances create vault-dev \
        --tags vault-dev \
        --metadata-from-file=startup-script=startup-script.sh \
        --image-family=ubuntu-1804-lts \
        --image-project=ubuntu-os-cloud \
        --machine-type=e2-small \
        --zone="$cluster_region"-b #change the zone accordingly
    ```
    
1. Add a firewall rule to allow access to the Vault port `8200`.

    ```shell
    gcloud compute firewall-rules create vault-dev \
        --target-tags vault-dev --direction INGRESS \
        --allow tcp:8200
    ```

1. Check if your Vault server is up. (Note that even after the machine is started it may take some seconds to a minute for the installation and initialization to complete)

    ```shell
    VAULT_DEV_PUBLIC_IP=$(gcloud compute instances describe vault-dev \
        --zone ${cluster_region}-b \
        --format="json" \
        --format="value(networkInterfaces.accessConfigs[0].natIP)")

    export VAULT_ADDR=http://"$VAULT_DEV_PUBLIC_IP":8200

    vault status
    # omitting output

    export VAULT_TOKEN=root #the vault token is defined in the startup script
    
    vault secrets list
    # omitting output
    ```

## Create the GKE cluster

1. Execute the gcloud command below to [create the GKE cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-regional-cluster)

    ```shell
    gcloud beta container clusters create "$cluster_name" \
      --release-channel regular \
      --enable-ip-alias \
      --region "$cluster_region" \
      --workload-pool="${gcp_project}".svc.id.goog
    ```

1. Check the Kubernetes configuration:

    ```shell
    kubectl config current-context
    ```

1. If your current context doesn't match the cluster you just created or if you need to connect to it again after changing your kubeconfig, use the get-credentials command to configure your local access to the cluster:

    ```shell
    gcloud container clusters get-credentials \
        "$cluster_name" --region "$cluster_region"
    ```

## Enable and configure the Google Cloud Auth method

1. In order to configure the Google Cloud Auth method we need to [create a Google Service Account](https://cloud.google.com/sdk/gcloud/reference/iam/service-accounts/create) that will be used by the Vault server to validate the incoming login requests. Instead of using existing roles, we will configure a [custom role](https://cloud.google.com/iam/docs/creating-custom-roles) to make sure that the service account is properly privileged with only the required permissions.

    ```shell
    gcloud iam roles create VaultAuthRole \
        --title=vault-auth-role \
        --stage=GA \
        --description="Role used for the Vault Auth Method" \
        --project "$gcp_project" \
        --permissions=iam.serviceAccounts.get,iam.serviceAccountKeys.get,compute.instances.get

    gcloud iam service-accounts create vault-auth-gsa --display-name="vault-auth-gsa"

    gcloud projects add-iam-policy-binding "$gcp_project" \
      --member "serviceAccount:vault-auth-gsa@${gcp_project}.iam.gserviceaccount.com" \
      --role projects/"$gcp_project"/roles/VaultAuthRole

    gcloud iam service-accounts keys create key.json --iam-account=vault-auth-gsa@"$gcp_project".iam.gserviceaccount.com
    ```

1. Enable and configure the Google Cloud Auth method in Vault.

    ```shell
    vault auth enable gcp
    vault write auth/gcp/config credentials=@key.json
    ```

## Configure the workload identity and respective Vault role

1. To configure the workload identity we need a Google Service Account that will be impersonated by a Kubernetes Service Account to access Google Cloud APIs and to establish the trust relationship with Vault.

    ```shell
    gcloud iam service-accounts create my-service-gsa --display-name="my-service-gsa"

    gcloud iam service-accounts add-iam-policy-binding \
      --role roles/iam.workloadIdentityUser \
      --member "serviceAccount:${gcp_project}.svc.id.goog[staging/my-service-ksa]" \
      my-service-gsa@${gcp_project}.iam.gserviceaccount.com

    gcloud projects add-iam-policy-binding "$gcp_project" \
      --member "serviceAccount:my-service-gsa@${gcp_project}.iam.gserviceaccount.com" \
      --role roles/iam.serviceAccountTokenCreator
    ```
    
    The first [policy binding](https://cloud.google.com/sdk/gcloud/reference/iam/service-accounts/add-iam-policy-binding) allows the Kubernetes service account `my-service-ksa` in the namespace `staging` to impersonate the Google service account `my-service-gsa`. The second policy binding allows the Google service account to sign JWTs to perform the Vault login. Worth noting that the only permission necessary for the Vault login is the `iam.serviceAccounts.signJwt` permission. You may consider creating a custom role with fewer privileges as we did for the service account used to configure the Vault server.
    
1. Create a Kubernetes namespace and service account to match the workload identity configured in the previous step.

    ```shell
    kubectl create namespace staging

    kubectl create serviceaccount my-service-ksa -n staging

    kubectl annotate serviceaccount my-service-ksa \
      iam.gke.io/gcp-service-account=my-service-gsa@"$gcp_project".iam.gserviceaccount.com \
      -n staging
    ```
    
1. Check if the workload identity is working as expected.

    ```shell
    kubectl run gcloud -it --rm --restart=Never \
        --serviceaccount my-service-ksa \
        -n staging \
        --image google/cloud-sdk:slim gcloud auth list
    ```

    This command will launch a Pod and check with the command `gcloud auth list` if the active (and only) identity corresponds to the Google service account email address previously configured. You should expect to see the Google service account `my-service-gsa@"$gcp_project".iam.gserviceaccount.com` as active.
    
1. Finally, create the Vault role that binds the Google service account granting access to the secrets.

    ```shell
    vault write auth/gcp/role/my-service-stg-role \
        type="iam" \
        policies="stg" \
        max_jwt_exp="3600" \
        bound_service_accounts="my-service-gsa@${gcp_project}.iam.gserviceaccount.com"
    ```
    
    Note that the policy `stg` doesn't exist yet. We will handle it when we get to the secrets step.
    
1. Check if the Vault login is working as expected.

    ```
    kubectl run vault -it --rm --restart=Never \
        --serviceaccount my-service-ksa \
        -n staging \
        --image vault \
        -- vault login -address="$VAULT_ADDR" -method=gcp service_account="my-service-gsa@${gcp_project}.iam.gserviceaccount.com" role="my-service-stg-role"
    ```
    
    This command will launch a Pod and perform a `vault login` command from within the Pod pointing to our Vault server. You should expect to see a successful response containing a Vault token.
    
## Inject secrets in a Pod

1. Let's start writing some secrets to Vault. For that, we will mount a `kv-v2` secrets engine and create a Vault policy that allows our Vault role to read from this secrets backend.

    ```shell
    vault secrets enable -path=my-service/secrets kv-v2

    vault kv put my-service/secrets/stg/database/config username="db-username" password="db-password"
    
    #check the data just written
    vault kv get my-service/secrets/stg/database/config
    # omitting output

    vault policy write stg - <<EOF
    path "my-service/secrets/data/stg/database/config" {
      capabilities = ["read"]
    }
    EOF
    ```
    
    Note how the `stg` policy allows reading only to the `my-service/secrets/stg` path preventing that our role (and application) would have access to secrets that are not necessary.
    
1. Install the Vault Agent Injector.

    We will follow the standard method to install the Agent Injector using Helm as described in the [installation docs](https://www.vaultproject.io/docs/platform/k8s/injector/installation). Check the [Vault Helm docs](https://www.vaultproject.io/docs/platform/k8s/helm/configuration) for more details about the available options.


    ```shell
    helm version
    version.BuildInfo{Version:"v3.3.1", GitCommit:"249e5215cde0c3fa72e27eb7a30e8d55c9696144", GitTreeState:"dirty", GoVersion:"go1.15"}

    helm repo add hashicorp https://helm.releases.hashicorp.com

    helm search repo hashicorp/vault
    NAME           	CHART VERSION	APP VERSION	DESCRIPTION
    hashicorp/vault	0.13.0       	1.7.3      	Official HashiCorp Vault Chart

    kubectl create ns vault-agent-injector

    helm install vault hashicorp/vault --namespace vault-agent-injector --set="server.enabled=false" --set="injector.externalVaultAddr=$VAULT_ADDR" --set "injector.authPath=auth/gcp"
    ```
    
1. Create a Deployment resource with the Agent Injector annotations.

    ```
    kubectl apply -f - <<EOF
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-service
      namespace: staging
      labels:
        app: my-service
    spec:
      selector:
        matchLabels:
          app: my-service
      replicas: 1
      template:
        metadata:
          annotations:
            vault.hashicorp.com/agent-inject: "true"
            vault.hashicorp.com/agent-inject-status: "update"
            vault.hashicorp.com/auth-type: "gcp"
            vault.hashicorp.com/auth-config-type: "iam"
            vault.hashicorp.com/auth-config-service-account: "my-service-gsa@${gcp_project}.iam.gserviceaccount.com"
            vault.hashicorp.com/role: "my-service-stg-role"
            vault.hashicorp.com/agent-inject-secret-database-config.txt: "my-service/secrets/data/stg/database/config"
            vault.hashicorp.com/agent-inject-template-database-config.txt: |
              {{- with secret "my-service/secrets/data/stg/database/config" -}}
              postgresql://{{ .Data.data.username }}:{{ .Data.data.password }}@postgres:5432/wizard
              {{- end -}}
          labels:
            app: my-service
        spec:
          serviceAccountName: my-service-ksa
          containers:
            - name: my-service
              image: nginx
    EOF
    ```

1. Check that the Pod is running 

    ```shell
    kubectl get po -n staging
    NAME                         READY   STATUS    RESTARTS   AGE
    my-service-d5dcfb55f-w8g89   2/2     Running   0          22s
    ```

    If the Pod is stuck in the `Init` status, check the `vault-agent-init` container logs to identify the problem.
    ```shell
    # run this only if you need to debug
    kubectl logs my-service-d5dcfb55f-w8g89 vault-agent-init -n staging
    ```

1. Check the `my-service` container and verify that the secrets have been injected

    ```shell
    kubectl exec \
        $(kubectl get pod -l app=my-service -n staging -o jsonpath="{.items[0].metadata.name}") \
        -c my-service -n staging -- cat /vault/secrets/database-config.txt

    postgresql://db-username:db-password@postgres:5432/wizard%
    ```

    Check the [Agent Injector documentation](https://www.vaultproject.io/docs/platform/k8s/injector/annotations) for a complete view of the available annotations, configuration options and features.
    
## Cleaning up

1. Delete the GKE cluster
    ```shell
    gcloud container clusters delete "$cluster_name" --region "$cluster_region"
    ```
1. Delete the GCE instance and firewall rule
    ```shell
    gcloud compute instances delete vault-dev --zone "$cluster_region"-b
    gcloud compute firewall-rules delete vault-dev
    ```
1. Delete the custom role and service accounts
    ```shell
    gcloud iam roles delete VaultAuthRole --project "$gcp_project"
    gcloud iam service-accounts delete vault-auth-gsa@"$gcp_project".iam.gserviceaccount.com
    gcloud iam service-accounts delete my-service-gsa@"$gcp_project".iam.gserviceaccount.com
    ```
