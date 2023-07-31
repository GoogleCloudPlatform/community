---
title: Sending connection notifications to Slack from Compute Engine
description: Learn how to send notifications to Slack with incoming webhooks from Compute Engine.
author: tswast
tags: Compute Engine, Slack
date_published: 2016-09-22
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial demonstrates how to send a [Slack](https://slack.com)
notification when someone connects to a [Compute Engine](https://cloud.google.com/compute/) instance with SSH.

Compute Engine provides virtual machine instances with support for Linux
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

1.  Create a Linux Compute Engine instance. You can follow 
    [the Compute Engine Linux quickstart guide](https://cloud.google.com/compute/docs/quickstart-linux) to create
    one.

    When choosing a machine size, note that the [Google Cloud free
    tier](https://cloud.google.com/free/) includes 1
    [f1-micro](https://cloud.google.com/compute/docs/machine-types#sharedcore)
    instance per month. This tutorial requires very little CPU or memory
    resources.
2.  Create a [new Slack team](https://slack.com/create), or use an team where
    you have permissions to add integrations.

## Costs

This tutorial uses billable components of Google Cloud including
Compute Engine. Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=6d866c0e-b928-4786-b2ab-bed5c380a2fd)
to estimate the costs for your usage.

Slack is free for up to 10 apps and integrations. Check the [Slack pricing
page](https://slack.com/pricing) for details.

## Connect to your instance

[Connect to your Compute Engine instance](https://cloud.google.com/compute/docs/instances/connecting-to-instance).
The easiest way to do this is to use the [SSH button from Cloud Console](https://console.cloud.google.com/compute/instances).

## Get the sample code

From the instance, clone the sample code repository and change to the `notify`
directory.

    git clone https://github.com/GoogleCloudPlatform/slack-samples.git
    cd slack-samples/notify

If git is not installed, download and extract the code.

    # Alternative if git is not installed.
    wget https://github.com/GoogleCloudPlatform/slack-samples/archive/master.tar.gz
    tar -xzf master.tar.gz
    cd slack-samples-master/notify

## Creating a Slack incoming webhook

An [incoming webhook](https://api.slack.com/incoming-webhooks) creates an HTTPS
endpoint where you can send messages. These messages will post the the
configured channel or direct message.

1.  Create a [new Slack app](https://api.slack.com/apps).
    1.  Give the app a name, such as "SSH Notifier".
    1.  Choose the Slack team where you want it installed.
1.  Select the [Slack incoming webhook](https://api.slack.com/incoming-webhooks) feature in the **Add
    features and functionality** section.
    1.  Click the **Off** switch in the upper right-hand corner to activate the
        incoming webhooks feature. The switch will turn green to indicate the
        feature is now **On**.
1.  Click the **Add new webhook to team** button at the bottom of the incoming
    webhooks feature page.
    1.  In the authorization dialog, select the channel where you want the SSH
        notifications to appear, such as #cloud or #botdev.
1.  You should now see a webhook URL, like
    `https://hooks.slack.com/services/T000000/B00000/XXXXXXXX`. Copy it to your
    clipboard by clicking the **Copy** button.
1.  Switch back to the SSH connection on the Compute Engine instance.
    1.  Write the webhook URL to a file called `slack-hook` in the `notify` directory.

            echo 'https://hooks.slack.com/services/T000000/B00000/XXXXXXXX' > slack-hook

[Be careful](https://api.slack.com/docs/oauth-safety) with your webhook URL.
Treat it like you would any other secret token. Do not store tokens in version
control or share them publicly.

## Examining the notification script

*This section explains the script used to send notifications to Slack. It
should be easy to understand if you are familiar with [Bash
syntax](https://tiswww.case.edu/php/chet/bash/bashtop.html). You may skip to
the **Testing the notification script** section if you only wish to try out the
code.*

Examine the [`login-notify.sh`
script](https://github.com/GoogleCloudPlatform/slack-samples/blob/master/notify/login-notify.sh).

First, it sets a variable with the location of this script. This will allow it
to load the `slack-hook` file so long as it is in the same directory as the
script.

    script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

Then it checks to see what kind of authentication event is happening. The
script notifies on all events except closing an SSH connection.

    if [[ $PAM_TYPE != "close_session" ]] ; then

Then it constructs a plain-text message to send. The message include the
username and remote IP address.

    host=$(hostname)
    message="SSH Login: ${PAM_USER} from ${PAM_RHOST} on ${host}"

It reads the webhook URL from the `slack-hook` file.

    hook=$(cat "${script_dir}/slack-hook")

Finally, it send a POST HTTP request with the message to the Slack webhook.

    curl -X POST --data-urlencode "payload={\"text\": \"${message}\"}" "${hook}"
    fi

## Testing the notification script

Test the script by setting the `PAM_USER` and `PAM_RHOST` variables and running
the script from the Compute Engine instance SSH terminal.

    PAM_USER=$USER PAM_RHOST=testhost ./login-notify.sh

You should receive a Slack message notifying you that there as a login from
`testhost`.

## Adding the PAM hook.

A PAM hook can run a script to run whenever someone SSHs into the machine.

1.  Verify that SSH is using PAM by making sure there is a line `UsePAM yes` in
    the `/etc/ssh/sshd_config` file.

        grep UsePAM /etc/ssh/sshd_config

    If you do not see `UsePAM yes` or it is commented out with a `#`, you can
    use whatever text editor you would like to edit the file. This tutorial
    uses `nano`.

        sudo nano /etc/ssh/sshd_config

1.  Use the [`install.sh`
    script](https://github.com/GoogleCloudPlatform/slack-samples/blob/master/notify/install.sh)
    to set up the PAM hook.

        sudo ./install.sh

1.  Keep this SSH window open in case something went wrong.
1.  Verify that you can login from another SSH terminal.

You should receive another notification on Slack, indicating that you just
connected.

## Cleaning up

To prevent unnecessary charges, clean up the resources created for this
tutorial.

1. [Delete any Compute Engine
   instances](https://cloud.google.com/compute/docs/instances/stopping-or-deleting-an-instance).
2. Remove the [custom integration from
   Slack](https://slack.com/apps/manage/custom-integrations).

## Next steps

- Explore the other [Slack APIs](https://api.slack.com/).
- Check out the [other Slack samples for Google Cloud](https://github.com/GoogleCloudPlatform/slack-samples)
