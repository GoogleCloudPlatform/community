---
title: Kubernetes ClamAV container
description: Scan Kubernetes pods and nodes from a dedicated AV pod.
author: ianmaddox
tags: kubernetes, cos, security, antivirus, av, clam, pci, dss, virus
date_published: 2019-03-18
---

This example provides a Clam antivirus Docker image that performs regularly scheduled scans.

This example is designed to be run on Google Container-Optimized OS, but it should work with most other Docker servers.

ClamAV is an open source antivirus engine for detecting trojans, viruses, malware, and other malicious threats.
