---
title: Monitor a Micronaut JVM application on GKE using Micrometer.
description: Learn how to use Micrometer to send JVM metrics to Cloud Monitoring through the Stackdriver agent.
author: viniciusccarvalho
tags: Google Kubernetes Engine, Java 
date_published: 2020-09-15
---

GKE offers built-in capabilities to monitor containers, providing insights into memory, CPU, and I/O resources. JVM applications, however, have
different memory configurations (heap versus non-heap), and each memory space can be split in several other parts (such as eden, tenured, and survivor). Often, 
Java developers face issues with memory configurations, and having the capability to inspect an application's memory utilization is essential.

Conventional APM tools make use of a [Java agent](https://docs.oracle.com/javase/7/docs/api/java/lang/instrument/package-summary.html) that's added to the 
class path of the application. In certain environments, such as Kubernetes and App Engine, configuring a Java agent is not always possible; this is where metrics
frameworks such as [Micrometer](https://micrometer.io) are useful.

In this tutorial, you learn how to use Micrometer integration with Cloud Monitoring to publish metrics without having to use a `javaagent` on your class path. 
You create a [Micronaut](https://micronaut.io) microservice application, deploy it to GKE, and create a dashboard to monitor the Java memory heap.

## Before you begin

For this tutorial, you must set up a Google Cloud project to host your [Micronaut](https://micronaut.io) application, and you must have Docker and the
Cloud SDK installed. We recommend that you create a new project for this tutorial, whcih makes the cleanup at the end easier.

1.  Use the [Cloud Console](https://console.cloud.google.com/)
    to create a new Google Cloud project. Remember the project ID; you will
    need it later. Later commands in this tutorial use `[PROJECT_ID]` as
    a placeholder, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.

3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure that
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project that you created.

3.  Install [JDK 11 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it.

## Prepare your environment

You need a new GKE cluster with [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) enabled. 

Run the following commands to setup your environment:

```
export CLUSTER_NAME=metrics-demo
export PROJECT_ID=[PROJECT_ID]
export GSA=micronaut-application
export KSA=$GSA
export NAMESPACE=default

gcloud config set project $PROJECT_ID

gcloud services enable container.googleapis.com \
containerregistry.googleapis.com

gcloud iam service-accounts create ${GSA} --project=${PROJECT_ID}

gcloud container clusters create ${CLUSTER_NAME} \
  --release-channel regular \
  --zone "us-central1-c" \
  --workload-pool=${PROJECT_ID}.svc.id.goog

gcloud container clusters --zone "us-central1-c" get-credentials ${CLUSTER_NAME}

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member="serviceAccount:${GSA}@${PROJECT_ID}.iam.gserviceaccount.com" \
--role="roles/monitoring.metricWriter"

gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${KSA}]" \
  ${GSA}@${PROJECT_ID}.iam.gserviceaccount.com

kubectl create serviceaccount --namespace $NAMESPACE $KSA

kubectl annotate serviceaccount \
  --namespace ${NAMESPACE} \
  ${KSA} \
  iam.gke.io/gcp-service-account=${GSA}@${PROJECT_ID}.iam.gserviceaccount.com    

```

## Create a new application

1.  Go to the [Micronaut Launch page](https://launch.micronaut.io).
1.  Add features:
    1.  Click **Features**. 
    1.  In the **Search Features** field, search for `jib` and then click to add the Jib component. 
    1.  In the **Search Features** field, search for `micrometer-stackdriver` and then click to add the Micrometer component.
    1.  Click **Done**.
1.  In the **Base package** section, enter `com.google.example`.
1.  In the **Name** section, enter `micronaut-jvm-metrics`.
1.  Click `Generate Project`.
1.  Download and extract the ZIP file and use it as your base directory for the rest of this tutorial.

## Set up the application

In this section, you set up the artifacts and necessary classes to get the application running.

1.  Open your `build.gradle` file and locate the line containing `jib.to.image = 'gcr.io/micronaut-jvm-metrics/jib-image'`. Replace that line with the following:

        jib{
            from {
                image= "gcr.io/distroless/java:11"
            }
            to{
                image = "gcr.io/[PROJECT_ID]/micronaut-jvm-metrics"
            }

        }

    Replace `[PROJECT_ID]` with the project ID for the project that you created at the beginning of this tutorial.

    The application uses [Jib](https://github.com/GoogleContainerTools/jib) to build and push your images to `gcr.io`. This code forces a `JDK 11` base image 
    and sets the target image that is used in the `deployment.yml` file.

1.  Replace your `application.yml` file with the following command:

        cat << EOL > src/main/resources/application.yml
        micronaut:
          application:
            name: micronautJvmMetrics
          metrics:
            export:
              stackdriver:
                enabled: true
                projectId: $PROJECT_ID
                step: PT1M
            enabled: true
        endpoints:
          health:
            enabled: true
            sensitive: false
        EOL

1.  Add the following class to your `src/main/java/com/google/example` directory:

        package com.google.example;

        import io.micrometer.core.instrument.MeterRegistry;
        import io.micronaut.configuration.metrics.aggregator.MeterRegistryConfigurer;
        import org.slf4j.Logger;
        import org.slf4j.LoggerFactory;

        import javax.inject.Singleton;
        import java.util.Optional;

        @Singleton
        public class ApplicationMeterRegistryConfigurer implements MeterRegistryConfigurer {

            private final Logger logger = LoggerFactory.getLogger(ApplicationMeterRegistryConfigurer.class);

            @Override
            public void configure(MeterRegistry meterRegistry) {
                String instanceId = Optional.ofNullable(System.getenv("HOSTNAME")).orElse("localhost");
                logger.info("Publishing metrics for pod " + instanceId);
                meterRegistry.config().commonTags("instance_id", instanceId);
            }

            @Override
            public boolean supports(MeterRegistry meterRegistry) {
                return true;
            }
        }

    This class adds labels that make the metrics unique for each application. Each container inside Kubernetes gets a hostname that is the same as the unique
    pod name. If you don't add a unique label and have multiple replicas of your application running, you can run into concurrency issues with Cloud Monitoring
    because multiple agents will report the same metrics with a window shorter than what was configured. Also, without a unique identifier, you wouldn't
    be able to filter or group metrics on the dashboard for each instance.

1.  Create a `deployment.yml` file:

        cat << EOL > deployment.yml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: "micronaut-jvm-metrics"
        spec:
          selector:
            matchLabels:
              app: "micronaut-jvm-metrics"
          template:
            metadata:
              labels:
                app: "micronaut-jvm-metrics"
            spec:
              serviceAccount: micronaut-application
              containers:
                - name: "micronaut-jvm-metrics"
                  image: "gcr.io/[PROJECT_ID]/micronaut-jvm-metrics"
                  ports:
                    - name: http
                      containerPort: 8080
                  readinessProbe:
                    httpGet:
                      path: /health
                      port: 8080
                    initialDelaySeconds: 5
                    timeoutSeconds: 3
                  livenessProbe:
                    httpGet:
                      path: /health
                      port: 8080
                    initialDelaySeconds: 5
                    timeoutSeconds: 3
                    failureThreshold: 10
          replicas: 2
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: "micronaut-jvm-metrics-svc"
        spec:
          selector:
            app: "micronaut-jvm-metrics"
          type: LoadBalancer
          ports:
            - protocol: "TCP"
              port: 80
              targetPort: 8080
        EOL

1.  Deploy the application:

        kubectl apply -f deployment.yml

Wait a few minutes before creating the dashboard in the next section, so that you can see the metrics.

## Create the dashboard

Navigate to [Cloud Monitoring](http://console.cloud.google.com/monitoring) and create a workspace if needed.

Visit [Metrics Explorer](https://console.cloud.google.com/monitoring/metrics-explorer) and add a few charts:

1. Heap memory chart

* Chart title: Heap memory
* On Metric use `custom/jvm/memory/used`
* On resource use `Global`
* On filter use `area` `=` `heap` and `instance_id` `=` `starts_with("micronaut")`
* Group by: `id` and `instance_id`

2. JVM memory chart

* Chart title: Heap memory
* On Metric use `custom/jvm/memory/used`
* On resource use `Global`
* On filter use `instance_id` `=` `starts_with("micronaut")`
* Group by: `instance_id`
* Aggregator: `sum`

3. Container memory chart

* Chart title: Container memory
* On Metric use `Memory usage`
* On resource use `k8s_container`
* On filter use `container_name` `=` `micronaut-jvm-metrics)`
* Group by: `pod_name`
* Aggregator: `sum`

Add the charts to a new dashboard, for instance name it `JVM`.

After letting your application running for a while your dashboard should look like this:

![JVM Metrics](https://storage.googleapis.com/gcp-community/tutorials/monitoring-jvm-metrics-gke/cloud_monitoring_jvm_dashboard.png)

You can now check different heap spaces on the `Heap Memory usage` such as Eden, Tenured and Survivor spaces. And see that our chart follow the nice sawtooth pattern expected from GC collection.


## _Optional_ Add some load to simulate memory pressure

You can simulate some traffic to see some memory pressure on your charts using the [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) tool:

```
export APPLICATION_URL=$(kubectl get service micronaut-jvm-metrics-svc -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

ab -n 50000 -c 100  $APPLICATION_URL/health
```

## Clean up

Once you are a done, remove the project to avoid extra costs.

To delete a project, do the following:

1.  In the Cloud Console, go to the **Manage resources** page.

    [Go to the **Manage resources** page](https://console.cloud.google.com/iam-admin/projects)

1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.
