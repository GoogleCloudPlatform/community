---
title: Migrating from Oracle to Cloud SQL for PostgreSQL using Ora2pg
description: Learn how to use Ora2PG to perform schema conversion and data migration from Oracle to Cloud SQL for PostgreSQL migration.
author: ktchana
tags: cloud sql, database migration, postgresql, ora2pg, oracle
date_published: 2021-04-23
---

Thomas Chan | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial focuses on the schema migration aspects of an offline migration from Oracle to Cloud SQL for PostgreSQL using Ora2pg. 

[Ora2pg](http://ora2pg.darold.net/) is an open source tool used to migrate an Oracle database to a PostgreSQL database. The tool scans and extracts the database 
schema and data and then generates PostgreSQL-compatible SQL scripts that you can use to populate the database.

Though Ora2pg supports exporting data from Oracle database and importing them into Cloud SQL for PostgreSQL, it is an offline migration in which the database has
to be taken out of service during the whole data migration process. It is common to use data migration tools that support real-time replication, such as Striim
or Oracle GoldenGate for migrations that require minimal downtime.

This document is intended for a technical audience who is responsible for database management and migration. This document assumes that you're familiar with 
database administration and schema conversions, and that you have basic knowledge of using shell scripts and Google Cloud.

High-level overview of the migration procedure using Ora2pg:

1. Install Ora2pg and initialize the migration project.
2. Set up source and target database connectivity.
3. Configure Ora2pg migration parameters.
4. Generate a database migration report.
5. Export the database schema from Oracle database.
6. Import the database schema into Cloud SQL for PostgreSQL.
7. Perform data migration.
8. Import indexes, constraints, foreign keys, and triggers into Cloud SQL for PostgreSQL.
9. Verify data integrity after the migration.

For more in-depth discussions of other aspects of the migration, see the following document series:

*   [Setting up Cloud SQL for PostgreSQL for production use](https://cloud.google.com/solutions/setting-up-cloud-sql-for-postgresql-for-production)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Terminology and functionality](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Data types, users, and tables](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-data-types)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Queries, stored procedures, functions, and triggers](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-queries)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Security, operations, monitoring, and logging](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-security)

## Objectives

*   Learn how to perform Oracle to PostgreSQL schema conversion using Ora2pg.
*   Perform an offline data migration from Oracle to PostgreSQL using Ora2pg.
*   Understand the downtime requirements and data integrity considerations during data migration.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

* [Compute Engine](https://cloud.google.com/compute/all-pricing)
* [Cloud SQL](https://cloud.google.com/sql/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

For this tutorial, you need a Google Cloud [project](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#projects). To make
cleanup easiest at the end of the tutorial, we recommend that you create a new project for this tutorial.

1.  [Create a Google Cloud project](https://console.cloud.google.com/projectselector2/home/dashboard).
1.  Make sure that [billing is enabled](https://support.google.com/cloud/answer/6293499#enable-billing) for your Google
    Cloud project.

When you finish this tutorial, you can avoid continued billing by deleting the resources that you created, as described in the "Cleaning up" section at the end 
of this document.

## Install Ora2pg and initialize the migration project

Ora2pg uses Oracle client libraries to connect to the source Oracle database to perform scans and exports. Though it is possible to install and use Ora2pg on the
same machine as the source Oracle database, we recommend that you use a dedicated machine for Ora2pg installation and runtime to prevent potential interruptions 
to the source database. 

This section shows an example of creating a [Compute Engine instance](https://cloud.google.com/compute/docs/instances/create-start-instance#publicimage) and
installing Ora2pg on that instance. 

1.  Set a variable for the Google Cloud project ID for VM creation:

        export PROJECT_ID="$(gcloud config get-value project -q)"

1.  Set a variable to specify a Google Cloud zone that is close to your source database for optimal performance:

        export GCP_ZONE=us-central1-a

1.  Set a variable for the disk size that allocates enough disk space for the following:

        export PD_SIZE=40GB

    Allocate enough disk space for the following:

    -   Oracle client library installation
    -   PostgreSQL client library installation
    -   Working directory for Ora2pg (usually less than 1GB, excluding data)
    -   Data export files from source database (optional)

1.  Create the Compute Engine instance:

        gcloud compute instances create ora2pg-vm \
          --project=${PROJECT_ID} \
          --zone=${GCP_ZONE} \
          --machine-type=e2-medium \
          --subnet=default \
          --network-tier=PREMIUM \
          --image-family=rhel-7 \
          --image-project=rhel-cloud \
          --boot-disk-size=${PD_SIZE} \
          --boot-disk-type=pd-balanced \
          --boot-disk-device-name=ora2pg-pd

1.  [Connect to the Compute Engine instance](https://cloud.google.com/compute/docs/instances/connecting-to-instance):

        gcloud compute ssh --zone ${GCP_ZONE} ora2pg-vm --project ${PROJECT_ID}

1.  Install an [Oracle instant client](https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html) version that supports your source
    Oracle database version.
    
    1.  To query the Oracle database version, connect to the source database and issue the following SQL statement:

            select banner from v$version;

    1.  For Oracle database version 19c, download the following files. The version number (e.g., 19.9.0.0.0) changes, so always 
        refer to the download page for the most up-to-date filenames.

        * instantclient-basic-linux.x64-19.9.0.0.0dbru.zip
        * instantclient-sdk-linux.x64-19.9.0.0.0dbru.zip
        * instantclient-sqlplus-linux.x64-19.9.0.0.0dbru.zip

    1.  Extract the files to the HOME directory to finish the installation:

            sudo yum install -y unzip
            unzip 'instantclient*'

1.  Install the PostgreSQL client library:

        sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
        sudo yum install -y postgresql12-libs.x86_64 postgresql12.x86_64

1.  Install Ora2pg dependencies:

        sudo yum install -y devtoolset-8 perl-CPAN perl-DBD-Pg libaio perl-Test-Simple perl-Test-NoWarnings

1.  As root, [download Ora2pg](https://github.com/darold/ora2pg/releases). This example uses Ora2pg v21.0. 

        yum install -y wget
        wget https://github.com/darold/ora2pg/archive/v21.0.zip

1.  As root, [install Ora2pg](http://ora2pg.darold.net/documentation.html#Installing-Ora2Pg).

    1.  Make sure that the following environment variables are set before installing. These environment variables are required whenever Ora2pg is used.

            export ORACLE_HOME=[PATH_TO_INSTANT_CLIENT_DIRECTORY]
            export LD_LIBRARY_PATH=$ORACLE_HOME
 
    1.  Verify source database connectivity using the instant client:

            $ORACLE_HOME/sqlplus [ORACLE_USERNAME]@//[ORACLE_IP_ADDRESS]:[LISTENER_PORT]/[DB_SERVICE_NAME]


    1.  Install the `DBD::Oracle` Perl module:

            perl -MCPAN -e 'install DBD::Oracle'

    1.  Extract and build Ora2pg:

            unzip v21.0.zip
            cd ora2pg-21.0
            perl Makefile.PL
            make && make install

        After installation, Ora2pg should be available to all users.
        
1.  Set the `ORACLE_HOME` and `LD_LIBRARY_PATH` environment variables:

            export ORACLE_HOME=[PATH_TO_INSTANT_CLIENT_DIRECTORY]
            export LD_LIBRARY_PATH=$ORACLE_HOME
            
1.  Run Ora2pg:

            ora2pg --help

1.  Initialize an Ora2pg project:

        ora2pg --project_base $HOME --init_project migration_project

    This creates a directory structure, generic configuration file, and migration scripts that are used throughout the migration:

        .
        └── migration_project
            ├── config
            │   └── ora2pg.conf
            ├── data
            ├── export_schema.sh
            ├── import_all.sh
            ├── reports
            ├── schema
            │   ├── dblinks
            │   ├── directories
            │   ├── functions
            │   ├── grants
            │   ├── mviews
            │   ├── packages
            │   ├── partitions
            │   ├── procedures
            │   ├── sequences
            │   ├── synonyms
            │   ├── tables
            │   ├── tablespaces
            │   ├── triggers
            │   ├── types
            │   └── views
            └── sources
                ├── functions
                ├── mviews
                ├── packages
                ├── partitions
                ├── procedures
                ├── triggers
                ├── types
                └── views

## Set up source and target database connectivity

This section focuses on how to configure Ora2pg to connect to the source and target database. This section assumes that the necessary network setup—such as
[VPC](https://cloud.google.com/vpc), [Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview), or
[Cloud Interconnect](https://cloud.google.com/network-connectivity/docs/interconnect/concepts/overview)—is already in place to allow network traffic among 
various components. For details of the connectivity options and detailed setup instructions, see
[Configure connectivity](https://cloud.google.com/database-migration/docs/postgres/configure-connectivity).

### Setup for the source Oracle database

By default, Ora2pg uses a configuration file located at `/etc/ora2pg/ora2pg.conf`. All of the source Oracle database connectivity settings are configured in this
file. You can also specify your own configuration file by using the `-c` flag when running Ora2pg. Throughout this document, the configuration file generated 
during Ora2pg project initialization is used: `$HOME/migration\_project/config/ora2pg.conf`.

To configure and test the connectivity between Ora2pg and the source Oracle database, do the following:

1.  Edit the `$HOME/migration\_project/config/ora2pg.conf` file to set the values of these parameters as shown:

        ORACLE_HOME     [PATH_TO_INSTANT_CLIENT_DIRECTORY]
        ORACLE_DSN      dbi:Oracle:host=[ORACLE_IP_ADDRESS];service_name=[DB_SERVICE_NAME];port=[LISTENER_PORT]
        ORACLE_USER     [ORACLE_USERNAME]
        ORACLE_PWD      [ORACLE_PWD]

        SCHEMA          [SCHEMA_NAME]

    Replace `[ORACLE_IP_ADDRESS]`, `[DB_SERVICE_NAME]`, `[LISTENER_PORT]`, `[ORACLE_USERNAME]` and `[ORACLE_PWD]` with the actual connection details. Replace
    `[SCHEMA_NAME]` with the actual name of the source schema to be migrated.

1.  Verify connectivity:

        ora2pg -t SHOW_VERSION -c $HOME/migration_project/config/ora2pg.conf

    If the connection is successful, the output of the this command is the source Oracle version.


### Setup for THE Target Cloud SQL for PostgreSQL Database

To configure the connectivity between Ora2pg and the target Cloud SQL for PostgreSQL database, do the following:

1.  Configure the [authorized network](https://cloud.google.com/sql/docs/mysql/authorize-networks#console) to allow the Compute Engine instance to connect to 
    your Cloud SQL for PostgreSQL database.

2.  Edit $HOME/migration\_project/config/ora2pg.conf. Locate the following parameters in the file and modify their values:

        PG_DSN          dbi:Pg:dbname=[DB_NAME];host=[PG_IP_ADDRESS];port=5432
        PG_USER         [PG_USERNAME]
        PG_PWD          [PG_PWD]

    Replace `[DB_NAME]`, `[PG_IP_ADDRESS]`, `[PG_USERNAME]` and `[PG_PWD]` with the actual connection details.

1.  Ora2pg uses the [psql client](https://www.postgresql.org/docs/12/app-psql.html) to perform various operations. To prevent psql from repeatedly prompting for
    a password during import operations, create a [password file](https://www.postgresql.org/docs/12/libpq-pgpass.html) `$HOME/.pgpass` with the following 
    content:

        [PG_IP_ADDRESS]:5432:[DB_NAME]:[PG_USERNAME]:[PG_PWD]

1.  Restrict the read and write permissions for the password file:

        chmod 600 $HOME/.pgpass

1.  Set environment variables to facilitate the connection to the target Cloud SQL for PostgreSQL database:

        export PGDATABASE=[DB_NAME]
        export PGUSER=[PG_USERNAME]
        export PGHOST=[PG_IP_ADDRESS]
        export PGPORT=5432

1.  Verify connectivity between the Compute Engine instance and the Cloud SQL for PostgreSQL database:

        psql

    If the password file is set up correctly, no password prompt should appear.

## Configure Ora2pg Migration Parameters

Ora2pg provides many [parameters](http://ora2pg.darold.net/documentation.html#CONFIGURATION) to control various aspects of the migration process. It is important to understand the effect each parameter has and configure them properly for a successful migration. Below are a few common parameters, their meanings and suggested values:


| Ora2pg parameter | Description | Suggested value |
|--- |--- |--- |
|DATA_TYPE|Controls the data type mappings between Oracle and PostgreSQL. Ora2pg comes with a set of data type mappings by default. Change this parameter if you want to custom the mappings.|(Modify only if needed)|
|MODIFY_TYPE|Force Ora2pg to use a data type for a particular table column.|(Modify only if needed)|
|EXPORT_SCHEMA|By default, Ora2pg generates schema creation scripts that will import objects into the public schema of the target PostgreSQL database. Applications that explicitly reference schema name could run into problems when an object does not exist in the target schema. Setting this parameter to 1 instructs Ora2pg to export the schema and create all objects under the correct schema name.|1|
|SCHEMA|Controls the schema(s) exported by Ora2pg. If not specified, Ora2pg exports all objects from all schemas.|(Application schema names)|
|EXCLUDE|Defines a list of objects to be excluded from export. Objects that are flagged as  not supported by Ora2pg in the migration report should be added to this list and manually handled if needed.|(Space or comma-separated list of object name to be excluded)|
|PG_SUPPORTS_PROCEDURE|Procedures are supported since PostgreSQL 11. Setting this parameter to 1 instructs Ora2pg to use PostgreSQL procedures during conversion.|1 (for PostgreSQL 11 or above) 0 (otherwise)|
|EXTERNAL_TO_FDW|By default, external tables in Oracle databases are converted by Ora2pg to foreign tables in PostgreSQL using file_fdw extension. However, file_fdw extension is not supported by Cloud SQL for PostgreSQL and errors will be returned during import. Setting this parameter to 0 instructs Ora2pg to exclude these tables.|0|
|USE_ORAFCE|[orafce](https://github.com/orafce/orafce) is an open-source PostgreSQL extension that provides a subset of functions and packages from Oracle RDBMS. Setting this parameter to 1 instructs Ora2pg to translate Oracle RDBMS function references to reference orafce functions. Cloud SQL for PostgreSQL does not currently support orafce extension.|0|
|STOP_ON_ERROR|By default, `\set ON_ERROR_STOP ON` is included in all SQL scripts generated by Ora2pg. This stops import operations on any errors. Setting it to 0 to disable this behavior and allow import to continue even if error happens.|0|
|NLS_LANG / NLS_NCHAR|Controls the `NLS_LANG` and `NLS_NCHAR` environment variables used by Oracle client library. Set these parameters to match the source database character set settings to avoid potential character conversion issues.|(Use source database NLS settings)|



To configure these parameters, modify $HOME/migration\_project/config/ora2pg.conf. Below is a sample configuration file for migrating the Oracle [HR sample schema](https://docs.oracle.com/en/database/oracle/oracle-database/19/comsc/introduction-to-sample-schemas.html#GUID-4DE9844F-0B28-4713-9AFC-CCD8D6249D76) (follow [these steps](https://docs.oracle.com/en/database/oracle/oracle-database/19/comsc/installing-sample-schemas.html#GUID-4D4984DD-A5F7-4080-A6F8-6306DA88E9FC) to install Oracle HR sample schema):


```
ORACLE_DSN              dbi:Oracle:host=<ORACLE_IP>;service_name=<DB_SERVICE_NAME>;port=<LISTENER_PORT>
ORACLE_USER             <ORACLE_USER>
ORACLE_PWD              <ORACLE_PWD>
PG_DSN                  dbi:Pg:dbname=<DB_NAME>;host=<PG_IP>;port=5432
PG_USER                 <PG_USER>
PG_PWD                  <PG_PWD>
EXPORT_SCHEMA           1
SCHEMA                  HR
STOP_ON_ERROR           0
USE_ORAFCE              0
EXTERNAL_TO_FDW         0
PG_SUPPORTS_PROCEDURE   1
```


## Generate Database Migration Report

Before performing the actual migration, it is a good idea to generate a [database migration report](http://ora2pg.darold.net/documentation.html#Migration-cost-assessment) using Ora2pg. By generating this report, Ora2pg inspect all database objects and codes and report if there are anything that could not be automatically converted.

Use the following command to generate this report:


```
ora2pg -t SHOW_REPORT -c $HOME/migration_project/config/ora2pg.conf --estimate_cost --dump_as_html > $HOME/migration_report.html
```


Review the report and take note of any objects that require manual conversion. Add these objects to the `EXCLUDE` parameter and handle them manually if needed.


## Export database schema from Oracle database

Exporting schema from Oracle database involves running the Ora2pg command, specifying the ora2pg.conf file with the correct settings and supplying various command line arguments specifying the type of objects to be exported. This requires multiple commands and a good knowledge of the tool itself. To ease this process, a shell script called `export_schema.sh` is generated during the project initialization step above. This is a wrapper script that takes the ora2pg.conf as input and then issues the required Ora2pg commands to export the actual schema from the source database. Use the following command to perform schema export from an Oracle database:


```
$HOME/migration_project/export_schema.sh 
```


The exported schema definitions are converted to PostgreSQL syntax and located in the `schema` directory as SQL files. These are the files that are going to be used during import. You can examine and make changes to the files if needed. The `sources` directory contains the schema definitions in source Oracle syntax.


```
.
├── config
│   └── ora2pg.conf
├── data
├── export_schema.sh
├── import_all.sh
├── reports
│   ├── columns.txt
│   ├── report.html
│   └── tables.txt
├── schema
│   ├── dblinks
│   ├── directories
│   ├── functions
│   ├── grants
│   ├── mviews
│   ├── packages
│   ├── partitions
│   ├── procedures
│   │   ├── ADD_JOB_HISTORY_procedure.sql
│   │   ├── procedure.sql
│   │   └── SECURE_DML_procedure.sql
│   ├── sequences
│   │   └── sequence.sql
│   ├── synonyms
│   ├── tables
│   │   ├── CONSTRAINTS_table.sql
│   │   ├── FKEYS_table.sql
│   │   ├── INDEXES_table.sql
│   │   └── table.sql
│   ├── tablespaces
│   ├── triggers
│   │   ├── trigger.sql
│   │   └── UPDATE_JOB_HISTORY_trigger.sql
│   ├── types
│   └── views
│       ├── EMP_DETAILS_VIEW_view.sql
│       └── view.sql
└── sources
    ├── functions
    ├── mviews
    ├── packages
    ├── partitions
    ├── procedures
    │   ├── ADD_JOB_HISTORY_procedure.sql
    │   ├── procedure.sql
    │   └── SECURE_DML_procedure.sql
    ├── triggers
    │   ├── trigger.sql
    │   └── UPDATE_JOB_HISTORY_trigger.sql
    ├── types
    └── views
        ├── EMP_DETAILS_VIEW_view.sql
        └── view.sql
```



## Import database schema into Cloud SQL for PostgreSQL

Ora2pg exports schema definitions as PostgreSQL-compliant SQL files. You can use standard PostgreSQL clients such as psql to execute those SQL files to import the schema into the target Cloud SQL for PostgreSQL database. 

Similar to export, a shell script called `import_all.sh` is generated by Ora2pg during the project initialization step above. This is a wrapper script that takes the ora2pg.conf as input and utilizes psql client commands to perform schema import. 

Depending on the data migration methodologies, it is advisable to first import static schema structures such as tables, partitions, views, functions and procedures into the target database first while leaving indexes, triggers, foreign keys and constraints to be imported after data has been loaded. Doing so has the following advantages:



1. Avoid import errors when data is not loaded in the order that observe constraint policies, such as inserting a record in the child table before the corresponding record in the parent table has been created.
2. Prevent side-effects from being applied more than once in the target database. Examples include triggers that update database tables. If these triggers are enabled during data import, the same change that has been applied in the source database will be applied again in the target database, causing the same update to be done more than once.
3. Improve data insertion performance, since data validation and index maintenance are skipped.

To import static schema structures into the target database using `import_all.sh`: 


```
$HOME/migration_project/import_all.sh -d $PGDATABASE -o $PGUSER -h $PGHOST -U $PGUSER -I -s
```


Optionally, specify `-D` to enable dry-run mode without actually changing the target database and `-y` to reply Yes to all questions for automatic import.


## Perform data migration

Once schema is imported to the target Cloud SQL for PostgreSQL database, you can start the actual data migration. Ora2pg supports exporting data from Oracle database and importing them into Cloud SQL for PostgreSQL. 

To export data from source the Oracle database and import the data directly into the target PostgreSQL database:


```
ora2pg -t COPY -o data.sql -b $HOME/migration_project/data -c $HOME/migration_project/config/ora2pg.conf
```


Optionally, specify `-j <parallelism>` to enable parallelism to fine tune import performance.

Please note that this is an offline data migration. Applications accessing the database have to be taken offline before the data export begins until the database migration is ready. To minimize downtime during migration, leverage data migration tools that support real-time replication, such as Striim or Oracle GoldenGate. 


## Import indexes, constraints, foreign keys and triggers into Cloud SQL for PostgreSQL

After data has been loaded into the target database, the next step is to import the indexes, constraints and foreign keys, make sure that the `PGDATABASE`, `PGUSER`, `PGHOST` and `PGPORT` environment variables are set to correct values:


```
$HOME/migration_project/import_all.sh -d $PGDATABASE -o $PGUSER -h $PGHOST -U $PGUSER -i
```


Optionally, specify `-D` to enable dry-run mode without actually changing the target database, `-j <parallelism>` to enable parallelism to fine tune import performance and `-y` to reply Yes to all questions for automatic import.

Next, import triggers into the target database by the following command.


```
psql -f $HOME/migration_project/schema/triggers/trigger.sql
```



## Verifying data integrity after the migration

In this phase, you want to identify any problems and inconsistencies with the target PostgreSQL environment so that you can rapidly resolve any discrepancies between the data. Follow these steps:



1. Compare the number of rows between the source and target database tables to identify any gaps. In addition to running `count`, also run `sum`, `avg`, `min`, and `max` on the same set of tables. 

    Ora2pg comes with a test mode that compares the source Oracle database and target PostgreSQL database in terms of row counts and object counts:

    ```
    ora2pg -t TEST -c config/ora2pg.conf
    ```

    Here is an excerpt of the command output showing one of the many test results that passed the verification:

    ```
    [TEST TABLE COUNT]
    ORACLEDB:TABLE:7
    POSTGRES:TABLE:7
    [ERRORS TABLE COUNT]
    OK, Oracle and PostgreSQL have the same number of TABLE.
    ```

    In case a discrepancy is found between the source and target database, the result will look similar to the one below:

    ```
    [TEST TRIGGER COUNT]
    ORACLEDB:TRIGGER:1
    POSTGRES:TRIGGER:0
    [ERRORS TRIGGER COUNT]
    TRIGGER does not have the same count in source database (1) and in PostgreSQL (0).
    ```

    In such cases, check if the result is expected and create the missing objects manually in the target Cloud SQL for PostgreSQL database as necessary.

2. Run frequently used SQL statements against the target PostgreSQL environment to ensure that the data matches the source Oracle database.

3. Connect the application to both the source and target databases and verify that the results match. 


## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

-   Learn about migrating an Oracle database to Cloud SQL PostgreSQL with the following series:
    -  [Migrating Oracle users to Cloud SQL for PostgreSQL: Terminology and functionality](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
    -  [Migrating Oracle users to Cloud SQL for PostgreSQL: Data types, users, and tables](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-data-types)
    -  [Migrating Oracle users to Cloud SQL for PostgreSQL: Queries, stored procedures, functions, and triggers](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-queries)
    -  [Migrating Oracle users to Cloud SQL for PostgreSQL: Security, operations, monitoring, and logging](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-security)
 

