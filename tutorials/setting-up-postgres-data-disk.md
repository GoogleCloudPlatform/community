---
title: Setting up a new persistent disk for PostgreSQL data
description: Learn how to add a separate persistent disk for your PostgreSQL database on Google Cloud.
author: jimtravis
tags: Compute Engine, PostgreSQL, persistent disk
date_published: 2017-02-16
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to add a separate persistent disk for your PostgreSQL database on Compute Engine.

The tutorial [How to set up PostgreSQL on Compute Engine](setting-up-postgres)
shows how to set up a basic installation of PostgreSQL, or Postgres, on a
single disk, which is also the boot disk. For better performance and data
safety, you can install the PostgreSQL database engine on the boot disk and then
set up the data storage on a separate persistent disk. This tutorial shows you
how to move your existing database to a new persistent disk on Google
Cloud.

Note that you can also use Postgres as a service through [Cloud SQL](https://cloud.google.com/sql/docs/postgres/).

## Objectives

* Insert test data
* Create and attach a new persistent disk
* Prepare the disk
* Move the data to the new disk
* Test the database

## Prerequisites

A running instance of PostgreSQL on Compute Engine.

This tutorial uses billable components of Google Cloud including:

+ Compute Engine
+ Persistent disk storage

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to
generate a cost estimate based on your projected usage.

## Inserting test data

Start by inserting some simple test data into the database. You'll use this data
to demonstrate that the database works on the persistent disk. Follow these
steps:

1. SSH into the Compute Engine instance that hosts your Postgres database.

1. In the terminal, run the root shell:

        $ sudo -s

1. Start PSQL:

        $ sudo -u postgres psql postgres

1. Create a simple table for testing purposes:

        CREATE TABLE tests(message text, id serial);

1. Add a message to the table:

        INSERT INTO tests (message) VALUES ('This is a test.');

    You should see a confirmation message that says `INSERT 0 1`.

1. Display the contents of the test table:

        SELECT * from tests;

    You should see the row that you inserted with the test message.

1. Exit PSQL:

        \q

1. Exit the root shell:

        $ exit

## Creating and attaching a new persistent disk

To create a new persistent disk for your Postgres database,
follow these steps:

1. Open the [**Disks** page in the
Google Cloud Platform Console](https://console.cloud.google.com/project/_/compute/disks).

1. Click **New disk**.

1. Enter a name, such as `postgres-data`.

1. Make sure the **Zone** is the same as the zone that contains your Postgres
instance.

1. Set the **Disk Type** to `Standard persistent disk`.

1. Set the **Source type** to `None (blank disk)`.

1. For this tutorial, you can leave the **Size** at the default setting.
Otherwise, you can set the size to a value that is sufficient for your project's
requirements.

1. Click **Create**.

Now, attach the disk to the Compute Engine instance that hosts your Postgres
database. Follow these steps:

1. Open the [**VM instances** page in the
Cloud Console](https://console.cloud.google.com/project/_/compute/instances).

1. Click your instance name to open the details page.

1. In the **Additional disks** section, click **Edit** and then click **Add
item**.

1. In the **Name** list, select the new disk you created. Make sure the **Mode**
is set to **Read/write**, which is the default setting.

    By default, the **When deleting instance** setting for the
    attached disk is set to **Keep disk**. This means that your new disk won't
    be deleted even if you  delete your Compute Engine instance that hosts
    Postgres, so your data won't be deleted.

1. For **Encryption**, leave the default setting of **Automatic**.

1. Click **Save**.

## Preparing the disk

To prepare the disk for data, you need to format and mount the disk and then set
permissions for the Postgres user. Follow these steps:

1. Create a directory for the mount point. In the SSH terminal window, enter
the following command:

        $ sudo mkdir ../../media/postgres-data

1. Find the location of your persistent disk:

        $ ls -l /dev/disk/by-id/google-*

1. Format and mount the disk, as described in the [Compute Engine documentation](https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting).

1. Change the owner for the new disk so Postgres can access it:

        sudo chown -R postgres:postgres ../../media/postgres-data

## Moving the data to the new disk

Now you must copy the database files to the new disk and change the Postgres
configuration to point to the new data directory. Follow these steps:

1. Stop the Postgres server:

        sudo service postgresql stop

1. Move the database files to the new data disk:

        sudo mv ~/../../var/lib/postgresql/9.3/main ~/../../media/postgres-data

1. Edit `postgresql.conf`:

        sudo nano ../../etc/postgresql/9.3/main/postgresql.conf

1. Change the location of the data directory:

        data_directory = '/media/postgres-data/main'

1. Save and close the file.

1. Start Postgres:

        sudo service postgresql start

## Testing the database

Your Postgres instance should now use the new persistent disk as the data disk.
Follow these steps to verify that the database works:

1. Run the root shell:

        $ sudo -s

1. Start PSQL:

        $ sudo -u postgres psql postgres

1. Display the contents of the test table:

        SELECT * from tests;

    You should see the row that you inserted with the test message, confirming
    that the database is operating from the new persistent disk.

1. Add a new message to the table:

        INSERT INTO tests (message) VALUES ('This is another test.');

    You should see a confirmation message that says `INSERT 0 1`.

1. Display the contents of the test table:

        SELECT * from tests;

    You should see both rows that you inserted with the test messages. This
    confirms that you can modify the data on the new persistent disk.

1. Exit PSQL:

        \q

1. Exit the root shell:

        $ exit

## Cleaning up

After you've finished the tutorial, you can clean up the resources you
created on Google Cloud so you won't be billed for them in the future.
The following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. If you don't want to delete the project, delete the individual
instances, as described in the next section.

**Warning**: Deleting a project has the following consequences:

+ If you used an existing project, you'll also delete any other work you've done
  in the project.
+ You can't reuse the project ID of a deleted project. If you created a custom
  project ID that you plan to use in the future, you should delete the resources
  inside the project instead. This ensures that URLs that use the project ID,
  such as an appspot.com URL, remain available.

If you are exploring multiple tutorials and quickstarts, reusing projects
instead of deleting them prevents you from exceeding project quota limits.

To delete the project:

1. In the Cloud Console, go to the [Projects
   page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete
   project**. After selecting the checkbox next to the project name, click
   **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete
   the project.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Console, go to the [**VM Instances**
   page](https://console.cloud.google.com/compute/instances).
1. Click the checkbox next to your `lemp-tutorial` instance.
1. Click the **Delete** button at the top of the page to delete the instance.

### Deleting disks

To delete a Compute Engine disk:

1. In the Cloud Console, go to the [**Disks** page](https://console.cloud.google.com/compute/disks).
1. Click the checkbox next to the disk you want to delete.
1. Click the **Delete** button at the top of the page to delete the disk.

## Next steps

* [Set up hot standby mode](setting-up-postgres-hot-standby)
* Explore the [PostgreSQL documentation](https://www.postgresql.org/docs/).
