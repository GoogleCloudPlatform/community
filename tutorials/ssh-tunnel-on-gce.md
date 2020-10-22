---
title: Set up an SSH tunnel for private browsing using Compute Engine
description: Learn how to create a homemade VPN to increase your browsing privacy through SSH tunneling.
author: ahmetb
tags: Compute Engine, SSH
date_published: 2017-04-13
---

Ahmet Alp Balkan | Developer Advocate | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

In this tutorial, you will explore how you can use [Compute Engine][gce]
Linux instances to route all your local network traffic with an encrypted SSH
tunnel.

This tutorial is not meant to be used for routing your server application
traffic, but rather to set a VPN-like proxy on your laptop or workstation to
bypass certain network limits, such as censorship, and browse the internet
privately.

This tutorial explores one specific use case of SSH tunnels. For more general 
information about setting up local port forwarding and other SSH tunnels on Google Cloud,
see [Connecting Securely to VM instances](https://cloud.google.com/solutions/connecting-securely).

## Overview

Without any VPN or SSH tunneling, all your internet traffic goes through your
ISP (internet service provider) or any intermediate firewalls your company
network might be enforcing.

Not only your ISP, other parties who can get in the middle can block your
access to websites. They can also inspect and modify the contents of your
requests and responses if your connection is not encrypted. For websites, TLS
(HTTPS) provides end-to-end encryption. However not all websites use TLS and
not all applications use the HTTP/HTTPS protocols.

However, you can host an instance on Compute Engine and use SSH to
create a SOCKS proxy on your machine to make all your traffic go through the
instance.

This way, anyone inspecting your traffic will only see that you are connecting
to the Compute Engine instance, and the Compute Engine instance will forward all of your traffic to its actual
destination smoothly.

This SOCKS proxy provided from the SSH tunnel can later be configured in your
operating system as the default proxy and on other applications which have a
proxy setting.

## Set up the SSH tunnel

First of all, you need a compute instance to route all your traffic through it.
If you have an existing instance, you can use it, or create a new a compute
instance named `tunnel` from Cloud Console or from `gcloud`:

    gcloud compute instances create --zone us-west1-a tunnel

Start an SSH tunnel on your machine on a local port, such as 5000, that
connects to a GCE instance on its SSH port 22:

    gcloud compute ssh --zone us-west1-a tunnel -- -N -p 22 -D localhost:5000

This command works out of the box on macOS, Windows, and Linux, and starts an
SSH tunnel which can be used as a SOCKS proxy. This command will keep running
until it is terminated, which will shut down the tunnel. If you do wish to run
it in the background, pass an additional `-f` flag to the command.

## Set up the proxy

Many operating systems have a system-wide proxy setting. However some
applications, such as browsers, might have their own separate proxy settings.

Once the SSH tunnel is started using the command above, your proxy host is
`localhost` and port is `5000`.

Here are some useful links to configure the proxy in various platforms:

- **Windows:** Follow the “using the SOCKS proxy” section in [this article][win]
  [[mirror][win-a]] to enable it on Internet Explorer, Edge and Firefox.
- **macOS:** System Preferences &rarr; Network &rarr; Advanced &rarr; Proxies
  &rarr; check “SOCKS proxy” and enter the host and the port.
- **Linux:** Most browsers have proxy settings in their Settings/Preferences.
- **Command-line apps:** Many CLIs accept `http_proxy` or `https_proxy`
  environment variables or arguments you can set the proxy. Consult the help or
  the manpage of the program.

**Privacy note:** Even though you use this solution, the DNS queries your
machine will make can still reveal the websites you visit to someone
intercepting your traffic. Consider using [DNSCrypt] to encrypt your DNS
traffic.

## Validate

You can visit [whatismyip.net](https://www.whatismyip.net/) with the proxy
enabled and disabled to see if your IP address (and resolved location) is
changing to see if the proxy is activated on your browser.

You can also use `curl` to see if your location is changed:

```sh
$ curl https://api.ip2geo.pl/json/
{"db":"MaxMind","country":"US","city":"Seattle","lat":"47.6738","lon":"-122.3419"}

$ curl --proxy socks5://localhost:5000 https://api.ip2geo.pl/json/
{"db":"MaxMind","country":"US","city":"Mountain View","lat":"37.4192","lon":"-122.0574"}
```

## Clean up

Once you are done using the SSH proxy, you can terminate `gcloud compute ssh`
command with Ctrl+C.

If you are no longer planning to use the instance serving the proxy, you can
delete the instance using the following command to prevent unwanted charges to
incur:

    gcloud compute instances delete --zone us-west1-a tunnel

[gce]: https://cloud.google.com/compute/
[win]: https://www.ocf.berkeley.edu/~xuanluo/sshproxywin.html
[win-a]: https://web.archive.org/web/20160609073255/https://www.ocf.berkeley.edu/~xuanluo/sshproxywin.html
[DNSCrypt]: https://dnscrypt.org/
