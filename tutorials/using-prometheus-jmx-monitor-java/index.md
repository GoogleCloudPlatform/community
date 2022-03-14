---
title: Use Prometheus and JMX to monitor Java applications on Google Kubernetes Engine 
description: Learn how to monitor Java applications running on GKE with Prometheus and Cloud Monitoring.
author: xiangshen-dk
tags: monitoring, stackdriver, prometheus, jmx, java
date_published: 2021-06-04
---

Xiang Shen | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to use [Prometheus](https://prometheus.io/) and
[Java Management Extensions(JMX)](https://en.wikipedia.org/wiki/Java_Management_Extensions) to monitor a Java application running on a
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine) cluster. This tutorial shows you how to deploy Prometheus, enable JMX monitoring, and view
metrics data in [Cloud Monitoring](https://cloud.google.com/monitoring). This tutorial is for developers and operators who want to have better observability of
the Java metrics exposed by JMX.

## Objectives 

+   Deploy Prometheus on a Google Kubernetes Engine cluster.
+   Deploy a Java application with JMX enabled.
+   Configure the Cloud Monitoring Prometheus sidecar.
+   Visualize JVM metrics in Cloud Monitoring.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

+   [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/pricing)
+   [Cloud Load Balancing](https://cloud.google.com/vpc/network-pricing#lb)
+   [Compute Engine](https://cloud.google.com/compute/pricing)
+   Chargeable [external metrics](https://cloud.google.com/stackdriver/pricing#metrics-chargeable)

To generate a cost estimate based on your projected usage, use the
[pricing calculator](https://cloud.google.com/products/calculator#id=38ec76f1-971f-41b5-8aec-a04e732129cc).

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)
1.  [Enable the Kubernetes Engine, Container Registry, Cloud Monitoring, and Cloud Build APIs.](https://console.cloud.google.com/flows/enableapi?apiid=containerregistry.googleapis.com,container.googleapis.com,monitoring.googleapis.com,cloudbuild.googleapis.com)
1.  Make sure that you have either a [project owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient 
    permissions to use the services listed above. 

This tutorial uses the [gcloud](https://cloud.google.com/sdk/gcloud) command-line tool. We recommend that you run the commands in this tutorial in
[Cloud Shell](https://cloud.google.com/shell).

## Set common variables

You need to define several variables that control where elements of the infrastructure are deployed.

1.  In Cloud Shell, set the region, zone, and project ID:

        region=us-east1
        zone=${region}-b
        project_id=[YOUR_PROJECT_ID]
        
    Replace `[YOUR_PROJECT_ID]` with your project ID. This tutorial uses the region `us-east1`. If you want to change the region, check that the zone 
    values are appropriate for the region that you specify.

1.  Set the default zone and project ID so that you don't need to specify these values in subsequent commands:

        gcloud config set project ${project_id}
        gcloud config set compute/zone ${zone}

## Create the GKE cluster

1.  In Cloud Shell, create the GKE cluster:

        gcloud container clusters create jmx-demo-cluster \
          --zone ${zone} \
          --tags=gke-cluster-with-jmx-monitoring

1.  Wait a few minutes until the cluster is successfully created, and ensure that the cluster's status is **RUNNING**.

    You can run the following command to view the status:

        gcloud container clusters list

## Install and configure the Prometheus server


1.  Clone the sample repository:

        git clone https://github.com/xiangshen-dk/gke-prometheus-jmx.git

    The sample repository includes the Kubernetes manifests for Prometheus and the demonstration app that you deploy.
    
1.  Go to the directory that contains the tutorial files:

        cd gke-prometheus-jmx

1.  Create a dedicated namespace in the cluster for Prometheus:

        kubectl create namespace prometheus

1.  Create a Prometheus Kubernetes service account, a `ClusterRole` role, and a cluster role binding:

        kubectl apply -f clusterRole.yaml

1.  Create the Prometheus configuration to scrape metrics from apps running in the `GKE` cluster:

        kubectl apply -f config-map.yaml

1.  Define environment variables used in the Prometheus deployment manifest:

        export KUBE_NAMESPACE=prometheus
        export KUBE_CLUSTER=jmx-demo-cluster
        export GCP_LOCATION=$zone
        export GCP_PROJECT=$(gcloud info --format='value(config.project)')
        export DATA_DIR=/prometheus
        export DATA_VOLUME=prometheus-storage-volume
        export SIDECAR_IMAGE_TAG=0.8.2
        export PROMETHEUS_VER_TAG=v2.19.3

1.  Apply the Prometheus deployment manifest by using the environment variables you defined:

        envsubst < prometheus-deployment.yaml | kubectl apply -f -
   
    The manifest creates the Prometheus deployment with a single pod. The pod is composed of two containers: the Prometheus server container and Google's
    [Monitoring sidecar](https://github.com/Stackdriver/stackdriver-prometheus-sidecar). The Prometheus server container collects metrics from pods in the GKE
    cluster that are exporting Prometheus metrics. The server uses the Monitoring sidecar container to push metrics to Monitoring.

1.  Confirm that the status of the Prometheus pod is **Running**:

        kubectl get pods -n prometheus
        
    Deployment can take a few minutes.

    When deployment is complete, the output looks similar to the following:

        NAME                                     READY   STATUS    RESTARTS   AGE
        prometheus-deployment-6d76c4f447-cbdlr   2/2     Running   0          38s

## Inspect Prometheus on the GKE cluster

Using the Prometheus Kubernetes service account, Prometheus discovers resources that are running in a GKE cluster. Some of these resources are already configured
to export Prometheus metrics.

1.  Set up port forwarding to the Prometheus server UI that's running in the GKE cluster:

        export PROMETHEUS_POD_GKE=$(kubectl get pods --namespace prometheus -l "app=prometheus-server" \
            -o jsonpath="{.items[0].metadata.name}")
        
        kubectl port-forward --namespace prometheus $PROMETHEUS_POD_GKE 8080:9090 >> /dev/null &

1.  In Cloud Shell, click **Web preview** in the upper-right corner of the panel, and choose **Preview on port 8080** from the menu that appears.

    If the port is not 8080, click **Change port**, change the port to 8080, and then click **Change and preview**.
    
    The Prometheus server UI is displayed.

1.  In the Prometheus UI, select **Status > Service discovery**. 

    ![prom-service-discovery](https://storage.googleapis.com/gcp-community/tutorials/using-prometheus-jmx-monitor-java/prom-svc-discovery.png)

1.  Click **Status > Targets**.

Targets are the HTTP(S) endpoints defined in resources that are exporting Prometheus metrics at regular intervals. You see various Kubernetes resources that are
exporting metrics, such as the Kubernetes API server exporting metrics from the `/metrics` HTTPS endpoint.

## Create the test Java application

In this tutorial, you create a Spring Boot application to test the configuration. To learn more about the application, see the
[quickstart for Java](https://cloud.google.com/kubernetes-engine/docs/quickstarts/deploying-a-language-specific-app#java_1).

1.  In Cloud Shell, create a new empty web project:

        curl https://start.spring.io/starter.zip \
            -d dependencies=web \
            -d javaVersion=11 \
            -d bootVersion=2.4.4.RELEASE \
            -d name=helloworld \
            -d artifactId=helloworld \
            -d baseDir=helloworld-gke \
            -o helloworld-gke.zip

        unzip helloworld-gke.zip

1.  Go to the `helloworld-gke` directory:

        cd helloworld-gke

1.  Update the `HelloworldApplication` class by adding a `@RestController` to handle the `/` mapping and return the response that you need:

        cp ../HelloworldApplication.java src/main/java/com/example/helloworld/HelloworldApplication.java

1.  Copy the example Dockerfile from the cloned repository:

        cp ../Dockerfile .

    If you open the Dockerfile, you can see that it downloads the Prometheus [JMX exporter](https://github.com/prometheus/jmx_exporter) and runs it as a
    Java agent on port 9404:

        # Run the web service on container startup.
        CMD ["java", "-javaagent:./jmx_prometheus_javaagent-0.15.0.jar=9404:config.yaml", \
            "-Djava.security.egd=file:/dev/./urandom", \
            "-Dcom.sun.management.jmxremote.ssl=false", \
            "-Dcom.sun.management.jmxremote.authenticate=false", \
            "-Dcom.sun.management.jmxremote.port=5555", \
            "-Dserver.port=${PORT}","-jar", \
            "/helloworld.jar"]

1.  Copy the configuration file for the JMX exporter:

        cp ../config.yaml .

    In the `jmx_exporter` repository, there are more [configuration examples](https://github.com/prometheus/jmx_exporter/tree/master/example_configs) for common
    applications such as Tomcat, Spark, and Kafka. 

    JMX is configured to use port 5555 and disable authentication and SSL. If you need to change the setup, refer to the
    [JMX documentation](https://docs.oracle.com/en/java/javase/11/management/monitoring-and-management-using-jmx-technology.html).

1.  Build the container image using Cloud Build:

        gcloud builds submit --tag gcr.io/${project_id}/helloworld-gke .

1.  Deploy the `hellworld-gke` application to the GKE cluster:

        envsubst < ../helloworld-deployment.yaml | kubectl apply -f -

    If you open the `helloworld-deployment.yaml` file, you can see that it uses the annotations in the Deployment to let Prometheus know to scrape the metrics 
    and on which port:

        # This file configures the hello-world app which serves public web traffic.
        apiVersion: apps/v1
        kind: Deployment
        metadata:
         name: helloworld-gke
        spec:
         replicas: 1
         selector:
           matchLabels:
             app: hello
         template:
           metadata:
             labels:
               app: hello
             annotations:
               prometheus.io/scrape: 'true'
               prometheus.io/port: '9404'
           spec:
             containers:
             - name: hello-app
               # Replace $GCLOUD_PROJECT with your project ID
               image: gcr.io/${GCP_PROJECT}/helloworld-gke:latest
               # This app listens on port 8080 for web traffic by default.
               ports:
               - containerPort: 8080
               env:
                 - name: PORT
                   value: "8080"
        ---
        apiVersion: v1
        kind: Service
        metadata:
         name: hello
        spec:
         type: LoadBalancer
         selector:
           app: hello
         ports:
         - port: 80
           targetPort: 8080

1.  View the status of the `helloworld-gke` pods:

        kubectl get pods

    Repeat this command until the output looks like the following, with the `helloworld-gke` pod running:

        NAME                              READY   STATUS    RESTARTS   AGE
        helloworld-gke-54c5b678c6-csdlw   1/1     Running   0          28s

1.  Check to see that the service is deployed:

        kubectl get services
        
    The output should be similar to the following:
    
        NAME         TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)        AGE
        hello        LoadBalancer   10.47.242.246   34.73.69.237   80:31374/TCP   62s
        kubernetes   ClusterIP      10.47.240.1     <none>         443/TCP        37m

1.  When the external IP address is provisioned, open a browser window using the external IP address as the URL.

    For example, using the value from above: `http://34.73.69.237`.

    When the service is running, you see the response `Hello World!`

## View the exported JVM metrics in Prometheus

1.  In Prometheus, in the **Expression** field, type `jvm_memory_bytes_used` in the search field and click the **Graph** tab.

    You see a graph similar to the following:

    ![jvm-memory-bytes](https://storage.googleapis.com/gcp-community/tutorials/using-prometheus-jmx-monitor-java/prom-cloud-monitoring.png)

## View the exported JVM metrics in Cloud Monitoring

Prometheus is configured to export metrics to Google Cloud's operations suite as
[external metrics](https://cloud.google.com/monitoring/api/metrics_other#externalgoogleapiscom).  

1.  In the Cloud Console to the [Cloud Monitoring **Metrics explorer** page](https://console.cloud.google.com/monitoring/metrics-explorer).
1.  In the **Find resource type and metric** menu, select **Kubernetes Container** (`k8s_container`) for the **Resource type**.
1.  For the **Metric** field, select one with the prefix `external/prometheus/`. For example, you might
    select `external.googleapis.com/prometheus/jvm_memory_bytes_used`.

    In the following example, a filter was added to display the metrics for a specific cluster and a container. Filtering is useful when you have multiple
    clusters and many containers:

    ![image](https://storage.googleapis.com/gcp-community/tutorials/using-prometheus-jmx-monitor-java/metric-explorer.png)

## Cleaning up

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the individual resources

If you don't want to delete the whole project, run the following command to delete the clusters: 

    gcloud container clusters delete jmx-demo-cluster --zone us-east1-b

You can delete the container images using the following steps:

1.  Go to the [Container Registry page](https://console.cloud.google.com/kubernetes/images/list).
1.  Click the `helloworld-gke` image, and select all versions by marking the checkbox next to **Name**. 
1.  Click **Delete** at the top of the page.

## What's next

+   Learn about [white-box app monitoring for GKE with Prometheus](https://cloud.google.com/solutions/white-box-app-monitoring-for-gke-with-prometheus).
+   Learn about the [Cloud Monitoring integration with Prometheus](https://cloud.google.com/stackdriver/docs/solutions/gke/prometheus).
+   Learn about
    [Monitoring apps running on multiple GKE clusters using Prometheus and Cloud Monitoring](https://cloud.google.com/solutions/monitoring-apps-running-on-multiple-gke-clusters-using-prometheus-and-stackdriver).
+   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
