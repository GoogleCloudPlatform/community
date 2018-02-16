---
title: Set up a Puppet Master Agent Configuration in Compute Engine
description: Learn how to configure Compute Engine instances as a Puppet master and agent, and use a manifest deploy an application from the master to the agent.
author: ksakib
tags: Puppet, Google Cloud, Compute Engine, Puppet Master, Puppet Agent
date_published: 2018-02-11
---

## Objectives

* Set up the virtual machines
* Install and run Puppet Master server
* Install Puppet Agent and request a certificate from Master
* Sign the certificate to establish communication between the Puppet master and Puppet agent
* Write a manifest for a simple web app and deploy it to the Puppet agent

## Set up the virtual machines

1. Create a small(1 shared vCPU + 1.7 GB memory) Compute Engine instance with the OS Ubuntu 16.04 xenial and with 'Allow HTTP traffic' option checked under Firewall section and name is puppet-agent.

2. Create another Compute Engine instance but this time a with 1 vCPU + 3.75 GB memory with the same OS (Ubuntu 16.04 xenial). Keep the default firewall option. No need to check http or https. Name the instance as puppet-master.

## Install and run Puppet Master server

1. SSH into the puppet-master and run the following commands to install puppet into the puppet-master

        wget https://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb
        sudo dpkg -i puppetlabs-release-pc1-xenial.deb
        sudo apt-get update
        sudo apt-get install puppetserver

2. Start the server by

        sudo systemctl start puppetserver

3. Make sure puppet server is running by

        sudo systemctl status puppetserver

We should see a line that says "active (running)"

4. Now that we've ensured the server is running, we can configure it to start at boot by

        sudo systemctl enable puppetserver

## Install Puppet Agent and request a certificate from Master

1. Now SSH in to the puppet agent and run the following commands to install puppet into puppet-Agent

        wget https://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb
        sudo dpkg -i puppetlabs-release-pc1-xenial.deb
        sudo apt-get update
        sudo apt-get install puppet-agent

2. Before starting Puppet Agent we want to make sure that it knows the Puppet Master address to request the certificate. To do that we will edit the        /etc/hosts file. At the end of the file, specify the Puppet master server as follows:

        Puppet_Master_Compute_Engine_Instance_Internal_IP_Adress      Puppet

3. Now run the following Commands to run the Puppet agent

        sudo systemctl start puppet
        sudo systemctl enable puppet

## Sign the certificate to establish a communication

1. The first time Puppet runs on an agent node, it sends a certificate signing request to the Puppet master. To list all unsigned certificate requests, run the following command on the Puppet master.

        sudo /opt/puppetlabs/bin/puppet cert list

2. We'll use the --all option to sign certificate:
        sudo /opt/puppetlabs/bin/puppet cert sign --all

You can also do a single sign by
        sudo /opt/puppetlabs/bin/puppet cert sign puppet-agent.c.YOUR_PROJECT_ID.internal

## Write a simple webserver module and Manifest that will install Apache2 and write hello world page

1. In the puppet-master, go to folder /etc/puppetlabs/code/environments/production/manifests/ and make a manifest file site.pp as

        node /agent/{
          include webserver
        }

2. Now go to modules directory by
        cd /etc/puppetlabs/code/environments/production/modulesand

then make a directory by
        sudo mkdir -p webserver/manifests

3. In the above manifests directory create a file init.pp as
        class webserver {
          package { 'apache2':
          ensure => present
        }
        file {'/var/www/html/index.html': # resource type file and filename
          ensure => present, # make sure it exists
          content => "<h1>This page is installed from Puppet Master</h1>", # content of the file
        }
      }
4. Run the following command in the Puppet Agent to get the Catalog from the Puppet Master to apply the manifest.

5. Copy and Paste the external IP of the Puppet Agent in your browser. We should see simple web page with a message: This page is installed from Puppet Master 
