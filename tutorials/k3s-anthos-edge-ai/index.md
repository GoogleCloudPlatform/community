---
title: Edge AI with Anthos and K3S
description: Learn how to deploy cloud trained AI models to edge servers
author: kalschi
tags: AI, artificial intelligence, Edge AI, K3
date_published: 
---

Michael Chi | Cloud Solution Architect | Google

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates using Cloud Build to deploy inferencing models from Google Cloud Platform to edge servers running K3s.

In this turtorial, you learn how to trigger Cloud Build pipeline to build contianer images and leverage Anthos Configuration Management service to deploy it to an edge server running K3s. To simulate edge server, you create a GCE VM in GCP project.

This turtrial uses a popular [YOLOv5 sample](https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch) created by [mikel-brostrom](https://github.com/mikel-brostrom) as the workload to be deployed. 


## Objectives

- Create a GCE VM and setup K3s
- Enable and register newly created K3s to Anthos
- Setup Source Repo and push sample codes
- Setup Cloud Build Pipeline
- Setup Anthos ACM
- Update codes and trigger automated deployment

## Costs

This tutorial uses billable components of Google Cloud, including the following:
```
*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Scheduler](https://cloud.google.com/scheduler)
*   [App Engine](https://cloud.google.com/appengine/docs/flexible/python)
```
Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.


## Before you begin

This tutorial assumes that you have a billing enabled GCP account

-  Create an account with the free tier. See [document from Google](https://cloud.google.com/billing/docs/how-to/modify-project) for detailed instructions.


## Setup edge server

### Create GCE Instance

Run below command in Cloud Shell to create a GCE virtual machine in `us-central1-a` zone:
    

        export ZONE=us-central1-a

        gcloud compute instances create edge-server-k3s --project=$GOOGLE_CLOUD_PROJECT --zone=$ZONE \
            --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default \
            --scopes=https://www.googleapis.com/auth/cloud-platform \
            --create-disk=auto-delete=no,boot=yes,device-name=k3s,image=projects/debian-cloud/global/images/debian-10-buster-v20211105,size=100

Wait for the compute engine instance to be created and ssh to it.


### Install K3s

SSH to the newly creeated machine and follow the Rancher [instruction](https://rancher.com/docs/k3s/latest/en/installation/install-options/#options-for-installation-with-script) to install K3s on the newly created machine

        curl -sfL https://get.k3s.io | sh -

If everything goes well, you should see outputs stating K3s is starting.


```
[INFO]  systemd: Starting k3s
```

## Enable Anthos and register K3s cluster

### Enable Anthos and Anthos Config Management API

If not already, [install gcloud command-line tool](https://cloud.google.com/anthos/multicluster-management/connect/prerequisites#install-cloud-sdk) in the machine.

To enable Anthos API if not already, run below in cloud shell

    gcloud services enable anthos.googleapis.com
    gcloud services enable anthosconfigmanagement.googleapis.com

### Register attached K3s cluster to Anthos

Follow the [instruction](https://cloud.google.com/anthos/docs/setup/attached-clusters#register_your_cluster) to register K3s cluster to Anthos.

    export MEMBERSHIP_NAME=edge-server-k3s
    export KUBECONFIG_CONTEXT=$(sudo kubectl config current-context)
    export KUBECONFIG_PATH=/etc/rancher/k3s/k3s.yaml #Kubectl config file in K3s defaults to `/etc/rancher/k3s`

    sudo gcloud container hub memberships register $MEMBERSHIP_NAME \
    --context=$KUBECONFIG_CONTEXT \
    --kubeconfig=$KUBECONFIG_PATH \
    --enable-workload-identity \
    --has-private-issuer

Once registered, it appears in Anthos clusters console, however, to access to the registered cluster, you'll need to [log in and authenticate to the cluster](https://cloud.google.com/anthos/multicluster-management/console/logging-in). As the document recommended, we'll use Google Cloud Identity to login to the cluster.

### Setup Connect Gateway

Your platform admin must perform the necessary [setup](https://cloud.google.com/anthos/multicluster-management/gateway/setup) to let you use your Google Cloud identity to log in, including granting you all the necessary roles and RBAC permissions to view and authenticate to registered clusters.

Below operations requires `roles/owner` in your GCP project.

If you haven't done so, go to Cloud shell and enable API


    gcloud services enable --project=$GOOGLE_CLOUD_PROJECT  \
    connectgateway.googleapis.com \
    anthos.googleapis.com \
    gkeconnect.googleapis.com \
    gkehub.googleapis.com \
    cloudresourcemanager.googleapis.com


Now we want to grant required IAM roles to users so they can interact with connected cluster through the gateway.

    export MEMBER=user:your-user-name@your-domain.com
    export GATEWAY_ROLE=roles/gkehub.gatewayAdmin   # or `roles/gkehub.gatewayReader`

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role $GATEWAY_ROLE

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/gkehub.viewer

    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member $MEMBER \
    --role roles/container.viewer

Update required RBAC policies

- The impersonation policy that authorizes the Connect agent to send requests to the Kubernetes API server on behalf of a user.
Replace `your-user-name@your-domain.com` and `your-service-account@example-project.iam.gserviceaccount.com` with desired user accout and service account


cat <<EOF > /tmp/impersonate.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gateway-impersonate
rules:
- apiGroups:
  - ""
  resourceNames:
  - your-user-name@your-domain.com
  - your-service-account@example-project.iam.gserviceaccount.com
  resources:
  - users
  verbs:
  - impersonate
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-impersonate
roleRef:
  kind: ClusterRole
  name: gateway-impersonate
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: connect-agent-sa
  namespace: gke-connect
EOF
kubectl apply -f /tmp/impersonate.yaml


- The permissions policy that specifies which permissions the user has on the cluster.


cat <<EOF > /tmp/admin-permission.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-cluster-admin
subjects:
- kind: User
  name: your-user-name@your-domain.com
- kind: User
  name: your-service-account@example-project.iam.gserviceaccount.com
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF
# Apply permission policy to the cluster.
kubectl apply -f /tmp/admin-permission.yaml


Go to Anthos Cluster console, select the `edge-server-k3s` cluster then click `Login` button, when popup prompts, choose `Use your Google identity to log-in`


---
To begin creating a tutorial, copy the Markdown source for this tutorial template into your blank Markdown file. Replace the explanatory text and examples with 
your own tutorial content. Not all documents will use all of the sections described in this template. For example, a conceptual document or code walkthrough
might not include the "Costs" or "Cleaning up" sections. For more information, see the 
[style guide](https://cloud.google.com/community/tutorials/styleguide) and [contribution guide](https://cloud.google.com/community/tutorials/write).

Replace the placeholders in the metadata at the top of the Markdown file with your own values. Follow the guidance provided by the placeholder values for spacing
and punctuation.

The first line after the metadata should be your name and an optional job description and organization affiliation.

After that is one of two banners that indicates whether the document was contributed by a Google employee. Just leave one banner and delete the other one.

The first paragraph or two of the tutorial should tell the reader the following:

  * Who the tutorial is for
  * What they will learn from the tutorial
  * What prerequisite knowledge they need for the tutorial

Don't use a heading like **Overview** or **Introduction**. Just get right to it.

## Objectives

Give the reader a high-level summary of what steps they take during the tutorial. This information is often most effective as a short bulleted list.

### Example: Objectives

*   Create a service account with limited access.
*   Create a Cloud Function that triggers on HTTP.
*   Create a Cloud Scheduler job that targets an HTTP endpoint.
*   Run the Cloud Scheduler job. 
*   Verify success of the job.

## Costs

Tell the reader which technologies the tutorial uses and what it costs to use them.

For Google Cloud services, link to the preconfigured [pricing calculator](https://cloud.google.com/products/calculator/) if possible.

If there are no costs to be incurred, state that.

### Example: Costs 

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Scheduler](https://cloud.google.com/scheduler)
*   [App Engine](https://cloud.google.com/appengine/docs/flexible/python)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

Give a numbered sequence of procedural steps that the reader must take to set up their environment before getting into the main tutorial.

Don't assume anything about the reader's environment. You can include simple installation instructions of only a few steps, but provide links to installation
instructions for anything more complex.

### Example: Before you begin

This tutorial assumes that you're using the Microsoft Windows operating system.

1.  Create an account with the BigQuery free tier. See
    [this video from Google](https://www.youtube.com/watch?v=w4mzE--sprY&list=PLIivdWyY5sqI6Jd0SbqviEgoA853EvDsq&index=2) for detailed instructions.
1.  Create a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/).
1.  Install [DBeaver Community for Windows](https://dbeaver.io/download/).

## Tutorial body

Break the tutorial body into as many sections and subsections as needed, with concise headings.

### Use short numbered lists for procedures

Use numbered lists of steps for procedures. Each action that the reader must take should be its own step. Start each step with the action, such as *Click*, 
*Run*, or *Enter*.

Keep procedures to 7 steps or less, if possible. If a procedure is longer than 7 steps, consider how it might be separated into sub-procedures, each in its
own subsection.

### Provide context, but don't overdo the screenshots

Provide context and explain what's going on.

Use screenshots only when they help the reader. Don't provide a screenshot for every step.

Help the reader to recognize what success looks like along the way. For example, describing the result of a step helps the reader to feel like they're doing
it right and helps them know things are working so far.

## Cleaning up

Tell the reader how to shut down what they built to avoid incurring further costs.

### Example: Cleaning up

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

Tell the reader what they should read or watch next if they're interested in learning more.

### Example: What's next

- Watch this tutorial's [Google Cloud Level Up episode on YouTube](https://youtu.be/uBzp5xGSZ6o).
- Learn more about [AI on Google Cloud](https://cloud.google.com/solutions/ai/).
- Learn more about [Cloud developer tools](https://cloud.google.com/products/tools).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).