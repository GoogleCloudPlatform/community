---
title: Google Kubernetes Engine quickstart - Create a guestbook with Redis and PHP
description: Use Google Kubernetes Engine to deploy a guestbook application with Redis and PHP.
author: jscud
tags: Kubernetes, Walkthrough
date_published: 2019-07-31
---

Jeff Scudder | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Use this interactive walkthrough to learn how to setup a multi-tier web app 
using [Google Kubernetes Engine (GKE)][gke-docs] and [Redis][redis]. There are 
step-by-step instructions in the **Learn** panel on the right side of the Cloud 
Console to guide you.

[![Open in Cloud Console](https://walkthroughs.googleusercontent.com/tutorial/resources/open-in-console-button.svg)](https://console.cloud.google.com/getting-started?tutorial=gke_guestbook)

## What you'll do

In this walkthrough you’ll do the following:

* Create a Kubernetes Engine cluster.
* Install Redis and a webserver in the cluster. 
* Configure Redis and the webserver to be accessible on the internet. 

[![Open walkthrough in the Cloud Console](https://storage.googleapis.com/gcp-community/tutorials/gke-guestbook/tutorial.png)](https://console.cloud.google.com/getting-started?tutorial=gke_guestbook)

[gke-docs]: https://cloud.google.com/kubernetes-engine/
[gke-registry]: https://cloud.google.com/container-registry
[redis]: http://redis.io/
