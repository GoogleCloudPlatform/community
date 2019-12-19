---
title: Using Prometheus and Grafana for IoT monitoring
description: This tutorial walks you through setting up a running stack for IoT monitoring using Prometheus and Grafana with integrations with Cloud IoT Core.
author: ptone
tags: IoT, Internet of Things, monitoring, prometheus
date_published: 2019-03-09
---

Preston Holmes | Solution Architect | Google Cloud

# Using Prometheus and Grafana for IoT monitoring

This tutorial walks you through setting up a running stack for IoT monitoring using Prometheus and Grafana with integrations
with Cloud IoT Core. For a more thorough discussion of the background and concepts, see
[Remote monitoring and alerting for IoT](https://cloud.google.com/solutions/remote-monitoring-and-alerting-for-iot).

## Objectives

*   Deploy Prometheus and Grafana in Google Kubernetes Engine (GKE).
*   Examine sample dashboards and Prometheus queries to understand how these tools relate to IoT monitoring use-cases.
*   Deploy a Cloud Function that responds to alerts.

## Introduction

Although telemetry data from devices may be used for both short-term and long-term use-cases, the tools supporting
shorter-term monitoring and longer-term analytics are generally specific to the task. Operational monitoring over minutes,
hours, and days requires different tools than you may use with the same telemetry data over months and years.

The open source toolkit [Prometheus](https://prometheus.io/) is built to ingest and query this type of monitoring data. 
Originally developed at SoundCloud and now [part](https://www.cncf.io/announcement/2016/05/09/cloud-native-computing-foundation-accepts-prometheus-as-second-hosted-project/)
of the [Cloud Native Computing Foundation](https://www.cncf.io/), Prometheus is typically used to monitor software
and services deployed in infrastructure fabric like Kubernetes. The underlying time-series database is
[optimized](https://fabxc.org/tsdb/) for storing millions of series and is designed for very fast writes and queries. This
design is well suited for the types of monitoring tasks you may want to perform with data coming from IoT devices.

[Grafana](https://grafana.com/) is a popular open source dashboard and visualization tool with support for Prometheus as a
data source. In this tutorial, we will work through some sample dashboards as well as use it as the place to look at metrics 
queries.

![architecture figure](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-prometheus-monitoring/architecture.png )

While some simple threshold alerts can be performed by a serverless function reacting to individual telemetry messages,
other scenarios require more complex time-series expressions, alerting policies, and graphs to aid those involved in 
managing a large fleet of devices.

Because this tooling is optimized around monitoring, the data in it should be considered more ephemeral, not as the durable
archive of your important analytical data which you may use for things such as usage trends over a year or training machine
learning models based on many occurrences of certain behaviors or patterns.

In version 2 of Prometheus, improvements were made to support the more ephemeral nature of container-based services, which 
cause higher churn of different series. As a result, Prometheus is now more capable of this kind of approach to device 
debugging.

## Setting up the workbench

We recommend that you perform these setup steps in the Cloud Shell environment.

### Clone the tutorial repository

```
git clone https://github.com/GoogleCloudPlatform/community.git
cd community/tutorials/cloud-iot-prometheus-monitoring
```

### Enable APIs

```
gcloud services enable compute.googleapis.com cloudiot.googleapis.com pubsub.googleapis.com cloudfunctions.googleapis.com container.googleapis.com
```

Enabling the APIs may take a few minutes.

### Set environment variables

```
export GCLOUD_PROJECT=$(gcloud config get-value project)

export CLOUD_REGION=us-central1 # or change to an alternate region;

export CLOUD_ZONE=us-central1-a

```

### Create cluster

```
gcloud beta container --project $GCLOUD_PROJECT clusters create "monitoring-demo" \
--zone $CLOUD_ZONE --username "admin" \
--cluster-version "1.10" --machine-type "n1-highmem-2" \
--image-type "COS" --disk-type "pd-standard" --disk-size "100" \
--scopes "cloud-platform","https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
--num-nodes "2" --enable-cloud-logging \
--enable-cloud-monitoring --enable-ip-alias \
--addons HorizontalPodAutoscaling,HttpLoadBalancing,KubernetesDashboard \
--no-enable-autoupgrade --enable-autorepair
```

### Create Cloud Pub/Sub topic and subscriptions for IoT Core

```
gcloud pubsub topics create metricdata
gcloud pubsub subscriptions create metric-pull --topic metricdata
```

###  (Optional) Set up an OAuth credential to allow Google login to Grafana

You can enable Google login to the deployed Grafana dashboard. To do this takes a couple of setup steps. Google login 
requires the site to be hosted at a valid domain name, with HTTPS enabled. The fastest way to do this for a tutorial is to
use a web proxy hosted on App Engine. In production, you would instead set up a
[load balancer](https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer) with a custom domain and Transport Layer Security (TLS).

In the console, choose **APIs & Services > Credentials > OAuth consent screen**.

#### Set values on the consent screen

*   Name: `iot-monitor`
*   Authorized domain: `[project-id].appspot.com`

#### Create OAuth client ID

1.  Create a credential of type `web`.
1.  Name it `grafana-login`.
1.  Add an authorized redirect URI:

        https://[project-id].appspot.com/login/google

1.  Edit the OAuth values in `iotmonitor-chart/values.yaml` with the client ID settings.
1.  In `iotmonitor-chart/values.yaml`, update the server `root_url` for Grafana to this:

        https://[project-id].appspot.com/

### (Optional) Set up Stackdriver data source

Grafana supports [Stackdriver](https://cloud.google.com/stackdriver/) as a built-in data source. This can be provisioned 
automatically as part of the setup, or manually added later.

To automate the setup of Stackdriver, you need to create a service account. Follow the
[instructions](http://docs.grafana.org/features/datasources/stackdriver/) from Grafana to create a service account with the
correct permissions.

Add the values from the downloaded JSON keyfile to the `clientEmail` and `privateKey` parts
of `iotmonitor-chart/values.yaml`.

You will also need to change some additional values in the chart's `values.yaml` for your project:

```
datasources:
    datasource.yaml:
        name: Stackdriver
            jsonData:
                defaultProject: [project-id]

grafana.ini:
    server:
        root_url: https://[project-id].appspot.com
```

Install [Helm](https://github.com/kubernetes/helm) in your Cloud Shell. The instructions below assume that you are starting
from this tutorial's root level: `$HOME/community/tutorials/cloud-iot-prometheus-monitoring`

```
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.12.0-linux-amd64.tar.gz
tar -xzvf helm-v2.12.0-linux-amd64.tar.gz
mv linux-amd64/helm $HOME/bin/

# Be sure you have the current cluster credentials
gcloud container clusters get-credentials monitoring-demo --zone $CLOUD_ZONE --project $GCLOUD_PROJECT

# add helm service account and rbac policy
kubectl apply -f helm-rbac.yaml

# install the helm "tiller" daemon
helm init --service-account helm
```

### Deploy the Prometheus and Grafana chart combination

```
cd iotmonitor-chart
helm dep up
helm install --name iotmonitor .
```

Wait for the ingress service to have an IP address

```
kubectl get service iotmonitor-grafana -o jsonpath={.status.loadBalancer.ingress[0].ip}
```

Make a note of this IP address. You will be injecting it into the source code for a simple proxy.

Get the Grafana admin password:

```
kubectl get secret --namespace default iotmonitor-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

### Deploy the Grafana web proxy

For Google Auth to work with Grafana, we need a valid domain and TLS. For this tutorial, we will set up a 
simple proxy in App Engine that allows us to have that quickly, but in production you would set up Grafana with a proper GKE
ingress-managed load balancer and a proper cert on your own domain.

Edit the source at `web-proxy/proxy.go` to include the private IP of the internal load balancer of the Grafana service.

Deploy the proxy:

```
cd ../web-proxy
gcloud app deploy
```

Choose the same region as your cluster.

## Introduction to the simulated data

This tutorial focuses on the use of the monitoring tools of Prometheus and Grafana. To facilitate this exploration, the
above steps have also deployed a device simulator. This simulator does not exercise the full architecture, but instead 
exposes simulated data directly to be scraped by Prometheus. The simulated data is from a set of imagined devices
installed in different cities across North America. These devices have a temperature sensor, a light sensor, and a
panel access door that has a sensor. These basic metrics are then used in queries and dashboards to illustrate the use
of Prometheus and Grafana.

## Using Grafana

A Grafana instance was deployed as part of this stack. By default it has been configured to support login with any Google 
account. You can limit this to a specific [G Suite](https://gsuite.google.com) domain by changing the values in the Helm 
chart used earlier. In this tutorial, Grafana is exposed with a simple App Engine base reverse proxy. This gives us HTTPS at
a domain name, which is a requirement of the Google login Grafana plugin. In production, you would replace this with a
proper ingress object associated with a load balancer.

Earlier, you retrieved the admin password from the Kubernetes secret. You can reach the Grafana login screen by
going here:

```
https://[project-id].appspot.com/
```

Log in as admin.

Grafana has already been configured with a data source, but you need to import the sample dashboards. 

**Note**: If you are working in a Cloud Shell environment, you may find it easier to make an additional clone (or download
the zip file) of the repository to your local machine for upload.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-prometheus-monitoring/grafana.png)

Click **Upload .json File** and locate the tutorial folder in the dashboards folder.

Pick the **Device Detail View...** file and import it. In the next dialog, you may need to choose **Prometheus** as the
data source.

Repeat the same steps for the **Region Dashboard**.

You will now review the queries that form the basis of these dashboards.

### Cautions when summarizing data visually

The goal of using a tool like Grafana with time series queries is to make information more readily interpretable by users.
However one must be careful to capture information in ways that do not obscure important take-aways.

Anscombe famously [showed](https://en.wikipedia.org/wiki/Anscombe%27s_quartet) how very different data distributions could 
result in identical statistical summaries.

A team at Autodesk Research has shown how this risk also
[extends to visualizations such as box plots](https://www.autodeskresearch.com/publications/samestats).

## PromQL syntax with IoT use case examples 

### Queries

A complete introduction to Prometheus Query Language or PromQL is beyond the scope of this tutorial. Instead, we focus on 
how PromQL can be applied to a set of IoT monitoring use-cases. For introductions to PromQL see
[this post](https://timber.io//blog/promql-for-humans/), and the
[official documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/).

### Device Detail dashboard

Go to the dashboard list view:
`https://[project-id].appspot.com/dashboards`

Choose **Device Detail View**.

Both sample dashboards take advantage of Grafana [template variables](http://docs.grafana.org/reference/templating/), which
allow a drop-down to apply the dashboard to a specific device or region.

By default, the "albuquerque-0" simulated device is selected.

Let's start with the temperature Graph. To see the queries that generate this dashboard element, click the small triangle
next to the panel's title and choose **Edit**.

![alt_text](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-prometheus-monitoring/temperature.png)

First notice that there are two queries. Each query draws a line in the graph. Let us start with the simpler, second one:

```
room_external_temp{instance="$device_id"}
```

Since the data source is Prometheus, this query is in PromQL. Let's break this down.

`room_external_temp` is the metric name. By convention, we assume that the unit is Celsius. Depending on your practices, it
is often a good idea to capture the units of the metric in the metric name. See Prometheus documentation
on [naming metrics](https://prometheus.io/docs/practices/naming/) for more discussion.

The part of the query inside the curly braces `{}` are selectors to filter the metric. In this case, we want measurements
that match the label for `instance` that equals the currently selected template drop-down.

The `$device_id` variable is expanded by Grafana before it is passed to Prometheus as follows:

```
room_external_temp{instance="albuquerque-0"}
```

This example uses a Prometheus configuration setting `honor_labels: true` in `prometheus.yml` so that `instance`, which is
commonly used in queries as the source of the metric data, is preserved as originally provided by the device, and not
replaced by the instance of the Kubernetes pod/node that provided it by scraping.

This type of query is referred to as an _instant vector_, since it retrieves one value per selector match that shares a
time-stamp. There are other settings in the adjacent Grafana gauge panel to limit this to the instant or latest value, but
the query actually returns the series of instant values, which are displayed as a yellow line in the graph.

The other query in this panel is this:

```
avg_over_time( room_external_temp{instance="$device_id"}[15m])
```

This adds two elements to the query. The first is the `[15m]` following the selector, which turns this into a range vector.
For each point in time, the range vector holds an array of 15m of values. The other is the `avg_over_time`, which is a 
function in PromQL applied to this group of measurements.

Click the **Return to Dashboard** button in the top right and look next at the query behind the **Message Data Rate** panel:

```
rate(device_msgs_total{instance="$device_id"}[10m]) * 60
```

This query demonstrates how to use the rate function to calculate a rate from a counter. Counters are a more flexible way of
looking at change over time, than calculating rates locally on the device, and then sending that value. Here we can see that
we calculate the rate over a 10-minute period. If we wanted instead to look at the per-second rate over an hour, we could
use the same counter.

Because rates are inherently calculated as per-second values, the result is multiplied by 60 to give us a per-minute value.

Finally, let's look at the last panel, **Luminance Predictions**.

The yellow dots are a plot of this simple metric:

```
room_luminance{instance="$device_id"}
```

The green line is a prediction of the value using linear regression:

```
predict_linear(room_luminance{instance="$device_id"}[15m], 300   )
```

This function takes a range vector, in this case the past 15m of the luminance value, and uses that to predict the value
for some time into the future.

The dashboard time range has been set to show now+5m. It
is [not currently possible](https://github.com/grafana/grafana/issues/10395) to set this offset only for this one panel.

With this offset, you will see the green line extending into the future. The flat-lining of the yellow dots represents that
Prometheus values for this gauge are assumed to stay the same as the current value if no prediction is applied.

There is some trial and error to find predictions that are useful with this technique. Obviously, it will not work to try
to predict an hour in the future based on the last one minute of data.

### Region dashboard

For some diagnostics, it may be useful to review a single device, but it is more often useful to look at data in an
aggregate form.

If you look at the provided "Region Dashboard" sample. You can see that we use two template variables to select a group of
devices, regions, and firmware versions.

To select these devices, we use a technique called _info blocks_
or [_machine roles_](https://www.robustperception.io/how-to-have-labels-for-machine-roles). The idea is to use a dummy
gauge to hold a set of metadata related to a device, instead of needing to repeat these on each metric.

PromQL then supports a join function to look up matching devices based on this metadata. 

Look at the device count panel:

```
count(device_boot_time* on (instance) group_left(region, firmware)  device_info{region="$region", firmware=~"$firmware"}) 
```

Here, `device_info` is the dummy gauge, always just set to one. You can see that we are selecting this gauge based on the
Grafana template values.

These two labels are used to `group_left` join on other metrics, for which we want (`on`) the instance. The metric
is `device_boot_time` but in this case the value is not relevant for the metric, as all we are doing using `count` to count
all devices that have a boot time greater than 0 (which is all devices).

This gives a count of all of the devices in the region that match the region and firmware.

In order to get the **All** option to work for firmware, a few things are needed:

 - Select **All** in the dashboard's variable settings
 - Set a custom value for the option of `.*`
 - Use the pattern match operator in the info-block selector of `=~`

As all of the panels use this approach, only the uses of other PromQL features are described.

**Hottest Devices**

```
topk(3, room_external_temp ...
```

The `topk` function sorts and limits a result. This example shows the three hottest places. Note that as the ranking evolves
over time, the graph is colored and the legend supports displaying past ranked places as well as the current hottest places.

**Longest Running Devices**

```
topk(5, time() - device_boot_time ...
```

Uses the `time()` function for `now` to select the top five longest-running devices. `device_boot_time` is a gauge that
is set to UNIX timestamp at startup.

**Devices with Lid Open**

```
sum without (instance, firmware) (lid_open_status ...
```

The `sum` function groups by each unique set of labels in the result across the series. Here you only want to sum for the
region by excluding the instance and firmware labels by using `without`.


**Temperature Distribution**

The **Temperature Distribution** panel shows how to use Grafana's support for dashboard-side histograms and heatmaps.

```
topk(10, changes(device_boot_time[1h])
```

Prometheus also supports a [histogram](https://prometheus.io/docs/practices/histograms/) type directly for metrics. 

**Crashing Devices**

```
topk(10, changes(device_boot_time[1h]) 
```

The `changes` function looks for sudden jumps to the value of a gauge. This can be used to track the number of times a 
device reboots in an hour. For this demo, our simulated devices reboot 8 times per hour on average. If you use the dashboard
selectors to choose **Massachusetts** as the region, you will see that one device is crashing much more frequently, and the
dashboard uses conditional formatting to show this as red. 

## Sending metrics from an IoT device

The workbench we have been using to look at different ways to query and visualize time series data has used purely synthetic
data. This has been done in a container running adjacent to Prometheus. Prometheus is designed
around [pull instead of push](https://prometheus.io/docs/introduction/faq/#why-do-you-pull-rather-than-push?) metric 
collection. Given that IoT devices will be remote from the Prometheus server, and not possible to scrape directly, how do
we get data from a device into Prometheus? Prometheus supports
a [push gateway](https://prometheus.io/docs/instrumenting/pushing/), but it is more intended for ephemeral jobs, not
long-running operational information like that which might be coming from devices. Instead, we want to tunnel metrics over 
the Cloud IoT Core MQTT telemetry channels. We will cover a couple of ways to do this, both of them using a client library 
approach to building metrics.

### Extracting metrics from payloads

The first approach is to simply send measurements in any format you want over MQTT and convert these to metrics by a
specialized converter. The converter needs to know how each sensor value is best represented into a Prometheus metric.
The firmware author does not need to know about the use of these values in the monitoring context. These values can be
easily consumed for other uses.

![Extract from payloads](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-prometheus-monitoring/extractor.png)

### Using Promiot to instrument an IoT device

Prometheus is based on a pattern of scraping applications and services directly for their metrics, and providing a central
place to query and aggregate them. This works well for the common case where these are deployed in the same infrastructure 
fabric as the Prometheus server. Prometheus provides several options to support situations where the applications are not 
natively instrumented with Prometheus instrumentation libraries. This includes exporters to adapt systems that provide 
metrics in another format, and a push gateway for systems that are designed to report directly which ephemeral or batch
jobs that are hard to scrape as stable targets can report metrics.

Scraping many remote IoT devices is not possible or practical for a monitoring system like Prometheus, so a different 
pattern is needed.

[Promiot](https://github.com/ptone/promiot) is an open source library that allows a device to use the Prometheus client
libraries directly on the device. It does this by locally scraping the metrics, then sending a serialized version of the
metrics over MQTT, where a receiver unserializes and exposes them to the Prometheus server, without needing to know anything
about the contents or how to convert them. This has the benefit that integrating the Prometheus client libraries with
sensor reading is intuitive, and the firmware author can focus on instrumentation, as Promiot handles all communication with
Cloud IoT Core.

![Using Promiot library](https://storage.googleapis.com/gcp-community/tutorials/cloud-iot-prometheus-monitoring/promiot.png)

### Caveats of this approach

Using these techniques is not without some caveats:

*   Prometheus assigns timestamps to metrics at the time they are scraped. There will be latency between the device and
    the Prometheus server. Promiot measures and reports this latency as its own metric.
*   Depending on the way a converter or Promiot is configured, it can can continue to expose stale metrics to be scraped
    by the Prometheus Server.
*   Many devices will route telemetry onto a single Cloud Pub/Sub topic. The converter or receiver can only be a
    singleton process, because there is no way to route messages from a specific set of devices in a sticky way to a node
    of a cluster of receivers. While the point at which scaling becomes an issue given this design depends on the number
    of metrics and series collected, it should support up to 10,000 devices typically. At some point, the system will need
    to be functionally sharded. Prometheus itself needs to be sharded at some point, as well.

These caveats are accepted, noting that the objective is to get the data into Prometheus, which affords the best-in-breed 
capabilities for queries with PromQL as illustrated above. This is also not meant to be a system for events or logs or
long-term analytics storage.

## Alerting

As noted in
[Remote monitoring and alerting for IoT](https://cloud.google.com/solutions/remote-monitoring-and-alerting-for-iot),
alerting often helps in drawing your attention in a timely manner to metrics that indicate some incident.

The Prometheus [Alertmanager](https://prometheus.io/docs/alerting/overview/) is available as a separate component and
running process, separate from the Prometheus metrics engine. Prometheus is configured with alert reporting rules, which 
send matching metrics to the Alertmanager.

Alerts move through the following states in order: inactive, pending, firing.

Pending alerts have a matching condition, but have not sustained that condition long enough to reach the 
rule's prescribed threshold. This is key to reducing noise from conditions that can vary transiently but are not worth
alerting about on a single recorded value.

The Prometheus Alertmanager design connects three main parts: alerts, routes, and receivers.

Alerts are defined by [alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/),
which can be grouped.

The chart that you deployed contains two preconfigured alerting rules:

```yaml
    alerts:
      groups:
        - name: device_alerts
          rules:
          - alert: LidLeftOpen
            expr: (time() - (lid_open_start_time *  lid_open_status)) > 900 and (time() - (lid_open_start_time *  lid_open_status)) < 9000
            for: 30s
            labels:
              severity: page
              system: mechanical
            annotations:
              summary: "Lid open on {% verbatim %}{{ $labels.instance }}{% endverbatim %}"
              description: "Lid has remained open for more than 15 minutes on {% verbatim %}{{ $labels.instance }}{% endverbatim %}"
          - alert: DeviceRebooting
            expr: changes(device_boot_time[1h]) > 20
            for: 2m
            labels:
              severity: debug
              system: software
            annotations:
              summary: "{% verbatim %}{{ $labels.instance }}{% endverbatim %} rebooting"
              description: "{% verbatim %}{{ $labels.instance }}{% endverbatim %} has been rebooting more than 20 times an hour"
```

We can see in these rules the Prometheus query to run, along with threshold time required for the alert to fire.

The rule labels in the rule can be used by the alert processing logic to determine how to route different alerts to 
different receivers.

In this sample, we let all alerts flow through a default route, and the default route sends all messages to a default 
receiver.

Prometheus supports a number of different types of receivers, but the most flexible is
the [webhook receiver](https://prometheus.io/docs/alerting/configuration/#webhook_config).

You will now deploy a very simple alert receiver as a Cloud Function:

```
cd alert-function
gcloud beta functions deploy handle_alert --runtime python37 --trigger-http
```

We need to update the Prometheus configuration with the URL of the deployed function. You can get this from the command line 
where you deployed the function, or look it up in the GCP Console. It willlook something like this:

```
https://us-central1-[project-id].cloudfunctions.net/handle_alert
```

Go into the [config maps section](https://console.cloud.google.com/kubernetes/configmap) of the GKE console and
edit the `yaml` for the `iotmonitor-prometheus-alertmanager` configuration, finding the URL
`http://example.com/willbe404/` and replacing it with the one for your function.

**Note**: Because this is a publicly accessible Cloud Function, you should add a level of security in production by setting 
a shared secret in the Prometheus [HTTP config](https://prometheus.io/docs/alerting/configuration/#http_config) of the 
receiver as a bearer token, and verify that secret is correct inside the Cloud Function.

You can verify that the alerts that are firing are being sent to this Cloud Function by looking at the Cloud Function logs
in the console.

## Using a Stackdriver data source

If you followed the optional setup instructions, you should have a functioning Stackdriver data source. You can import the 
`stackdriver-example` sample dashboard provided in this repository to see a few ways to use this integration.

You can also follow the setup instructions from Grafana to add Stackdriver via the Grafana UI now. You will need to choose
a different data source name, and choose this data source when you import the sample dashboard.

For IoT monitoring, the primary value of this integration is to be able to
include [IoT Core metrics](https://cloud.google.com/monitoring/api/metrics_gcp#gcp-cloudiot) directly into your dashboards.

## Inserting Google Sheets

It may be useful to include some information collaboratively edited in Google Sheets directly inside a dashboard.

The Text graph type supports HTML, and we can use that to embed an iFrame of a Google sheet.

While you can embed an iFrame for the complete edit view URL if you want the full editor chrome, you have a few other
choices.

Assuming a standard edit URL like the following, you can choose
[**Publish to Web**](https://support.google.com/docs/answer/183965?co=GENIE.Platform%3DDesktop&hl=en),
which will make the document public and will automatically create the `iframe src` code for you if you choose to embed it:

```
https://docs.google.com/spreadsheets/d/1FvwKEqVbnY1k3ZfQ3SJNLr-CAb3U_3bIOIFe_XE2wGY/edit#gid=0
```

If you want to keep the document private to your shared recipients or a
[group](https://support.google.com/a/answer/167101?hl=en), you can use a special URL to get the content.
Replace `edit#gid=0` in the URL with `htmlembed?single=true&gid=0&widget=false&chrome=false`. You can also
add `range=f2:g6` if you want to further restrict to a specific range.

The easiest way to refresh this is to right-click in Chrome and choose and **Reload Frame**, but this could also be 
achieved with a clever bit of Javascript and a button.

You can also add `&kiosk` to the Grafana dashboard itself to get your dashboard to display without all of the Grafana editor 
chrome.

## Next steps

*   Use a custom domain with a load balancer and GKE ingress to replace the App Engine proxy.
*   Set up [Thanos](https://github.com/improbable-eng/thanos) for longer data retention and archives.
*   Use Prometheus [Remote Storage Adapter](https://github.com/prometheus/prometheus/tree/master/documentation/examples/remote_storage/remote_storage_adapter)
    to also write data to [OpenTSDB backed by Cloud Bigtable](https://cloud.google.com/solutions/opentsdb-cloud-platform).
