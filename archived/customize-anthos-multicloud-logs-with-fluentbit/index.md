---
title: Customize Anthos Multi-Cloud logs with Fluent Bit
description: Learn how to customize Cloud Logging logs with Fluent Bit for Anthos on AWS and Azure.
author: amandawestlake
tags: logging, stackdriver, gke, fluent-bit, cloud logging, Anthos on AWS, Anthos on Azure
date_published: 2022-08-19
---

Amanda Westlake | Technical Writer | Google
<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to use [Fluent Bit](https://fluentbit.io/)
to customize your Cloud Logging logs for an
[Anthos Multi-Cloud](https://cloud.google.com/anthos/clusters/docs/multi-cloud)
cluster. In this document, you learn how to host your own configurable Fluent
Bit DaemonSet to send logs to [Cloud Logging](http://cloud.google.com/logging)
instead of using default workload logs.

Unlike default workload logs, Fluent Bit allows you to customize your logs.
Fluent Bit can also be used with specific workloads and namespaces, as opposed
to workload logs, which can only be used with all applications running on a
cluster. 

This tutorial applies to Linux nodes only.

## Objectives 

* Deploy a Fluent Bit DaemonSet on an Anthos Multi-Cloud cluster.
* Use the Fluent Bit DaemonSet to remove sensitive data from
  Cloud Logging logs.

## Costs

This tutorial uses billable components of Google Cloud.

You will be charged for the following:

* Your Anthos Multi-Cloud cluster
* Storage in Artifact Registry
* Cloud Logging

See [Cloud Logging pricing](https://cloud.google.com/stackdriver/pricing)
for more information.

## Before you begin

1.  [Create a cluster](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/create-cluster)
    with Anthos on AWS or
    [Create a cluster](https://cloud.google.com/anthos/clusters/docs/multi-cloud/azure/how-to/create-cluster)
    with Anthos on Azure.

1.  [Authorize Cloud Logging / Cloud Monitoring](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/create-cluster#telemetry-agent-auth)
    for your cluster.

1.  [Configure and authenticate Docker](https://cloud.google.com/container-registry/docs/advanced-authentication#gcloud-helper).

1.  To authenticate to Artifact Registry, [create a service account](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/private-registry#create_a_service_account) 
    and
    [save the key to your cluster](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/private-registry#save_the_key_to_your_cluster)
    as a Kubernetes secret.

    Make a note of the name of your service account key secret. You'll
    need it later.

## Setup

To set up your environment, do the following:

1.  Clone the [sample repository](https://github.com/GoogleCloudPlatform/anthos-samples.git):

        git clone https://github.com/GoogleCloudPlatform/anthos-samples.git

    This sample repository includes manifest files that will create the following:
 
    * A `test-logger` sample application
    * A Fluent Bit DaemonSet

1.  Go to the correct directory in the cloned repository:

        cd anthos-samples/anthos-multi-cloud/customize-logs-fluentbit
    
    Stay in this directory for the duration of the tutorial.

1.  Set the environment variables used by this tutorial:

        export REGION=[REGION]
        export PROJECT_ID=[PROJECT_ID]
        export PROJECT_NUMBER=[PROJECT_NUMBER]
        export CLUSTER_NAME=[CLUSTER_NAME]
        export CLUSTER_TYPE=[CLUSTER_TYPE]
        export SECRET_NAME=[SECRET_NAME]
    
    Replace the following:
    * `REGION`, the Google Cloud region your cluster is located in
    * `PROJECT_ID`, the ID of your Google Cloud project
    * `PROJECT_NUMBER`, the numerical unique identifier associated with your
       Google Cloud project
    * `CLUSTER_NAME`, the name of your Anthos Multi-Cloud cluster
    * `CLUSTER_TYPE`, either `awsClusters` or `azureClusters`
    * `SECRET_NAME`, the Kubernetes secret that contains the service account
      key you created above

## Update your cluster to turn Cloud Logging user logs off

Update your cluster so it uses only system logs and not workload logs. Disabling
workload logs means that you will not produce two sets of logs when using
the Fluent Bit DaemonSet.

1.  To turn off workload logs on your cluster, run the following command:

        gcloud alpha container [CLUSTER_CLOUD] clusters update [CLUSTER_NAME] \
            --location=[REGION] --logging=SYSTEM
    
    Replace the following:
    * `CLUSTER_CLOUD`, the cloud your cluster runs in, either `aws` or `azure`
    * `CLUSTER_NAME`, the name of your Anthos Multi-Cloud cluster
    * `REGION`, the Google Cloud region your cluster is located in

## Prepare and deploy the test logger application

Deploy the `test-logger` sample application, which is built from the source
code in the `test-logger` subdirectory. By default, this application
continuously emits random logging statements. The Fluent Bit Daemonset
you deploy later customizes these logs.

In this tutorial, you
[use a private image registry](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/private-registry)
and store your container image in Artifact Registry. Then, you deploy the
application to your cluster.

### Prepare the test logger application

To prepare the test logger sample application, do the following:

1.  Build the `test-logger` container image:

        docker build -t test-logger test-logger

1.  Configure the Docker command-line tool to authenticate to
    Artifact Registry.

        gcloud auth configure-docker [REGION]-docker.pkg.dev

    Replace `[REGION]` with the Google Cloud region you want to create
    your repository in.

1.  Create a repository named `test-logger-repo` in Artifact Registry:

        gcloud artifacts repositories create test-logger-repo \
                --repository-format=docker \
                --location=[REGION] \
                --description="Docker repository"

    Replace `[REGION]`.

    To see a list of available locations, run the following command:

        gcloud artifacts locations list

1.  Tag the container image:

        docker tag test-logger [REGION]-docker.pkg.dev/${PROJECT_ID}/test-logger-repo/test-logger:v1

    Replace `[REGION]`.

1.  Push the container image to the registry:

        docker push [REGION]-docker.pkg.dev/${PROJECT_ID}/test-logger-repo/test-logger:v1

    Replace `[REGION]`.

1.  Update the deployment file using the `envsubst` command. This adds the
    variables you set earlier to a `test-logger-deploy.yaml` configuration
    file:

        envsubst < kubernetes/test-logger.yaml > kubernetes/test-logger-deploy.yaml

    If you created your Artifact Registry repository in a different region than
    your cluster, change the region in the `test-logger-deploy.yaml` file to match.

### Deploy the test logger application

To deploy the sample application and check that it is working, 
do the following:

1.  Deploy the `test-logger` sample application:

        kubectl apply -f kubernetes/test-logger-deploy.yaml

1.  View the status of the `test-logger` pods:

        kubectl get pods

1.  Repeat this command until the output looks like the following, with all
    three `test-logger` pods running:

        NAME                           READY   STATUS    RESTARTS   AGE
        test-logger-58f7bfdb89-4d2b5   1/1     Running   0          28s
        test-logger-58f7bfdb89-qrlbl   1/1     Running   0          28s
        test-logger-58f7bfdb89-xfrkx   1/1     Running   0          28s

## Deploy the Fluent Bit DaemonSet to your cluster

In this section, you configure and deploy your Fluent Bit DaemonSet.

The Kubernetes manifests for Fluent Bit that you deploy in this procedure are
versions of the ones available from the Fluent Bit site for
[logging using Cloud Logging](https://docs.fluentbit.io/manual/installation/kubernetes/)
and
[watching changes to Docker log files](https://kubernetes.io/docs/concepts/cluster-administration/logging/).

### Prepare and deploy the FluentBit ConfigMap and Daemonset

To deploy the Fluent Bit ConfigMap and DaemonSet, do the following:

1.  Create a namespace called `logging-system`, a service account, and a
    cluster role:

        kubectl apply -f ./kubernetes/fluentbit-rbac.yaml

1.  Take the proxy-config Kubernetes secret from the built-in
    `gke-system` namespace, and apply it to the `logging-system` namespace:

        kubectl get secret proxy-config --namespace=gke-system -o yaml \
            | sed 's/namespace: .*/namespace: logging-system/' | kubectl apply -f -

1.  Replace variables in the `kubernetes/fluentbit-configmap.yaml` and
    `kubernetes/fluentbit-daemonset.yaml` files with the environment variables you
    set above.

        envsubst < kubernetes/fluentbit-configmap.yaml > kubernetes/fluentbit-configmap-deploy.yaml
        envsubst < kubernetes/fluentbit-daemonset.yaml > kubernetes/fluentbit-daemonset-deploy.yaml

    If your cluster is not running in the United States, change the `us`
    in `us.gcr.io/gke-multi-cloud-release/gke-addon-sidecar:gke_multicloud.gke_multicloud_images_20220317_1445_RC00`
    to `asia` or `eu` to match your cluster's region.

1.  Deploy the Fluent Bit configuration:

        kubectl apply -f kubernetes/fluentbit-configmap-deploy.yaml

1.  Deploy the Fluent Bit DaemonSet:

        kubectl apply -f kubernetes/fluentbit-daemonset-deploy.yaml


### Confirm that the DaemonSet has been deployed correctly

To confirm that your FluentBit ConfigMap and DaemonSet are working correctly
and sending logs to Cloud Logging, do the following:

1.  View the status of the Fluent Bit pods:

        kubectl get pods --namespace=logging-system

1.  Repeat this command until the output looks like the following, with two
   `fluent-bit-user` pods running:

        NAME                   READY   STATUS    RESTARTS   AGE
        fluentbit-user-4fv84   2/2     Running   0          16s
        fluentbit-user-xt6hq   2/2     Running   0          16s

1.  In the Cloud console, go to the [Logs Explorer page](https://console.cloud.google.com/logs/query).

1.  Click **Resource** to the right of the search bar, and select
    **Kubernetes Container** as a resource type.
    
1.  Select **Run Query**, a button on the top right.

1.  In the **Logs field explorer**, select **test-logger** for **CONTAINER_NAME**.
    You should see logs similar to the following:

    ![fluentbit-filter-before](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-before.png)

    The Fluent Bit DaemonSet is deployed.

## Filter information from the log file

In this section, you configure Fluent Bit to filter certain data so that it is
not logged. For this tutorial, you filter out Social Security numbers, credit
card numbers, and email addresses. To do this, you change the DaemonSet
to use a different ConfigMap that contains these filters. You use the Kubernetes
rolling updates feature and preserve the old version of the ConfigMap.

1.  Open the `kubernetes/fluentbit-configmap-deploy.yaml` file in an editor.

1.  Uncomment the lines after `### Sample log scrubbing filters` and before
    `### End sample log scrubbing filters`.

1.  Change the name of the ConfigMap from `fluentbit-user-config` to
    `fluentbit-user-config-filtered` by editing the `metadata.name` field.

    Edit the portion of the file above so it looks like this:

        name: fluentbit-user-config-filtered
        namespace: logging-system
        labels:
          k8s-app: fluentbit-user

1.  Save and close the file.

## Update the Fluent Bit DaemonSet to use the new configuration

In this section, you change the `kubernetes/fluentbit-daemonset-deploy.yaml` file to mount
the `fluentbit-user-config-filtered` ConfigMap instead of the
`fluentbit-user-config` ConfigMap.

1.  Open the `kubernetes/fluentbit-daemonset-deploy.yaml` file in an editor.

1.  Change the name of the ConfigMap from `fluentbit-user-config` to
    `fluentbit-user-config-filtered` by editing the `configMap.name` field so
    it looks like this:

        - name: fluentbit-user-config-filtered
        configMap:
            name: fluentbit-user-config-filtered

1.  Change the name of the `fluentbit-user-config` volumeMount to 
    `fluentbit-user-config-filtered`. It should look like this:

        - name: fluentbit-user-config-filtered
        mountPath: /fluent-bit/etc/

1.  Deploy the new version of the ConfigMap to your cluster:

        kubectl apply -f kubernetes/fluentbit-configmap-deploy.yaml

1.  Roll out the new version of the DaemonSet:
        
        kubectl apply -f kubernetes/fluentbit-daemonset-deploy.yaml

1.  Roll out the update and wait for it to complete:

        kubectl rollout status ds/fluentbit-user --namespace=logging-system

    When it completes, you should see the following message:

        daemon set "fluentbit-user" successfully rolled out

1.  When the rollout is complete, refresh the Cloud Logging logs and make sure
    that the Social Security number, credit card number, and email address data
    has been filtered out.

    ![fluentbit-filter-after](https://storage.googleapis.com/gcp-community/tutorials/kubernetes-engine-customize-fluentbit/fluentbit-filter-after.png)

    You have now used the Fluent Bit DaemonSet to customize your Cloud Logging
    logs.

## Clean up

After you've finished the tutorial, clean up the resources you created
so you won't be billed for them in the future.

1. Delete the Fluent Bit DaemonSet:

        kubectl delete -f kubernetes/fluentbit-daemonset-deploy.yaml

1. Delete the Fluent Bit configuration:

        kubectl delete -f kubernetes/fluentbit-configmap-deploy.yaml

1. Delete the namespace, service account, and cluster role:

        kubectl delete -f kubernetes/fluentbit-rbac.yaml

1. Delete the `test-logger` application:

        kubectl delete -f kubernetes/test-logger-deploy.yaml

## What's next

* For more information about configuring Fluent Bit for Kubernetes, see the
  [Fluent Bit manual]( https://docs.fluentbit.io/manual/installation/kubernetes).
* Read about [Cloud Logging](https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/cloud-logging)
  with Anthos Multi-Cloud.
