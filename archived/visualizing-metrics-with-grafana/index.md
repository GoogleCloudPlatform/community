---
title: Visualize Google Kubernetes Engine and Istio metrics with Grafana
description: Deploy a sample application and Grafana on a GKE cluster and configure Cloud Monitoring as a backend for Grafana to create dashboards displaying key observability details about the cluster and application running on it.
author: yuriatgoogle
tags: stackdriver, gke, monitoring, charts, dashboards
date_published: 2019-09-27
---

Yuri Grinshteyn | Site Reliability Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Cloud Monitoring is a full-featured operations and observability toolkit that includes capabilities specifically targeted at 
Kubernetes operators, including a rich set of [features](https://cloud.google.com/monitoring/kubernetes-engine/) for 
Kubernetes observability. However, users with experience in this area tend to have familiarity with the open-source 
observability toolkit that includes the [ELK stack](https://www.elastic.co/what-is/elk-stack) and
[Prometheus](https://prometheus.io) and often prefer to use [Grafana](https://grafana.com) as their visualization layer.

In this tutorial, you learn how to how to install Grafana using Helm templates, deploy a sample application on a GKE 
cluster, and configure Cloud Monitoring as a backend for Grafana to create dashboards displaying key observability details about
the cluster and application running on it. At the end of the tutorial, you will have a fully functional monitoring system 
that will scale with your needs and can be further customized to evolve with your monitoring requirements.

The sample application is provided [here](https://github.com/GoogleCloudPlatform/microservices-demo).

The architecture you deploy in this tutorial is as follows:

![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/1-architecture.png)

## Costs

This tutorial uses billable components of Google Cloud, including the following:

-   Google Kubernetes Engine
-   Cloud Monitoring

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your 
projected usage.

## Before you begin

1.  Select or create a Google Cloud project on the
    [**Manage resources** page](https://console.cloud.google.com/cloud-resource-manager).

1.  If you didn't select a billing account during project creation, enable billing for your project.

    For information about enabling billing, see [this page](https://support.google.com/cloud/answer/6293499#enable-billing).

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. See the "Cleaning
up" section at the end of this tutorial for details.

## Set up your environment

In this section, you set up your environment with the tools that you use throughout this tutorial. You run all of the 
terminal commands in this tutorial from Cloud Shell.

1.  [Open Cloud Shell](https://console.cloud.google.com?cloudshell=true).

1.  Set environment variables:

        export PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)

1.  Enable the relevant APIs:

        gcloud services enable \
        cloudshell.googleapis.com \
        cloudbuild.googleapis.com \
        containerregistry.googleapis.com \
        container.googleapis.com \
        cloudtrace.googleapis.com

1.  Run the following commands to download the files for this tutorial and set up your working directory:

        cd $HOME
        git clone https://github.com/GoogleCloudPlatform/microservices-demo
        cd $HOME/microservices-demo
        WORKDIR=$(pwd)

     These commands clone the sample application repository and make the repository folder your working directory. You
     perform all of the tutorial tasks in the working directory, which you can delete when finished.
     
1. Install Istio 1.6 and Istio custom resource definitions:

        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.6.1 sh -
        cd istio-1.6.1
        export PATH=$PWD/bin:$PATH
        istioctl install --set profile=demo

### Install tools

Install [kubectx and kubens](https://github.com/ahmetb/kubectx), which make it easier to work with multiple Kubernetes 
clusters, contexts, and namespaces:

    git clone https://github.com/ahmetb/kubectx $WORKDIR/kubectx
    export PATH=$PATH:$WORKDIR/kubectx

## Deploy application on GKE cluster

In this section, you create a GKE cluster with the Istio on GKE add-on and Cloud Monitoring, and you deploy the sample 
application on the cluster.

1.  In Cloud Shell, set the environment variables to be used for cluster creation:

        #cluster name
        export CLUSTER=monitoring-cluster

        #zone for the cluster
        export ZONE=us-central1-a

        #namespace for the application
        export APP_NS=hipstershop

        #namespace for Grafana
        export MONITORING_NS=grafana

2.  Create the GKE cluster:

        gcloud beta container clusters create $CLUSTER \
        --zone=$ZONE \
        --num-nodes=6 \
        --cluster-version=latest \
        --enable-stackdriver-kubernetes \
        --addons=Istio \
        --istio-config=auth=MTLS_PERMISSIVE

    You are using the `PERMISSIVE` setting for MTLS configuration for the sake of simplicity. Review the
    [Istio documentation](https://istio.io/docs/concepts/security/#mutual-tls-authentication) to choose the appropriate 
    policy for your deployment.

3.  Get cluster credentials:

        gcloud container clusters get-credentials $CLUSTER --zone=$ZONE

4.  Set the context for `kubectx` and switch to it:

        kubectx cluster=gke_${PROJECT_ID}_${ZONE}_${CLUSTER}
        kubectx cluster

5.  Create a dedicated namespace for your application and switch to it:

        kubectl create namespace $APP_NS
        kubens $APP_NS

6.  Label the namespace to enable automatic Istio sidecar injection:

        kubectl label namespace $APP_NS istio-injection=enabled

7.  Apply the Istio manifests:

        kubectl apply -f $WORKDIR/istio-manifests

8.  Deploy the sample application:

        kubectl apply -f $WORKDIR/release/kubernetes-manifests.yaml

9.  Confirm that all components of the application have been deployed correctly:

        kubectl get pods -n $APP_NS

    The output should be similar to this:
    
        NAME                                     READY   STATUS     RESTARTS   AGE
        adservice-5d9dc7989b-8t2ql               0/2     Pending    0          78s
        cartservice-7555f749f-dw8mq              1/2     Running    2          80s
        checkoutservice-b96bf455b-2wx6n          2/2     Running    0          83s
        currencyservice-7f8658c69d-cnn4v         2/2     Running    0          80s
        emailservice-6658cb8f7b-tch6p            2/2     Running    0          83s
        frontend-65c5cc876c-pnk2l                2/2     Running    0          82s
        loadgenerator-778c8489d6-vflz2           0/2     Init:0/2   0          80s
        paymentservice-65bcb767c6-5w7p4          2/2     Running    0          81s
        productcatalogservice-6c4f68859b-848hg   2/2     Running    0          81s
        recommendationservice-5f844c876-m4p4j    2/2     Running    0          82s
        redis-cart-65bf66b8fd-hclhm              2/2     Running    0          79s
        shippingservice-55bc4768dd-8fgtv         2/2     Running    0          79s

    It may take some time for all pods to switch to the `Running` status.

## Deploy Grafana

In this section, you deploy Grafana in a dedicated namespace in your cluster using a Helm chart and template. Helm
is an open-source package manager for Kubernetes.

### Install Grafana

1.  Initialize Helm repository. (You can skip this step if you have helm already set up.)

        helm init

1.  Update the local Helm repository:

        helm repo update

1.  Download Grafana:

        helm fetch stable/grafana --untar

1.  Create a namespace dedicated to Grafana:

        kubectl create ns $MONITORING_NS

1.  Use the Helm chart to create the `.yaml` file:

        helm template grafana --namespace $MONITORING_NS --name grafana > $WORKDIR/grafana.yaml

1.  Deploy Grafana using the file created in the previous step:

        kubectl apply -f $WORKDIR/grafana.yaml -n $MONITORING_NS

1.  Verify the installation:

        kubectl get pods -n $MONITORING_NS
    
    The output should be similar to this:
    
        NAME                      READY   STATUS    RESTARTS   AGE
        grafana-8cf6ddd7b-d5srh   1/1     Running   0          23s
        grafana-test              0/1     Error     0          23s

### Connect to Grafana

1.  Get the Grafana password and copy the output:

        kubectl get secret \
            --namespace $MONITORING_NS grafana \
            -o jsonpath="{.data.admin-password}" \
            | base64 --decode ; echo

2.  Capture the name of the Grafana pod as a variable:

        export GRAFANA_POD=$(kubectl get pods --namespace $MONITORING_NS -l "app=grafana,release=grafana" -o jsonpath="{.items[0].metadata.name}")

3.  Use port forwarding to enable access to the Grafana UI:

        kubectl port-forward $GRAFANA_POD 3000 -n $MONITORING_NS

4.  Use the web preview in Cloud Shell to access the UI after changing the port to 3000:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/2-webpreview.png)

5.  At the Grafana login screen, enter `admin` as the username and paste in the password from step 1 to access Grafana.

## Configure data source and create dashboards

In this section, you configure Grafana to use Cloud Monitoring as the data source and create dashboards that will be used to 
visualize the health and status of your application.

### Configure Cloud Monitoring data source

1.  In the Grafana UI, click **Add data source**.

2.  Click **Stackdriver**.

3.  Switch **Authentication Type** to **Default GCE Service Account**. Note that this works because Grafana is running on a
    GKE cluster with default access scopes configured.

4.  Click **Save and Test**.

### Create the dashboard

In this section, you create a dashboard focusing on the
[golden signals](https://landing.google.com/sre/sre-book/chapters/monitoring-distributed-systems/) of monitoring: request
rates, errors, and latencies.

#### Create request rates view

1.  Hold your pointer over the **+** on the left side and select **Create** > **Dashboard**:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/3-create.png)

2.  Click **Add Query**.
   
3.  From the **Service** dropdown, select **Istio**.
   
4.  From the **Metric** dropdown, select **Server Request Count**.

5.  Click the **+** next to **Group By** and select **metric.label.destination_service_name**.

6.  From the **Aggregation** menu, select **Sum**.

7.  On the left side, click **Visualization**.

8.  Under **Axes** > **Left Y**, click the **Units** menu and select **Throughput** > **requests/sec (rps)**.

9.  On the left side, click **General**:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/4-query.png)

10. In the **Panel Title** field, enter **Request Rates by Service**.
    
11. Click the **Save Dashboard** button at the top right to save your work.
    
12. Click the left arrow at the top left to go back.
    
13. Click the **Dashboard Settings** button at the top right.
    
14. Under **General**, in the **Name** field, enter `GKE Services Dashboard` and click **Save**.

At this point, you should have a dashboard with a single view on it showing request rates for the services in your Istio 
service mesh.

![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/5-dashboard.png)

#### Create errors view

1.  At the top right, click the **Add Panel** button.

2.  Click **Add Query**.
   
3.  From the **Service** menu, select **Istio**.
   
4.  From the **Metric** dropdown, select **Server Request Count**.
   
5.  Click the **+** next to **Group By** and select **metric.label.destination_service_name**.
   
6.  Click the **+** next to **Filter** and select **metric.label.response_code**.

7.  Select **!=** as the operator and **200** as the value to only count failed requests.

    In this example, you're including 4xx errors in your count. Often, people choose to exclude these, because they 
    may be caused by issues on the client.

8.  From the **Aggregation** menu, select **Sum**.
   
9.  On the left side, click **Visualization**.

10. Under **Axes** > **Left Y**, click the **Units** menu and select **Throughput** > **requests/sec (rps)**.
    
11. On the left side, click **General**:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/6-query.png)

12.  In the **Panel Title** field, enter **Errors by Service**.
    
13. At the top right, click the **Save Dashboard** button.

At this point, your dashboard should contain two panels showing request rates and errors.

![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/7-dashboard.png)

#### Create latencies view

At this point, you have enough information to create the third view, showing server latency. Use the Server Response Latency
metric from the Istio service, filter out requests that meet the condition `metric.label.response_code!=200`, and group
by `metric.label.destination_service_name`. Use 99th percentile as the aggregator. (For information about why 99th percentile latency is the right signal to measure, see
[Metrics that matter](https://storage.googleapis.com/pub-tools-public-publication-data/pdf/9c3491f50f97dd01a973173d09dd8590c688eba6.pdf), by Ben Traynor, from Google's
[SRE](https://landing.google.com/sre/) group). When you're done, name the panel, save the dashboard, and organize the panels 
as you like. Your final result looks like this:

![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/8-dashboard.png)

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is
to delete the project that you created for the tutorial:

1.  In the Cloud Console, go to the [**Projects** page](https://console.cloud.google.com/iam-admin/projects).

2.  In the project list, select the project you want to delete, and click **Delete**.

    ![image](https://storage.googleapis.com/gcp-community/tutorials/visualizing-metrics-with-grafana/9-delete.png)

3.  In the dialog, type the project ID, and then click **Shut down**.

## What's next

-   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
