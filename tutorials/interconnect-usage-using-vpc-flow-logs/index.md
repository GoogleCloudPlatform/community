---
title: Use VPC Flow Logs to monitor Cloud Interconnect usage
description: Learn how to analyze information from VPC Flow Logs to estimate the amount of Cloud Interconnect usage by different projects.
author: manokhina
tags: VLAN attachments
date_published: 2021-02-22
---

Anastasiia Manokhina | Strategic Cloud Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>
 
This tutorial shows you how to analyze VPC Flow Logs to estimate the amount of Interconnect attachment usage by different projects and instances. 
This data can be used to calculate how much to charge the business units that use the Interconnect connections. This technique can be used by a network 
administrator who administers the *landing zone*, an environment that has been provisioned and prepared to host workloads in the cloud.

VPC Flow Logs captures different flows to and from VMs; this tutorial focuses on those that involve egress traffic through Interconnect connections, shown by red 
arrows in the diagram below. Only egress traffic from the VPC network toward Cloud Interconnect is chargeable, unless there is a resource that is processing 
ingress traffic, such as a load balancer.

![image](https://storage.googleapis.com/gcp-community/tutorials/interconnect-usage-using-vpc-flow-logs/diagram.png)

This tutorial assumes that you're familiar with VPC networks, Cloud Logging, and BigQuery.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

-  BigQuery
-  VPC Flow Logs
-  Compute Engine VM instances
-  VPC egress traffic 

For large volumes of traffic, you can reduce the size of logs by using [different sampling rates](https://cloud.google.com/vpc/docs/flow-logs#log-sampling) 
without lowering the accuracy of results.

When you're editing a subnet in the Cloud Console, you can view the estimated size of logs generated per day. You can also use the
[Cloud Monitoring sample dashboard](https://github.com/GoogleCloudPlatform/monitoring-dashboard-samples/blob/master/dashboards/networking/vpc-flow-logs-monitoring.json)
to estimate the size of flow logs.

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select an existing project.

1. Select or create a Google Cloud project.
1. Enable billing for your project.

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created.

## Enabling VPC Flow Logs

Open Cloud Shell and run the following command:

    gcloud compute networks subnets update [YOUR_SUBNET_NAME] --enable-flow-logs
    
 Replace `[YOUR_SUBNET_NAME]` with the name of your subnet.
 
 Run this command for each of the subnets that have VMs sending traffic to on-premises resources.

## Exporting VPC Flow Logs to the BigQuery sink

You need only VM instance logs for traffic that goes outside of the Shared VPC network. This section includes three options for how to filter logs by IP ranges.
The first method, the additive approach, involves explicitly listing the IP ranges that you want to include. However, if there are many CIDR blocks advertised 
from on-premises into the cloud and only a few CIDR blocks in the cloud, it can instead be easier to use a subtractive approach to list the ranges to exclude. 
The second and third methods described in this section use a subtractive approach. The second  method involves listing the IP ranges to exclude during the log 
creation step. The third method involves adding exclusion filters during the sink creation step.

### Additive approach

1.  In the Cloud Console, open [Cloud Logging](https://console.cloud.google.com/logs/). 
1.  Filter logs using the following in Query Builder:  

        logName="projects/[YOUR_SHARED_VPC_HOST_PROJECT_ID]/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "[ON_PREM_IP_RANGE_1]") OR ip_in_net(jsonPayload.connection.dest_ip, "[ON_PREM_IP_RANGE_2]"))

    Add more `ip_in_net` clauses to cover the IP ranges of your on-premises network, if necessary. Replace `[ON_PREM_IP_RANGE_1]` and `[ON_PREM_IP_RANGE_2]`
    with IP ranges in the format `10.1.0.0/24`.

1.  Run the query.
1.  Click **Actions**, and choose **Create sink** from the menu. 
1.  On the **Create logs routing sink** page, name the sink and click **Next**.
1.  Choose the BigQuery dataset as a destination.
1.  Click **Create sink**.

### Subtractive approach: excluding unwanted IP ranges from log export by extending the log query

1.  In the Cloud Console, open [Cloud Logging](https://console.cloud.google.com/logs/). 
1.  At the log query creation stage, modify the query from the example in the additive approach above in the following way:

        logName=~"/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "[BIG_OVERLAPPING_ON_PREM_IP_RANGE_1]") OR ip_in_net(jsonPayload.connection.dest_ip, "[ON_PREM_IP_RANGE_2]"))
        (NOT (ip_in_net(jsonPayload.connection.dest_ip, "[SMALL_CLOUD_IP_RANGE_1]") OR ip_in_net(jsonPayload.connection.dest_ip, "[SMALL_CLOUD_IP_RANGE_1]")))

1.  Run the query.
1.  Click **Actions**, and choose **Create sink** from the menu. 
1.  On the **Create logs routing sink** page, name the sink and click **Next**.
1.  Choose the BigQuery dataset as a destination.
1.  Click **Create sink**.

### Subtractive approach: excluding unwanted IP ranges with exclusion filters during sink creation

1.  In the Cloud Console, open [Cloud Logging](https://console.cloud.google.com/logs/). 
1.  Filter logs using the following in Query Builder using the same query as in the additive approach:

        logName="projects/[YOUR_SHARED_VPC_HOST_PROJECT_ID]/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "[ON_PREM_IP_RANGE_1]") OR ip_in_net(jsonPayload.connection.dest_ip, "[ON_PREM_IP_RANGE_2]"))

    Add more `ip_in_net` clauses to cover the IP ranges of your on-premises network, if necessary. Replace `[ON_PREM_IP_RANGE_1]` and `[ON_PREM_IP_RANGE_2]`
    with IP ranges in the format `10.1.0.0/24`.

1.  Run the query.
1.  Click **Actions**, and choose **Create sink** from the menu. 
1.  On the **Create logs routing sink** page, name the sink and click **Next**.
1.  Choose the BigQuery dataset as a destination.
1.  Verify that the inclusion filter is the query from step 2, and click **Next**.
1.  Specify the IP ranges that you want to exclude with the exclusion filter:

        (ip_in_net(jsonPayload.connection.dest_ip, "[SMALL_CLOUD_IP_RANGE_1]") OR ip_in_net(jsonPayload.connection.dest_ip, "[SMALL_CLOUD_IP_RANGE_2]"))

1.  Click **Create sink**.

## Selecting the appropriate logs in BigQuery

1.  Open [BigQuery](https://console.cloud.google.com/bigquery). 
1.  In the **Explorer** pane on the left, choose the sink that you just created. 
1.  Use the following query template to create your own query.

    Configure IP ranges for on-premises, project ID, sink name, and aggregation period (day or month).
    The list of IP ranges in the `IP_TO_LABEL` function represents the
    [ranges of Google APIs](https://cloud.google.com/vpc/docs/configure-private-google-access#ip-addr-defaults).


        CREATE TEMP FUNCTION PORTS_TO_PROTO(src_port INT64, dst_port INT64)
          as (
          case 
          when src_port = 22 OR dst_port = 22 then 'ssh'
            when src_port = 80 OR dst_port = 80 then 'http'
            when src_port = 443 OR dst_port = 443 then 'https'
            when src_port = 10402 OR dst_port = 10402 then 'gae' -- App Engine flexible environment
            when src_port = 8443 OR dst_port = 8443 then 'gae' -- App Engine flexible environment
          else
              FORMAT('other-%d->%d', src_port, dst_port)
             end
          );
        
        SELECT 
          DATE_TRUNC(PARSE_DATE('%F', SPLIT(jsonPayload.start_time, 'T')[OFFSET(0)]), [AGGREGATION_PERIOD]) as time_period        -- Uncomment this section to add protocol to the result
        --  PORTS_TO_PROTO(
        --    CAST(jsonPayload.connection.src_port as INT64), 
        --    CAST(jsonPayload.connection.dest_port as INT64)
        --  ) as protocol,
          SUM(CAST(jsonPayload.bytes_sent as int64)) as bytes,
          SUM(CAST(jsonPayload.packets_sent as int64)) as packets,
          jsonPayload.src_instance.project_id as src_project_id
        FROM `[PROJECT_ID].[DATASET_NAME].compute_googleapis_com_vpc_flows_*`
        GROUP BY
        time_period, protocol, src_project_id
        ORDER BY packets DESC

1.  Paste the query into the query window and click **Run**.

    The top talkers are represented by the top rows of the table. You can change the query and sort the results by bytes, for example.
    `src_project_id` field represents the source project of the specific flow.

## Cleaning up

The easiest way to eliminate billing and avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project 
that you created for the tutorial:

1. In the Cloud Console, [go to the **Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project that you want to delete, and then click **Delete**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next
-  [Using VPC Flow Logs](https://cloud.google.com/vpc/docs/using-flow-logs)
-  [Overview of logs exports](https://cloud.google.com/logging/docs/export)
-  [BigQuery schema for exported logs](https://cloud.google.com/logging/docs/export/bigquery) 
