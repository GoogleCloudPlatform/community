---
title: Compute Engine Quickstart - Linux VM
description: Create a Linux virtual machine in Compute Engine.
author: jscud
tags: Compute Engine
date_published: 2019-04-12
---

# Compute Engine Quickstart

<walkthrough-tutorial-url url="https://cloud.google.com/compute/docs/quickstart-linux"></walkthrough-tutorial-url>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=compute_short_quickstart)

</walkthrough-alt>

## Introduction

<walkthrough-tutorial-duration duration="10"></walkthrough-tutorial-duration>

This tutorial explains how to create a Linux virtual machine instance in Compute
Engine using the Google Cloud Platform Console.

## Project setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Navigate to Compute Engine

Open the [menu][spotlight-console-menu] on the left side of the console.

Then, select the **Compute Engine** section.

<walkthrough-menu-navigation sectionId="COMPUTE_SECTION"></walkthrough-menu-navigation>

## Create a virtual machine instance

Click the [Create instance][spotlight-create-instance] button.

*   Select a [name][spotlight-instance-name] and [zone][spotlight-instance-zone]
    for this instance.

*   In the [Firewall selector][spotlight-firewall], select **Allow HTTP
    traffic**. This opens port 80 (HTTP) to access the app.

*   Click the [Create][spotlight-submit-create] button to create the instance.

Note: Once the instance is created your billing account will start being charged
according to the GCE pricing. You will remove the instance later to avoid extra
charges.

## VM instances page

While the instance is being created take your time to explore the VM instances
page.

*   At the bottom you can see the [list of your VMs][spotlight-vm-list]
*   At the top you can see a [control panel][spotlight-control-panel] allowing
    you to
    *   Create a new VM instance or an instance group
    *   Start, stop, reset and delete instances

## Connect to your instance

When the VM instance is created, you'll run a web server on the virtual machine.

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

The instance creation needs to finish before the tutorial can proceed. The
activity can be tracked by clicking the
[notification menu][spotlight-notification-menu] from the navigation bar at the
top.

### Connect to the instance

Enter the following command to SSH into the VM. If this is your first time using
SSH from Cloud Shell, you will need to create a private key. Enter the zone and
name of the instance you created.

```bash
gcloud compute --project "{{project-id}}" ssh --zone <vm-zone> <vm-name>
```

It may take several minutes for the SSH key to propagate.

### Run a simple web server

Create a simple index.html file with the following command:

```bash
echo "<h1>Hello World</h1>" > index.html
```

Then, enter this command to run a simple Python webserver:

```bash
sudo python -m SimpleHTTPServer 80
```

### Visit your application

Visit your webserver at the IP address listed in the
[External IP][spotlight-external-ip] column.

## Cleanup

To remove your instance, select the [checkbox][spotlight-instance-checkbox] next
to your instance name and click the [Delete button][spotlight-delete-button].

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
