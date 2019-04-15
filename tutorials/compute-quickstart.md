---
title: Compute Engine Quickstart - To-Do App
description: Use Compute Engine to create a two-tier application.
author: jscud
tags: Compute Engine
date_published: 2019-04-12
---

# Compute Engine Quickstart

## Build a to-do app with MongoDB

<walkthrough-tutorial-duration duration="15"></walkthrough-tutorial-duration>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=compute_quickstart)

</walkthrough-alt>

In this quickstart, you'll use Compute Engine to create a two-tier application.
The frontend VM runs a Node.js to-do web app, and the backend VM runs MongoDB.

This tutorial will walk you through:

-   Creating and configuring two VMs
-   Setting up firewall rules
-   Using SSH to install packages on your VMs

## Project setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Navigate to Compute Engine

Open the [menu][spotlight-console-menu] on the left side of the console.

Then, select the **Compute Engine** section.

<walkthrough-menu-navigation sectionId="COMPUTE_SECTION"></walkthrough-menu-navigation>

## Create instances

You will create 2 instances to be backend and frontend servers for the
application.

### Create the backend instance

First, create the backend instance that runs MongoDB. This server stores the
to-do items.

Click the [Create instance][spotlight-create-instance] button.

*   Select a [name][spotlight-instance-name] and [zone][spotlight-instance-zone]
    for this instance.

*   Select [f1-micro][spotlight-machine-type]. This will incur fewer charges.

    *   [Learn more about pricing][pricing]

*   Select [Ubuntu 14.04 LTS][spotlight-boot-disk] as your boot disk image for
    this tutorial.

*   In the [Firewall selector][spotlight-firewall], select **Allow HTTP
    traffic**. This opens port 80 (HTTP) to access the app.

*   Click the [Create][spotlight-submit-create] button to create the instance.

Note: Once the instance is created your billing account will start being charged
according to the GCE pricing. You will remove the instance later to avoid extra
charges.

### Create the frontend instance

While the backend VM is spinning up, create the frontend instance that runs the
Node.js to-do application. Use the same configuration as the backend instance.

## Setup

You'll install a MongoDB database on the backend instance to save your data.

The [SSH buttons][spotlight-ssh-buttons] in the table will open up an SSH
session to your instance in a separate window.

For this tutorial you will connect using Cloud Shell. Cloud Shell is a built-in
command line tool for the console.

### Open the Cloud Shell

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar
in the upper-right corner of the console.

### Wait for the instance creation to finish

The instances need to finish creating before the tutorial can proceed. The
activity can be tracked by clicking the
[notification menu][spotlight-notification-menu] from the navigation bar at the
top.

## Connect to your backend instance

### Connect to the instance

Enter the following command to SSH into the VM. If this is your first time using
SSH from Cloud Shell, you will need to create a private key. Enter the zone and
name of the instance you created.

```bash
gcloud compute --project "{{project-id}}" ssh --zone <backend-zone> <backend-name>
```

It may take several minutes for the SSH key to propagate.

### Install the backend database

Now that you have an SSH connection to the backend instance, use the following
commands to install the backend database:

Update packages and install MongoDB. When asked if you want to continue, type
`Y`:

```bash
sudo apt-get update
```

```bash
sudo apt-get install mongodb
```

### Run the database

The MongoDB service started when you installed it. You must stop it so you can
change how it runs.

```bash
sudo service mongodb stop
```

Create a directory for MongoDB and then run the MongoDB service in the
background on port 80.

```bash
sudo mkdir $HOME/db
```

```bash
sudo mongod --dbpath $HOME/db --port 80 --fork --logpath /var/tmp/mongodb
```

After, exit the SSH session using the `exit` command:

```bash
exit
```

## Connect to your frontend instance

### Install and run the web app on your frontend VM

The backend server is running, so it is time to install the frontend web
application.

### Connect to the instance

Enter the following command to SSH into the VM. Enter the zone and name of the
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

### Visit your application

Visit your webserver at the IP address listed in the
[External IP][spotlight-external-ip] column next to your frontend instance.

## Cleanup

To remove your instances, select the [checkbox][spotlight-instance-checkbox]
next to your instance names and click the
[Delete button][spotlight-delete-button].

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You're done!

Here's what you can do next:

*   Find Google Cloud Platform
    [samples on GitHub](http://googlecloudplatform.github.io/).

*   Learn how to set up
    [Load Balancing](https://cloud.google.com/compute/docs/load-balancing/).

*   Learn how to
    [transfer files to your Virtual Machine](https://cloud.google.com/compute/docs/instances/transfer-files/).

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
