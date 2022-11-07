---
title: Install Anthos Service Mesh with a Google-managed control plane on GKE with Terraform
description: Use Terraform to deploy a Kubernetes Engine cluster and install Anthos Service Mesh with a Google-managed control plane.
author: alizaidis
tags: Kubernetes Engine, ASM, MCP, Managed
date_published: 2022-01-21
---

Ali Zaidi | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to install managed Anthos Service Mesh with a Google-managed control plane on two Google Kubernetes Engine (GKE) clusters using the
[Anthos Service Mesh Terraform submodule](https://gitlab.com/asm7/asm-terraform). This tutorial has been tested in
[Google Cloud Shell](https://cloud.google.com/shell/docs/features). Cloud Shell has all of the tools that you need to perform the following steps.

## Objectives

- Prepare Terraform.
- Build a Virtual Private Cloud (VPC) network.
- Create two GKE clusters.
- Install Anthos Service Mesh.
- Deploy the [sample Online Boutique application](https://github.com/GoogleCloudPlatform/microservices-demo).
- Monitor application golden signals.

## Costs

This tutorial uses the following Google Cloud products:

*   [Kubernetes Engine](https://cloud.google.com/kubernetes_engine)
*   [Anthos Service Mesh](https://cloud.google.com/service-mesh)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

This guide assumes that you have owner IAM permissions for your Google Cloud project. In production, you do not require owner permission.

1.  [Select or create a Google Cloud project](https://console.cloud.google.com/projectselector2).

1.  [Verify that billing is enabled](https://cloud.google.com/billing/docs/how-to/modify-project) for your project.

## Set up your environment

Follow these steps to set up your environment.

1.  In the Google Cloud Console, [activate Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell).

1.  Create a `WORKDIR` folder:

        mkdir asm-terraform-tutorial
        cd asm-terraform-tutorial
        export WORKDIR=$(pwd)

1.  Define variables used in this tutorial:

        export PROJECT_ID=PROJECT ID
        export REPO_URL="https://gitlab.com/asm7/asm-terraform"
        export VPC="vpc"
        export GKE1="gke1"
        export GKE2="gke2"
        export REGION="us-central1"
        export GKE1_LOCATION="${REGION}-a"
        export GKE2_LOCATION="${REGION}-b"
        export GKE1_CTX="gke_${PROJECT_ID}_${GKE1_LOCATION}_${GKE1}"
        export GKE2_CTX="gke_${PROJECT_ID}_${GKE2_LOCATION}_${GKE2}"
        export GKE1_KUBECONFIG="${WORKDIR}/gke1_kubeconfig"
        export GKE2_KUBECONFIG="${WORKDIR}/gke2_kubeconfig"
        export GKE_CHANNEL="REGULAR"
        export ASM_CHANNEL="regular"
        export CNI_ENABLED="true"
        export ASM_GATEWAYS_NAMESPACE="asm-gateways"
        
    Replace the value of `PROJECT_ID` with your project ID.
    
    You can use the `ASM_CHANNEL` variable to set up Anthos Service Mesh with Regular, Rapid, or Stable release channels. For more information, see
    [Anthos Service Mesh control plane revisions](https://cloud.google.com/service-mesh/docs/revisions-overview).
    
    To support GKE Autopilot clusters, `CNI_ENABLED` must be `true`.

1.  Configure your Google Cloud project:

        gcloud config set project "${PROJECT_ID}"
        
1.  Enable the Google Cloud APIs required for this tutorial:

        gcloud --project="${PROJECT_ID}" services enable \
            container.googleapis.com \
            compute.googleapis.com \
            gkehub.googleapis.com \
            cloudresourcemanager.googleapis.com

## Set up the VPC network and GKE clusters with Terraform

Follow these steps to set up the VPC network and GKE clusters with Terraform.

1.  Set up Terraform authentication:

        gcloud auth application-default login --no-launch-browser

    For more information, see
    [Google Provider Configuration Reference](https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#authentication).

1.  Clone the repository and go to the tutorial directory:

        git clone "${REPO_URL}" ${WORKDIR}/asm-terraform
        cd ${WORKDIR}/asm-terraform
        git checkout aa/tutorial
        cd tutorial

1.  Prepare the VPC and GKE terraform modules:

        cd vpc-gke
        envsubst < variables.tf.tmpl > variables.tf
        envsubst < provider.tf.tmpl > provider.tf
        
    This step populates the variables and provider files with the variables defined at the beginning of the tutorial.

1.  Deploy the VPC and GKE Terraform module:

        terraform init && \
        terraform plan && \
        terraform apply --auto-approve

    The deployment can take up to 10 minutes to complete. This module also exports the kubeconfig using the `gke_auth` module for the two GKE clusters as 
    local_file resources. These kubeconfig files are used in the Anthos Service Mesh module later.

1.  Inspect the deployed resources using `gcloud` commands starting from the global VPC network called `vpc`:

        gcloud compute networks describe vpc

    The output is similar to the following:

        autoCreateSubnetworks: false
        creationTimestamp: '2021-11-16T20:37:54.520-08:00'
        id: '932232537524746701'
        kind: compute#network
        name: vpc
        routingConfig:
          routingMode: GLOBAL
        selfLink: https://www.googleapis.com/compute/v1/projects/zl-asm-exp2688feb2/global/networks/vpc
        subnetworks:
        - https://www.googleapis.com/compute/v1/projects/zl-asm-exp2688feb2/regions/us-central1/subnetworks/subnet-01
        x_gcloud_bgp_routing_mode: GLOBAL
        x_gcloud_subnet_mode: CUSTOM

1.  List the GKE clusters:

        gcloud container clusters list

    Take note of the `MASTER_IP` value for each. This is the cluster endpoint, which you will need in the following Anthos Service Mesh module.
    
    The output is similar to the following:

        NAME: gke1
        LOCATION: us-central1-a
        MASTER_VERSION: 1.21.5-gke.1802
        MASTER_IP: 104.154.57.122
        MACHINE_TYPE: e2-standard-4
        NODE_VERSION: 1.21.5-gke.1802
        NUM_NODES: 2
        STATUS: RUNNING

        NAME: gke2
        LOCATION: us-central1-b
        MASTER_VERSION: 1.21.5-gke.1802
        MASTER_IP: 23.251.149.3
        MACHINE_TYPE: e2-standard-4
        NODE_VERSION: 1.21.5-gke.1802
        NUM_NODES: 2
        STATUS: RUNNING

1.  Verify that the cluster endpoint in each of the generated kubeconfig files matches the value in the previous step:

    *   GKE1:

            cat ${WORKDIR}/gke1_kubeconfig

        The output is similar to the following:

                server: https://104.154.57.122
              name: gke1
            contexts:
            - context:
                cluster: gke1
                user: gke1
              name: gke1

    *   GKE2:

            cat ${WORKDIR}/gke2_kubeconfig

        The output is similar to the following:

                server: https://23.251.149.3
              name: gke2
            contexts:
            - context:
                cluster: gke2
                user: gke2
              name: gke2

## Set up Anthos Service Mesh

Follow these steps to set up Anthos Service Mesh.

1.  Register the clusters to a fleet and enable the mesh feature: 

        cd ${WORKDIR}/asm-terraform/tutorial/hub-mesh
        envsubst < variables.tf.tmpl > variables.tf
        envsubst < provider.tf.tmpl > provider.tf

        terraform init && \
        terraform plan && \
        terraform apply --auto-approve

    This step may take a few minutes to complete.
     
    For more information, see [Fleets](https://cloud.google.com/anthos/multicluster-management/fleets).

1.  Inspect the deployed resources using `gcloud` commands: 

        gcloud container hub memberships list

    The output is similar to the following:

        NAME: gke1
        EXTERNAL_ID: d2f6bf3b-b0df-47be-b841-39b0f4bc25ba

        NAME: gke2
        EXTERNAL_ID: 84724e99-9acf-45cc-954c-a4db53c7ecf3

    For more details on cluster registration see
    [Registering a cluster](https://cloud.google.com/anthos/multicluster-management/connect/registering-a-cluster#terraform).

1.  Verify that Anthos Service Mesh is enabled:

        gcloud beta container hub mesh describe

    The output is similar to the following:

        createTime: '2021-11-17T05:24:36.150402113Z'
        membershipStates:
          projects/132310186441/locations/global/memberships/gke1:
            state:
              code: OK
              description: Please see https://cloud.google.com/service-mesh/docs/install for
                instructions to onboard to Anthos Service Mesh.
              updateTime: '2021-11-17T05:26:58.175206417Z'
          projects/132310186441/locations/global/memberships/gke2:
            state:
              code: OK
              description: Please see https://cloud.google.com/service-mesh/docs/install for
                instructions to onboard to Anthos Service Mesh.
              updateTime: '2021-11-17T05:26:59.778268604Z'
        name: projects/zl-asm-exp2688feb2/locations/global/features/servicemesh
        resourceState:
          state: ACTIVE
        spec: {}
        updateTime: '2021-11-17T05:27:02.350986468Z'

1.  Verify that you have the `ControlPlaneRevision` custom resource definition (CRD) in both GKE clusters. The `ControlPlaneRevision` custom resource is used to
    deploy managed Anthos Service Mesh.

    *   Verify GKE1:

            gcloud --project=${PROJECT_ID} container clusters get-credentials ${GKE1} --zone ${GKE1_LOCATION}
            kubectl  wait --for=condition=established crd controlplanerevisions.mesh.cloud.google.com --timeout=5m

    *   Verify GKE2:

            gcloud --project=${PROJECT_ID} container clusters get-credentials ${GKE2} --zone ${GKE2_LOCATION}
            kubectl  wait --for=condition=established crd controlplanerevisions.mesh.cloud.google.com --timeout=5m

    The output is similar to the following:

        customresourcedefinition.apiextensions.k8s.io/controlplanerevisions.mesh.cloud.google.com condition met

1.  Install Anthos Service Mesh on the GKE clusters:

        cd ${WORKDIR}/asm-terraform/tutorial/asm
        envsubst < variables.tf.tmpl > variables.tf
        envsubst < provider.tf.tmpl > provider.tf

        terraform init && \
        terraform plan && \
        terraform apply --auto-approve

        export ASM_LABEL=$(terraform output asm_label | tr -d '"')
        
     This module also configures multi-cluster mesh by configuring cross-cluster kubeconfig secrets.

1.  Ensure that Anthos Service Mesh provisioning finishes successfully:
  
        kubectl --context=${GKE1_CTX} wait --for=condition=ProvisioningFinished controlplanerevision ${ASM_LABEL} -n istio-system --timeout=10m
        kubectl --context=${GKE2_CTX} wait --for=condition=ProvisioningFinished controlplanerevision ${ASM_LABEL} -n istio-system --timeout=10m

    This step can take a few minutes to complete.
     
    The output is similar to the following:

        controlplanerevision.mesh.cloud.google.com/asm-managed condition met

1.  Inspect the deployed resources:

        kubectl get ns --context=${GKE1_CTX}
        kubectl get ns --context=${GKE2_CTX}

    The output is similar to the following:

        NAME              STATUS   AGE
        default           Active   23m
        istio-system      Active   8m30s
        kube-node-lease   Active   23m
        kube-public       Active   23m
        kube-system       Active   23m

    The `istio-system` namespace should be present on both clusters.

1.  Inspect the status of the `ControlPlaneRevision` custom resource:

        kubectl describe controlplanerevision ${ASM_LABEL} -n istio-system --context=${GKE1_CTX}
        kubectl describe controlplanerevision ${ASM_LABEL} -n istio-system --context=${GKE2_CTX}

    The output is similar to the following:

        Name:         asm-managed
        Namespace:    istio-system

        ...

        Status:
          Conditions:
            Last Transition Time:  2021-11-17T04:58:29Z
            Message:               The provisioning process has completed successfully
            Reason:                Provisioned
            Status:                True
            Type:                  Reconciled
            Last Transition Time:  2021-11-17T04:58:29Z
            Message:               Provisioning has finished
            Reason:                ProvisioningFinished
            Status:                True
            Type:                  ProvisioningFinished
            Last Transition Time:  2021-11-17T04:58:29Z
            Message:               Provisioning has not stalled
            Reason:                NotStalled
            Status:                False
            Type:                  Stalled

    This is a useful resource to observe when installing or upgrading Anthos Service Mesh. For more information, see
    [What is a revision](https://cloud.google.com/service-mesh/docs/revisions-overview#what_is_a_revision).

1.  Inspect the cluster credentials for each cluster stored as opaque secrets in the `istio-system` namespace present in the other cluster. These are required 
    for cross-cluster service discovery:

        kubectl describe secret gke2-secret-kubeconfig -n istio-system --context=${GKE1_CTX}
        kubectl describe secret gke1-secret-kubeconfig -n istio-system --context=${GKE2_CTX}

    The output is similar to the following:

        Name:         gke1-secret-kubeconfig
        Namespace:    istio-system
        Labels:       istio/multiCluster=true
        Annotations:  networking.istio.io/cluster: gke1

        Type:  Opaque

        Data
        ====
        gke1:  3232 bytes

## Configure multi-cluster Anthos Service Mesh

Follow these steps to configure multi-cluster Anthos Service Mesh.

1.  Deploy Anthos Service Mesh ingress gateways in both clusters:

        cd ${WORKDIR}/asm-terraform/tutorial/asm-gateways
        envsubst < variables.tf.tmpl > variables.tf
        envsubst < provider.tf.tmpl > provider.tf

        terraform init && \
        terraform plan && \
        terraform apply --auto-approve

1.  Confirm that both Anthos Service Mesh ingress gateways are running:

        kubectl --context=${GKE1_CTX} -n ${ASM_GATEWAYS_NAMESPACE} wait --for=condition=available --timeout=5m deployment asm-ingressgateway
        kubectl --context=${GKE2_CTX} -n ${ASM_GATEWAYS_NAMESPACE} wait --for=condition=available --timeout=5m deployment asm-ingressgateway

    The output is similar to the following:

        deployment.apps/asm-ingressgateway condition met

1.  Inspect the deployment and service for Anthos Service Mesh ingress gateways on each cluster:

    *   Inspect GKE1:

            kubectl --context=${GKE1_CTX} -n ${ASM_GATEWAYS_NAMESPACE} get deploy
            kubectl --context=${GKE2_CTX} -n ${ASM_GATEWAYS_NAMESPACE} get deploy

        The output is similar to the following:

            NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
            asm-ingressgateway   1/1     1            1           4m19s

    *   Inspect GKE2:

            kubectl --context=${GKE1_CTX} -n ${ASM_GATEWAYS_NAMESPACE} get service
            kubectl --context=${GKE2_CTX} -n ${ASM_GATEWAYS_NAMESPACE} get service

        The output is similar to the following:

            NAME                 TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)                      AGE
            asm-ingressgateway   LoadBalancer   10.100.1.124   35.192.78.53   80:32514/TCP,443:30712/TCP   4m30s

## Deploy a sample application

In this section, you deploy a sample application ([Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo)) on both GKE1 and GKE2 to verify 
the multi-cluster mesh.

1.  Create the `online-boutique` namespace on both clusters:

        cat <<EOF > ${WORKDIR}/namespace-online-boutique.yaml
        apiVersion: v1
        kind: Namespace
        metadata:
          name: online-boutique
          labels:
            istio.io/rev: ${ASM_LABEL}
        EOF

        kubectl --context=${GKE1_CTX} apply -f ${WORKDIR}/namespace-online-boutique.yaml
        kubectl --context=${GKE2_CTX} apply -f ${WORKDIR}/namespace-online-boutique.yaml

1.  Clone the sample application repository and deploy Kubernetes manifests to both clusters:

        git clone https://github.com/GoogleCloudPlatform/microservices-demo.git ${WORKDIR}/online-boutique
        kubectl --context=${GKE1_CTX} -n online-boutique apply -f ${WORKDIR}/online-boutique/release/kubernetes-manifests.yaml
        kubectl --context=${GKE2_CTX} -n online-boutique apply -f ${WORKDIR}/online-boutique/release/kubernetes-manifests.yaml

1.  Delete some deployments from each cluster to set up the application architecture with services communicating transparently across clusters:

        kubectl --context=${GKE1_CTX} -n online-boutique delete deployment adservice
        kubectl --context=${GKE1_CTX} -n online-boutique delete deployment cartservice
        kubectl --context=${GKE1_CTX} -n online-boutique delete deployment redis-cart
        kubectl --context=${GKE1_CTX} -n online-boutique delete deployment currencyservice
        kubectl --context=${GKE1_CTX} -n online-boutique delete deployment emailservice

        kubectl --context=${GKE2_CTX} -n online-boutique delete deployment paymentservice
        kubectl --context=${GKE2_CTX} -n online-boutique delete deployment productcatalogservice
        kubectl --context=${GKE2_CTX} -n online-boutique delete deployment shippingservice
        kubectl --context=${GKE2_CTX} -n online-boutique delete deployment checkoutservice
        kubectl --context=${GKE2_CTX} -n online-boutique delete deployment recommendationservice

1.  Wait for all deployments to be ready:

        kubectl --context=${GKE1_CTX} -n online-boutique wait --for=condition=available --timeout=5m --all deployments
        kubectl --context=${GKE2_CTX} -n online-boutique wait --for=condition=available --timeout=5m --all deployments

    The output is similar to the following:

        deployment.apps/adservice condition met
        deployment.apps/cartservice condition met
        deployment.apps/currencyservice condition met
        deployment.apps/emailservice condition met
        deployment.apps/frontend condition met
        deployment.apps/loadgenerator condition met
        deployment.apps/redis-cart condition met

1.  Deploy Anthos Service Mesh manifests to both clusters:

        kubectl --context=${GKE1_CTX} -n online-boutique apply -f ${WORKDIR}/asm-terraform/tutorial/online-boutique/asm-manifests.yaml
        kubectl --context=${GKE2_CTX} -n online-boutique apply -f ${WORKDIR}/asm-terraform/tutorial/online-boutique/asm-manifests.yaml

1.  Access Online Boutique through the Anthos Service Mesh ingress:

        export GKE1_ASM_INGRESS_IP=$(kubectl --context=${GKE1_CTX} --namespace ${ASM_GATEWAYS_NAMESPACE} get svc asm-ingressgateway -o jsonpath={.status.loadBalancer.ingress..ip})
        export GKE2_ASM_INGRESS_IP=$(kubectl --context=${GKE2_CTX} --namespace ${ASM_GATEWAYS_NAMESPACE} get svc asm-ingressgateway -o jsonpath={.status.loadBalancer.ingress..ip})

        echo -e "GKE1 ASM Ingressgateway IP is ${GKE1_ASM_INGRESS_IP} accessible at http://${GKE1_ASM_INGRESS_IP}"
        echo -e "GKE2 ASM Ingressgateway IP is ${GKE2_ASM_INGRESS_IP} accessible at http://${GKE2_ASM_INGRESS_IP}"

    Verify multicluster mesh service discovery and routing by accessing the Online Boutique application through the Anthos Service Mesh ingress gateways.
    You can access the application through either IP address. Browse through the application to observe behavior from each endpoint. The behavior should be the 
    same. 

## Monitor application golden signals

Inspect service dashboards by accessing the link generated in the following command:

    echo -e "https://console.cloud.google.com/anthos/services?project=${PROJECT_ID}"

Explore the topology and metrics for services by switching to Topology view located in the top right section of the page.

## Clean up

The easiest way to prevent continued billing for the resources that you created for this tutorial is to delete the project you created for the tutorial.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

- Learn more about [community support for Terraform](https://cloud.google.com/docs/terraform#terraform_support_for).
- Learn more about [Anthos Service Mesh](https://cloud.google.com/service-mesh).
