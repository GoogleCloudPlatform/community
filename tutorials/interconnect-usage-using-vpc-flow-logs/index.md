---
title: Use VPC FLow Logs to monitor Cloud Interconnect usage
description: Learn how to analyze information from VPC Flow Logs to estimate the amount of Cloud Interconnect usage by different projects.
author: manokhina
tags: VLAN attachments
date_published: 2021-02-11
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>
 
This tutorial describes the mechanism of analyzing VPC Flow Logs to estimate the amount of Interconnect attachment usage by different projects. It can be used by the Network Administrator who administers the Landing Zone (an environment that's been provisioned and prepared to host workloads in cloud).  

VPC Flow Logs capture different flows from/to VMs, but we will focus only on those which involve Egress traffic through Interconnect (the flow is shown by red arrows on the diagram). Only Egress traffic from VPC towards Interconnect is chargeable, unless there is a resource that is processing ingress traffic, such as a load balancer.

![image](https://storage.googleapis.com/gcp-community/tutorials/interconnect-usage-using-vpc-flow-logs/diagram.png)

This tutorial assumes you are familiar with VPC networks, Cloud Logging and BigQuery.

## Objective

You will learn how to monitor how much capacity of the interconnect attachment is used by projects and instances. This data can be used for calculating the cost to charge the business units which use interconnect.

## Costs

This tutorial uses billable components of Google Cloud Platform, including:

-  BigQuery
-  VPC Flow Logs
-  GCE VM instances
-  VPC Egress traffic 

For large enough volumes of traffic, VPC Flow logs size can be reduced using [the different sampling rate](https://cloud.google.com/vpc/docs/flow-logs#log-sampling) which will not lower the accuracy of results. Also, you can view the estimated logs size generated per day during the subnet editing in the Cloud Console. 

Use the [Pricing Calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage and [Cloud Monitoring sample dashboard](https://github.com/GoogleCloudPlatform/monitoring-dashboard-samples/blob/master/dashboards/networking/vpc-flow-logs-monitoring.json) which can estimate the size of flow logs.

## Before you begin

For this reference guide, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a new one, or select a project you already created:

1. Select or create a Google Cloud project.
1. Enable billing for your project.

When you finish this tutorial, you can avoid continued billing by deleting the resources you created. See [Cleaning up](#cleaning-up) for more detail.

## Enabling VPC Flow logs

Open Cloud Shell and run the following command. Put the name of the subnet instead of `<SUBNET-NAME>`. Run this command for all the subnets that have VMs sending traffic to on-prem.

    gcloud compute networks subnets update <SUBNET-NAME> --enable-flow-logs

## Exporting VPC Flow Logs to BigQuery sink

1. In Cloud Console, open Cloud Logging. 
1. We need only VM instance logs for traffic that goes outside of the Shared VPC. Filter logs using the following query. Put the Shared VPC host project id in the query template and run the query in Query Builder. Add more `ip_in_net` clauses to cover IP ranges of your on-premises network, if necessary. `ON-PREM-IP-RANGE` should be in the format `10.1.0.0/24`.  

        logName="projects/<PROJECT_ID>/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-2>"))

> Note: if you want to use the subtractive approach for selecting the subnets (i.e. when a supernet is advertised from on-prem to cloud), go to section [Excluding the unwanted IP ranges from log export](#heading=h.kdwekww1g9b8).
## Creating the sink

1. Click **Actions**.
1. In the drop-down menu, click **Create sink**. 
1. Name the sink. Click **Next**.
1. Choose BigQuery dataset as a destination. Click **Create Sink**.

## Excluding the unwanted IP ranges from log export
If there are many CIDR blocks advertised from on-prem into the cloud and only a few CIDR blocks in the cloud, it'd be easier to list the unwanted ranges instead. It can be done in two ways:<br>

**First option: extend the log query.**

1. At the log query creation stage, modify the query in the following way:

        logName=~"/logs/compute.googleapis.com%2Fvpc_flows"
        jsonPayload.reporter="SRC"
        (ip_in_net(jsonPayload.connection.dest_ip, "<BIG-OVERLAPPING-ON-PREM-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<ON-PREM-IP-RANGE-2>"))
        (NOT (ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>") OR ip_in_net(jsonPayload.connection.dest_ip, "<SMALL-CLOUD-IP-RANGE-1>")))

1. Run the query.
1. Continue with the [sink creation](#creating-the-sink).

**Second option: add exclusion filters during sink creation.**

1. At the log query creation stage, use the same query as in additive approach:

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

To avoid incurring charges to your Google Cloud Platform account for the resources used in this tutorial:

### Delete the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.  
**Caution**: Deleting a project has the following effects:

   -  **Everything in the project is deleted.** If you used an existing project for this tutorial, when you delete it, you also delete any other work you've done in the project.
   -  **Custom project IDs are lost.** When you created this project, you might have created a custom project ID that you want to use in the future. To preserve the URLs that use the project ID, such as an **`appspot.com`** URL, delete selected resources inside the project instead of deleting the whole project.

   If you plan to explore multiple tutorials and quickstarts, reusing projects can help you avoid exceeding project quota limits.

1. In the Cloud Console, [go to the Manage resources page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project that you want to delete and then click **Delete**.
1. In the dialog, type the project ID and then click **Shut down** to delete the project.

----

## What's next
-  [Using VPC Flow Logs](https://cloud.google.com/vpc/docs/using-flow-logs)
-  [Overview of logs exports | Cloud Logging](https://cloud.google.com/logging/docs/export)
-  [BigQuery schema for exported logs | Cloud Logging](https://cloud.google.com/logging/docs/export/bigquery) 
