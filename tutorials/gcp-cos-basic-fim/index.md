---
title: Kubernetes simple file integrity monitoring (FIM) container
description: Learn how to monitor file integrity on a Kubernetes node and all its pods.
author: ianmaddox
tags: security, fim, pci, dss, file integrity, kubernetes, pod, node
date_published: 2019-03-21
---

Ian Maddox | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[This example](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/gcp-cos-basic-fim) provides a basic FIM Docker image with regularly scheduled scans.

This example is designed to be run on Google Container-Optimized OS, but should work with most other Docker servers.

basic-fim is an open source file integrity monitoring application that monitors for files that are new, altered, or deleted.

## Basic usage
1. Configure the ENV vars below as needed
1. Build your Docker image.
1. Deploy that image to your Kubernetes cluster.
1. Use Daemonsets to configure the new workload to run one scanner pod per node.
1. Ensure that scan-required paths within other pods are mounted as named volumes so they will be included in the scan of 
   the node.

## ENV vars
* FIM_PATH       [/host-fs]   Path to monitor
* FIM_THREADS    [4]          Number of threads to use when hashing
* FIM_SYMLINKS   [false]      Follow symlinks found in FIM_PATH
* FIM_DATDIR     [/root/.fim] Data file directory
* FIM_LOGDIR     [/logs]      Log file directory

For more information, see [Installing antivirus and file integrity monitoring on Container-Optimized OS](https://cloud.google.com/solutions/installing-antivirus-and-file-integrity-monitoring-on-container-optimized-os).
