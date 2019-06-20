---
title: Migrate on-premises virtual machines with StratoZone and Velostrata
description: Learn how to use StratoZone and Velostrata to migrate on-premises VMs to Google Cloud Platform.
author: laidig
tags: VM migration, Velostrata, StratoZone
date_published: 2019-06-21
---

This article walks you through the migration of an on-premises virtual machine (VM) to Google Cloud Platform (GCP), using
StratoZone and Velostrata. In the planning phase, you prioritize the workloads (applications and assets) for an efficient 
migration to the cloud. Integrations between GCP, StratoZone, and Velostrata enable you to export your plans to Velostrata.
Velostrata then handles migrating your VMs to GCP.

## Before you begin

Follow the steps below to get started.

### Sign up and register

Go to the [StratoZone website](https://gogcp.stratozone.com/) and follow the instructions on that page to sign up and 
register.

### Create an assessment

After you have registered, sign in to the [StratoZone portal](https://portal.stratozone.com/).

1.  At the bottom of the **Getting Started** section on the StratoZone portal page, click **Create New Assessment**.
1.  Select your **Assessment Type** and fill out the rest of the form. Note the **Activation Code** provided to you.
1.  You will then be able to download the StratoProbe collector application.

### Discovery

Follow these steps to discover your environment's assets for migration to GCP:

1.  Download the StratoProbe data collector to a machine that has
    [SSH or WMI access](https://portal.stratozone.com/Documentation/StratoProbe_Guide.html#4) to the assets to be collected.
1.  To install StratoProbe, run `setup.exe`. Follow the prompts for the application.
1.  Run the StratoProbe shortcut created by the installer.
1.  Enter the **Activation Code** and click **Activate Now**.

#### Add credentials

To begin the collection process, you must create credentials groups, which are used to log in to assets to be collected.
From the StratoZone portal, select **Create Credentials Group**.

In the **Group Credentials** dropdown, choose one of the following:

* **No Group Credentials**: Specify credentials for each asset.
* **Username and Password**: For Windows and Linux.
* **SSH Key / Certificate**: For Linux only. You will need a `.pem` certificate to proceed.
* **vCenter**: Use vCenter host and credentials to gather asset data.

#### Add target assets

After credentials groups are created, add target assets to that group:

1.  Select the **Scanning Target Guest OS Method**:
    * **Manually**: You will provide the following for each asset individually: name, IP address, OS type, and credentials.
    * **CSV Load**: You will provide a CSV file containing pre-identified assets. You can download a pre-formatted CSV file 
      by clicking the gear icon in the upper right and clicking **Export File: Asset Import Template**.
    * **Bulk Scan**: Automatically scans IP ranges to discover assets. Before beginning a bulk scan, you must agree to the 
      terms and conditions. After agreeing, you will provide CIDR IP ranges (`/16` or smaller). To start a scan on a range,
      click the **Play** button on the row with the range you would like to scan. When scanning, StratoZone will attempt to 
      log in with all available credentials groups.
1.  If vSphere credentials were entered, select **Collect from vSphere** to collect assets from vSphere.

#### Schedule asset collection

To schedule an asset group for collection, click the **Calendar** icon from the **StratoProbe Data Collector** panel.
The **Schedule Group Collection** dialog appears. Choose **Run on Schedule**, and select the start date, end date, and which
days of the week the scan will run on. Run a collector in each data center, and leave it running 
for at least 1-2 weeks so that it can accurately collect utilization data.

## Analyze

Use this module to analyze discovered assets, cloud-fit scoring, and server dependency mapping.

Log in to the [StratoZone portal](https://portal.stratozone.com/). Data on your assets appears. From here, you will see 
several tabs:

* **Inventory**: View detailed information about all assets, including storage, network, running processes, installed
  software, memory, and CPU utilization.
* **Dependency**: View dependencies between servers. You can also view details relating to network traffic (ports,
  traffic type, protocol) for each network relationship in the dependency map.
  
  ![An example graph of workload dependencies](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--t13ecagmadj.png)

* **StratoFit**: Scores how well applications are suited for migration to the cloud. A StratoFit score of high, medium,
  or low is assigned to assets based on the size of system and number of dependencies.

## Plan

In this section, you build application groups based on dependencies, right-size assets, and perform a total cost
of ownership (TCO) analysis.

### Create dependency groups

1. Click the **+** icon in the title bar.
1. Enter a group name and description and click the save button.
1. Select the assets you want to add to the group by checking the boxes to the left of each asset.
1. Click the **Add Selected assets to the Group** button when finished 

### Migrate applications using Velostrata APIs

The StratoZone Migrate module allows you to do the following:

- Group workload servers into waves.
- Assign migration date and time.
- Track tasks associated with each migration.
- Migrate the servers to GCP using Velostrata.

On the StratoZone portal, select the **Migrate** module and click the **Setup** tab.

![Where to set up Velostrata configuration in StratoZone](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--qg4mkjg2r3q.png)

Provide your **GCP account credentials**, **Velostrata Manager IP**, and **Password** StratoZone groups workloads
into move groups. Click the **Move Groups** tab to create groups and assign a migration date to them.

![Move Groups in StratoZone Velostrata integration](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--9x3h33xbz4c.png)

![Create new Move Group](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--z6t5la7bsu.png)

Add workloads (servers) to the newly created move group.

![The plus icon adds workloads to a move group](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--jmi7c7n05hr.png)

For each added workload, configure migration settings.

![Where to set workload migration preferences](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--e08674y0y2n.png)

Click the **Migrate** tab.

![The Migrate Tab](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--fta43u2jvfs.png)

To start a migration, click **Migration** and select the action to be performed.
Migration progress can be tracked by clicking the down arrow to see list of completed migration steps.	

### Migrate applications using Velostrata CSV 

You can also download a pre-configured CSV file and import it manually into the Velostrata Runbook Automation portal.

1.  When creating move groups, select **Velostrata CSV**.

1.  To download the CSV, click the download icon next to move group.

    ![Exporting a Velostrata CSV](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-stratozone/seamlessmigrat--fta43u2jvfs.png)

### Next steps

For more help with StratoZone, see [Troubleshooting](https://portal.stratozone.com/Documentation/StratoProbe_Troubleshooting.html).

Continue with the [wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/overview) process on your Velostrata Manager:

* [Create a wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-new-waves) from the CSV.
* [Add jobs](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-aborting-jobs) to that wave
* [Monitor the progress](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/monitoring-waves-runbooks-jobs) of your waves.
