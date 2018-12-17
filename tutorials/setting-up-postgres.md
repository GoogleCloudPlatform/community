---
title: How to Set Up PostgreSQL on Google Compute Engine
description: Learn how to get PostgreSQL running on Google Compute Engine.
author: jimtravis
tags: Compute Engine, PostgreSQL
date_published: 2016-06-03
---
This tutorial shows how to set up [PostgreSQL](https://www.postgresql.org) on
Google Cloud Platform in just a few minutes. Follow this tutorial to configure
PostgreSQL on an Ubuntu virtual machine instance on Compute Engine.

If you don't want to install and manage your own PostgreSQL database,
[Google Cloud SQL](https://cloud.google.com/sql/docs/postgres/) provides managed PostgreSQL.

You can also use [Cloud Launcher](https://cloud.google.com/launcher/?q=postgres)
to set up PostgreSQL on Compute Engine with just a few clicks.


## Objectives

* Install PostgreSQL on a Compute Engine instance.
* Configure PostgreSQL for remote access.
* Configure a Cloud Platform firewall to open a port.
* Connect to PostgreSQL from a remote computer.

## Before you begin

You'll need a Google Cloud Console project. You can use an existing project or
click the button to create a new project.

**[Create a project](https://console.cloud.google.com/project)**

## Costs

This tutorial uses billable components of Cloud Platform,
including:

+ Google Compute Engine

Use the [pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538)
to generate a cost
estimate based on your projected usage. New Cloud Platform users might be
eligible for a [free trial](https://cloud.google.com/free-trial).


## Creating a Compute Engine instance

For the purposes of this tutorial, the default machine type works fine, so
you don't need to change the default setting.
In production, you need to decide how much computing power is required
for your application. In general, database systems tend to be more
constrained by I/O bottlenecks and hard disk speed than by CPU capabilities.

Most Linux distributions have some version of PostgreSQL integrated with
their package managers. For this tutorial, you use Ubuntu Trusty because
it includes PostgreSQL 9.3, which has some helpful tools that aren't
available in earlier versions.

1. In the Cloud Platform Console, go to the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the **Create instance** button.
1. Set Name to `postgres-tutorial`.
1. In the **Boot disk** section, click **Change** to begin configuring your boot disk.
1. In the **Preconfigured image** tab, choose **Ubuntu 14.04 LTS**.
1. In the **Boot disk type** section, select **Standard persistent disk**.
1. Click **Select**.
1. In the **Firewall** section, select **Allow HTTP traffic** and **Allow HTTPS traffic**.
1. Click the **Create** button to create the instance.

It will take a few moments to create your new instance.

Stay on the **VM instances** page for the next step.


## Setting up PostgreSQL

To set up PostgreSQL, you must install it and set up a user.


### Install PostgreSQL

Follow these steps to install PostgreSQL on your Compute Engine instance.

1. In the list of virtual machine instances, click the **SSH** button in the row of the instance to which you want to connect.
1. Update the packages. In the SSH terminal, enter the following command:

        sudo apt-get update

1. Install PostgreSQL, including the PSQL client and server instrumentation:

        sudo apt-get -y install postgresql postgresql-client postgresql-contrib


### Use PSQL to complete the setup

PostgreSQL created a default user, named "postgres", during installation. This
user doesn't yet have a password, so you'll need to set one.

1. In your SSH terminal, run the root shell:

        sudo -s

1. Run [PSQL](https://www.postgresql.org/docs/9.3/static/app-psql.html)
 as user `postgres`, instead of `root`, accessing the database
 named `postgres`:

        sudo -u postgres psql postgres

    You should see the PSQL command prompt, which looks like this: `postgres=#`

1. Enter the following command to set the password:

        \password postgres


1. When prompted, enter and confirm the password you've chosen.

    **Important**:
     For any system with an Internet connection, use a
     strong password to help keep the system secure.

1. Install the `adminpack` extension to enable the server instrumentation that
you installed earlier. The console prints `CREATE EXTENSION` when successful.

        CREATE EXTENSION adminpack;

1. Enter `\q` to exit PSQL.

1. Enter `exit` to exit the root shell.


## Connecting remotely

To connect to your Postgres database, you'll need to change a configuration
file and open a port in the firewall on Cloud Platform.

### Configure PostgreSQL remote access

By default, Postgres doesn't allow remote connections. To change this setting,
you can change the file named
[`pg_hba.conf`](http://www.postgresql.org/docs/9.3/static/auth-pg-hba-conf.html).
Follow these steps.

Caution: On production systems, or any
system that has an Internet connection, use strong
authentication methods and restrict traffic to only those users and IP addresses
that you want to connect to each database.

#### Edit `pg_hba.conf`

1. In the SSH terminal window, edit `pg_hba.conf`. This tutorial uses the
`nano` editor, but you can substitute your favorite editor. For PostgreSQL
version 9.3, you can enter:

        sudo nano ../../etc/postgresql/9.3/main/pg_hba.conf

1. Navigate to [ip4.me](http://ip4.me) to get the IPv4
address of your local computer.

    You'll need this IP address in an upcoming steps.

1. Scroll down to the bottom of the file and add the following lines:

        # IPv4 remote connections for the tutorial:
        host    all             all           [YOUR_IPV4_ADDRESS]/32         md5


1. Replace `[YOUR_IPV4_ADDRESS]` with the address of your local computer. Note
that the
    [CIDR](https://wikipedia.org/wiki/Classless_Inter-Domain_Routing)
    suffix `/32` is used for a single address,
    which is what you're providing in this tutorial.

1. Save the file and exit the editor. In `nano`, press `Control+x` and then
use the `Return` key to accept the prompts to save the file. Note that `nano`
might not clear the console screen properly, so if you have trouble reading the
text in the console after closing `nano`, enter `clear` to clear the screen.

#### Edit `postgresql.conf`

1. Open [`postgresql.conf`](https://www.postgresql.org/docs/9.3/static/config-setting.html) for editing. For example, enter the following command:

        sudo nano ../../etc/postgresql/9.3/main/postgresql.conf

1. Scroll down to the line that begins with `#listen_addresses = 'localhost'`.

1. Delete the `#` character to uncomment the line.

1. Replace `localhost` with `*`:

        listen_addresses = '*'

    The `'*'` setting enables Postgres to listen on all IP addresses. This is
   a commonly used setting. When you set the IP address in `hba.conf` in the
   previous step, you restricted access to the database to only your computer.

1. Save the file and exit the editor.

1. Restart the database service. In the SSH terminal, enter:

        sudo service postgresql restart

### Open the network port

PostgreSQL accepts remote connections on port 5432. Follow these steps to add
a firewall rule that enables traffic on this port.

1. In the Cloud Console, navigate to the **Create a firewall rule**
page.

    **[Create a firewall rule](https://console.cloud.google.com/networking/firewalls/add)**

1. In the **Network** field, leave the network as **default**.

1. In the **Name** field, enter:

        postgres-tutorial

1. In the **Direction of traffic** field, create a rule as **Ingress** and another rule as **Egress**.

1. In **Source IP Ranges**, enter the same IP address you used in `hba.conf`.
   This is the IP address of your local computer. Remember to include the `/32`
   suffix, for example: `1.2.3.4/32`.

1. In **Allowed protocols and ports**, enter:

        tcp:5432

1. Click **Create**.

Note that firewall rules are a global resource, so you'll only need to
create this rule once for all instances.

### Connect using pgAdmin

Now you can connect to your PostgreSQL database from your computer. This
tutorial uses [pgAdmin](http://www.pgadmin.org/), which is a
popular client application for working
with Postgres databases. Follow these steps.

1. Install [pgAdmin](http://www.pgadmin.org/download/index.php)
on your local computer.

1. Run pgAdmin.

    Note: On Mac OS X, you must open the program
from Finder by choosing **Open** from the context menu. Otherwise, Mac OS X
will display a security warning and fail to run the program.

1. Add the server. In pgAdmin3, you can click the first icon on the left
side of the toolbar. Alternatively, click **File** > **Add server**.

1. In the **New Server Registration** window, in the **Name** field, enter:

        Postgres tutorial

1. Navigate to the **VM instances** page and find the external IP address of
your Compute Engine instance in the **External IP** column.

    **[Open VM instances](https://console.cloud.google.com/compute/instances)**

1. In the **Host** field, enter the external IP address of your Compute Engine
instance.

    Note: Enter only the address as it appears in the Cloud Console;
    don't add any protocol specifiers, such as `http://` or other characters.

1. In the **Port** field, enter:

        5432

1. In the **Password** field, enter the password that you set previously for
the user named `postgres`.

1. Click **OK** to close the window.

You should now be connected to your PostgreSQL database that is hosted on your
Compute Engine instance. You can use pgAdmin to browse and modify the database
and other settings. PgAdmin also includes a PSQL console that you can use to
administer the database remotely.

## Best practices

This tutorial provided you with a basic look at a one-machine, single-disk
installation of PostgreSQL. In a production environment, it's a good idea to
employ strategies for high availability, scalability, archiving, backup, load
balancing, and disaster recovery. For information about disaster recovery
planning, see
[How to Design a Disaster Recovery Plan](https://cloud.google.com/solutions/designing-a-disaster-recovery-plan).

For better performance and data safety, install the database engine on the boot
disk as this tutorial showed, and then set up the  data storage on a separate
persistent disk. To learn how to add a disk for your database, see the follow-up
tutorial
[How to Set Up a New Persistent Disk for PostgreSQL Data](setting-up-postgres-data-disk).

For machines that have an Internet connection, use only strong passwords and
limit access only to trusted IP ranges.


## Cleaning up

After you've finished the PostgreSQL tutorial, you can clean up the resources you created on Google Cloud Platform so you won't be billed for them in the future. The following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Platform Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.


### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Platform Console, go to the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the checkbox next to your postgres-tutorial instance.
1. Click the Delete button at the top of the page to delete the instance.


### Deleting firewall rules for the default network

To delete a firewall rule:

1. In the Cloud Platform Console, go to the **[Firewall Rules](https://console.cloud.google.com/networking/firewalls)** page.
1. Click the checkbox next to the firewall rule you want to delete.
1. Click the Delete button at the top of the page to delete the firewall rule.


## Next steps

* [Set up a new persistent disk for your PostgreSQL Data](setting-up-postgres-data-disk).
* [Set up Postgres for high availability and replication with Hot Standby](setting-up-postgres-hot-standby).
* Explore the [PostgreSQL documentation](https://www.postgresql.org/docs/).
* Learn more about [pgAdmin](http://www.pgadmin.org/docs/).
