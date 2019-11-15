---
title: Compute Engine quickstart - Create a to-do app with MongoDB
description: Use Compute Engine to create a two-tier web application.
author: jscud
tags: Compute Engine
date_published: 2019-07-31
---

# Compute Engine quickstart: Create a to-do app with MongoDB

<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-tutorial-duration duration="15"></walkthrough-tutorial-duration>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=compute_quickstart)

</walkthrough-alt>

In this quickstart, you'll use Compute Engine to create a two-tier web app.
The frontend VM runs a Node.js to-do web app, and the backend VM runs MongoDB.

This tutorial guides you through the following:

-   Creating and configuring two VMs
-   Setting up firewall rules
-   Using SSH to install packages on your VMs

## Project setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Navigate to Compute Engine

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console, and 
then select **Compute Engine**.

<walkthrough-menu-navigation sectionId="COMPUTE_SECTION"></walkthrough-menu-navigation>

## Create instances

You create two instances for the web app, one to be the backend server and one to be the frontend server.

### Create the backend instance

First, create the backend instance, which runs MongoDB and stores the to-do items:

1.  In the **VM instances** section, click [**Create**][spotlight-create-instance].

1.   Enter a [name][spotlight-instance-name] for this instance.

1.   Choose a region and a [zone][spotlight-instance-zone] for this instance.

1.  In the [**Machine type**][spotlight-machine-type] menu, select **micro**, which specifies a lower-cost
    machine type. ([Learn more about pricing][pricing].)

1.  In the [**Boot disk**][spotlight-boot-disk] section, click **Change**, choose
    **Google Drawfork Ubuntu 14.04 LTS**, and click **Select**.

1.  In the [**Firewall selector**][spotlight-firewall] section, select **Allow HTTP traffic**.
    This opens port 80 (HTTP) to access the app.

1.  Click [**Create**][spotlight-submit-create] to create the instance.

Note: After the instance is created, your billing account will start being charged
according to the Compute Engine pricing. You will remove the instance later to avoid extra
charges.

### Create the frontend instance

While the backend VM is starting, create the frontend instance, which runs the
Node.js to-do app:

1.  In the **VM instances** toolbar, click [**Create Instance**][spotlight-create-instance].

1.  Use the same configuration settings as the backend instance.

1.  Click [**Create**][spotlight-submit-create] to create the instance.

## Opening Cloud Shell

For this tutorial, you connect using Cloud Shell, which is a built-in command-line tool for the console.

### Open Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Wait for the instance creation to finish

The instances need to finish being created before the tutorial can proceed. To track the progress of this activity
and others, click the [**Notifications**][spotlight-notification-menu] button in the navigation bar
in the upper-right corner of the console.

## Set up the backend instance

In this section, you install a MongoDB database on the backend instance to save your data.

### Connect to the instance

Connect to the VM using SSH:  

```bash
gcloud compute --project "{{project_id}}" ssh --zone [backend-zone] [backend-name]
```

Replace `[backend-zone]` and `[backend-name]` with the zone and name of the instance that you created.

If this is your first time using SSH from Cloud Shell, follow the instructions to create a private key.

It may take several minutes for the SSH key to propagate.

### Install the backend database

Update packages:

```bash
sudo apt-get update
```

Install the backend MongoDB database:

```bash
sudo apt-get install mongodb
```

When asked if you want to continue, enter `Y`.

### Run the database

The MongoDB service starts when you install it. You must stop it so that you can change how it runs:

```bash
sudo service mongodb stop
```

Create a directory for MongoDB:

```bash
sudo mkdir $HOME/db
```

Run the MongoDB service in the background on port 80:

```bash
sudo mongod --dbpath $HOME/db --port 80 --fork --logpath /var/tmp/mongodb
```

Exit the SSH session and disconnect from the backend instance:

```bash
exit
```

## Set up the frontend instance

In this section, you install the dependencies for the web app and then install and run the frontend web app.

### Connect to the instance

Connect to the VM with SSH:

```bash
gcloud compute --project "{{project_id}}" ssh --zone [frontend-zone] [frontend-name]
```

Replace `[frontend-zone]` and `[frontend-name]` with the zone and name of the instance that you created.

### Install the dependencies

Update packages:

```bash
sudo apt-get update
```

Install `git` and `npm`:

```bash
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
```

Install Node.js:

```bash
sudo apt-get install git nodejs
```

When asked if you want to continue, enter `Y`.

### Install and run the frontend web app

Clone the sample app:

```bash
git clone https://github.com/GoogleCloudPlatform/todomvc-mongodb.git
```

Install the app dependencies:

```bash
cd todomvc-mongodb; npm install
```

```bash
sed -i -e 's/8080/80/g' server.js
```

Start the to-do web app:

```bash
sudo nohup nodejs server.js --be_ip [backend-internal-ip] --fe_ip [frontend-internal-ip] &
```

Replace `[backend-internal-ip]` and `[frontend-internal-ip]` with the
internal IP addresses for the instances that you created.
These IP addresses are listed for each instance in the **VM instances** table.

Exit the SSH session and disconnect from the frontend instance:

```bash
exit
```

### Visit the web app

Visit your webserver over an HTTP connection at the [external IP address][spotlight-external-ip] listed
next to the frontend instance in the **VM instances** table. Use a URL in the form `http://[external-ip-address]`.

## Cleanup

To remove your instances, select the [checkbox][spotlight-instance-checkbox]
next to the instance names and click the [**Delete**][spotlight-delete-button] button.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You're done!

Here are some suggestions for what you can do next:

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
[spotlight-external-ip]: walkthrough://spotlight-pointer?cssSelector=.p6n-external-link
[spotlight-instance-checkbox]: walkthrough://spotlight-pointer?cssSelector=.p6n-checkbox-form-label
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
