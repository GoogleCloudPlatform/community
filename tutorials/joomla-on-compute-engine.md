---
title: Setting up Joomla! on Compute Engine
description: Learn how to get Joomla! running on a virtual machine instance on Compute Engine easily in just a few minutes.
author: jimtravis
tags: Compute Engine, SendGrid, Joomla
date_published: 2017-01-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Get Joomla! running on a virtual machine instance on Compute Engine easily
in just a few minutes. Follow the detailed tutorial to configure Joomla! on a
Debian virtual machine instance with the LAMP stack installed and root access.

## Objectives

* Setting up the virtual machine
* Downloading Joomla!
* Setting up the database
* Running the web-based setup
* Viewing your Joomla! site
* Sending email from Joomla!

## Setting up the virtual machine

First, automatically deploy the LAMP development stack by using
[Cloud Launcher][launcher].

When done, make a note of the **MySQL administrator password**. You can always
return to the **Click to Deploy** page in the Cloud Console to
see the password or any other deployment information at any time.

Next, open port 80 to allow HTTP traffic to your server. Follow these steps:

1. View your virtual machine instances in the
[Compute Engine instances page][instances].
1. In the **External IP** column, click the external IP address for your LAMP server
name.
1. In the dialog box that opens, select the **Allow HTTP traffic** check box.
1. Click Apply to close the dialog box.

## Downloading Joomla!

Download the Joomla! package file to your virtual machine instance, unpack the
files, and change the required ownership and permissions settings.

1. Use the Cloud Console to connect to your virtual machine
instance over SSH.

1. In the SSH console window, change directory to the web root.

        cd /var/www/html

1. Remove the default index.html file. This step will leave a robots.txt file.

        sudo rm index.html

1. Enter the following command to download the package for Joomla! version 3.3.6.

        sudo wget http://joomlacode.org/gf/download/frsrelease/19822/161255/Joomla_3.3.6-Stable-Full_Package.tar.gz

    If you want to use a different version, you can find the links to available
    versions on the [JoomlaCode][joomlacode] page.

1. Extract the files from the archive that you downloaded.

        sudo tar -xvzf Joomla_VERSION-Stable-Full_Package.tar.gz

    replacing `VERSION` with the version of Joomla! that you downloaded.

1. Change the ownership of the web server root directory so that Apache can
access files.

        sudo chown -R www-data:www-data /var/www/

1. Change the permissions on the files and directories. These settings enable
owners to read and write files and to read, write, and execute in the
directories. Non-owners can read files and and read and execute in the
directories.

        sudo find . -type f -exec chmod 644 {} \;
        sudo find . -type d -exec chmod 755 {} \;

## Setting up the database

Create a MySQL database for Joomla! and then grant permissions to a non-root user
account that Joomla! can use to access the database. You can see MySQL
administrator password on the Click to Deploy setup page after your LAMP stack
is deployed.

1. Create the new database. For example, you can name the database "joomla".

        mysqladmin -u root -p create joomla

1. Log in to the MySQL console. Enter the MySQL administrator password, when
prompted.

        mysql -u root -p

1. Set the permissions on the database for the MySQL user account used by
Joomla!.

        GRANT ALL ON YOUR_DATABASE_NAME.* TO 'YOUR_USERNAME'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';

    replacing `YOUR_DATABASE_NAME`, `YOUR_USERNAME`, and `YOUR_PASSWORD` with
    your values.

1. Exit the MySQL console.

        exit

## Running the web-based setup

You can complete the Joomla! setup in your browser.

1. Browse to the Joomla! setup page by entering the external IP address for your
site. Alternatively, you can click the IP address link for your virtual machine
instance in the [virtual machine instance in the Cloud Console][console_instance].
1. Enter the required information on the **Configuration** tab and then click
**Next**.
1. On the **Database** tab, enter the information about the MySQL account that
you previously created. Be sure to use the same account name, password, and
database name that you provided when you set the database permissions. Click
**Next** when you're done.
1. On the **Overview** tab, select an option for sample data. For a production
site, you'll probably want to accept the default value of **None**.
1. In the **Email configuration** setting, click **Yes** if you want Joomla! to
send you an email containing your site settings.
1. To complete the setup, click **Install**.
1. When the setup is done, click **Remove installation folder** to clean up the
setup files.

## Viewing your Joomla! site

You can browse to your Joomla! site by entering the IP address for your site.
Alternatively, you can click the external IP address link for your
[virtual machine instance in the Cloud Console][console_instance].

## Sending email from Joomla!

Google Compute Engine doesn't allow outbound connections on ports 25, 465, and
587. To send email from your instances, you must use a partner service, such as
[SendGrid][sendgrid]. SendGrid offers customers of Google Compute Engine free or
paid packages with costs that vary by monthly email volume.

### Getting a SendGrid account

Use SendGrid's [Google partner page][sendgrid_partner] to create an account.
Note that Google will be compensated for customers who sign up for a paid
package.

For more details about sending email, see [Sending Email from an Instance][sending].

### Configuring Joomla! to use SendGrid

Use the Joomla! control panel to configure email settings in Joomla!.

1. To browse to the control panel, enter your site's external IP address and
append `/administrator` to the URL. You might need to log in.
1. In the left-side navigation menu, click **Global Configuration**.
1. In the **Mail Settings** section, verify that **Send mail** is set to **Yes**.
1. In the **Mailer** list, select **SMTP**.
1. Change **From email** to contain a valid email address from your site's domain.
1. In **SMTP Authentication** select **Yes**.
1. In **SMTP Port** enter `2525`.
1. Enter the username and password for your SendGrid account.
1. In **SMTP Host** enter `smtp.sendgrid.net`.
1. Click **Save & Close**.

### Sending a test email

You can send an email from Joomla! to test your SendGrid integration. You must
create a user and then send a private message to the user.

1. In the Joomla! control panel main page, in the left-side navigation, click
**User Manager**.
1. On the **User Manager** page, click **New**.
1. Use the form to provide details about the user. The email address must be
different from the one you used for your administrator account.
1. On the **Assigned User Groups** tab, select **Administrator**.
1. Click **Save & Close**.
1. In the menu bar, select **Components > Messaging > New Private Message**.
1. For **Recipient**, click the button and then select the new user that you
added previously.
1. Enter a subject and a message and then click **Send**.

If sending the email fails, log in to SendGrid website and verify that your
SendGrid account is active. It's possible that activating the account can take
some time. You can also check SendGrid's email activity page to see whether your
email was blocked for some reason.

## Next steps

* [Set up a host name for your website][dns].
* Read the [Joomla documentation][joomla_docs].
* Try out other Google Cloud features. Have a look at the [tutorials][tutorials].

*The Joomla! name, logo and related trademarks are the property of Open Source Matters, Inc. and have been used with permission.*

[launcher]: https://cloud.google.com/launcher/?q=lamp
[instances]: https://console.cloud.google.com/compute/instances
[joomlacode]: http://joomlacode.org/gf/project/joomla/frs/?action=FrsReleaseBrowse&frs_package_id=6957
[console_instance]: https://console.cloud.google.com/compute/instances
[sendgrid]: https://sendgrid.com/
[sendgrid_partner]: http://sendgrid.com/partner/google?mbsy=gHNj
[sending]: https://cloud.google.com/compute/docs/sending-mail
[dns]: https://cloud.google.com/compute/docs/tutorials/lamp/setting-up-dns
[joomla_docs]: https://docs.joomla.org/
[tutorials]: https://cloud.google.com/docs/tutorials
