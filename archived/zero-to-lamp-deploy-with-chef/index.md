---
title: Zero to LAMP deployment on Google Cloud with Chef
description: Learn how to deploy a LAMP stack on Google Cloud with Chef cookbooks.
author: slevenick
tags: Compute Engine, Cloud SQL, Chef
date_published: 2018-12-17
---

Sam Levenick | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

## Objectives

* Create a Chef Workstation on Google Cloud.
* Use the Workstation to create a Compute Engine VM, Cloud SQL instance, firewall rules, and a database with Chef.
* Deploy Apache and PHP on the VM to serve a simple page backed by the database instance.

## Costs

This tutorial uses billable components of Google Cloud, including:

* [Compute Engine][gce]
* [Cloud SQL][csql]

[gce]: https://cloud.google.com/compute/
[csql]: https://cloud.google.com/sql/

Use the [Pricing Calculator][pricing] to generate a cost estimate based on your
projected usage.

[pricing]: https://cloud.google.com/products/calculator

## Before you begin

1. Select or create a [Google Cloud][console] project.
[Go to the projects page][projects].
1. Enable billing for your project. [Enable billing][billing].
1. Install the [Cloud SDK][sdk].
1. Authenticate `gcloud` with Google Cloud.

        gcloud init

[console]: https://console.cloud.google.com/
[projects]: https://console.cloud.google.com/project
[billing]: https://support.google.com/cloud/answer/6293499#enable-billing
[sdk]: https://cloud.google.com/sdk/

You will be executing commands on both a local machine (assuming Mac or Linux-based) and a Compute Engine VM. Command blocks will be prefixed with the bash comment (#) to indicate the correct machine.

## Create a Chef Workstation on a Compute Engine VM

1. The instructions assume you are using either a Mac or Linux-based local machine. Specify default settings for the Cloud SDK. Future gcloud commands will assume you are using this project, region, and zone.

    
        # local-machine
        PROJECT_NAME=your-project-name-here
        gcloud config set project $PROJECT_NAME
        gcloud config set compute/region us-west1
        gcloud config set compute/zone us-west1-a
        gcloud services enable compute.googleapis.com
        gcloud services enable sqladmin.googleapis.com
        gcloud services enable iam.googleapis.com
    

## Create the service accounts that Chef will use

From the original machine:

1.  Create Compute Engine service account
     1. Create a new service account
      
            # local-machine
            gcloud iam service-accounts create chef-workstation
     
     1. Add Compute Engine and Cloud SQL permissions to the account
     
            # local-machine
            gcloud projects add-iam-policy-binding $PROJECT_NAME \            
              --member='serviceAccount:chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com' \
              --role='roles/compute.admin'
            gcloud projects add-iam-policy-binding $PROJECT_NAME \
              --member='serviceAccount:chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com' \
              --role='roles/iam.serviceAccountAdmin'
            gcloud projects add-iam-policy-binding $PROJECT_NAME \
              --member='serviceAccount:chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com' \
              --role='roles/iam.serviceAccountUser'
            gcloud projects add-iam-policy-binding $PROJECT_NAME \
              --member='serviceAccount:chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com' \
              --role='roles/cloudsql.admin'
            gcloud projects add-iam-policy-binding $PROJECT_NAME \
              --member='serviceAccount:chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com' \
              --role='roles/iam.serviceAccountKeyAdmin'

1.  Use gcloud to create a new Compute Engine instance with the service account you just created and ssh to it.

        # local-machine
        gcloud compute instances create chef-workstation \
          --image-family debian-9 --image-project debian-cloud \
          --service-account=chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com \
          --scopes=https://www.googleapis.com/auth/cloud-platform
        gcloud compute ssh chef-workstation

1.  From the chef-workstation machine, install the Chef Workstation and git:

        # gce: chef-workstation
        PROJECT_NAME=$(gcloud compute project-info describe | grep ^name | awk '{print $2}')
        echo "PROJECT_NAME=$PROJECT_NAME" >> ~/.bashrc
        wget https://packages.chef.io/files/stable/chef-workstation/0.1.162/ubuntu/18.04/chef-workstation_0.1.162-1_amd64.deb
        sudo dpkg -i chef-workstation_0.1.162-1_amd64.deb
        sudo apt update
        sudo apt install git -y
        exit

## Create an infrastructure cookbook

1.  Create a cookbooks folder.

        # gce: chef-workstation
        mkdir -p chef-repo/cookbooks
        cd chef-repo/cookbooks

1.  Chef requires a git repository with at least one commit, so set up git and make an initial commit in the cookbooks directory.

        # gce: chef-workstation
        git config --global user.email "youremail@provider.com"
        git config --global user.name "Your Name"
        git init
        git commit -am "Initial Commit" --allow-empty
    

1.  Generate the Chef cookbook to specify your infrastructure.
    
        # gce: chef-workstation
        chef generate cookbook infrastructure
    
1.  Add the dependency on the google-cloud cookbook to the `metadata.rb` file of the cookbook

        # gce: chef-workstation
        echo "depends 'google-cloud', '~> 0.4.0'" >> infrastructure/metadata.rb
    
1.  Install Google Cloud cookbooks from the [supermarket][supermarket] using the knife tool
   
        # gce: chef-workstation
        knife cookbook site install google-cloud -o .
    
1.  Create a copy of your `chef-workstation` service account key on the chef workstation machine. This will be used by the Chef cookbooks you create.

        # gce: chef-workstation
        gcloud iam service-accounts keys create ~/key.json --iam-account=chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com

[supermarket]: https://supermarket.chef.io/cookbooks/google-cloud

## Create Compute Engine cookbook

Use the Chef Google Cloud cookbooks to define your Compute Engine infrastructure. More information on these cookbooks can be found at the [Chef Supermarket.][supermarket]

1.  Create a new recipe within the infrastructure cookbook.

        # gce: chef-workstation
        chef generate recipe infrastructure compute
    
1.  Create the credentials that will be used to communicate with the Compute Engine APIs within the new compute recipe within the infrastructure cookbook.

        gauth_credential 'compute-credentials' do
          action :serviceaccount
          path '/home/$USER/key.json'
          scopes [
            'https://www.googleapis.com/auth/cloud-platform'
          ]
        end

1.  Create a network to build our infrastructure in. This network will contain your Compute Engine instances and allow you to create firewall rules that apply to everything within the network.

        gcompute_network 'web-server-network' do
          action :create
          auto_create_subnetworks true
          project '$PROJECT_NAME'
          credential 'compute-credentials'
        end
        
1.  Add a firewall rule that allows ssh and http traffic for your web server.

        gcompute_firewall 'fw-allow-ssh-http' do
          action :create
          allowed [
            {
              ip_protocol: 'tcp',
              ports: ['22', '80']
            }
          ]
          network 'web-server-network'
          project '$PROJECT_NAME'
          credential 'compute-credentials'
        end
       
1.  Create the Compute Engine instance and static IP address.

        gcompute_address 'web-server-ip' do
          action :create
          region 'us-west1'
          project '$PROJECT_NAME'
          credential 'compute-credentials'
        end

        gcompute_disk 'web-server-os-1' do
          action :create
          source_image 'projects/debian-cloud/global/images/family/debian-9'
          zone 'us-west1-a'
          project '$PROJECT_NAME'
          credential 'compute-credentials'
        end

        gcompute_instance 'web-server' do
          action :create
          machine_type 'n1-standard-1'
          disks [
            {
              boot: true,
              auto_delete: true,
              source: 'web-server-os-1'
            }
          ]
          network_interfaces [
          {
            network: 'web-server-network',
              access_configs: [
                {
                  name: 'External NAT',
                  nat_ip: 'web-server-ip',
                  type: 'ONE_TO_ONE_NAT'
                }
              ]
            }
          ]
          zone 'us-west1-a'
          project '$PROJECT_NAME'
          credential 'compute-credentials'
        end    

1.  Include the Compute Engine recipe to your infrastructure cookbook's default recipe.
   
        # gce: chef-workstation
        echo "include_recipe 'infrastructure::compute'" >> infrastructure/recipes/default.rb
    
## Create Cloud SQL cookbook

Use the `google-gsql` Google Cloud cookbook to define a Cloud SQL instance.

1.  Create a new recipe within the infrastructure cookbook.

        # gce: chef-workstation
        chef generate recipe infrastructure sql
    
1.  Create credentials that will be used for building the Cloud SQL infrastructure.

        gauth_credential 'sql-credentials' do
          action :serviceaccount
          path '/home/$USER/key.json'
          scopes [
            'https://www.googleapis.com/auth/sqlservice.admin'
          ]
        end
    
1.  Define the Cloud SQL instance. To allow access from your webserver you must add the IP address of the web server to the `authorized_networks` field of the instance. The `gcompute_address_ip` function allows you to dynamically find the address of a named static IP address.

        ::Chef::Resource.send(:include, Google::Functions)
        gsql_instance 'sql-instance' do
          action :create
          database_version 'MYSQL_5_7'
          settings({
            tier: 'db-n1-standard-1',
            ip_configuration: {
              authorized_networks: [
                name: 'webapp',
                value: gcompute_address_ip('web-server-ip', 'us-west1', '$PROJECT_NAME', gauth_credential_serviceaccount_for_function('/home/$USER/key.json', ['https://www.googleapis.com/auth/compute']))
              ]
            }
          })
          region 'us-west1'
          project '$PROJECT_NAME'
          credential 'sql-credentials'
        end
    
1.  Define the database and MySQL user to create.

        gsql_database 'my_db' do
          action :create
          charset 'utf8'
          instance "sql-instance"
          project '$PROJECT_NAME'
          credential 'sql-credentials'
        end

        gsql_user 'db_user' do
          action :create
          password 'S3cUr!tY'
          host '%'
          instance 'sql-instance'
          project '$PROJECT_NAME'
          credential 'sql-credentials'
        end
    
1.  Include the Cloud SQL recipe into your infrastructure cookbook's default recipe.
    
        # gce: chef-workstation
        echo "include_recipe 'infrastructure::sql'" >> infrastructure/recipes/default.rb
    
It is important to be sure that the sql cookbook is included after the compute cookbook because the sql cookbook depends on the web server IP address existing.

[supermarket]: https://supermarket.chef.io/cookbooks/google-cloud

## Run the infrastructure cookbook

Now that you have created your infrastructure cookbook, run it on your Chef Workstation to configure your cloud environment.

1.  Run `chef-client` in local mode with the infrastructure cookbook as the run-list.

        # gce: chef-workstation
        chef-client -z -o infrastructure
  
This may take a couple of minutes as it creates the virtual machine and Cloud SQL instance.

## Create a web server cookbook

For the purposes of this tutorial you can download a LAMP cookbook that can be run on Debian 9 [here][cookbook]. This cookbook is adapted from https://learn.chef.io/modules/create-a-web-app-cookbook to work within the context of chef-run and connect to an external MySQL server. Download this cookbook to your Chef Workstation and unzip it within the `cookbooks` directory that you created.

        # gce: chef-workstation
        $USER@chef-workstation:~/chef-repo/cookbooks$ ls
        google-cloud  google-gauth  google-gcompute  google-gcontainer  google-gdns
        google-glogging  google-gsql  google-gstorage  infrastructure  lamp

## Configure the web server cookbook for your environment

1.  Find your Cloud SQL IP address using `gcloud sql instances list` from your original machine.

1.  Modify the `lamp/attributes/default.rb` file to match your environment. Be sure to update `default['lamp']['database']['dbhost'] = '$CLOUD_SQL_IP'` to reference the IP address of your Cloud SQL instance.

## Run the cookbook to configure your web server

Configure your web server machine for ssh access from the Chef Workstation.

1.  Authenticate the Chef Workstation machine to use Compute Engine commands.

        # gce: chef-workstation
        gcloud auth activate-service-account chef-workstation@$PROJECT_NAME.iam.gserviceaccount.com --key-file=key.json

1.  Connect to the `web-server`. This will force the creation of a new SSH key and upload it to the Compute Engine instance.

        # gce: chef-workstation
        gcloud compute ssh web-server --command='exit'

1.  Find the IP address of the web server.

        gcloud compute addresses list
        
1.  Use the [chef-run][chefrun] command to run the `lamp` cookbook on your web server.

        # gce: chef-workstation
        cd ~/chef-repo/cookbooks
        chef-run -i ~/.ssh/google_compute_engine $USER@$WEB_SERVER_IP lamp
    
1.  Verify that the cookbook completed by retrieving the content hosted by the web server.

        # gce: chef-workstation
        curl $WEB_SERVER_IP
    
Or visit `$WEB_SERVER_IP` in your browser. If everything is working it will display a simple HTML table view of your Cloud SQL database.

[cookbook]: https://github.com/slevenick/community/raw/zero-to-lamp-deploy/tutorials/zero-to-lamp-deploy-with-chef/lamp.tgz
[chefrun]: https://www.chef.sh/docs/chef-workstation/getting-started/

## Cleaning up

After you've finished the tutorial, you can clean up the resources you created on Google Cloud so you won't be billed for them in the future. The following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for the tutorial.

To delete the project:

1. In the Cloud Console, go to the **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1. Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done in the project.
You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the future, you should delete the resources inside the project instead. This ensures that URLs that use the project ID, such as an appspot.com URL, remain available.

### Deleting instances

To delete a Compute Engine instance:

1. In the Cloud Console, go to the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.
1. Click the checkbox next to your chef-workstation and web-server instances.
1. Click the Delete button at the top of the page to delete the instances.

### Deleting VPC network

To delete the VPC network you must first delete firewall rules that depend on it:

1. In the Cloud Console, go to the **[Firewall Rules](https://console.cloud.google.com/networking/firewalls)** page.
1. Click the checkbox next to the firewall rules for the `web-server-network` network.
1. Click the Delete button at the top of the page to delete the firewall rules.
1. In the Cloud Console, go to the **[VPC Networks](https://console.cloud.google.com/networking/networks)** page.
1. Click on `web-server-network`.
1. Click the Delete VPC Network button at the top of the page.

### Delete Cloud SQL instance

1. In the Cloud Console, go to the **[Cloud SQL Instances](https://console.cloud.google.com/sql/instances)** page.
1. Click the checkbox next to the SQL instance.
1. Click the Delete button at the top of the page to delete the instance.

### Delete service accounts

1. In the Cloud Console, go to the **[Service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)** page.
1. Click the checkbox next to the `sql` and `compute` accounts.
1. Click the Delete button at the top of the page to delete the service accounts.
