---
title: Create a Self-Deleting Virtual Machine
description: Learn how to launch a Compute Engine VM that will delete itself after a set duration, insuring that costly resources are not left running.
author: engelke
tags: Compute Engine, self-deleting, education, cost control
date_published: 2019-04-30
---
# Create a Self-Deleting Virtual Machine on Google Compute Engine

Learning to use Google Cloud is best done hands-on, by actually creating, using,
and removing resources. But a common problem with doing this is that learners may
forget to clean up their resources when finished trying something, resulting
in continuing running resources, often at a cost.

This tutorial shows how to create Compute Engine instances (virtual machines)
that will automatically delete themselves after a set time, insuring that
those resources will not remain and incur charges indefinitely even
if the learner forgets to clean them up. This will be particularly useful
in class settings.

## Objectives

Learn how to create Cloud Engine instances that will delete themselves after
a set period of time. You will see two ways to do this.

* Using the cloud console
* Using the `gcloud` CLI tool

## Before you begin

Create a Google Cloud Platform project in a web browser.

1. Open your web browser to the [Google Cloud Console](https://console.cloud.google.com/).
1. Sign in with a Google or GSuite account. You can create an account by clicking _Create account_
if you don't already have one.
1. Click the _Select a project_ drop-down at the top of the page and then
click **NEW PROJECT**.
1. Enter a name for your project, and note the _Project ID_ shown under
the name.
1. Click **CREATE**. A notification will pop up saying that the project is
being created.
1. Once the notification says the project is ready, click on the notification
or select the project from the _Select a project_ drop down to open it
in the console.

Use this new project in the tutorial below so that you don't inadvertently
affect your other projects, if you have any.

## Costs

This tutorial has you create a Compute Engine instance. That instance
will incur charges as long as it exists, as listed in [Google Compute
Engine Pricing](https://cloud.google.com/compute/pricing). Your 
account can use one free micro instance (the kind created in this
tutorial) as part of the [Free Tier](https://cloud.google.com/free),
in which case you will incur no costs.

## Preparation

The way the self-deleting instance works is by automatically executing a
startup script that waits a set amount of time and then issues a
[gcloud](https://cloud.google.com/sdk/gcloud/)
command to delete itself. This script needs to be provided in a file or
at an available URL when launching the instance.

1. Open a text editor and enter the following text:
```
    #!/bin/sh
    sleep 3600s
    export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
    gcloud --quiet compute instances delete $NAME --zone=$ZONE
```

2. Save the file as `startup.sh`.

When you start a new instance and specify that it should automatically run
this script, it will do nothing for one hour (the `3600s` value on the second
line), then look up information about the running instance and put it in shell
variables (the third and fourth lines), and finally run a `gcloud` command to
delete itself.

You can use this file as is to make your instances delete themselves after
one hour (3600 seconds), or you can customize it to your exact needs:

* Change the duration before self-deletion by replacing `3600s` with a different
value. A number, or a number followed by an `s`, stands for that number
of seconds. You can specify a duration in minutes, hours, or days, by using
the suffix `m`, `h`, or `d` in place of `s`.

* Instead of the instance deleting itself after a given duration, you can have
the instance install and configure a program to run, and then delete itself
when that program completes. Replace the `sleep 3600s` line with one or more
commands to install, configure, and run the program you want.

## Explanation

This section explains how the file shown above works. You can safely skip
this if you just want to create self-deleting instances.

Every Linux OS image available by default in Google Compute Engine is
configured to run a program when it first boots, if you specify such a program.
The `startup.sh` file in the previous section is such a program. When you
create an image with that option it will run the `startup.sh` program when
it launches. In this case, that program does nothing but wait for an hour
and then issue a command to delete the instance that runs it.

_Default Windows instances have a similar capability, but there are some
important differences in exactly how it works. The ideas in this tutorial
can be adapted to work with Windows instances by an experienced Windows
programmer._

Here is an explanation of what each line in `startup.sh` does:

    #!/bin/sh
    
If the first two characters in the file are `#!`, as they are here, the
Linux environment will run the program named, providing the file as its
input. So Linux will invoke `/bin/sh`, the 
[Bourne shell](https://en.wikipedia.org/wiki/Bourne_shell),
to run this file. You may be familiar with 
[Bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)) in the terminal
window for Linux and Mac machines. The Bourne shell is an earlier, similar
program for running commands.

    sleep 3600s

This line runs the `sleep` program, which does nothing at all except wait
the specified time before it exits. That prevents the following commands from
running for an hour (3600 seconds).

    export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')

These two lines may seem a bit cryptic. Each one of them sets the value of a
shell variable (called _NAME_ and _ZONE_). Those variables will be used in a later
command. The `$(command)` portion runs the _command_ in the parentheses and
returns the output of that command as its value. The commands here are each
[curl](https://curl.haxx.se/) commands that make web requests and output the
response to the requests.

This is the trickiest part of the `startup.sh` program. Compute Engine instances
have access to a *metadata service* that looks like a web site. Any web request
made against that apparent site (http://metadata.google.com.internal) will fetch
some information about the instance itself. There is no actual network traffic
involved, though; the Google Cloud infrastructure handles the requests and
responses internally. That's one of the reasons that it is safe for the URL
to start with `http` instead of `https` - no actual network activity means that
there is no need for a secure network connection.

These two metadata requests discover the running instance's _name_ and _zone_,
which are required for the last line of the program.

    gcloud --quiet compute instances delete $NAME --zone=$ZONE

Finally, the `gcloud` command
is run. The `--quiet` option indicates that the command should never ask for
user confirmation of an action, since it is running in batch mode with no
user available. The `compute instances` command group performs operations on
Compute Engine instances. The `delete` command completely removes an
instance. Which instance is to be deleted is specified by the instance
_NAME_ and _ZONE_ in the command.

Every standard Linux option in Compute Engine has the `gcloud` command already
installed for your use.

## Using the console

This section gives the steps to create a self-deleting instance by using the
Google Cloud console in your web browser. If you prefer to use the command line
instead, see the next section, **Using the command line**.

1. Open the [Cloud Console] (https://console.cloud.google.com/) and select your
project, if it is not already selected.

1. Click on the menu icon in the upper left corner and select
_Compute Engine_ / _VM Instances_. The *VM Instances* control panel will
display.

1. Click **CREATE INSTANCE**. A form to set the properties of the new instance
will display. Leave most values at the default value already filled in for
you, but change the following values:
  - **Name:** Fill in any name (e.g., `myinstance`).
  - **Region and Zone:** Select a location near you.
  - **Access Scopes (under Identity and API access):** Click _Set access for each API_,
the set the value for *Compute Engine* to _Read Write_.

1. Click _More_ at the bottom of the form, then fill in the following value:
  -- **Startup script (under Automation):** Copy and past the script shown above.
For testing purposes you may want to change the sleep duration from `3600s`
to `300s`, so you will only have to wait five minutes to see that the
deletion worked.

1. Click **CREATE**.

You will see a list of your VM instances, with a spinning icon next to your
new instance. In a short while, the spinner will change to a green check mark.

Wait the duration you specified in the script. The instance you created should
disappear from the list. You can click the refresh icon if it doesn't update
on its own.

This completes the tutorial.


## Using the command line

This section gives the steps to create a self-deleting instance by using the
command line on your PC. If you prefer to use the command line
instead, see the previous section, **Using the console**.

Install the [Google Cloud SDK] (https://cloud.google.com/sdk/), then run
`gcloud init` to log in to your Google Cloud account and select the project
you want to work in. Alternatively, you can open the
[Cloud Console] (https://console.cloud.google.com/), select your project,
and then open the Cloud Shell command line by clicking the _Activate Cloud
Shell_ icon near the top right of the screen. The SDK is already installed
and initialized for you in the Cloud Shell.

Create the `startup.sh` file from the previous section. If you just want to
test whether the self-deleting code works, you can change the
sleep time from `3600s` to `300s` so you won't have to wait
for a full hour to see if it deletes itself. Then create a
self-deleting virtual machine called `myinstance` with the command:

    gcloud compute instances create myinstance \
    --metadata-from-file=startup-script=startup.sh \
    --scopes=compute-rw

You can use a different name than `myinstance` if you desire.

The `--metadata-from-file=startup-script=startup.sh` option specifies
that the new instance's metadata-server should provide the contents
of the `startup.sh` file as the value of `startup-script` when the
instance requests it. For standard Google Compute Engine instances,
that will cause the instance to run that script when it is first started.

The `--scopes=compute-rw` option specifies that the instance should have
permission to use all Compute APIs, including the API to delete an
instance. By default, new instances do *not* have that privilege, so it
needs to be added here so it can delete itself.

You may be prompted to allow the SDK to create the needed API if you
haven't used it before. Go ahead and answer `Y` for yes if needed.

You will be asked to select a region for your instance to run in. Select
one in a convenient location for you and likely users.

In a few minutes you should see a confirmation that the instance has been
created successfully:

    Created [https://www.googleapis.com/compute/v1/projects/myproject/zones/us-central1-a/instances/myinstance].
    NAME        ZONE           MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
    myinstance  us-central1-a  n1-standard-1               10.128.0.2   35.239.136.206  RUNNING

You can check on your running instances at any time with the command:

    gcloud compute instances list

Wait until the specified sleep time has expired, and run that command again.
The instance should be gone.
    
## Cleaning up

If everything went as planned, the only resource you created, the new
instance, cleaned itself up. If you no longer need the project you created
for trying this out, you can delete it, too, eliminating every resource
in it.

Click the menu icon in the upper left-hand corner of the cloud console and
select _Home_. There should be a box labeled _Project info_. Click
_Go to project settings_ at the bottom of that box.

Click **SHUT DOWN**. Type the project ID you gave the project and
click **SHUT DOWN**. The project will be shut down and will be deleted
in thirty days.
