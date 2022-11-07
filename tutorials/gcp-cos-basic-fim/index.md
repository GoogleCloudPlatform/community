---
title: Containerized simple file integrity monitoring (FIM) service
description: Monitor file integrity on a Kubernetes node and all its pods.
author: ianmaddox
tags: security, fim, pci, dss, file integrity, kubernetes, pod, node
date_published: 2019-03-21
---

Ian Maddox | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[This example](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/gcp-cos-basic-fim) provides a basic FIM Docker image with regularly 
scheduled scans.

This example is designed to be run on Google Container-Optimized OS, but it will work with most other Docker servers.

basic-fim is an open source file integrity monitoring application that monitors for files that are new, altered, or deleted.

## Docker Usage

1.  Modify the following script to define your data directory and the path to monitor:

        BASEDIR="/YOUR_DOCKER_APP_DATA_PATH/fim"
        NAME=fim
        IMAGE=ianmaddox/basic-fim
        TAG=latest
        FIM_DIR=/PATH/TO/MONITOR

        docker stop $NAME
        docker rm $NAME
        docker pull $IMAGE:$TAG
        docker create \
          --name $NAME \
          -v $BASEDIR/logs:/logs \
          -v $BASEDIR/data:/root/.fim \
          -v $FIM_DIR:/host-fs:ro \
          -e FIM_IGNORE_PATH="*/tmp/*" \
          -e FIM_THREADS="8" \
          -e FIM_PATH="/host-fs" \
          -e TZ="America/Los_Angeles" \
          $IMAGE:$TAG

1.  Define and override environment variables (listed below) as needed.
1.  Launch the container.
1.  Monitor the logs.

## Kubernetes Usage

1.  Override environment variables shown below as needed.
1.  Build your Docker image.
1.  Deploy that image to your Kubernetes cluster.
1.  Use Daemonsets to configure the new workload to run one scanner pod per node.
1.  Ensure that scan-required paths within other pods are mounted as named volumes so they will be included in the scan of the node.

## Environment variables

| variable name      | value        | description |
|--------------------|--------------|-------------|
| `FIM_PATH`         | `/host-fs`   | Path to monitor |
| `FIM_THREADS`      | `4`          | Number of threads to use when hashing |
| `FIM_SYMLINKS`     | `false`      | Follow symlinks found in `FIM_PATH` |
| `FIM_DATDIR`       | `/root/.fim` | Data file directory |
| `FIM_LOGDIR`       | `/logs`      | Log file directory |
| `FIM_IGNORE_FILE`  |              | Glob file ignore filter |
| `FIM_IGNORE_PATH`  |              | Glob path ignore filter |

For more information, see
[Installing antivirus and file integrity monitoring on Container-Optimized OS](https://cloud.google.com/solutions/installing-antivirus-and-file-integrity-monitoring-on-container-optimized-os).
