---
title: Write Prometheus metrics to BigQuery
description: Learn how to use the Prometheus remote write feature to write metrics to BigQuery.
author: tzehon
tags: monitoring, prometheus, metrics, bigquery
date_published: 2021-03-29
---

Tze Hon | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes a solution that uses [Kohl's](https://www.kohls.com/)
[Prometheus to BigQuery remote storage adapter](https://github.com/KohlsTechnology/prometheus_bigquery_remote_storage_adapter) to enable
[Prometheus](https://prometheus.io/) to write metrics to [BigQuery](https://cloud.google.com/bigquery) using
[remote write and remote read integration](https://prometheus.io/docs/operating/integrations/#remote-endpoints-and-storage).

You might want to access your Prometheus data for various purposes like machine learning or anomaly detection. These are difficult to do inside Prometheus, so 
it's useful to have this data in remote storage such as BigQuery. This also means that your metrics can be stored for much longer retention periods. BigQuery can
also provide a global querying view by accepting data from multiple Prometheus instances across datacenters or multiple cloud providers. This is useful for 
building global dashboards for multi-datacenter/multi-cloud setups.

In this tutorial, you learn how to deploy Prometheus to a [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine) cluster using the 
[Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator), and write metrics to BigQuery directly.

For this tutorial, basic knowledge of GKE, [Kubernetes Operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/), Prometheus, and BigQuery is 
assumed.

## Objectives

*   Deploy Prometheus using the Prometheus Operator
*   Configure Prometheus to write to BigQuery remotely
*   Update the Prometheus configuration using the Prometheus operator
*   Query metrics from BigQuery
*   Query metrics from Prometheus

## Costs

This tutorial uses billable components of Google Cloud, including the following:

-  [GKE](https://cloud.google.com/kubernetes-engine/pricing)
-  [BigQuery](https://cloud.google.com/bigquery/pricing)
-  [Cloud Logging](https://cloud.google.com/stackdriver/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you have already created. When you finish this tutorial, you can avoid continued billing by deleting the resources that you
created. To make cleanup easiest, you may want to create a new project for this tutorial, so that you can delete the project when you're done. For details, see
the  "Cleaning up" section at the end of the tutorial.

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://cloud.google.com/billing/docs/how-to/modify-project#enable-billing)

1.  Make sure that you have either a project [owner or editor role](https://cloud.google.com/iam/docs/understanding-roles#primitive_roles), or sufficient
    permissions to use the services listed above.

## Using Cloud Shell

This tutorial uses the following tool packages:

* [`gcloud`](https://cloud.google.com/sdk/gcloud)
* [`bq`](https://cloud.google.com/bigquery/docs/bq-command-line-tool)
* [`jq`](https://stedolan.github.io/jq/)

Because [Cloud Shell](https://cloud.google.com/shell) automatically includes these packages, we recommend that you run the commands in this tutorial in Cloud
Shell, so that you don't need to install these packages locally.

## Preparing your environment

### Open Cloud Shell

Open Cloud Shell by clicking the **Activate Cloud Shell** button in the navigation bar in the upper-right corner of the console.

### Get the sample code

The sample code for this tutorial is in the
[Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/exporting-prometheus-metrics-bigquery).

1.  Clone the repository:

        git clone https://github.com/GoogleCloudPlatform/community.git

1.  Go to the tutorial directory:

        cd community/tutorials/writing-prometheus-metrics-bigquery

## Implementation steps

### Set the environment variables

1. Set the environment variables used for the rest of this tutorial:

        export PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
        export BIGQUERY_DATASET=prometheus
        export BIGQUERY_TABLE=metrics
        export CLUSTER_NAME=prom-cluster
        export DEFAULT_ZONE=asia-southeast1-a
        export SERVICE_ACCOUNT=prom-to-bq

### Enable the required APIs

1.  Enable the GKE and BigQuery APIs:

        gcloud services enable \
          container.googleapis.com \
          bigquery.googleapis.com

### Create BQ dataset and table

1.  Create a BigQuery dataset:

        bq mk $BIGQUERY_DATASET

1.  Create a table using the schema JSON file:

        bq mk --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE} ./bigquery_schema.json

### Create a GKE cluster

1.  Create a GKE cluster:

        gcloud container clusters create ${CLUSTER_NAME} --zone ${DEFAULT_ZONE} \
          --machine-type "e2-standard-8" --num-nodes "3" \
          --enable-stackdriver-kubernetes --enable-ip-alias \
          --workload-pool=${PROJECT_ID}.svc.id.goog

1.  Connect to your cluster:

        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${DEFAULT_ZONE}

### Deploy the Prometheus Operator

1. Deploy the Prometheus Operator into your cluster:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/bundle.yaml


### Deploy the sample application

1. Deploy three instances of a simple example application, which listens and exposes metrics on port 8080:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/user-guides/getting-started/example-app-deployment.yaml

1. Deploy the Service:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/user-guides/getting-started/example-app-service.yaml

   This Service object is discovered by a `ServiceMonitor`, which selects in the same way. The `app` label must have the value `example-app`.

1. Deploy the Service Monitor:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/user-guides/getting-started/example-app-service-monitor.yaml

### Deploy RBAC resources

1. Deploy the Kubernetes Service Account called `prometheus` to the `default` namespace :

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/rbac/prometheus/prometheus-service-account.yaml

1. Deploy the `ClusterRole`:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/rbac/prometheus/prometheus-cluster-role.yaml

1. Deploy the `ClusterRoleBinding`:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/rbac/prometheus/prometheus-cluster-role-binding.yaml

### Deploy Prometheus

1. Using the Prometheus Operator lets us configure and manage Prometheus with familiar Kubernetes APIs in a declarative approach. Deploy Prometheus with a default Prometheus configuration:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/rbac/prometheus/prometheus.yaml

### Expose Prometheus

1. Expose Prometheus using a `NodePort` Service:

        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.46.0/example/user-guides/getting-started/prometheus-service.yaml

### Check that Prometheus is successfully deployed

1. Forward a local port to the Prometheus port so we  can access it locally in Cloud Shell:

        PORT=$(kubectl get -o jsonpath="{.spec.ports[0].port}" services prometheus) \
          && kubectl port-forward service/prometheus 8080:$PORT

      `kubectl port-forward` does not return. Click the **+** tab in Cloud Shell to open a new terminal for the next step.

1. In the new terminal, check that you have deployed Prometheus successfully:

        curl http://localhost:8080/metrics

    You should see some results:

        # HELP promhttp_metric_handler_requests_total Total number of scrapes by HTTP status code.
        # TYPE promhttp_metric_handler_requests_total counter
        promhttp_metric_handler_requests_total{code="200"} 6
        promhttp_metric_handler_requests_total{code="500"} 0
        promhttp_metric_handler_requests_total{code="503"} 0

1. Close this terminal and return to your previous terminal. Enter `Ctrl-c` to stop port forwarding.

### Deploy an updated Prometheus configuration

1. Create a Google service account that Prometheus will use to write metrics to BigQuery:

        gcloud iam service-accounts create ${SERVICE_ACCOUNT}

1. We use [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) to access BigQuery from GKE instead of exporting service account keys and storing them as Kubernetes Secrets. Allow the Kubernetes service account to impersonate the Google service account by creating an IAM policy binding between the two. This binding allows the Kubernetes Service account to act as the Google service account:

        gcloud iam service-accounts add-iam-policy-binding \
            --role roles/iam.workloadIdentityUser \
            --member "serviceAccount:${PROJECT_ID}.svc.id.goog[default/prometheus]" \
            ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com

    `[default/prometheus]` is a combination of the Kubernetes namespace where you [created the Kubernetes service account and the service account name](#deploy-rbac-resources) in the form of `[namespace/service account name]`

1. Give your service account the necessary permissions to read/write data and submit jobs to BigQuery:

        gcloud projects add-iam-policy-binding ${PROJECT_ID}  \
            --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="roles/bigquery.dataEditor"

        gcloud projects add-iam-policy-binding ${PROJECT_ID}  \
            --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="roles/bigquery.jobUser"

1. Add the `iam.gke.io/gcp-service-account=${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com` annotation to the Kubernetes service account, using the email address of the Google service account:

        kubectl annotate serviceaccount \
            --namespace default \
            prometheus \
            iam.gke.io/gcp-service-account=${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com

1. Deploy the updated Prometheus configuration:

        envsubst < custom_prometheus_template.yaml > custom_prometheus.yaml
        kubectl apply -f custom_prometheus.yaml

### Query metrics from BigQuery

1. You can query metrics directly from BigQuery after the Prometheus configuration is updated in a minute:

        envsubst < query_template.sql > query.sql
        bq query --use_legacy_sql=false < query.sql

1. The query in [query_template.sql](query_template.sql) shows how to get all metrics belonging to the `example-app` service that have a HTTP 200 response code:

        SELECT
          metricname,
          tags,
          JSON_EXTRACT(tags,
            '$.service') AS service,
          value,
          timestamp
        FROM
          `${PROJECT_ID}.${BIGQUERY_DATASET}.${BIGQUERY_TABLE}`
        WHERE
          JSON_EXTRACT(tags,
            '$.status') = "\"200\""
          AND JSON_EXTRACT(tags,
            '$.service') = "\"example-app\""
        LIMIT
          10

### Query metrics from Prometheus

1. You can also query metrics from Prometheus. When configured, Prometheus queries are sent to both local and remote storage, and the results are merged. In this tutorial, this means that Prometheus queries BigQuery remotely, and merges the returned results with results from local storage for you. Forward a local port to the Prometheus port:

        kubectl port-forward service/prometheus 8080:$PORT

1. Click the **Web preview** icon in Cloud Shell and click **Preview on port 8080** to open the Prometheus UI:

    ![web-preview](web_preview.png)

1. Enter a query to return the number of successful HTTP requests as measured over the last 5 minutes for the `example-app` job and click `Execute`:

        sum by (job, code) (
          increase(http_requests_total{job="example-app", code="200"}[5m])
        )

    ![prom-ui](prom-ui.png)

1. Prometheus fetches data from local storage and BigQuery, processes the data and displays it. Return to your terminal and enter `Ctrl-c` to stop port-forwarding. After a few seconds, you can check Cloud Logging to see the actual query used by Prometheus's BigQuery remote read integration:

        gcloud logging read "resource.type=bigquery_resource \
            AND protoPayload.serviceData.jobQueryRequest.projectId=${PROJECT_ID} \
            AND severity=INFO" \
            --limit 1 --format json | jq '.[].protoPayload.serviceData.jobQueryRequest.query'

1. You should see the translated query in the returned result:

        SELECT
          metricname,
          tags,
          UNIX_MILLIS(timestamp) AS timestamp,
          value
        FROM
          prometheus.metrics
        WHERE
          IFNULL(JSON_EXTRACT(tags, '$.job'), '\"\"') = '\"example-app\"'
          AND IFNULL(JSON_EXTRACT(tags, '$.code'), '\"\"') = '\"200\"'
          AND metricname = 'http_requests_total'
          AND IFNULL(JSON_EXTRACT(tags, '$.prometheus'), '\"\"') = '\"default/prometheus\"'
          AND IFNULL(JSON_EXTRACT(tags, '$.prometheus_replica'), '\"\"') = '\"prometheus-prometheus-1\"'
          AND timestamp >= TIMESTAMP_MILLIS(1614994292423)
          AND timestamp <= TIMESTAMP_MILLIS(1614994592423)
        ORDER BY
          timestamp

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the resources that you created. You can either
delete the entire project or delete individual resources.

Deleting a project has the following effects:

* Everything in the project is deleted. If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the
  project.
* Custom project IDs are lost. When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs
  that use the project ID, delete selected resources inside the project instead of deleting the whole project.

If you plan to explore multiple tutorials, reusing projects can help you to avoid exceeding project quota limits.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

1.  In the Cloud Console, go to the [**Manage resources page**](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

### Delete the resources

If you don't want to delete the project, you can delete the provisioned resources:

    gcloud container clusters delete ${CLUSTER_NAME} --zone ${DEFAULT_ZONE}

    gcloud iam service-accounts delete ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com

    bq rm --table ${BIGQUERY_DATASET}.${BIGQUERY_TABLE}

    bq rm ${BIGQUERY_DATASET}

## What's next

-  Learn how to [manage Cloud Monitoring dashboards with the Cloud Monitoring API](https://cloud.google.com/solutions/managing-monitoring-dashboards-automatically-using-the-api)
-  Learn more about to [export metrics from multiple projects](https://cloud.google.com/solutions/stackdriver-monitoring-metric-export).
-  Try out other Google Cloud features for yourself. Have a look at those [tutorials](https://cloud.google.com/docs/tutorials).
