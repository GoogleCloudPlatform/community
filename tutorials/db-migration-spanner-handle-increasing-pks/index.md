---
title: Database migration from MySQL to Cloud Spanner, handling auto-incrementing keys
description: Prevent hotspots in Cloud Spanner when migrating auto-incrementing primary keys, using STRIIM.
author: shashank-google,zk-gt
tags: mysql, spanner, cloud spanner, striim, migration, zero downtime, data migration
date_published: 2021-05-20
---

Shashank Agarwal, Zeeshan Khan, and David Ng | Database Migration Engineers | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial you learn about migrating databases that have auto-incrementing primary keys. The primary key uniquely identifies each row in a table. If you
insert records with a monotonically increasing integer as the key, you always insert at the end of your key space. This is undesirable because Cloud Spanner 
divides data among servers by key ranges, which means that your inserts are directed at a single server, creating a *hotspot*. This applies even when an existing
database needs to be migrated. Unless mitigated, these hotspots can lead to slow data ingestion from MySQL to Cloud Spanner.   

This tutorial implements a [bit-reverse](https://cloud.google.com/spanner/docs/schema-design#bit_reverse_primary_key) technique to reliably convert incrementing
keys to prevent hotspots in Cloud Spanner. The core idea is to write a deterministic mathematical function that gives a unique non-incrementing value. Reversing
the bits maintains unique values across the primary keys. You only need to store the reversed value, because you can recalculate the original value in your 
application code, if needed.   

Cloud Spanner does not provide auto-generated keys, so applications need to generate primary keys after migration. This tutorial assumes that the applications
use [UUID](https://cloud.google.com/spanner/docs/schema-design#uuid_primary_key) for generating keys after the migration to Cloud Spanner.  

This tutorial uses [Striim](https://www.striim.com/) to perform the zero-downtime data migration from MySQL to Cloud Spanner.  

## Objectives

*   Create and set up a Cloud SQL for MySQL instance with auto-incrementing primary keys.
*   Create and set up a Cloud Spanner instance.
*   Deploy and configure Striim for performing data migration.
*   Add custom functions to Striim for real-time data transformation.
*   Create a Striim pipeline for the initial loading of data.
*   Create a Striim pipeline for continuous replication of data.

## Costs

Ths tutorial requires a Striim license, which you can get with a free trial period through the
[Google Cloud Marketplace](https://console.cloud.google.com/marketplace/details/striim/striim).

This tutorial uses billable components of Google Cloud, including the following:

*   Compute Engine (for running Striim)
*   Cloud SQL for MySQL
*   Cloud Spanner

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.   

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). You can create a
new project, or you can select a project that you already created.

1.  [Select or create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  [Enable billing for your project](https://support.google.com/cloud/answer/6293499#enable-billing).
1.  [Enable the Compute Engine, Cloud SQL, and Cloud Spanner APIs](https://console.cloud.google.com/flows/enableapi?apiid=compute.googleapis.com,spanner.googleapis.com,sqladmin.googleapis.com).
1.  In the Cloud Console, activate [Cloud Shell](https://cloud.google.com/shell/docs/launching-cloud-shell#launching_from_the_console).

    Cloud Shell provides an interactive shell that includes the `gcloud` command-line interface, which you use to run the commands in this tutorial.

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created. For details, see the "Cleaning up" 
section at the end of this tutorial.

## Set up the source database with Cloud SQL for MySQL

1.  Create a Cloud SQL instance:

        gcloud sql instances create mysql-57  \
            --database-version=MYSQL_5_7 \
            --tier=db-n1-standard-1  \
            --region=us-central1 \
            --root-password=password123

1.  Enable binary logging for change data capture (CDC):

        gcloud sql instances patch mysql-57 --backup-start-time 00:00
        gcloud sql instances patch mysql-57 --enable-bin-log    

1.  Connect to the Cloud SQL for MySQL instance:

        gcloud sql connect mysql-57 --user=root
        
    Enter the password (`password123`) when you are prompted.

1.  Create a database and table:

        CREATE DATABASE employeedb;
        use employeedb;
        CREATE TABLE `signin_log` (
          `id` int not null AUTO_INCREMENT,
          `employee_email` varchar(200) DEFAULT NULL,
          `details` varchar(500) DEFAULT NULL,
          PRIMARY KEY (`id`)
        );
    
1.  Insert sample data rows:

        INSERT INTO signin_log (employee_email, details) values ('test-1@email.com', 'ip address a.b.c.d');
        INSERT INTO signin_log (employee_email, details) values ('test-2@email.com', 'new ip address 1');

## Set up the target database with Cloud Spanner

1.  Create a Cloud Spanner instance

        gcloud spanner instances create spanner-tgt \
            --config=regional-us-central1 \
            --nodes=1 \
            --description=spanner-tgt

1.  Create the database and empty table:

        gcloud spanner databases create employeedb \
        --instance=spanner-tgt \
        --ddl='CREATE TABLE signin_log (id STRING(36), employee_email STRING(200), details STRING(500)) PRIMARY KEY (id)'
       
The `employee_id` column has been changed to `STRING` in this example, so that the application can generate UUID keys after the migration.

## Deploy and configure the middleware, Striim

1.  [Deploy a Striim instance from  Google Cloud Marketplace](https://console.cloud.google.com/marketplace/product/striim/striim-spanner).

1.  Click **Launch**.

1.  Keep the default configuration, and click **Deploy**.

    When deployment is complete, get a link to a Striim instance along with administrator username and password. You can also access this information from the 
    [Deployment Manager](https://console.cloud.google.com/dm/deployments).

    ![Striim Credentials](https://storage.googleapis.com/gcp-community/tutorials/db-migration-spanner-handle-increasing-pks/3_striim_deployment_manager.png)

1.  Set the zone to the zone of the VM that is running Striim:
 
        STRIIM_VM_ZONE=us-central1-f
        
        gcloud config set compute/zone $STRIIM_VM_ZONE

1.  To allow Striim to communicate with Cloud SQL for MySQL, [add the Striim server's IP address](https://cloud.google.com/sql/docs/mysql/connect-external-app)
    to the Cloud SQL for MySQL instance's authorized networks.

        gcloud sql instances patch mysql-57 \
            --authorized-networks=$(gcloud compute instances describe striim-spanner-1-vm \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)' \
            --zone=$STRIIM_VM_ZONE)

1.  Deploy [the MySQL driver (MySQL Connector/J)](https://cloud.google.com/architecture/partners/continuous-data-replication-cloud-spanner-striim#setting_up_mysql_connector_j):

    1.  Connect to the VM running Striim using SSH:
    
            gcloud compute ssh striim-spanner-1-vm
    
    1.  Download the MySQL driver (MySQL Connector/J) to the instance and extract the contents of the file:

            wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-5.1.49.tar.gz
            tar -xvzf mysql-connector-java-5.1.49.tar.gz

    1.  Copy the file to the Striim library path, allow it to be executable, and change ownership of the file that you downloaded:

            sudo cp ~/mysql-connector-java-5.1.49/mysql-connector-java-5.1.49.jar /opt/striim/lib
            sudo chmod +x /opt/striim/lib/mysql-connector-java-5.1.49.jar
            sudo chown striim /opt/striim/lib/mysql-connector-java-5.1.49.jar

    1.  To load the new library, restart the Striim server:
    
            sudo systemctl stop striim-node
            sudo systemctl stop striim-dbms
            sudo systemctl start striim-dbms
            sudo systemctl start striim-node

1.  Create a service account key for Striim to authenticate with Cloud Spanner: 

        export PROJECT=$(gcloud info --format='value(config.project)')

        export PROJECT_NUMBER=$(gcloud projects list \
            --filter="projectId=$PROJECT" --format="value(projectNumber)")
           
        export compute_sa=$PROJECT_NUMBER-compute@developer.gserviceaccount.com

        gcloud iam service-accounts keys create ~/striim-spanner-key.json --iam-account $compute_sa

    This creates a service account key called `striim-spanner-key.json` on your Cloud Shell home path.

1.  Move the service account key to the `/opt/striim_ directory` on the Striim instance:

        gcloud compute scp ~/striim-spanner-key.json striim-spanner-1-vm:~
        
1.  Grant the `striim` user owner permissions:

        gcloud compute ssh striim-spanner-1-vm \
            -- 'sudo cp ~/striim-spanner-key.json /opt/striim && \
            sudo chown striim /opt/striim/striim-spanner-key.json'

## Migrate data using Striim

Data migration is a two-phase process: 

1. Initial load of data
2. Continuous replication with change data capture (CDC)

This section includes custom functions written in Java for manipulating data during both of these phases. During the initial load of data, you use a custom
bit-reverse function. During replication, you use a custom string conversion function.

### Add the bit-reverse function to Striim

1.  Connect to the VM that's running Striim with SSH:

        gcloud compute ssh striim-spanner-1-vm

1.  Run the following command to add a bit-reverse function to the `CustomFunctions.java` file:

        cat > CustomFunctions.java << EOF
        public abstract class CustomFunctions {
        
        //used by STRIIM to convert MySQL's int ids to bit reversed strings
        public static String bitReverseInt(Integer id) {
               return String.valueOf(Integer.reverse(id));
               }
        }
        EOF

1.  Compile and package the code:

        javac CustomFunctions.java
        jar -cf CustomFunctions.jar CustomFunctions.class CustomFunctions.java

1.  Move the `CustomFunctions.jar` file to the Striim instance's `/opt/striim/lib/` directory:

        sudo cp CustomFunctions.jar /opt/striim/lib/
        sudo chown striim /opt/striim/lib/CustomFunctions.jar
        sudo chmod +x /opt/striim/lib/CustomFunctions.jar

1.  Restart the Striim application so that it loads this JAR package: 

        sudo systemctl stop striim-node
        sudo systemctl stop striim-dbms
        sudo systemctl start striim-dbms
        sudo systemctl start striim-node

### Create the initial load pipeline

The initial load job bulk-loads existing data. It loads all data existing at job start time. When the data is loaded, the job quiesces (pauses).
Any changes (updates, deletes, inserts, append) to data after the job start time will not be replicated by this job.

1.  Get the MySQL IP address, which you use in a later step:

        gcloud sql instances list --filter=name=mysql-57

1.  Save the following code to a new `mysql_to_spanner_initial_load.tql` file on your local computer:

        drop APPLICATION mysql_to_spanner_initial_load CASCADE;

        IMPORT STATIC CustomFunctions.*;

        CREATE APPLICATION mysql_to_spanner_initial_load;

        CREATE FLOW sample1;

        CREATE OR REPLACE SOURCE mysql_dbreader USING Global.DatabaseReader (
          Username: 'root',
          DatabaseProviderType: 'Default',
          FetchSize: 10,
          adapterName: 'DatabaseReader',
          QuiesceOnILCompletion: true,
          Password_encrypted: 'false',
          ConnectionURL: 'jdbc:mysql://PRIMARY_IP:3306/employeedb',
          Tables: 'employeedb.signin_log',
          Password: 'password123',
          ReturnDateTimeAs: 'String')
        OUTPUT TO sample_raw;

        CREATE STREAM SampleModifiedData OF Global.WAEvent;

        CREATE CQ POPULATE_SAMPLE_TABLE
        INSERT INTO SampleModifiedData
        SELECT * from sample_raw
        MODIFY(data[0] = bitReverseInt(data[0]));

        CREATE TARGET spanner_sample USING Global.SpannerWriter (
          InstanceID: 'spanner-tgt',
          ServiceAccountKey: '/opt/striim/striim-spanner-key.json',
          BatchPolicy: 'EventCount: 100, Interval: 10s',
          ParallelThreads: '',
          Tables: 'employeedb.signin_log,employeedb.signin_log' )
        INPUT FROM SampleModifiedData;

        END FLOW sample1;

        END APPLICATION mysql_to_spanner_initial_load;

1.  Go to the Striim web interface and log in.

    If needed, go to the [Deployment Manager page](https://console.cloud.google.com/dm/deployments) to get the URL for the Striim web interface and credentials.
    
1.  Click the **☰** menu in the upper left and select **Apps**.
1.  Click **+ Add App** in the upper right.
1.  Click **Import existing app**, choose the `mysql_to_spanner_initial_load.tql` file, and click **Import**.
1.  Click the `mysql_dbreader` adaptor and replace `Primary_IP` in the **Connection URL** field with the Cloud SQL for MySQL IP address.
    
    ![initial load](https://storage.googleapis.com/gcp-community/tutorials/db-migration-spanner-handle-increasing-pks/4_striim_initial_load.png)

1.  Click **Save**.

1.  Deploy the application using default values: Choose **Created > Deploy App > Deploy**.

    ![initial load deploy](https://storage.googleapis.com/gcp-community/tutorials/db-migration-spanner-handle-increasing-pks/5_striim_deploy.png)

1.  Start the application: Choose **Deployed > Start App**.

    You should see rows being replicated through Striim and inserted to Cloud Spanner.

1.  In Cloud Spanner, verify that rows have been written with bit-reversed ID values.

    ![initial complete](https://storage.googleapis.com/gcp-community/tutorials/db-migration-spanner-handle-increasing-pks/6_spanner_il_complete.png)

### Create the continuous replication pipeline

After the initial load is complete, you can deploy a CDC (change data capture) pipeline to continuously replicate any new changes into Cloud Spanner that are
made after the initial load job was started. This keeps Cloud SQL for MySQL and Spanner synchronized while the CDC application is running. It reads data from
the Cloud SQL for MySQL binary logs using the Striim MysqlReader adapter.  

**Note**: In production, you use the `StartTimestamp` property to specify the binary log position (the timestamp at which initial load was started) from which 
the CDC application should start replicating. You should also create a [Checkpoint table](https://www.striim.com/docs/en/spanner-writer.html) so that Striim can 
recover from a failure. However, these concepts are out of scope for this tutorial.

The steps in this section are abbreviated to highlight only the portions that differ from the previous section. Refer to the previous section for details of
interacting with the user interface.

1.  Import the following code for the CDC pipeline and replace `Primary_IP` with the IP address for Cloud SQL for MySQL. 

        drop APPLICATION mysql_to_spanner_cdc CASCADE;

        IMPORT STATIC CustomFunctions.*;

        CREATE APPLICATION mysql_to_spanner_cdc;

        CREATE FLOW sample1_cdc;

        CREATE SOURCE mysql_cdc_source USING MysqlReader  (
        ConnectionURL: 'jdbc:mysql://PRIMARY_IP:3306/employeedb',
          Username: 'root',
          Compression: false,
          Password_encrypted: 'false',
          connectionRetryPolicy: 'retryInterval=30, maxRetries=3',
          FilterTransactionBoundaries: true,
          Tables: 'employeedb.signin_log',
          Password: 'password123',
          SendBeforeImage: true
          --change this timestamp
          --,StartTimestamp: '2021-MAR-19 13:00:00'
          )
        OUTPUT TO sample_raw_cdc;

        CREATE STREAM SampleModifiedDataCDC OF Global.WAEvent;

        CREATE CQ POPULATE_SAMPLE_TABLE_CDC
        INSERT INTO SampleModifiedDataCDC
        SELECT * FROM sample_raw_cdc
        MODIFY(data[0] = bitReverseInt(data[0]));

        CREATE TARGET spanner_sample_cdc USING Global.SpannerWriter (
          InstanceID: 'spanner-tgt',
          --CheckpointTable: 'CHKPOINT',
          BatchPolicy: 'EventCount: 100, Interval: 10s',
          ParallelThreads: '',
          ServiceAccountKey: '/opt/striim/striim-spanner-key.json',
          Tables: 'employeedb.signin_log,employeedb.signin_log' )
        INPUT FROM SampleModifiedDataCDC;

        END FLOW sample1_cdc;

        END APPLICATION mysql_to_spanner_cdc;

1.  Deploy and start the application.

3.  Connect to MySQL and insert a few rows:

        gcloud sql connect mysql-57 --user=root
  
        use employeedb;
        insert into signin_log (employee_email, details) values ('cdc-test-3@email.com', 'ip 3333 ');
        insert into signin_log (employee_email, details) values ('cdc-test-4@email.com', 'ip 4444');
        insert into signin_log (employee_email, details) values ('cdc-test-5@email.com', 'ip 5555');

1.  Verify that the data has been replicated into Cloud Spanner.

    ![spanner cdc complete](https://storage.googleapis.com/gcp-community/tutorials/db-migration-spanner-handle-increasing-pks/7_spanner_cdc_complete.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next
- Learn more about [choosing a primary key in Cloud Spanner](https://cloud.google.com/spanner/docs/schema-and-data-model#choosing_a_primary_key).
- Learn about [using Striim for continuous data replication to Cloud Spanner](https://cloud.google.com/solutions/partners/continuous-data-replication-cloud-spanner-striim).
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
