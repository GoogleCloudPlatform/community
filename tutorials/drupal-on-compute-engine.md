---
title: Setting up Drupal on Compute Engine
description: Learn how to get Drupal running on a virtual machine instance on Compute Engine easily in just a few minutes.
author: jimtravis
tags: Compute Engine, SendGrid, Drupal
date_published: 2017-01-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Get Drupal running on a virtual machine instance on Compute Engine
easily in just a few minutes. You can use automated tools or follow the detailed
tutorial to configure Drupal on a Debian virtual machine instance with the LAMP
stack installed and root access.

## Objectives

* Setting up the virtual machine
* Installing Drush
* Downloading Drupal
* Running the installer
* Viewing your Drupal site
* Sending email from Drupal

## Setting up the virtual machine

First, automatically deploy the LAMP development stack. You can use the
[Cloud Launcher][launcher], or you can [set up a LAMP stack][lamp] yourself.

You can also automatically deploy Drupal on your virtual machine by using the
[Cloud Launcher][launcher_drupal] or you can use the remaining steps to install
Drupal yourself.

After your virtual machine instance is up and running, use the Cloud
Console to connect over SSH.

## Installing Drush

[Drush][drush], the Drupal shell utility, simplifies installation and
administration of Drupal. Use the following steps to install Drush:

1. Download Drush:

        wget https://github.com/drush-ops/drush/releases/download/8.0.0-rc4/drush.phar

1. Move the file:

        chmod +x drush.phar
        sudo mv drush.phar /usr/local/bin/drush

1. Initialize Drush:

        drush init

## Downloading Drupal

Drush can download Drupal for you. Follow these steps:

1. Change directory to the web server root directory:

        cd /var/www/html

1. Remove the index file:

        sudo rm index.html

1. Download Drupal by using Drush:

        sudo drush dl drupal

Drush downloads the latest version. To learn how to download a specific version,
see the help for Drush: `drush --help`.

### Moving the files to the web server's root directory

Drush puts the Drupal files in a subdirectory that uses the format
`drupal-VERSION`, where `VERSION` represents the Drupal version number. You
probably don't want that directory name in your website path.

1. Move the files up one level in the directory structure. Note that the version
   number appears twice.

        sudo mv drupal-/* drupal-/.htaccess ./

    For Drupal 7, add:

        sudo mv drupal-/.gitignore ./

1. Remove the now-empty directory:

        sudo rm -rf drupal-/

## Running the installer

Drush runs the installer for you. You must provide the following information:

* The password of the MySQL administrator that you provided before deploying the
  LAMP stack.
* An account name and password for the first Drupal user (the administrator).
* A name and user account information for the MySQL database.

Use the following command:

    sudo drush site-install \
      --db-su=root \
      --db-su-pw=MYSQL_ADMIN_PASSWORD \
      --account-name=NAME \
      --account-pass=PASSWORD \
      --site-name="Drupal on Google Compute Engine" \
      --db-url=mysql://MYSQL_USERNAME:MYSQL_PASSWORD@localhost/DATABASE_NAME

replacing `MYSQL_ADMIN_PASSWORD`, `NAME`, `PASSWORD`, `MYSQL_USERNAME`,
`MYSQL_PASSWORD`, and `DATABASE_NAME` with the appropriate values.

### Updating directory settings

You will need to set the Drupal `files` directory to be writeable by the web
server by updating its permissions and ownership.

1. Change the permissions for the `sites/default/files` directory, as follows:

        sudo chmod o+w sites/default/files

    If you find that the directory doesn't already exist, simply create a new
    directory named `files` under `sites/default/` and then change its
    permissions.

1. Change the ownership of the web server root directory so that Apache can
   access files:

        sudo chown -RL www-data:www-data /var/www

## Viewing your Drupal site

To view your Drupal site in a browser, first open port 80 to allow
HTTP traffic to your server. Follow these steps:

1. View your virtual machine instances in the
   [Compute Engine instances page][console_instances].
1. In the **External IP** column, click the external IP address for your Drupal
   server name.
1. In the dialog box that opens, select the **Allow HTTP** traffic check box.
1. Click **Apply** to close the dialog box.

After completing these steps, you can click the external IP address link or
enter it in the address bar to open your Drupal site's home page in your
browser.

To log in to your site, use the Drupal administrator user name and the Drupal
administrator password that you provided in the Drush installation command.

## Sending email from Drupal

Google Compute Engine doesn't allow outbound connections on ports 25, 465,
and 587. To send email from your instances, you must use a partner service,
such as [SendGrid][sendgrid]. SendGrid offers customers of Google Compute Engine
free or paid packages with costs that vary by monthly email volume.

### Getting a SendGrid account

Use SendGrid's [Google partner page][sendgrid_partner] to create an account.
Note that Google will be compensated for customers who sign up for a paid
package.

For more details about sending email, see [Sending Email from an Instance][sending].

### Installing the SMTP Authentication Support module on Drupal

You must install the SMTP Authentication Support module to enable Drupal to
send email.

1. From the **Downloads** section of the [SMTP Authentication Support page][smtp],
   copy the link address for the module. For example, in the **Recommended releases**
   table, right-click the link to **tar.gz** for the latest release and then copy
   its address.
1. Log in to Drupal as the administrator.
1. In Drupal, on the **Modules** page, click **Install new module**.
1. In the **Install from a URL** text box, paste the URL that you copied.
1. Click **Install**.
1. After the installation completes, browse to the **Modules** page.
1. Scroll to the bottom of the page. In the **Mail** section, select **Enabled**.
1. Click **Save configuration**.

### Configuring the module to use SendGrid

Now that the SMTP Authentication Support module is installed, provide the
settings that connect it to your SendGrid account.

1. In Drupal, on the **Modules** page, locate the **SMTP Authentication Module**
   row and then click **Configure**. The **Configuration** page opens.
1. In **Install options**, turn the module on.
1. In **SMTP server settings**, enter the following settings:
    * **SMTP server**: `smtp.sendgrid.net`
    * **SMTP port**: `2525`
1. In **SMTP authentication**, enter the username and password that you provided
   when you set up your SendGrid account.
1. In **E-mail options**, enter the address and name that you want email to come
   from. Note that if you don't provide these values, your e-mail will use
   your Drupal site name and have an address similar to `admin@example.com`.
   These values might cause spam filters to intercept the messages.

### Sending a test email

You can send an email from Drupal to test your SendGrid integration.

1. On the **Configuration** page for the SMTP Authentication Module, select
   **Enable debugging**. This setting lets you see all of the messages about
   activity as your email is being sent.
1. In **Send test e-mail**, enter the email address that you want to send the
   test email to.
1. Click **Save configuration** to send the email.

If sending the email fails, log in to SendGrid website and verify that your
SendGrid account is active. It's possible that activating the account can take
some time. You can also check SendGrid's email activity page to see whether
your email was blocked for some reason.

## Next steps

* [Set up a host name for your website][dns]
* Read the [Drupal documentation][drupal_docs]
* Try out other Google Cloud features. Have a look at the [tutorials][tutorials].

[launcher]: https://cloud.google.com/launcher/?q=lamp
[lamp]: https://cloud.google.com/compute/docs/tutorials/setting-up-lamp
[launcher_drupal]: https://cloud.google.com/launcher/?q=drupal
[drush]: http://docs.drush.org/en/master/
[console_instances]: https://console.cloud.google.com/compute/instances
[sendgrid]: https://sendgrid.com/
[sendgrid_partner]: http://sendgrid.com/partner/google?mbsy=gHNj
[sending]: https://cloud.google.com/compute/docs/sending-mail
[smtp]: https://www.drupal.org/project/smtp
[dns]: https://cloud.google.com/compute/docs/tutorials/lamp/setting-up-dns
[drupal_docs]: https://www.drupal.org/documentation
[tutorials]: https://cloud.google.com/docs/tutorials
