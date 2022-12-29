---
title: Migrate an Oracle database to Cloud SQL for PostgreSQL using Datastream
description: Learn how to use Ora2Pg, Datastream, and Dataflow to migrate a database from Oracle to Cloud SQL for PostgreSQL.
author: ktchana
tags: datastream, dms, database migration, ora2pg, dataflow, cloud sql, postgresql, oracle
date_published: 2021-05-26
---

Thomas Chan | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to migrate a database from Oracle® to Cloud SQL for PostgreSQL using [Datastream](https://cloud.google.com/datastream/), a
[Dataflow](https://cloud.google.com/dataflow/) template, a customized setup for [Ora2Pg](https://ora2pg.darold.net/), and an open source
[validation tool developed by Google](https://github.com/GoogleCloudPlatform/professional-services-data-validator).

![Migration pipeline using Datastream](https://storage.googleapis.com/gcp-community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg-datastream-architecture.png)

This tutorial is part of a series that shows you how to migrate a database from Oracle to Cloud SQL for PostgreSQL. For detailed discussions of migration-related
concepts, see the other documents in the series:

*   [Migrating Oracle users to Cloud SQL for PostgreSQL](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
*   [Setting up Cloud SQL for PostgreSQL for production use](https://cloud.google.com/solutions/setting-up-cloud-sql-for-postgresql-for-production)

This tutorial is intended for a technical audience who is responsible for database management and migration. This tutorial assumes that you're familiar with 
concepts related to database administration, including [schema conversion](https://en.wikipedia.org/wiki/Schema_migration) and
[change data capture](https://en.wikipedia.org/wiki/Change_data_capture). This tutorial also assumes that you have some familiarity with shell scripts and basic 
knowledge of Google Cloud.

## Objectives

*   Understand the process, prerequisites, notable behaviors, and limitations of the method used by this tutorial.
*   Set up a Google Cloud project with the following resources:
    *   a bastion VM for schema conversion
    *   a [Cloud SQL for PostgreSQL](https://cloud.google.com/sql) database as the target database
    *   a [Cloud Storage](https://cloud.google.com/storage/) bucket to store schema conversion output and replicated data
    *   a [Pub/Sub](https://cloud.google.com/pubsub/) topic subscription to track changes to the Cloud Storage bucket
*   Create a demonstration schema in the Oracle database to be used for data migration.
*   Perform schema conversion using Ora2pg.
*   Create a Datastream stream to perform initial loads and change data capture (CDC) replication from the source database.
*   Create a template-based Dataflow job to load data into the target database.
*   Verify that the replication is successful.
*   Validate the correctness of the replicated data.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Datastream](https://cloud.google.com/datastream/pricing)
*   [Dataflow](https://cloud.google.com/dataflow/pricing)
*   [Pub/Sub](https://cloud.google.com/pubsub/pricing)
*   [Cloud Storage](https://cloud.google.com/storage/pricing)
*   [Compute Engine](https://cloud.google.com/compute/all-pricing)
*   [Cloud SQL](https://cloud.google.com/sql/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Source database requirements

For the migration to be successful, you must ensure that several requirements are satisfied on the source Oracle database, to ensure compatibility with the 
toolchain used in this tutorial. For up-to-date information about version requirements, see the
[Datastream documentation](https://cloud.google.com/datastream/docs/sources#versionsfororaclesourcedb).

*   **Version**: Oracle 10g v10.2, 11g v11.2.0.4, 12c v12.1.0.2/1, 18c, or 19c

*   **Single instance or Real Application Clusters (RAC)**: Both are supported. The Single Client Access Name (SCAN) listener is not supported; use the
    local or VIP listener instead.

*   **Multi-tenancy**: Container databases (CDB), pluggable databases (PDB), and autonomous databases are not supported.

*   **Change replication**: [LogMiner with supplemental logging](https://cloud.google.com/datastream/docs/configure-your-source-database) is required.

*   **Size**:

    *   Tables of up to 100 GB.

        This is a soft limit, and Datastream will attempt to perform backfill on any table that you supply. However, we recommend
        that you use tools such as [Ora2Pg](http://ora2pg.darold.net/) to perform initial loads for tables that exceed this soft limit.

*   **Throughput**: Approximately 5 MB per second, with a maximum 3 MB row size limit.

    *   Throughput is a soft limit. Larger throughputs may incur replication delays and potentially lost log positions.
    *   Rows larger than 3 MB are discarded.

*   **Network connectivity**: For the migration to work, both the Datastream service and a Compute Engine instance hosting the migration utilities need to 
    connect to the source Oracle database. For details, see the
    [Datastream network connectivity options](https://cloud.google.com/datastream/docs/source-network-connectivity-options).

## Notable behaviors and limitations

This section describes notable behaviors and limitations of the migration process. It is important for you to understand these behaviors and limitations and plan
ahead to avoid running into problems during the migration. For up-to-date information about known limitations, see the
[Datastream documentation](https://cloud.google.com/datastream/docs/sources#oracleknownlimitations).

*   **Primary key and ROWID**: We recommend that you have a primary key on all tables.

    Migration will work for all tables, with the following caveats:
    
    *   For tables that don’t have a primary key, the Oracle `ROWID` is added to each table as a BIGINT primary key column to work as a substitute for a primary 
        key. `ROWID` is stable for the life of a row, but it can change during Oracle table cleanup. The PostgreSQL row ID column will be stable to use as a 
        primary key after promotion.
    *   For tables with a primary key, the row ID will be copied as an indexed BIGINT column. It is required to maintain consistency during CDC replication.

*   **DML only**: No DDL changes are supported during replication.

*   **Column support**:

    *   Columns of data types ANYDATA, BLOB, CLOB, LONG/LONG RAW, NCLOB, UDT, UROWID, XMLTYPE aren't supported, and will be replaced with NULL values.

    *   For Oracle database 11g, tables that have columns of data types ANYDATA or UDT aren't supported, and the entire table won't be replicated.

*   Deferred constraints are converted to non-deferred constraints as part of the standard conversion. This can be customized by setting `FKEY_DEFERRABLE=0` in
    the `ora2pg.conf` configuration file.
    
*   **Unsupported features in the Oracle database**:

    *   External tables
    *   DBLinks
    *   Index Only Tables (IOTs)
    *   Oracle Label Security (OLS)

*   **Replication lag:** Datastream uses Oracle LogMiner to capture changes from archived redo log files. Recently changed data will not be visible to Datastream
    until a log switch occurs and the current redo log file is archived. It is important to
    [force a log switch](https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-the-redo-log.html)
    before the final migration cutover to make sure that Datastream captures and replicates all changes to the destination Cloud SQL instance.

## Set up a Google Cloud project

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make
cleanup easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google Cloud project.

When you finish this tutorial, you can avoid continued billing by deleting the resources you created. For instructions, see the "Cleaning up" section at the end
of this tutorial.

## Deploy migration resources

1.  In [Cloud Shell](https://cloud.google.com/shell), enable APIs for the Compute Engine, Cloud Storage, Dataflow, Cloud SQL, and Datastream services:

        gcloud services enable \
            compute.googleapis.com \
            storage.googleapis.com \
            dataflow.googleapis.com \
            sqladmin.googleapis.com \
            pubsub.googleapis.com \
            datastream.googleapis.com \
            servicenetworking.googleapis.com

1.  Set environment variables: 

        # Google Cloud project to use for this tutorial
        export PROJECT_ID="[YOUR_PROJECT_ID]"

        # Google Cloud region to use for Cloud SQL, Compute Engine, Datastream, and Cloud Storage bucket
        export GCP_REGION_ID="[YOUR_GOOGLE_CLOUD_REGION]"

        # Google Cloud zone to use for hosting the bastion Compute Engine instance
        export GCP_ZONE_ID="[YOUR_GOOGLE_CLOUD_ZONE]"

        # Name of the bastion VM
        export BASTION_VM_NAME="[NAME_OF_BASTION_COMPUTE_ENGINE_INSTANCE]"

        # Name of the Cloud Storage bucket used to host schema conversion outputs
        export GCS_BUCKET="[YOUR_CLOUD_STORAGE_BUCKET]"

        # Name of the Pub/Sub topic for Cloud Storage notifications
        export PUBSUB_TOPIC="[YOUR_PUB_SUB_TOPIC]"
    
        # ID of the Cloud SQL for PostgreSQL instance
        export CLOUD_SQL="[CLOUD_SQL_INSTANCE_ID]"

        # Target Cloud SQL for PostgreSQL version (e.g., POSTGRES_12)
        export CLOUD_SQL_PG_VERSION="[CLOUD_SQL_PG_VERSION]"
        
        # Cloud SQL Database Password
        export DATABASE_PASSWORD="[DATABASE_PASSWORD]

1.  Create the bastion Compute Engine VM instance:

        gcloud compute instances create ${BASTION_VM_NAME} \
            --zone=${GCP_ZONE_ID} \
            --boot-disk-device-name=${BASTION_VM_NAME} \
            --boot-disk-size=10GB \
            --boot-disk-type=pd-balanced \
            --image-family=debian-10 \
            --image-project=debian-cloud

1.  Create the Cloud Storage bucket used to host schema conversion output:

        gsutil mb -p ${PROJECT_ID} "gs://${GCS_BUCKET}"

1.  Set up Pub/Sub notifications for Cloud Storage, which are used by the Dataflow template to pick up changes output by Datastream:

        export PUBSUB_SUBSCRIPTION=${PUBSUB_TOPIC}-subscription

        gcloud pubsub topics create ${PUBSUB_TOPIC} --project=${PROJECT_ID}

        gcloud pubsub subscriptions create ${PUBSUB_SUBSCRIPTION} \
            --topic=${PUBSUB_TOPIC} \
            --project=${PROJECT_ID}

        gsutil notification create -f "json" \
            -p "ora2pg/" \
            -t "projects/${PROJECT_ID}/topics/${PUBSUB_TOPIC}" \
            "gs://${GCS_BUCKET}"

1.  Create the target Cloud SQL for PostgreSQL instance and give the associated service account the necessary role:

        gcloud compute addresses create psql-reserve-ip-range \
            --global \
            --purpose=VPC_PEERING \
            --prefix-length=16 \
            --description="Test for Oracle Migration" \
            --network=default \
            --project=${PROJECT_ID}
        
        gcloud beta sql instances create ${CLOUD_SQL} \
            --database-version=${CLOUD_SQL_PG_VERSION} \
            --cpu=4 --memory=3840MiB \
            --region=${GCP_REGION_ID} \
            --no-assign-ip \
            --network=default \
            --root-password=${DATABASE_PASSWORD} \
            --project=${PROJECT_ID}
            
        SERVICE_ACCOUNT=$(gcloud sql instances describe ${CLOUD_SQL} --project=${PROJECT_ID} | grep 'serviceAccountEmailAddress' | awk '{print $2;}')
        
        gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectViewer "gs://${GCS_BUCKET}"

## Create the demonstration schema for migration

In the source Oracle database, create the `demoapp` schema that will be used for the migration.

1.  Connect to the source Oracle database as the `SYS` (administrator) user:

        conn / as sysdba
        
1.  Create and populate the schema `demoapp`:

        create user demoapp;
        grant unlimited tablespace to demoapp;
        create table demoapp.demotable (id number primary key, name varchar2(10));
        insert into demoapp.demotable values (1, 'A');
        insert into demoapp.demotable values (2, 'B');
        commit;

1.  From the SQL command line, examine the table `demotable`:

        select * from demoapp.demotable;
        
    The output should be the following:

                 ID NAME
         ---------- ----------
                  1 A
                  2 B

## Set up the bastion VM with Oracle Access

The bastion VM is used during the migration process to execute Ora2Pg queries, as well as for executing validations before the cutover to the new database.

1.  From Cloud Shell, connect to the VM with SSH:

        gcloud compute ssh ${BASTION_VM_NAME} \
            --zone ${GCP_ZONE_ID} \
            --project ${PROJECT_ID}

1.  In the VM shell, install Docker:

        sudo apt-get update -y
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg-agent \
            software-properties-common
        curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
        sudo add-apt-repository -y \
            "deb [arch=amd64] https://download.docker.com/linux/debian \
            $(lsb_release -cs) \
            stable"
        sudo apt-get update -y
        sudo apt-get install -y docker-ce docker-ce-cli
        sudo usermod -aG docker ${USER}

1.  Exit the current VM shell and start a new shell session to pick up the new `docker` user group.

1.  Set environment variables:

        # Google Cloud project to use for this tutorial
        export PROJECT_ID="[YOUR_PROJECT_ID]"

        # Google Cloud region to use for Cloud SQL, Compute Engine, Datastream, and Cloud Storage bucket
        export GCP_REGION_ID="[YOUR_GOOGLE_CLOUD_REGION]"
    
        # Google Cloud zone to use for hosting the bastion Compute Engine instance
        export GCP_ZONE_ID="[YOUR_GOOGLE_CLOUD_ZONE]"
    
        # Name of the Cloud Storage bucket used to host schema conversion output
        export GCS_BUCKET="[YOUR_CLOUD_STORAGE_BUCKET]"
    
        # ID of the Cloud SQL for PostgreSQL instance
        export CLOUD_SQL="[YOUR_CLOUD_SQL_INSTANCE_ID]"
    
        # Version of Ora2Pg (e.g., 21.0)
        export ORA2PG_VERSION="[ORA2PG_VERSION]"
    
        # Version of Oracle Instant Client (e.g., 12.2)
        export ORACLE_ODBC_VERSION="[ORACLE_ODBC_VERSION]"
    
        # Space-separated list of Oracle schemas to export (e.g., "HR OE"). Leave blank to export all schemas.
        export ORACLE_SCHEMAS="[SPACE_SEPARATED_ORACLE_SCHEMA_LIST]"
    
        # Space-separated list of Oracle object types to export (e.g., "TABLE VIEW"). Leave blank to export all object types supported by Ora2Pg.
        export ORACLE_TYPES="[SPACE_SEPARATED_OBJECT_TYPES]"

1.  Install `git` and use it to clone the repository:

        sudo apt-get install git -y
        git clone https://github.com/GoogleCloudPlatform/community.git
     
1.  Download Oracle Instant Client packages:

    1.  Go to the [Oracle Instant Client download page](https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html).
    1.  Download the RPM packages for your source database version.

        For example, download the following files for Oracle 12c:

        *   `oracle-instantclient12.2-basiclite-12.2.0.1.0-1.x86_64.rpm`
        *   `oracle-instantclient12.2-devel-12.2.0.1.0-1.x86_64.rpm`
        *   `oracle-instantclient12.2-odbc-12.2.0.1.0-2.x86_64.rpm`

    1.  Copy the RPM files to `community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg/oracle/` on the bastion VM.

1.  Go to the `ora2pg` directory:

        cd ~/community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg

1.  Build the Ora2Pg Docker image:

        docker build . \
            -f Ora2PGDockerfile \
            -t ora2pg \
            --build-arg ORA2PG_VERSION=${ORA2PG_VERSION} \
            --build-arg ORACLE_ODBC_VERSION=${ORACLE_ODBC_VERSION}

## Perform schema conversion

The wrapper script `ora2pg.sh` takes the `ORACLE_SCHEMAS` and `ORACLE_TYPES` environment variables as input and runs the `ora2pg` container to perform the 
schema export and conversion process. The result is a PostgreSQL-compliant SQL file stored in `ora2pg/data/output.sql`. This file is then uploaded to the Cloud
Storage bucket and imported to the target PostgreSQL instance.

1.  On the bastion VM, edit the `community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg/ora2pg/config/ora2pg.conf` configuration file to set up 
    database connection details, target PostgreSQL version, and Oracle schema to export.
    
    Refer to the [Ora2Pg documentation](http://ora2pg.darold.net/documentation.html) for detailed setting descriptions.
    
    Here is a sample configuration file:

        ####################  Ora2Pg configuration file   #####################

        #------------------------------------------------------------------------------
        # INPUT SECTION (Oracle connection or input file)
        #------------------------------------------------------------------------------

        # Set the Oracle home directory
        ORACLE_HOME    /usr/local/oracle/10g

        # Set Oracle database connection (datasource, user, password)
        ORACLE_DSN       dbi:Oracle:host=<ORACLE_HOST>;sid=<ORACLE_DATABASE>;port=<ORACLE_PORT>
        ORACLE_USER     <ORACLE_USER>
        ORACLE_PWD      <ORACLE_PASSWORD>

        PG_VERSION      <CLOUD_SQL_PG_VERSION>

        #------------------------------------------------------------------------------
        # SCHEMA SECTION (Oracle schema to export and use of schema in PostgreSQL)
        #------------------------------------------------------------------------------
        SCHEMA      demoapp

        # Export Oracle schema to PostgreSQL schema
        EXPORT_SCHEMA 1
        ROLES 1

        # This overrides the owner of the target schema to postgres.
        # Removing this parameter instructs Ora2Pg to alter the owner of the schema to a user of the same name.
        # You need to manually create the owner user in PostgreSQL before import.
        FORCE_OWNER postgres

        USE_RESERVED_WORDS 1
        FKEY_DEFERRABLE 1

        #------------------------------------------------------------------------------
        # EXPORT SECTION (Export type and filters)
        #------------------------------------------------------------------------------

        TYPE            TABLE

        OUTPUT_DIR             /data
        OUTPUT                 output.sql
        FILE_PER_INDEX         0
        FILE_PER_CONSTRAINT    0
        FILE_PER_FKEYS         1
        FILE_PER_TABLE         0

1.  Run the `ora2pg.sh` wrapper script to perform schema export and conversion:

        cd ~/community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg
    
        ./ora2pg.sh

1.  (Optional) Examine the schema conversion result stored in `ora2pg/data/output.sql`:

        less ora2pg/data/output.sql

1.  Upload the script to Cloud Storage:

        gsutil cp ora2pg/data/output.sql "gs://${GCS_BUCKET}/resources/ora2pg/output.sql"

1.  From Cloud Shell, import the conversion result into the target Cloud SQL for PostgreSQL instance to create the destination schema:

        gcloud sql import sql \
            ${CLOUD_SQL} \
            "gs://${GCS_BUCKET}/resources/ora2pg/output.sql" \
            --user=postgres \
            --project=${PROJECT_ID} \
            --database=postgres \
            --quiet

## Set up Datastream to capture data from the source Oracle database

[Datastream](https://cloud.google.com/datastream) is a serverless change data capture (CDC) and replication service that handles the ingestion and replication of
Oracle data into a Cloud Storage bucket. An initial snapshot of the tables is taken (backfilled) and saved in Cloud Storage as Avro-formatted files, time-stamped
with the time the table query began. Continuous CDC changes are streamed to Cloud Storage in a similar format. Datastream setup begins with creating connection 
profiles for the source and destination that specify how to connect.

In this tutorial, a connection profile for the source Oracle database and a connection profile for the destination Cloud Storage bucket are created. A stream is 
then configured based on the source and destination connection profiles.

### Create a connection profile for the source Oracle database

1.  Go to the [Datastream connection profiles page](https://console.cloud.google.com/datastream/connection-profiles).
1.  Click **Create profile** and select **Oracle**.
1.  Set the connection details as follows:
    1.  **Connection profile name**: `orclsrc`
    1.  **Connection profile ID**: `orclsrc`
    1.  **Hostname or IP**: Hostname or IP address of the source Oracle database
    1.  **Port**: Local listener port address for the source Oracle database
    1.  **System identifier (SID)**: SID of the source Oracle database
    1.  **Username**: Username to log in to the source Oracle database
    1.  **Password**: Password to log in to the source Oracle database
1.  Click **Show more settings**.
1.  For **Connection profile region**, select a Google Cloud region that is close to the source Oracle database. You use the same region for your stream and 
    destination connection profile.
1.  Click **Continue**.
1.  For **Connectivity method**, select the
    [option that corresponds to your network setup](https://cloud.google.com/datastream/docs/source-network-connectivity-options).
1.  Click **Continue**.
1.  Verify that the connection profile is set up correctly by clicking **Run test**.
1.  Click **Create**.

### Create a connection profile for the Cloud Storage bucket

1.  Go to the [Datastream connection profiles page](https://console.cloud.google.com/datastream/connection-profiles).
1.  Click **Create profile** and select **Cloud Storage**.
1.  Set the connection details as follows:
    1.  **Connection profile name**: `ora2pggcs`
    1.  **Connection profile ID**: `ora2pggcs`
    1.  **Bucket name**: `[GCS_BUCKET]`
    1.  **Connection profile path prefix**: `/ora2pg`
1.  Click **Show more settings**.
1.  For **Connection profile region**, select the same Google Cloud region that you chose for your source connection profile. 
1.  Click **Create**.

### Create a stream to capture data from the source database for the data migration

A stream in Datastream consists of configured source and destination connection profiles, as well as a definition of the scope of source data to be streamed.

Create a new stream to capture data from the source Oracle database:

1.  Go to the [Datastream Streams page](https://console.cloud.google.com/datastream/streams).
1.  Create **Create stream**.
1.  Set the stream details as follows:
    1. **Stream name**: `ora2pgstream`
    1. **Stream ID**: `ora2pgstream`
    1. **Region**: Select the same Google Cloud region that you chose for your source connection profile.
    1. **Source type**: Oracle
    1. **Destination type**: Cloud Storage
1.  Review the prerequisites and apply changes to the source database as needed.
1.  Click **Continue**.
1.  For **Source connection profile**, select `orclsrc`.
1.  Click **Continue**.
1.  Fill out the stream source details as follows:
    1.  **Objects to include**: Custom manual definition
    1.  **Object matching criteria**: Enter the Oracle schema to export followed by `.*`. For this tutorial, enter `DEMOAPP.*`.
    1.  **Objects to exclude**: Leave this field empty.
    1.  **Backfill mode for historical data**: Automatic
1.  Click **Continue**.
1.  For **Destination connection profile**, select `ora2pggcs`.
1.  Click **Continue**.
1.  Keep everything default on the **Configure stream destination** page, and click **Continue**.
1.  Click **Run validation** to ensure that the stream is set up correctly.
1.  Click **Create & start** to complete setup and start the Datastream job.

## Set up a Dataflow job to replicate data from Cloud Storage into the target PostgreSQL database

A [Dataflow Flex Template](https://cloud.google.com/dataflow/docs/guides/templates/provided-streaming#oracle-to-postgres) reads the Avro-formatted files output 
by the Datastream stream as they are written and applies them to the target PostgreSQL database.

Deploy this Dataflow job by running the following commands in Cloud Shell:

    export NEW_UUID=$(cat /proc/sys/kernel/random/uuid)
    export DATAFLOW_JOB_PREFIX=ora2pg
    export DATAFLOW_JOB_NAME="${DATAFLOW_JOB_PREFIX}-${NEW_UUID}"
    export DATABASE_HOST=$(gcloud sql instances list --project=${PROJECT_ID} | grep "${CLOUD_SQL}" | awk '{print $6;}')
    export GCS_STREAM_PATH="gs://${GCS_BUCKET}/ora2pg/"
    export DATABASE_PASSWORD="<TARGET_PG_DATABASE_PASSWORD>"

    gcloud beta dataflow flex-template run "${DATAFLOW_JOB_NAME}" \
        --project="${PROJECT_ID}" --region="${GCP_REGION_ID}" \
        --template-file-gcs-location="gs://dataflow-templates/latest/flex/Cloud_Datastream_to_SQL" \
        --parameters inputFilePattern="${GCS_STREAM_PATH}",\
            gcsPubSubSubscription="projects/${PROJECT_ID}/subscriptions/${PUBSUB_TOPIC}-subscription",\
            databaseHost=${DATABASE_HOST},\
            databasePort="5432",\
            databaseUser="postgres",\
            databasePassword="${DATABASE_PASSWORD}",\
            schemaMap=":",\
            maxNumWorkers=10,\
            autoscalingAlgorithm="THROUGHPUT_BASED"

## Verify that the data replication is working

When the Dataflow job is up and running, verify that data is replicated correctly from the source Oracle database to the target Cloud SQL for PostgreSQL
database:

1.  Connect to the target Cloud SQL for PostgreSQL database:

        gcloud sql connect ${CLOUD_SQL} --user=postgres --quiet

1.  Query the table:

        postgres=> select * from demoapp.demotable;
    
    The output should look like the following, though the values in the `rowid` column may differ:

    ```
           rowid    | id | name 
        ------------+----+------
         1343264979 |  1 | A
         1345112114 |  2 | B
        (2 rows)
    ```

1.  Connect to the source Oracle database and make some changes with the following SQL statements:

        insert into demoapp.demotable values (3, 'C');
        update demoapp.demotable set name = 'Z' where id = 1;
        delete from demoapp.demotable where id = 2;
        commit;

1.  Examine the updated table on the Oracle side:

        select * from demoapp.demotable;
        
    The output should look like the following:
    
                ID NAME
        ---------- ----------
                 1 Z
                 3 C

1.  Force a redo log switch:

        alter system switch logfile;

1.  Go back to the target Cloud SQL for PostgreSQL database and verify that the changes have been replicated:

        postgres=> select * from demoapp.demotable;

    The output should look similar to this:
    
    ```
            rowid    | id | name 
         ------------+----+------
          1345112276 |  3 | C
          1343264979 |  1 | Z
         (2 rows)
    ```

## Data validation before cutover

In this section, you use an open source data validation toolkit to validate row numbers and aggregated column metrics. 

1.  Build the data validation Docker image:

        # Version of Oracle Instant Client Version (e.g., 12.2)
        export ORACLE_ODBC_VERSION="[ORACLE_ODBC_VERSION]"

        cd ~/community/tutorials/migrate-oracle-postgres-using-datastream/ora2pg
        docker build . \
            -f DataValidationDockerfile \
            -t data-validation \
            --build-arg ORACLE_ODBC_VERSION=${ORACLE_ODBC_VERSION}

1.  Set up database connection profiles:

        docker run -v $(pwd)/data_validation:/config data-validation connections add -c oracle Raw --json "{\"host\":\"${ORACLE_HOST}\",\"user\":\"${ORACLE_USER}\",\"password\":\"${ORACLE_PASSWORD}\",\"source_type\":\"Oracle\",\"database\":\"${ORACLE_DATABASE}\"}"

        docker run -v $(pwd)/data_validation:/config data-validation connections add -c postgres Raw --json "{\"host\":\"${DATABASE_HOST}\",\"user\":\"${DATABASE_USER}\",\"password\":\"${DATABASE_PASSWORD}\",\"source_type\":\"Postgres\",\"database\":\"postgres\"}"

1.  Discover the list of tables to compare:

        TABLES_LIST=$(docker run -v $(pwd)/data_validation:/config data-validation find-tables --source-conn oracle --target-conn postgres)
        echo ${TABLE_LIST}

    The output should be a JSON object containing schema and table name tuples. For example:

        [{"schema_name": "demoapp", "table_name": "demotable", "target_schema_name": "demoapp", "target_table_name": "demotable"}]

1.  Perform data validation:

        docker run -v $(pwd)/data_validation:/config data-validation run --source-conn oracle --target-conn postgres --tables-list "${TABLES_LIST}" --type Column

    The data validator counts the number of rows in each table from the source database and the target database and report any changes as a list of tables and 
    their comparison results. For example:
    
        validation_name validation_type aggregation_type source_table_name source_column_name source_agg_value target_table_name target_column_name target_agg_value group_by_columns  difference  pct_difference                               run_id labels                       start_time                         end_time
                  count          Column            count demoapp.demotable               None                5 demoapp.demotable               None                5             None         0.0             0.0 86e35cc7-113f-4559-95c9-683e708b4ab8     [] 2021-04-07 06:55:31.246836+00:00 2021-04-07 06:55:31.246846+00:00

    The data validator also supports other types of validation. For details, see the
    [Data Validation Tool GitHub page](https://github.com/GoogleCloudPlatform/professional-services-data-validator).

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [**Manage resources** page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete and then click **Delete**.
1.  In the dialog, type the project ID and then click **Shut down** to delete the project.

## What's next

Learn about migrating an Oracle database to Cloud SQL PostgreSQL with the following series:

-   [Migrating Oracle users to Cloud SQL for PostgreSQL: Terminology and functionality](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
-   [Migrating Oracle users to Cloud SQL for PostgreSQL: Data types, users, and tables](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-data-types)
-   [Migrating Oracle users to Cloud SQL for PostgreSQL: Queries, stored procedures, functions, and triggers](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-queries)
-   [Migrating Oracle users to Cloud SQL for PostgreSQL: Security, operations, monitoring, and logging](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-security)
-   [Setting up Cloud SQL for PostgreSQL for production use](https://cloud.google.com/solutions/setting-up-cloud-sql-for-postgresql-for-production)
