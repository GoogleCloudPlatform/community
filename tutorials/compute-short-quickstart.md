---
title: Compute Engine quickstart - Create a virtual machine
description: Create a virtual machine instance in Compute Engine.
author: jscud
tags: Compute Engine
date_published: 2019-07-31
---

# Compute Engine quickstart: Create a virtual machine 

<!-- {% setvar project_id "<your-project>" %} -->

<walkthrough-tutorial-duration duration="10"></walkthrough-tutorial-duration>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=compute_short_quickstart)

</walkthrough-alt>

This tutorial explains how to create a virtual machine instance in Compute
Engine using the GCP Console.

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

## Create a virtual machine instance

1.  In the **VM instances** section, click [**Create**][spotlight-create-instance].

1.   Enter a [name][spotlight-instance-name] for this instance.

1.   Choose a region and a [zone][spotlight-instance-zone] for this instance.

1.  In the [**Machine type**][spotlight-machine-type] menu, select **micro**, which specifies a lower-cost
    machine type. ([Learn more about pricing][pricing].)

1.  In the [**Firewall selector**][spotlight-firewall] section, select **Allow HTTP traffic**.
    This opens port 80 (HTTP) to access the app.

1.  Click [**Create**][spotlight-submit-create] to create the instance.

The instances need to finish being created before the tutorial can proceed. To track the progress of this
activity and others, click the [**Notifications**][spotlight-notification-menu] button in the navigation
bar in the upper-right corner of the console.

Note: After the instance is created, your billing account will start being charged
according to the Compute Engine pricing. You will remove the instance later to avoid extra
charges.

## VM instances page

While the instance is being created, take your time to explore the VM instances
page.

At the top is a [control panel][spotlight-control-panel] with controls for doing the following:

- Create a VM instance or instance group.
- Start, stop, reset, and delete instances.

The body of the page contains a [list of your VMs][spotlight-vm-list].

## Set up a web server on the VM instance

After the VM instance is created, you run a web server on the virtual machine.

For this tutorial, you connect using Cloud Shell, which is a built-in command-line tool for the console.

### Open the Cloud Shell

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Connect to the instance

Connect to the VM using SSH:  

```bash
gcloud compute --project "{{project_id}}" ssh --zone [vm-zone] [vm-name]
```

Replace `[vm-zone]` and `[vm-name]` with the zone and name of the instance that you created.

If this is your first time using SSH from Cloud Shell, follow the instructions to create a private key.

It may take several minutes for the SSH key to propagate.

### Run a simple web server

Create a simple `index.html` file:

```bash
echo "Hello, world!" > index.html
```

Start a simple Python webserver:

```bash
sudo python -m SimpleHTTPServer 80
```

### Visit the webserver application

Visit your webserver over an HTTP connection at the [external IP address][spotlight-external-ip] listed
next to the instance in the **VM instances** table. Use a URL in the form `http://[external-ip-address]`.

## Cleanup

To remove your instance, select the [checkbox][spotlight-instance-checkbox]
next to the instance name and click the [**Delete**][spotlight-delete-button] button.

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
[spotlight-create-instance]: walkthrough://spotlight-pointer?spotlightId=gce-zero-new-vm,gce-vm-list-new
[spotlight-instance-name]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-name
[spotlight-instance-zone]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-zone-select
[spotlight-boot-disk]: walkthrough://spotlight-pointer?cssSelector=vm-set-boot-disk
[spotlight-firewall]: walkthrough://spotlight-pointer?spotlightId=gce-vm-add-firewall
[spotlight-vm-list]: walkthrough://spotlight-pointer?cssSelector=.p6n-checkboxed-table
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
