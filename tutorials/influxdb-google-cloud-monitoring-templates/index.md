---
title: Monitoring Google Cloud with InfluxDB Templates
description: Deploy a Google Cloud Monitoring solution quickly with InfluxDB templates.
author: gunnaraasen,chobbs
tags: Google Compute, Google Cloud SQL, Google Load Balancers, monitoring, time series, database, metrics, dashboard
date_published: 2020-10-16
---

Gunnar Aasen | Product Manager | InfluxData

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Google Cloud allows businesses of all types to modernize their workloads on a world-class infrastructure and help them drive better decision-making with intelligent analytics. Monitoring your Google Cloud infrastructure can help you ensure your technology is properly aligned with your goals as a business.

InfluxDB Templates let users build and share comprehensive monitoring solutions for any technology in one open-source text file that can be imported into InfluxDB with a single command. Once the templated monitoring solution is installed, it is easy to modify the dashboards and configurations to meet your specific needs.

The Google Cloud Monitoring template for InfluxDB, provides a comprehensive view across your entire Google Cloud environment, containers, applications and microservices. On install it provides pre-built and customizable dashboards to monitor:

- Google Cloud SQL instances
- Google Compute instances
- Google Load Balancers

You can combine this with the Kubernetes template to get even more visibility into your GKE instances as well as any metrics you may have from other environments to get visibility across hybrid environments.

## Objectives

1. Set up InfluxDB Cloud on Google Cloud.
2. Install Google Cloud Monitoring template for InfluxDB.
3. Launch Google Cloud Monitoring solution.  Just a few of the key Google Cloud monitoring metrics to monitor using the template include:
    - Basic status, including reserved cores, current state, and uptime.
    - Database server hardware utilization, including CPU utilization and memory utilization
    - Pages read/written
    - Sent/received rate
    - Relative uptime
    - Instance received/sent (measured in bytes)
    - Backend latencies - mean
    - Platform - total latencies - mean

## Costs

This tutorial does not incur any costs on InfluxDB Cloud if using a Free-tier account.

This tutorial explains how to monitor existing Google Cloud resources but does not require any new resources on Google Cloud.

## Before you begin

This tutorial assumes that you're using a unix-based operating system, like MacOS.

1. Create a [free InfluxDB Cloud account](https://cloud2.influxdata.com/signup) from [InfluxData](https://www.influxdata.com/partners/google/). InfluxDB Cloud Usage-based plans can also be created through [Google Marketplace](https://console.cloud.google.com/marketplace/details/influxdata-public/cloud2-gcp-marketplace-prod?q=influxdb%20cloud&id=728e75cb-5bc4-4ee1-8bb7-2040e325e91a).
2. [Install the InfluxDB CLI](https://docs.influxdata.com/influxdb/v2.0/get-started/#optional-download-install-and-use-the-influx-cli).
3. [Install Telegraf](https://docs.influxdata.com/telegraf/latest/introduction/installation/) on your local machine with access to you GCP environment, in one of your existing GCP instances, or into a deployment if using a K8s cluster.
4. Review the [Google Cloud Monitoring Template Setup instructions](https://github.com/influxdata/community-templates/tree/master/gcp_monitoring#setup-instructions).
5. Create a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/). We recommend using an existing Google Cloud project with resources you wish to monitor.

## Tutorial body

### Create a GCP Monitoring stack in InfluxDB Cloud

1. [Generate a new token](https://docs.influxdata.com/influxdb/v2.0/security/tokens/create-token/) to be used by the Telegraf component by navigating in InfluxDB Cloud to: Load Data > Tokens > Generate Read/Write Token for your Telegraf configuration.
2. Use the token with the `influx` CLI to install the [gcp_monitoring template](https://github.com/influxdata/community-templates/tree/master/gcp_monitoring), which will create a new stack in your InfluxDB Cloud account with dashboards for GCP Monitoring.

### Configure data collection with Telegraf

1. In the InfluxDB Cloud UI, navigate to the "Data" page and then the "Telegraf" tab.
2. If the GCP Monitoring template was installed successfully, a `GCP Stackdriver` configuration will appear as a Telegraf configuration.
3. Click on `GCP Stackdriver` and copy the pre-populated Telegraf configuration, which will look roughly like this:

    ```toml
    [agent]
      interval = "1m"
      flush_interval = "10s"
      metric_buffer_limit = 50000
      debug = true
      omit_hostname = false

    [[outputs.influxdb_v2]]
    # Replace INFLUX_HOST,INFLUX_TOKEN, and INFLUX_ORG
    # with the values from your InfluxDB Cloud account
      urls = ["$INFLUX_HOST"]
      token = "$INFLUX_TOKEN"
      organization = "$INFLUX_ORG"

    [[inputs.stackdriver]]
      project = "$GCP_PROJECTNAME" #mygcpproject
      metric_type_prefix_include = [
        "compute.googleapis.com/instance/",
        "loadbalancing.googleapis.com/",
        "cloudsql.googleapis.com/database/cpu/",
        "cloudsql.googleapis.com/database/disk/",
        "cloudsql.googleapis.com/database/disk/",
        "cloudsql.googleapis.com/database/network/",
        "cloudsql.googleapis.com/database/memory/",
        "cloudsql.googleapis.com/database/mysql/",
      ]
      # metric_type_prefix_exclude = []
      interval = "5m" # the more frequency the higher impact to your GCloud bills
      rate_limit = 20
    ```

4. Replace the contents of your `telegraf.conf` configuration file with the Telegraf configuration from the InfluxDB Cloud UI. By default, the Telegraf configuration file is located in the `/etc/telegraf` directory.
5. Update the entries for `INFLUX_HOST`, `INFLUX_TOKEN`, and `INFLUX_ORG` with the proper corresponding values from your InfluxDB Cloud instance. See the guide on [manually configuring telegraf](https://docs.influxdata.com/influxdb/v2.0/write-data/no-code/use-telegraf/manual-config/) to learn where these values can be found.
6. After saving your changes, start the metric collection by starting (or restarting) the Telegraf service with the updated configuration file. Data will begin to flow to InfluxDB Cloud after a couple minutes.

    `telegraf --config /etc/telegraf/telegraf.conf`

    For Linux (sysvinit and upstart installations)

    `sudo service telegraf start`

    For Linux (systemd installations)

    `sudo systemctl telegraf start`

7. Finally, navigate to one of the pre-built GCP Monitoring dashboards in the InfluxDB Cloud UI.

![GCP Monitoring Dashboard](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/Google-Cloud-SQL-Monitoring-Dashboard.png)

> Note: If you do not have `loadbalancing` or `mysql` resources deployed you will not receive any metrics for these services and thus the corresponding dashboards will be empty.

You can also modify the pre-built dashboard layouts and underlying analysis.

 ![Edit Dashboard Reports](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-edit-dashboard-reports.png)

 ![Custom layout using various report types](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-layout-various-reports.png)

 ![Custom analysis by updating query language](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-analysis-query.png)

## Cleaning up

If you are on a usage-based plan on InfluxDB Cloud, you may be charged for collecting GCP monitoring metrics. Run the following command to shut down the Telegraf agent to stop collection of GCP metrics.

```sh
    # For Linux (sysvinit and upstart installations)
    sudo service telegraf stop

    # For Linux (systemd installations)
    sudo systemctl telegraf stop
```

To remove the GCP Monitoring resources in InfluxDB Cloud:

1. Look up the GCP monitoring stack ID via the `influx` CLI.

```sh
> influx stacks
ID			OrgID			Active	Name	Description	Num Resources	Sources											URLs	Created At				Updated At
067f6daf0752b00x	5f57bfbb27a7decx	true				7		[https://raw.githubusercontent.com/influxdata/community-templates/master/gcp_monitoring/gcp_monitoring.yml]	[]	2020-10-22 00:00:00.000000000 +0000 UTC	2020-10-22 00:00:00.000000000 +0000 UTC
```

2. Then delete the GCP monitoring stack ID.

```sh
influx stacks remove --stack-id 067f6daf0752b00x
ID			OrgID			Active	Name	Description	Num Resources	Sources											URLs	Created At				Updated At
067f6daf0752b00x	5f57bfbb27a7decx	true				7		[https://raw.githubusercontent.com/influxdata/community-templates/master/gcp_monitoring/gcp_monitoring.yml]	[]	2020-10-22 00:00:00.000000000 +0000 UTC	2020-10-22 00:00:00.000000000 +0000 UTC

Confirm removal of the stack[067f6daf0752b00x] and all associated resources (y/n): y
```

If you created any GCP resources specifically to monitor for this tutorial, they can be shut down now as well.

## What's next

- View the entire [InfluxDB Template Gallery](https://www.influxdata.com/products/influxdb-templates/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
- Learn more about [Google and InfluxDB](https://www.influxdata.com/partners/google/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
