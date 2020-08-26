---
title: Monitor a Micronaut JVM application on GKE using Micrometer.
description: Learn how to use Micrometer to send JVM metrics to cloud monitoring via stackdriver agent.
author: vinnyc
tags: App Engine, Kotlin, Spring Boot
date_published:
---

GKE offers built-in capabilities to monitor containers, it provides insights into memory, cpu and IO resources. JVM applications however have
different memory configurations (heap vs non-heap) and each memory space can be split in several other parts (Eden, Tenured, Survivor). More often than not, java developers face issues with memory configurations and having the capability to inspect an application memory utilization is an essential feature for java developers.

Traditional application monitoring tools leverage the use of a [java agent](https://docs.oracle.com/javase/7/docs/api/java/lang/instrument/package-summary.html) that is added to the classpath of the application. In certain environments such as Kubernetes and App Engine, configuring a java agent is not always possible, this is where metrics frameworks such as
[Micrometer](https://micrometer.io) comes in hand.

On this tutorial we will explain how you can use Micrometer integration with stackdriver, to publish metrics without having to use a `javaagent` on your path. We will create a [Micronaut](https://micronaut.io) microservice application, deploy it to GKE create a dashboard to monitor the java memory heap space.

## Before you begin

Before running this tutorial, you must set up a Google Cloud Platform project,
and you need to have Docker and the Google Cloud SDK installed.

Create a project that will host your [Micronaut](https://micronaut.io) application. You can also reuse
an existing project.

1.  Use the [Google Cloud Platform Console](https://console.cloud.google.com/)
    to create a new Cloud Platform project. Remember the project ID; you will
    need it later. Later commands in this tutorial will use `[PROJECT_ID]` as
    a substitution, so you might consider setting the `PROJECT_ID` environment
    variable in your shell.

2.  Enable billing for your project.

3.  Install the [Google Cloud SDK](https://cloud.google.com/sdk/). Make sure
    you [initialize](https://cloud.google.com/sdk/docs/initializing) the SDK
    and set the default project to the new project you created.

3.  Install [JDK 11 or higher](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) if you do not already have it.

## Prepare your environments

You will need a new GKE cluster with [workload identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) enabled. Run the following commands to setup your environment

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

Go to https://launch.micronaut.io and create a new application.

* On Features search for `jib` and `micrometer-stackdriver`
* Base package set to `com.google.example` - This will make easier to paste code from this tutorial on the right packages
* Name: `micronaut-jvm-metrics`
* Click `Generate Project`
* Extract the zip file and use it as your base directory for the rest of this tutorial

### Set up the applications

Now you need to setup the artifacts and necessary classes to get the application running.

Open your `build.gradle` and locate the line containing `jib.to.image = 'gcr.io/micronaut-jvm-metrics/jib-image'`, replace it with the following:

```
jib{
    from {
        image= "gcr.io/distroless/java:11"
    }
    to{
        image = "gcr.io/[PROJECT_ID]/micronaut-jvm-metrics"
    }

}
```

NOTE: Make sure you use the `[PROJECT_ID]` created on the first step of this tutorial

We are using [jib](https://github.com/GoogleContainerTools/jib) to build and push our images to `gcr.io`, here we are forcing a `JDK 11` base image and pointing to the image we will use on our `deployment.yml` file.

Replace your `application.yml` file via the following command:

```
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
```

Add the following class to your `src/main/java/com/google/example` directory :

```java
package com.google.example;

import io.micrometer.core.instrument.MeterRegistry;
import io.micronaut.configuration.metrics.aggregator.MeterRegistryConfigurer;
import io.micronaut.context.annotation.Value;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.inject.Singleton;

@Singleton
public class ApplicationMeterRegistryConfigurer implements MeterRegistryConfigurer {

    private final Logger logger = LoggerFactory.getLogger(ApplicationMeterRegistryConfigurer.class);

    @Value("${POD_NAME:micronaut}")
    private String applicationName;

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
```

The reason we need this class is to add the correct labels to Stackdriver. For instance, if multiple replicas are sending metrics at the same time we could run in issues with stackdriver saying that we are sending more data points than the configured time window of 1 minute. By adding a label (`instance_id`) that makes each metric unique, we won't run into this issue and we will also be able to group and filter metrics on the cloud monitoring dashboard.

Create a `deployment.yml` file

```
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
```
Deploy the application using `kubectl apply -f deployment.yml`.

NOTE: You should wait a few minutes before creating the dashboard on the next section to be able to see the metrics.

## Create the dashboard

Navigate to Cloud Monitoring and create a workspace if needed.

Visit `metrics explorer` and we will create a few charts.

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
