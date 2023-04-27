---
title: Monitor HBase metrics of Dataproc cluater with HBase optional component
description: Setup monitoring dashboard using Prometheus and Grafana to monitor HBase metrics.
author: NuwanSameera
tags: dataproc, hbase
date_published: 2023-04-27
---

NuwanSameera | Technical Lead | Synergen Technology Labs (PVT) LTD

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community.</i></p>

In this tutorial, you run HBase on Dataproc cluster and setup monitoring dashboard to monitor HBase metrics using Prometheus and Grafana.

## Prerequisites

This is a followup to Using [Dataproc Clusters in GCP](https://cloud.google.com/dataproc), [HBase Optional Component](https://cloud.google.com/dataproc/docs/concepts/components/hbase) and [Dataproc Initilization Actions](https://github.com/GoogleCloudDataproc/initialization-actions/blob/master/hbase/README.md), so read that tutorials before beginning this one.

This tutorial steps describe using Google Cloud Console.

### Create Dataproc Cluster

*   Open Dataproc [Create Cluster Page](https://console.cloud.google.com/dataproc/clustersAdd?_ga=2.169589857.1553433411.1682413276-2038332095.1628251603) page in the Google Cloud console in your browser.
*   start create cluster using `CREATE CLUSTER` button.
*   Select `Cluster on Compute Engine` option from popup
*   Enter basic details of the cluster in `Set up cluster` page
*   Tick `Enable component gateway` option and add `Zookeper` and `HBase` as optional components
*   In `Customize cluster` page select initialization action script from `Cloud Storage`
*   Initialization action script content as follows

```
#!/bin/bash
wget https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.18.0/jmx_prometheus_javaagent-0.18.0.jar
mkdir /user/
mkdir /user/jmx-connector/
mv jmx_prometheus_javaagent-0.18.0.jar /user/jmx-connector/
cat > /user/jmx-connector/config.yaml << EOF
rules:
- pattern: ".*"
EOF
```

### Enable JMX ports in all master and worker nodes

* Open `/etc/hbase/config/hbase-env.sh` file using nano editor as root user. Uncomment following lines

```
export HBASE_JMX_BASE="-Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false"
export HBASE_MASTER_OPTS="$HBASE_MASTER_OPTS $HBASE_JMX_BASE -Dcom.sun.management.jmxremote.port=10101"
export HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS $HBASE_JMX_BASE -Dcom.sun.management.jmxremote.port=10102"
```

* Restart nodes

1. Master nodes : `sudo systemctl restart hbase-master`
2. worker nodes : `sudo systemctl restart hbase-regionserver`

* Check JMX ports : `netstat -lptn`

1. master nodes - port number `10101`
2. worker nodes - port number `10102`


### Configure JMX exporter java agent in all master and worker nodes

* Open /usr/bin/hbase file using nano editor as root user. Add following content before last line [1](https://github.com/prometheus/jmx_exporter)

``` 
if [ `netstat -lptn | grep ':7000' | wc -l` -eq "0" ]; then
  export HBASE_OPTS="$HBASE_OPTS -javaagent:/user/jmx-connector/jmx_prometheus_javaagent-0.18.0.jar=7000:/user/jmx-connector/config.yaml"
  fi
```

* This will bind jmx_prometheus_javaagent to HBase and expose JMX metrics to port 7000
* Restart master and worker nodes.
* Check port `7000` is open using `netstat -lptn`
* Port forward 7000 t local machine using gcloud compute ssh node_name --tunnel-through-iap -- -L 7000:127.0.0.1:7000
* Browse http://localhost:7000/metrics and check metrics are received or not

### Setup Prometheus and Grafana 

* [2](https://godatadriven.com/blog/monitoring-hbase-with-prometheus/)
* Create VM instance to monitoring tools
* Install [Prometheus](https://devopscube.com/install-configure-prometheus-linux/) following
* At Setup Prometheus Configuration Step 2. Need to add all master and worker DNS:7000 to targets. This connect to jmx_prometheus_javaagents in all worker and master nodes and collect metrics to Prometheus

```
global:
  scrape_interval: 10s

scrape_configs:
  - job_name: 'prometheus'
    scrape_interval: 5s
    static_configs:
      - targets: ['m1-vm-name.c.project-id.internal:7000',.. 'mn-vm-name.c.project-id.internal:7000', 'w1-vm-name.c.project-id.internal:7000',.. 'wn-vm-name.c.project-id.internal:7000']
```

* After configuration complete Prometheus will start on port 9090
* Port forward monitoring vm port 9090 to local machine using gcloud compute ssh node_name --tunnel-through-iap -- -L 9090:127.0.0.1:9090
* Browse http://localhost:9090/
* Open Status -> Targets tab. It will show all the connected targets at Prometheus Configuration Step 2. All nodes should in Up state


* Install [Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/). (Use latest stable version)
* After configuration complete Grafana start on port 3000
* Port forward monitoring vm port 9090 to local machine using gcloud compute ssh node_name --tunnel-through-iap -- -L 30000:127.0.0.1:3000
* Browse http://localhost:30000/

### Create Dashboard and Graphs to monitor HBase stats

* Login to Grafana dashboard using default username and password
* Change password after login
* Create Datasource with Prometheus
* Configuration -> Data Sources -> Prometheus
* Set HTTP URL as http://localhost:9090
* Add graphs using required metrics
* Dashboard -> Add Panel -> Select Data Source as Prometheus -> Select HBase metric -> Click Run Query button -> Save Graph to Dashboard

* All the [HBase metrics](https://hbase.apache.org/book.html#hbase_metrics) available in Grafana dashboard.

