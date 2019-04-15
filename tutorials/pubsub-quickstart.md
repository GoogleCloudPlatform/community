---
title: Introduction to Cloud Pub/Sub
description: Learn to use Cloud Pub/Sub to send and receive real-time messages.
author: jscud
tags: Pub/Sub
date_published: 2019-04-15
---

# Introduction to Cloud Pub/Sub

<walkthrough-tutorial-url url="https://cloud.google.com/pubsub/quickstart-console"></walkthrough-tutorial-url>

<walkthrough-devshell-precreate></walkthrough-devshell-precreate>

<walkthrough-alt>
Take the interactive version of this tutorial, which runs in the Google Cloud Platform (GCP) Console:

[![Open in GCP Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?walkthrough_tutorial_id=pubsub_quickstart)

</walkthrough-alt>

## Introduction

Cloud Pub/Sub is a fully-managed real-time messaging service that allows you to
send and receive messages independent applications. This tutorial gives a brief
introduction to Cloud Pub/Sub's command-line interface using the `gcloud`
command.

## Project Setup

Google Cloud Platform organizes resources into projects. This allows you to
collect all the related resources for a single application in one place.

Cloud Pub/Sub needs a project to set up messages.

<walkthrough-project-setup></walkthrough-project-setup>

## Create your first topic

### Open Google Cloud Shell

Cloud Shell is a built-in command line tool for the console. You're going to use
Cloud Shell to set up Cloud Pub/Sub.

Open Cloud Shell by clicking the
<walkthrough-cloud-shell-icon></walkthrough-cloud-shell-icon>
[**Activate Cloud Shell**][spotlight-open-devshell] button in the navigation bar in the upper-right corner of the console.

### Create a topic

A topic is a named resource to which you will send messages. Create your first
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
`my-topic`. All the messages published to `my-topic` will be delivered to this
subscription.

You may notice the `--ack-deadline=60` option. `ack-deadline` stands for
`Acknowledgement deadline`. This new subscription has a 60 seconds
`Acknowledgement deadline`. We will explain this a bit later.

## List topics and subscriptions

Before sending your first message, check if the topic and the subscription are
successfully created. List your topic and subscription using the following
command:

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
messageId returned from the server. This is a unique id automatically assigned
by the server to each message.

## Pull messages from the subscription

### Pull messages

Now, pull the messages with the following command:

```bash
gcloud pubsub subscriptions \
    pull --auto-ack --limit=2 my-sub
```

You likely saw the two messages that you have just published. The messages have
the data, `hello` and `goodbye`, as well as `MESSAGE_ID`. The `MESSAGE_ID` is a
unique id of the message that the server assigned.

Note: Cloud Pub/Sub doesn't guarantee the order of the messages. It is also
possible that you saw only one message. In that case, try running the same
command several times until you see the other message.

### Acknowledge and acknowledgement deadline

After you pull a message and correctly process it, you must notify Cloud Pub/Sub
that you successfully received the message. This action is called
**acknowledge**.

You may have noticed the `--auto-ack` flag passed along with the `pull` command.
The `--auto-ack` flag automatically pulls the message and acknowledges it.

## Manual acknowledgement

### Send a new message

Send a new message with the following command:

```bash
gcloud pubsub \
    topics publish my-topic --message thanks
```

### Pull messages again

Pull the messages with:

```bash
gcloud pubsub subscriptions \
    pull my-sub
```

This should display the `thanks` message, as well as `MESSAGE_ID`, and `ACK_ID`.
The `ACK_ID` is another id that you can use for acknowledging the message.

### Acknowledge the message

After you pull a message, you need to acknowledge the message before the
**acknowledgement deadline** has passed. For example, if a subscription is
configured to have a 60 seconds **acknowledgement deadline**, as we did in this
tutorial, you need to acknowledge the message within 60 seconds after you pulled
the message. Otherwise, Cloud Pub/Sub will re-send the message.

Acknowledge the message with the following command (replace the `ACK_ID` with
the real one by copy/paste):

```bash
gcloud pubsub subscriptions ack \
    my-sub --ack-ids ACK_ID
```

## See the topic and the subscription in Pub/Sub UI

This concludes the `gcloud` command line tutorial, but let's look at the UI on
the Google Cloud Console before finishing the tutorial.

You can also see the topics and subscriptions in the Pub/Sub section.

### Navigate to the Pub/Sub section

Open the [menu][spotlight-console-menu] on the left side of the console.

Then, select the **Pub/Sub** section.

<walkthrough-menu-navigation sectionId="CLOUDPUBSUB_SECTION"></walkthrough-menu-navigation>

The UI also allows you to create and manage topics and subscriptions.

### Delete the topic

Check the checkbox next to the topic that you created and click the [Delete
button][spotlight-delete-button] to permanently delete the topic.

## Conclusion

Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You have just walked through the basic concepts of Cloud
Pub/Sub using the `gcloud` command line tool, and you got a glimpse of the Cloud
Pub/Sub UI. The next step is to create your awesome applications! For more
information, see [the Pub/Sub documentation][pubsub-docs].

Here's what you can do next:

[See code
samples](https://cloud.google.com/pubsub/docs/quickstart-client-libraries)

[pubsub-docs]: https://cloud.google.com/pubsub/docs/
[spotlight-console-menu]: walkthrough://spotlight-pointer?spotlightId=console-nav-menu
[spotlight-delete-button]: walkthrough://spotlight-pointer?cssSelector=.p6n-icon-delete
[spotlight-open-devshell]: walkthrough://spotlight-pointer?spotlightId=devshell-activate-button
