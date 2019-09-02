---
title: Provision Couchbase on Google Kubernetes Engine using Terraform
description: Learn how to provision a Couchbase Autonomous Operator and Cluster inside a Google Kubernetes Engine cluster using Terraform scripts.
author: Kishore Allwynraj
tags: Google Kubernetes Engine, Couchbase Autonomous Operator, Couchbase Cluster, Terraform
date_published: 
---

## Introduction

This guide will help you learn how to provision a Couchbase autonomous operator and cluster inside a Kubernetes Engine cluster in Google Cloud Platform using Terraform scripts.

## Prerequisites

1.  A Google Cloud Platform account. If you don’t have a GCP account, [create one now][gcpcreateaccount]. This tutorial can be completed using only the services included in GCP [free tier][gcpfree].
1.  A system with Terraform installed. You can install terraform by following the instruction available [here][terraform].
1.  A system with Google Cloud SDK installed. You can install the SDK by following the instruction available [here][googlesdk]. This SDK will install `kubectl` tool which will be required later. Go ahead and login to your project using gcloud sdk.
1.  A system with Helm installed. You can install it by following the instruction available [here][helm].

[gcpcreateaccount]: https://console.cloud.google.com/freetrial/
[gcpfree]: https://cloud.google.com/free/
[terraform]: https://learn.hashicorp.com/terraform/gcp/install
[googlesdk]: https://cloud.google.com/sdk/install
[helm]: https://helm.sh/docs/using_helm/#install-helm

## Setting up GCP

In addition to a GCP account, you will also need two things for Terraform to provision the needed infrastructure.

1.  A GCP Project. GCP organizes resources into projects. You can [create one][gcpcreateproject] in the GCP console. You will be needing this project ID later.
1.  A GCP service account key. Terraform will access your GCP account by using a service account key. You can [create one][gcpcreatesvcacc] in the console. While creating the key, assign the role as `Project -> Editor`.
1.  Google Kubernetes Engine. You will need to enable Google Kubernetes Engine API for your project. You can do so [in the console][gcpk8api].

[gcpcreateproject]: https://console.cloud.google.com/projectcreate
[gcpcreatesvcacc]: https://console.cloud.google.com/apis/credentials/serviceaccountkey
[gcpk8api]: https://console.developers.google.com/apis/api/container.googleapis.com

## Initializing the workspace

Create a directory for the examples in this guide and create a file named `main.tf` and copy below configuration into it.

    provider "google" {
      credentials = file("<SERVICE ACCOUNT>.json")
      project = "<PROJECT ID>"
      region  = "europe-west3"
      zone    = "europe-west3-a"
    }

Be sure to replace the `<SERVICE ACCOUNT>` and `<PROJECT ID>` with the file name and the ID you got while setting up your GCP.

The provider block is used to configure the named provider, in our case `google`. A provider is responsible for creating and managing the resources. Multiple provider blocks can exist in the terraform file if you need to manage resources from different providers. We will be doing this as we go further in this guide.

Whenever a new provider is added to the terraform file, the first command that needs to run is the `terraform init` in the same directory where you have the `main.tf` file. This will download the google provider plugin and install it in a subdirectory within the current working directory. You need to run this command whenever you add a new provider section in your script file.

## Creating the Kubernetes cluster

Terraform google provider has resources available for provisioning a container cluster. More details on the resource is available [here][tfcontainer]. For this guide we will provide with many of the defaults. Copy below configuration into your `Main.tf` file.

    resource "google_container_cluster" "gke-cluster" {
      name               = "tf-gke-cluster"
      network            = "default"
      zone               = "europe-west3-a"
      initial_node_count = 3
    }

This script will provision a 3 node Kubernetes cluster in the project we have configured earlier in the provider section. It uses the default network which is already available in your project. The network can be customized as per our need through script, but it is not covered in this guide and you can go through the Terraform documentation available [here][tfcontainer].

Now you can run `terraform plan` in same directory. This command will output the details on what resources terraform is going to create for you. This command does not create the resources. You need to run `terraform apply` command for the actual creation.

Once the cluster is created you will require the credentials to connect to the cluster and view the workloads running. The Google console will display the SDK command that needs to be executed to get the credentials and save into your local kube config file. Terraform provides a way for you to run this command within the script as part of provisioning scripts which can be executed on cluster bootstrapping. There are multiple providers for running provisioning scripts, but for this guide we will use `local-exec` provisioner. You can refer [here][tfprovisioner] to know more on other provisioners available in terraform.

    provisioner "local-exec" {
        command = "gcloud container clusters get-credentials ${google_container_cluster.gke-cluster.name} --zone  ${google_container_cluster.gke-cluster.zone} --project <PROJECT ID>"
      }

Now go ahead and run `terraform apply` command, which will output the same details as plan and will ask for a confirmation from you to proceed further. Once you typed `yes` it will go ahead and start creating cluster. The cluster creation will take approximately 4 minutes to get completed which you can validate from the Google Console. You can validate if the cluster credentials are saved in your kube config by running `kubectl config view`.

    D:\Program Files\Google\Cloud SDK>kubectl config view
    apiVersion: v1
    clusters:
    - cluster:
        certificate-authority-data: DATA+OMITTED
        server: https://<ClusterIP>
      name: gke_<project_id>_europe-west3-a_tf-gke-cluster
    contexts:
    - context:
        cluster: gke_<project_id>_europe-west3-a_tf-gke-cluster
        user: gke_<project_id>_europe-west3-a_tf-gke-cluster
      name: gke_<project_id>_europe-west3-a_tf-gke-cluster
    current-context: gke_<project_id>_europe-west3-a_tf-gke-cluster
    kind: Config
    preferences: {}
    users:
    - name: gke_<project_id>_europe-west3-a_tf-gke-cluster
      user:
        auth-provider:
          config:
            access-token: *******************************
            cmd-args: config config-helper --format=json
            cmd-path: D:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd
            expiry: "2019-08-21T15:55:11Z"
            expiry-key: '{.credential.token_expiry}'
            token-key: '{.credential.access_token}'
          name: gcp

You can view the cluster created and running in Google Console. You can directly view the workloads in UI or since the cluster configurations are now available in your kube config, you can also run the kubectl command `kubectl get pods --all-namespaces` to display the pods running.

    D:\Program Files\Google\Cloud SDK>kubectl get pods --all-namespaces
    NAMESPACE     NAME                                                       READY   STATUS    RESTARTS   AGE
    kube-system   event-exporter-v0.2.4-5f7d5d7dd4-p6xzv                     2/2     Running   0          18m
    kube-system   fluentd-gcp-scaler-7b895cbc89-d9d2l                        1/1     Running   0          17m
    kube-system   fluentd-gcp-v3.2.0-44ptk                                   2/2     Running   0          17m
    kube-system   fluentd-gcp-v3.2.0-pp59n                                   2/2     Running   0          16m
    kube-system   fluentd-gcp-v3.2.0-w6967                                   2/2     Running   0          17m
    kube-system   heapster-v1.6.1-5457fd4bf9-z5s6c                           3/3     Running   0          17m
    kube-system   kube-dns-autoscaler-76fcd5f658-hdrkn                       1/1     Running   0          17m
    kube-system   kube-dns-b46cc9485-7td2d                                   4/4     Running   0          18m
    kube-system   kube-dns-b46cc9485-km5b7                                   4/4     Running   0          17m
    kube-system   kube-proxy-gke-tf-gke-cluster-default-pool-928c9f65-4rw2   1/1     Running   0          18m
    kube-system   kube-proxy-gke-tf-gke-cluster-default-pool-928c9f65-5936   1/1     Running   0          18m
    kube-system   kube-proxy-gke-tf-gke-cluster-default-pool-928c9f65-h9zh   1/1     Running   0          18m
    kube-system   l7-default-backend-6f8697844f-q76sn                        1/1     Running   0          18m
    kube-system   metrics-server-v0.3.1-5b4d6d8d98-dwgkz                     2/2     Running   0          17m
    kube-system   prometheus-to-sd-6tgbp                                     1/1     Running   0          18m
    kube-system   prometheus-to-sd-bncjr                                     1/1     Running   0          18m
    kube-system   prometheus-to-sd-r9dsb                                     1/1     Running   0          18m

[tfcontainer]: https://www.terraform.io/docs/providers/google/r/container_cluster.html
[tfprovisioner]: https://www.terraform.io/docs/provisioners/index.html

## Installing Helm

Helm is the package manager for deploying software packages inside your Kubernetes cluster. Helm works alongside its server side component `Tiller` to perform the installations inside the cluster. The tiller needs to be provided with a service account with cluster admin privilege so that it can deploy the required software packages. So the first step before installing Tiller is creating the service account. Terraform has Kubernetes provider which we will use to create a cluster admin role and associate a service account with it. 

Create a new file `helm.tf` and copy below code into it.

    provider "kubernetes" {
      version = ">= 1.4.0"
     }

Now run the `terraform init` command since this is a new provider added after our previous init run. Now copy below code to create the service account.

    resource "kubernetes_service_account" "tiller" {
      depends_on = [google_container_cluster.gke-cluster]
      metadata {
      name      = "terraform-tiller"
      namespace = "kube-system"
      }
      automount_service_account_token = true
    }

The above code snippet has a `depends_on` section where we have given the name of the Google container cluster we added in the `Main.tf`. This will ensure Terraform creates the Kubernetes cluster first before trying to create the service account. The next step is to create the cluster admin role and associate the service account. Copy the below configuration in your `helm.tf` file.

    resource "kubernetes_cluster_role_binding" "tiller" {
      depends_on = [google_container_cluster.gke-cluster]
      metadata {
        name = "terraform-tiller"
      }
      role_ref {
        kind      = "ClusterRole"
        name      = "cluster-admin"
        api_group = "rbac.authorization.k8s.io"
      }
      subject {
        kind = "ServiceAccount"
        name = "terraform-tiller"
        namespace = "kube-system"
      }
    }

Now run `terraform apply` command again to provision the new changes we had added after the previous run. Terraform maintains the state of the previous installation in a `.tfstate` file in same folder. This file is very important for Terraform to keep a track on what was installed before and it will apply only the delta changes from the previous run.

Once the service account is installed, you can proceed with installing the tiller by using the below configuration

    provider "helm" {
      version        = "~> 0.9"
      install_tiller = true
      service_account = "${kubernetes_service_account.tiller.metadata.0.name}"
      namespace       = "${kubernetes_service_account.tiller.metadata.0.namespace}"
      tiller_image    = "gcr.io/kubernetes-helm/tiller:v2.14.0"
    }

Remember to run the `terraform init` since it is a new provider. Once the plugins are downloaded, run the `terraform apply` command. Once the command completes, you should be seeing the tiller pod running in your kubernetes cluster.

    D:\Program Files\Google\Cloud SDK>kubectl get pods --all-namespaces
    NAMESPACE     NAME                                                       READY   STATUS    RESTARTS   AGE
    ...
    kube-system   tiller-deploy-865899565b-p7wb4                             1/1     Running   0          50m

## Installing Couchbase

Couchbase autonomous operator enables and automates operations best practices for deploying and managing Couchbase cluster inside Kubernetes. Couchbase team have published helm charts for both operator and cluster which we will utilize for this guide. However further customization is also possible to replace the default configurations. First step is to tell Helm the repository where to find the charts for Couchbase. You can add the below script into the `helm.tf` file.

    data "helm_repository" "couchbase" {
        name = "couchbase"
        url  = "https://couchbase-partners.github.io/helm-charts/"
    }

Now we will add the necessary resources for installing the couchbase operator and cluster. Copy the below configuration inside your `helm.tf` file.

    resource "helm_release" "cb-operator" {
      depends_on = [kubernetes_service_account.tiller]
        name       = "cb-operator"
        repository = "${data.helm_repository.couchbase.metadata.0.name}"
        chart      = "couchbase-operator"
    }
    resource "helm_release" "cb-cluster" {
      depends_on = [kubernetes_service_account.tiller]
        name       = "cb-cluster"
        repository = "${data.helm_repository.couchbase.metadata.0.name}"
        chart      = "couchbase-cluster"
    }

Run the `terraform apply` command and this will install the couchbase operator and cluster into your Kubernetes cluster. You can validate the workloads by either login to your Google Console and check in UI or you can run the `kubectl` command and view the pods.

    D:\Program Files\Google\Cloud SDK>kubectl get pods --all-namespaces
    NAMESPACE     NAME                                                          READY   STATUS    RESTARTS   AGE
    default       cb-cluster-couchbase-cluster-0000                             0/1     Running   0          3m44s
    default       cb-cluster-couchbase-cluster-0001                             0/1     Running   0          2m23s
    default       cb-cluster-couchbase-cluster-0002                             0/1     Running   0          80s
    default       cb-operator-couchbase-admission-controller-5bc947df98-vnfh5   1/1     Running   0          12m
    default       cb-operator-couchbase-operator-6b8778794f-cvm4q               1/1     Running   0          12m
    ...

## Connecting to Couchbase cluster

Couchbase admin console will be exposed in port 8091 of the cluster pod. You can do port forwarding to any one of the pod by running below command. This exposes the UI console to be accessed through URL [http://localhost:8091][couchbaseadminui] 

    D:\Program Files\Google\Cloud SDK>kubectl port-forward cb-cluster-couchbase-cluster-0000 8091:8091
    Forwarding from 127.0.0.1:8091 -> 8091
    Forwarding from [::1]:8091 -> 8091

[couchbaseadminui]: http://localhost:8091

## Destroying the infrastructure

Terraform keeps a track of the infrastructure provisioned till now, so it is really easy to destroy it with just a single command `terraform destroy`. Just like all previous terraform commands this will list the infrastructure details that are marked for deletion and requests for your confirmation. Once you typed `yes`, it will go ahead and destroy the infrastructure.

You can also destroy any one specific resource alone by specifying a target attribute. So in our scenario, if we want to destroy the resources one by one in an order then you can run the below commands in order.

    terraform destroy -target helm_release.cb-cluster
    terraform destroy -target helm_release.cb-operator
    terraform destroy -target kubernetes_service_account.tiller
    terraform destroy -target kubernetes_cluster_role_binding.tiller
    terraform destroy -target google_container_cluster.gke-cluster
