---
title: Getting started with Anthos on bare metal
description: Learn how to deploy a sample Anthos on bare metal cluster.
author: mikegcoleman
tags: Kubernetes, cluster
date_published: 2020-01-15
---

Mike Coleman | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial is for developers and operators who want to learn about Anthos on bare metal. It walks you through installing an Anthos cluster on your own
server hardware using Anthos on bare metal. It covers the benefits of deploying Anthos on bare metal, necessary prerequisites, the installation process, and 
using Google Cloud operations capabilities to inspect the health of the deployed cluster. This tutorial assumes that you have a base understanding of both Google
Cloud and Kubernetes, as well as familiarity operating from the command line in Cloud Shell.

In this tutorial you deploy a two-node Kubernetes cluster that is registered with the Google Cloud Console. You use the `bmctl` command-line utility to create a 
skeleton configuration file that you customize, and then you deploy the cluster using `bmctl` and your customized configuration file. You then take a look at 
some automatically created Google Cloud Operations dashboards.

## Objectives

* Install the Anthos on bare metal command-line utility (`bmctl`).
* Create a cluster configuration file.
* Adjust the cluster configuration file.
* Deploy the cluster.
* Enable the cluster in the Google Cloud Console.
* Access custom Google Cloud Operations dashboards.

## Costs

This tutorial uses billable components of Google Cloud, including
[Anthos on bare metal](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/concepts/about-bare-metal).

Use the [Anthos pricing documentation](https://cloud.google.com/anthos/pricing) to get a cost estimate based on your projected usage.

## Before you begin

To complete this tutorial you need the resources described in this section.

### Google Cloud resources

* A Google Cloud account with sufficient permissions to create the necessary resources and service accounts.

* A Google Cloud project for which you have the `owner` and `editor` roles.

* Three Google Cloud service accounts (SAs), which can be automatically created with the `bmctl` command-line tool:

  * GCR SA: This service account is used to access the Anthos on bare metal software. This service account doesn’t require any specific IAM roles.
  
  * GKE connect SA: This service account is used to register your cluster and view it in the Cloud Console. This service account requires the
  `roles/gkehub.connect` and `roles/gkehub.admin` IAM roles.

  * Cloud operations SA: This service account is used to send system logs and metrics to your project. This service account requires the following IAM roles:

    * `roles/logging.logWriter`
    * `roles/monitoring.metricWriter`
    * `roles/stackdriver.resourceMetadata.writer`
    * `roles/monitoring.dashboardEditor`

* If you want Anthos on bare metal to automatically provision some Google Cloud Operations dashboards, you need to create a Cloud Monitoring Workspace.

* Your local network needs connectivity to Google Cloud. This can be through the internet, a VPN, or Cloud Interconnect. 

### Computers and operating systems

You need two computers that meet the following requirements:

* At least 32GB of RAM, a 4-core CPU, and 128GB of free storage.
* Linux operating system supported for Anthos on bare metal:

  * [Ubuntu 18.04/20.04 LTS](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/ubuntu)
  * [Red Hat Enterprise Linux 8.1](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/rhel)
  * [CentOS 8.1](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/centos)

One of these computers is the Kubernetes control plane; the other is a Kubernetes worker node. The author of this tutorial used Intel Next Unit of Computing 
(NUC) devices in his home lab.

On Ubuntu, AppArmor and UFW must be disabled, if they are installed.

On Red Hat Enterprise Linux and CentOS, SELinux must be set to `permissive` if it's installed, and `firewalld` must be disabled.

This tutorial uses passwordless root SSH access to the Kubernetes nodes. You must be able to access the worker computer from the control plane computer (and vice
versa) with the following command:

    ssh -o IdentitiesOnly=yes -i [YOUR_IDENTITY_FILE] root@&[NODE_IP_ADDRESS]

Anthos for bare metal also supports non-root users (`sudo`). For more information, see
[the documentation](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/install-prereq).

### Software

One of the two computers needs the following software in order to run `bmctl` and provision your cluster:

 * `gcloud` and `gsutil`, which you can install as part of the [Cloud SDK](https://cloud.google.com/sdk/docs/install)
 * `kubectl`
 * [Docker](https://docs.docker.com/engine/install/) version 19.03 or later

## Install the Anthos on bare metal command-line utility

In this section, you install the Anthos on bare metal command-line utility, `bmctl`.

`bmctl` is used to manage the provisioning and deprovisioning of your Anthos on bare metal clusters.

1.  Connect to one of your two nodes with SSH.

1.  Create a `baremetal` directory and change into that directory:

        mkdir baremetal && cd baremetal

1.  Download the `bmctl` binary and set the execution bit:

        gsutil cp gs://anthos-baremetal-release/bmctl/1.6.0/linux-amd64/bmctl . 
        && chmod a+x bmctl

1.  Ensure that `bmctl` was installed correctly by viewing the help information

        ./bmctl -h

## About networking for Anthos on bare metal

Before you deploy the cluster, it’s important to understand some details about how networking works with Anthos on bare metal.

When configuring Anthos on bare metal, you specify three distinct IP subnets. Two are fairly standard to Kubernetes: the pod network and the services network. 
The third subnet is used for ingress and load balancing. The IP addresses associated with this network must be on the same local L2 network as your load balancer
node (which in the case of this tutorial is the same as the control plane node). You need to specify an IP address for the load balancer, one for ingress, and 
then a range for the load balancers to draw from to expose your services outside the cluster. The ingress virtual IP address must be within the range that you 
specify for the load balancers, but the load balancer IP address should not be in the given range. 

The CIDR block that the author of this tutorial used for his local network is `192.168.86.0/24`. The author's Intel NUCs are all on the same switch, so they are 
all on the same L2 network. The default pod network (`192.168.0.0/16`) overlaps with this home network. To avoid any conflicts, the author set his pod network to 
use `172.16.0.0/16`. Because there is no conflict, the services network is using the default (`10.96.0.0/12`). Ensure that your chosen local network doesn’t 
conflict with the defaults chosen by `bmctl`. 

Given this configuration, the control plane virtual IP address is set to `192.168.86.99`. The ingress virtual IP address, which needs to be part of the range
that you specify for your load balancer pool, is `192.168.86.100`. The pool of addresses for the load balancers is set to `192.168.86.100`-`192.168.86.150`.  

In addition to the IP ranges, you also need to specify the IP address of the control plane node and the worker node. In the case of the author's setup, the
control plane is `192.168.86.51` and the worker node IP address is `192.168.86.52`.

## Creating the cluster configuration File

To get started, you use `bmctl` to create a configuration file. Then you customize the configuration file and deploy the cluster based on your configuration 
file. When the clusters are deployed, you can view the cluster nodes and deploy applications with `kubectl`.

With Anthos on bare metal, you can create
[standalone or multi-cluster deployments](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/install-prep):

* **Standalone**: This deployment model has a single cluster that serves as a user cluster and as an admin cluster.
* **Multi-cluster**: This deployment model is used to manage fleets of clusters and includes both admin and user clusters.

In this tutorial you deploy a standalone cluster. 

1.  Using the SSH connection that you established in the installation section, authenticate to Google Cloud:

        gcloud auth application-default login 

1.  Export an environment variable that holds your Google Cloud project ID:

        export PROJECT_ID=[YOUR_PROJECT_ID]

    For example:
    
        export PROJECT_ID=mikegcoleman-anthos-bm

     You must have owner and editor permissions for this project.

1.  Create the cluster configuration file:  

        ./bmctl create config -c demo-cluster 
        --enable-apis \
        --create-service-accounts \
        --project-id=$PROJECT_ID
    
    This command creates a configuration file that creates a cluster with the name `demo-cluster`. If you want to use a different cluster name, change
    `demo-cluster` here. The `--enable-apis` and `--create-service-accounts` flags automatically enable the
    [correct APIs and service accounts](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/quickstart#configuring-sa).
    
    You should see output similar to the following: 

        Enabling APIs for GCP project mikegcoleman-anthos-bm
        Creating service accounts with keys for GCP project mikegcoleman-anthos-bm
        Service account keys stored at folder bmctl-workspace/.sa-keys
        Created config: bmctl-workspace/demo-cluster/demo-cluster.yaml

The `bmctl` command creates a configuration file under the `baremetal` directory at `bmctl-workspace/demo-cluster/demo-cluster.yaml`.

## Edit the cluster configuration file

In this section, you update the configuration file with the appropriate values.

Open the configuration file in a text editor and make the following changes, being careful of indentation:

* In the list of access keys at the top of the file, after `sshPrivateKeyPath`, specify the path to your SSH private key.
* In the cluster definition, do the following:
    *   Change the type (`Cluster:spec:type`) to `standalone`.
    *   Set the IP address of the control plane node (`Cluster:controlPlane:nodePoolSpec:nodes:addresses`).
    *   Ensure that the networks for the pods and services do not conflict with your home network
        (`Cluster:clusterNetwork:pods:cidrBlocks` and `Cluster:clusterNetwork:services:cidrBlocks`).
    *   Specify the control plane virtual IP address (`Cluster:loadBalancer:vips:controlPlaneVIP`).
    *   Uncomment and specify the ingress virtual IP address (`Cluster:loadBalancer:vips:controlPlaneVIP`).
    *   Uncomment the `addressPools` section (excluding actual comments) and specify the load balancer address pool 
        (`Cluster:loadBalancer:addressPools:addresses`).
* In the `NodePool` definition, specify the IP address of the worker node (`NodePool:spec:nodes:addresses`).

For reference, below is a complete example cluster definition YAML file, with the comments removed for brevity. As described in the previous section
about networking, this example shows changes to the pod and services networks; you may not need to make such changes, depending on the IP address range of your
local network.  

    sshPrivateKeyPath: /home/mikegcoleman/.ssh/id_rsa
    gkeConnectAgentServiceAccountKeyPath: /home/mikegcoleman/baremetal/bmctl-workspace/.sa-keys/mikegcoleman-anthos-bm-anthos-baremetal-connect.json
    gkeConnectRegisterServiceAccountKeyPath: /home/mikegcoleman/baremetal/bmctl-workspace/.sa-keys/mikegcoleman-anthos-bm-anthos-baremetal-register.json
    cloudOperationsServiceAccountKeyPath: /home/mikegcoleman/baremetal/bmctl-workspace/.sa-keys/mikegcoleman-anthos-bm-anthos-baremetal-cloud-ops.json
    ---
    apiVersion: v1
    kind: Namespace
    metadata:
      name: cluster-demo-cluster
    ---
    apiVersion: baremetal.cluster.gke.io/v1
    kind: Cluster
    metadata:
      name: demo-cluster
      namespace: cluster-demo-cluster
    spec:
      type: standalone
      anthosBareMetalVersion: 0.7.0-gke.0
      gkeConnect:
        projectID: mikegcoleman-anthos-bm
      controlPlane:
        nodePoolSpec:
          nodes:
          - address: 192.168.86.51
      clusterNetwork:
        pods:
          cidrBlocks:
          - 172.16.0.0/16
        services:
          cidrBlocks:
          - 10.96.0.0/12
      loadBalancer:
        mode: bundled
        ports:
          controlPlaneLBPort: 443
        vips:
          controlPlaneVIP: 192.168.86.99
          ingressVIP: 192.168.86.100
        addressPools:
        - name: pool1
          addresses:
          - 192.168.86.100-192.168.86.150
      clusterOperations:
        projectID: mikegcoleman-anthos-bm
        location: us-central1
      storage:
        lvpNodeMounts:
          path: /mnt/localpv-disk
          storageClassName: local-disks
        lvpShare:
          path: /mnt/localpv-share
          storageClassName: local-shared
          numPVUnderSharedPath: 5
    ---
    apiVersion: baremetal.cluster.gke.io/v1
    kind: NodePool
    metadata:
      name: node-pool-1
      namespace: cluster-demo-cluster
    spec:
      clusterName: demo-cluster
      nodes:
      - address: 192.168.86.52

## Create the cluster

In this section, you create the cluster based on the configuration file that you modified in the previous section.

1.  Create the cluster:

        ./bmctl create cluster -c demo-cluster

    `bmctl` runs a series of preflight checks before creating your cluster. If any of the checks fail, check the log files specified in the output.

    When the installation is complete, you can find the `kubeconfig` file at: `/bmctl-workspace/demo-cluster/demo-cluster-kubeconfig`.

1.  To avoid specifying the `kubeconfig` file location in each `kubectl` command after this point, export it to an environment variable:

        export KUBECONFIG=$(pwd)/bmctl-workspace/demo-cluster/demo-cluster-kubeconfig
        
    You may need to modify the command above for your cluster name.

1.  List the nodes in the cluster:

        kubectl get nodes

    The output looks something like this: 
 
        NAME     STATUS   ROLES    AGE     VERSION 
        node-1   Ready    master   5m27s   v1.17.8-gke.16
        node-2   Ready    <none>   4m57s   v1.17.8-gke.1

## View your cluster in the Cloud Console

In this section, you view your deployed cluster in the Cloud Console.

1.  Go to the [Cloud Console](https://console.cloud.google.com). 

1.  If the navigation menu is not open, click the **Navigation menu** icon in the upper-left corner of the Cloud Console.

1.  In the navigation menu, scroll down to **Anthos** and choose **Clusters**.

    Your cluster is displayed in the right-hand pane. You’ll notice, however, that there is an error. That’s because you need to create a Kubernetes service 
    account (KSA) with the appropriate roles to view cluster details.  
 
    The KSA needs the built-in `view` role as a custom role (`cloud-console-reader`), which you create next. You also need the `cluster-admin` role to allow
    installation of applications from Google Marketplace (which you do in the next section).

1.  Using the SSH connection that you have been working in for previous sections, run the following commands to create the `cloud-console-reader` cluster role:

        cat <<EOF > cloud-console-reader.yaml
        kind: ClusterRole
        apiVersion: rbac.authorization.k8s.io/v1
        metadata:
          name: cloud-console-reader
        rules:
        - apiGroups: [""]
          resources: ["nodes", "persistentvolumes"]
          verbs: ["get", "list", "watch"]
        - apiGroups: ["storage.k8s.io"]
          resources: ["storageclasses"]
          verbs: ["get", "list", "watch"]
        EOF

        kubectl apply -f cloud-console-reader.yaml

    You should see the following output: 
 
        clusterrole.rbac.authorization.k8s.io/cloud-console-reader created


1.  Export an environment variable to hold the KSA name:

        KSA_NAME=abm-console-service-account

1.  Create the KSA: 

        kubectl create serviceaccount ${KSA_NAME}
  
     You should see the following output: 
 
        serviceaccount/abm-console-service-account created

1.  Bind the `view`, `cloud-console-reader`, and `cluster-admin` roles to the newly created KSA:

        kubectl create clusterrolebinding cloud-console-reader-binding \
        --clusterrole cloud-console-reader \
        --serviceaccount default:${KSA_NAME}

        kubectl create clusterrolebinding cloud-console-view-binding \
        --clusterrole view \
        --serviceaccount default:${KSA_NAME}

        kubectl create clusterrolebinding \
        cloud-console-cluster-admin-binding \
        --clusterrole cluster-admin \
        --serviceaccount default:${KSA_NAME}

    If the role bindings are created successfully, the output looks like the following:

        clusterrolebinding.rbac.authorization.k8s.io/cloud-console-view-binding created

1.  Create a secret and obtain the bearer token for the KSA:

        SECRET_NAME=${KSA_NAME}-token

        kubectl apply -f - << __EOF__
        apiVersion: v1
        kind: Secret
        metadata:
          name: "${SECRET_NAME}"
          annotations:
            kubernetes.io/service-account.name: "${KSA_NAME}"
        type: kubernetes.io/service-account-token
        __EOF__

        kubectl get secret ${SECRET_NAME} -o jsonpath='{$.data.token}' \
        | base64 --decode

    The output from the `kubectl` command is a long string.

1.  Copy the token string output from the previous step.

    In some cases the token string might not be copied in a format that can be pasted correctly in the next step.You can paste the token string 
    into a text editor and ensure there are no line breaks. The token string must be continuous for the next step to work.  

1.  In the Cloud Console, click the name of your cluster. 

1.  Click **Login**.

1.  Choose **Token** from the list of options. 

1.  Paste the token string  into the text box. 

14. Click **Login**. 

The Cloud Console should now indicate that the cluster is healthy. If you receive a login error, double-check that your string contains no line breaks. 

## Exploring Cloud Logging and Cloud Monitoring

Anthos on bare metal automatically creates three Google Cloud Operations (formerly Stackdriver) logging and monitoring dashboards when a cluster is provisioned:
node status, pod status, and control plane status. These dashboards enable you to quickly gain visual insight into the health of your cluster. In addition to the
three dashboards, you can use [Google Cloud Operations Metrics Explorer](https://cloud.google.com/monitoring/charts/metrics-explorer) to create custom queries 
for a wide variety of performance data points.

1.  In the Cloud Console navigation menu, scroll down to **Operations**, choose **Monitoring**, and then choose **Dashboards**.

    You should see the three dashboards in the list in the middle of the screen. 

1.  Choose each of the three dashboards and examine the available graphs. 

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

That’s it! You now know how to use Athos on bare metal to deploy a centrally managed Kubernetes cluster on your own hardware and keep track of it using the 
built-in logging and monitoring dashboards. 

As a next step, you may want to deploy your own application to the cluster or potentially deploy a more complex cluster architecture featuring both Anthos on 
bare metal admin and worker clusters.
