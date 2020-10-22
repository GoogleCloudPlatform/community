---
title: How to set up MySQL on Compute Engine
description: This document provides guidance on MySQL options on Google Cloud and walks through the manual installation of a MySQL database on Compute Engine.
author: jimtravis
tags: Compute Engine, MySQL
date_published: 2015-08-25
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This page shows you several options for deploying MySQL as part of your Google Cloud project.
You can use Cloud SQL, use Cloud Launcher, or manually install MySQL on Compute Engine.

[Cloud SQL](https://cloud.google.com/sql/docs/introduction)
offers MySQL as a web service. You can use Cloud SQL to host
your MySQL database and let Google Cloud handle
administrative duties like replication, patch management, and database
management.

[Cloud Launcher](https://console.cloud.google.com/launcher/search?q=mysql)
provides a simple, click-to-deploy interface that makes it easy to install
MySQL onto a Compute Engine instance. Cloud Launcher includes not only a standalone MySQL
installation, but also several web development stacks that use
MySQL, including LAMP stacks, LEMP stacks, and Percona MySQL clusters.

If you prefer to manually install and customize MySQL, you can use Compute
Engine to create a MySQL database in a matter of minutes. This document
provides guidance on which option to choose and walks through the manual
installation of a MySQL database on Compute Engine.

## How to choose the right MySQL deployment option

Cloud SQL is a great option if you want the convenience of having
Cloud Platform take care of the backend database and server administration
chores. For example, Cloud SQL provides automated backups and point-in-time
recovery. Moreover, your data is replicated across multiple zones for greater
availability and resiliency.

You might prefer to install MySQL on Compute Engine if you require a
MySQL feature that is not supported by Cloud SQL. For example, Cloud SQL
does not support user defined functions or the SUPER privilege. For more
information, see
[the Cloud SQL FAQ](https://cloud.google.com/sql/faq#supportmysqlfeatures).

If you decide to install MySQL on Compute Engine, you can either use
Cloud Launcher to deploy a MySQL installation, or you can manually install
MySQL on a Compute Engine instance. Cloud Launcher provides a convenient way to
deploy MySQL as part of larger development stacks. Cloud Launcher offers several
[options for MySQL installations](https://cloud.google.com/launcher/?q=mysql),
including a stand alone MySQL installation, LAMP stacks, LEMP stacks, Nginx
Stacks, a Percona MySQL Cluster installation, and several other options.

If the Cloud Launcher offerings don't meet your needs, you can manually install
MySQL on a Compute Engine instance. You might, for example, want to deploy
MySQL on a custom image that you have created, or you might want to have
complete control of the installation process.

To manually install MySQL on a Compute Engine instance, you need only create
a Compute Engine instance and install MySQL directly onto the instance.
The remainder of this document describes the manual installation of MySQL on a
Compute Engine instance.

## Objectives

* Create a Compute Engine instance
* Install MySQL
* Connect to MySQL

## Costs

This tutorial uses Compute Engine, which is a billable component of Google Cloud.
Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost
estimate based on your projected usage. New Google Cloud users may be eligible
for a [free trial](https://cloud.google.com/free-trial).


## Before you begin

1. Create a new project in the [Cloud Console](https://console.cloud.google.com/project).
   You can use an existing project, but creating a new project makes cleanup easier.

    You can complete all of the steps in this document using the Cloud
    Console, but if you prefer to use the
    [`gcloud` command-line tool](https://cloud.google.com/sdk/gcloud/), follow the
    rest of these steps to enable the Compute Engine API and install the
    Cloud SDK.

1. Use the Cloud Console to
   [enable the Compute Engine API](https://console.cloud.google.com/flows/enableapi?apiid=compute_component).

1. Install the [Cloud SDK](https://cloud.google.com/sdk/docs/).

1. Configure your workspace to make commands less verbose.
   Substitute your project's values for `[PROJECT_ID]` and `[MY_ZONE]` in
   the following commands. For the full list of zones, see
   [Available regions and zones](https://cloud.google.com/compute/docs/regions-zones/regions-zones#available).

        me@local:~$ gcloud config set project [PROJECT_ID]
        me@local:~$ gcloud config set compute/zone [MY_ZONE]

## Create a Compute Engine instance

The following steps describe how to create a Compute Engine instance for MySQL
and establish an SSH connection to the newly created instance. The default
operating system is Debian version 7. If you prefer to use a different operating
system for this tutorial, you can choose from the options described on the
[Images](https://cloud.google.com/compute/docs/images/) page in the Compute
Engine documentation.

### Using the Cloud Console

To create a Compute Engine instance in the Cloud Console:

1. Open the [Cloud Console](https://console.cloud.google.com/compute/instances).

1. Select your newly created project and click **Continue**.

1. Click **Create instance** (**New instance** if you have existing
   instances). Name the instance **mysql-test**.

1. To specify an operating system other than the default value,
   in the **Boot disk** section, click **Change**, select the operating
   system, and then click **Select**.

1. Click **Create**.

To establish an SSH connection:

1. On the **VM instances** page, find your new VM instance in the list.

1. In the **Connect** column, click **SSH**. The SSH terminal opens in a
   browser window.

### Using the `gcloud` tool

1. To create a Compute Engine instance, use the `gcloud compute instances
create` command. To use a different operating system, add the `--image`
parameter followed by the image name. For example, to use Debian 8, add
`--image debian-8`.

        me@local:~$ gcloud compute instances create mysql-test

1. Connect to the instance using `ssh`.

        me@local:~$ gcloud compute ssh mysql-test

## Install MySQL

The following steps describe how to install MySQL on a Compute Engine instance.

### Using Debian or Ubuntu

1. Update the `apt-get` package manager.

        $ sudo apt-get update

1. Install MySQL. The installation process starts the MySQL service for you.

        $ sudo apt-get -y install mysql-server

### Using CentOS 6 and RHEL 6

1. Install MySQL.

        $ sudo yum -y install mysql-server

1. Start MySQL server.

        sudo service mysqld start

### Using CentOS 7 and RHEL 7

Version 7 of CentOS and RHEL contain MariaDB instead of MySQL as part of its
package management system. To install MySQL on CentOS 7, you must first update
the package manager.

1. Update the package manager to include MySQL.

        $ sudo rpm -Uvh http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm

1. Install MySQL.

        $ sudo yum -y install mysql-community-server

1. Start MySQL server.

        $ sudo /usr/bin/systemctl start mysqld


## Improve MySQL installation security

To improve the security of your MySQL installation, run the
`mysql_secure_installation` command. If you didn't set a password during
the installation process, create a password in this step. For more information
about this command, see the MySQL documentation for
[mysql_secure_installation](https://dev.mysql.com/doc/refman/5.0/en/mysql-secure-installation.html).

        $ sudo mysql_secure_installation

## Connect to MySQL

The following steps describe how to connect to MySQL from your `mysql-test`
instance.

1. Connect to MySQL using the MySQL client.

        $ mysql --user=root --password

1. When you connect to MySQL, the prompt changes to:

        mysql>

   You can then run MySQL commands. For example, the following command shows
   the threads running, including the current connection.

        mysql> show processlist;

        +----+------+-----------+------+---------+------+-------+------------------+
        | Id | User | Host      | db   | Command | Time | State | Info             |
        +----+------+-----------+------+---------+------+-------+------------------+
        | 51 | root | localhost | NULL | Query   |    0 | NULL  | show processlist |
        +----+------+-----------+------+---------+------+-------+------------------+
        1 row in set (0.00 sec)

   You can use the following command to generate a list of users.

        mysql> SELECT User, Host, Password FROM mysql.user;

        +------------------+------------+-------------------------------------------+
        | User             | Host       | Password                                  |
        +------------------+------------+-------------------------------------------+
        | root             | localhost  | *992C4DB09F487A275976576CCFA554F7D20A4207 |
        | root             | mysql-test | *992C4DB09F487A275976576CCFA554F7D20A4207 |
        | root             | 127.0.0.1  | *992C4DB09F487A275976576CCFA554F7D20A4207 |
        | root             | ::1        | *992C4DB09F487A275976576CCFA554F7D20A4207 |
        | debian-sys-maint | localhost  | *AD7B08AF7691A552A57900F1A9D8AE26ED499117 |
        +------------------+------------+-------------------------------------------+
        5 rows in set (0.00 sec)

1. When you are done running commands, use the `exit` command to quit out of the
   MySQL client, and then use `exit` again to sign out of the Compute Engine
   instance.

        mysql> exit
        mysql-test:~$ exit

## Cleaning up

After you've finished the PostgreSQL tutorial, you can clean up the resources you created on Google Cloud so you won't be billed for them in the future. The following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

To delete the project:

1. In the Cloud Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Console, go to the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the checkbox next to your postgres-tutorial instance.
1. Click the Delete button at the top of the page to delete the instance.


## Next steps

You've now seen how to install MySQL server on Compute Engine. To see more
complex applications that use MySQL, browse the
[wide variety of development stacks](https://console.cloud.google.com/launcher/search?q=mysql)
on Cloud Launcher that use MySQL.

If your requirements include high availability and scalability, consider
installing [MySQL Cluster](https://www.mysql.com/products/cluster/)
on Compute Engine. MySQL Cluster provides high availability and scalability
through shared-nothing clustering and auto-sharding. Cloud Launcher
provides a click-to-deploy option for [Percona](https://console.cloud.google.com/launcher/search?q=percona),
an open source solution for MySQL clustering.

Another open source solution for MySQL scalability is [Vitess](http://vitess.io/),
which has served all YouTube database traffic since 2011. Vitess is
well-suited for applications that run in containers. For more information on
using Vitess in a containerized environment, see
[Running Vitess on Kubernetes](http://vitess.io/getting-started/).

For more information about MySQL, see the
[official MySQL documentation](https://dev.mysql.com/doc).
