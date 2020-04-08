---
title: Provision Couchbase on Google Kubernetes Engine using Terraform
description: Learn how to provision a Couchbase Autonomous Operator and cluster inside a Google Kubernetes Engine cluster using Terraform scripts.
author: kishoreallwynraj
tags: Google Kubernetes Engine, Couchbase Autonomous Operator, Couchbase cluster, Terraform
date_published: 2019-09-04
---

## Introduction

This tutorial helps you learn how to provision a Couchbase Autonomous Operator and cluster inside a Google Kubernetes Engine 
cluster on Google Cloud Platform (GCP) using Terraform scripts.

## Prerequisites

-   **GCP account**: If you don’t have a GCP account, [create one now][gcpcreateaccount]. This tutorial can be
    completed using only the services included in [GCP  Free Tier][gcpfree].
-   **GCP project**: GCP organizes resources into projects. You can [create one][gcpcreateproject] in the GCP Console.
    You need the project ID later in this tutorial.
-   **GCP service account key**: Terraform will access your GCP account by using a service account key. You
    can [create one][gcpcreatesvcacc] in the GCP Console. While creating the key, assign the role as **Project > Editor**.
-   **Cloud SDK**: You can install the Cloud SDK with [these instructions][googlesdk]. This SDK installs `kubectl`, which
    is required for this tutorial. Go ahead and log in to your project using `gcloud`.
-   **Google Kubernetes Engine API**: You can enable the Google Kubernetes Engine API for your project in
    the [GCP Console][gcpk8api].
-   **Terraform**: You can install Terraform with [these instructions][terraform].
-   **Helm**: You can install Helm with [these instructions][helm].

[gcpcreateaccount]: https://console.cloud.google.com/freetrial/
[gcpfree]: https://cloud.google.com/free/
[terraform]: https://learn.hashicorp.com/terraform/gcp/install
[googlesdk]: https://cloud.google.com/sdk/install
[helm]: https://helm.sh/docs/using_helm/#install-helm
[gcpcreateproject]: https://console.cloud.google.com/projectcreate
[gcpcreatesvcacc]: https://console.cloud.google.com/apis/credentials/serviceaccountkey
[gcpk8api]: https://console.developers.google.com/apis/api/container.googleapis.com

## Initializing the workspace

Create a directory for the examples in this tutorial, create a file named `main.tf`, and copy this configuration into it:

    provider "google" {
      credentials = file("[SERVICE_ACCOUNT].json")
      project = "[PROJECT_ID]"
      region  = "europe-west3"
      zone    = "europe-west3-a"
    }

Be sure to replace the `[SERVICE_ACCOUNT]` and `[PROJECT_ID]` with the file name and the ID you got while setting up your
GCP project.

The provider block is used to configure the named provider, in this case `google`. A provider is responsible for creating 
and managing the resources. Multiple provider blocks can exist in the Terraform file if you need to manage resources from 
different providers, which you do later in this tutorial.

When a new provider is added to the Terraform file, the first command that needs to run is the `terraform init` in the same
directory where you have the `main.tf` file. This downloads the `google` provider plugin and installs it in a subdirectory
in the current working directory. You need to run this command whenever you add a new provider section in your script file.

## Creating the Kubernetes cluster

The Terraform `google` provider has resources available for provisioning a container cluster. More details on the resource 
are available [here][tfcontainer]. This tutorial uses the defaults for many of these resources. Copy this configuration into
your `main.tf` file:

    resource "google_container_cluster" "gke-cluster" {
      name               = "tf-gke-cluster"
      network            = "default"
      zone               = "europe-west3-a"
      initial_node_count = 3
    }

This script provisions a three-node Kubernetes cluster in the project configured in the `provider` section. It uses the
default network, which is already available in your project. (The network can be customized to your needs with a script, but
this is not covered in this tutorial. For details, see the [Terraform documentation][tfcontainer].)

Now you can run `terraform plan` in same directory. The output of this command is the details of what resources Terraform
is going to create for you. This command does not create the resources. To create the resources, you need to run the 
`terraform apply` command.

After the cluster is created, you need the credentials to connect to the cluster and view the workloads running. The GCP 
Console displays the SDK command that needs to be executed to get the credentials and save into your local kube config file.
Terraform provides a way for you to run this command within the script as part of provisioning scripts, which can be 
executed during cluster bootstrapping. There are multiple providers for running provisioning scripts, but for this tutorial 
you use the `local-exec` provisioner:

    provisioner "local-exec" {
        command = "gcloud container clusters get-credentials ${google_container_cluster.gke-cluster.name} --zone  ${google_container_cluster.gke-cluster.zone} --project [PROJECT_ID]"
    }

For information about other provisioners available in Terraform, see the [Terraform documentation][tfprovisioner].

Now run the `terraform apply` command. This command outputs the same details as the `terraform plan` command, and it also
asks for confirmation from you to proceed further. After you enter `yes`, Terraform creates the cluster. The cluster 
creation takes a few minutes. You can verify the creation of the cluster in the GCP Console.

To verify that the cluster credentials are saved in your kube config, run `kubectl config view`. The output should look 
something like this:

    D:\Program Files\Google\Cloud SDK>kubectl config view
    apiVersion: v1
    clusters:
    - cluster:
        certificate-authority-data: DATA+OMITTED
        server: https://[Cluster_IP]
      name: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
    contexts:
    - context:
        cluster: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
        user: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
      name: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
    current-context: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
    kind: Config
    preferences: {}
    users:
    - name: gke_[PROJECT_ID]_europe-west3-a_tf-gke-cluster
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

You can view the cluster created and running in the GCP Console. You can directly view the workloads in the web UI or, since
the cluster configurations are now available in your kube config, you can also run the command
`kubectl get pods --all-namespaces` to display the pods running. The output from that command should look something like 
this:

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

Helm is the package manager for deploying software packages inside your Kubernetes cluster. Helm works alongside its
server-side component Tiller to perform the installations inside the cluster. Tiller needs to be provided with a service 
account with cluster admin privileges so that it can deploy the required software packages. So, before installing Tiller, 
create the service account. Terraform has a Kubernetes provider, which we will use to create a cluster admin role and 
associate a service account with it. 

Create a new file `helm.tf` and copy this code into it:

    provider "kubernetes" {
      version = ">= 1.4.0"
     }

Run the `terraform init` command, since this is a new provider added after our previous `init` run.

Copy this code into the `helm.tf` file to create the service account:

    resource "kubernetes_service_account" "tiller" {
      depends_on = [google_container_cluster.gke-cluster]
      metadata {
      name      = "terraform-tiller"
      namespace = "kube-system"
      }
      automount_service_account_token = true
    }

The code above has a `depends_on` section that gives the name of the Google container cluster added in `main.tf`. This 
ensures that Terraform creates the Kubernetes cluster before trying to create the service account. The next step is to 
create the cluster admin role and associate the service account. Copy this code into your `helm.tf` file:

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

Run `terraform apply` again to provision the new changes added after the previous run. Terraform maintains the state of the 
previous installation in a `.tfstate` file in same folder. This file is very important for Terraform to keep track of what
was installed before, and it will apply only the incremental changes since the previous run.

After the service account is installed, you can proceed with installing Tiller with this configuration:

    provider "helm" {
      version        = "~> 0.9"
      install_tiller = true
      service_account = "${kubernetes_service_account.tiller.metadata.0.name}"
      namespace       = "${kubernetes_service_account.tiller.metadata.0.namespace}"
      tiller_image    = "gcr.io/kubernetes-helm/tiller:v2.14.0"
    }

Run the `terraform init` command again, since the code above adds a new provider. After the plugins are downloaded, run the 
`terraform apply` command. After the command completes, you should see the Tiller pod running in your Kubernetes cluster:

    D:\Program Files\Google\Cloud SDK>kubectl get pods --all-namespaces
    NAMESPACE     NAME                                                       READY   STATUS    RESTARTS   AGE
    ...
    kube-system   tiller-deploy-865899565b-p7wb4                             1/1     Running   0          50m

## Installing Couchbase

The Couchbase Autonomous Operator enables and automates operations best practices for deploying and managing Couchbase 
clusters inside Kubernetes. The Couchbase team has published Helm charts for operators and clusters, which are used in this
tutorial. Further customization is also possible to replace the default configurations. Add the following code into the 
`helm.tf` file to tell Helm the repository where it can find the charts for Couchbase:

    data "helm_repository" "couchbase" {
        name = "couchbase"
        url  = "https://couchbase-partners.github.io/helm-charts/"
    }

To add the resources for installing the Couchbase operator and cluster, copy the following code into your `helm.tf` file:

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

Run the `terraform apply` command to install the Couchbase operator and cluster into your Kubernetes cluster.

You can verify the workloads in the GCP Console, or you can run the `kubectl get pods` command to view the pods: 

    D:\Program Files\Google\Cloud SDK>kubectl get pods --all-namespaces
    NAMESPACE     NAME                                                          READY   STATUS    RESTARTS   AGE
    default       cb-cluster-couchbase-cluster-0000                             0/1     Running   0          3m44s
    default       cb-cluster-couchbase-cluster-0001                             0/1     Running   0          2m23s
    default       cb-cluster-couchbase-cluster-0002                             0/1     Running   0          80s
    default       cb-operator-couchbase-admission-controller-5bc947df98-vnfh5   1/1     Running   0          12m
    default       cb-operator-couchbase-operator-6b8778794f-cvm4q               1/1     Running   0          12m
    ...

## Connecting to Couchbase cluster

The Couchbase admin console is exposed on port 8091 of the cluster pod. You can use port forwarding to any of the pods by 
running the `kubectl port-forward` as shown here:

    D:\Program Files\Google\Cloud SDK>kubectl port-forward cb-cluster-couchbase-cluster-0000 8091:8091
    Forwarding from 127.0.0.1:8091 -> 8091
    Forwarding from [::1]:8091 -> 8091

This exposes the UI console to be accessed through the URL `http://localhost:8091`.

## Destroying the resources

Terraform keeps track of the resources that it has provisioned, so it is easy to destroy these resources with a single 
command: `terraform destroy`. This lists the resources that are marked for deletion and requests your confirmation. After 
you have entered `yes`, Terraform destroys the resources.

You can also destroy any one specific resource alone by specifying a target attribute. So, in the scenario of this tutorial,
if you want to destroy the resources one by one, then you can run these commands:

    terraform destroy -target helm_release.cb-cluster
    terraform destroy -target helm_release.cb-operator
    terraform destroy -target kubernetes_service_account.tiller
    terraform destroy -target kubernetes_cluster_role_binding.tiller
    terraform destroy -target google_container_cluster.gke-cluster
