---
title: Monitoring Google Cloud with InfluxDB templates
description: Deploy a Google Cloud Monitoring solution quickly with InfluxDB templates.
author: gunnaraasen,chobbs
tags: Google Compute, Google Cloud SQL, Google Load Balancers, monitoring, time series, database, metrics, dashboard
date_published: 2020-11-10
---

Gunnar Aasen | Product Manager | InfluxData

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

Google Cloud allows businesses of all types to modernize their workloads on world-class infrastructure and help them to drive better decision making with 
intelligent analytics. Monitoring your Google Cloud infrastructure can help you to ensure that your technology is properly aligned with your goals as a business.

InfluxDB templates let you build and share comprehensive monitoring solutions for any technology in one open-source text file that can be imported into InfluxDB
with a single command. After the templated monitoring solution is installed, you can modify the dashboards and configurations to meet your specific
needs.

The Google Cloud Monitoring template for InfluxDB, provides a comprehensive view across your entire Google Cloud environment, containers, applications, and 
microservices. It provides pre-built and customizable dashboards to monitor the following:

- Cloud SQL instances
- Compute Engine instances
- Cloud Load Balancing instances

Some of the metrics that you can monitor using the template include the following:

  - Basic status, including reserved cores, current state, and uptime
  - Database server hardware utilization, including CPU utilization and memory utilization
  - Pages read and written
  - Sent and received rates
  - Relative uptime
  - Instance received and sent (measured in bytes)
  - Backend latencies (mean)
  - Platform total latencies (mean)

You can combine this with the Kubernetes template to get even more visibility into your GKE instances, as well as any metrics that you may have from other 
environments to get visibility across hybrid environments.

## Objectives

1. Set up InfluxDB Cloud on Google Cloud.
2. Install the Google Cloud Monitoring template for InfluxDB.
3. Start the Google Cloud Monitoring solution.

## Costs

This tutorial does not incur any costs on InfluxDB Cloud if using a Free-tier account.

This tutorial explains how to monitor existing Google Cloud resources but does not require any new resources on Google Cloud.

## Before you begin

This tutorial assumes that you're using a Unix-like operating system, such as Linux or macOS.

1.  Create a [free InfluxDB Cloud account](https://cloud2.influxdata.com/signup) from [InfluxData](https://www.influxdata.com/partners/google/).

    You can also create InfluxDB Cloud usage-based plans through
    [Google Marketplace](https://console.cloud.google.com/marketplace/details/influxdata-public/cloud2-gcp-marketplace-prod?q=influxdb%20cloud&id=728e75cb-5bc4-4ee1-8bb7-2040e325e91a).
    
1.  [Install the InfluxDB CLI](https://docs.influxdata.com/influxdb/v2.0/get-started/#optional-download-install-and-use-the-influx-cli).
1.  [Install Telegraf](https://docs.influxdata.com/telegraf/latest/introduction/installation/) on your local machine with access to you Google Cloud environment,
    in one of your existing Google Cloud instances, or into a deployment if using a Kubernetes cluster.
1.  Review the
    [Google Cloud Monitoring template setup instructions](https://github.com/influxdata/community-templates/tree/master/gcp_monitoring#setup-instructions).
1.  Create or select a Google Cloud project in the [Cloud Console](https://console.cloud.google.com/). We recommend using an existing Google Cloud project with
    resources that you want to monitor.

## Create a Google Cloud Monitoring stack in InfluxDB Cloud

1.  [Generate a new token](https://docs.influxdata.com/influxdb/v2.0/security/tokens/create-token/) to be used by the Telegraf component by navigating in 
    InfluxDB Cloud to **Load Data** > **Tokens** > **Generate Read/Write Token** for your Telegraf configuration.
1.  Use the token with the `influx` command-line interface to install the
    [Google Cloud Monitoring template](https://github.com/influxdata/community-templates/tree/master/gcp_monitoring), which creates a new stack in your InfluxDB 
    Cloud account with dashboards for Google Cloud Monitoring.

### Configure data collection with Telegraf

1. In the InfluxDB Cloud UI, navigate to the **Data** page, and select the **Telegraf** tab.
2. If the Google Cloud Monitoring template was installed successfully, a `GCP Stackdriver` configuration appears as a Telegraf configuration.
3. Click `GCP Stackdriver` and copy the pre-populated Telegraf configuration, which should look something like this:

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

1.  Replace the contents of your `telegraf.conf` configuration file with the Telegraf configuration from the InfluxDB Cloud UI. By default, the Telegraf 
    configuration file is located in the `/etc/telegraf` directory.
1.  Update the entries for `INFLUX_HOST`, `INFLUX_TOKEN`, and `INFLUX_ORG` with the corresponding values from your InfluxDB Cloud instance. See the guide on
    [manually configuring Telegraf](https://docs.influxdata.com/influxdb/v2.0/write-data/no-code/use-telegraf/manual-config/) to learn where to find these 
    values.
1.  After saving your changes, start the metric collection by starting (or restarting) the Telegraf service with the updated configuration file:

        telegraf --config /etc/telegraf/telegraf.conf

    Linux SysVinit and Upstart:

        sudo service telegraf start

    Linux Systemd:

        sudo systemctl telegraf start
        
    Data will begin to flow to InfluxDB Cloud after a couple of minutes.

1.  Navigate to one of the pre-built Google Cloud Monitoring dashboards in the InfluxDB Cloud UI.

    ![Google Cloud Monitoring Dashboard](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/Google-Cloud-SQL-Monitoring-Dashboard.png)

    **Note**: If you do not have `loadbalancing` or `mysql` resources deployed, you won't receive any metrics for these services, so the corresponding dashboards
    will be empty.

You can also modify the pre-built dashboard layouts and underlying analysis.

 ![Edit Dashboard Reports](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-edit-dashboard-reports.png)

 ![Custom layout using various report types](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-layout-various-reports.png)

 ![Custom analysis by updating query language](https://storage.googleapis.com/gcp-community/tutorials/influxdb-google-cloud-monitoring-templates/GCP-analysis-query.png)

## Cleaning up

### Shut down the Telegraf agent

If you are on a usage-based plan on InfluxDB Cloud, you may be charged for collecting Google Cloud Monitoring metrics. 

To stop collection of Google Cloud metrics, stop the Telegraf agent:

  * Linux SysVinit and Upstart:
  
        sudo service telegraf stop

  * Linux Systemd:
  
        sudo systemctl telegraf stop

### Remove the Google Cloud Monitoring resources in InfluxDB Cloud

1.  Look up the Google Cloud Monitoring stack ID with the `influx` command-line interface:

        influx stacks
        
    In the output, the stack ID appears in the first column. For example:
    
    
        ID                  OrgID               Active  ...
        067f6daf0752b00x    5f57bfbb27a7decx    true    ...

1.  Use the stack ID to delete the Google Cloud Monitoring stack:

        influx stacks remove --stack-id 067f6daf0752b00x

    When prompted to confirm removal of the stack and all associated resources, enter `y` to agree.

If you created any Google Cloud resources specifically to monitor for this tutorial, shut them down, too.

## What's next

- View the [InfluxDB Template Gallery](https://www.influxdata.com/products/influxdb-templates/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
- Learn more about [Google and InfluxDB](https://www.influxdata.com/partners/google/?utm_source=partner&utm_medium=referral&utm_campaign=2020-10-20_tutorial_influxdb-templates_google&utm_content=google)
