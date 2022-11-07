---
title: Setting up Drupal on Compute Engine
description: Learn how to get Drupal running on a virtual machine instance on Compute Engine.
author: jimtravis
tags: Compute Engine, SendGrid, Drupal
date_published: 2017-01-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Get Drupal running on a Debian virtual machine instance on Compute Engine with the LAMP stack installed.

Alternatively, you can use options from the
[Cloud Marketplace][marketplace_drupal] to deploy a Drupal stack automatically.

## Objectives

* Set up the virtual machine
* Install Drush
* Download Drupal
* Run the installer
* View your Drupal site
* Send email from Drupal

## Prerequisites

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

## Costs

This tutorial uses billable components of Google Cloud,
including [Compute Engine](https://cloud.google.com/compute/all-pricing).

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage.

## Setting up the virtual machine

First, you need to deploy the LAMP development stack. You can
[set up a LAMP stack][lamp] yourself or you can use the
[Cloud Marketplace][marketplace_lamp]. If you use a Marketplace solution,
make sure that you select the PHP and MySQL versions that Drupal supports. You
also need to read the provider's documentation, because the defaults such as
`/var/www/html` might be changed by the provider.

### Test Apache and PHP

1.  After your virtual machine instance is running,
    get the external IP address of your instance from the
    [VM instances][instances] page in the Cloud Console.
1.  In the **External IP** column, copy the external IP address for your LAMP server name.
1.  In a browser, enter your external IP address to verify that Apache is running:

        http://[YOUR_EXTERNAL_IP_ADDRESS]

    You should see the Apache test page. Make sure that you don't use the `https` protocol specifier, because HTTPS is not configured.

### Connect to your instance

You can connect directly to your instance using SSH from
Cloud Console or using the `gcloud compute ssh` command, which is
part of the [Cloud SDK](https://cloud.google.com/sdk).
This tutorial demonstrates the steps in the Cloud Console.

*  In the [Cloud Console](https://console.cloud.google.com/compute/instances),
    go to the **VM instances** page.
    
*  In the list of virtual machine instances, click the **SSH** button in the row of the instance
    to which you want to connect.    

## Installing Drush and needed packages

[Drush][drush], the Drupal shell utility, simplifies installation and
administration of Drupal.

1.  Install `wget` and PHP `composer`:

        sudo apt-get install wget composer

1.  Download Drush:

        wget -O drush.phar https://github.com/drush-ops/drush/releases/download/8.4.5/drush.phar
   
    If you want to use a different version, you can find the links to available
    versions on the [Drush releases](https://github.com/drush-ops/drush/releases) page.

1.  Move the file:

        chmod +x drush.phar
        sudo mv drush.phar /usr/local/bin/drush

1.  Initialize Drush:

        drush init

## Downloading Drupal

In this section, you use Drush to download Drupal.

1.  Go to the web server root directory:

        cd /var/www/html

1.  Remove the index file:

        sudo rm index.html

1.  Download Drupal:

        sudo drush dl drupal

Drush downloads the latest version. To learn how to download a specific version,
see the help for Drush: `drush --help`.

### Moving the files to the web server's root directory

Drush puts the Drupal files in a subdirectory that uses the format
`drupal-[VERSION]`, where `[VERSION]` represents the Drupal version number. You
probably don't want that directory name in your website path.

1.  Move the files up one level in the directory structure. For example:

        sudo mv drupal-8.9.10/{.[!.],}* ./

1.  Remove the directory, which is now empty:

        sudo rmdir drupal-8.9.10/

## Setting up the database

Create a MySQL database for Drupal and then grant permissions to a non-root user
account that Drupal can use to access the database. If you're using a Marketplace
solution, you can see the MySQL administrator password on the Deployment Manager
deploy page after your LAMP stack is deployed.

1.  Create a new database:

        mysqladmin -u root -p create drupal
        
    In this example, the database is named `drupal`.

1.  Log in to the MySQL console:

        mysql -u root -p

    Enter the MySQL administrator password when prompted.
    
1.  Set the permissions on the database for the MySQL user account used by Drupal:

        CREATE USER 'MYSQL_USERNAME'@'localhost' IDENTIFIED BY 'MYSQL_PASSWORD';
        GRANT ALL ON drupal.* TO 'MYSQL_USERNAME'@'localhost';

    Replace `MYSQL_USERNAME` and `MYSQL_PASSWORD` in these commands with your values.

1.  Exit the MySQL console:

        exit

## Running the installer

Drush runs the installer for you.

You must provide the following information:

* An account name and password you choose for the first Drupal user (the administrator)
* The MySQL user account and password that you created in the previous step

Run the installer with the following command:

    sudo drush site-install \
    --account-name=[NAME] \
    --account-pass=[PASSWORD] \
    --site-name="Drupal on Google Compute Engine" \
    --db-url=mysql://[MYSQL_USERNAME]:[MYSQL_PASSWORD]@localhost/drupal

Replace `[NAME]`, `[PASSWORD]`, `[MYSQL_USERNAME]`, and
`[MYSQL_PASSWORD]` with the appropriate values.

### Updating directory settings

You need to set the Drupal `files` directory to be writeable by the web
server by updating its permissions and ownership.

1.  Change the permissions for the `sites/default/files` directory, as follows:

        sudo chmod o+w sites/default/files

    If you find that the directory doesn't already exist, create a new
    directory named `files` under `sites/default/` and then change its
    permissions.

1.  Change the ownership of the web server root directory so that Apache can
    access files:

        sudo chown -RL www-data:www-data /var/www

## Viewing your Drupal site

Browse to your Drupal site by entering the IP address for your site.

To log in to your site, use the Drupal administrator user name and the Drupal
administrator password that you provided in the Drush installation command.

If you get a `Page not found` error when you click the login link, verify that
your Apache configuration has `AllowOverride` set to `All`. For example, in
`/etc/apache2/apache2.conf`, you should have the following:

        <Directory /var/www/>
                Options Indexes FollowSymLinks
                AllowOverride All
                Require all granted
        </Directory>

## Sending email from Drupal

Compute Engine doesn't allow outbound connections on ports 25, 465,
and 587. To send email from your instances, you must use a partner service,
such as [SendGrid][sendgrid]. SendGrid offers customers of Compute Engine
free or paid packages with costs that vary by monthly email volume.

### Getting a SendGrid account

Use SendGrid's [Google partner page][sendgrid_partner] to create an account.
Note that Google will be compensated for customers who sign up for a paid
package.

For more details about sending email, see [Sending email from an instance][sending].

### Installing the SMTP Authentication Support module on Drupal

You can install the SMTP Authentication Support module to enable Drupal to
send email.

The SMTP Authentication Support module depends on PHP Mailer.

1.  Install PHP Mailer by running the following commands in in the
    command shell that you are connected to through SSH:

        cd /var/www/html
        sudo -uwww-data composer require drupal/phpmailer_smtp

1.  From the **Downloads** section of the [SMTP Authentication Support page][smtp],
    copy the link address for the module. For example, in the **Recommended by the project's maintainer** block, right-click the link to **tar.gz** for the
    latest release and copy its address.
1.  Log in to Drupal as the administrator.
1.  In Drupal, on the **Extend** page, click **Install new module**.
1.  In the **Install from a URL** text box, paste the URL that you copied.
1.  Click **Install**.
1.  After the installation completes, browse to the **Extend** page.
1.  Scroll to the bottom of the page. In the **Mail** section, mark the checkbox.
1.  Click **Install**.

### Configuring the module to use SendGrid

After you have installed the SMTP Authentication Support module, provide the
settings that connect it to your SendGrid account.

1.  In Drupal, on the **Extend** page, locate the **SMTP Authentication Support**
    row, expand it and then click **Configure**. The **Configuration** page opens.
1.  In **Install options**, turn the module on.
1.  In **SMTP server settings**, enter the following settings:
     * **SMTP server**: `smtp.sendgrid.net`
     * **SMTP port**: `2525`
1.  In **SMTP authentication**, enter `apikey` and the API key value that you created
    in your SendGrid account.
1.  In **E-mail options**, enter the address and name that you want email to come
    from. Note that if you don't provide these values, your e-mail will use
    your Drupal site name and have an address similar to `admin@example.com`.
    These values might cause spam filters to intercept the messages.

### Sending test email

You can send an email message from Drupal to test your SendGrid integration.

1. On the same **Configuration** page for the SMTP Authentication Module, select
   **Enable debugging**. This setting lets you see all of the messages about
   activity as your email is being sent.
1. In **Send test e-mail**, enter the email address that you want to send the
   test email message to.
1. Click **Save configuration** to send the email message.

If sending the email message fails, log in to the SendGrid website and verify that your
SendGrid account is active. Activating the account can take some time. You can also check
SendGrid's email activity page to see whether your email was blocked for some reason.

## Next steps

* [Set up a hostname for your website][dns].
* Read the [Drupal documentation][drupal_docs].
* Try out other Google Cloud features. Have a look at the [tutorials][tutorials].

[marketplace_lamp]: https://console.cloud.google.com/marketplace/browse?q=lamp
[lamp]: https://cloud.google.com/compute/docs/tutorials/setting-up-lamp
[marketplace_drupal]: https://console.cloud.google.com/marketplace/browse?q=drupal
[drush]: https://www.drush.org/
[console_instances]: https://console.cloud.google.com/compute/instances
[sendgrid]: https://sendgrid.com/
[sendgrid_partner]: http://sendgrid.com/partner/google?mbsy=gHNj
[sending]: https://cloud.google.com/compute/docs/sending-mail
[smtp]: https://www.drupal.org/project/smtp
[dns]: https://cloud.google.com/community/tutorials/setting-up-lamp#setting_up_dns
[drupal_docs]: https://www.drupal.org/documentation
[tutorials]: https://cloud.google.com/docs/tutorials
