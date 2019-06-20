---
title: Migrate a virtual machine to Google Cloud Platform with StratoZone and Velostrata
description: Learn how to use StratoZone and Velostrata to migrate on-premises VMs to Google Cloud Platform.
author: laidig
tags: VM Migration, Velostrata, StratoZone
date_published: 2019-06-21
---

This article walks you through a VM migration using StratoZone from planning to completion. In the planning phase, you will prioritize the workloads (applications and assets) for an efficient migration to the cloud. Integrations between Google Cloud Platform (GCP), StratoZone, and Velostrata enable you to export your plans into Velostrata. Velostrata then handles migrating your VMs to GCP.

## Before you begin

Follow the steps below to get started.

### Sign up and register

Go to StratoZone to sign up and register at [http://gogcp.stratozone.com/](http://gogcp.stratozone.com/)

### Create an assessment

Once registered, sign in to the [StratoZone portal](https://portal.stratozone.com/).

1. Click **Create new assessment**.

![The placement of the Create New Assessment button on the StratoZone page](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--ozuclxm8r4f.png)

1. Select your **Assessment Type** and fill out the rest of the form. Note the **Activation Code** provided to you.
1. You will then be able to download the StratoProbe collector application.

### Discovery

Follow the steps below to discover your environment's assets for migration to Google Cloud Platform:

1. Download the StratoProbe data collector to a machine that has [SSH or WMI access](https://portal.stratozone.com/Documentation/StratoProbe_Guide.html#4) to the assets to be collected.
1. To install StratoProbe, run `setup.exe`. Follow the prompts for the application.
1. Run the StratoProbe shortcut created by the installer
1. Enter the **Activation Code** and click **Activate Now**.

#### Add credentials

To begin the collection process, you must create **Credentials Groups**, used to log in to assets to be collected.
From the StratoZone portal, select **Create Credentials Group**.

In the **Group Credentials** dropdown, choose one of the following:

| Group Credentials | Description |
| ----------------- | ----------- |
| No Group Credentials | Specify credentials for each asset|
| Username and Password | For Windows and Linux |
| SSH Key / Certificate | For Linux only. You will need a `.pem` certificate to proceed |
| vCenter | Use vCenter host and credentials to gather asset data. |

#### Add target assets

Once credentials groups are created, add target assets to that group by:

1. Select the **Scanning Target Guest OS Method**:
   1. **Manually** to provide each asset individually. You will provide the **name**, **IP address**, **OS type**, and **credentials** for each asset.
   1. **CSV Load** to provide a CSV containing pre-identified assets. You can download a pre-formatted CSV by clicking on the gear wheel icon in the upper right hand corner and clicking **Export File: Asset Import Template**.
   1. **Bulk Scan** to automatically scan IP ranges to discover assets. Before beginning a bulk scan, you will have to **agree** to the terms and conditions. After agreeing, you will provide CIDR IP ranges (/16 or smaller). To start a scan on a range, click the **Play** button on the row with the range you would like to scan. When scanning, StratoZone will attempt to login with all available credentials groups.

1. If vSphere credentials were entered, select **Collect from vSphere** to collect assets from vSphere.

#### Schedule asset collection

To schedule an Asset Group for collection, click the **Calendar** icon from the **StratoProbe Data Collector** panel. The **Schedule Group Collection** dialog appears. Choose to **Run on Schedule**, and select the **Start Date**, **End Date**, and which days of the week the scan will **Run On**.  
Run a collector in each data center and leave it running for at least 1-2 weeks so it can accurately collect utilization data.

## Analyze

This module allows the users to analyze discovered assets, Cloud-fit scoring and server dependency mapping.  
Log in to your [StratoZone portal](https://portal.stratozone.com/). Data on your assets appears. From here you will see several tabs:

- The **Inventory** tab allows users to view detailed information about all the assets. (for example: storage, network, running processes, installed software, memory and CPU Utilization)
- The **Dependency** tab allows users to view the dependencies between servers. Additionally users can view all the details relating to network traffic (ports, traffic type, protocol etc.) for each network relationship in the dependency map.

![An example graph of workload dependencies](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--t13ecagmadj.png)

- The **StratoFit** tab scores how well applications are suited for migration to the cloud. StratoFit scoring is categorized into high, medium, and low, which is assigned to assets based on the size of system and number of dependencies.

## Plan

In this section, you will build application groups based on the dependencies, right size assets and perform a total cost of ownership (TCO) analysis.  
To Create Dependency Groups, follow the steps below:

1. Click the "+" icon from the title bar
1. Enter a group name and description and click the save button
1. Select the assets you want to add to the group by checking the boxes to the left of each asset
1. Click the Add Selected assets to the Group button when finished 

### Migrate applications using Velostrata APIs

The StratoZone Migrate module allows you to:

- Group workloads servers into waves.
- Assign migration date and time.
- Track tasks associated with each migration.
- Migrate the servers to GCP using Velostrata.

On the StratoZone portal, select migrate module and click the "setup" tab

![Where to set up Velostrata configuration in StratoZone](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--qg4mkjg2r3q.png)

Provide your **GCP account credentials**, **Velostrata Manager IP**, and **Password** StratoZone groups workloads
into Move Groups. Click the **Move Groups** tab to create groups and assign migration date to them.

![Move Groups in StratoZone Velostrata integration](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--9x3h33xbz4c.png)

![Create new Move Group](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--z6t5la7bsu.png)

1. Add workloads (servers) to newly created move group.

![The plus icon adds workloads to a move group](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--jmi7c7n05hr.png)

1. For each added workload configure migration settings

![Where to set workload migration preferences](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--e08674y0y2n.png)

1. Click on the **migrate** tab.

![The Migrate Tab](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--fta43u2jvfs.png)

1. To start a migration, click **Migration** and select action to be performed
1. Migration progress can be tracked by clicking the down arrow to see list of completed migration steps.	

### Migrate applications using Velostrata CSV 

You can also download a pre-configured CSV file and import it manually into Velostrata Runbook Automation portal.

1. When creating move groups, select **Velostrata CSV**
1. To download CSV, click the download icon next to Move group.

![Exporting a Velostrata CSV](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--fta43u2jvfs.png)

### Next steps

For more help with StratoZone, see [Troubleshooting](https://portal.stratozone.com/Documentation/StratoProbe_Troubleshooting.html).

Continue with the [Wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/overview) process on your Velostrata Manager:

1. [Create a Wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-new-waves) from the CSV.
1. [Add Jobs](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-aborting-jobs) to that wave
1. [Monitor the progress](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/monitoring-waves-runbooks-jobs) of your waves.
