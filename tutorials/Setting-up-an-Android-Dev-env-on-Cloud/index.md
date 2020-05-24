---
title: Setting up an Android Development environment on Compute Engine
description: Learn how to set up an Android development environment running on the Compute Engine.
author: Rishit Dagli
tags: Compute Engine
date_published: 2020-05-24
---

This tutorial shows how to set up an [Android Studio](https://developer.android.com/studio) on
Google Cloud Platform (GCP) in just a few minutes. Follow this tutorial to configure
Android Studio development environment on an Ubuntu or Windows server virtual machine instance on Compute Engine with the ability 
to use Android Emulators and accelerate your development.

We will set up a full fledged environment which is fast enough to do Gradle Builds in a second!

## Objectives

* Understand why a straightforward approach does not work.
* Understand nested virtualization in GCP.
* Connecting to a GUI based instance
* Using nested virtualization to test out your apps locally.

## Before you begin

You'll need a GCP project. You can use an existing project or
click the button to create a new project:

**[Create a project](https://console.cloud.google.com/project)**

## Costs

This tutorial uses billable components of GCP, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/)
to generate a cost estimate based on your projected usage. New Cloud Platform users might be
eligible for a [free trial](https://cloud.google.com/free-trial).

Here is a prefilled Pricing calculator if you follow this tutorial:
* If you follow along using Linux VMs - [Costs](https://cloud.google.com/products/calculator#id=ca135004-465c-4a43-bc5b-701af07df644)
* If you follow along using Windows VMs - [Costs](https://cloud.google.com/products/calculator#id=eff1ebe1-1ed8-4475-a5f2-d07519fb5883)

