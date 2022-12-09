---
title: Filtering Prometheus metrics
description: Learn how to setup filtering Prometheus metrics on the Pod side
author: ganochenkodg
tags: Prometheus, metrics
date_published: 2020-12-07
---

Ganochenko Dmitrii

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to set up filtering Prometheus metrics on the Pod size, without using `metric_relabel_config` feature.
Follow this tutorial to update the Pod specification and configure filtering metrics with allow and block lists.

### Objectives

*   Add Pod that exposes metrics in the Prometheus format.
*   Add `metrics-filter` container to the Pod's containers.
*   Pass allow and block rules as environment variables.
*   Update Pod's annotations to scrape metrics from the new endpoint.
*   Check the new endpoint.

### Costs

This tutorial uses Kubernetes Engine, a billable component of Google Cloud.
You can use the [pricing calculator](https://cloud.google.com/products/calculator)
to generate a cost estimate based on your projected usage.

### Prerequisite: Kubernetes cluster

This tutorial assumes that you have a running Kubernetes cluster. This can be a cluster created through
[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/), or any other solution. 

You will also need a recent `kubectl` command-line interface (version 1.22 or greater). 
If you have an older version of `kubectl`, install version 1.22 or greater from the
[Kubernetes website](https://kubernetes.io/docs/tasks/tools/install-kubectl/). 
Ensure that `kubectl` is configured to communicate with your cluster.

### Deploy simple Pod with metrics

Now we're going to deploy simple Pod, that will expose some metrics. 
Please run the following command in your terminal:

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-metrics-pod
  labels:
    app: test-metrics-pod
spec:
  containers:
  - name: node-exporter
    image: docker.io/bitnami/node-exporter:latest
    ports:
    - containerPort: 9100
EOF
```

You can verify that everything is running:

```
% kubectl get pod
NAME                                       READY   STATUS      RESTARTS   AGE
test-metrics-pod                           1/1     Running     0          10s
```

It's time to check exposed metrics of our Pod. Let's expose his metrics:

```
% kubectl expose pod test-metrics-pod --port=9100 --name=original-metrics
service/originial-metrics exposed
```

We will run simple Pod with curl to run requests to Kubernetes services:

```
% kubectl run curl-orig --image=curlimages/curl -it -- sh
If you don't see a command prompt, try pressing enter.
/ $ curl original-metrics:9100/metrics
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
go_gc_duration_seconds{quantile="0"} 5.3779e-05
go_gc_duration_seconds{quantile="0.25"} 5.3779e-05
...
promhttp_metric_handler_requests_total{code="500"} 0
promhttp_metric_handler_requests_total{code="503"} 0
```

You'll get a long list of metrics.

### Add metrics-filter

What if you want to filter out some expose metrics without configuring Prometheus, or you don't even use it for scraping metrics? 
We're now going to add [metrics-filter](https://github.com/ganochenkodg/metrics-filter) container to your Pod by running this command:

```
kubectl delete pod test-metrics-pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-metrics-pod
  labels:
    app: test-metrics-pod
spec:
  containers:
  - name: node-exporter
    image: docker.io/bitnami/node-exporter:latest
    ports:
    - containerPort: 9100
  - name: metrics-filter
    image: docker.io/dganochenko/metrics-filter:latest
    env:
      - name: ALLOW_LIST
        value: "process_"
      - name: BLOCK_LIST
        value: "_memory"
      - name: REMOTE_METRICS_ENDPOINT
        value: "http://localhost:9100/metrics"
    ports:
    - containerPort: 9200
EOF
```

Let's check if metrics were successfully filtered:

```
% kubectl expose pod test-metrics-pod --port=9200 --name=filtered-metrics
service/filtered-metrics exposed
% kubectl run curl-filter --image=curlimages/curl -it -- sh
If you don't see a command prompt, try pressing enter.
/ $ curl filtered-metrics:9200/metrics
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 0.03
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 9
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.67052730803e+09
```

### Behind the scenes

What's going on behind the scenes? 
Your incoming request goes to the `metrics-filter` container. It scrapes original metrics from the node-exporter container, ENV `REMOTE_METRICS_ENDPOINT` tells where to get them. 
After that metrics were filtered the next way:
- If ENV `ALLOW_LIST` is set, all metrics that don't have keywords from this list will be filtered out.
- If ENV `BLOCK_LIST` is set, all metrics that have keywords from this list will be filtered out.

The result will be returned. It's not necessary to set both ENVs simultaneously.

### What's next

- Learn more about [metrics-filter](https://github.com/ganochenkodg/metrics-filter).
- Learn more about [auto-discovery Prometheus metrics](https://www.acagroup.be/en/blog/auto-discovery-of-kubernetes-endpoint-services-prometheus/).
- Try out collecting metrics to Google Monitoring service. Have a look at the [tutorial](https://cloud.google.com/stackdriver/docs/solutions/gke/prometheus).
