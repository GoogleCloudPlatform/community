---
title: Use Cloud Pub/Sub to send and receive real-time messages
description: Learn to use Cloud Pub/Sub to send and receive real-time messages.
author: jscud
tags: PubSub
date_published: 2019-07-31
---

# Use Cloud Pub/Sub to send and receive real-time messages

<walkthrough-devshell-precreate></walkthrough-devshell-precreate>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=pubsub_quickstart)

</walkthrough-alt>

## Introduction

Cloud Pub/Sub is a fully-managed real-time messaging service that allows you to
send and receive messages between independent applications. This tutorial gives a brief
introduction to the command-line interface for Cloud Pub/Sub, using the `gcloud`
command-line tool.

## Project setup

GCP organizes resources into projects. This allows you to
collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-setup></walkthrough-project-setup>

For details, see
[Creating a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).

## Open Cloud Shell

In this tutorial, you do much of your work in Cloud Shell, which is a built-in command-line tool for the GCP Console.

Open Cloud Shell by clicking the <walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

## Create your first topic

A topic is a named resource to which you send messages. Create your first
topic with the following command:

```bash
gcloud pubsub topics create my-topic
```

## Add a subscription

To receive messages, you need to create subscriptions. A subscription needs to
have a corresponding topic. Create your first subscription with the following
command:

```bash
gcloud pubsub subscriptions \
    create my-sub --topic my-topic \
    --ack-deadline=60
```

This command creates a subscription named `my-sub` attached to the topic
`my-topic`. All of the messages published to `my-topic` will be delivered to this
subscription.

The `ack-deadline` option sets an *acknowledgement deadline* of 60 seconds
for this subscription. This deadline is explained in more detail later.

## List topics and subscriptions

Before sending your first message, check whether the topic and the subscription
have been successfully created. 

List your topic and subscription using the following commands:

```bash
gcloud pubsub topics list
```

```bash
gcloud pubsub subscriptions list
```

## Publish messages to the topic

Send two messages with the following commands:

```bash
gcloud pubsub topics publish my-topic --message hello
```

```bash
gcloud pubsub topics publish my-topic --message goodbye
```

Each of these commands sends a message. The first message is `hello` and the
second is `goodbye`. When you successfully publish a message, you should see the
`messageId` returned from the server. This is a unique ID automatically assigned
by the server to each message.

## Pull messages from the subscription

Now, pull the messages with the following command:

```bash
gcloud pubsub subscriptions \
    pull --auto-ack --limit=2 my-sub
```

This should return the two messages that you have just published. The messages have
the data, `hello` and `goodbye`, as well as `MESSAGE_ID`. The `MESSAGE_ID` is a
unique ID of the message that the server assigned.

Note: Cloud Pub/Sub doesn't guarantee the order of the messages. It is also
possible that only one message was returned; in that case, run the same
command again until you see the other message.

### Acknowledging messages

After you pull a message and process it, you must notify Cloud Pub/Sub
that you successfully received the message. This action is called
*acknowledgement*.

If you do not acknowledge the message before the acknowledgement deadline has
passed, Cloud Pub/Sub will re-send the message.

The `--auto-ack` flag passed with the `pull` command automatically acknowledges
a message when it is pulled.

## Manual acknowledgement

### Send a new message

Send a new message with the following command:

```bash
gcloud pubsub \
    topics publish my-topic --message thanks
```

### Pull messages again

Pull the messages with this command:

```bash
gcloud pubsub subscriptions \
    pull my-sub
```

This should display the `thanks` message, as well as `MESSAGE_ID` and `ACK_ID`.
The `ACK_ID` is an ID that you can use for acknowledging the message. Copy
the `ACK_ID` value, which you will paste into an acknowledgement in the next
step.

### Acknowledge the message

Acknowledge the message with the following command, replacing `[ACK_ID]` with
the ID that you copied in the previous step:

```bash
gcloud pubsub subscriptions ack \
    my-sub --ack-ids [ACK_ID]
```

## See the topic and the subscription in the GCP Console

This concludes the `gcloud` command-line tutorial, but let's look at the web
interface for the GCP Console before finishing the tutorial.

Open the [**Navigation menu**][spotlight-console-menu] in the upper-left corner of the console,
and select **Pub/Sub**.

<walkthrough-menu-navigation sectionId="CLOUDPUBSUB_SECTION"></walkthrough-menu-navigation>

You can use this web interface to create and manage topics and subscriptions.

## Clean up

Now that you have completed the tutorial, you should delete the resources that you created for the
tutorial.

Select the checkbox next to the topic that you created, and click the [**Delete**][spotlight-delete-button]
button to permanently delete the topic.

## Conclusion

Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You have just walked through the basic concepts of Cloud Pub/Sub.
The next step is to create your awesome applications!

For more information, see the [Cloud Pub/Sub documentation][pubsub-docs]
and [explore our code samples](https://cloud.google.com/pubsub/docs/quickstart-client-libraries).

[pubsub-docs]: https://cloud.google.com/pubsub/docs/
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
