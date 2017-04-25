---
title: Using the Google Cloud Logging Driver for Docker
description: Learn to use the gcplogs logging driver to save your Docker logs to Stackdriver Logging.
author: tswast
tags: Docker, Logging
date_published: 2017-04-24
---
This tutorial shows you how to use the [Google Cloud logging
driver](https://docs.docker.com/engine/admin/logging/gcplogs/) to [upload logs
from your Docker
containers](https://docs.docker.com/engine/admin/logging/overview/) to
[Stackdriver Logging](/logging/).

## Objectives

- Run a Docker container configured with the Google Cloud logging driver.
- View logs in the Google Cloud Platform console.

## Before you begin

1.  Create or select a Cloud Platform project from the [Google Cloud Platform
    console's projects page](https://console.cloud.google.com/project).
1.  [Enable
    billing](https://support.google.com/cloud/answer/6293499#enable-billing)
    for your project.

## Costs

This tutorial uses billable components of Cloud Platform including

- [Google Compute Engine](/compute/pricing)
- [Stackdriver Logging](/stackdriver/pricing)

Use the [Pricing Calculator](/products/calculator/) to estimate the costs for
your usage.

## Setting up the virtual machine

Create a new Compute Engine instance using the [Container-Optimized
OS](/container-optimized-os/docs/) stable image. Container-Optimized OS comes
with [Docker](https://www.docker.com/what-docker) pre-installed and supports
automatic system updates.

1.  Open the [Google Cloud Platform console](https://console.cloud.google.com).
1.  [Create a new Compute Engine instance](https://console.cloud.google.com/compute/instancesAdd).
1.  Select the desired **Zone**, such as "us-central1-f".
1.  Select the desired **Machine type**, such as "micro" (f1-micro).
1.  Change the **Boot disk** to "Container-Optimized OS stable".
1.  Click the **Create** button to create the Compute Engine instance.

## Configuring the Google Cloud logging driver for a single container

1.  After the instance is created, click the **SSH** button to open a terminal
    connected to the machine.
1.  To use the [Google Cloud logging driver for
    Docker](https://docs.docker.com/engine/admin/logging/gcplogs/), specify the
    `--log-driver=gcplogs` command-line argument to the `docker run` command.

    Run the following command to start an NGINX container which writes logs to
    Stackdriver Logging.

        docker run -d --name mysite --log-driver=gcplogs -p 80:80 nginx

    You can specify additional options with the `--log-opt` command-line
    argument. This command tells Docker to also log the command that the container
    was started with.

        docker run -d \
            --name mysite \
            --log-driver=gcplogs \
            --log-opt gcp-log-cmd=true \
            -p 80:80 \
            nginx

1.  Make a request to your container so that it logs something.

        curl 127.0.0.1:80

## Configuring the Google Cloud logging driver with Docker Compose

When using Docker Compose, specify a logging driver for each service in the
`docker-compose.yml` configuration file. For example:

    version: '2'
    services:
      web:
        logging:
          driver: gcplogs
        ...
      database:
        logging:
          driver: gcplogs
        ...

## Viewing your logs

Now that you are uploading logs to Stackdriver Logging, you can view them in
the [Google Cloud Platform Console Logs
Viewer](https://console.cloud.google.com/logs/viewer).

1.  Open the [Google Cloud Platform Console Logs
    Viewer](https://console.cloud.google.com/logs/viewer) via that link or by
    opening **Logging** from the left menu.

    ![logging menu](logging-menu.png)

2.  Select the **Global** logs.

    ![global logs](logging-global.jpg)

3.  Select the `gcplogs-docker-driver` label to limit to just the logs from your
    Docker containers.

    ![gcplogs docker driver logs](logging-driver.jpg)

4.  Enter a search filter to narrow the logs further. Enter
    `jsonPayload.container.name:nginx-proxy` to limit to logs just from containers
    with the name `nginx-proxy`.

    ![logging container name filter](logging-container-name.jpg)

## Setting the default logging driver

Instead of configuring the driver for each container, you can configure Docker
to use the Google Cloud logging driver by default.

To set the Google Cloud logging driver as the [default Docker logging
driver](https://docs.docker.com/engine/admin/logging/overview/#configure-the-default-logging-driver-for-the-docker-daemon),
specify the `--log-driver=gcplogs` option in the `dockerd` command.

    dockerd --log-driver=gcplogs

Container-Optimized OS starts [Docker using
systemd](https://docs.docker.com/engine/admin/systemd/).  To configure Docker
to use the Google Cloud logging driver when it is started by systemd:

1.  Create or edit `/etc/docker/daemon.json`.

        sudo vim /etc/docker/daemon.json

    Note that the `vim` command comes with Container-Optimized OS. To use other
    editors, use the bundled [CoreOS
    toolbox](/container-optimized-os/docs/how-to/toolbox).

1.  Write the following contents:

        {
          "log-driver": "gcplogs"
        }

1.  Restart the docker service.

        sudo systemctl stop docker
        sudo systemctl start docker

1.  Test it out by running a container without specifying an explicit
    `--log-driver`.

        docker run -d --name mysite -p 80:80 nginx

    After making a few requests to this container, you should see the logs in
    the [Logs Viewer](https://console.cloud.google.com/logs/viewer) as you did
    before.

## Next steps

- [Install the Stackdriver Logging Agent to stream system logs to Stackdriver
  Logging](/logging/docs/agent/installation).
- [Try out some other Docker-related community
  tutorials](/community/tutorials/?q=Docker).

