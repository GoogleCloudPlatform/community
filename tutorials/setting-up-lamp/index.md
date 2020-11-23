---
title: Setting Up LAMP on Compute Engine
description: Learn how to set up a LAMP stack on a virtual machine.
author: jimtravis
tags: Compute Engine, LAMP
date_published: 2017-02-15
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This page shows you how to get a LAMP stack running on a Compute Engine
virtual machine instance. Follow the steps in this tutorial to configure LAMP
on a Debian, Ubuntu, or CentOS instance.

Alternatively, you can use the
[Cloud Marketplace](https://cloud.google.com/marketplace) to deploy a LAMP stack automatically.

## Objectives

+ Create a virtual machine instance.
+ Connect to your instance using SSH.
+ Deploy the LAMP stack on your instance.
+ Transfer files.
+ Set up DNS mapping.

## Prerequisites

1.  [Select or create a Google Cloud project.](https://cloud.console.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

## Costs

This tutorial uses billable components of Google Cloud,
including [Compute Engine](https://cloud.google.com/compute/all-pricing).

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage.

## Creating a virtual machine instance

You can use these steps to deploy the LAMP stack using
the Cloud Console:

1. In the Cloud Console, go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances).
1. Click the Create instance button.
1. Set **Name** to **lamp-tutorial**.
1. Set **Machine type** to **e2-micro**.
1. We use **Debina GNU/Linux 10(buster)** for **Boot disk**
1. In the **Firewall** section, select **Allow HTTP traffic** and **Allow HTTPS traffic**.
1. Click the **Create** button to create the instance.

__Note:__ If you want to use a different operating system, click the **Change** button for the **Boot disk**,
select the OS and the version you want. For this tutorial, we assume you are using Debian 10
or Ubuntu 20.04 LTS. For other Linux distributions they probably have different steps to install the stack.
You can search on the internet for the latest install procedures.

Give the instance a few seconds to start up.

## Deploying the LAMP stack on Compute Engine

Now that your virtual machine instance is running, configure the LAMP stack.

### Connect to your instance

You can connect directly to your instance using SSH from
Cloud Console or using the `gcloud compute ssh` command, which is
part of the [Cloud SDK](https://cloud.google.com/sdk).
This tutorial demonstrates the steps in the Cloud Console.

1. In the [Cloud Console](https://console.cloud.google.com/compute/instances),
go to the **VM Instances** page.
1. In the list of virtual machine instances, click the *SSH* button in the row of the instance
to which you want to connect.

Make a note of the IP address of your VM instance. You can see this address in the External IP column.

### Install Apache and PHP on your instance

By creating an instance, you already have the "Linux" part of
LAMP. Next, install Apache and PHP.

    sudo apt-get update
    sudo apt-get install apache2 php libapache2-mod-php

### Test Apache and PHP

1. For this step, you need the external IP address of your instance. You can
look up the address in the
**VM Instances** page in the Cloud Console.

    In a browser, enter your external IP address to verify that Apache is running:

        http://[YOUR_EXTERNAL_IP_ADDRESS]

    You should see the Apache test page. Make sure you are not using `https` because it's not configured.

1. Create a test file in the default web server root at `/var/www/html/`. You can follow the instructions in the [php documentation](http://php.net/manual/en/tutorial.firstpage.php). Example number 2 is the simplest example.

    You can write the code to the file from the command line by using a statement like the following. Replace `[YOUR_PHP_CODE]` with the code you want to write out:

        sudo sh -c 'echo "[YOUR_PHP_CODE]" > /var/www/html/phpinfo.php'
    
    For example:

        sudo sh -c 'echo "<?php phpinfo(); ?>" > /var/www/html/phpinfo.php'

1. Browse to the test file to verify that Apache and PHP are working together:

        http://[YOUR_EXTERNAL_IP_ADDRESS]/phpinfo.php

    You should see the standard PHP info page that provides information about
    your current Apache environment.

If the page failed to load (`HTTP 404`), verify:

+ In the Cloud Console, HTTP traffic is allowed for your instance.
+ The URL uses `http` with the correct IP address and file name.


### Install MariaDB on your instance

Install [MariaDB](https://mariadb.org/) and related PHP components:

    sudo apt-get update
    sudo apt-get install mariadb-server php php-mysql

### Check MariaDB server statuses

You can run the following command to check if the MariaDB database server is running:

    sudo systemctl status mariadb

If in any case, `mariadb` service is not running, then start the service with the following command:

    sudo systemctl start mariadb

You can also use the `mysql` client connect to the database server, for example:

    sudo mysql

### Configure MariaDB

Now that you have MariaDB installed, you should run the
[mysql_secure_installation](https://mariadb.com/kb/en/mysql_secure_installation/) command to improve the security of your
installation. This performs steps such as setting the root user password if
it is not yet set, removing the anonymous user, restricting root user access to
the local machine, and removing the test database.

    sudo mysql_secure_installation

### Optional: Use phpMyAdmin for database administration

You can use phpMyAdmin to administer your database through a UI.

    sudo apt-get install php-bz2 php-gd php-curl

    # this command is only needed for Debian 10
    sudo apt-get install -t buster-backports php-twig

    sudo apt-get install phpmyadmin

During the installation, configure phpMyAdmin as following:

  + Use the `SPACE Bar` to select **apache2** and the `TAB` key to move the cursor.
  + Select **Yes** to use `dbconfig-common` for database setup.
  + Enter a password for the phpMyAdmin application and make a note of it.

#### Test phpMyAdmin

1. Browse to phpMyAdmin.

       http://[YOUR_EXTERNAL_IP_ADDRESS]/phpmyadmin

      You should see the phpMyAdmin login page.

1. Log in by using the `phpmyadmin` username and the password you created when you install phpMyAdmin.

#### Secure phpMyAdmin

To prevent unauthorized access to your instance, you should take steps
to [secure your phpMyAdmin installation](https://docs.phpmyadmin.net/en/latest/setup.html#securing-your-phpmyadmin-installation), such as by serving phpMyAdmin only over HTTPS
or using an authentication proxy.

## Transferring files

There are several ways to transfer files to your VM instance that runs your web server,
including FTP and the `gcloud` command. For full details, see
[Transferring files to Linux Instances](https://cloud.google.com/compute/docs/instances/transfer-files).
This tutorial uses the `gcloud` command, which is part of the Cloud SDK.
Copy files to your instance using the `copy-files` command.
The following example copies a file from your workstation to the home directory on the instance.

    gcloud compute scp [LOCAL_FILE_PATH] root@lamp-tutorial:/var/www/html

Replace [LOCAL_FILE_PATH] with the path to the file on your workstation.

You can also copy files from an instance to your local workstation by reversing
the source and destination variables. The following example copies a file from
your instance to your workstation.

    gcloud compute scp lamp-tutorial:/var/www/html [LOCAL_FILE_PATH]

Replace [LOCAL_FILE_PATH] with the path where you want to put the file on your workstation.

## Setting up DNS

After you have set up your software stack and transferred your files, you might want to map your
own domain name to your site. If you want complete control of your own DNS system, you can use
[Google Cloud DNS](https://cloud.google.com/dns) to serve as your domain name service (DNS) provider.
If you need instructions that are specific to Cloud DNS, [see the quickstart](https://cloud.google.com/dns/quickstart).

This tutorial walks you through the more-common scenario of setting up DNS through a third-party provider,
such as your domain registrar.

If you have an existing DNS provider that you want to use, you need to create a couple of records
with that provider. This lesson assumes that you are mapping `example.com` and `www.example.com`
to point to your website hosted on Compute Engine.

For the `example.com` domain name, create an `A` record with your DNS provider. For the `www.example.com` sub-domain,
create a `CNAME` record for `www` to point it to the `example.com` domain. The `A` record maps a hostname
to an IP address. The `CNAME` record creates an alias for the `A` record. This lesson assumes you want
`example.com` and `www.example.com` to map to the same IP address.

1. Get your external IP address for your instance. You can look up the IP address from the [*VM instances* page
in the Cloud Console](https://console.cloud.google.com/compute/instances).
1. Sign in to your provider's DNS management interface and find the domain that you want to manage.
Refer to your DNS provider's documentation for specific steps.
1. Create an `A` record and set the value to your external IP address. The name or host field can be set to `@`,
which represents the naked domain. For more information,
the [Google Apps support page](https://support.google.com/a/answer/2579934) provides help
for completing various DNS tasks.
1. Create a `CNAME` record, set the name to `www`, and set the value to `@` or to your hostname followed by a period:
`example.com.`. Read the [Google Apps support](https://support.google.com/a/answer/112037)
for help creating the `A` record with various providers.
1. If appropriate for your provider, increment the serial number in your `SOA`
record to reflect that changes have been made so that your records will propagate.

### Verify your DNS changes

If your domain name registrar, such as [Google Domains](https://domains.google/),
is also your DNS provider, you're probably all set.
If you use separate providers for registration and DNS, make sure that your domain name registrar, has
the correct name servers associated with your domain.

After making your DNS changes, the record updates will take some time to propagate depending on your
time-to-live (TTL) values in your zone. If this is a new hostname, the changes should go into effect
quickly because the DNS resolvers will not have cached previous values and will contact the DNS provider
to get the necessary information to route requests.

## Cleaning up

After you've finished the LAMP tutorial, you can clean up the resources you created on
Google Cloud so you won't be billed for them in the future. The following sections
describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial. If you don't want
to delete the project, delete the individual instances, as described in the next section.

**Warning**: Deleting a project has the following consequences:

+ If you used an existing project, you'd also delete any other work you've done in the project.
+ You can't reuse the project ID of a deleted project. If you created a custom project ID that you
plan to use in the future, you should delete the resources inside the project instead. This ensures
that URLs that use the project ID, such as an appspot.com URL, remain available.

If you are exploring multiple tutorials and quickstarts, reusing projects instead of deleting
them prevents you from exceeding project quota limits.

To delete the project:

1. In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
After selecting the checkbox next to the project name, click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Console, go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances).
1. Click the checkbox next to your `lamp-tutorial` instance.
1. Click the **Delete** button at the top of the page to delete the instance.

## What's next

- By default, the web server document root is owned by the `root` user. You might
want to configure your document root for another user or want to change
the directory location in the Apache configuration file. **Debian/Ubuntu**: The web server document root is at `/var/www/html` and the Apache configuration file is at `/etc/apache2/sites-available/default`.
- Learn more about [serving websites on Google Cloud](https://cloud.google.com/solutions/web-serving-overview).
- Try out other Google Cloud features for yourself. Have a look at those [tutorials](https://cloud.google.com/docs/tutorials).