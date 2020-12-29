---
title: Deploy a production-ready MEAN application using Bitnami MongoDB with Replication on Google Cloud
description: Deploy a MEAN application with a multi-node MongoDB replica set on Google Cloud using Bitnami MEAN and Bitnami MongoDB with Replication.
author: vikram-bitnami
tags: mean, mongodb, replication, scalability, bitnami
date_published: 2017-07-06
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

This tutorial demonstrates how to deploy a MEAN (MongoDB, Express, Angular and Node) Web application with a multi-node MongoDB replica set on Google Cloud using Bitnami MEAN and Bitnami MongoDB with Replication. This approach produces a more scalable and resilient deployment that could be used for production or mission-critical scenarios. This tutorial assumes that you're familiar with MongoDB and MEAN applications.

## Objectives

* Deploy Bitnami MEAN on a Compute Engine instance.
* Install and configure a sample MEAN application.
* Serve the application with Apache.
* Deploy Bitnami MongoDB with Replication on a set of Compute Engine instances.
* Connect the MEAN application to the Bitnami MongoDB with Replication cluster.
* Test service continuity (optional)

## Before you begin

Before starting this tutorial, ensure that you have set up a Google Cloud project. You can use an existing project or [create a new project](https://console.cloud.google.com/project).

## Cost

The default configuration allows you to run a MEAN application using 1 `f1-micro` instance with a standard 10 GB persistent disk for the application server, and 3 `n1-standard-2` instances, each with a standard 10 GB persistent disk, for the MongoDB cluster. You can customize the configuration when deploying this solution or change it later, although the default configuration is fine for the purposes of this tutorial.

Estimated cost for the above default configuration is $4.28 per month for the single `f1-micro` instance and $148.04 per month for the three `n1-standard-2` instances comprising the Bitnami MongoDB with Replication cluster, based on 30-day, 24 hours per day usage in the `us-central1` (Iowa) region. Sustained use discount is included.

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to generate a cost estimate based on your projected usage. New Google Cloud customers may be eligible for a [free trial](https://cloud.google.com/free-trial).

## Deploy Bitnami MEAN on a Compute Engine instance

Deploy Bitnami MEAN on a Compute Engine instance:

1. From the [Cloud Marketplace](https://console.cloud.google.com/marketplace), select the [**MEAN Certified by Bitnami**](https://console.cloud.google.com/marketplace/details/bitnami-launchpad/meanstack) template.
1. Review the information and cost. Click **Launch on Compute Engine** to proceed.
1. Review the default zone, machine type, boot disk size and other parameters and modify as needed. Ensure that the **Allow HTTP traffic** and **Allow HTTPS traffic** boxes are checked in the firewall configuration. Click **Deploy** to proceed with the deployment.

The Cloud Marketplace deploys Bitnami MEAN on a new Compute Engine instance. You can monitor the progress of the deployment from the [Deployment Manager](https://console.cloud.google.com/dm/deployments). Once deployed, note the public IP address of the instance and the password for the MongoDB database.

## Install and configure a sample MEAN application

This section uses a [sample MEAN application from GitHub](https://github.com/cornflourblue/mean-stack-registration-login-example). If you already have a MEAN application to deploy, you can use it instead; simply adapt the installation and configuration steps below as needed.

Login to the deployed instance and install and configure the MEAN application:

1. From the [Deployment Manager](https://console.cloud.google.com/dm/deployments), click the **SSH** button to login to the instance over SSH.
1. Once logged in, switch to the `bitnami` user account:

        sudo su - bitnami

1. Navigate to the default application folder:

        cd /opt/bitnami/apps/

1. Create the folder structure for the MEAN application:

        sudo mkdir myapp
        sudo mkdir myapp/conf
        sudo mkdir myapp/htdocs

1. Download the application source code into the `myapp/htdocs` folder:

        cd myapp/htdocs
        sudo git clone https://github.com/cornflourblue/mean-stack-registration-login-example.git .

1. Install the necessary application dependencies:

        sudo npm install

1. Login to the MongoDB database using the `mongo` command-line client. Use the password obtained from the [Deployment Manager](https://console.cloud.google.com/dm/deployments) when prompted.

        mongo admin --username root -p

1. Once logged in, create a new database and user account for the application:

        use mydb
        db.createUser(
           {
             user: "myuser",
             pwd: "mypass",
             roles: [ "readWrite" ]
           }
        )
        exit

1. Modify the application configuration to use the new database and credentials by modifying the `/opt/bitnami/apps/myapp/htdocs/config.json` file as shown below:

        {
            "connectionString": "mongodb://myuser:mypass@localhost:27017/mydb",
            ...
        }

## Serve the application with Apache

Express will typically serve the MEAN application on port 3000. This port is closed by default in Bitnami MEAN for security reasons. However, Bitnami MEAN also includes the Apache Web server, which can be configured as a reverse proxy for Express on the standard Web server port 80.

Configure Apache to work as a reverse proxy for Express and accept requests for the MEAN application on port 80:

1. Create the `/opt/bitnami/apps/myapp/conf/httpd-prefix.conf` file and add the line below to it:

        Include "/opt/bitnami/apps/myapp/conf/httpd-app.conf"

1. Create the `/opt/bitnami/apps/myapp/conf/httpd-app.conf` file and add the content below to it to enable the reverse proxy:

        ProxyPass / http://127.0.0.1:3000/
        ProxyPassReverse / http://127.0.0.1:3000/

1. Add the following line to the end of the main Apache configuration file at `/opt/bitnami/apache2/conf/bitnami/bitnami-apps-prefix.conf`:

        Include "/opt/bitnami/apps/myapp/conf/httpd-prefix.conf"

1. Restart the Apache server using the Bitnami control script:

        sudo /opt/bitnami/ctlscript.sh restart apache

1. Start the Express server:

        cd /opt/bitnami/apps/myapp/htdocs
        forever start server.js

Browse to the public IP address of your Bitnami MEAN instance and confirm that you see the MEAN example application's welcome page. Register a new user account in the example application using the **Register** link and then log in to the example application by entering the new user account credentials into the login form and clicking the **Login** button.

If you are able to perform the above tasks, your MEAN application is now operational, albeit using the locally-installed MongoDB database instance. The remaining sections of this tutorial will show you how to deploy a separate Bitnami MongoDB with Replication cluster and reconfigure the MEAN application to use that cluster instead.

## Deploy Bitnami MongoDB with Replication on a set of Compute Engine instances

Deploy Bitnami MEAN on a Compute Engine instance:

1. From the [Cloud Marketplace](https://console.cloud.google.com/marketplace), select the [**MongoDB with Replication**](https://console.cloud.google.com/marketplace/details/bitnami-launchpad/mongodb-multivm) template.
1. Review the information and cost. Click **Launch on Compute Engine** to proceed.
1. Review the default zone, number of nodes and arbiters, machine type, boot disk size and other parameters and modify as needed. Ensure that the **Allow HTTP traffic** and **Allow HTTPS traffic** boxes are checked in the firewall configuration and that the default zone matches the zone for the Bitnami MEAN instance. Click **Deploy** to proceed with the deployment.

The Cloud Marketplace deploys Bitnami MEAN on multiple Compute Engine instances. You can monitor the progress of the deployment from the [Deployment Manager](https://console.cloud.google.com/dm/deployments). Once deployed, note the password for the MongoDB database. Then, click the **Manage** link for each instance in the Deployment Manager and note its internal IP address from the corresponding instance detail page.

## Connect the MEAN application to the Bitnami MongoDB with Replication cluster

Before proceeding, confirm that the Bitnami MEAN instance and the Bitnami MongoDB with Replication cluster instances are on the same VPC network. You can check this by visiting each instance's detail page from the [Deployment Manager](https://console.cloud.google.com/dm/deployments) and viewing the network name in the **Network interfaces** section. If the Bitnami MEAN instance and the Bitnami MongoDB with Replication cluster instances are not on the same network, [configure VPC peering between the two networks](https://cloud.google.com/vpc/docs/vpc-peering) before proceeding.

Reconfigure the MEAN application to use the Bitnami MongoDB with Replication cluster:

1. From the Bitnami MEAN instance, login to the Bitnami MongoDB with Replication cluster using the `mongo` command-line client. Use the internal IP address of the primary MongoDB node as the host IP address and enter the password obtained from the [Deployment Manager](https://console.cloud.google.com/dm/deployments) when prompted.

        mongo --host XX.XX.XX.XX admin --username root -p

1. Once logged in, create a new database and user account for the application:

        use mydb
        db.createUser(
           {
             user: "myuser",
             pwd: "mypass",
             roles: [ "readWrite" ]
           }
        )
        exit

1. Modify the application configuration to use the new Bitnami MongoDB with Replication cluster and credentials by modifying the `/opt/bitnami/apps/myapp/htdocs/config.json` file as shown below. Replace the `XX`, `YY` and `ZZ` placeholders with the internal IP addresses of all the nodes in the Bitnami MongoDB with Replication cluster, starting with the primary node.

        {
            "connectionString": "mongodb://myuser:mypass@XX.XX.XX.XX:27017,YY.YY.YY.YY:27017,ZZ.ZZ.ZZ.ZZ:27017/mydb?replicaSet=rs0",
            ...
        }

1. Restart the Express server:

        cd /opt/bitnami/apps/myapp/htdocs
        forever restart server.js

Browse to the public IP address of your Bitnami MEAN instance and confirm that it is working as expected. Note that since the MEAN application is now connected to a different MongoDB database, it is necessary to re-register a user account before logging in to the example application.

## Test service continuity (optional)

In the Bitnami MongoDB with Replication template, one node in the cluster is designated as the primary node and receives all write operations, while other nodes are designated as secondary nodes which hold their own copies of the data set. If the primary node fails, the secondary nodes and arbiters elect a new primary automatically to ensure that writes continue without interruption. This provides redundancy and ensures minimal downtime for your application.

Test service continuity for the MEAN application:

1. From the [Deployment Manager](https://console.cloud.google.com/dm/deployments), select the Bitnami MongoDB with Replication deployment.
1. From the list of instances in the deployment, select the primary instance and click the **Manage** button to be redirected to the instance detail page.
1. Click the **Stop** button to stop the instance. Wait a few minutes for the instance to stop.

When the primary node stops, a new primary node is automatically elected from amongst the secondary nodes to ensure continuity of service. To verify this, browse to the public IP address of your Bitnami MEAN instance and confirm that you are still able to log in using the previously-registered user account as well as register a new user account.

If you are able to perform the above tasks, your MEAN application is now operational and configured to use the  MongoDB replica set.

## Cleaning up

After you have finished this tutorial, you can remove the resources you created on Google Cloud so you aren't billed for them any longer. You can delete the resources individually, or delete the entire project.

### Deleting the project

Visit the [Resource Manager](https://console.cloud.google.com/cloud-resource-manager). Select the project you used for this tutorial and click **Delete**. Once deleted, you cannot reuse the project ID.

### Deleting individual resources

Navigate to the [Deployment Manager](https://console.cloud.google.com/dm/deployments). Select the deployments you used for this tutorial and click **Delete**.

## Next steps

Learn more about the topics discussed in this tutorial:

* [Bitnami MEAN documentation](https://docs.bitnami.com/google/infrastructure/mean/)
* [Bitnami MongoDB with Replication documentation](https://docs.bitnami.com/google-templates/infrastructure/mongodb/)
* [MongoDB replication documentation](https://docs.mongodb.com/manual/replication/)
