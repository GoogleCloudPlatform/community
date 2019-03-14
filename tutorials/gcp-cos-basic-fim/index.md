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
