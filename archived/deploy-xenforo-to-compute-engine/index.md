---
title: Deploying XenForo to Compute Engine
description: Learn how to deploy a XenForo application to Compute Engine.
author: michaelawyu
tags: Compute Engine, PHP, XenForo, Cloud Storage, Cloud SQL
date_published: 2017-12-04
---

Chen Yu | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial explains how to deploy [XenForo](https://xenforo.com/) on
[Compute Engine](https://cloud.google.com/compute/).

XenForo is an extensible and flexible community forum software written in PHP.
With proper configurations, you can transform XenForo into a simple message
board of your own or an online forum serving thousands of users.

Compute Engine delivers virtual machines (VMs) running in Google’s
data centers and worldwide fiber network. Compute Engine allows you
to host your own XenForo website, while giving you all the benefits of
Google Cloud, such as fast and efficient networking, high flexibility,
great performance, and access to a variety of Google Cloud services.

## Objectives

* Create a Compute Engine instance
* Configure the instance for XenForo
* Upload and deploy XenForo

## Costs

This tutorial uses billable components of Google Cloud, including

* Compute Engine
* Cloud Storage
* Google Compute Network Bandwidth

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to
generate a cost estimate based on your projected usage. Depending on the scale
of your XenForo website, you might be eligible for
[Google Cloud Free Tier](https://cloud.google.com/free/). Costs listed
above do not include the license fee for purchasing XenForo.

## Before you begin

1.  Create or select a project from [Cloud Console](https://console.cloud.google.com/).
		If you have never used Google Cloud before, sign up or log in with
		your existing Google account, then follow the on-screen instructions to
		start using Google Cloud.
1.  [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project)
		for your account.
1.  Install the [Cloud SDK](https://cloud.google.com/sdk/) (Optional).
1.  Create a Compute Engine instance. You can do this from the
		[VM Instances](https://console.cloud.google.com/compute/instances) page of
		Cloud Console, via Cloud SDK, or using the Compute Engine API.

	If you decide to use Cloud Console, perform the following steps:

	* Enter the name of your instance and choose a
		[compute zone](https://cloud.google.com/compute/docs/regions-zones/) for it.
		Compute zone determines what computing resources are available and where
		your data is stored. Though you may deploy your instance in any compute zone
		you like, generally speaking it is better to deploy it as close as possible
		to the visitors of your website.
	* Grant your instance full access to all Cloud APIs.
	* Allow HTTP and HTTPS traffic to your instance.
	* Click **Create**. It takes a short while for Compute Engine to create and
		start your instance.

	Depending on the scale of your website, you may need to add more CPU cores,
	increase the amount of memory available, and use a large SSD persistent boot
	disk instead of the default 10GB standard one. However, for the purposes of
	this tutorial, you can leave these settings unchanged.. It is also possible to
	upgrade (or downgrade) your instance after deployment.

	For instructions on creating and starting a Compute Engine instance via Cloud
	SDK or with Compute Engine API, refer to the
	[Creating and Starting an Instance page](https://cloud.google.com/compute/docs/instances/create-start-instance)
	in the Compute Engine documentation.

5. Download your copy of XenForo from XenForo’s website. For this tutorial you
need to use XenForo 1.5.

## Understanding the architecture

To serve requests from the Internet, XenForo needs to work with a web server
frontend and a MySQL database backend. In this tutorial you will use
[Apache HTTP server](https://httpd.apache.org/) for the web server and
[MariaDB](https://mariadb.org/) for the database. At a basic level, the
architecture of the project looks as follows:

![Understanding the Architecture](https://storage.googleapis.com/gcp-community/tutorials/deploy-xenforo-to-compute-engine/architecture_overview.png)

## Installing the prerequisites

To complete the following steps, you need to connect to your Compute Engine
instance. To connect to your instance using Cloud Console, visit the
[VM Instances](https://console.cloud.google.com/compute/instances) menu and
click **SSH** in the row of the instance that you want to connect to. For other
ways of connecting to instances, refer to the
[Connecting to Linux Instances](https://cloud.google.com/compute/docs/instances/connecting-to-instance)
page of Compute Engine documentation.

1.  Update package lists to get information on the newest packages and their
    dependencies:

				sudo apt-get update

1.  Install Apache server and its module for PHP support:

				sudo apt-get install apache2 apache2-mod-php7.0 -y

		After the installation is complete, open your browser and visit
		`http://[SERVER_EXTERNAL_IP]` (note that it is a HTTP link instead of a
		HTTPS link). `[SERVER_EXTERNAL_IP]` can be found on the
		[VM Instances](https://console.cloud.google.com/compute/instances) menu, in
		the row of the instance that you connect to. You should see a page titled
		"Apache Debian Default Page" in your browser.

1.  Install MariaDB server:

				sudo apt-get install mariadb-server -y

1.  Set up MariaDB:

				sudo mysql_secure_installation

		The script prepares MariaDB for production use. For security reasons, you
		should follow the on-screen prompts, set up a root password, remove all
		anonymous users, disable remote login for the root user, remove test
		database, and reload the privilege tables.

1.  Create a database and a database user for XenForo to use:

				sudo mysql

		Then enter the following commands in MariaDB monitor:

				CREATE DATABASE [DATABASE_NAME];
				CREATE USER ‘[DATABASE_USER]’@’localhost’ IDENTIFIED BY ‘[DATABASE_PASSWORD]’;
				GRANT ALL PRIVILEGES ON *.* TO ‘[DATABASE_USER]’@’localhost’;

		These commands create a new database and a new database user with full
		privileges in the system. Replace `[DATABASE_NAME]`, `[DATABASE_USER]` and
		`[DATABASE_PASSWORD]` with your own values. You might want to write down
		these values, as you need them to install XenForo.

1.  Install PHP and PHP modules required by XenForo:

				sudo apt-get install php7.0 php7.0-mysql php7.0-gd php7.0-xml -y

1.  Install additional tools and packages:

			sudo apt-get install unzip postfix libsasl2-modules

		Although not all of the tools and packages listed above are required for
		XenForo, you might find them useful during installation and configuration.

		During the installation of postfix, a configuration screen is presented. Use
		the TAB key to move the cursor, UP and DOWN keys to change the choice, and
		Enter to confirm. For this tutorial, use the Local Only type and leave other
		settings unchanged.

		Now the instance is ready to run XenForo.

## Uploading and configuring XenForo

1.  Copy the XenForo installation file to your Compute Engine instance:

		* Visit the [Cloud Storage Browser](https://console.cloud.google.com/storage/browser)
			menu and click Create **Bucket**. Enter a name for the new bucket and
			choose a storage class for the bucket on the new page. For this tutorial,
			create a regional bucket in the same location as your Compute Engine
			instance.
		* Click **Upload Files** and choose your XenForo installation file. It
			should be a .zip file downloaded from XenForo website. If you have Cloud
			SDK installed on your system, you can also
			[use the `gsutil` tool to upload the file](https://cloud.google.com/storage/docs/gsutil/commands/cp).
		* Connect to your Compute Engine instance and download the file you uploaded
			earlier:

    			gsutil cp gs://[BUCKET_NAME]/[FILENAME] .

    	`gsutil` is pre-installed on your Compute Engine instance. The command
			above copies the file you uploaded earlier to your Compute Engine
			instance. Replace `[BUCKET_NAME]` and `[FILENAME]` with your bucket name
			and the name of your XenForo installation file respectively.

1.  Unzip the installation file and copy the contents to Apache web root directory:

		* Unzip the installation file:

	    		unzip [FILENAME]

			where `[FILENAME]` is the name of your XenForo installation file.

	* Copy the contents to Apache web root directory:

	    	sudo cp -r upload/* /var/www/html

	* Change directory to Apache web root directory, grant file access permission
		XenForo requires and remove the default homepage (`index.html`):

				cd /var/www/html
				sudo chmod -R 777 *
				sudo rm index.html

	* Open your browser and visit `https://[SERVER_EXTERNAL_IP]`. As shown in
		previous steps, you can find the external IP of your Compute Engine instance
		on the [VM Instances](https://console.cloud.google.com/compute/instances)
		page, in the row of the instance that you connect to. Follow the prompts on
		screen to configure your XenForo installation. During installation XenForo
		will ask you for credentials to connect to your MySQL server. Your MySQL
		Server and MySQL Port are localhost and 3306 respectively. Your MySQL User
		Name, MySQL Password and MySQL Database Name are the values you entered
		previously when installing MariaDB.

Your XenForo website is now up and running.

## Setting up a mailing service

XenForo by default uses a mail transfer agent (MTA), such as postfix, to send
emails. The agent then utilizes an outgoing connection to common SMTP ports
(25, 587, etc.) to transfer information (mails). However, many cloud service
providers, including Google Cloud, block such connections for security
reasons; additionally, emails sent this way are often considered spam by many
email service providers, and are dropped before getting into the inboxes of
recipients. For these reasons, you should use a third-party service for sending
emails from your XenForo website.

[SendGrid](https://sendgrid.com/), [Mailgun](https://www.mailgun.com/), and
[Mailjet](https://www.mailjet.com/) are Compute Engine’s third-party partners
for sending emails. For more information on Compute Engine’s partnerships with
these services, refer to [Sending Email with SendGrid](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-sendgrid),
[Sending Email with Mailgun](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-mailgun),
and [Sending Email with Mailjet](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-mailjet).
If you plan to use other services, follow instructions on their websites to set
up SMTP Relay for your XenForo website.

Instructions below are general procedures to set up a mailing service for this
tutorial:

1.  Sign up with the mailing service you would like to use. Write down the SMTP
    username and the SMTP password provided by the service.

1.  Connect to your Compute Engine instance and change to the directory of
		postfix preferences:

				cd /etc/postfix

1.  Edit the preferences:

				nano main.cf

		Use arrow keys (UP, DOWN, LEFT, and RIGHT keys) to move the cursor around. Comment out the following lines:

		| Before                    | After                     |
		| --------------------------|---------------------------|
		| default_transport = error | #default_transport = error |
		| relay_transport = error   | #relay_transport = error  |

		Edit the following lines:

		| Before      | After                             |
		| ------------|-----------------------------------|
		| relayhost = | relayhost = [RELAY_SERVER]:[PORT] |

		where the `[RELAY_SERVER]` and `[PORT]` are provided by the mailing service.
		Note that you cannot use common SMTP ports such as 25, 465 or 587. If you
		are using SendGrid, Mailgun, or Mailjet, here are their relay services and
		ports for Compute Engine instances, as seen in the
		[Compute Engine documentation](https://cloud.google.com/compute/docs/tutorials/sending-mail/):

		| Mailing Service | Relay Server      | Port |
		| --------------- |-------------------|------|
		| SendGrid        | smtp.sendgrid.net | 2525 |
		| Mailgun         | smtp.mailgun.org  | 2525 |
		| Mailjet         | in.mailjet.com    | 2525 |

		and finally, move to the end of the file and add the following lines:

				smtp_tls_security_level = encrypt
				smtp_sasl_auth_enable = yes
				smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
				smtp_sasl_security_options = noanonymous

1.  Generate a new SASL password map and convert it to a .db file:

				sudo nano sasl_password

		Enter this line:

				[RELAY_SERVER]:[PORT] [SMTP_USERNAME]:[SMTP_PASSWORD]

		Replace `[RELAY_SERVER]`, `[PORT]`, `[SMTP_USERNAME]` and `[SMTP_PASSWORD]`
		with the values you used or recorded earlier.

		Press Ctrl + O (Control Key and O Key together) to write the file. Then press Ctrl + X (Control Key and X Key together) to exit.

		Convert the file you just created to a .db file, grant proper access permission to it, and remove the old file with the following commands:

				sudo postmap sasl_password
				sudo chmod 600 sasl_password.db
				sudo rm sasl_password

1.  Restart the postfix service:

				sudo service postfix restart

		Now your XenForo website can use the third-party service to send emails more
		securely and efficiently.

## Update your domain (optional)

Anyone can now use the external IP of your Compute Engine instance to access
your XenForo website. To assign a domain name to this IP address, perform the
following steps:

1.  Assign a static IP to your Compute Engine instance:

		Currently the external IP you see on the [VM Instances](https://console.cloud.google.com/compute/instances)
		menu changes every time you restart the instance. You need to assign a
		static IP address to it to make sure that your website is always accessible
		even if the server restarts. Visit the [External IP addresses](https://console.cloud.google.com/networking/addresses/list)
		menu, and click **Ephemeral** in the row of the Compute Engine instance
		hosting your XenForo website. From the drop-down menu, choose **Static**.
		Enter a new name for this static address, then click **Reserve**.

		If you have Cloud SDK installed in the system, you can also
		[use the `gcloud` command-line to reserve a static IP address](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address).

1.  If you haven’t done so, get a domain name from domain name registrars.
		Follow their instructions to add the IP address you just reserved to your
		domain. Your website should be accessible with the domain name in a short
		while.

## Cleaning up

After you have finished this tutorial, you can clean up the resources you
created on Google Cloud so that you will not be billed for them in the
future. To clean up, you can delete the whole project or stop the Compute Engine
instance.

### Deleting the project

Visit the [Manage resources](https://console.cloud.google.com/cloud-resource-manager)
menu. Select the project you used for this tutorial and click **Delete**. Note
that once the project is deleted, the project ID cannot be reused.

If you have Cloud SDK installed in the system, you can also
[use the `gcloud` command-line to delete a project](https://cloud.google.com/sdk/gcloud/reference/projects/delete).

### Stopping the Compute Engine instance

Visit the [VM Instances](https://console.cloud.google.com/compute/instances)
menu. Select the instance you used for this tutorial and click **Stop**. If you
have reserved a static IP address, you are charged at an hourly rate when the
address is not used. To release the address, go to
[External IP addresses](https://console.cloud.google.com/networking/addresses/list)
menu, select the address, and click **Release Static Address**. You may also
want to go to the Cloud Storage [browser](https://console.cloud.google.com/storage/browser)
page and delete the bucket you created during the tutorial.
