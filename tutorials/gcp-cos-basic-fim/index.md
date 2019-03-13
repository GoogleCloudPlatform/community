---
title: Kubernetes Simple File Integrity Monitoring container
description: Learn how to monitor file integrity on a Kubernetes node and all its pods.
author: ianmaddox
tags: security, fim, pci, dss, file integrity, kubernetes, pod, node
date_published: 2019-01-08
---

Example Simple File Integrity Monitoring (FIM) container.

A basic FIM docker image with regularly scheduled scans.
Designed to be run inside Google's Container Optimized OS,
but should work with most other Docker servers.

basic-fim is an open source file integrity monitoring application that monitors for files that are new, altered, or deleted.
