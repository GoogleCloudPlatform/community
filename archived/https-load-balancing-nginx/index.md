---
title: HTTPS load balancing using NGINX and Compute Engine
description: Learn about HTTPS Load Balancing using NGINX and Google Compute Engine.
author: tzero
tags: Compute Engine, Nginx
date_published: 2015-08-14
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

HTTP(S) load balancing is an invaluable tool for scaling your website or web
application, allowing you to route your traffic through a single IP and
distribute it across multiple backends. In addition, HTTP(S) load balancing
allows you to route incoming requests with a high degree of granularity. With
the right configuration, you can configure your load balancer to route requests
based on geographical point of origin, requested content type, machine resource
availability, and more.

This tutorial walks you through one possible load balancing solution: an
[NGINX][nginx]-based HTTP(S) load balancer on Compute Engine. NGINX is a popular
load balancing solution, with a mature, complete feature set and high
configurability. Features include:

[nginx]: http://nginx.org/

* SSL encryption and decryption
* Server weighting
* Session persistence
* Health checking
* Several common load balancing algorithms

Note that an NGINX-based solution also has some limitations when compared to
Compute Engine's built-in HTTP(S) load balancing solution:

*   Because an NGINX-based load balancer is installed on a single
    [Compute Engine instance][instance], it represents a single point of
    failure. In contrast, Compute Engine's HTTP(S) load balancing solution is a
    managed service with built-in redundancy and fault tolerance.
*   Because Compute Engine instances are tied to specific Compute Engine
    [zones][zones], all traffic is funneled through the zone in which your
    load balancer instance resides, regardless of the traffic's point of origin.
    In contrast, Compute Engine's HTTP(S) load balancing solution can receive
    and route traffic in the zone nearest to the client making the request. See
    [Cross-Region Load Balancing][cross_region] for an example configuration.

[instance]: https://cloud.google.com/compute/docs/instances
[zones]: https://cloud.google.com/compute/docs/zones
[cross_region]: https://cloud.google.com/compute/docs/load-balancing/http/cross-region-example

## Implementation overview

In this tutorial, you build a simple NGINX-based HTTP(S) load balancer.
This load balancer features end-to-end SSL/TLS encryption; traffic is
routed to one of three SSL/TLS-enabled Apache web servers, and incoming HTTP
traffic is encrypted as it passes through the load balancer.

The following diagram illustrates the load balancer architecture:

![Nginx load balancing overview][nginx_overview]

[nginx_overview]: https://storage.googleapis.com/gcp-community/tutorials/https-load-balancing-nginx/nginx-load-balancer-overview.svg

Figure 1: Architecture of NGINX-based HTTPS load balancer

**Important**:  This tutorial uses Compute Engine virtual machine instances,
            a billable component of Google Cloud. The cost of running
            this tutorial varies depending on run time, number of instances,
            and machine type. Use the [pricing calculator][pricing] to generate
            a cost estimate based on your projected usage. New Google Cloud
            users may be eligible for a [free trial][trial].

[pricing]: https://cloud.google.com/products/calculator/#id=4dd2c1cc-7da8-495a-a1a8-191d3343ee11
[trial]: https://cloud.google.com/free-trial/

## Prerequisites

This tutorial assumes that you've already performed the following setup tasks:

* [Created a Google Cloud project and enabled the Compute Engine API](https://console.cloud.google.com/flows/enableapi?apiid=compute&_ga=1.122528201.332687869.1476592937)
* [Installed the Cloud SDK](https://cloud.google.com/sdk/docs/)

## Obtain an SSL/TLS certificate

To enable NGINX and Apache to encrypt traffic, you need to have a private key
and signed SSL/TLS certificate that you can add to their respective
configurations.

If you already have a private key, certificate, and (optionally) PEM file issued
by a certificate authority, create a new directory called `ssl-certs` and copy
your files into that directory. After you're finished, move on to the next
section of this tutorial.

If you do not yet have a private key and certificate, you can create a new key
and generate a [self-signed certificate][self_signed] using the `openssl`
command.

[self_signed]: https://wikipedia.org/wiki/Self-signed_certificate

**Caution**: Self-signed certificates are not suitable for public sites. While
          a self-signed certificate implements full encryption, it causes
          most browsers to present a warning or error when visitors try to
          access your site.

To create a new private key:

1. Create a new directory to store your key and certificate:

        mkdir ssl-certs

1. Navigate to the new directory:

        cd ssl-certs

1. Use `openssl` to generate the key:

        openssl genrsa -out example.key 2048

1. Remove the key's passphrase (optional):

        openssl rsa -in example.key -out example.key

To generate a signed certificate, you need a certificate signing request
(CSR). Run the following command to create one:

    openssl req -new -key example.key -out example.csr

You can use your new CSR to obtain a valid certificate from a certificate
authority. Alternatively, you can generate a self-signed certificate by running
the following:

    openssl x509 -req -days 365 -in example.csr -signkey example.key -out example.crt

## Create and configure the load balancer backends

Before you create the load balancer, you need to have some backend server
instances to which the load balancer can route traffic. In this section, you
create three identical Compute Engine virtual machine instances that you
can use as backends for your load balancer. After the backends have been
created, you configure their respective Apache servers to use SSL.

### Create your load balancer backends

To create your load balancer backends and allow them to be accessed by external
HTTPS traffic:

1.  Create your virtual machine instances, tag them to automatically allow
    external HTTPS traffic through the firewall, install Apache Web Server on
    them, and enable Apache's SSL module:

    ```sh
    for i in {1..3}; \
      do \
        gcloud compute instances create www-$i \
          --tags "https-server" \
          --zone us-central1-f \
          --metadata startup-script="#! /bin/bash
          apt-get update
          apt-get install -y apache2
          /usr/sbin/a2ensite default-ssl
          /usr/sbin/a2enmod ssl
          service apache2 reload
              "; \
      done
    ```

1.  Obtain the external IP addresses of your instances:

        gcloud compute instances list

1.  Run `curl` to verify that each instance is up and running:

        curl -k https://IP_ADDRESS_HERE

    The **-k** flag allows you to bypass the `curl` command's standard SSL/TLS
    certificate verification. This flag is necessary because, although the
    startup script configured Apache to receive HTTPS traffic on each
    instance, the instances do not yet have SSL certificates installed.

### Install your SSL certificates

Now that your backend server instances are healthy and running properly, you can
install your key, certificate, and PEM file (if applicable) on each. Begin by
copying the files to the instances as follows:

```sh
for i in {1..3};
  do \
    gcloud compute scp /local/path/to/ssl-certs \
      root@www-$i:/etc/apache2; \
  done
```

Next, for each instance, perform the following tasks:

1.  Establish an SSH connection to the instance:

        gcloud compute ssh [INSTANCE_NAME]

1.  Edit default-ssl.conf:

        sudo nano /etc/apache2/sites-enabled/default-ssl.conf

1.  Find the following lines:

        SSLCertificateFile    /etc/ssl/certs/ssl-cert-snakeoil.pem
        SSLCertificateKeyFile /etc/ssl/private/ssl-cert-snakeoil.key

1.  Replace the example paths with the paths to your own certificate and key:

    SSLCertificateFile    /etc/apache2/ssl-certs/example.crt
    SSLCertificateKeyFile /etc/apache2/ssl-certs/example.key

1.  If applicable, find the line that starts with `SSLCertificateChainFile` and
    replace that path with the path to the SSL certificate chain file provided
    by your certificate authority.

1.  Reload Apache:

        sudo service apache2 reload

1.  Repeat steps 1-6 for each instance.

## Create and configure the load balancer

Now that your backend servers are in place, create your load balancer and
configure it to route traffic to them.

### Create the NGINX instance

To create your NGINX instance:

1.  Create a new static IP address:

        gcloud compute addresses create lb-ip \
          --region us-central1

1.  Create a firewall rule to allow external HTTP traffic to reach your load
    balancer instance. Later in this tutorial, you configure the load
    balancer to redirect this traffic through your HTTPS proxy:

        gcloud compute firewall-rules create http-firewall \
           --target-tags lb-tag --allow tcp:80

1.  Create a new Compute Engine instance, assign your new static IP address to
    the instance, and tag the instance so that it can receive both HTTP and
    HTTPS traffic:

        gcloud compute instances create nginx-lb \
          --zone us-central1-f --address lb-ip \
          --tags lb-tag,be-tag

1.  Establish an SSH connection to the **nginx-lb** instance:

        gcloud compute ssh nginx-lb

1.  Update the instance's Debian repositories (as `user@nginx-lb`):

        sudo apt-get update

1.  Install NGINX:

        sudo apt-get install -y nginx

1.  Create a folder for your ssl certificates on your instance:

        mkdir ~/ssl_certs
        
1.  Run the `exit` command to exit your SSH session.

    After you've exited your session, use `gcloud compute` to copy your private key,
    SSL/TLS certificate, and (if applicable) certificate authority PEM file to the
    load balancer instance:

        gcloud compute scp /local/path/to/ssl-certs/* \
        nginx-lb:~/ssl-certs --zone us-central1-f

    Since you do not have write access for */etc/nginx*, you will have to log on to the load balancer instance and move the files to the correct folder.

1.  Reconnect to your **nginx-lb**:

        gcloud compute ssh nginx-lb
        
1.  Move your folder for ssl certificate to NGINX:

        sudo mv ~/ssl-certs /etc/nginx/

### Create your virtual host

Now that you've installed NGINX on and copied your SSL/TLS files to your
instance, you can start configuring the NGINX installation as an HTTPS load
balancer:

1.  Run the following command to view a list of your instances' IPs:

        gcloud compute instances list

    Take note of each target instance's internal IP. You need these IPs
    when you begin configuring NGINX.

1.  Establish an SSH connection to the **nginx-lb** instance:

        gcloud compute ssh nginx-lb

1.  Create and open a new virtual host file:

        sudo nano /etc/nginx/sites-available/my-vhost

1.  Create a new top-level `upstream` directive and add your backend server
    instances to it, specifying the internal IP address of each instance. Your
    backend server instances are configured to receive SSL/TLS-encrypted traffic
    only, so add port 443 to each IP as well:

        upstream lb {
          server IP_ADDRESS_1:443;
          server IP_ADDRESS_2:443;
          server IP_ADDRESS_3:443;
        }

1.  Configure the load balancer to route incoming and outgoing HTTPS traffic.
    Create a new top-level `server` directive in the virtual host file and
    populate it as follows:

        server {
          listen 443 ssl;
          server_name lbfe;
          ssl on;
          ssl_certificate         /etc/nginx/ssl-certs/example.crt;
          ssl_certificate_key     /etc/nginx/ssl-certs/example.key;
          location / {
            proxy_pass https://lb;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
          }
        }

    This directive tells NGINX to listen for HTTPS traffic on port 443, decrypt
    and encrypt the traffic using your key and certificate, and route the
    traffic to one of the three servers specified in your `upstream` directive
    (`lb`).

    **Important**:  If you have a certificate chain file from a certificate
                authority, add it to your `server` block using the
                `ssl_trusted_certificate` directive. Place this directive after
                the `ssl_certificate_key` directive:

        ssl_trusted_certificate /etc/nginx/ssl-certs/your-file.pem;

1.  Add an additional top-level `server` directive to intercept HTTP traffic and
    redirect it to the HTTPS gateway:

        server {
          listen 80;
            if ($scheme = "http") {
            return 301 https://$host$request_uri;
            }
        }

1.  Save and close the virtual host file.

Now that you've finished configuring your load balancer, perform some minor clean up and sanity checking tasks:

1.  Create a symbolic link to the `sites-enabled` directory:

        sudo ln -s /etc/nginx/sites-available/my-vhost \
          /etc/nginx/sites-enabled/my-vhost

1.  To avoid conflicting host configurations, remove the default virtual host
    file:

        sudo rm /etc/nginx/sites-enabled/default

1.  Test your configuration for errors:

        sudo service nginx configtest

If all is well, reload the NGINX service to add your SSL/TLS-enabled virtual
host:

    sudo service nginx reload

Congratulations! You now have a fully-operational HTTPS load balancer.

### Configure your load balancer

Now that your load balancer is working, configure it to fit your needs.

#### Harden your SSL/TLS configuration

To remove potential vulnerabilities caused by older ciphers or encryption
protocols, you should customize your SSL/TLS configuration to reflect current
best practices.

**Important**:  The following directives should be positioned after the certificate
            and key directives in the SSL/TLS `server` block of your virtual
            host file. If you've defined a certificate authority PEM file,
            position these directives after the `ssl_trusted_certificate`
            directive; otherwise, position them after the `ssl_certificate_key`
            directive.

To harden your SSL/TLS configuration:

1.  Set the `ssl_prefer_server_ciphers` directive to specify that server ciphers
    should be preferred over client ciphers:

        ssl_prefer_server_ciphers on;

1.  Disable SSLv2, which is known to be insecure, by whitelisting your preferred
    protocols using the `ssl_protocols` directive:

        ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;

1.  Define your cipher suite. The cipher suite provided here is a strong,
    minimal suite that disables weak or outmoded encryption methods. Your own
    suite should be determined by your specific use case.

        ssl_ciphers   EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA256:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EDH+aRSA+AESGCM:EDH+aRSA+SHA256:EDH+aRSA:EECDH:!aNULL:!eNULL:!MEDIUM:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS:!RC4:!SEED;

1.  Enable Strict Transport Security by adding the following `add_header`
    directive. This header explicitly instructs web browsers to use HTTPS only:

        add_header Strict-Transport-Security "max-age=31536000";

1.  To improve the performance of your website, you can also enable SSL session
    caching. The following directives enable a shared cache of 15 MB and set a
    cache lifetime of 10 minutes:

        ssl_session_cache shared:SSL:15m;
        ssl_session_timeout 10m;

After you've hardened your configuration, test the configuration for errors and
then reload the NGINX service:

    service nginx configtest && service nginx reload

#### Choose a load balancing method

NGINX load balancing defaults to the **round-robin** method of routing traffic.
This method routes traffic to your backends using round-robin ordering, where
each new request is sent to a different server. In addition, NGINX provides the
following load balancing methods:

* **Least-connected**

    Incoming traffic is sent to the target server with the lowest number of
    active connections.

* **IP Hash**

    Incoming traffic is routed according to hash function that uses the
    client's IP address as input. This method is particularly useful for use
    cases that require [session persistence][session].

[session]: https://www.nginx.com/resources/glossary/session-persistence/

You can substitute the default round-robin method with an alternative method by
adding the appropriate directive to your virtual host's `upstream` block. To use
the least-connected method, add the `least_conn` directive:

    upstream {
      least_conn;
      server 1.2.3.4;
      …
    }

To use the IP hash method, add the ip_hash directive:

    upstream {
      ip_hash;
      server 1.2.3.4;
      …
    }

#### Weight your servers

You can adjust your load balancer to send more traffic to certain servers by
setting server weights. To set a server weight, add a `weight` attribute to the
specific `server` in your `upstream` directive:

    upstream {
      server 1.2.3.4 weight=3
      server 2.3.4.5
      server 3.4.5.6 weight=2
    }

If you use this configuration with the default round-robin load balancing
method, for every six incoming requests, three are sent to `1.2.3.4`, one
is sent to `2.3.4.5`, and two are sent to `3.4.5.6`. The IP hash method
and least-connected method also support weighting.

#### Configure health checks

NGINX automatically performs server health checks. By default, NGINX marks a
server as failed if the server fails to respond within ten seconds. You can
customize the health checks for individual servers by using the `max_fails` and
`fail_timeout` parameters.

    server 1.2.3.4 max_fails=2 fail_timeout=15s

#### Set server state

If you want to set a specific backend server to be used only when the other
servers are unavailable, you can do so by adding the `backup` parameter to the
`server` definition in your `upstream` directive:

    server 1.2.3.4 backup

Similarly, if you know that a server will remain unavailable for an indefinite
period of time, you can set the `down` parameter to mark it as permanently
unavailable:

    server 1.2.3.4 down

## Clean up

After you've finished the NGINX load balancer tutorial, you can clean up the
resources you created on Google Cloud so you won't be billed for them
in the future. The following sections describe how to delete or turn off these
resources.

### Delete the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial.

To delete the project:

Warning:  Deleting a project has the following consequences:

          * If you used an existing project, you'll also delete any other work
            you've done in the project.
          * You can't reuse the project ID of a deleted project. If you created
            a custom project ID that you plan to use in the future, you should
            delete the resources inside the project instead. This ensures that
            URLs that use the project ID, such as an `appspot.com` URL, remain
            available.

          If you are exploring multiple tutorials and quickstarts, reusing
          projects instead of deleting them prevents you from exceeding project
          quota limits.

1.  In the Cloud Console, go to the Projects page:

    [Go to the project page](https://console.cloud.google.com/iam-admin/projects)

1.  In the project list, select the project you want to delete and click Delete
    project:

    ![Nginx load balancing overview](https://storage.googleapis.com/gcp-community/resources/delete-project-screenshot.png)

1.  In the dialog, type the project ID, and then click **Shut down** to delete
    the project.

### Delete your instances

To delete a Compute Engine instance:

1.  In the Cloud Console, go to the VM Instances page:

    [Go to the VM instances page](https://console.cloud.google.com/compute/instances)

1.  Click the checkbox next to your **nginx-lb** instance.

1.  Click the **Delete** button at the top of the page to delete the instance.

### Delete your disks

To delete a Compute Engine disk:

1.  In the Cloud Console, go to the Disks page:

    [Go to the disks page](https://console.cloud.google.com/compute/disks)

1.  Click the checkbox next to the disk you want to delete.

1.  Click the **Delete** button at the top of the page to delete the disk.

## Next steps

### Check out other possible load balancing solutions

Read about other load balancing solutions available on Google Cloud:

* [Network Load Balancing](https://cloud.google.com/compute/docs/load-balancing/network)
* [HTTP(S) Load Balancing](https://cloud.google.com/compute/docs/load-balancing/http)

### Implement a load balancer recovery strategy

Because your NGINX-based load balancer is a single point of failure, you should
implement some method of quickly recovering in the event that it fails. The
[Application recovery][recovery] section of the
[Disaster Recovery Cookbook][cookbook] outlines several possibilities.

[recovery]: https://cloud.google.com/solutions/disaster-recovery-cookbook#application-recovery
[cookbook]: https://cloud.google.com/solutions/disaster-recovery-cookbook
