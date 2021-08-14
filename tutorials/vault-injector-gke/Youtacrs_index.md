---
title: Injecting secrets into Google Kubernetes Engine Pods using HashiCorp Vault and Google Cloud Auth
description: Learn how to inject secrets in applications running in Google Kubernetes Engine (GKE) with the HashCorp Vault Agent Injector.
author: soeirosantos
tags: gcp, gke, google kubernetes engine, workload identity, cloud-native security, devsecops, secrets management, hashicorp vault, vault agent injector
date_published: 2021-08-09
---

Romulo Santos

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial, you use the [Agent Sidecar Injector](https://www.vaultproject.io/docs/platform/k8s/injector) to read secrets from
[HashiCorp Vault](https://www.vaultproject.io/) and inject secrets into Pods running in Google Kubernetes Engine. This tutorial uses the
[Google Cloud Auth method](https://www.vaultproject.io/docs/auth/gcp) with a trust relationship configured based on
[Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) to authenticate with Vault.

This tutorial emulates a common use case in which you have an external Vault server providing secrets management as a service to multiple clients and 
applications running in different platforms and environments. In this case, you connect your workloads running in GKE to this Vault server to read secrets.

## Before you begin

For this tutorial, you need a [Google Cloud project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new one, or select a project that you have already created.

1.  Create a [Google Cloud project](https://console.cloud.google.com/cloud-resource-manager).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for your project.
1.  For the commands in this tutorial, you use the `gcloud` command-line interface. To install the Cloud SDK, which includes the `gcloud` tool, follow
    [these instructions](https://cloud.google.com/sdk/gcloud/#downloading_the_gcloud_command-line_tool).
1.  To install the Vault Agent Injector, you use the Helm command-line interface. Follow the
    [instructions to install Helm](https://helm.sh/docs/intro/install/).

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
* [Compute Engine](https://cloud.google.com/compute)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Start a Vault server in dev mode

In this section, you use a Compute Engine VM instance to start a [Vault server in dev mode](https://www.vaultproject.io/docs/concepts/dev-server) for
experimentation. There is nothing special about this choice; a VM instance is a quick and convenient way to simulate a situation in which the Vault server is 
external to your Kubernetes cluster. Never run a server in dev mode in production.

1.  Define some variables that you use during the tutorial:

        gcp_project=[YOUR_PROJECT_NAME]
        cluster_name=[YOUR_CLUSTER_NAME]
        cluster_region=us-east1

        gcloud config set project $gcp_project

1.  Create a file named `startup-script.sh` with the instructions to download and run Vault in dev mode:

        cat << EOF > startup-script.sh
        #!/bin/bash

        set -e

        wget https://releases.hashicorp.com/vault/1.7.3/vault_1.7.3_linux_amd64.zip
        sudo apt install unzip -y
        unzip vault_1.7.3_linux_amd64.zip

        ./vault server -dev -dev-root-token-id="root" \
            -dev-listen-address="0.0.0.0:8200"  &
        EOF

     This file runs during the [VM instance startup](https://cloud.google.com/compute/docs/instances/startup-scripts).

1.  Change permissions for the file to make it executable:

        chmod +x startup-script.sh

1.  [Create a VM instance](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create) using the startup script to start a Vault server:

        gcloud compute instances create vault-dev \
          --tags vault-dev \
          --metadata-from-file=startup-script=startup-script.sh \
          --image-family=ubuntu-1804-lts \
          --image-project=ubuntu-os-cloud \
          --machine-type=e2-small \
          --zone="$cluster_region"-b #change the zone accordingly
    
1.  Add a firewall rule to allow access to the Vault port `8200`:

        gcloud compute firewall-rules create vault-dev \
          --target-tags vault-dev --direction INGRESS \
          --allow tcp:8200

1.  Check whether your Vault server is up:

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

    It may take a minute for the installation and initialization to complete after the machine has started.

## Create the GKE cluster

1.  [Create the GKE cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-regional-cluster):

        gcloud beta container clusters create "$cluster_name" \
          --release-channel regular \
          --enable-ip-alias \
          --region "$cluster_region" \
          --workload-pool="${gcp_project}".svc.id.goog

1.  Check the Kubernetes configuration:

        kubectl config current-context

1.  If your current context doesn't match the cluster that you just created, or if you need to connect to it again after changing your kubeconfig, use the
    `get-credentials` command to configure your local access to the cluster:

        gcloud container clusters get-credentials "$cluster_name" --region "$cluster_region"
   
## Enable and configure the Google Cloud Auth method

To configure the Google Cloud Auth method, you need to
[create a Google service account](https://cloud.google.com/sdk/gcloud/reference/iam/service-accounts/create) that will be used by the Vault server to validate 
the incoming login requests. Instead of using existing roles, this tutorial configures a [custom role](https://cloud.google.com/iam/docs/creating-custom-roles)
to make sure that the service account is properly privileged with only the required permissions.

1.  Create the role:

        gcloud iam roles create VaultAuthRole \
          --title=vault-auth-role \
          --stage=GA \
          --description="Role used for the Vault Auth Method" \
          --project "$gcp_project" \
          --permissions=iam.serviceAccounts.get,iam.serviceAccountKeys.get,compute.instances.get

1.  Create the service account:

        gcloud iam service-accounts create vault-auth-gsa --display-name="vault-auth-gsa"

1.  Apply the policy:

        gcloud projects add-iam-policy-binding "$gcp_project" \
          --member "serviceAccount:vault-auth-gsa@${gcp_project}.iam.gserviceaccount.com" \
          --role projects/"$gcp_project"/roles/VaultAuthRole

1.  Create the key:

        gcloud iam service-accounts keys create key.json --iam-account=vault-auth-gsa@"$gcp_project".iam.gserviceaccount.com

1.  Enable and configure the Google Cloud Auth method in Vault:

        vault auth enable gcp
        vault write auth/gcp/config credentials=@key.json

## Configure Workload Identity and respective Vault role

To configure Workload Identity, you need a Google service account that will be impersonated by a Kubernetes service account to access Google Cloud APIs
and to establish the trust relationship with Vault.

1.  Create the service account:

        gcloud iam service-accounts create my-service-gsa --display-name="my-service-gsa"

1.  Create the policy bindings:

        gcloud iam service-accounts add-iam-policy-binding \
          --role roles/iam.workloadIdentityUser \
          --member "serviceAccount:${gcp_project}.svc.id.goog[staging/my-service-ksa]" \
          my-service-gsa@${gcp_project}.iam.gserviceaccount.com

        gcloud projects add-iam-policy-binding "$gcp_project" \
          --member "serviceAccount:my-service-gsa@${gcp_project}.iam.gserviceaccount.com" \
          --role roles/iam.serviceAccountTokenCreator
    
    The first [policy binding](https://cloud.google.com/sdk/gcloud/reference/iam/service-accounts/add-iam-policy-binding) allows the Kubernetes service account 
    `my-service-ksa` in the namespace `staging` to impersonate the Google service account `my-service-gsa`. The second policy binding allows the Google service
    account to sign JWTs to perform the Vault login. The only permission necessary for the Vault login is the `iam.serviceAccounts.signJwt` permission. You may
    consider creating a custom role with fewer privileges as you did for the service account used to configure the Vault server.
    
1.  Create a Kubernetes namespace and service account to match the workload identity configured in the previous step:

        kubectl create namespace staging

        kubectl create serviceaccount my-service-ksa -n staging

        kubectl annotate serviceaccount my-service-ksa \
          iam.gke.io/gcp-service-account=my-service-gsa@"$gcp_project".iam.gserviceaccount.com \
          -n staging
    
1.  Check whether the workload identity is working as expected:

        kubectl run gcloud -it --rm --restart=Never \
          --serviceaccount my-service-ksa \
          -n staging \
          --image google/cloud-sdk:slim gcloud auth list

    This command launches a Pod and checks with the command `gcloud auth list` whether the active (and only) identity corresponds to the Google service account 
    email address previously configured. You should see the Google service account `my-service-gsa@"$gcp_project".iam.gserviceaccount.com` as active.
    
1.  Create the Vault role that binds the Google service account granting access to the secrets:

        vault write auth/gcp/role/my-service-stg-role \
          type="iam" \
          policies="stg" \
          max_jwt_exp="3600" \
          bound_service_accounts="my-service-gsa@${gcp_project}.iam.gserviceaccount.com"
    
    The policy `stg` doesn't exist yet. This is handled in the secrets step.
    
1.  Check whether the Vault login is working as expected:

        kubectl run vault -it --rm --restart=Never \
          --serviceaccount my-service-ksa \
          -n staging \
          --image vault \
          -- vault login -address="$VAULT_ADDR" -method=gcp service_account="my-service-gsa@${gcp_project}.iam.gserviceaccount.com" role="my-service-stg-role"
    
    This command launches a Pod and performs a `vault login` command from within the Pod pointing to your Vault server. You should see a successful response 
    containing a Vault token.
    
## Inject secrets in a Pod

In this section, you start writing some secrets to Vault. For that, you mount a `kv-v2` secrets engine and create a Vault policy that allows your Vault role to
read from this secrets backend.

1.  Set up the secrets engine:

        vault secrets enable -path=my-service/secrets kv-v2

        vault kv put my-service/secrets/stg/database/config username="db-username" password="db-password"
    
1.  Check the data just written:

        vault kv get my-service/secrets/stg/database/config

1.  Create the `stg` policy:

        vault policy write stg - <<EOF
        path "my-service/secrets/data/stg/database/config" {
          capabilities = ["read"]
        }
        EOF
    
    The `stg` policy allows reading only to the `my-service/secrets/stg` path, preventing that the role (and application) from having access to secrets that are 
    not necessary.
    
1.  Install the Vault Agent Injector using Helm, as described in the
    [Vault Agent Injector installation documentation](https://www.vaultproject.io/docs/platform/k8s/injector/installation):

    1.  Add the HashiCorp Helm repository:

            helm repo add hashicorp https://helm.releases.hashicorp.com

    1.  Check whether you have access to the Helm chart:
    
            helm search repo hashicorp/vault
            
        You should see output similar to this:
        
            NAME            CHART VERSION    APP VERSION    DESCRIPTION
            hashicorp/vault 0.13.0           1.7.3          Official HashiCorp Vault Chart

    1.  Create the namespace:

            kubectl create ns vault-agent-injector

    1.  Install the Vault Agent Injector:

            helm install vault hashicorp/vault --namespace vault-agent-injector --set="server.enabled=false" --set="injector.externalVaultAddr=$VAULT_ADDR" --set "injector.authPath=auth/gcp"
    
     For more information about configuration options, see the [Vault Helm documentation](https://www.vaultproject.io/docs/platform/k8s/helm/configuration).
    
1.  Create a Deployment resource with the Agent Injector annotations:

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
                  {% verbatim %}{{- with secret "my-service/secrets/data/stg/database/config" -}}
                  postgresql://{{ .Data.data.username }}:{{ .Data.data.password }}@postgres:5432/wizard
                  {{- end -}}{% endverbatim %}
              labels:
                app: my-service
            spec:
              serviceAccountName: my-service-ksa
              containers:
                - name: my-service
                  image: nginx
        EOF

1.  Check whether the Pod is running:

        kubectl get po -n staging
        
    The output should be similar to the following:
    
        NAME                         READY   STATUS    RESTARTS   AGE
        my-service-d5dcfb55f-w8g89   2/2     Running   0          22s

    If the Pod is stuck in the `Init` status, check the `vault-agent-init` container logs to identify the problem:
    
        # run this only if you need to debug
        kubectl logs my-service-d5dcfb55f-w8g89 vault-agent-init -n staging

1.  Check the `my-service` container and verify that the secrets have been injected:

        kubectl exec \
          $(kubectl get pod -l app=my-service -n staging -o jsonpath="{.items[0].metadata.name}") \
          -c my-service -n staging -- cat /vault/secrets/database-config.txt

        postgresql://db-username:db-password@postgres:5432/wizard%

    For more information about the available annotations, configuration options, and features, see the
    [Agent Injector documentation](https://www.vaultproject.io/docs/platform/k8s/injector/annotations).
    
## Cleaning up

1.  Delete the GKE cluster:

        gcloud container clusters delete "$cluster_name" --region "$cluster_region"

1.  Delete the Compute Engine VM instance and firewall rule:

        gcloud compute instances delete vault-dev --zone "$cluster_region"-b
        gcloud compute firewall-rules delete vault-dev

1.  Delete the custom role and service accounts:

        gcloud iam roles delete VaultAuthRole --project "$gcp_project"
        gcloud iam service-accounts delete vault-auth-gsa@"$gcp_project".iam.gserviceaccount.com
        gcloud iam service-accounts delete my-service-gsa@"$gcp_project".iam.gserviceaccount.com
