---
title: Sending Connection Notifications to Slack from Google Compute Engine
description: Learn how to send notifications to Slack with incoming webhooks from Google Compute Engine.
author: tswast
tags: Compute Engine, Slack
date_published: 09/22/2016
---
This tutorial demonstrates how to send a [Slack](https://slack.com)
notification when someone SSHs into a [Google Compute
Engine](https://cloud.google.com/compute/) instance.

Google Compute Engine provides virtual machine instances with support for Linux
and Windows operating systems, billed at minute-level increments.

Slack is a messaging application for working with teams, and it provides a
[rich set of APIs](https://api.slack.com/) to integrate with your applications.

## Objectives

-   Send a request to a [Slack incoming
    webhook](https://api.slack.com/incoming-webhooks).
-   Add a [Pluggable Authentication Modules
    (PAM)](http://tldp.org/HOWTO/User-Authentication-HOWTO/x115.html) hook to run
    a script on SSH logins.

## Before you begin

1.  Create a Linux Google Compute Engine instance. You can follow [the Compute
    Engine Linux quickstart
    guide](https://cloud.google.com/compute/docs/quickstart-linux) to create
    one.
2.  Create a [new Slack team](https://slack.com/create), or use an team where
    you have permissions to add custom integrations.

## Costs

This tutorial uses billable components of Cloud Platform including Google
Compute Engine. Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=6d866c0e-b928-4786-b2ab-bed5c380a2fd)
to estimate the costs for your usage.

Slack is free for up to 10 apps and integrations. Check the [Slack pricing
page](https://slack.com/pricing) for details.

## Connect to your instance

[Connect to your Google Compute Engine
instance](https://cloud.google.com/compute/docs/instances/connecting-to-instance).
The easiest way to do this is to use the [SSH button from Google Cloud
Console](https://console.cloud.google.com/compute/instances).

## Get the sample code

From the instance, clone the sample code repository and change to the `notify`
directory.

    git clone https://github.com/GoogleCloudPlatform/slack-samples.git
    cd slack-samples/notify

## Creating a Slack incoming webhook

Create a [Slack incoming webhook](https://api.slack.com/incoming-webhooks) from
the [custom integrations page for your Slack
team](https://slack.com/apps/manage/custom-integrations). You should see a
webhook URL, like
`https://hooks.slack.com/services/T000000/B00000/XXXXXXXX`.

Write this webhook URL to a file called `slack-hook` in the `notify` directory.

    echo 'https://hooks.slack.com/services/T000000/B00000/XXXXXXXX' > slack-hook

## Examining the notification script

Examine the [`login-notify.sh`
script](https://github.com/GoogleCloudPlatform/slack-samples/blob/master/notify/login-notify.sh).

First, it sets a variable with the location of this script. This will allow it
to load the `slack-hook` file so long as it is in the same directory as the
script.

    script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

Then, check to see what kind of authentication event is happening. Notify on
all events except closing an SSH connection.

    if [[ $PAM_TYPE != "close_session" ]] ; then

Construct a plain-text message to send. Include the username and remote IP
address in the message.

    host=$(hostname)
    message="SSH Login: ${PAM_USER} from ${PAM_RHOST} on ${host}"

Read the webhook URL from the `slack-hook` file.

    hook=$(cat "${script_dir}/slack-hook")

Send a POST HTTP request with the message to the Slack webhook.

    curl -X POST --data-urlencode "payload={\"text\": \"${message}\"}" "${hook}"
    fi

## Testing the notification script

Test the script by setting the `PAM_USER` and `PAM_RHOST` variables and running
the script.

    PAM_USER=$USER PAM_RHOST=testhost ./login-notify.sh

You should receive a Slack message notifying you that there as a login from
`testhost`.

## Adding the PAM hook.

A PAM hook can run a script to run whenever someone SSHs into the machine.
Verify that SSH is using PAM by making sure there is a line `UsePAM yes` in
the `/etc/ssh/sshd_config` file. You can use whatever text editor you would
like. This tutorial uses `nano`.

    sudo nano /etc/ssh/sshd_config

-   Use the [`install.sh`
    script](https://github.com/GoogleCloudPlatform/slack-samples/blob/master/notify/install.sh)
    to set up the PAM hook.

        ./install.sh

-   Keep this SSH window open in case something went wrong.
-   Verify that you can login from another SSH terminal.

You should receive another notification on Slack, indicating that you just
connected.

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this
tutorial.

1. [Delete any compute engine
   instances](https://cloud.google.com/compute/docs/instances/stopping-or-deleting-an-instance).
2. Remove the custom integration from Slack.

## Next steps

- Explore the other [Slack APIs](https://api.slack.com/).
- Check out the [other Slack samples for Google Cloud
  Platform](https://github.com/GoogleCloudPlatform/slack-samples)

