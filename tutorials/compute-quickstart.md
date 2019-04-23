---
title: Compute Engine quickstart - Create a to-do app
description: Use Compute Engine to create a two-tier application.
author: jscud
tags: Compute Engine
date_published: 2019-04-30
---

# Compute Engine quickstart

## Build a to-do app with MongoDB

<walkthrough-tutorial-duration duration="15"></walkthrough-tutorial-duration>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=compute_quickstart)

</walkthrough-alt>

In this quickstart, you'll use Compute Engine to create a two-tier application.
The frontend VM runs a Node.js to-do web app, and the backend VM runs MongoDB.

This tutorial will walk you through the following:

-   Creating and configuring two VMs
-   Setting up firewall rules
-   Using SSH to install packages on your VMs

## Project setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Navigate to Compute Engine

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console and select 
**Compute Engine**.

<walkthrough-menu-navigation sectionId="COMPUTE_SECTION"></walkthrough-menu-navigation>

## Create instances

You will create two instances for the application, one to be backend server and one to be the frontend server.

### Create the backend instance

First, create the backend instance, which runs MongoDB and stores the to-do items:

1.  In the **VM instances** section, click [**Create**][spotlight-create-instance].

1.   Enter a [name][spotlight-instance-name] for this instance.

1.   Choose a region and a [zone][spotlight-instance-zone] for this instance.

1.  In the [**Machine type**][spotlight-machine-type] menu, select **micro**, which specifies a lower-cost
    machine type. ([Learn more about pricing][pricing].)

1.  In the [**Boot disk**][spotlight-boot-disk] section, click **Change** and choose **Google Drawfork Ubuntu 14.04 LTS**.

1.  In the [**Firewall selector**][spotlight-firewall] section, select **Allow HTTP traffic**.
    This opens port 80 (HTTP) to access the app.

1.  Click [**Create**][spotlight-submit-create] to create the instance.

Note: After the instance is created, your billing account will start being charged
according to the Compute Engine pricing. You will remove the instance later to avoid extra
charges.

### Create the frontend instance

While the backend VM is starting, create the frontend instance, which runs the
Node.js to-do application. Use the same configuration as the backend instance.

## Setup

You install a MongoDB database on the backend instance to save your data.

You can click the [**SSH**][spotlight-ssh-buttons] button for each instance in the VM instances table to open an SSH
session to the instance in a separate window.

For this tutorial, you connect using Cloud Shell. Cloud Shell is a built-in command-line tool for the console.

### Open Cloud Shell

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar
in the upper-right corner of the console.

### Wait for the instance creation to finish

The instances need to finish being created before the tutorial can proceed. To track the progress of this activity
and others, click the [**Notifications**][spotlight-notification-menu] button in the navigation bar
in the upper-right corner of the console.

## Set up the backend instance

### Connect to the instance

Enter the following command to connect to the VM:  

```bash
gcloud compute --project "{{project-id}}" ssh --zone [backend-zone] [backend-name]
```

Replace `[backend-zone]` and `[backend-name]` with the zone and name of the instance that you created.

If this is your first time using SSH from Cloud Shell, you need to create a private key.

It may take several minutes for the SSH key to propagate.

### Install the backend database

Use the following commands to update packages and install the backend MongoDB database:

```bash
sudo apt-get update
```

```bash
sudo apt-get install mongodb
```

When asked if you want to continue, type `Y`.

### Run the database

The MongoDB service starts when you install it. You must stop it so that you can change how it runs:

```bash
sudo service mongodb stop
```

Create a directory for MongoDB and then run the MongoDB service in the background on port 80.

```bash
sudo mkdir $HOME/db
```

```bash
sudo mongod --dbpath $HOME/db --port 80 --fork --logpath /var/tmp/mongodb
```

Exit the SSH session using the `exit` command:

```bash
exit
```

## Set up the frontend instance

### Install and run the web app on your frontend VM

The backend server is running, so it is time to install the frontend web
application.

### Connect to the instance

Enter the following command to connect to the VM with SSH. Enter the zone and name of the
instance you created.

```bash
gcloud compute --project "{{project-id}}" ssh --zone <frontend-zone> <frontend-name>
```

### Install the dependencies

Now that you're connected to your frontend instance, update packages and install
git, Node.js and npm. When asked if you want to continue, type `Y`:

```bash
sudo apt-get update
```

```bash
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
```

```bash
sudo apt-get install git nodejs
```

### Install and run the frontend web app

Clone the sample application and install application dependencies.

```bash
git clone https://github.com/GoogleCloudPlatform/todomvc-mongodb.git
```

```bash
cd todomvc-mongodb; npm install
```

```bash
sed -i -e 's/8080/80/g' server.js
```

Start the to-do web application with the following command, entering the
[internal ip addresses][spotlight-internal-ip] for the instances you created.

```bash
sudo nohup nodejs server.js --be_ip <backend-internal-ip> --fe_ip <frontend-internal-ip> &
```

After, exit the SSH session using the `exit` command:

```bash
exit
```

### Visit the application

Visit your webserver at the IP address listed in the
[External IP][spotlight-external-ip] column next to your frontend instance.

## Cleanup

To remove your instances, select the [checkbox][spotlight-instance-checkbox]
next to your instance names and click the
[Delete][spotlight-delete-button] button.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You're done!

Here's what you can do next:

*   Find Google Cloud Platform
    [samples on GitHub](http://googlecloudplatform.github.io/).

*   Learn how to set up
    [Cloud Load Balancing](https://cloud.google.com/compute/docs/load-balancing/).

*   Learn how to
    [transfer files to your virtual machine](https://cloud.google.com/compute/docs/instances/transfer-files/).

*   Learn how to
    [run containers](https://cloud.google.com/compute/docs/containers).

[pricing]: https://cloud.google.com/compute/#compute-engine-pricing
[spotlight-instance-name]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-name
[spotlight-instance-zone]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-zone-select
[spotlight-create-instance]: walkthrough://spotlight-pointer?spotlightId=gce-zero-new-vm,gce-vm-list-new
[spotlight-boot-disk]: walkthrough://spotlight-pointer?cssSelector=vm-set-boot-disk
[spotlight-firewall]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-firewall
[spotlight-vm-list]: walkthrough://spotlight-pointer?cssSelector=vm2-instance-list%20.p6n-checkboxed-table
[spotlight-control-panel]: walkthrough://spotlight-pointer?cssSelector=#p6n-action-bar-container-main
[spotlight-ssh-buttons]: walkthrough://spotlight-pointer?cssSelector=gce-connect-to-instance
[spotlight-notification-menu]: walkthrough://spotlight-pointer?cssSelector=.p6n-notification-dropdown,.cfc-icon-notifications
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
[spotlight-machine-type]: walkthrough://spotlight-pointer?spotlightId=gce-add-machine-type-select
[spotlight-submit-create]: walkthrough://spotlight-pointer?spotlightId=gce-submit
[spotlight-internal-ip]: walkthrough://spotlight-pointer?cssSelector=gce-internal-ip
[spotlight-external-ip]: walkthrough://spotlight-pointer?cssSelector=.p6n-external-link
[spotlight-instance-checkbox]: walkthrough://spotlight-pointer?cssSelector=.p6n-checkbox-form-label
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
