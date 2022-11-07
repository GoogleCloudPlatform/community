---
title: Setting up Joomla! on Compute Engine
description: Learn how to get Joomla! running on a virtual machine instance on Compute Engine.
author: jimtravis
tags: Compute Engine, SendGrid, Joomla
date_published: 2017-01-17
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Get Joomla! running on an Ubuntu virtual machine instance on Compute Engine with the LAMP stack installed.

Alternatively, you can use options from the
[Cloud Marketplace](https://console.cloud.google.com/marketplace/browse?q=joomla) to deploy a Joomla! stack automatically.

## Objectives

* Set up the virtual machine
* Download Joomla!
* Set up the database
* Run the web-based setup
* View your Joomla! site
* Send email from Joomla!

## Prerequisites

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)

1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

## Costs

This tutorial uses billable components of Google Cloud,
including [Compute Engine](https://cloud.google.com/compute/all-pricing).

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage.

## Setting up the virtual machine

First, deploy the LAMP development stack by using
[Cloud Marketplace](http://console.cloud.google.com/marketplace/browse?q=lamp).
Select Ubuntu and use the default options.

Make a note of the **MySQL root password**. You can
return to the **Deployment Manager** page in the Cloud Console to
see the password or any other deployment information at any time.

### Test Apache and PHP

1.  Get the external IP address of your instance from the
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

## Downloading Joomla!

Download the Joomla! package file to your virtual machine instance, unpack the
files, and change the required ownership and permissions settings.

1.  In the SSH console window, change directory to the web root:

        cd /var/www/html

1.  Remove the default `index.html` file:

        sudo rm index.html

1.  Download the package for Joomla! version 3.9.23:

        sudo wget https://downloads.joomla.org/us/cms/joomla3/3-9-23/Joomla_3-9-23-Stable-Full_Package.tar.bz2

    If you want to use a different version, you can find the links to available
    versions on the [Joomla! Downloads](https://downloads.joomla.org/us/cms) page.

1.  Extract the files from the archive that you downloaded:

        sudo tar -xvjf Joomla_3-9-23-Stable-Full_Package.tar.bz2

1.  Change the ownership of the web server root directory so that Apache can access files:

        sudo chown -R www-data:www-data /var/www/

1.  Change the permissions on the files and directories:

        sudo find . -type f -exec chmod 644 {} \;
        sudo find . -type d -exec chmod 755 {} \;

    These settings enable owners to read and write files and to read, write, and execute in the
    directories. Non-owners can read files and read and execute in the directories.
    
1.  Install `sendmail` if it's not installed on your Linux distribution:

        sudo apt install sendmail -y

## Setting up the database

Create a MySQL database for Joomla! and then grant permissions to a non-root user
account that Joomla! can use to access the database. You can see the MySQL
administrator password on the Deployment Manager deploy page after your LAMP stack
is deployed.

1.  Create the new database:

        mysqladmin -u root -p create joomla
        
     In this example, the database is named `joomla`.

1.  Log in to the MySQL console:

        mysql -u root -p

    Enter the MySQL administrator password, when prompted.
    
1.  Set the permissions on the database for the MySQL user account used by Joomla!:

        CREATE USER 'YOUR_USERNAME'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
        GRANT ALL ON joomla.* TO 'YOUR_USERNAME'@'localhost';

    Replace `YOUR_USERNAME` and `YOUR_PASSWORD` in the commands above with your values.

1.  Exit the MySQL console.

        exit

## Running the web-based setup

You can complete the Joomla! setup in your browser.

1. Browse to the Joomla! setup page by entering the external IP address for your
site. Refresh if you still see the Apache test page.
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

## Sending email from Joomla!

Compute Engine doesn't allow outbound connections on ports 25, 465, and
587. To send email from your instances, you must use a partner service, such as
[SendGrid][sendgrid]. SendGrid offers customers of Compute Engine free or
paid packages with costs that vary by monthly email volume.

### Getting a SendGrid account

Use SendGrid's [Google partner page][sendgrid_partner] to create an account.
Note that Google will be compensated for customers who sign up for a paid
package.

For more details about sending email, see [Sending email from an instance][sending].

### Configuring Joomla! to use SendGrid

Use the Joomla! control panel to configure email settings in Joomla!:

1. To browse to the control panel, enter your site's external IP address and
append `/administrator` to the URL. You might need to log in.
1. In the left-side navigation menu, click **Global** under **Configuration**. Alternatively, select **Global Configuration** under the top **System** menu.
1. Select the **Server** tab, in the **Mail Settings** section, verify that **Send Mail** is set to **Yes**.
1. In the **Mailer** list, select **SMTP**.
1. Change **From email** to contain a valid email address from your site's domain.
1. In **SMTP Authentication** select **Yes**.
1. In **SMTP Port** enter `2525`.
1. Enter the username and password for your SendGrid account.
1. In **SMTP Host** enter `smtp.sendgrid.net`.
1. Click **Save & Close**.

### Sending a test email message

You can send an email message from Joomla! to test your SendGrid integration. You must
create a user and then send a private message to the user.

1. In the Joomla! control panel main page, in the left-side navigation, click
**User**.
1. On the **User** page, click **New**.
1. Use the form to provide details about the user. The email address must be
different from the one you used for your administrator account.
1. On the **Assigned User Groups** tab, select **Administrator**.
1. Click **Save & Close**.
1. In the menu bar, select **Components > Messaging > New Private Message**.
1. For **Recipient**, click the button and then select the new user that you
added previously.
1. Enter a subject and a message and then click **Send**.

If sending the email message fails, log in to SendGrid website and verify that your
SendGrid account is active. It's possible that activating the account can take
some time. You can also check SendGrid's email activity page to see whether your
email message was blocked for some reason.

## Next steps

* [Set up a host name for your website][dns].
* Read the [Joomla! documentation][joomla_docs].
* Try out other Google Cloud features. Have a look at the [tutorials][tutorials].

*The Joomla! name, logo and related trademarks are the property of Open Source Matters, Inc. and have been used with permission.*

[instances]: https://console.cloud.google.com/compute/instances
[console_instance]: https://console.cloud.google.com/compute/instances
[sendgrid]: https://sendgrid.com/
[sendgrid_partner]: http://sendgrid.com/partner/google?mbsy=gHNj
[sending]: https://cloud.google.com/compute/docs/sending-mail
[dns]: https://cloud.google.com/community/tutorials/setting-up-lamp#setting_up_dns
[joomla_docs]: https://docs.joomla.org/
[tutorials]: https://cloud.google.com/docs/tutorials
