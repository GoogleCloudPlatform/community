---
title: Migrating from an Oracle database to Cloud SQL for PostgreSQL using Ora2Pg
description: Learn how to use Ora2Pg to perform schema conversion and data migration from an Oracle database to Cloud SQL for PostgreSQL.
author: ktchana
tags: cloud sql, database migration, postgresql, ora2pg, oracle
date_published: 2021-04-26
---

Thomas Chan | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to perform schema conversion and offline data migration from an Oracle database to a Cloud SQL for PostgreSQL database using Ora2Pg. 

[Ora2Pg](http://ora2pg.darold.net/) is an open source tool used to migrate an Oracle database to a PostgreSQL database. The tool scans and extracts the database 
schema and data and then generates PostgreSQL-compatible SQL scripts that you can use to populate the database.

This document is intended for a technical audience who is responsible for database management and migration. This document assumes that you're familiar with 
database administration and schema conversions, and that you have basic knowledge of using shell scripts and Google Cloud.

High-level overview of the migration procedure using Ora2Pg:

1. Install Ora2Pg and initialize the migration project.
2. Set up source and target database connectivity.
3. Configure Ora2Pg migration parameters.
4. Generate a database migration report.
5. Export the database schema from the Oracle database.
6. Import the database schema into Cloud SQL for PostgreSQL.
7. Perform data migration.
8. Import indexes, constraints, foreign keys, and triggers into Cloud SQL for PostgreSQL.
9. Verify data integrity after the migration.

This document focuses on the schema migration aspects of an offline migration. For more in-depth discussions of other aspects of the migration, see the following
document series:

*   [Setting up Cloud SQL for PostgreSQL for production use](https://cloud.google.com/solutions/setting-up-cloud-sql-for-postgresql-for-production)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Terminology and functionality](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Data types, users, and tables](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-data-types)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Queries, stored procedures, functions, and triggers](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-queries)
*   [Migrating Oracle users to Cloud SQL for PostgreSQL: Security, operations, monitoring, and logging](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-security)

Though Ora2Pg supports exporting data from Oracle database and importing it into Cloud SQL for PostgreSQL, it is an offline migration in which the database must
be taken out of service during the data migration process. It's common to use data migration tools that support real-time replication, such as Striim
or Oracle GoldenGate for migrations that require minimal downtime.

## Objectives

*   Learn how to perform Oracle to PostgreSQL schema conversion using Ora2Pg.
*   Perform an offline data migration from an Oracle database to PostgreSQL using Ora2Pg.
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

## Install Ora2Pg and initialize the migration project

Ora2Pg uses Oracle client libraries to connect to the source Oracle database to perform scans and exports. Though it is possible to install and use Ora2Pg on the
same machine as the source Oracle database, we recommend that you use a dedicated machine for the Ora2Pg installation and runtime to prevent potential 
interruptions to the source database. 

This section shows an example of creating a [Compute Engine instance](https://cloud.google.com/compute/docs/instances/create-start-instance#publicimage) and
installing Ora2Pg on that instance. 

1.  Set a variable for the Google Cloud project ID for VM creation:

        export PROJECT_ID="$(gcloud config get-value project -q)"

1.  Set a variable to specify a Google Cloud zone that is close to your source database for optimal performance:

        export GCP_ZONE=us-central1-a

1.  Set a variable for the disk size:

        export PD_SIZE=40GB

    Allocate enough disk space for the following:

    -   Oracle client library installation
    -   PostgreSQL client library installation
    -   Working directory for Ora2Pg (usually less than 1GB, excluding data)
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

    1.  For Oracle database version 19c, download the following files:

        * instantclient-basic-linux.x64-19.9.0.0.0dbru.zip
        * instantclient-sdk-linux.x64-19.9.0.0.0dbru.zip
        * instantclient-sqlplus-linux.x64-19.9.0.0.0dbru.zip

        The version number (e.g., 19.9.0.0.0) changes, so refer to the download page for the most up-to-date filenames.

    1.  Extract the files to the HOME directory to finish the installation:

            sudo yum install -y unzip
            unzip 'instantclient*'

1.  Install the PostgreSQL client library:

        sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
        sudo yum install -y postgresql12-libs.x86_64 postgresql12.x86_64

1.  Install Ora2Pg dependencies:

        sudo yum install -y devtoolset-8 perl-CPAN perl-DBD-Pg libaio perl-Test-Simple perl-Test-NoWarnings

1.  As root, [download Ora2pg](https://github.com/darold/ora2pg/releases). This example uses Ora2Pg v21.0. 

        yum install -y wget
        wget https://github.com/darold/ora2pg/archive/v21.0.zip

1.  As root, [install Ora2Pg](http://ora2pg.darold.net/documentation.html#Installing-Ora2Pg).

    1.  Make sure that the following environment variables are set before installing. These environment variables are required whenever Ora2Pg is used.

            export ORACLE_HOME=[PATH_TO_INSTANT_CLIENT_DIRECTORY]
            export LD_LIBRARY_PATH=$ORACLE_HOME
 
    1.  Verify source database connectivity using the instant client:

            $ORACLE_HOME/sqlplus [ORACLE_USERNAME]@//[ORACLE_IP_ADDRESS]:[LISTENER_PORT]/[DB_SERVICE_NAME]


    1.  Install the `DBD::Oracle` Perl module:

            perl -MCPAN -e 'install DBD::Oracle'

    1.  Extract and build Ora2Pg:

            unzip v21.0.zip
            cd ora2pg-21.0
            perl Makefile.PL
            make && make install

        After installation, Ora2Pg should be available to all users.
        
1.  Set the `ORACLE_HOME` and `LD_LIBRARY_PATH` environment variables:

        export ORACLE_HOME=[PATH_TO_INSTANT_CLIENT_DIRECTORY]
        export LD_LIBRARY_PATH=$ORACLE_HOME
            
1.  Run Ora2Pg:

        ora2pg --help

1.  Initialize an Ora2Pg project:

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

This section focuses on how to configure Ora2Pg to connect to the source and target database. This section assumes that the necessary network setup—such as
[VPC](https://cloud.google.com/vpc), [Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview), or
[Cloud Interconnect](https://cloud.google.com/network-connectivity/docs/interconnect/concepts/overview)—is already in place to allow network traffic among 
various components. For details of the connectivity options and detailed setup instructions, see
[Configure connectivity](https://cloud.google.com/database-migration/docs/postgres/configure-connectivity).

### Set up connectivity for the source Oracle database

By default, Ora2Pg uses a configuration file located at `/etc/ora2pg/ora2pg.conf`. All of the source Oracle database connectivity settings are configured in this
file. You can also specify your own configuration file by using the `-c` flag when running Ora2Pg. Throughout this document, the configuration file generated 
during Ora2Pg project initialization is used: `$HOME/migration\_project/config/ora2pg.conf`.

To configure and test the connectivity between Ora2Pg and the source Oracle database, do the following:

1.  Edit the `$HOME/migration\_project/config/ora2pg.conf` file to set the values of these parameters as shown:

        ORACLE_HOME     [PATH_TO_INSTANT_CLIENT_DIRECTORY]
        ORACLE_DSN      dbi:Oracle:host=[ORACLE_IP_ADDRESS];service_name=[DB_SERVICE_NAME];port=[LISTENER_PORT]
        ORACLE_USER     [ORACLE_USERNAME]
        ORACLE_PWD      [ORACLE_PWD]

        SCHEMA          [SCHEMA_NAME]

    Replace `[ORACLE_IP_ADDRESS]`, `[DB_SERVICE_NAME]`, `[LISTENER_PORT]`, `[ORACLE_USERNAME]`, and `[ORACLE_PWD]` with the actual connection details. Replace
    `[SCHEMA_NAME]` with the actual name of the source schema to be migrated.

1.  Verify connectivity:

        ora2pg -t SHOW_VERSION -c $HOME/migration_project/config/ora2pg.conf

    If the connection is successful, the output of the this command is the source Oracle database version.

### Set up connectivity for the target Cloud SQL for PostgreSQL database

To configure the connectivity between Ora2Pg and the target Cloud SQL for PostgreSQL database, do the following:

1.  Configure the [authorized network](https://cloud.google.com/sql/docs/mysql/authorize-networks#console) to allow the Compute Engine instance to connect to 
    your Cloud SQL for PostgreSQL database.

1.  Edit the `$HOME/migration\_project/config/ora2pg.conf` file to set the values of these parameters as shown:

        PG_DSN          dbi:Pg:dbname=[DB_NAME];host=[PG_IP_ADDRESS];port=5432
        PG_USER         [PG_USERNAME]
        PG_PWD          [PG_PWD]

    Replace `[DB_NAME]`, `[PG_IP_ADDRESS]`, `[PG_USERNAME]`, and `[PG_PWD]` with the actual connection details.

1.  Ora2Pg uses the [psql client](https://www.postgresql.org/docs/12/app-psql.html) to perform various operations. To prevent psql from repeatedly prompting for
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

## Configure Ora2Pg migration parameters

Ora2Pg provides many [parameters](http://ora2pg.darold.net/documentation.html#CONFIGURATION) to control various aspects of the migration process. It is important 
to understand the effect each parameter has and configure them properly for a successful migration. 

Here are a few common parameters, their meanings, and suggested values:


| Ora2Pg parameter        | Description | Suggested value |
|-------------------------|-------------|-----------------|
| `DATA_TYPE`             | Controls the data type mappings between Oracle and PostgreSQL. Ora2Pg comes with a set of data type mappings by default. Change this parameter if you want to customize the mappings. | Modify only if needed. |
| `MODIFY_TYPE`           | Force Ora2Pg to use a data type for a particular table column. | Modify only if needed. |
| `EXPORT_SCHEMA`         | By default, Ora2Pg generates schema creation scripts that will import objects into the public schema of the target PostgreSQL database. Applications that explicitly reference the schema name could run into problems when an object does not exist in the target schema. Setting this parameter to `1` instructs Ora2Pg to export the schema and create all objects under the correct schema name. | `1` |
| `SCHEMA`                | Specifies which schemas are exported by Ora2Pg. If not specified, Ora2Pg exports all objects from all schemas. | Application schema names |
| `EXCLUDE`               | Objects to be excluded from export. Objects that are flagged as not supported by Ora2Pg in the migration report should be added to this list and manually handled if needed.| Space-separated or comma-separated list of object names to be excluded |
| `PG_SUPPORTS_PROCEDURE` | Procedures are supported since PostgreSQL 11. Setting this parameter to `1` instructs Ora2Pg to use PostgreSQL procedures during conversion.| `1` for PostgreSQL 11 or above; `0` otherwise|
| `EXTERNAL_TO_FDW`       | By default, external tables in Oracle databases are converted by Ora2Pg to foreign tables in PostgreSQL using the `file_fdw` extension. However, the `file_fdw` extension is not supported by Cloud SQL for PostgreSQL, and errors will be returned during import. Setting this parameter to `0` instructs Ora2Pg to exclude these tables. | `0` |
| `USE_ORAFCE`            | [Orafce](https://github.com/orafce/orafce) is an open-source PostgreSQL extension that provides a subset of functions and packages from Oracle RDBMS. Setting this parameter to `1` instructs Ora2Pg to translate Oracle RDBMS function references to reference Orafce functions. Cloud SQL for PostgreSQL does not support the Orafce extension. | `0` |
| `STOP_ON_ERROR`         | By default, `\set ON_ERROR_STOP ON` is included in all SQL scripts generated by Ora2Pg. This stops import operations on any errors. Set it to `0` to disable this behavior and allow import to continue even if errors occur. | `0` |
| `NLS_LANG`, `NLS_NCHAR` | Controls the `NLS_LANG` and `NLS_NCHAR` environment variables used by Oracle client library. Set these parameters to match the source database character set settings to avoid potential character conversion issues. | Use source database NLS settings. |

To configure these parameters, modify the `$HOME/migration\_project/config/ora2pg.conf` file. 

The following is an example configuration file for migrating the Oracle
[HR sample schema](https://docs.oracle.com/en/database/oracle/oracle-database/19/comsc/introduction-to-sample-schemas.html).

    ORACLE_DSN              dbi:Oracle:host=[ORACLE_IP_ADDRESS];service_name=[DB_SERVICE_NAME];port=[LISTENER_PORT]
    ORACLE_USER             [ORACLE_USERNAME]
    ORACLE_PWD              [ORACLE_PWD]
    PG_DSN                  dbi:Pg:dbname=[DB_NAME];host=[PG_IP_ADDRESS];port=5432
    PG_USER                 [PG_USERNAME]
    PG_PWD                  [PG_PWD]
    EXPORT_SCHEMA           1
    SCHEMA                  HR
    STOP_ON_ERROR           0
    USE_ORAFCE              0
    EXTERNAL_TO_FDW         0
    PG_SUPPORTS_PROCEDURE   1

To install the Oracle HR sample schema, follow the instructions in
[Installing Sample Schemas](https://docs.oracle.com/en/database/oracle/oracle-database/19/comsc/installing-sample-schemas.html).

## Generate a database migration report

Before performing the actual migration, it is a good idea to generate a
[database migration report](http://ora2pg.darold.net/documentation.html#Migration-cost-assessment) using Ora2Pg. When you generate this report, 
Ora2Pg inspects all database objects and codes and reports whether there is anything that couldn't be automatically converted.

1.  Generate the report:

        ora2pg -t SHOW_REPORT -c $HOME/migration_project/config/ora2pg.conf --estimate_cost --dump_as_html > $HOME/migration_report.html

1.  Review the report, take note of any objects that require manual conversion, add these objects to the `EXCLUDE` parameter, and handle them manually if 
    needed.

## Export the database schema from the Oracle database

Exporting a schema from an Oracle database involves running the `ora2pg` command, specifying the `ora2pg.conf` file with the correct settings, and supplying 
command-line arguments specifying the type of objects to be exported. This requires multiple commands and a good knowledge of the tool itself. To ease this 
process, a shell script called `export_schema.sh` is generated during the project initialization step. This is a wrapper script that takes the 
`ora2pg.conf` as input and then issues the required Ora2Pg commands to export the actual schema from the source database. Use the following command to perform 
schema export from an Oracle database:


    $HOME/migration_project/export_schema.sh

The exported schema definitions are converted to PostgreSQL syntax and located in the `schema` directory as SQL files. These are the files that are 
used during import. You can examine and make changes to the files if needed. The `sources` directory contains the schema definitions in source Oracle syntax.

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

## Import the database schema into Cloud SQL for PostgreSQL

Ora2Pg exports schema definitions as PostgreSQL-compliant SQL files. You can use standard PostgreSQL clients such as psql to execute those SQL files to import
the schema into the target Cloud SQL for PostgreSQL database. 

A shell script called `import_all.sh` is generated by Ora2Pg during the project initialization step. This is a wrapper script that takes the `ora2pg.conf`
file as input and uses psql client commands to perform the schema import. 

Depending on the data migration methodologies, it is advisable to first import static schema structures such as tables, partitions, views, functions, and 
procedures into the target database first while leaving indexes, triggers, foreign keys, and constraints to be imported after data has been loaded. Doing so has
the following advantages:

- Avoid import errors when data is not loaded in the order that observe constraint policies, such as inserting a record in the child table before the 
  corresponding record in the parent table has been created.
- Prevent side-effects from being applied more than once in the target database. Examples include triggers that update database tables. If these triggers are 
  enabled during data import, the same change that has been applied in the source database will be applied again in the target database, causing the same update
  to be done more than once.
- Improve data insertion performance, since data validation and index maintenance are skipped.

To import static schema structures into the target database using `import_all.sh`, use the following command: 

    $HOME/migration_project/import_all.sh -d $PGDATABASE -o $PGUSER -h $PGHOST -U $PGUSER -I -s

Optionally, use the `-D` flag to enable dry-run mode without actually changing the target database and `-y` to reply yes to all questions for automatic import.

## Perform data migration

After the schema is imported into the target Cloud SQL for PostgreSQL database, you can start the actual data migration. Ora2Pg supports exporting data from 
an Oracle database and importing it into Cloud SQL for PostgreSQL. 

To export data from source the Oracle database and import the data directly into the target PostgreSQL database, use the following command:

    ora2pg -t COPY -o data.sql -b $HOME/migration_project/data -c $HOME/migration_project/config/ora2pg.conf

Optionally, specify `-j <parallelism>` to enable parallelism to fine-tune import performance.

This is an offline data migration. Applications accessing the database must be taken offline before the data export begins and until the database migration is
complete. To minimize downtime during migration, use data migration tools that support real-time replication, such as Striim or Oracle GoldenGate. 

## Import indexes, constraints, foreign keys, and triggers into Cloud SQL for PostgreSQL

After data has been loaded into the target database, the next step is to import the indexes, constraints, and foreign keys.

1.  Make sure that the `PGDATABASE`, `PGUSER`, `PGHOST` and `PGPORT` environment variables are set to correct values:

        $HOME/migration_project/import_all.sh -d $PGDATABASE -o $PGUSER -h $PGHOST -U $PGUSER -i

    Optionally, use the `-D` flag to enable dry-run mode without actually changing the target database, `-j <parallelism>` to enable parallelism to fine-tune
    import performance, and `-y` to reply yes to all questions for automatic import.

1.  Import triggers into the target database:

        psql -f $HOME/migration_project/schema/triggers/trigger.sql

## Verify data integrity after the migration

After the data has been imported, you need to identify any problems and inconsistencies with the target PostgreSQL environment so that you can rapidly resolve 
any discrepancies in the data.

1.  Compare the number of rows between the source and target database tables to identify any gaps. In addition to running `count`, also run `sum`, `avg`, `min`,
    and `max` on the same set of tables.

    Ora2Pg comes with a test mode that compares the source Oracle database and target PostgreSQL database in terms of row counts and object counts:

        ora2pg -t TEST -c config/ora2pg.conf

    Here is an excerpt of the command output showing one of the many test results that passed the verification:

        [TEST TABLE COUNT]
        ORACLEDB:TABLE:7
        POSTGRES:TABLE:7
        [ERRORS TABLE COUNT]
        OK, Oracle and PostgreSQL have the same number of TABLE.

    If a discrepancy is found between the source and target databases, the result looks similar to the following:

        [TEST TRIGGER COUNT]
        ORACLEDB:TRIGGER:1
        POSTGRES:TRIGGER:0
        [ERRORS TRIGGER COUNT]
        TRIGGER does not have the same count in source database (1) and in PostgreSQL (0).

    In such cases, check whether the result is expected, and create the missing objects manually in the target Cloud SQL for PostgreSQL database as necessary.

1.  Run frequently used SQL statements against the target PostgreSQL environment to ensure that the data matches the source Oracle database.

1.  Connect the application to both the source and target databases and verify that the results match. 

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project that you want to delete, and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

Learn about migrating an Oracle database to Cloud SQL PostgreSQL with the following series:

-  [Migrating Oracle users to Cloud SQL for PostgreSQL: Terminology and functionality](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-terminology)
-  [Migrating Oracle users to Cloud SQL for PostgreSQL: Data types, users, and tables](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-data-types)
-  [Migrating Oracle users to Cloud SQL for PostgreSQL: Queries, stored procedures, functions, and triggers](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-queries)
-  [Migrating Oracle users to Cloud SQL for PostgreSQL: Security, operations, monitoring, and logging](https://cloud.google.com/solutions/migrating-oracle-users-to-cloud-sql-for-postgresql-security)
