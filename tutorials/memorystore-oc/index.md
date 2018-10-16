---
title: Client-side Tracing of Cloud Memorystore for Redis Workloads with OpenCensus
description: implement client-side tracing in your Cloud Memorystore for Redis workloads using OpenCensus and Stackdriver.
author: karthit
tags: Cloud Memorystore, OpenCensus, Observability, Monitoring, Tracing, Caching
date_published: 2018-10-31
---

* Karthi Thyagarajan | Solutions Architect | Google Cloud

This tutorial shows how to use implement client-side tracing in your Cloud Memorystore for Redis workloads using OpenCensus and Stackdriver. While Cloud Memorystore for Redis surfaces a number of helpful server-side metrics via Stackdriver, applications can realize added benefit from implementing client-side tracing. For instance, server-side metrics do not give you a window into the round-trip latency of calls made to your Redis endpoint and can only be surfaced using client-side tracing.

Cloud Memorystore for Redis provides a fully managed and Google-hosted Redis deployment for your caching needs.

OpenCensus is an open source library that can be used to provide observability in your applications. It is vendor agnostic and integrates with a number of backends such as Prometheus and Zipkin. In this tutorial, we will use Stackdriver as the tracing backend.

## Objectives

- Deploy a Cloud Memorystore for Redis instance.
- Deploy a Google Compute Engine (GCE) VM for running an OpenCensus instrumented Java client.
- Download, deploy and run instrumented Java client.
- View OpenCensus traces in the Stackdriver Trace tool.


## Before you begin