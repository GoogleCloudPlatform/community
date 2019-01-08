---
title: Google COS ClamAV container
description: Learn how to scan Kubernetes pods and nodes for viruses from a dedicated AV pod.
author: ianmaddox
tags: kubernetes, cos, security, antivirus, av, clam, pci, dss, virus
date_published: 2019-01-08
---
Google COS ClamAV container
======================

Clam antivirus docker image with regularly scheduled scans.
Designed to be run inside Google's Container Optimized OS,
but should work with most other Docker servers.

ClamAV is an open source antivirus engine for detecting trojans, viruses,
malware & other malicious threats.
