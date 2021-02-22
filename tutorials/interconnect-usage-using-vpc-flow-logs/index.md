---
title: Use VPC Flow Logs to monitor Cloud Interconnect usage
description: Learn how to analyze information from VPC Flow Logs to estimate the amount of Cloud Interconnect usage by different projects.
author: manokhina
tags: VLAN attachments
date_published: 2021-02-22
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>
 
This tutorial shows you how to analyzine VPC Flow Logs to estimate the amount of Interconnect attachment usage by different projects and instances. 
This data can be used for calculating the cost to charge the business units that use the Interconnect connections. This technique can be used by a network 
administrator who administers the *landing zone* (an environment that has been provisioned and prepared to host workloads in the cloud.

VPC Flow Logs captures different flows to and from VMs; this tutorial focuses on those which involve egress traffic through Interconnect, shown by red arrows in
the diagram below. Only egress traffic from VPC towards Interconnect is chargeable, unless there is a resource that is processing ingress traffic, such as a load
balancer.

![image](https://storage.googleapis.com/gcp-community/tutorials/interconnect-usage-using-vpc-flow-logs/diagram.png)

This tutorial that assumes that you're familiar with VPC networks, Cloud Logging, and BigQuery.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

-  BigQuery
-  VPC Flow Logs
-  Compute Engine VM instances
-  VPC egress traffic 

For large volumes of traffic, you can reduce the size of logs by using [different sampling rate](https://cloud.google.com/vpc/docs/flow-logs#log-sampling), which 
doesn't lower the accuracy of results. Also, you can view the estimated size of logs generated per day during the subnet editing in the Cloud Console. 

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage. Yo can also use the
[Cloud Monitoring sample dashboard](https://github.com/GoogleCloudPlatform/monitoring-dashboard-samples/blob/master/dashboards/networking/vpc-flow-logs-monitoring.json) to estimate the size of flow logs.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project or select a project that you already created.

1. Select or create a Google Cloud project.
1. Enable billing for your project.

When you finish this tutorial, you can avoid continued billing by deleting the resources you created.

## Enabling VPC Flow Logs

Open Cloud Shell and run the following command:

    gcloud compute networks subnets update [YOUR_SUBNET_NAME] --enable-flow-logs
    
 Replace `[YOUR_SUBNET_NAME]` with the name of your subnet.
 
 Run this command for each of the subnets that have VMs sending traffic to on-premises resources.

## Exporting VPC Flow Logs to the BigQuery sink

1. In the Cloud Console, open Cloud Logging. 
1. You need only VM instance logs for traffic that goes outside of the Shared VPC network. Filter logs using the following query. Put the Shared VPC host project id in the query template and run the query in Query Builder. Add more `ip_in_net` clauses to cover IP ranges of your on-premises network, if necessary. `ON-PREM-IP-RANGE` should be in the format `10.1.0.0/24`.  

        logName="projects/<PROJECT_ID>/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-2>"))

**Note**: If you want to use the subtractive approach for selecting the subnets (when a supernet is advertised from on-premises to cloud), go to the "Excluding the unwanted IP ranges from log export" section later in this document.

## Creating the sink

1. Click **Actions**.
1. In the drop-down menu, click **Create sink**. 
1. Name the sink. Click **Next**.
1. Choose BigQuery dataset as a destination. Click **Create Sink**.

## Excluding the unwanted IP ranges from log export

If there are many CIDR blocks advertised from on-premises into the cloud and only a few CIDR blocks in the cloud, it might be easier to list the unwanted ranges
instead. It can be done in two ways:

**First option: extend the log query.**

1. At the log query creation stage, modify the query in the following way:

        logName=~"/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "<BIG-OVERLAPPING-ON-PREM-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-2>"))
        (NOT (ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>")))

1. Run the query.
1. Continue with the [sink creation](#creating-the-sink).

**Second option: add exclusion filters during sink creation.**

1. At the log query creation stage, use the same query as in the additive approach:

        logName="projects/<PROJECT_ID>/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-2>"))

1. Click **Actions**.
1. In the drop-down menu, click **Create sink**.
1. Name the sink, click **Next**.
1. Choose BigQuery dataset as a destination. Click **Next**.
1. Check the inclusion filter. It should be the query from step 1. Click **Next**.
1. Specify the IP ranges you want to exclude with the exclusion filter:

        (ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>"))

1. Click **Create Sink**.

## Selecting the appropriate logs in BigQuery

1. Open BigQuery. 
1. On the left pane, choose the sink you have just created. 
1. Use the following query template to create your own query. Configure IP ranges for on-premises, project id, sink name, aggregation period (day or month)  and run the query. The list of IP ranges in the `IP_TO_LABEL` function is representing [the ranges of Google APIs](https://cloud.google.com/vpc/docs/configure-private-google-access#ip-addr-defaults).


        CREATE TEMP FUNCTION PORTS_TO_PROTO(src_port INT64, dst_port INT64)
          as (
          case 
          when src_port = 22 OR dst_port = 22 then 'ssh'
            when src_port = 80 OR dst_port = 80 then 'http'
            when src_port = 443 OR dst_port = 443 then 'https'
            when src_port = 10402 OR dst_port = 10402 then 'gae' -- AppEngine Flex
            when src_port = 8443 OR dst_port = 8443 then 'gae' -- AppEngine Flex
          else
              FORMAT('other-%d->%d', src_port, dst_port)
             end
          );
        
        SELECT 
          DATE_TRUNC(PARSE_DATE('%F', SPLIT(jsonPayload.start_time, 'T')[OFFSET(0)]), <AGGREGATION_PERIOD>) as time_period        -- Uncomment this section to include protocol to the result
        --  PORTS_TO_PROTO(
        --    CAST(jsonPayload.connection.src_port as INT64), 
        --    CAST(jsonPayload.connection.dest_port as INT64)
        --  ) as protocol,
          SUM(CAST(jsonPayload.bytes_sent as int64)) as bytes,
          SUM(CAST(jsonPayload.packets_sent as int64)) as packets,
          jsonPayload.src_instance.project_id as src_project_id
        FROM `<PROJECT_ID>.<DATASET_NAME>.compute_googleapis_com_vpc_flows_*`
        GROUP BY
        time_period, protocol, src_project_id
        ORDER BY packets DESC

1. Paste the query into the query window and click Run. The top talkers will be represented by the top rows of the table. You can change the query and sort the results by bytes, for example. `src_project_id` field represents the source project of the specific flow.

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
