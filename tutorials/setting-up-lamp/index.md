---
title: Setting Up LAMP on Compute Engine
description: Learn how to set up a LAMP stack on a virtual machine.
author: jimtravis
tags: Compute Engine, LAMP
date_published: 2017-02-15
---

This page shows you how to get a LAMP stack running on a Google Compute Engine
virtual machine instance. Follow the steps in this tutorial to configure LAMP
on a Debian, Ubuntu, or CentOS instance.

Alternatively, you can use the
[Google Cloud Launcher](https://cloud.google.com/launcher) to deploy a LAMP stack automatically.

## Objectives

+ Create a virtual machine instance.
+ Connect to your instance using SSH.
+ Deploy the LAMP stack on your instance.
+ Transfer files.
+ Set up DNS mapping.

## Prerequisites

+ Select or create a Google Cloud Platform project.
+ Enable billing for your project.

## Costs

This tutorial uses billable components of Cloud Platform,
including:

+ Google Compute Engine

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage.

## Creating a virtual machine instance

You can use these steps to deploy the LAMP stack using
the Google Cloud Platform Console:

1. In the Cloud Platform Console, go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances).
1. Click the Create instance button.
1. Set **Name** to **lamp-tutorial**.
1. Set **Machine type** to **f1-micro**.
1. In the **Boot disk** section, click **Change** to begin configuring your boot disk.
1. In the **OS images** tab, choose a **Debian 7.x**, **Ubuntu 14.04**, **CentOS 6.x**, or **CentOS 7.x** version.
1. Click **Select**.
1. In the **Firewall** section, select **Allow HTTP traffic** and **Allow HTTPS traffic**.
1. Click the **Create** button to create the instance.

Give the instance a few seconds to start up.

## Deploying the LAMP stack on Compute Engine

Now that your virtual machine instance is running, configure the LAMP stack.

### Connect to your instance

You can connect directly to your instance using SSH from
Cloud Platform Console or using the `gcloud compute ssh` command, which is
part of the [Cloud SDK](https://cloud.google.com/sdk).
This tutorial demonstrates the steps in the Cloud Platform Console.

1. In the [Cloud Platform Console](https://console.cloud.google.com/compute/instances),
go to the **VM Instances** page.
1. In the list of virtual machine instances, click the *SSH* button in the row of the instance
to which you want to connect.

Make a note of the IP address of your VM instance. You can see this address in the External IP column.

### Install Apache and PHP on your instance

By creating an instance, you already have the "Linux" part of
LAMP. Next, install Apache and PHP.

#### Debian 8 and Ubuntu 14

    sudo apt-get update
    sudo apt-get install apache2 php5 libapache2-mod-php5

#### Debian 9 and Ubuntu 16/17

    sudo apt-get update
    sudo apt-get install apache2 php libapache2-mod-php

#### CentOS 6 and 7

1. Install Apache and PHP:

        sudo yum check-update
        sudo yum -y install httpd php

1. Start the Apache service:

        sudo service httpd start

1. Optional: Set the Apache service to start automatically:

        sudo chkconfig httpd on


### Test Apache and PHP

1. For this step, you need the external IP address of your instance. You can
look up the address in the
**VM Instances** page in the Cloud Platform Console.

    In a browser, enter your external IP address to verify that Apache is running:

        http://[YOUR_EXTERNAL_IP_ADDRESS]

    You should see the Apache test page.

1. Create a test file in the default web server root at `/var/www/html/`. You can follow the instructions in the [php documentation](http://php.net/manual/en/tutorial.firstpage.php). Example number 2 is the simplest example.

    You can write the code to the file from the command line by using a statement like the following. Replace `[YOUR_PHP_CODE]` with the code you want to write out:

        sudo sh -c 'echo "[YOUR_PHP_CODE]" > /var/www/html/phpinfo.php'

1. Browse to the test file to verify that Apache and PHP are working together:

        http://[YOUR_EXTERNAL_IP_ADDRESS]/phpinfo.php

    You should see the standard PHP info page that provides information about
    your current Apache environment.

If the page failed to load (`HTTP 404`), verify:

+ In the Cloud Platform Console, HTTP traffic is allowed for your instance.
+ The URL uses the correct IP address and file name.


### Install MySQL on your instance

Install MySQL and related PHP components:

#### Debian/Ubuntu

    sudo apt-get install mysql-server php-mysql php-pear

#### Ubuntu 16

    sudo apt-get install mysql-server php7.0-mysql php-pear

#### CentOS 6

1. Install MySQL and related components:

        sudo yum -y install httpd mysql-server php php-mysql

1. Start the MySQL service:

        sudo service mysqld start

1. Optional: Set the MySQL service to start automatically:

        sudo chkconfig mysqld on

#### CentOS 7

1. Install MariaDB and related components:

        sudo yum -y install httpd mariadb-server php php-mysql

1. Start the MariaDB service:

        sudo systemctl start mariadb

1. Optional: Set the MariaDB service to start automatically:

        sudo systemctl enable mariadb


### Configure MySQL

Now that you have MySQL installed, you should run the
`mysql_secure_installation` command to improve the security of your
installation. This performs steps such as setting the root user password if
it is not yet set, removing the anonymous user, restricting root user access to
the local machine, and removing the test database.

    sudo mysql_secure_installation

### Optional: Use phpMyAdmin for database administration

You can use phpMyAdmin to administer your database through a UI.

#### Install phpMyAdmin

##### Debian/Ubuntu

    sudo apt-get install phpmyadmin

##### CentOS 6 and 7

    sudo yum install phpMyAdmin

#### Configure phpMyAdmin

##### Debian/Ubuntu
  + Select **apache2**.
  + Select **yes** to use `dbconfig-common` for database setup.
  + Enter the database administrator's password that you chose during MySQL configuration.
  + Enter a password for the phpMyAdmin application.

##### CentOS 6 and 7
By default, phpMyAdmin allows connections from only localhost. To access the
database from a workstation, modify the Allow directive in the Apache
configuration file for phpMyAdmin.

1. In your text editor, open `phpMyAdmin.conf`.

       sudo nano /etc/httpd/conf.d/phpMyAdmin.conf

1.  To allow hosts on your network to access phpMyAdmin,
    [modify the Allow directive](https://httpd.apache.org/docs/current/mod/mod_access_compat.html#allow)
    for Apache 2.2, adding your workstation's IP address. [See an example](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/setting-up-lamp/code-phpmyadmin.txt).

1. Restart the Apache service:

##### CentOS 6

     sudo service httpd restart

##### CentOS 7

     sudo systemctl restart httpd

#### Test phpMyAdmin

1. Browse to phpMyAdmin.

       http://[YOUR_EXTERNAL_IP_ADDRESS]/phpmyadmin

      You should see the phpMyAdmin login page.

1. Log in by using the `root` username and the administrative password
that you chose during MySQL configuration.

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

    gcloud compute scp [LOCAL_FILE_PATH] lamp-tutorial:/var/www/html

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
create a `CNAME` record for `www` to point it to the `example.com` domain. The `A` record maps a host name
to an IP address. The `CNAME` record creates an alias for the `A` record. This lesson assumes you want
`example.com` and `www.example.com` to map to the same IP address.

1. Get your external IP address for your instance. You can look up the IP address from the [*VM instances* page
in the Cloud Platform Console](https://console.cloud.google.com/compute/instances).
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
Google Cloud Platform so you won't be billed for them in the future. The following sections
describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial. If you don't want
to delete the project, delete the individual instances, as described in the next section.

**Warning**: Deleting a project has the following consequences:

+ If you used an existing project, you'll also delete any other work you've done in the project.
+ You can't reuse the project ID of a deleted project. If you created a custom project ID that you
plan to use in the future, you should delete the resources inside the project instead. This ensures
that URLs that use the project ID, such as an appspot.com URL, remain available.

If you are exploring multiple tutorials and quickstarts, reusing projects instead of deleting
them prevents you from exceeding project quota limits.

To delete the project:

1. In the Cloud Platform Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
After selecting the checkbox next to the project name, click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Platform Console, go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances).
1. Click the checkbox next to your `lamp-tutorial` instance.
1. Click the **Delete** button at the top of the page to delete the instance.

## Next steps

+ By default, the web server document root is owned by the `root` user. You might
want to configure your document root for another user or want to change
the directory location in the Apache configuration file.

  * **Debian/Ubuntu**: The web server document root is at `/var/www/html` and the Apache configuration
  file is at `/etc/apache2/sites-available/default`.

  * **CentOS**: The web server document root is at `/var/www/html` and the Apache
  configuration file is at `/etc/httpd/conf/httpd.conf`.

+ [Learn more about serving websites on Cloud Platform.](https://cloud.google.com/solutions/web-serving-overview)
