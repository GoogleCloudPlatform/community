---
title: Deploy a Microsoft SQL Server Always On availability group in a single subnet
description: Learn how to deploy a Microsoft SQL Server Always On availability group in a single subnet.
author: shashank-google
tags: databases, MSSQL, AOAG, AG
date_published: 2020-12-10
---

Shashank Agarwal | Database Cloud Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you learn how to deploy the Microsoft SQL Server database engine in an
[Always On availability group](https://docs.microsoft.com/en-us/sql/database-engine/availability-groups/windows/always-on-availability-groups-sql-server) configuration in a single subnet.

## Objectives

*   Install Microsoft SQL Server in Always On availability group configuration using a single subnet.
*   Set up a VPC network with a Windows domain controller.
*   Create two Windows SQL Server VM instances to act as cluster nodes.
*   Set up an internal load balancer to direct traffic to the active node.
*   Test the failover operation to verify that the cluster is working.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   Compute Engine
*   SQL Server licensing through a [premium image](https://cloud.google.com/compute/disks-image-pricing#premiumimages)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new one, or you can select a project that you already created.

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. For details, see the "Cleaning up" 
section at the end of this tutorial.

## Overview

SQL Server Always On availability groups allow users to deploy highly available SQL Server databases with automated failover. Always On availability groups 
are commonly deployed using multiple network subnets in Google Cloud. However, sometimes you need to deploy in a single subnet configuration. For example,
your network design may have been planned to only have one subnet per region, and adding new subnets might be difficult. 

This tutorial is based in part on
[SQL Server failover cluster instance setup](https://cloud.google.com/compute/docs/instances/sql-server/configure-failover-cluster-instance) 
and [SQL Server multi-subnet Always On availability groups](https://cloud.google.com/solutions/deploy-multi-subnet-sql-server).

## Create and configure a Windows domain controller

In this tutorial, you use an existing default VPC network.

An Active Directory domain is used for domain name services and Windows Failover Clustering, which is used by Always On availability groups. 

Having the AD domain controller in the same VPC network is not a requirement, but is a simplification for the purpose of this tutorial.

It is possible to use [Managed Service for Microsoft Active Directory](https://cloud.google.com/managed-microsoft-ad), but it takes an hour to initialize, so 
this tutorial uses a virtual machine (VM) for AD.   

In this tutorial, the domain is `gontoso.com`. The domain controller VM name is `dc-windows`. By default, the Windows computer name matches the VM name, 
`dc-windows`. The VM is created in the `us-central1` default subnet, with the IP address `10.128.0.3`.

1.  In Cloud Shell, create a VM to use as the domain controller:

        gcloud compute instances create "dc-windows" \
            --zone "us-central1-a" \
            --machine-type "n1-standard-2" \
            --private-network-ip "10.128.0.3" \
            --can-ip-forward \
            --image-family "windows-2016" \
            --image-project "windows-cloud" \
            --boot-disk-size "200" \
            --boot-disk-type "pd-standard" \
            --boot-disk-device-name "dc-windows" \
            --metadata sysprep-specialize-script-ps1="Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools;"

1.  [Generate a password](https://cloud.google.com/compute/docs/instances/windows/creating-passwords-for-windows-instances#generating_a_password)
    so that you can connect to the domain controller VM using a local account. Note the username and password for future use.

1.  [Using RDP](https://cloud.google.com/compute/docs/instances/connecting-to-instance#windows), connect to the domain controller VM with 
    your local account username and password.

1.  In [PowerShell with administrator privileges](https://docs.microsoft.com/en-us/powershell/scripting/windows-powershell/starting-windows-powershell?view=powershell-7.1#with-administrative-privileges-run-as-administrator), set the following variables, which are used to configure the Active Directory forest:

        $DomainName = "gontoso.com";
        $DomainMode = "Win2012R2";
        $ForestMode = "Win2012R2";
        $DatabasePath = "C:\Windows\NTDS";
        $LogPath = "C:\Windows\NTDS";
        $SysvolPath = "C:\Windows\SYSVOL";

1.  Set the local `Administrator` account password:

        net user Administrator *

1.  Install and configure the Active Directory forest:

        net user Administrator /active:yes
        Install-ADDSForest -CreateDnsDelegation:$false -DatabasePath $DatabasePath -LogPath $LogPath -SysvolPath $SysvolPath -DomainName $DomainName -DomainMode $DomainMode -ForestMode $ForestMode -InstallDNS:$true -NoRebootOnCompletion:$false -SafeModeAdministratorPassword ((Get-Credential Administrator).Password) -Force:$true;

    When this command prompts you for credentials, use the `Administrator` username and password that you created in a previous step.

## Create the Always On cluster's VMs

1.  In Cloud Shell, create two SQL Server VMs:

        gcloud compute instances create "node-1" \
            --zone "us-central1-f" \
            --machine-type "n1-standard-2" \
            --subnet "default" \
            --private-network-ip "10.128.0.4" \
            --image-family "sql-ent-2016-win-2016" \
            --image-project "windows-sql-cloud" \
            --boot-disk-size "200" \
            --boot-disk-type "pd-ssd" \
            --boot-disk-device-name "node-1" \
            --metadata enable-wsfc=true,sysprep-specialize-script-ps1="Install-WindowsFeature Failover-Clustering -IncludeManagementTools;"

        gcloud compute instances create "node-2" \
            --zone "us-central1-a" \
            --machine-type "n1-standard-2" \
            --subnet "default" \
            --private-network-ip "10.128.0.5" \
            --image-family "sql-ent-2016-win-2016" \
            --image-project "windows-sql-cloud" \
            --boot-disk-size "200" \
            --boot-disk-type "pd-ssd" \
            --boot-disk-device-name "node-2" \
            --metadata enable-wsfc=true,sysprep-specialize-script-ps1="Install-WindowsFeature Failover-Clustering -IncludeManagementTools;"

## Create a file share witness

To provide a tie-breaking vote and achieve a
[quorum](https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-R2-and-2012/jj612870(v=ws.11))
for the failover scenario, create a file share that will act as a witness. For the purposes of this tutorial, you create the file share witness on the 
domain controller VM. 

In a production environment, you should create the witness file share on one of the following:

  - Separate single node in the third zone (`us-central-b` in this scenario)
  - Highly available file share, if the SQL Server node's zone is used

1.  Using RDP, connect to the domain controller VM, `dc-windows`, with the `gontoso.com\Administrator` account.

    If you are using Chrome RDP for Google Cloud, in the **Options** menu, under the **Certificates** list, delete the existing RDP certificates for these
    addresses.

1.  Open PowerShell as administrator.
1.  Create the witness folder:

        New-Item "C:\QWitness" –type directory

1.  Share the folder:

        New-SmbShare -Name "QWitness" -Path "C:\QWitness" -Description "SQL File Share Witness" -FullAccess "Authenticated Users"

## Configuring the cluster VMs

###  Configure the first node

1.  Generate a password for `node-1`. Note the username and password for future use.   
1.  Connect to `node-1` using RDP.   
1.  Open PowerShell as administrator.   
1.  Add a firewall rule to open a port for the health check service:
        
        netsh advfirewall firewall add rule name="Open port for Health Check" dir=in action=allow protocol=TCP localport=59997
        
    This tutorial uses `tcp:59997`. You can change this to a different port, but it must match the health check port that you define later. The health check
    process periodically pings the agent on each cluster node to determine its availability.
            
1.  Set the DNS to the domain controller:
    
        netsh interface ip set dns Ethernet static 10.128.0.3
 
1.  Open Windows firewall ports for the SQL Server availability group:
    
        netsh advfirewall firewall add rule name="5022 for Avail Groups" dir=in action=allow protocol=TCP localport=5022
        netsh advfirewall firewall add rule name="1433 for SQL Server" dir=in action=allow protocol=TCP localport=1433

1.  Add the node to the Active Directory domain that you created earlier:
    
        Add-Computer -DomainName gontoso.com -Restart -Force -Credential gontoso.com\Administrator
            
    When you are prompted for credentials, use the administrator username and password that you set when you configured the domain controller VM in a previous 
    step.

    The machine will restart.  
    
1.  Use RDP to connect to the SQL Server instance by using the credentials for the `gontoso.com\Administrator` account.
1.  Create a new folder for database backups and share it:

        New-Item -ItemType directory -Path C:\SQLBackup
        New-SMBShare -Name SQLBackup -Path C:\SQLBackup -FullAccess "Authenticated Users"

### Configure the second node

1.  Generate a password for `node-2`. Note the username and password for future use.   
1.  Connect to `node-2` using RDP.   
1.  Open PowerShell as administrator.
1.  Add a firewall rule to open a port for the health check service:

        netsh advfirewall firewall add rule name="Open port for Health Check" dir=in action=allow protocol=TCP localport=59997
        
1.  Set the DNS to the domain controller:

        netsh interface ip set dns Ethernet static 10.128.0.3

1.  Open Windows firewall ports for the SQL Server availability group:

        netsh advfirewall firewall add rule name="5022 for Avail Groups" dir=in action=allow protocol=TCP localport=5022
        netsh advfirewall firewall add rule name="1433 for SQL Server" dir=in action=allow protocol=TCP localport=1433
        
1.  Add the node to the Active Directory domain that you created earlier:

        Add-Computer -DomainName gontoso.com -Restart -Force -Credential gontoso.com\Administrator
  
    When you are prompted for credentials, use the Administrator username and password that you set when you configured 
    the domain controller VM in a previous step. 
  
    The machine will restart.  

## Configure the Failover Cluster Manager

In this section, you enable failover clustering on the instances in your availability group, configure one instance to act as the Failover Cluster Manager,
and enable Always On high availability on all instances in the group.

1.  Reconnect to `node-1` using RDP using `gontoso.com\Administrator`.

1.  Open PowerShell as an administrator and create a Windows Server Failover Cluster (WSFC):

        $node1 = "node-1"
        $node2 = "node-2"
        $nameWSFC = "cluster-dbclus" #Name of cluster
        $ipWSFC = "10.128.0.10" #This should un-utilized / free ip
        New-Cluster -Name $nameWSFC -Node $node1, $node2 -NoStorage -StaticAddress $ipWSFC

1.  Enable Always On high availability for both nodes in the cluster:

        Enable-SqlAlwaysOn -ServerInstance $node1 -Force
        Enable-SqlAlwaysOn -ServerInstance $node2 -Force

1.  Add the file share witness:

        Set-ClusterQuorum -FileShareWitness \\dc-windows\QWitness

## Create the availability group

Create a test database and configure it to work with a new availability group. Alternatively, you can specify 
an existing database for the availability group.

1.  Reconnect to `node-1` using RDP using `gontoso.com\Administrator`.   

1.  If you do not have a database configured already, create a test database:

        osql -E -Q "CREATE DATABASE TestDB"
        osql -E -Q "ALTER DATABASE [TestDB] SET RECOVERY FULL"
        osql -E -Q "BACKUP DATABASE [TestDB] to disk = 'C:\SQLBackup\TestDB.bak' with INIT"

1.  Create a database mirrioring endpoint (required for Always On availability groups) in each SQL Server node:   

        osql -S node-1 -E -Q "CREATE ENDPOINT [aodns-hadr] 
            STATE=STARTED
            AS TCP (LISTENER_PORT = 5022, LISTENER_IP = ALL)
        FOR DATA_MIRRORING (
           ROLE = ALL, 
           AUTHENTICATION = WINDOWS NEGOTIATE,
           ENCRYPTION = REQUIRED ALGORITHM AES
        );"

        osql -S node-2 -E -Q "CREATE ENDPOINT [aodns-hadr] 
            STATE=STARTED
            AS TCP (LISTENER_PORT = 5022, LISTENER_IP = ALL)
        FOR DATA_MIRRORING (
           ROLE = ALL, 
           AUTHENTICATION = WINDOWS NEGOTIATE,
           ENCRYPTION = REQUIRED ALGORITHM AES
        );"

1.  Create the availability group:

        osql -S node-1 -E -Q "CREATE AVAILABILITY GROUP [sql-ag]   
        FOR DATABASE TestDB   
        REPLICA ON N'node-1' WITH (ENDPOINT_URL = N'TCP://node-1.gontoso.com:5022',  
            FAILOVER_MODE = AUTOMATIC,  
            AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,   
            BACKUP_PRIORITY = 50,   
            SECONDARY_ROLE(ALLOW_CONNECTIONS = NO),   
            SEEDING_MODE = AUTOMATIC),   
        N'node-2' WITH (ENDPOINT_URL = N'TCP://node-2.gontoso.com:5022',   
            FAILOVER_MODE = AUTOMATIC,   
            AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,   
            BACKUP_PRIORITY = 50,   
            SECONDARY_ROLE(ALLOW_CONNECTIONS = NO),   
            SEEDING_MODE = AUTOMATIC);"

1.  Join secondary node `node-2` to the availability group:

        osql -S node-2 -E -Q "ALTER AVAILABILITY GROUP [sql-ag] JOIN"
        osql -S node-2 -E -Q "ALTER AVAILABILITY GROUP [sql-ag] GRANT CREATE ANY DATABASE"

1.  Create the availability group listener:

        osql -S node-1 -E -Q "USE [master] ALTER AVAILABILITY GROUP [sql-ag] 
        ADD LISTENER N'sql-listener' (WITH IP ((N'10.128.0.20', N'255.255.252.0')) , PORT=1433);"

    The listener must be created with an unused IP address before creating the internal load balancer. Later, the same IP address is allocated to the 
    internal load balancer. If SQL Server detects that the IP address is already in use, then this command to create the listener fails.

1.  Create the Windows Server Failover Cluster health check:

        $cluster_network_name = 'Cluster Network 1'
        $ip_resource_name = 'sql-ag_10.128.0.20'
        $load_balancer_ip = '10.128.0.20'
        [int]$health_check_port = 59997
        Get-ClusterResource $ip_resource_name |
          Set-ClusterParameter -Multiple @{ 'Address'=$load_balancer_ip;
                                            'ProbePort'=$health_check_port;
                                            'SubnetMask'='255.255.240.0';
                                            'Network'=$cluster_network_name;
                                            'EnableDhcp'=0; }
        #restart cluster resource group  
        Stop-ClusterGroup 'sql-ag'
        Start-ClusterGroup 'sql-ag'

     This makes the primary node accept connections on port `59997`, which is used by the internal load balancer for health checks.

## Create an internal load balancer

An [internal load balancer](https://cloud.google.com/compute/docs/load-balancing/internal#deploying_internal_load_balancing) 
provides a single IP address for SQL Server. The load balancer listens for requests and routes network 
traffic to the active cluster node. It knows which node is the active node because a health check runs for each node. 
Only the active node responds as healthy. If the active node goes down, then the other Always On availability group node activates. The health checker 
receives the signal, and traffic is redirected to the other node.

1.  Create two instance groups, and add one SQL Server node to each group:

        gcloud compute instance-groups unmanaged create wsfc-group-f --zone us-central1-f
        gcloud compute instance-groups unmanaged add-instances wsfc-group-f --instances node-1 --zone us-central1-f

        gcloud compute instance-groups unmanaged create wsfc-group-a --zone us-central1-a
        gcloud compute instance-groups unmanaged add-instances wsfc-group-a --instances node-2 --zone us-central1-a

    These instance groups act as backends that the load balancer can direct traffic to.

1.  Create a health check that the load balancer can use to determine which is the active node:

        gcloud compute health-checks create tcp sql-healthcheck \
            --check-interval="2s" \
            --healthy-threshold=1 \
            --unhealthy-threshold=2 \
            --port=59997 \
            --timeout="1s"

1.  Add a firewall rule to allow the health check:

        gcloud compute firewall-rules create allow-health-check \
            --source-ranges 130.211.0.0/22,35.191.0.0/16 \
            --allow tcp

1.  Create one backend service and add the two backend instance groups:

        gcloud compute backend-services create wsfcbackend \
            --load-balancing-scheme internal \
            --region us-central1 \
            --health-checks sql-healthcheck \
            --protocol tcp
    
        gcloud compute backend-services add-backend wsfcbackend \
            --instance-group wsfc-group-a \
            --instance-group-zone us-central1-a \
            --region us-central1
    
        gcloud compute backend-services add-backend wsfcbackend \
            --instance-group wsfc-group-f \
            --instance-group-zone us-central1-f \
            --region us-central1    

1.  Create an internal load balancer to forward requests to the IP address of the listener for the active node in the Always On availability group: 

        gcloud compute forwarding-rules create wsfc-forwarding-rule \
            --load-balancing-scheme internal \
            --ports 1433 \
            --region us-central1 \
            --backend-service wsfcbackend \
            --address 10.128.0.20

    By design, the internal load balancer will show only one instance group healthy at any time.
    
    ![ILB Created](https://storage.googleapis.com/gcp-community/tutorials/sql-server-ao-single-subnet/ILB-Image.png)

## Simulate failure to test failover

To simulate failure, execute this SQL query on the secondary node to make it primary:

    osql -S node-2 -E -Q "ALTER AVAILABILITY GROUP [sql-ag] FAILOVER;"

The internal load balancer starts pointing to this node automatically.

Another way to test the failover mechanism is to shut down or reset the primary node.

![ILB Updated](https://storage.googleapis.com/gcp-community/tutorials/sql-server-ao-single-subnet/ILB-Moved.png)

## Cleaning up

The easiest way to avoid incurring charges to your Google Cloud account for the resources used in this tutorial is to delete the project that you created for
the tutorial.

You can delete a project with the following command, where `[PROJECT_ID]` is your Google Cloud project ID:

    gcloud projects delete [PROJECT_ID]

## What's next

*   [Deploying Microsoft SQL Server for multi-regional disaster recovery](https://cloud.google.com/solutions/deploying-microsoft-sql-server-multi-regional-disaster-recovery)
*   Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
