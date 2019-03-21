---
title: Kubernetes simple file integrity monitoring (FIM) container
description: Learn how to monitor file integrity on a Kubernetes node and all its pods.
author: ianmaddox
tags: security, fim, pci, dss, file integrity, kubernetes, pod, node
date_published: 2019-03-18
---

Example simple file integrity monitoring (FIM) container.

A basic FIM Docker image with regularly scheduled scans.
Designed to be run on Google Container-Optimized OS, but should work with most other Docker servers.

basic-fim is an open source file integrity monitoring application that monitors for files that are new, altered, or deleted.

# Basic Usage
1. Build your Docker image
1. Deploy that image to your Kubernetes cluster
1. Use Daemonsets to configure the new workload to run one scanner pod per node
1. Ensure scan-required paths within other pods are mounted as named volumes so they will be included in the scan of the node

Full documentation is available here:
https://cloud.google.com/solutions/installing-antivirus-and-file-integrity-monitoring-on-container-optimized-os
