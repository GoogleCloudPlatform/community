---
title: Using the Google Cloud Logging driver for Docker
description: Learn to use the Google Cloud Logging driver to save your Docker logs to Cloud Logging.
author: tswast
tags: Docker, Logging, devops
date_published: 2017-04-24
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to use the [Google Cloud Logging driver](https://docs.docker.com/engine/admin/logging/gcplogs/)
to [upload logs from your Docker containers](https://docs.docker.com/engine/admin/logging/overview/) to
[Cloud Logging](https://cloud.google.com/logging/).

## Objectives

- Run a Docker container configured with the Google Cloud Logging driver.
- View logs in the Cloud Console.

## Before you begin

1.  Create or select a Google Cloud project from the [Cloud Console projects page](https://console.cloud.google.com/project).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing)
    for your project.

## Costs

This tutorial uses billable components of Google Cloud, including

- [Compute Engine](https://cloud.google.com/compute/all-pricing)
- [Cloud Logging](https://cloud.google.com/stackdriver/pricing)

Use the [pricing calculator](https://cloud.google.com/products/calculator/) to estimate the costs for
your usage.

## Setting up the virtual machine

Create a new Compute Engine instance using the [Container-Optimized OS](https://cloud.google.com/container-optimized-os/)
stable image. Container-Optimized OS comes with [Docker](https://www.docker.com/why-docker) pre-installed and supports
automatic system updates.

1.  Open the [Cloud Console](https://console.cloud.google.com).
1.  [Create a new Compute Engine instance](https://console.cloud.google.com/compute/instancesAdd).
1.  Select the desired **Zone**, such as **us-central1-f**.
1.  Select the desired **Machine series**, such as **N1**.
1.  Select the desired **Machine type**, such as **f1-micro**.
1.  Change the **Boot disk** to **Container-Optimized OS stable**.
1.  Click **Create** to create the Compute Engine instance.

## Configuring the Google Cloud Logging driver for a single container

1.  After the instance is created, click the **SSH** button to open a terminal
    connected to the machine.
1.  To use the [Google Cloud logging driver for Docker](https://docs.docker.com/config/containers/logging/gcplogs/), specify the
    `--log-driver=gcplogs` command-line argument to the `docker run` command.

    Run the following command to start an NGINX container which writes logs to
    Cloud Logging:

        docker run -d \
            --name mysite \
            --log-driver=gcplogs \
            -p 80:80 \
            nginx

1.  Make a request to your container, which will generate logs and push them
    to Cloud Logging:

        curl 127.0.0.1:80

## Configuring the Google Cloud Logging driver with Docker Compose

When using Docker Compose, specify a [logging driver](https://docs.docker.com/compose/compose-file/#logging) for each
service in the `docker-compose.yml` configuration file. For example:

    version: '3'
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

Now that you are uploading logs to Cloud Logging, you can view them in
the [Cloud Console Logs Viewer](https://console.cloud.google.com/logs/viewer).

1.  Open the [Cloud Console Logs Viewer](https://console.cloud.google.com/logs/viewer).

1.  In the **GCE VM instance** menu, choose your instance, and then select the `gcplogs-docker-driver` label to limit to just the logs from your
    Docker containers.

1.  Enter a search filter to narrow the logs further. Enter
    `jsonPayload.container.name:nginx-proxy` to limit to logs just from containers
    with the name `nginx-proxy`.

## Setting the default logging driver

Instead of configuring the driver for each container, you can configure Docker
to use the Google Cloud Logging driver by default.

To set the Google Cloud Logging driver as the
[default Docker logging driver](https://docs.docker.com/engine/admin/logging/overview/#configure-the-default-logging-driver-for-the-docker-daemon),
specify the `--log-driver=gcplogs` option in the `dockerd` command.

    dockerd --log-driver=gcplogs

Container-Optimized OS starts [Docker using systemd](https://docs.docker.com/config/daemon/systemd/). To configure Docker
to use the Google Cloud Logging driver when it is started by systemd, do the following:

1.  Create `/etc/docker/daemon.json`:

        echo '{"log-driver":"gcplogs"}' | sudo tee /etc/docker/daemon.json

1.  Restart the docker service:

        sudo systemctl restart docker

1.  Test it out by running a container without specifying an explicit
    `--log-driver`:

        docker run -d --name mysite2 -p 80:80 nginx

    After making a few requests to this container, you should see the logs in
    the [Logs Viewer](https://console.cloud.google.com/logs/viewer) as you did
    before.

## Persisting configuration across reboots

On [Container-Optimized OS](https://cloud.google.com/container-optimized-os/), files in `/etc/` are
writable, but [data does not persist across reboots](https://cloud.google.com/container-optimized-os/docs/concepts/security#filesystem).
Instead,
[use cloud-init to configure Container-Optimized OS instances](https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance#using_cloud-init).

To configure cloud-init,
[update the instance metadata](https://cloud.google.com/compute/docs/storing-retrieving-metadata#updatinginstancemetadata)
by writing a configuration to the `user-data` key.

You can write the configuration to the instance metadata from the command line
or from the Cloud Console. Both methods are described in the following
sections.

### Writing metadata from the Cloud Console

1.  Go to the [VM instances page](https://console.cloud.google.com/compute/instances).
1.  Edit the instance.
1.  Add a **Custom metadata** item with the key `user-data` and the value:

        #cloud-config

        write_files:
          - path: /etc/docker/daemon.json
            content: '{"log-driver":"gcplogs"}'

        runcmd:
          - systemctl restart docker

1.  Save the changes to the instance.
1.  Reboot the instance.
1.  Verify that the `/etc/docker/daemon.json` file is present:

        sudo ls /etc/docker

### Writing metadata from the command line

*If you have already written the metadata using the Cloud Console,
you can skip this section.*

From [Cloud Shell](https://cloud.google.com/shell/docs/quickstart) or a development machine
where you have [installed and initialized the Cloud SDK](https://cloud.google.com/sdk/docs/),
use the [gcloud compute instances add-metadata](https://cloud.google.com/sdk/gcloud/reference/compute/instances/add-metadata)
command to add the `user-data` key to your instance.

1.  Create a file `instance-config.txt` with the following contents:

        #cloud-config

        write_files:
          - path: /etc/docker/daemon.json
            content: '{"log-driver":"gcplogs"}'

        runcmd:
          - systemctl restart docker

1.  Add the `user-data` key to your instance:

        gcloud compute instances add-metadata INSTANCE_NAME \
            --metadata-from-file user-data=./instance-config.txt

    Replace `INSTANCE_NAME` with the name of your instance.

1.  Reboot the instance.
1.  Verify that the `/etc/docker/daemon.json` file is present:

        sudo ls /etc/docker

## Next steps

- [Install the Cloud Logging agent to stream system logs to Cloud Logging](https://cloud.google.com/logging/docs/agent/installation).
- [Try out some other DevOps tutorials](https://cloud.google.com/docs/tutorials/).
