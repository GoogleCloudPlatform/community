---
title: Migrate virtual machines with RISC Networks and Migrate for Compute Engine
description: Learn how to migrate virtual machines (VMs) from VMware to Google Cloud using RISC Networks and Migrate for Compute Engine.
author: laidig
tags: Migrate for Compute Engine, RISC Networks
date_published: 2019-09-03
---

Tony Laidig | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This article walks you through a VM migration from VMware to Google Cloud, from planning to completion.
Integrations between Google Cloud, RISC Networks (now
[Flexera](https://www.flexera.com/about-us/press-center/flexera-acquires-risc-networks.html)),
and Migrate for Compute Engine (formerly Velostrata) enable you to export your plans into Migrate for Compute 
Engine.

## Prerequisites

This tutorial assumes that you have a Migrate for Compute Engine environment set up on Google Cloud.

For more information, see
[Getting started with Migrate for Compute Engine](https://cloud.google.com/velostrata/docs/getting-started)
and
[Overview of on-premises to Google Cloud migrations](https://cloud.google.com/velostrata/docs/how-to/migrate-on-premises-to-gcp/overview).

## Creating a RISC Networks assessment

You begin by signing up and registering on the RISC Networks website and creating an assessment. 

1.  Go to the [RISC Networks website](https://portal.riscnetworks.com/register.php) to sign up and register.
1.  Log in to the [RISC Networks portal](https://portal.riscnetworks.com/) and follow the directions to create an 
    assessment.
    
    Copy the bootstrap code for later use.

    For more information about creating an assessment, see [this video](https://www.youtube.com/watch?v=GESZAjhjiJI).

## Discovery

In this section, you install and configure the RN150 virtual appliance.

### Deploy the RN150 virtual appliance on-premises

The RISC Networks RN150 virtual appliance handles discovery.

1.  From the RISC Network portal, download the ZIP file that contains the RN150.
1.  Extract the contents of the file.
1.  Use VMware Player or vSphere vCenter to install the OVF template extracted from the ZIP file.

For more information about downloading and deploying the RN150 virtual appliance, see
[this video](https://www.youtube.com/watch?v=GsunC6IaAq4).

### Sign in to the RN150 virtual appliance

1.  If you have not done so already, start the VM from the OVF template.
1.  In your web browser, go to the IP address of the RN150 virtual appliance.
1.  Sign in with your RISC Networks credentials and accept the license.
1.  Provide the bootstrap code that you copied from the RISC Networks portal when you registered and created an assessment.
1.  Click **Verify Key**.
1.  When asked if you will use Flex Deploy, click **No**.
1.  Click the **Dashboard** button to return to the dashboard. 

For more information about the steps in this section, see [this video](https://www.youtube.com/watch?v=X8XjSPSlq48).

### Enter subnet information

In this section, you populate subnets that RISC Networks will scan for assets.

- In the dashboard, click **Subnets**.

You can populate subnets manually, from a routing table discovered using SNMP, or from a CSV file.

Adding subnets manually and discovering subnets with SNMP are demonstrated in
[this video](https://www.youtube.com/watch?v=csF1dOtb4nE).

#### Add subnets manually

1.  Enter the subnet information into the **Subnet** field.
1.  Select the **Subnet Mask**.
1.  Click **Add**.

#### Discover subnets with SNMP

1.  Click **Populate from Routing Table**.
1.  Select whether you will use SNMP v1/2 or v3.
1.  Enter the IP address of the device that you will discover the routing table from.
1.  Enter the credentials for your SNMP version

When the subnets have been added, enable them in leftmost column in the list.

### Enter SNMP information

RISC Networks can scan the routing tables of SNMP devices for their inclusion in your migration. For more information,
see [this video](https://www.youtube.com/watch?v=uJPPZwxHLLY).

### Enter Windows credentials

To discover what workloads are running on Windows machines, enter Windows credentials:

1.  In the dashboard, click **Windows**.
1.  Fill in the **Domain**, **Username**, and **Password** fields.
1.  Enable **Netstat** to discover network dependencies from VMs.
1.  Click **Validate Credential** and enter an **IP address** of a Windows
    host.
   
    RISC Networks will connect and attempt to run `netstat`. A validation screen appears.
1.  If the validation is successful, click **Add Credential**.

After adding credentials, you must rescan to inventory your Windows resources.  

For more information about the steps in this section, see [this video](https://www.youtube.com/watch?v=Lj7Op7xRyKI).

### Enter VMWare credentials

Adding VMware credentials enables RISC Networks to scan VMware for information about your hosts:

1.  In the dashboard, click **VMware**.
1.  Fill in the **vCenter IP**, **Port**, **Username**, and **Password** fields.
1.  Click **Add**.

    A new dialog box appears, asking if you would like to test the credentials.
1.  Click **Test**.
1.  If the test is successful, click **OK**.

For more information about the steps in this section, see [this video](https://www.youtube.com/watch?v=jzIrWKn6UOQ).

### Enter SSH credentials

Adding SSH credentials enables RISC Networks to scan Linux and Unix hosts for information.

1.  In the dashboard, click **SSH**.
1.  Enter a **Username**.
1.  Choose an **Auth Type** (password or publickey).
1.  If you are using password authentication, enter the user's **Password**.
1.  If you are using publickey authentication, paste the **Public Key**.
1.  Set **Privilege Elevation** if you would like RISC Networks to use `sudo` on the host.

For more information about the steps in this section, see [this video](https://www.youtube.com/watch?v=_FTOzaB9oqQ).

### Start assessment

You are now ready to continue your assessment.

-   In the dashboard, click the **Start Assessment** or **Request Rescan** button.

This step may take several hours, based on the number of assets or complexity of the environment.

You will receive an email when the discovery process is complete.

## Review assets

When the assessment is complete, your results will be available on the
[RISC Networks website](https://portal.riscnetworks.com). 

## Migrating

You are now ready to plan a migration using the information collected by the RN150 virtual appliance on your network.

### License devices for data collection

1.  Select **Collect Data > Licensing**.
1.  Select the **License** checkbox for only those assets that you would like to collect additional data from for planning. 

For more information, see [this video](https://www.youtube.com/watch?v=nYCEaXwvl1w).

After you have collected data for two to four weeks, RISC Networks can automatically determine the dependencies of your 
applications for planning your migration.

### Build application stacks

Application stacks are groups of servers that depend on one another. In this section, you build application stacks based on
the information collected by the RN150 virtual appliance.

For a full description of the application stacks feature, see [this video](http://www.youtube.com/watch?v=2UHYGso_BKc).

## Export an application stack as a runbook for Migrate for Compute Engine

1.  Sign in to the [RISC Networks website](https://portal.riscnetworks.com).
1.  Click **Add Intelligence**, and choose **Available Reports** near the bottom of the menu.
1.  Click **Velostrata Export** in the **Available Reports** list.  ![image](https://storage.googleapis.com/gcp-community/tutorials/vm-migration-with-risc-networks/seamlessmigrat--qdj7zg672hg.png)
1.  Select the application stack from the dropdown.
1.  Fill out any missing entries.
1.  Click **Save**.
1.  Click **Export CSV**.

    Note the file location so that you can upload it to Migrate for Compute Engine.

### Next steps

Continue with the [wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/overview)
process in Velostrata Manager:

1.  [Create a wave](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-new-waves)
    from the CSV.
1.  [Add jobs](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/creating-aborting-jobs)
    to that wave.
1.  [Monitor the progress](https://cloud.google.com/velostrata/docs/how-to/organizing-migrations/monitoring-waves-runbooks-jobs)
    of your waves.
