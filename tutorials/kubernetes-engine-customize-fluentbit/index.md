---
title: Customizing Fluent Bit for Google Kubernetes Engine logs 
description: Learn how to customize Fluent Bit for Google Kubernetes Engine logs.
author: xiangshen-dk
tags: logging, stackdriver, gke, fluent-bit
date_published: 2020-11-25
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to customize [Fluent Bit](https://fluentbit.io/) logging for a [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)
cluster. In this tutorial, you learn how to host your own configurable Fluent Bit daemonset to send logs to Cloud Logging, instead of selecting the Cloud Logging
option when creating the Google Kubernetes Engine (GKE) cluster, which does not allow configuration of the Fluent Bit daemon.

This tutorial assumes that you're familiar with [Kubernetes](https://kubernetes.io/docs/home/).

This tutorial applies to Linux nodes only.

Unless otherwise noted, you enter all commands for this tutorial in Cloud Shell.

## Objectives 

+   Deploy your own Fluent Bit daemonset on a Google Kubernetes Engine cluster, configured to log data to [Cloud Logging](https://cloud.google.com/logging).
+   Customize GKE logging to remove sensitive data from the Cloud Logging logs.

## Costs

This tutorial uses billable components of Google Cloud, including a three-node [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/pricing) 
cluster.

The [pricing calculator](https://cloud.google.com/products/calculator#id=38ec76f1-971f-41b5-8aec-a04e732129cc) estimates the cost of this environment at around 
$1.14 for 8 hours.

## Before you begin

1.  In the Cloud Console, on the [project selector page](https://console.cloud.google.com/projectselector2/home/dashboard), select or create a Cloud project.  

    **Note**: If you don't plan to keep the resources that you create in this procedure, create a project instead of selecting an existing project. After you 
    finish this tutorial, you can delete the project, removing all resources associated with the project.  

1.  Make sure that billing is enabled for your Google Cloud project.

    [Learn how to confirm whether billing is enabled for your project.](https://cloud.google.com/billing/docs/how-to/modify-project)
    
1.  Enable the Google Kubernetes Engine and Compute Engine APIs.

    [Enable the APIs.](https://console.cloud.google.com/flows/enableapi?apiid=container,compute.googleapis.com)

## Initializing common variables

In this section, you define variables that control where elements of the infrastructure are deployed.

1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

1.  Set the variables used by this tutorial:

        export region=us-east1
        export zone=${region}-b
        export project_id=[YOUR_PROJECT_ID]
        
    This tutorial uses the region `us-east-1`. If you change the region, make sure that the zone values reference your region.

1.  Set the default zone and project ID so that you don't have to specify these values in every subsequent command:

        gcloud config set compute/zone ${zone}
        gcloud config set project ${project_id}

## Creating the GKE cluster

1.  Clone the sample repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

    The sample repository includes the Kubernetes manifests for the Fluent Bit daemonset and a test logging program that you deploy.

1.  Go to the directory for this tutorial in the cloned repository:

        cd community/tutorials/kubernetes-engine-customize-fluentbit

1.  Create the GKE cluster with system-only logging turned on:

        gcloud container clusters create custom-fluentbit \
        --zone $zone \
        --logging=SYSTEM \
        --tags=gke-cluster-with-customized-fluentbit \
        --scopes=logging-write,storage-rw

## Deploying the test logger application

By default, the sample application that you deploy continuously emits random logging statements. The Docker container is
built from the source code under the `test-logger` subdirectory.

1.  Build the `test-logger` container image:

        docker build -t test-logger test-logger

1.  Tag the container before pushing to the registry:

        docker tag test-logger gcr.io/${project_id}/test-logger

1.  Push the container image:

        docker push gcr.io/${project_id}/test-logger

1.  Update the deployment file:

        envsubst < kubernetes/test-logger.yaml > kubernetes/test-logger-deploy.yaml

1.  Deploy the `test-logger` application to the GKE cluster:

        kubectl apply -f kubernetes/test-logger-deploy.yaml

1.  View the status of the `test-logger` pods:

        kubectl get pods

1.  Repeat this command until the output looks like the following, with all three `test-logger` pods running:

        NAME                           READY   STATUS    RESTARTS   AGE
        test-logger-58f7bfdb89-4d2b5   1/1     Running   0          28s
        test-logger-58f7bfdb89-qrlbl   1/1     Running   0          28s
        test-logger-58f7bfdb89-xfrkx   1/1     Running   0          28s

## Deploying the Fluent Bit daemonset to your cluster

In this section, you configure and deploy your Fluent Bit daemonset.

Because you turned on system-only logging, a GKE-managed Fluentd daemonset is deployed that is responsible for system logging. The Kubernetes manifests for 
Fluent Bit that you deploy in this procedure are versions of the ones available from the Fluent Bit site for
[logging using Cloud Logging](https://docs.fluentbit.io/manual/installation/kubernetes/) and
[watching changes to Docker log files](https://kubernetes.io/docs/concepts/cluster-administration/logging/).

1.  Create the service account and the cluster role in a new `logging` namespace:

        kubectl apply -f ./kubernetes/fluentbit-rbac.yaml

1.  Deploy the Fluent Bit configuration:

        kubectl apply -f kubernetes/fluentbit-configmap.yaml

1.  Deploy the Fluent Bit daemonset:

        kubectl apply -f kubernetes/fluentbit-daemonset.yaml

1.  Check that the Fluent Bit pods have started:

        kubectl get pods --namespace=logging

1.  If they're running, you see output like the following:

        NAME               READY   STATUS    RESTARTS   AGE
        fluent-bit-246wz   1/1     Running   0          26s
        fluent-bit-6h6ww   1/1     Running   0          26s
        fluent-bit-zpp8q   1/1     Running   0          26s

    For details of configuring Fluent Bit for Kubernetes, see the [Fluent Bit manual]( https://docs.fluentbit.io/manual/installation/kubernetes).  

1.  Verify that you're seeing logs in Cloud Logging. In the console, on the left-hand side, select **Logging** > **Logs Explorer**, and then select
    **Kubernetes Container** as a resource type in the **Resource** list.
    
1.  Click **Run Query**.

1.  In the **Logs field explorer**, select **test-logger** for **CONTAINER_NAME**. After you add the `log` field to the summary line, you should see logs similar
    to the following:

    ![fluentbit-filter-before](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-before.png)

## Filtering information from the log file

In this section, you configure Fluent Bit to filter certain data so that it is not logged. For this tutorial, you filter out Social Security numbers, credit
card numbers, and email addresses. To make this update, you change the daemonset to use a different ConfigMap that contains these filters. You use Kubernetes
rolling updates feature and preserve the old version of the ConfigMap.

1.  Open the
    [`kubernetes/fluentbit-configmap.yaml`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/kubernetes-engine-customize-fluentbit/kubernetes/fluentbit-configmap.yaml) file in an editor.
1.  Uncomment the lines after `### sample log scrubbing filters` and before `### end sample log scrubbing filters`.
1.  Change the name of the ConfigMap from `fluent-bit-config` to `fluent-bit-config-filtered` by editing the `metadata.name` field.
1.  Save and close the file.

## Updating the Fluent Bit daemonset to use the new configuration

In this section, you change `kubernetes/fluentbit-daemonset.yaml` to mount the `fluent-bit-config-filtered` ConfigMap instead of the
`fluent-bit-config` ConfigMap.

1.  Open the
    [`kubernetes/fluentbit-daemonset.yaml`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/kubernetes-engine-customize-fluentbit/kubernetes/fluentbit-daemonset.yaml) file in an editor.
1.  Change the name of the ConfigMap from `fluent-bit-config` to `fluent-bit-config-filtered` by editing the `configMap.name` field:

        - name: fluent-bit-etc
        configMap:
            name: fluent-bit-config

1.  Deploy the new version of the ConfigMap to your cluster:

        kubectl apply -f kubernetes/fluentbit-configmap.yaml

1.  Roll out the new version of the daemonset:
        
        kubectl apply -f kubernetes/fluentbit-daemonset.yaml

1.  Roll out the update and wait for it to complete:

        kubectl rollout status ds/fluent-bit --namespace=logging

    When it completes, you should see the following message:

        daemon set "fluent-bit" successfully rolled out

1.  When the rollout is complete, refresh the Cloud Logging logs and make sure that the Social Security number, credit card number, and email address data has 
    been filtered out.

    ![fluentbit-filter-after](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-after.png)

## Cleaning up: deleting the GKE cluster

If you don't want to delete the whole project, run the following command to delete the GKE cluster:

    gcloud container clusters delete custom-fluentbit --zone us-east1-b

## What's next

+   Review [Fluent Bit](https://docs.fluentbit.io/manual/) documentation in more detail.
+   Review [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine) documentation in more detail.
+   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
