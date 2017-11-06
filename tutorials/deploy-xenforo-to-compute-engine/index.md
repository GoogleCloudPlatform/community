# Deploying XenForo on Google Cloud Platform with Compute Engine

This tutorial explains how to deploy [XenForo](https://xenforo.com/) on [Google Cloud Compute Engine](https://cloud.google.com/compute/).

XenForo is an extensible and flexible community forum software written in PHP. With proper configurations you can transform XenForo into a simple message board of your own or an online forum serving thousands of users.

Google Cloud Compute Engine delivers virtual machines (VMs) running in Google’s innovative data centers and worldwide fiber network. Compute Engine allows you to easily host your own XenForo website, while giving you all the benefits of Google Cloud Platform, such as fast and efficient networking, high flexibility, great performance and access to a variety of Google Cloud services.

## Objectives

* Create a compute engine instance
* Configure the instance for XenForo
* Upload and deploy XenForo

## Costs

This tutorial uses billable components of Google Cloud Platform, including

* Google Compute Engine
* Google Cloud Storage
* Google Compute Network Bandwidth

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage. Depending on the scale of your XenForo website, you might be eligible for [Google Cloud Platform Free Tier](https://cloud.google.com/free/). Costs listed above DOES NOT include the license fee for purchasing XenForo.

## Before you begin

1. Create or select a project from [Google Cloud Console](https://console.cloud.google.com/). If you have never used Google Cloud Platform before, sign up or log in with your existing Google Account, then follow the instructions on screen to start using Google Cloud Platform.
2. [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project) for your account.
3. Install the [Google Cloud SDK](https://cloud.google.com/sdk/) (Optional).
4. Create a Compute Engine instance. You can do this from [Cloud Console](https://console.cloud.google.com/compute/instances), via Cloud SDK or with Compute Engine API.

	If you decide to use Cloud Console:

	* Enter the name of your instance and choose a zone for it. The zone determines what computing resources are available and where your data is stored. Though you may deploy your instance in any zone you like, generally speaking it is better to deploy it as close as possible to the visitors of your website.
	* Grant your instance full access to all Cloud APIs.
	* Allow HTTP and HTTPS traffic to your instance.
	* Click Create. It takes a short while for Compute Engine to create and start your instance.

	Depending on the scale of your website, you may need to add more CPU cores, increase the amount of memory available and use a large SSD persistent boot disk instead of the default 10GB standard one. Though for this tutorial it is OK to leave these settings unchanged. It is also possible to upgrade (or downgrade) your instance after deployment.

	For instructions on creating and starting a Compute Engine instance via Cloud SDK or with Compute Engine API, refer to the [Creating and Starting an Instance page](https://cloud.google.com/compute/docs/instances/create-start-instance) in Compute Engine documentation.

5. Download your copy of XenForo from XenForo’s website. For this instruction you need to use XenForo 1.5.

## Understanding the Architecture

XenForo needs to work with a web server software and a MySQL database backend to serve requests from the Internet. In this tutorial you will use [Apache HTTP server](https://httpd.apache.org/) for web server software and [MariaDB](https://mariadb.org/) for database backend. At a basic level, the architecture of the project looks as follows:

![Understanding the Architecture](/architecture_overview.png)

## Installing the Prerequisites

You need to connect to your Compute Engine instance to complete the following steps. To connect from your browser, go to the [VM Instances page](https://console.cloud.google.com/compute/instances) and click **SSH** in the row of the instance that you want to connect to. For other ways of connecting to instances, refer to the [Connecting to Linux Instances](https://cloud.google.com/compute/docs/instances/connecting-to-instance) page of Compute Engine documentation.

1. Update package lists to get information on the newest packages and their dependencies:

	```bash
	sudo apt-get update
	```

2. Install Apache server and its module for PHP support:

	```bash
	sudo apt-get install apache2 apache2-mod-php7.0 -y
	```

	After the installation is completed, open your browser and visit http://[SERVER_EXTERNAL_IP] (note that it is a HTTP link instead of a HTTPS link). [SERVER_EXTERNAL_IP] can be found on the [VM Instances](https://console.cloud.google.com/compute/instances) page, in the row of the instance that you connect to. You should see a page titled “Apache Debian Default Page” in your browser. 

3. Install MariaDB server:

	```bash
	sudo apt-get install mariadb-server -y
	```

4. Set up MariaDB:

	```bash
	sudo mysql_secure_installation
	```

	The script prepares MariaDB for production use. For security reasons you should follow the prompts on screen, set up a root password, remove all anonymous users, disable remote login for root user, remove test database and reload the privilege tables.

5. Create a database and a database user for XenForo to use:

	```bash
	sudo mysql
	```

	Then enter the following commands in MariaDB monitor:

	```sql
	CREATE DATABASE [DATABASE_NAME];
	CREATE USER ‘[DATABASE_USER]’@’localhost’ IDENTIFIED BY ‘[DATABASE_PASSWORD]’;
	GRANT ALL PRIVILEGES ON *.* TO ‘[DATABASE_USER]’@’localhost’;
	```

	Commands above create a new database and a new database user with full privileges in the system. Replace [DATABASE_NAME], [DATABASE_USER] and [DATABASE_PASSWORD] with values of your own. You may want to write down those values as you need to use them later when installing XenForo.

6. Install PHP and PHP modules required by XenForo:

	```bash
	sudo apt-get install php7.0 php7.0-mysql php7.0-gd php7.0-xml -y
	```

7. Install additional tools and packages:

	```bash
	sudo apt-get install unzip postfix libsasl2-modules
	```

	Not all of the tools and packages listed above are required XenForo; however you may find them useful when installing and configuring XenForo.

	During the installation of postfix a configuration screen will come up. Use TAB key to move the cursor, UP and DOWN keys to change the choice and Enter to confirm. For this tutorial we will use the `Local Only` type. You can leave other settings unchanged.

	Now the instance is ready for running XenForo. 

## Uploading and Configuring XenForo

1. Copy the XenForo installation file to your Compute Engine instance:

	* Open [Cloud Storage Browser](https://console.cloud.google.com/storage/browser) page and click Create **Bucket**. Enter a name for the new bucket and choose a storage class for the bucket in the new page. For this tutorial you should create a regional bucket in the same location as your Compute Engine instance.
	* Click **Upload Files** and choose your XenForo installation file. It should be a .zip file downloaded from XenForo website. If you have Cloud SDK installed on your system, you can also [use the gsutil tool to upload the file](https://cloud.google.com/storage/docs/gsutil/commands/cp).
	* Connect to your Compute Engine instance and download the file you uploaded earlier:

	```bash
	gsutil cp gs://[BUCKET_NAME]/[FILENAME] .
	```

	`gsutil` is pre-installed on your Compute Engine instance. The command above copies the file you uploaded earlier to your Compute Engine instance. Replace [BUCKET_NAME] and [FILENAME] with your bucket name and the name of your XenForo installation file respectively.

2. Unzip the installation file and copy the contents to Apache web root directory:

	* Unzip the installation file:

	```bash
	unzip [FILENAME]
	```

	where [FILENAME] is the name of your XenForo installation file.

	* Copy the contents to Apache web root directory:

	```bash
	sudo cp -r upload/* /var/www/html
	```

	* Change directory to Apache web root directory, grant file access permission XenForo requires and remove the default homepage (index.html):

	```bash
	cd /var/www/html
	sudo chmod -R 777 *
	sudo rm index.html
	```

	* Open your browser and visit https://[SERVER_EXTERNAL_IP]. As shown in previous steps, you can find the external IP of your Compute Engine instance on the [VM Instances](https://console.cloud.google.com/compute/instances) page, in the row of the instance that you connect to. Follow the prompts on screen to configure your XenForo installation. During installation XenForo will ask you for credentials to connect to your MySQL server. Your MySQL Server and MySQL Port are localhost and 3306 respectively. Your MySQL User Name, MySQL Password and MySQL Database Name are the values you entered previously when installing MariaDB.

Your XenForo website is now up and running.

## Setting Up a Mailing Service

XenForo by default uses a mail transfer agent (MTA), such as postfix, to send emails. The agent then utilizes an outgoing connection to common SMTP ports (25, 587, etc.) to transfer information (mails). However, many Cloud service providers, including Google Cloud Platform, block such connections for security reasons; additionally, emails sent this way are often considered spams by many email service providers, and will be dropped before getting into the inboxes of recipients. For those reasons, you should use a third-party service for sending emails from your XenForo website.

[SendGrid](https://sendgrid.com/), [Mailgun](https://www.mailgun.com/), and [Mailjet](https://www.mailjet.com/) are Compute Engine’s third-party partners for sending emails. For more information on Compute Engine’s partnerships with those services, refer to [Sending Email with SendGrid](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-sendgrid), [Sending Email with Mailgun](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-mailgun) and [Sending Email with Mailjet](https://cloud.google.com/compute/docs/tutorials/sending-mail/using-mailjet). If you plan to use other services, follow instructions on their websites to set up SMTP Relay for your XenForo website.

Instructions below are general procedures to set up a mailing service for this tutorial:

1. Sign up with the mailing service you would like to use. Write down the SMTP username and the SMTP password provided by the service.

2. Connect to your Compute Engine instance and change to the directory of postfix preferences:

	```bash
	cd /etc/postfix
	```

3. Edit the preferences:

	```bash
	nano main.cf
	```

	Use arrow keys (UP, DOWN, LEFT and RIGHT keys) to move the cursor around. Comment out the following lines:

	| Before                    | After                     |
	| --------------------------|---------------------------|
	| default_transport = error | #default_transpot = error |
	| relay_transport = error   | #relay_transport = error  |

	Edit the following lines:

	| Before      | After                             |
	| ------------|-----------------------------------|
	| relayhost = | relayhost = [RELAY_SERVER]:[PORT] |

	where the [RELAY_SERVER] and [PORT] are provided by the mailing service. Note that you cannot use common SMTP ports such as 25, 465 or 587. If you are using SendGrid, Mailgun or Mailjet, here are their relay services and ports for Compute Engine instances, as seen in the [Compute Engine documentation](https://cloud.google.com/compute/docs/tutorials/sending-mail/):

	| Mailing Service | Relay Server      | Port |
	| --------------- |-------------------|------|
	| SendGrid        | smtp.sendgrid.net | 2525 |
	| Mailgun         | smtp.mailgun.org  | 2525 |
	| Mailjet         | in.mailjet.com    | 2525 |

	and finally, move to the end of the file and add the following lines:

	```
	smtp_tls_security_level = encrypt
	smtp_sasl_auth_enable = yes
	smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
	smtp_sasl_security_options = noanonymous
	```

4. Generate a new SASL password map and convert it to a .db file:

	```bash
	sudo nano sasl_password
	```

	Enter this line:

	```
	[RELAY_SERVER]:[PORT] [SMTP_USERNAME]:[SMTP_PASSWORD]
	```

	Replace [RELAY_SERVER], [PORT], [SMTP_USERNAME] and [SMTP_PASSWORD] with the values you used or recorded earlier.

	Press Ctrl + O (Control Key and O Key together) to write the file. Then press Ctrl + X (Control Key and X Key together) to exit.

	Convert the file you just created to a .db file, grant proper access permission to it and remove the old file with

	```bash
	sudo postmap sasl_password
	sudo chmod 600 sasl_password.db
	sudo rm sasl_password
	```

5. Lastly, restart the postfix service:

	```bash
	sudo service postfix restart
	```

	And now your XenForo website can use the third-party service you choose to send emails more securely and efficiently.

## Update Your Domain (Optional)

Anyone can now use the external IP of your Compute Engine instance to access your XenForo website. To assign a domain name to this IP address, follow the steps below:

1. Assign a static IP to your Compute Engine instance:

	Currently the external IP you see on the [VM Instances](https://console.cloud.google.com/compute/instances) page changes every time you restart the instance. You need to assign a static IP address to it to make sure that your website is always accessible even if the server restarts. Go to the [External IP addresses](https://console.cloud.google.com/networking/addresses/list) page, and click **Ephemeral** in the row of the Compute Engine instance hosting your XenForo website. In the drop-down menu, choose **Static**. Enter a new name for this static address and click **Reserve**.

	If you have Cloud SDK installed in the system, you can also [use the gcloud command-line to reserve a static IP address](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address).

2. If you haven’t done so, get a domain name from domain name registrars. Follow their instructions to add the IP address you just reserved to your domain. Your website should be accessible with the domain name in a short while.

## Cleaning Up

After you have finished this tutorial, you can clean up the resources you created on Google Cloud Platform so that you will not be billed for them in the future. To clean up, you can delete the whole project or stop the Compute Engine instance.

### Deleting the Project

Go to the [Manage resources](https://console.cloud.google.com/cloud-resource-manager) page. Select the project you used for this tutorial, and click **Delete**. Note that once the project is deleted, the project ID cannot be reused.

If you have Cloud SDK installed in the system, you can also [use the gcloud command-line to delete a project](https://cloud.google.com/sdk/gcloud/reference/projects/delete).

### Stopping the Compute Engine Instance

Go the [VM Instances](https://console.cloud.google.com/compute/instances) page. Select the instance you used for this tutorial, and click **Stop**. If you have reserved a static IP address, it charges you at an hourly rate when the address is not used. To release the address, go to [External IP addresses](https://console.cloud.google.com/networking/addresses/list) page, select the address and click **Release Static Address**. You may also want to go to the Cloud Storage [browser](https://console.cloud.google.com/storage/browser) page and delete the bucket you created during the tutorial.