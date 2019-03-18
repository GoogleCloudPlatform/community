---
title: Setting up LEMP on Compute Engine
description: Learn how to set up a LEMP stack on a virtual machine.
author: steveperry-53
tags: Compute Engine, LEMP
date_published: 2017-02-15
---


This page shows you how to get a LEMP stack running on a virtual machine. Follow
the steps in this tutorial to configure LEMP on a Debian, Ubuntu, or CentOS
instance. Generally, these instructions will be similar
on other operating systems.

Alternatively, you can use the [Google Cloud
Launcher](https://cloud.google.com/launcher) to deploy a LEMP stack
automatically.

For this tutorial, the LEMP stack has the following components:

+ Linux
+ NGINX
+ MySQL
+ PHP

## Objectives

* Create a virtual machine instance.
* Connect to your instance using SSH.
* Deploy the LEMP stack on your instance.
* Transfer files.
* Set up DNS mapping.


## Prerequisites

+ Select or create a Google Cloud Platform project.
+ Enable billing for your project.

## Costs

This tutorial uses billable components of Cloud Platform, including:

+ Google Compute Engine

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage.

## Creating a virtual machine instance

You can use these steps to deploy the LEMP stack using
the Google Cloud Platform Console:

1. In the Cloud Platform Console, go to the [**VM Instances** page](https://console.cloud.google.com/compute/instances).
1. Click the **Create instance** button.
1. Set **Name** to **lemp-tutorial**.
1. Set **Machine type** to **f1-micro**.
1. In the **Boot disk** section, click **Change** to begin configuring your boot disk.
1. In the **OS images** tab, choose a **Debian 7.x**, **Ubuntu 14.04**, or **CentOS 6.x** version.
1. Click **Select**.
1. In the **Firewall** section, select **Allow HTTP traffic** and **Allow HTTPS traffic**.
1. Click the **Create** button to create the instance.

Give the instance a few seconds to start up.


## Deploying the LEMP stack on Compute Engine

Now that your virtual machine instance is running, configure the LEMP stack.

### Connect to your instance

You can connect directly to your instance using SSH from
Cloud Platform Console or using the `gcloud compute ssh` command, which is
part of the [Cloud SDK](https://cloud.google.com/sdk).
This tutorial demonstrates the steps in the Cloud Platform Console.

1. In the [Cloud Platform Console](https://console.cloud.google.com/compute/instances),
go to the **VM Instances** page.
1. In the list of virtual machine instances, click the **SSH** button in the row
   of the instance to which you want to connect.

Make a note of the IP address of your VM instance. You can see this address in
the External IP column.

### Install `nginx` and PHP on your instance

By creating an instance, you already have the "Linux" part of
LEMP. Next, install `nginx` and PHP.

1. Install `nginx` and PHP:

        sudo apt-get update
        sudo apt-get install -y nginx php5-fpm

1. Edit the default `nginx` configuration file:

        sudo nano /etc/nginx/sites-available/default

1. Uncomment selected lines in the PHP section, as shown here:

        # pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000
        #
        location ~ \.php$ {
        #       fastcgi_split_path_info ^(.+\.php)(/.+)$;
        #       # NOTE: You should have "cgi.fix_pathinfo = 0;" in php.ini
        #
        #       # With php5-cgi alone:
        #       fastcgi_pass 127.0.0.1:9000;
        #       # With php5-fpm:
                fastcgi_pass unix:/var/run/php5-fpm.sock;
        #       fastcgi_index index.php;
                include fastcgi_params;
        }

1. Restart the `nginx` service:

        sudo service nginx restart


### Test `nginx` and PHP

1. For this step, you need the external IP address of your instance. You can
look up the address in the
**VM Instances** page in the Cloud Platform Console.


    In a browser, enter your external IP address to verify that `nginx` is running:

        http://[YOUR_EXTERNAL_IP_ADDRESS]

    You should see **Welcome to nginx!**

1. Create a test file in the default web server root:

    * Debian 7

            sudo sh -c 'echo "&lt;?php phpinfo();?&gt;" > /usr/share/nginx/www/phpinfo.php'

    * Ubuntu 14.04 or CentOS 6

            sudo sh -c 'echo "&lt;?php phpinfo();?&gt;" > /usr/share/nginx/html/phpinfo.php'

1. Browse to the test file to verify that `nginx` and PHP are working together:

        http://[YOUR_EXTERNAL_IP_ADDRESS]/phpinfo.php

    You should see the standard PHP info page that provides information about
    your current `nginx` environment.

If the page failed to load (`HTTP 404`), verify:

+ In the Cloud Platform Console, HTTP traffic is allowed for your instance.
+ The URL uses the correct IP address and file name.


### Install MySQL on your instance

Install MySQL and related PHP components:

#### Debian/Ubuntu

    sudo apt-get install mysql-server php5-mysql php-pear

#### CentOS 6

1. Install MySQL and related components:

        sudo yum -y install httpd mysql-server php php-mysql

1. Start the MySQL service

        sudo service mysqld start

1. Optional: Set the MySQL service to start automatically:

        sudo chkconfig mysqld on


### Configure MySQL

Now that you have MySQL installed, you should run the
`mysql_secure_installation` command to improve the security of your
installation. This performs steps such as setting the root user password if
it is not yet set, removing the anonymous user, restricting root user access to
the local machine, and removing the test database.

    sudo mysql_secure_installation

## Transferring files

There are several ways to transfer files to your VM instance that runs your web
server, including FTP and the `gcloud` command. For full details, see
[Transferring files to Linux
Instances](https://cloud.google.com/compute/docs/instances/transfer-files). This
tutorial uses the `gcloud` command, which is part of the Cloud SDK. Copy files
to your instance using the `copy-files` command. The following example copies a
file from your workstation to the home directory on the instance.

    gcloud compute scp [LOCAL_FILE_PATH] lemp-tutorial:/var/www/html

Replace [LOCAL_FILE_PATH] with the path to the file on your workstation.

You can also copy files from an instance to your local workstation by reversing
the source and destination variables. The following example copies a file from
your instance to your workstation.

    gcloud compute scp lemp-tutorial:/var/www/html [LOCAL_FILE_PATH]

Replace [LOCAL_FILE_PATH] with the path where you want to put the file on your
workstation.

## Setting up DNS

After you have set up your software stack and transferred your files, you might
want to map your own domain name to your site. If you want complete control of
your own DNS system, you can use [Google Cloud
DNS](https://cloud.google.com/dns) to serve as your domain name service (DNS)
provider. If you need instructions that are specific to Cloud DNS, [see the
quickstart](https://cloud.google.com/dns/quickstart).

This tutorial walks you through the more-common scenario of setting up DNS
through a third-party provider, such as your domain registrar.

If you have an existing DNS provider that you want to use, you need to create a
couple of records with that provider. This lesson assumes that you are mapping
`example.com` and `www.example.com` to point to your website hosted on Compute
Engine.

For the `example.com` domain name, create an `A` record with your DNS provider.
For the `www.example.com` sub-domain, create a `CNAME` record for `www` to point
it to the `example.com` domain. The `A` record maps a host name to an IP
address. The `CNAME` record creates an alias for the `A` record. This lesson
assumes you want `example.com` and `www.example.com` to map to the same IP
address.

1. Get your external IP address for your instance. You can look up the IP
   address from the [*VM instances* page in the Cloud Platform
   Console](https://console.cloud.google.com/compute/instances).
1. Sign in to your provider's DNS management interface and find the domain that
   you want to manage. Refer to your DNS provider's documentation for specific
   steps.
1. Create an `A` record and set the value to your external IP address. The name
   or host field can be set to `@`, which represents the naked domain. For more
   information, the [Google Apps support
   page](https://support.google.com/a/answer/2579934) provides help for
   completing various DNS tasks.
1. Create a `CNAME` record, set the name to `www`, and set the value to `@` or
   to your hostname followed by a period: `example.com.`. Read the [Google Apps
   support](https://support.google.com/a/answer/112037) for help creating the
   `A` record with various providers.
1. If appropriate for your provider, increment the serial number in your `SOA`
   record to reflect that changes have been made so that your records will
   propagate.

### Verify your DNS changes

If your domain name registrar, such as [Google
Domains](https://domains.google/), is also your DNS provider, you're probably
all set. If you use separate providers for registration and DNS, make sure that
your domain name registrar, has the correct name servers associated with your
domain.

After making your DNS changes, the record updates will take some time to
propagate depending on your time-to-live (TTL) values in your zone. If this is a
new hostname, the changes should go into effect quickly because the DNS
resolvers will not have cached previous values and will contact the DNS provider
to get the necessary information to route requests.

## Cleaning up

After you've finished the LEMP tutorial, you can clean up the resources you
created on Google Cloud Platform so you won't be billed for them in the future.
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

1. In the Cloud Platform Console, go to the [Projects
   page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete
   project**. After selecting the checkbox next to the project name, click
   the trash can icon.
1. In the dialog, type the project ID, and then click **Shut down** to delete
   the project.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Platform Console, go to the [**VM Instances**
   page](https://console.cloud.google.com/compute/instances).
1. Click the checkbox next to your `lemp-tutorial` instance.
1. Click the **Delete** button at the top of the page to delete the instance.

## Next steps

+ By default, the web server document root is owned by the `root` user. You
  might want to configure your document root for another user or want to change
  the directory location in the NGINIX configuration file. The web server
  document root is at `/usr/share/nginx/www`, and the `nginx` configuration file
  is at `/etc/nginx/sites-available`.

+ [Learn more about serving websites on Cloud
  Platform.](https://cloud.google.com/solutions/web-serving-overview)
