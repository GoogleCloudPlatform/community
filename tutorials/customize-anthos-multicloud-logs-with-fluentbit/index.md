---
title: Customizing Fluent Bit for Anthos Multi-Cloud
description: Learn how to customize Cloud Logging logs with Fluent Bit for
Anthos on AWS and Azure
author: amandawestlake
tags: logging, stackdriver, gke, fluent-bit
date_published: 2021-07-26
---

Amanda Westlake | Technical Writer Intern | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to use [Fluent Bit](https://fluentbit.io/)
to customize your Cloud Logging logs for an Anthos on AWS/Azure cluster.
In this tutorial, you learn how to host your own configurable Fluent Bit
daemonset to send logs to Cloud Logging, instead of selecting the Cloud
Logging option when creating the cluster, which does not allow configuration of
the Fluent Bit daemon.

Unlike user logs, Fluent Bit allows you to customize
logs. Fluent Bit can also be used with specific applications or namespaces, as opposed
user logs which can only be used with all applications running on a cluster. 

This tutorial applies to Linux nodes only.

Unless otherwise noted, you enter all commands for this tutorial in Cloud Shell.

## Objectives 

+   Deploy your own Fluent Bit daemonset on an Anthos on AWS/Azure cluster,
    configured to log data to [Cloud Logging](https://cloud.google.com/logging).
+   Customize GKE logging to remove sensitive data from the Cloud Logging logs.

## Costs


## Before you begin

1.  Create an Anthos on AWS/Azure cluster with user logs turned off.

## Setup

In this section, you define variables that control where elements of the infrastructure are deployed.

1.  [Open Cloud Shell](https://console.cloud.google.com/?cloudshell=true).

1.  Set the variables used by this tutorial:

        export region=us-east1
        export zone=${region}-b
        export project_id=[YOUR_PROJECT_ID]
        
    This tutorial uses the region `us-east-1`. If you change the region,
    make sure that the zone values reference your region.

1.  Set the default zone and project ID so that you don't have to specify these
    values in every subsequent command:

        gcloud config set compute/zone ${zone}
        gcloud config set project ${project_id}

1.  Clone the sample Git repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

    This sample repository includes manifest files that will create the following:

    * A `test-logger` sample application
    * A Fluent Bit DaemonSet

1.  Go to the directory for this tutorial in the cloned repository:

        cd community/tutorials/kubernetes-engine-customize-fluentbit
    
    Stay in this directory for the duration of the tutorial.    

## Prepare and deploy the test logger application

Deploy the `test-logger` sample application, which is built from the source
code in the `test-logger` subdirectory. By default, this application
continuously emits random logging statements.

In this tutorial, you
[Use a private image registry](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to-private-registry)
and store your container image in Artifact Registry. You upload the container image to
a registry so that your Anthos on AWS/Azure cluster can access it.
Then, you deploy the application to your cluster.


### Prepare the test-logger application

To prepare the test logger sample application, complete the following.

1.  Build the `test-logger` container image:

        docker build -t test-logger test-logger

1.  Create a repository named `test-logger-repo` in Artifact Registry:

        gcloud artifacts repositories create test-logger-repo \
                --repository-format=docker \
                --location=[REGION] \
                --description="Docker repository"

    Replace [REGION] with the Google Cloud region you want to create
    your repository in.

1.  Tag the container before pushing it to the registry:

        docker tag test-logger [REGION]-docker.pkg.dev/${project_id}/test-logger-repo/test-logger:v1

    Replace [REGION].

1.  Configure the Docker command-line tool to authenticate to
    Artifact Registry.

        gcloud auth configure-docker [REGION]-docker.pkg.dev

    Replace [REGION].

1.  Push the container image:

        docker push [REGION]-docker.pkg.dev/${project_id}/test-logger/test-logger:v1

        Replace [REGION].

1.  Update the deployment file using the `envsubst` command. This will add the
    `PROJECT_ID` variable you set earlier to a
    `test-logger-deploy.yaml` configuration file:


        envsubst < kubernetes/test-logger.yaml > kubernetes/test-logger-deploy.yaml

1.  Add your service account key secret, which you created above, to end of the
    `kubernetes/test-logger-deploy.yaml` deployment file underneath the
    `spec:` subheading. The indentation should be equal to the `containers:` line. 

    Add the following text to the manifest file:

        imagePullSecrets:
         - name: {{"<var>SECRET_NAME</var>"}}

    Replace `{{"<var>SECRET_NAME</var>"}}` with the name of your service 
    account key secret.

     The file should now contain the following:

        spec:
        containers:
            - name: test-logger
            image: gcr.io/awestlake/test-logger
        imagePullSecrets:
         - name: gcr-secret 

### Deploy the test logger application

To deploy the sample application and check that it is working, 
complete the following.

1.  Deploy the `test-logger` application:

        kubectl apply -f kubernetes/test-logger-deploy.yaml

1.  View the status of the `test-logger` pods:

        kubectl get pods

1.  Repeat this command until the output looks like the following, with all three `test-logger` pods running:

        NAME                           READY   STATUS    RESTARTS   AGE
        test-logger-58f7bfdb89-4d2b5   1/1     Running   0          28s
        test-logger-58f7bfdb89-qrlbl   1/1     Running   0          28s
        test-logger-58f7bfdb89-xfrkx   1/1     Running   0          28s

## Deploy the Fluent Bit daemonset to your cluster

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

1.  Verify that you're seeing logs in Cloud Logging. In the
    [Google Cloud console](http://console.cloud.google.com), on the left-hand
    side, scroll down to the **Operations** subheading and select
    **Logging** > **Logs Explorer**. On this page, click the **Resource**
    list dropdown menu to the right of the search bar, then select
    **Kubernetes Container** as a resource type.
    
1.  Select **Run Query**, a button on the top right.

1.  In the **Logs field explorer**, select **test-logger** for **CONTAINER_NAME**. After you add the `log` field to the summary line, you should see logs similar
    to the following:

    ![fluentbit-filter-before](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-before.png)

## Filter information from the log file

In this section, you configure Fluent Bit to filter certain data so that it is not logged. For this tutorial, you filter out Social Security numbers, credit
card numbers, and email addresses. To make this update, you change the daemonset to use a different ConfigMap that contains these filters. You use Kubernetes
rolling updates feature and preserve the old version of the ConfigMap.

1.  Open the
    [`kubernetes/fluentbit-configmap.yaml`](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/kubernetes-engine-customize-fluentbit/kubernetes/fluentbit-configmap.yaml) file in an editor.
1.  Uncomment the lines after `### sample log scrubbing filters` and before `### end sample log scrubbing filters`.
1.  Change the name of the ConfigMap from `fluent-bit-config` to `fluent-bit-config-filtered` by editing the `metadata.name` field.
1.  Save and close the file.

## Update the Fluent Bit daemonset to use the new configuration

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

    When it completes, you should see the follwoing message:

        daemon set "fluent-bit" successfully rolled out

1.  When the rollout is complete, refresh the Cloud Logging logs and make sure
    that the Social Security number, credit card number, and email address data
    has been filtered out.

    ![fluentbit-filter-after](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-after.png)

## Clean up

After you've finished the tutorial, clean up the resources you created
on {{product_name_short}} so you won't be billed for them in the future.

1. Delete the Fluent Bit DaemonSet:

      kubectl delete -f kubernetes/fluentbit-daemonset.yaml


1. Delete the Fluentd configuration:

      kubectl delete -f kubernetes/fluentd-configmap.yaml


1. Delete the `test-logger` application:


      kubectl delete -f test-logger-deploy.yaml


## What's next