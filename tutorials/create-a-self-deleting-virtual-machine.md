---
title: Create a self-deleting virtual machine on Compute Engine
description: Learn how to launch a Compute Engine VM that will delete itself after a set duration, ensuring that costly resources are not left running.
author: engelke,lauriewhite
tags: Compute Engine, self-deleting, education, cost control
date_published: 2019-05-15
---

Charlie Engelke and Laurie White | Developer Program Engineers | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Learning to use Google Cloud is best done hands-on, by actually
creating, using, and removing resources. However, a common problem with doing
this is that learners may forget to clean up their resources when finished
trying something, resulting in continuing running resources, often at a cost.

This tutorial shows how to create Compute Engine instances (virtual machines)
that will automatically delete themselves after a set time, ensuring that
those resources will not remain and incur charges indefinitely, even
if the learner forgets to clean them up. A variation is also shown that
will simply stop the instances after a set time, after which they can
be restarted—and again automatically stop after the set time. Be aware
that stopped instances, unlike deleted instances, still incur some charges
(see [Compute Engine pricing](https://cloud.google.com/compute/pricing)
for details).

The use of self-deleting virtual machines is particularly useful in class
settings.

## Objectives

Learn how to create Compute Engine instances that will delete themselves after
a set period of time. You will see two ways to do this:

* Using the Cloud Console
* Using the `gcloud` command-line tool

## Before you begin

Create a Google Cloud project in a web browser:

1.  Open your web browser to the [Cloud Console](https://console.cloud.google.com/).
1.  Sign in with a Google or G Suite account. If you don't have an account, you can
    create one by clicking **Create account**.
1.  Click **Select a project** at the top of the page, and then click **New Project**.
1.  Enter a name for your project, and note the project ID shown under the
    **Project name** field.
1.  Select a location. 
1.  Click **Create**.

    A notification appears, saying that the project is being created.
    
    If you are prompted to enter billing information, follow the instructions
    for doing so.
   
1.  When the notification says that the project is ready, click the notification
    or select the project from the project selector menu to open the project.

Use this new project in the tutorial below so that you don't inadvertently
affect your other projects, if you have any.

## Costs

In this tutorial, you create a Compute Engine instance. That instance
incurs charges as long as it exists, as listed in the
[Compute Engine pricing](https://cloud.google.com/compute/pricing). Your 
account can use one micro instance (the kind created in this tutorial)
as part of the [Free Tier](https://cloud.google.com/free), which incurs no costs.

## Creating the startup script

The self-deleting instance works by automatically executing a startup script that
waits a set amount of time and then issues a
[`gcloud`](https://cloud.google.com/sdk/gcloud/) command to delete itself. This
script needs to be provided in a file or at an available URL when launching the
instance.

1.  Open a text editor and enter the following text:

        #!/bin/sh
        sleep 3600s
        export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
        export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
        gcloud --quiet compute instances delete $NAME --zone=$ZONE

1.  Save the file as `startup.sh`.

When you start a new instance and specify that it should automatically run
this script, it will do nothing for one hour (the `3600s` value on the second
line), then look up information about the running instance and put it in shell
variables (the third and fourth lines), and finally run a `gcloud` command to
delete itself.

You can use this file as is to make your instances delete themselves after
one hour (3600 seconds), or you can customize it to your exact needs:

* You can modify the script to stop the instance rather than deleting it. To
make this change, replace `delete` in the `gcloud` command with `stop`.

* You can change the duration before self-deletion by replacing `3600s` with a
different value. A number, or a number followed by an `s`, stands for that number
of seconds. You can specify a duration in minutes, hours, or days, by using
the suffix `m`, `h`, or `d` in place of `s`.

* Instead of the instance deleting itself after a given duration, you can have
the instance install and configure a program to run, and then delete itself
when that program completes. Replace the `sleep 3600s` line with one or more
commands to install, configure, and run the program you want.

Every standard Linux option in Compute Engine includes the `gcloud` command-line
tool.

### How the startup script works

This section explains how the file created in the previous section works. You can
skip this section if you just want to create self-deleting instances.

Every Linux OS image available by default in Compute Engine is configured to run
a program when the operating system starts, if you specify such a program. The
`startup.sh` file created in the previous section is such a program.

**Note**: Default Windows instances have a similar capability, but there are some
important differences in exactly how it works. The ideas in this tutorial can be
adapted to work with Windows instances.

The startup script that you created in the previous section does nothing but wait
for an hour and then issue a command to delete the instance that runs the script.

Let's look at an explanation of what each line in `startup.sh` does:

**Invoking the Bourne shell**

    #!/bin/sh
    
If the first two characters in the file are `#!`, as they are here, the
Linux environment will run the program named, providing the file as its
input. So, Linux will invoke `/bin/sh`, the 
[Bourne shell](https://en.wikipedia.org/wiki/Bourne_shell),
to run this file. You may be familiar with 
[Bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)) in the terminal
window for Linux and Mac machines. The Bourne shell is an earlier, similar
program for running commands.

**Waiting for an hour**

    sleep 3600s

This line runs the `sleep` program, which does nothing but wait the
specified time before it exits, which introduces a delay of an hour
(3600 seconds) before the next commands are run.

**Setting shell variables to specify the instance**

    export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')

Each of these lines sets the value of a shell variable (`NAME` and `ZONE`). 
These variables are used in a later command. The `$(command)` portion runs the
command in the parentheses and returns the output of that command as its value.
The commands here are each [`curl`](https://curl.haxx.se/) commands that make
web requests and output the responses to the requests.

Compute Engine instances have access to a *metadata service* that looks like a
web site. Any web request made to that apparent site
(http://metadata.google.internal) will fetch some information about the
instance itself. There is no actual network traffic involved, though; the Google Cloud
infrastructure handles the requests and responses internally. That's one of the
reasons that it is safe for the URL to start with `http` instead of `https`: 
because there is no actual network activity, there is no need for a secure network
connection.

These two metadata requests discover the running instance's name and zone,
which are required for the last line of the program.

**Deleting the instance**

    gcloud --quiet compute instances delete $NAME --zone=$ZONE

This last line runs the `gcloud` command. The `--quiet` option indicates that the command
should not ask for user confirmation of an action, because it runs in batch mode with
no user available. The `compute instances` command group performs operations on
Compute Engine instances. The `delete` command completely removes an instance.
The instance `NAME` and `ZONE` variables in the command specify which instance to
delete. You can replace `delete` with `stop` to stop the instance so that it can be
restarted later.

## Using the console to create a self-deleting instance

This section gives the steps to create a self-deleting instance by using the
Cloud Console in your web browser. If you prefer to use the command line
instead, see the next section.

1.  Open the [Cloud Console](https://console.cloud.google.com/) and select your
    project, if it is not already selected.

1.  Click the **Navigation menu** in the upper-left corner of the console, and 
    then select **Compute Engine** > **VM instances**. 

1.  On the **VM instances** page, click **Create Instance**.

1.  If you are prompted to enable the **Compute Engine API**, click **Enable**.

    When you are redirected to the **VM Instances** page, click **Create Instance**.

1.  In the **New VM instance** form, leave most values at the default values,
    but change the following values:
      - **Name**: Fill in any name (for example, `myinstance`).
      - **Region** and **Zone**: Select a location near you.
      - **Access Scopes** (in the **Identity and API access** section): Select
        **Set access for each API**, and then choose **Read Write** from the 
        **Compute Engine** menu in this section.

1.  Click **Management, security, disks, networking, sole tenancy** at the bottom
    of the form to open more sections of the form.

1.  Copy the startup script from the "Preparation" section in this tutorial, and 
    paste the script into the **Startup script** field in the **Automation**
    section of the form.
   
    For testing purposes you may want to change the sleep duration from `3600s`
    to only `300s`.

1.  Click **Create**.

In the list of your VM instances, a spinning icon next to your new instance
indicates that it is starting. When the instance is ready, the spinner 
changes to a green icon with a check mark.

Wait the duration that you specified in the script. The instance that you created
should disappear from the list. The list is automatically updated periodically;
you can click the **Refresh** button to update the list at any time.

## Using the command line to create a self-deleting instance

This section gives the steps to create a self-deleting instance by using the
command line on your local computer. If you prefer to use the web console
instead, see the previous section, "Using the console".

1.  Install the [Cloud SDK](https://cloud.google.com/sdk/).

1.  Log in to your Google Cloud account:

        gcloud auth login

1.  Select the project you want to work in:

        gcloud init

1.  Create a self-deleting virtual machine:

        gcloud compute instances create myinstance \
        --metadata-from-file=startup-script=startup.sh \
        --scopes=compute-rw

    Replace `myinstance` in this command with your instance name.
    
    This command uses the `startup.sh` file that you created in the
    "Preparation" section early in this tutorial.
    
    For an explanation of the other options in this command, see the 
    "Options" section below.
    
1.  You may be prompted to allow the SDK to create the needed API if you
    haven't used it before. Go ahead and answer `Y` for yes if needed.

1.  You will be asked to select a region for your instance to run in. Select
    one in a location that is convenient for you and your users.

In a few minutes, you should see a confirmation that the instance has been
created successfully:

    Created [https://www.googleapis.com/compute/v1/projects/myproject/zones/us-central1-a/instances/myinstance].
    NAME        ZONE           MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
    myinstance  us-central1-a  n1-standard-1               10.128.0.2   35.239.136.206  RUNNING

You can check on your running instances at any time with this command:

    gcloud compute instances list

Wait until the specified sleep time has expired, and run that command again. The
instance should be gone.
    
### Options

The `--metadata-from-file=startup-script=startup.sh` option specifies
that the new instance's metadata-server should provide the contents
of the `startup.sh` file as the value of `startup-script` when the
instance requests it. For standard Compute Engine instances,
that will cause the instance to run that script when it starts.

The `--scopes=compute-rw` option specifies that the instance should have
permission to use all Compute Engine APIs, including the API to delete an
instance. By default, new instances do *not* have that privilege, so it
needs to be added here so it can delete itself.

## Cleaning up

If everything went as planned, the only resource you created, the new
instance, cleaned itself up. If you no longer need the project you created
for trying this out, you can delete it, too, eliminating every resource
in it.

1. Click the **Navigation menu** in the upper-left corner of the console, and 
then select **Home**. 

1. In the **Project info** box, click **Go to project settings**.

1. Click **Shut down**.

1. To confirm project deletion, enter the project ID.

1. Click **Shut down** below the project ID you entered. The project
will be shut down and will be deleted in 30 days.
