---
title: How to set up Redis on Compute Engine
description: Learn how to get Redis running on Compute Engine.
author: chingor13
tags: Compute Engine, Redis
date_published: 2017-06-08
---

Jeff Ching | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to set up [Redis](https://redis.io/) on
Google Cloud in just a few minutes. Follow this tutorial to configure a standalone
Redis instance on a Debian 8 (jessie) virtual machine instance on Compute Engine.

You can also use [Cloud Launcher](https://console.cloud.google.com/launcher/details/click-to-deploy-images/redis)
to set up a Redis cluster on Compute Engine with just a few clicks.

## Objectives

* Install Redis on a Compute Engine instance.
* Configure Redis for remote access.
* Configure a Google Cloud firewall to open a port. (optional)
* Connect to Redis from a remote computer. (optional)

## Before you begin

You'll need a Google Cloud project. You can use an existing project or
click the following link to create a new project:

[**Create a project**](https://console.cloud.google.com/project)

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

Use the [pricing calculator](https://cloud.google.com/products/calculator/#id=88a62458-4ab4-42fa-a7f3-e6b1d66bd307)
to generate a cost estimate based on your projected usage. New Google Cloud users might be
eligible for a [free trial](https://cloud.google.com/free-trial).

## Creating a Compute Engine instance

For the purposes of this tutorial, the default machine type works fine, so
you don't need to change the default setting.
In production, you need to decide how much computing power is required
for your application. In general, database systems tend to be more
constrained by I/O bottlenecks and hard disk speed than by CPU capabilities.
Redis, in particular, relies heavily on memory, so be sure to allocate enough memory for your use case.

Most Linux distributions have some version of Redis integrated with
their package managers. For this tutorial, you use Debian 8 (jessie) which includes Redis 2.8.

1. In the Cloud Console, go to the [**VM Instances**](https://console.cloud.google.com/compute/instances) page.
1. Click the **Create instance** button.
1. Set Name to `redis-tutorial`.
1. In the **Boot disk** section, click **Change** to begin configuring your boot disk.
1. In the **OS images** tab, choose **Debian GNU/Linux 8 (jessie)**.
1. In the **Boot disk type** section, select **Standard persistent disk**.
1. Click **Select**.
1. Click the **Create** button to create the instance.

It will take a few moments to create your new instance.

Stay on the **VM instances** page for the next step.

## Install Redis

Follow these steps to install Redis on your Compute Engine instance.

1. In the list of virtual machine instances, click the **SSH** button in the row of the
   instance to which you want to connect.
1. Update the Debian packages list. In the SSH terminal, enter the following command:

        sudo apt-get update

1. Install Redis:

        sudo apt-get -y install redis-server

1. Verify that Redis is running:

        ps -f -u redis

   You should see something like the following:

        yourname@redis-tutorial:~$ ps -f -u redis
        UID        PID  PPID  C STIME TTY          TIME CMD
        redis      802     1  0 21:07 ?        00:00:00 /usr/bin/redis-server 127.0.0.1:6379

Congratulations! Redis is running, but will only accept connections from `127.0.0.1`, the local machine
running the Redis server.

## Configure Redis remote access

By default, Redis doesn't allow remote connections. To change this setting,
you can change the configuration in the [`redis.conf`](https://redis.io/topics/config) file.

1. In the SSH terminal window, edit the `redis.conf` file. This tutorial uses the
`nano` editor, but you can substitute your favorite editor. Enter the following:

        sudo nano /etc/redis/redis.conf

1. Scroll down to the line that begins with `bind 127.0.0.1`. 

1. Replace `127.0.0.1` with `0.0.0.0`:

        bind 0.0.0.0

   The `bind 0.0.0.0` setting enables Redis to accept connections from any IP address. This is
   a commonly used setting. When bound to `127.0.0.1`, Redis will only accept connections
   from the local machine running Redis, meaning that your application would have to reside on the
   same machine as the Redis server.
   
   The `bind 0.0.0.0` setting makes your instance publicly accessible. This requires you to add a
   strong password to protect your instance from unauthorized access and malicious activities. 

1. Scroll down to the line that begins with `# requirepass`.   

1. Uncomment `# requirepass` and add a strong password.

         requirepass [REPLACE_WITH_YOUR_STRONG_PASSWORD]
   
   For details, see the "SECURITY" section of the
   [Redis configuration file example](http://download.redis.io/redis-stable/redis.conf).
   
1. Save the file and exit the editor.

1. Restart the database service. In the SSH terminal, enter the following:

        sudo service redis-server restart

1. Verify that Redis is listening to all traffic:

        ps -f -u redis

   You should now see something like the following:

        yourname@redis-tutorial:~$ ps -f -u redis
        UID        PID  PPID  C STIME TTY          TIME CMD
        redis      950     1  0 21:07 ?        00:00:00 /usr/bin/redis-server 0.0.0.0:6379

Congratulations! Redis will now accept connections from external machines.

## Open the network port (optional)

By default, this Compute Engine instance is added to the `default` network in your project.
The `default` network allows all TCP connections between its Compute Engine instances using
the internal network. In a production environment, you will want to skip this step.

Redis accepts remote connections on TCP port 6379. Follow these steps to add
a firewall rule that enables traffic on this port.


1. In the Cloud Console, go to the
   [**Create a firewall rule**](https://console.cloud.google.com/networking/firewalls/add) page.

1. In the **Network** field, leave the network as **default**.

1. In the **Name** field, enter `redis-tutorial`.

1. In a separate window, navigate to [ip4.me](http://ip4.me) to get the IPv4 address of your local computer.

1. Back in the Cloud Console, In **Source IP Ranges**, enter the IPv4 address from the previous step.
   Append `/32` to the end of the IPv4 address to format in
   [CIDR notation](https://wikipedia.org/wiki/Classless_Inter-Domain_Routing). For example: `1.2.3.4/32`.

1. In **Allowed protocols and ports**, enter `tcp:6379`.

1. Click **Create**.

You are now able to connect to your Redis instance from your local machine.

Firewall rules are a global resource, so you'll only need to create this rule once for all instances.

### Connect using redis-cli

Now you can connect to your Redis database from your computer. This tutorial uses `redis-cli`,
an officially supported command-line tool to interact with a Redis server.

1. Install [Redis](https://redis.io/topics/quickstart#installing-redis) on your local computer.

1. Go to the [**VM instances**](https://console.cloud.google.com/compute/instances) page and find the
   external IP address of your Compute Engine instance in the **External IP** column.

1. Ping the Redis server. Replace `[REDIS_IPV4_ADDRESS]` with the external IP address from the previous step
   and `[YOUR_STRONG_PASSWORD]` with the password you defined in step 5 of the "Configure Redis remote access"
   section:

        redis-cli -h [REDIS_IPV4_ADDRESS] -a '[YOUR_STRONG_PASSWORD]' ping

You should receive a response of `PONG` output to the terminal.

Congratulations! You've successfully connected to your Redis server.

## Best practices

This tutorial provided you with a basic look at a one-machine, single-disk
installation of Redis. In a production environment, it's a good idea to
employ strategies for high availability, scalability, archiving, backup, load
balancing, and disaster recovery. For information about disaster recovery
planning, see
[How to design a disaster recovery plan](https://cloud.google.com/solutions/designing-a-disaster-recovery-plan).

For better performance and data safety, install the database engine on the boot
disk as this tutorial showed, and then set up the data storage on a separate
persistent disk.

For machines that have an internet connection, limit access only to trusted IP ranges.

## Cleaning up

After you've finished the Redis tutorial, you can clean up the resources you created on
Google Cloud Platform so you won't be billed for them in the future. The following sections
describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Console, go to the [**Projects**](https://console.cloud.google.com/iam-admin/projects) page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Console, go to the [**VM Instances**](https://console.cloud.google.com/compute/instances) page.
1. Click the checkbox next to your `redis-tutorial` instance.
1. Click the Delete button at the top of the page to delete the instance.


### Deleting firewall rules for the default network

To delete a firewall rule:

1. In the Cloud Console, go to the [**Firewall Rules**](https://console.cloud.google.com/networking/firewalls) page.
1. Click the checkbox next to the firewall rule you want to delete.
1. Click the Delete button at the top of the page to delete the firewall rule.


## Next steps

* Explore the [Redis documentation](https://redis.io/documentation).
