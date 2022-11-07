---
title: Running Docker Compose with Docker
description: Running Docker Compose on a Container-Optimized OS instance.
author: tswast
tags: Docker,Docker Compose,Container-Optimized OS,Compute Engine
date_published: 2017-05-03
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial guides you through running [Docker
Compose](https://docs.docker.com/compose/) in a container on a
[Container-Optimized OS](/container-optimized-os/) instance.

## Objectives

- Run Docker Compose with Docker on Container-Optimized OS.
- Create an alias for the containerized `docker-compose` command.

## Before you begin

1.  Create or select a Google Cloud project from the [Cloud Console projects page](https://console.cloud.google.com/project).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing)
    for your project.

## Costs

This tutorial uses billable components of Google Cloud, including [Compute Engine](/compute/pricing).

Use the [Pricing Calculator](/products/calculator/) to estimate the costs for
your usage.

## Setting up the virtual machine

Create a new Compute Engine instance using the [Container-Optimized
OS](/container-optimized-os/) stable image.

1.  Open the [Cloud Console](https://console.cloud.google.com).
1.  [Create a new Compute Engine instance](https://console.cloud.google.com/compute/instancesAdd).
1.  Select the desired **Zone**, such as "us-central1-f".
1.  Select the desired **Machine type**, such as "micro" (f1-micro).
1.  Change the **Boot disk** to "Container-Optimized OS stable".
1.  Check the box to allow HTTP traffic in the **Firewall** section.
1.  Click the **Create** button to create the Compute Engine instance.

## Getting the sample code

1.  After the instance is created, click the **SSH** button to open a terminal
    connected to the machine.
1.  Download the [Hello World
    sample](https://github.com/docker/dockercloud-hello-world) using the `git`
    command.

        git clone https://github.com/docker/dockercloud-hello-world.git
        cd dockercloud-hello-world

## Running Docker Compose

[Container-Optimized OS](/container-optimized-os/) has many
[benefits](/container-optimized-os/docs/concepts/features-and-benefits), but
since it is [locked down by
default](/container-optimized-os/docs/concepts/security), it is difficult to
run software that is not bundled in a container. For example, the general
instructions for installing [Docker Compose](https://docs.docker.com/compose/)
will not work because very few parts of the filesystem are mounted as
executable. Instead, you can run [Docker Compose
image](https://hub.docker.com/r/docker/compose/).

1.  Download and run the Docker Compose image. Check the [tags for Docker
    Compose](https://hub.docker.com/r/docker/compose/tags/) to use the latest
    version.

        docker run docker/compose:1.24.0 version

1.  Ensure that your location is a writable directory.

    Many directories are [mounted as read-only in the Container-Optimized
    OS](/container-optimized-os/docs/concepts/disks-and-filesystem). Change
    to a writable directory such as your home directory.

        $ pwd
        /home/username/dockercloud-hello-world

1.  Run the Docker Compose command to run the sample code.

    So that the Docker Compose container has access to the Docker daemon, mount
    the Docker socket with the `-v /var/run/docker.sock:/var/run/docker.sock`
    option.

    To make the current directory available to the container, use the `-v
    "$PWD:$PWD"` option to mount it as a volume and the `-w="$PWD"` to
    change the working directory.

        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "$PWD:$PWD" \
            -w="$PWD" \
            docker/compose:1.24.0 up

1.  With the `docker run` command still running, open the [Cloud Console instances page](https://console.cloud.google.com/compute/instances). Click the link
    to your instance's **External IP** address.

    You should see a "Hello World" message appear.

1.  With the SSH window open, press Control-C on your keyboard to stop the
    sample application.

## Making an alias to Docker Compose

The `docker run ... docker/compose:1.24.0 up` command is equivalent to running
the `docker-compose up` command on systems where Docker Compose is installed by
the usual method. So that you don't have to remember or type this long command,
create an alias for it.

1.  Add a `docker-compose` alias to your shell configuration file, e.g.
    `.bashrc`.

        echo alias docker-compose="'"'docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "$PWD:$PWD" \
            -w="$PWD" \
            docker/compose:1.24.0'"'" >> ~/.bashrc

1.  Reload the Bash configuration.

        source ~/.bashrc

1.  Change back to the sample directory if you aren't already there.

        cd ~/dockercloud-hello-world

1.  Run the sample code using the new `docker-compose` alias.

        docker-compose up

    You should be able to view the "Hello World" message at your instance's
    external IP address.

## Next steps

- [Set up the Google Cloud logging driver for Docker to upload your containers'
  logs to Stackdriver Logging](/community/tutorials/docker-gcplogs-driver).
- [Use CoreOS Toolbox to run other tools in the Container-Optimized
  OS](/container-optimized-os/docs/how-to/toolbox).
- Learn how to orchestrate containers using
  [Kubernetes](https://kubernetes.io/). [Use Kompose to transform Docker
  Compose configuration into Kubernetes
  manifests](http://blog.kubernetes.io/2016/11/kompose-tool-go-from-docker-compose-to-kubernetes.html).

