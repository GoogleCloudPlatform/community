---
title: GKE: Less disruptive node upgrades using Surge Upgrade
description: Learn how Surge Upgrade reduces disruption caused by node upgrades through updating the nodes while running a sample application.
author: tamasr
tags: GKE, Upgrade, Node, Surge Upgrade
date_published: 2020-01-24
---

# Overview

This is a hands on tutorial and demo that demonstrates how GKE helps with reducing disruption of the workloads during node upgrades with the help of Surge Upgrade feature. We will build a demo application that uses some kind of a limited resource (like a connection pool to backend system, which we will emulate only). Then we deploy this application to a GKE cluster and start a client that puts load on the system. Then we’ll upgrade the node pool with and without surge upgrade and measure the error rate on the client side.

# Objectives

* Run a simple demo application that serves HTTP requests. Processing of each request requires access to a resource. Each node of the cluster has access only to a limted pool of resources. If there's no available resources left, the server returns an error.
* Test the application with lower and higher load and observe how error rate increases as the server runs out of resources.
* Upgrade the nodes without using Surge Upgrade. Observe how the temporary loss of capacity causes increased error rates.
* Upgrade the nodes using Surge Upgrade. Observe how error rates remain significantly lower due to the additional capacity provided by the surge node.

# Before you begin

This tutorial builds on top of [Deploying a containerized web application tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/hello-app). It is strongly recommended to complete that tutorial before starting this one.

# Costs

You will create a GKE cluster for this demo with 3 g1-small VMs. See [VM Instances Pricing](https://cloud.google.com/compute/vm-instance-pricing) for pricing details. The total cost of the demo should be significantly less than $0.1.

# Demonstrating less disruptive node upgrades

## 1. Change the hello-app to include allocation of a limited resource

To extend the application with the use of a limited resource, first you introduce an (emulated) resource pool. In response to each request the application attempts to allocate a resource from the pool. If there is no available resources then the application returns an error. If the allocation is successful, then the application performs some work, then it releases the resource back to the pool.

First add the resource pool and implement related operations.

[embedmd]:# (main.go)


## 2. Change the hello-app to provide health signals based on the available resources left

## 3. Deploy the application and verify it’s running and health check works

## 4. Start a client that generates load on the application and run tests with a single pod

## 5. Add more replicas, configure pod anti affinity, readiness probe and generate load

## 6. Run an upgrade without surge node while serving traffic

## 7. Run upgrade with surge while serving traffic

# Conclusion and follow up steps

# Cleaning up
