---
title: Install Anthos Service Mesh with an in-cluster control plane on GKE with Terraform
description: Use Terraform to deploy a Kubernetes Engine cluster and Anthos Service Mesh with an in-cluster control plane.
author: ameer00
tags: Kubernetes Engine, ASM
date_published: 2021-07-28
---

Ameer Abbas | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to install Anthos Service Mesh 1.9 with an in-cluster control plane on a Google Kubernetes Engine (GKE) cluster using the
[GKE Anthos Service Mesh Terraform submodule](https://github.com/terraform-google-modules/terraform-google-kubernetes-engine/tree/master/modules/asm).

## Objectives

- Use the GKE Anthos Service Mesh Terraform submodule to do the following:
  - Create a Virtual Private Cloud (VPC) network.
  - Create a GKE cluster.
  - Install Anthos Service Mesh 1.9.
- Deploy the [Online Boutique](https://cloud.google.com/service-mesh/docs/onlineboutique-install-kpt) sample app on an Anthos Service Mesh.
- Clean up or destroy all resources with Terraform.

## Costs

This tutorial uses the following Google Cloud products:

*   [Kubernetes Engine](https://cloud.google.com/kubernetes_engine)
*   [Anthos Service Mesh](https://cloud.google.com/service-mesh)
*   [Cloud Storage](https://cloud.google.com/storage)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

1.  [Select or create a Google Cloud project](https://console.cloud.google.com/projectselector2).
1.  [Verify that billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project) for your project.
1.  Enable the required APIs:

        gcloud services enable \
          cloudresourcemanager.googleapis.com \
          container.googleapis.com

1.  Install [Krew](https://github.com/kubernetes-sigs/krew), the package manager for kubectl plugins:

        (
        set -x; cd "$(mktemp -d)" &&
        curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/krew.{tar.gz,yaml}" &&
        tar zxvf krew.tar.gz &&
        KREW=./krew-"$(uname | tr '[:upper:]' '[:lower:]')_amd64" &&
        $KREW install --manifest=krew.yaml --archive=krew.tar.gz &&
        $KREW update
        )
        echo -e "export PATH="${PATH}:${HOME}/.krew/bin"" >> ~/.bashrc && source ~/.bashrc

1.  Install the ctx, ns, and neat [plugins](https://krew.sigs.k8s.io/plugins/):

        kubectl krew install ctx ns neat

1.  Install [kpt](https://cloud.google.com/architecture/managing-cloud-infrastructure-using-kpt):

        sudo apt-get update && sudo apt-get install -y google-cloud-sdk-kpt netcat

1.  Set an environment variable for your project ID, replacing `[YOUR_PROJECT_ID]` with your project ID:

        export PROJECT_ID=[YOUR_PROJECT_ID]

1.  Set the working project to your project:

        gcloud config set project ${PROJECT_ID}
        
1.  Set other environment variables:       
        
        export PROJECT_NUM=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
        export CLUSTER_1=gke-central
        export CLUSTER_1_ZONE=us-central1-a
        export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
        export MESH_ID="proj-${PROJECT_NUM}"
        export TERRAFORM_SA="terraform-sa"
        export ASM_MAJOR_VERSION=1.9
        export ASM_VERSION=1.9.5-asm.2
        export ASM_REV=asm-195-2
        export ASM_MCP_REV=asm-managed

1.  Create a `WORKDIR` folder:

        mkdir -p asm-tf && cd asm-tf && export WORKDIR=`pwd`
    
1.  Create a `KUBECONFIG` file for this tutorial:

        touch asm-kubeconfig && export KUBECONFIG=`pwd`/asm-kubeconfig

1.  Verify that your Terraform version is 0.13.
  
    If you don't have Terraform version 0.13, then download and install Terraform version 0.13:

        wget https://releases.hashicorp.com/terraform/0.13.7/terraform_0.13.7_linux_amd64.zip
        unzip terraform_0.13.7_linux_amd64.zip
        export TERRAFORM_CMD=`pwd`/terraform # Path of your terraform binary

## Prepare Terraform

 You can use Terraform to customize your in-cluster Anthos Service Mesh control plane using `IstioOperator` resource files. In this tutorial, you use a simple
 `IstioOperator` resource file to customize your`istio-ingressgateways`.
   
1.  Create a Google Cloud service account and give it the following roles:

        gcloud --project=${PROJECT_ID} iam service-accounts create ${TERRAFORM_SA} \
          --description="terraform-sa" \
          --display-name=${TERRAFORM_SA}

        ROLES=(
          'roles/servicemanagement.admin' \
          'roles/storage.admin' \
          'roles/serviceusage.serviceUsageAdmin' \
          'roles/meshconfig.admin' \
          'roles/compute.admin' \
          'roles/container.admin' \
          'roles/resourcemanager.projectIamAdmin' \
          'roles/iam.serviceAccountAdmin' \
          'roles/iam.serviceAccountUser' \
          'roles/iam.serviceAccountKeyAdmin' \
          'roles/gkehub.admin')
        for role in "${ROLES[@]}"
        do
          gcloud projects add-iam-policy-binding ${PROJECT_ID} \
          --member "serviceAccount:${TERRAFORM_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="$role"
        done
    
1.  Create the service account credential JSON key for Terraform:

        gcloud iam service-accounts keys create ${TERRAFORM_SA}.json \
          --iam-account=${TERRAFORM_SA}@${PROJECT_ID}.iam.gserviceaccount.com

1.  Set the Terraform credentials and project ID:

        export GOOGLE_APPLICATION_CREDENTIALS=`pwd`/${TERRAFORM_SA}.json
        export TF_VAR_project_id=${PROJECT_ID}

1.  Create a Cloud Storage bucket and the backend resource for the Terraform state file:

        gsutil mb -p ${PROJECT_ID} gs://${PROJECT_ID}
        gsutil versioning set on gs://${PROJECT_ID}

        cat <<'EOF' > backend.tf_tmpl
        terraform {
          backend "gcs" {
            bucket  = "${PROJECT_ID}"
            prefix  = "tfstate"
          }
        }
        EOF

        envsubst < backend.tf_tmpl > backend.tf

1.  Create a custom overlay file:

        cat <<EOF > ${WORKDIR}/custom_ingress_gateway.yaml
        apiVersion: install.istio.io/v1alpha1
        kind: IstioOperator
        spec:
          components:
            ingressGateways:
            - name: istio-ingressgateway
              enabled: true
              k8s:
                hpaSpec:
                  maxReplicas: 10
                  minReplicas: 2
        EOF

## Deploy resources with Terraform

In this section, you create and apply Terraform files that define the deployment of a VPC network, GKE cluster, and Anthos Service Mesh.

1.  Create the `main.tf`, `variables.tf`, and `output.tf` files:

        cat <<'EOF' > main.tf_tmpl
        data "google_client_config" "default" {}

        provider "kubernetes" {
          host                   = "https://${module.gke.endpoint}"
          token                  = data.google_client_config.default.access_token
          cluster_ca_certificate = base64decode(module.gke.ca_certificate)
        }

        data "google_project" "project" {
          project_id = var.project_id
        }

        module "vpc" {
          source  = "terraform-google-modules/network/google"
          version = "~> 3.0"

          project_id   = var.project_id
          network_name = var.network
          routing_mode = "GLOBAL"

          subnets = [
            {
              subnet_name   = var.subnetwork
              subnet_ip     = var.subnetwork_ip_range
              subnet_region = var.region
            }
          ]

          secondary_ranges = {
            (var.subnetwork) = [
              {
                range_name    = var.ip_range_pods
                ip_cidr_range = var.ip_range_pods_cidr
              },
              {
                range_name    = var.ip_range_services
                ip_cidr_range = var.ip_range_services_cidr
              }
            ]
          }
        }

        module "gke" {
          source                  = "terraform-google-modules/kubernetes-engine/google"
          project_id              = var.project_id
          name                    = var.cluster_name
          regional                = false
          region                  = var.region
          zones                   = var.zones
          release_channel         = "REGULAR"
          network                 = module.vpc.network_name
          subnetwork              = module.vpc.subnets_names[0]
          ip_range_pods           = var.ip_range_pods
          ip_range_services       = var.ip_range_services
          network_policy          = false
          identity_namespace      = "enabled"
          cluster_resource_labels = { "mesh_id" : "proj-${data.google_project.project.number}" }
          node_pools = [
            {
              name         = "asm-node-pool"
              autoscaling  = false
              auto_upgrade = true
              # ASM requires minimum 4 nodes and e2-standard-4
              node_count   = 4
              machine_type = "e2-standard-4"
            },
          ]
        }

        module "asm" {
          source                = "github.com/terraform-google-modules/terraform-google-kubernetes-engine//modules/asm"
          cluster_name          = module.gke.name
          cluster_endpoint      = module.gke.endpoint
          project_id            = var.project_id
          location              = module.gke.location
          enable_all            = false
          enable_cluster_roles  = true
          enable_cluster_labels = false
          enable_gcp_apis       = true
          enable_gcp_iam_roles  = true
          enable_gcp_components = true
          enable_registration   = false
          asm_version           = "1.9"
          managed_control_plane = false
          service_account       = "${TERRAFORM_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
          key_file              = "./${TERRAFORM_SA}.json"
          options               = ["envoy-access-log,egressgateways"]
          custom_overlays       = ["./custom_ingress_gateway.yaml"]
          skip_validation       = false
          outdir                = "./${module.gke.name}-outdir-${var.asm_version}"
          # ca                    = "citadel"
          # ca_certs = {
          #   "ca_cert"    = "./ca-cert.pem"
          #   "ca_key"     = "./ca-key.pem"
          #   "root_cert"  = "./root-cert.pem"
          #   "cert_chain" = "./cert-chain.pem"
          # }
        }
        EOF
 
        cat <<'EOF' > variables.tf
        variable "project_id" {}

        variable "cluster_name" {
          default = "gke-central"
        }

        variable "region" {
          default = "us-central1"
        }

        variable "zones" {
          default = ["us-central1-a"]
        }

        variable "network" {
          default = "asm-vpc"
        }

        variable "subnetwork" {
          default = "subnet-01"
        }

        variable "subnetwork_ip_range" {
          default = "10.10.10.0/24"
        }

        variable "ip_range_pods" {
          default = "subnet-01-pods"
        }

        variable "ip_range_pods_cidr" {
          default = "10.100.0.0/16"
        }

        variable "ip_range_services" {
          default = "subnet-01-services"
        }

        variable "ip_range_services_cidr" {
          default = "10.101.0.0/16"
        }

        variable "asm_version" {
          default = "1.9"
        }
        EOF

        cat <<'EOF' > output.tf
        output "kubernetes_endpoint" {
          sensitive = true
          value     = module.gke.endpoint
        }

        output "client_token" {
          sensitive = true
          value     = base64encode(data.google_client_config.default.access_token)
        }

        output "ca_certificate" {
          value = module.gke.ca_certificate
        }

        output "service_account" {
          description = "The default service account used for running nodes."
          value       = module.gke.service_account
        }
        EOF

        envsubst < main.tf_tmpl > main.tf

1.  Initialize Terraform and apply the configurations:

        ${TERRAFORM_CMD} init
        ${TERRAFORM_CMD} plan
        ${TERRAFORM_CMD} apply -auto-approve

## Configure access to your cluster

1.  Connect to the GKE cluster:

        gcloud container clusters get-credentials ${CLUSTER_1} --zone ${CLUSTER_1_ZONE}

    Remember to unset your `KUBECONFIG` variable when you're finished.

1.  Rename the cluster context for easy switching:

        kubectl ctx ${CLUSTER_1}=gke_${PROJECT_ID}_${CLUSTER_1_ZONE}_${CLUSTER_1}

1.  Confirm the cluster context:

        kubectl ctx
    
    The output is similar to the following:

        gke-central

## Deploy the Online Boutique app

1.  Set the Anthos Service Mesh revision variable:

        export ASM_REVISION=${ASM_REV}
    
1.  Deploy the Online Boutique app to the GKE cluster:

        kpt pkg get \
          https://github.com/GoogleCloudPlatform/microservices-demo.git/release \
          online-boutique

        kubectl --context=${CLUSTER_1} create namespace online-boutique
        kubectl --context=${CLUSTER_1} label namespace online-boutique istio.io/rev=${ASM_REVISION}
        kubectl --context=${CLUSTER_1} -n online-boutique apply -f online-boutique

1.  Wait until all Deployments are ready:

        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment adservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment checkoutservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment currencyservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment emailservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment frontend
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment paymentservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment productcatalogservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment shippingservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment cartservice
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment loadgenerator
        kubectl --context=${CLUSTER_1} -n online-boutique wait --for=condition=available --timeout=5m deployment recommendationservice

    The output is similar to the following:

        deployment "adservice" successfully rolled out
        deployment "checkoutservice" successfully rolled out
        deployment "currencyservice" successfully rolled out
        deployment "emailservice" successfully rolled out
        deployment "frontend" successfully rolled out
        deployment "paymentservice" successfully rolled out
        deployment "productcatalogservice" successfully rolled out
        deployment "shippingservice" successfully rolled out
        deployment "cartservice" successfully rolled out
        deployment "loadgenerator" successfully rolled out
        deployment "recommendationservice" successfully rolled out

## Access the Online Boutique app

Run the following command to get the IP address of the external load balancer:

    kubectl --context=${CLUSTER_1} -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

Now that you've deployed Online Boutique, you can view the Anthos Service Mesh telemetry dashboards to view the metrics for the application.

For more information about metrics, logs, and tracing with Anthos Service Mesh, see
[Exploring Anthos Service Mesh in the Cloud Console](https://cloud.google.com/service-mesh/docs/observability/explore-dashboard).

## Clean up

### Terraform destroy

Use the `terraform destroy` command to destroy all Terraform resources:

    ${TERRAFORM_CMD} destroy -auto-approve

### Delete the project

Alternatively, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, delete the resources inside the 
  project instead. This ensures that URLs that use the project ID, such as an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [community support for Terraform](https://cloud.google.com/docs/terraform#terraform_support_for).
- Learn more about [Anthos Service Mesh](https://cloud.google.com/service-mesh).
