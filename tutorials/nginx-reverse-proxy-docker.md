---
title: Running an NGINX reverse proxy with Docker and Let's Encrypt on Compute Engine
description: Learn to serve multiple websites simultaneously in a single Compute Engine instance with Docker and NGINX. Also, learn how to secure the sites with Let's Encrypt.
author: tswast
tags: Compute Engine, NGINX, Docker, Let's Encrypt
date_published: 2017-04-19
---

Tim Swast | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial guides you through running multiple websites on a Compute
Engine instance using Docker. You secure the websites using free SSL/TLS
certificates from [Let's Encrypt](https://letsencrypt.org/).

## Objectives

- Create a Compute Engine instance.
- Run an NGINX reverse proxy.
- Run multiple web applications in Docker.
- Install SSL/TLS certificates with Let's Encrypt.

## Before you begin

1.  Create or select a Google Cloud project from the [Cloud Console projects page](https://console.cloud.google.com/project).
1.  [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing)
    for your project.

## Costs

This tutorial uses billable components of Google Cloud including [Compute Engine](https://cloud.google.com/compute/pricing).

Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=bb109d69-241c-4262-afdf-a6604401e053)
to estimate the costs for your usage.

## Setting up the virtual machine

Create a new Compute Engine instance using the [CoreOS](https://coreos.com/why)
stable image. CoreOS comes with [Docker](https://www.docker.com/what-docker)
pre-installed and supports automatic system updates.

1.  Open the [Cloud Console](https://console.cloud.google.com).
1.  [Create a new Compute Engine instance](https://console.cloud.google.com/compute/instancesAdd).
1.  Select the desired **Zone**, such as "us-central1-f".
1.  Select the desired **Machine type**, such as "micro" (f1-micro).
1.  Change the **Boot disk** to "CoreOS stable".
1.  Check the boxes to allow HTTP and HTTPS traffic in the **Firewall** section.
1.  Expand the **Management, disk, networking** section.
1.  Click the **Networking** tab.
1.  Select **New static IP address** under **External IP**.
1.  Give the IP address a name, such as "reverse-proxy".
1.  Click the **Create** button to create the Compute Engine instance.

## Set up some domains for your instance

Create multiple [A type DNS
records](https://en.wikipedia.org/wiki/List_of_DNS_record_types) for various
domains/subdomains on your DNS provider pointing at the external IP address for
your new instance.

For example, in [Google Domains](https://domains.google.com/registrar), open
**DNS** for your domain, scroll to [Custom resource
records](https://support.google.com/domains/answer/3251147) and add an **A**
type record. The name "@" corresponds to the root of your domain or you can
change it to a subdomain, such as "a" and "b".

This tutorial assumes that you have two subdomains with A records:

- a.example.com
- b.example.com

## Setting up the reverse proxy

To have the separate websites respond only to their respective hosts, you
use a [reverse proxy](https://en.wikipedia.org/wiki/Reverse_proxy). This
tutorial uses the [nginx-proxy Docker
container](https://github.com/jwilder/nginx-proxy) to automatically configure
NGINX to forward requests to the corresponding website.

As an example, this tutorial shows a plain NGINX server running as
site A and a [plain Apache server](https://hub.docker.com/_/httpd/) running as site B.

You run the commands in this section from the VM instance that you created
in the "Setting up the virtual machine" section. Before you run these commands,
connect to the VM instance using SSH.

1.  Run the reverse proxy.

        docker run -d \
            --name nginx-proxy \
            -p 80:80 \
            -v /var/run/docker.sock:/tmp/docker.sock:ro jwilder/nginx-proxy

1.  Start the container for site A, specifying the domain name in the
    `VIRTUAL_HOST` variable.

        docker run -d --name site-a -e VIRTUAL_HOST=a.example.com nginx

1.  Check out your website at http://a.example.com.
1.  With site A still running, start the container for site B.

        docker run -d --name site-b -e VIRTUAL_HOST=b.example.com httpd

1.  Check out site B at http://b.example.com.

Congratulations, you are running multiple apps on the same host using
Docker and an [nginx reverse proxy](https://github.com/jwilder/nginx-proxy).

**Note**: If you do not wish to set up HTTPS for your websites using [Let's Encrypt](https://letsencrypt.org/), you can skip reading the rest of this tutorial.

## Setting up HTTPS with Let's Encrypt

Plain HTTP is not secure. It is not encrypted and is vulnerable to
[man-in-the-middle
attacks](https://en.wikipedia.org/wiki/Man-in-the-middle_attack). In this step,
you'll add support for the HTTPS protocol.

1.  Stop the containers.

        docker stop site-a
        docker stop site-b
        docker stop nginx-proxy

1.  Remove the containers.

        docker rm site-a
        docker rm site-b
        docker rm nginx-proxy

To enable HTTPS via
[TLS/SSL](https://en.wikipedia.org/wiki/Transport_Layer_Security), your reverse
proxy requires cryptographic certificates. Use [Let's
Encrypt](https://letsencrypt.org/) via the [Docker Let's Encrypt nginx-proxy
companion](https://github.com/JrCs/docker-letsencrypt-nginx-proxy-companion) to
automatically issue and use signed certificates.

1.  Create a directory to hold the certificates.

        cd
        mkdir certs

1.  Run the proxy, but this time declaring volumes so that the 
    [Let's Encrypt
    companion](https://github.com/JrCs/docker-letsencrypt-nginx-proxy-companion)
    can populate them with certificates.

        docker run -d -p 80:80 -p 443:443 \
            --name nginx-proxy \
            -v $HOME/certs:/etc/nginx/certs:ro \
            -v /etc/nginx/vhost.d \
            -v /usr/share/nginx/html \
            -v /var/run/docker.sock:/tmp/docker.sock:ro \
            --label com.github.jrcs.letsencrypt_nginx_proxy_companion.nginx_proxy=true \
            jwilder/nginx-proxy

1.  Run the Let's Encrypt companion container.

        docker run -d \
            --name nginx-letsencrypt \
            --volumes-from nginx-proxy \
            -v $HOME/certs:/etc/nginx/certs:rw \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            jrcs/letsencrypt-nginx-proxy-companion

1.  Run site A.

    In addition to `VIRTUAL_HOST`, specify `LETSENCRYPT_HOST` to declare the
    host name to use for the HTTPS certificate. Specify the `LETSENCRYPT_EMAIL`
    so that [Let's Encrypt can email you about certificate
    expirations](https://letsencrypt.org/docs/expiration-emails/).

        docker run -d \
            --name site-a \
            -e 'LETSENCRYPT_EMAIL=webmaster@example.com' \
            -e 'LETSENCRYPT_HOST=a.example.com' \
            -e 'VIRTUAL_HOST=a.example.com' nginx

1.  You can watch the companion creator request new certificates by watching the logs.

        docker logs nginx-letsencrypt

    You should eventually see a log which says `Saving cert.pem`.

1.  After the certificate is issued, check out your website at
    https://a.example.com.

1.  Run site B.

        docker run -d \
            --name site-b \
            -e 'LETSENCRYPT_EMAIL=webmaster@example.com' \
            -e 'LETSENCRYPT_HOST=b.example.com' \
            -e 'VIRTUAL_HOST=b.example.com' httpd

1.  You can watch the companion creator request new certificates by watching the logs.

        docker logs nginx-letsencrypt

    You should eventually see a log which says `Saving cert.pem`.

1.  After the certificate is issued, check out your website at
    https://b.example.com.

Congratulations, your web apps are now running behind an HTTPS reverse proxy.

## Proxying composed web apps

In order to proxy the `nginx-proxy` container and the web app container must be on
the same [Docker network](https://runnable.com/docker/basic-docker-networking).

When you run a multi-container web app with `docker-compose`, [Docker attaches the
containers to a default network](https://runnable.com/docker/docker-compose-networking).
The default network is different from the bridge network that containers run with
the `docker run` command attach to.

If you run the `docker-compose` and have specified a `VIRTUAL_HOST`
environment variable in the `docker-compose.yml` configuration file,
you'll see this error message in the `docker logs nginx-proxy` output:

     no servers are inside upstream

The proxy will also stop working. To resolve this,

1.  Create a new Docker network.

        docker network create --driver bridge reverse-proxy
 
1.  Stop and remove your web application containers, the `nginx-proxy` container,
    and the `nginx-letsencrypt` container.
    
        docker stop my-container
        docker rm my-container
        docker stop nginx-proxy
        docker rm nginx-proxy
        docker stop nginx-letsencrypt
        docker rm nginx-letsencrypt

1.  Run the proxy and other containers, specifying the network with the
    `--net reverse-proxy` command-line parameter.
    
    Run the proxy container.
    
        docker run -d -p 80:80 -p 443:443 \
            --name nginx-proxy \
            --net reverse-proxy \
            -v $HOME/certs:/etc/nginx/certs:ro \
            -v /etc/nginx/vhost.d \
            -v /usr/share/nginx/html \
            -v /var/run/docker.sock:/tmp/docker.sock:ro \
            --label com.github.jrcs.letsencrypt_nginx_proxy_companion.nginx_proxy=true \
            jwilder/nginx-proxy

    Run the Let's Encrypt helper container.
    
        docker run -d \
            --name nginx-letsencrypt \
            --net reverse-proxy \
            --volumes-from nginx-proxy \
            -v $HOME/certs:/etc/nginx/certs:rw \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            jrcs/letsencrypt-nginx-proxy-companion

    Run your website containers.
    
        docker run -d \
            --name site-a \
            --net reverse-proxy \
            -e 'LETSENCRYPT_EMAIL=webmaster@example.com' \
            -e 'LETSENCRYPT_HOST=a.example.com' \
            -e 'VIRTUAL_HOST=a.example.com' nginx

1.  Modify the `docker-compose.yml` file to include the network you created
    in the networks definition.

        networks:
          reverse-proxy:
            external:
              name: reverse-proxy
          back:
            driver: bridge

    In the container definitions, specify the appropriate networks. Only
    the web server needs to be on the reverse-proxy network. The other
    containers can stay on their own network.
    
    The final `docker-compose.yml` file will look something like this:
    
        version: '2'
        services:

          db:
            restart: always
            image: my_database
            networks:
              - back

          web:
            restart: always
            image: my_webserver
            networks:
              - reverse-proxy
              - back
            environment:
              - VIRTUAL_PORT=1234
              - VIRTUAL_HOST=c.example.com
              - LETSENCRYPT_HOST=c.example.com
              - LETSENCRYPT_EMAIL=webmaster@example.com
    
        networks:
          reverse-proxy:
            external:
              name: reverse-proxy
          back:
            driver: bridge
   
1.  Run the `docker-compose up -d` command to run your composed containers
    with the new configuration.

## Surviving reboots

When your Compute Engine instance restarts, the Docker containers will not
automatically restart. Use the `--restart` flag for the `docker run` command to
specify a [Docker restart
policy](https://docs.docker.com/engine/reference/run/#restart-policies---restart).
I suggest `always` or `unless-stopped` so that Docker restarts the containers
on reboot.

## Next steps

Running many web apps on a single host behind a reverse proxy is an efficient
way to run hobby applications. To make your experience even better,

- [Set up the Google Cloud logging driver for Docker to upload your containers'
  logs to Stackdriver
  Logging](/community/tutorials/docker-gcplogs-driver).

Note that apps deployed to a single instance are not highly available. For
example, your applications will not be available during a system reboot.

To see how to run an app which requires high availability or scaling to many
queries per second, try out some more scalable ways of hosting.

1.  Deploy a scalable web app using [App Engine flexible
    environment](/appengine/docs/flexible/python/quickstart).
1.  Host a [static website using Firebase Hosting](https://firebase.google.com/docs/hosting/quickstart).
1.  Host a [static website using Cloud Storage](/storage/docs/hosting-static-website).

