---
title: Set up a Puppet master and agent configuration in Compute Engine
description: Learn how to configure Compute Engine instances as a Puppet master and agent, and use a manifest to deploy an application from the master to the agent.
author: ksakib
tags: Puppet, Google Cloud, Compute Engine, Puppet Master, Puppet Agent
date_published: 2018-06-11
---

## Objectives

* Set up the virtual machines
* Install and run Puppet master
* Install Puppet agent and request a certificate from the master
* Sign the certificate to establish communication between the Puppet master and Puppet agent
* Write a manifest for a simple web app and deploy it to the Puppet agent

## Set up the virtual machines

1. Create a small(1 shared vCPU + 1.7 GB memory) Compute Engine instance with the OS Ubuntu 16.04 xenial and with 'Allow HTTP traffic' option checked under Firewall section and name is puppet-agent.

2. Create another Compute Engine instance but this time a with 1 vCPU + 3.75 GB memory with the same OS (Ubuntu 16.04 xenial). Keep the default firewall option. No need to check http or https. Name the instance as puppet-master.

## Install and run Puppet master

1. SSH into the puppet-master instance, then run the following commands to install the Puppet server:

        wget https://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb
        sudo dpkg -i puppetlabs-release-pc1-xenial.deb
        sudo apt-get update
        sudo apt-get install puppetserver

2. Start the Puppet server by running the following command:

        sudo systemctl start puppetserver

3. Make sure the Puppet server has started by running the following command:

        sudo systemctl status puppetserver

You should see a see a line that says "active (running)" in the result.

4. Configure the Puppet server to start at boot by running the following command:

        sudo systemctl enable puppetserver

## Install and run the Puppet agent, and request a certificate from the Puppet master

1. SSH into the puppet-agent instance, then run the following commands to install the Puppet agent:

        wget https://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb
        sudo dpkg -i puppetlabs-release-pc1-xenial.deb
        sudo apt-get update
        sudo apt-get install puppet-agent

2. Before starting Puppet agent, edit the /etc/hosts file to identify the Puppet master to use to request the certificate. At the end of the file, specify the internal IP address of the puppet-master Compute Engine instance, as shown following:

        [PUPPET_MASTER_COMPUTE_ENGINE_INSTANCE_INTERNAL_IP_ADDRESS]      Puppet
You can get the internal IP address of the puppet-master Compute Engine instance from the VM instances page in the GCP console.
3. Run the following commands to run the Puppet agent:

        sudo systemctl start puppet
        sudo systemctl enable puppet

## Sign the certificate to establish communication between the Puppet master and Puppet agent

1. The first time the Puppet agent runs, it sends a certificate signing request to the Puppet master. To list all unsigned certificate requests, run the following command on the puppet-master instance:

        sudo /opt/puppetlabs/bin/puppet cert list

2. We'll use the --all option to sign certificate:

        sudo /opt/puppetlabs/bin/puppet cert sign --all

You can also do a single sign by

        sudo /opt/puppetlabs/bin/puppet cert sign puppet-agent.c.YOUR_PROJECT_ID.internal

## Write a simple webserver module and Manifest that will install Apache2 and write hello world page

1.  On the puppet-master instance, navigate to the folder /etc/puppetlabs/code/environments/production/manifests/, make a manifest file named site.pp, and copy the following code into it:

        node /agent/{
          include webserver
        }

2.  Navigate to the /etc/puppetlabs/code/environments/production/modules directory and make a new directory by running the following command:

        sudo mkdir -p webserver/manifests

3.  In the new manifests directory, create a file named init.pp, and copy the following code into it:

        class webserver {
          package { 'apache2':
           ensure => present
          }
          file {'/var/www/html/index.html': # resource type file and filename
            ensure => present, # make sure it exists
            content => "<h1>This page is installed from Puppet Master</h1>", # content of the file
          }
        }
        
        
4. Run the following command on the puppet-agent instance to get the catalog from the Puppet master and apply the manifest:

        sudo /opt/puppetlabs/bin/puppet agent --test

5. Copy the external IP address of the puppet-agent instance (you can get this from the VM instances page in the GCP console) and paste it into your browser. You should see a web page with the message "This page is installed from Puppet Master". 
