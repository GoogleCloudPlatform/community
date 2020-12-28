---
title: Getting Started with Anthos for Bare Metal
description: This tutorial covers deploying a sample Anthos on Bare Metal cluster. 
author: mikegcoleman
tags: Kubernetes, Cluster, Anthos, Bare, Metal, Google Cloud Platform
date_published: 2020-12-28
---

Mike Coleman | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial is aimed at developers and opeartors who want to learn about Anthos for bare metal. It walks through installing an Anthos cluster on your own server hardware using Anthos for Bare Metal. It covers the benefits of deploying Anthos on bare metal, necessary prerequisites, the installation process, and using Google Cloud operations capabilities to inspect the health of the deployed cluster. It assumes that you have a base understanding of both Google Cloud Platform and Kubernetes, as well as familiarity operating from the command line in Gooogle Cloud Shell.


## Objectives

* Install the Anthos on bare metal conmmand line utility (`bmctl`)
* Creating a cluster configuration file
* Adjusting the cluster configuration file
* Deploying the cluster
* Enabling the cluster in the Google Cloud console
* Accessing custom Google Cloud Operations dashboards


## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Anthos on bare metal](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/concepts/about-bare-metal)


Use the [Anthos pricing documentation](https://cloud.google.com/anthos/pricing) to get a cost estimate based on your projected usage.

## What is Anthos and Why Run it on Bare metal?

We recently announced that [Anthos on bare metal](https://cloud.google.com/blog/topics/hybrid-cloud/anthos-on-bare-metal-is-now-ga) is generally available. I don’t want to rehash the entirety of that post, but I do want to recap some key benefits of running Anthos on your own systems, in particular: 



*   Removing the dependency on a hypervisor can lower both the cost and complexity of running your applications. 
*   In many use cases, there are performance advantages to running workloads directly on the server. 
*   Having the flexibility to deploy workloads closer to the customer can open up new use cases by lowering latency and increasing application responsiveness. 


## What You Will Deploy

For this tutorial you’ll deploy a two-node Kubernetes cluster that is registered with the Google Cloud console. You’ll also take a quick look at some automatically created Google Cloud Operations dashboards.


## Before you begin

To complete this tutorial you’ll need the following:

*   A Google Cloud account with sufficient permissions to create the necessary resources and service accounts, as well as access to a Google Cloud project for which you have the `owner` and `editor` roles.
*   Anthos on bare metal needs the following three Google Cloud service account (SA) (note: these service accounts can be automatically created with `bmctl`).
*   The first service account is used to access the Anthos on bare metal software, this is referenced as the GCR SA. It doesn’t require any specific IAM roles. 
*   The second service account is used to register your cluster and view it in the cloud console. This is referenced as GKE connect SA and requires the `roles/gkehub.connect` and `roles/gkehub.admin `IAM roles
*   The third service account is used to send system logs and metrics to your project. This is referenced as cloud operations SA and requires the following IAM Roles:
    *   `roles/logging.logWriter`
    *   `roles/monitoring.metricWriter`
    *   `roles/stackdriver.resourceMetadata.writer`
    *   `roles/monitoring.dashboardEditor`
*   If you wish for Anthos on bare metal to automatically provision some Google Cloud Operations dashboards you will need to create a Cloud Monitoring Workspace.
*   Two Linux-based machines. One of these will serve as the Kubernetes controle plane, the other will be a Kubernetes worker node. I used Intel Next Unit of Computing (NUC) devices in my home lab.
    *   These machines need to be running a supported operating system and be equipped with at least 32GB or RAM, a 4 core processor, and 128GB of free storage. \
    \
    Anthos on bare metal supports the following distributions and versions:

        *   [Ubuntu 18.04/20.04 LTS](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/ubuntu)
        *   [Red Hat Enterprise Linux 8.1](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/rhel)
        *   [CentOS 8.1](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/configure-os/centos)
    *   On Ubuntu machines, if installed, AppArmor and UFW must be disabled. On RHEL or CentOS machines, if installed, SELinux must be set to `permissive`, and `firewalld` disabled. 
*   One of the two machines also needs the following software in order to run `bmctl` and provision your cluster
    *   Both `gcloud` and `gsutils`, which can be installed as part of the [Cloud SDK](https://cloud.google.com/sdk/docs/install)
    *   `Kubectl`
    *   [Docker 19.03](https://docs.docker.com/engine/install/) or later.
*   This tutorial uses passwordless root SSH access to the Kubernetes nodes. You must be able to access the worker machine from the control plane machine (and vice versa) with the command below.  \
 \
`ssh -o IdentitiesOnly=yes -i <your identity file> root@&<node_ip> `
 \
\
Anthos for bare metal also supports non-root users (sudo) see [the documentation](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/install-prereq) for more information. 
*   Your local network needs connectivity to Google Cloud. This can be over the Internet, via VPN, or via Cloud Interconnect. 

Once the above requirements have been met you’re ready to begin deploying Anthos on bare metal. You will start by downloading the `bmctl` binary. You will use `bmctl` to create a skeleton configuration file that you’ll customize, and then you will deploy the actual cluster using `bmctl` and your customized configuration file. 


## Install the Anthos on Bare Metal Command Line Utility

In this section you will install the Anthos on bare metal CLI utility, `bmctl`. `bmctl` is used to manage the provisioning and deprovisioning of your Anthos on bare metal clusters

1. SSH into one of your two nodes 

2. Create a baremetal directory and change into that directory \
 \
`mkdir baremetal && cd baremetal` 

3. Download the bmctl binary and set the execution bit \
 \
`gsutil cp gs://anthos-baremetal-release/bmctl/1.6.0/linux-amd64/bmctl . 
&& chmod a+x bmctl` 

4. Ensure bmctl installed correctly by viewing the help information \
 \
`./bmctl -h`

With `bmctl` installed you’re now ready to create your Anthos on bare metal cluster. 

## Side note: Anthos on Bare Metal Networking

Before you actually deploy the cluster it’s important to talk about networking. When configuring Anthos on bare metal, you will need to specify three distinct IP subnets.

Two are fairly standard to Kuberenetes: the pod network and the services network. 

The third subnet is used for ingress and load balancing. The IPs associated with this network must be on the same local L2 network as your load balancer node (which in the case of this tutorial is the same as the control plane node). You will need to specify an IP for the load balancer, one for ingress, and then a range for the load balancers to draw from to expose your services to outside the cluster. The ingress VIP must be within the range you specify for the load balancers, but the load balancer IP should not be in the given range. 

The CIDR range for my local network is 192.168.86.0/24. Furthermore, I have my Intel NUCs all on the same switch, so they are all on the same L2 network. 

One thing to note is that the default pod network (192.168.0.0/16) overlaps with my home network. To avoid any conflicts, I set my pod network to use 172.16.0.0/16. Because there is no conflict, my services network is using the default (10.96.0.0/12). Ensure that your chosen local network doesn’t conflict with the defaults chosen by `bmctl`. 

Given this configuration, I’ve set my control plane VIP to 192.168.86.99. The ingress VIP, which needs to be part of the range that you specify for your load balancer pool, is 192.168.86.100. And, I’ve set my pool of addresses for my load balancers to 192.168.86.100-192.168.86.150.  

In addition to the IP ranges, you will also need to specify the IP address of the control plane node and the worker node. In my case the control plane is 192.168.86.51 and the worker node IP is 192.168.86.52.

## Creating the Cluster Configuration File

With the networking covered, you’re ready to deploy the cluster. To get started, you use `bmctl` to create a config file. Next you’ll customize the configuration file. Finally you will deploy the cluster based upon your configuration file. Once deployed you can view the cluster nodes and deploy applications with `kubectl`.

Using Anthos on bare metal you can create [standalone or multi-cluster deployments](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/installing/install-prep):

* __Standalone__: This deployment model has a single cluster that serves as a user cluster and as an admin cluster
* __Multi-cluster__: Used to manage fleets of clusters and includes both admin and user clusters.

In this tutorial you will be deploying a Standalone cluster. 

1. You should still be ssh’d into the node you were using previously 

2. Authenticate to Google Cloud \
 \
`gcloud auth application-default login 
`
3. Export an environment variable that holds your Google Cloud project ID. Remember, you need to have owner and editor permissions on this project. \
 \
`export PROJECT_ID=<your project id>` \
 \
For example: \
 \
`export PROJECT_ID=mikegcoleman-anthos-bm` 

4. Create the cluster configuration file. The command below creates a configuration file, which will in turn create a cluster with the name “demo-cluster.” If you want to use a different cluster name, change “demo-cluster” here. The `--enable-apis` and `--create-service-accounts` flags automatically enable the [correct APIs and service accounts](https://cloud.google.com/anthos/gke/docs/bare-metal/1.6/quickstart#configuring-sa).  
 
    ```
        ./bmctl create config -c demo-cluster 
        --enable-apis \
        --create-service-accounts \
        --project-id=$PROJECT_ID
    ```
      You should see output similar to the following:  
      

    ```
    Enabling APIs for GCP project mikegcoleman-anthos-bm
        Creating service accounts with keys for GCP project mikegcoleman-anthos-bm
        Service account keys stored at folder bmctl-workspace/.sa-keys
        Created config: bmctl-workspace/demo-cluster/demo-cluster.yaml
    ```


As the output shows, the `bmctl` command creates a configuration file under the `baremetal` directory at: `bmctl-workspace/demo-cluster/demo-cluster.yaml ` \

## Edit the Cluster Configuration File and Create the Cluster
The next step is to edit the config file supplying the appropriate values and then use this configuration file to deplooy the actual cluster

1. Open the configuration file in your favorite text editor and make the following changes:

    Under the list of access keys at the top of the file:

    *   After `sshPrivateKeyPath` specify the path to your SSH private key

    Under the Cluster definition:

    *   Change the type to **_standalone_** (`Cluster:spec:type`)
    *   Set the IP address of the control plane node (`Cluster:controlPlane:nodePoolSpec:nodes:addresses`) 
    *   Ensure the neworks for the pods and services do not conflict with your home network (`Cluster:clusterNetwork:pods:ciderBlocks` and `Cluster:clusterNetwork:services:ciderBlocks`)
    *   Specify the control plane VIP (`Cluster:loadBalancer:vips:controlPlaneVIP`)
    *   Uncomment and specify the ingress VIP (`Cluster:loadBalancer:vips:controlPlaneVIP`)
    *   Uncomment the addressPools section (excluding actual comments) and specify the load balancer address pool (`Cluster:loadBalancer:addressPools:addresses`) 

    Note: Be careful with the indentation; you can check yours against my example below. 

    Under the NodePool definition:

    *   Specify the IP address of the worker node (`NodePool:spec:nodes:addresses`)

    For reference, here is a complete cluster definition yaml for my cluster setup (with the comments removed for the sake of brevity).

    Note: remember that I needed to change my pod and services networks, you may not need to do this depending on the IP address range of your local network.  

    ```
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
      - address: <strong>192.168.86.52
    ```

1. Use `bmctl` to create the cluster \
 \
./`bmctl create cluster -c demo-cluster`

    `bmctl` will complete a series of preflight checks before creating your cluster. If any of the checks fail, check the log files specified in the output. 


    Once the installation is complete, you can find the kubeconfig file at: `/bmctl-workspace/demo-cluster/demo-cluster-kubeconfig` 

1. To avoid having to specify it in each kubectl command after this point, export an environment variable for the kubeconfig (be sure to edit this to reflect your cluster name). \
 \
`export KUBECONFIG=$(pwd)/bmctl-workspace/demo-cluster/demo-cluster-kubeconfig \
`
1. List the nodes in the cluster \
 \
`kubectl get nodes` \
 \
The output looks something like this: 
 
    ```
    NAME     STATUS   ROLES    AGE     VERSION \
    node-1   Ready    master   5m27s   v1.17.8-gke.16`
    node-2   Ready    <none>   4m57s   v1.17.8-gke.1
    ```



## View Your Cluster in the Google Cloud Console

You now have your cluster deployed, and it should be visible in the Google Cloud console. To verify this:

1. Navigate to [https://console.cloud.google.com](https://console.cloud.google.com). 

2. If your navigation menu is not visible, click the “hamburger” menu in the upper left corner 

3.  Scroll down to **_Anthos_** and choose **_Clusters._**

4. Your cluster is displayed in the right-hand pane. You’ll notice, however, that there is an error. That’s because you need to create a Kubernetes service account (KSA) with the appropriate roles to view cluster details.  
 
    The KSA needs the built-in `view` role as a custom role (`cloud-console-reader`), which you’ll create next. Additionally you need the `cluster-admin` role to allow installation of applications from Google Marketplace (which you will do in the next section). \

5. **_Move back to the SSH session_** and issue the following command to create the `cloud-console-reader` cluster role:

    ```
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
    ```



    You should see the following output: 
 
    ```
    clusterrole.rbac.authorization.k8s.io/cloud-console-reader created
    ```

6. Export an environment variable to hld the KSA name

    ```
    KSA_NAME=abm-console-service-account
    ```


1. Create the KSA. 

    ```
    kubectl create serviceaccount ${KSA_NAME}
    ``` 
  
    You should see the following output: 
 
    ```
    serviceaccount/abm-console-service-account created
    ``` 


7. Next, you need to bind the view, cloud-console-reader, and cluster-admin roles to the newly created KSA. Issue the commands below to create the appropriate cluster role bindings:

    ```
    kubectl create clusterrolebinding cloud-console-reader-binding \
    --clusterrole cloud-console-reader \
    --serviceaccount default:${KSA_NAME}

    kubectl create clusterrolebinding cloud-console-view-binding \
    --clusterrole view \
    --serviceaccount default:${KSA_NAME}

    kubectl create clusterrolebinding \
    cloud-console-cluster-admin-binding \
    --clusterrole cluster-admin \
    --serviceaccount default:$KSA_NAME
    ```

    You should receive messages indicating that the role bindings were created successfully:

      ```
      clusterrolebinding.rbac.authorization.k8s.io/cloud-console-view-binding created
      ```


8. Obtain the bearer token for the KSA:

    ```
    SECRET_NAME=$(kubectl get serviceaccount ${KSA_NAME} \
    -o jsonpath='{$.secrets[0].name}') 

    kubectl get secret ${SECRET_NAME} \
    -o jsonpath='{$.data.token}' \
    | base64 --decode` 
    ```

    The output from the `kubectl` command will be a long string.

9. Copy the string from the previous step.  \
 \
Note: In some cases the string will not be copied in a format that can be pasted correctly in the next step. I suggest you paste the string into a text editor and ensure there are no line breaks – it needs to be one continuous string for the next step to work.  

10. Return to the Google Cloud console and click the name of your cluster. 

11. In the right-hand pane click **Login**.

12. Choose **Token** from the list of options. 

13. Paste the token string you previously copied into the text box. 

14. Click **Login**. 

The Google Cloud console should now indicate that the cluster is healthy. If you receive a login error, double-check that your string contains no line breaks. 


## Exploring Logging and Monitoring

Anthos on bare metal automatically creates three Google Cloud Operations (formerly Stackdrive) logging and monitoring dashboards when a cluster is provisioned: node status, pod status, and control plane status. These dashboards enable you to quickly gain visual insight into the health of your cluster. In addition to the three dashboards, you can use [Google Cloud Operations Metrics Explorer](https://cloud.google.com/monitoring/charts/metrics-explorer) to create custom queries for a wide variety of performance data points. 

To view the dashboards, return to the Google Cloud console. 

1. In the left-hand menu scroll down to **Operations**. Choose **Monitoring** and then choose **Dashboards.** 

2. You should see the three dashboards in the list in the middle of the screen. Choose each of the three dashboards and examine the available graphs. 

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
That’s it! You now know how to use Athos on bare metal to deploy a centrally managed Kubernetes cluster on your own hardware and keep track of it using the built-in logging and monitoring dashboards. 

As a next step, you may want to deploy your own application to the cluster or potentially deploy a more complex cluster architecture featuring both Anthos on bare metal admin and worker clusters. 