---
title: Create a Self-Deleting Virtual Machine
description: Learn how to launch a Compute Engine VM that will delete itself after a set duration, insuring that costly resources are not left running.
author: engelke
tags: Compute Engine, self-deleting, education, cost control
date_published: 2019-03-15
---
# Create a Self-Deleting Virtual Machine on Google Compute Engine

Learning to use Google Cloud is best done hands-on, by actually creating, using,
and removing resources. But a common problem with doing this is learners may
forget to clean up their resources when finished trying something, resulting
in continuing running resources, often at a cost.

This tutorial shows how to create Compute Engine instances (virtual machines)
that will automatically delete themselves after a set time, insuring that
those resources will not remain, and incur charges, indefinitely even
if the learner forgets to clean them up. This will be particularly useful
in class settings.

## Objectives

Learn how to create Cloud Engine instances that will delete themselves after
a set period of time. You will see two ways to do this.

* Using the cloud console
* Using the `gcloud` CLI tool

## Before you begin

Create a Google Cloud Platform project in a web browser.

## Costs

This tutorial has you create a Compute Engine instance. That instance
will incur charges as long as it exists. Your account can use one free
micro instance (the kind created in this tutorial) as part of the
[Free Tier](https://cloud.google.com/free).

## Preparation

The way the self-deleting instance works is by automatically executing a
startup script that waits a set amount of time and then issues a `gcloud`
command to delete itself. This script needs to be provided in a file or
at an available URL when launching the instance.

Begin this tutorial by opening a text editor and creating a file named
`startup.sh` with the following contents:

    #!/bin/sh
    sleep 3600s
    export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
    gcloud --quiet compute instances delete $NAME --zone=$ZONE

When you start a new instance and specify that it should automatically run
this script, it will do nothing for one hour (the `3600s` value on the second
line), then look up information about the running instance and put it in shell
variables (the third and fourth lines), and finally run a `gcloud` command to
delete itself.

You can use this file as is to make your instances delete themselves after
one hour (3600 seconds), or you can customize it to your exact needs:

* Change the duration before self-deletion by replacing `3600s` with a different
value. A plain numbers, or a number followed by an `s`, stands for that number
of seconds. You can specify a duration in minutes, hours, or days, by using
the suffix `m`, `h`, or `d` in place of `s`.

* Instead of the instance deleting itself after a given duration, you can have
the instance install and configure a program to run, and then delete itself
when that program deletes. Replace the `sleep 3600s` line with one or more
commands to install, configure, and run the program you want.
You can use 

## Explanation

This section explains how the file shown above works. You can safely skip
this if you just want to create self-deleting instances.

Every Linux OS image available by default in Google Compute Engine is
configured to run a program when it first boots, if you specify such a program.
The `startup.sh` file in the previous section is such a program. When you
create an image with that option, it will run the `startup.sh` program when
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
shell variable (called NAME and ZONE). Those variables will be used in a later
command. The `$(_command_)` portion runs the _command_ in the parentheses and
returns the output of that command as its value. The command here are each
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

Finally, the Cloud SDK [`gcloud`](https://cloud.google.com/sdk/gcloud/) command
is run. The `--quiet` option indicates that the command should never ask for
user confirmation of an action, since it is running in batch mode with no
user available. The `compute instances` command group performs operations on
Compute Engine instances. The `delete` command completely removes an
instance. Which instance is to be deleted is specified by the instance
_NAME_ and _ZONE_ in the command.

Every standard Linux option in Compute Engine has the `gcloud` command already
installed for your use.

## Using the console

## Using the command line

## Cleaning up
