---
title: Kubernetes ClamAV container
description: Scan Kubernetes pods and nodes from a dedicated antivirus pod.
author: ianmaddox
tags: kubernetes, cos, security, antivirus, av, clam, pci, dss, virus
date_published: 2019-03-21
---

Ian Maddox | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[This example](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/gcp-cos-clamav) provides a Clam antivirus Docker image that performs regularly scheduled scans.

This example is designed to be run on Container-Optimized OS, but it should work with most other Docker servers.

ClamAV is an open source antivirus engine for detecting trojans, viruses, malware, and other malicious threats.

## Basic usage

1. Build your Docker image.
1. Deploy that image to your Kubernetes cluster.
1. Use Daemonsets to configure the new workload to run one scanner pod per node.
1. Ensure that scan-required paths within other pods are mounted as named volumes so they will be included in the scan of the node.

For more information, see
[Installing antivirus and file integrity monitoring on Container-Optimized OS](https://cloud.google.com/solutions/installing-antivirus-and-file-integrity-monitoring-on-container-optimized-os).

Use the following to create the container, replacing `[DOCKER_APP_CONFIG_PATH]` with the value for your environment:

    IMAGE=clamav
    CONTAINER=clamav
    APP=clamav
    BASEDIR=/[DOCKER_APP_CONFIG_PATH]/$APP

    docker create --name=$APP \
       -v /share:/host-fs:ro \
       -v $BASEDIR/logs:/logs \
       -v $BASEDIR/conf:/etc/clamav \
       --health-cmd "/health.sh" \
       $IMAGE

The first time you start the container, default configuration files will be deployed into the `conf/` subfolder. You can customize the configuration
files, and they will be deployed the next time you start the container.

Be sure to tune the `MaxThreads` value in `clamd.conf` to work well with the other workloads.
