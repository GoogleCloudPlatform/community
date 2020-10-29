---
title: Zero-to-Deploy with Chef on Google Cloud
description: Learn how to manage Compute Engine with Chef.
author: djmailhot
tags: Compute Engine, Chef
date_published: 2018-06-14
---

David Mailhot | Developer Programs Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows how to quickly set up infrastructure on Google Cloud with the [Chef configuration management
tool](https://www.chef.io/chef/). You will start from nothing and end with
provisioning and configuring multiple resources on Google Cloud using open source Chef cookbooks.

## Objectives

*   Demonstrate an example configuration management workflow using a single
    machine running **[Chef Client](https://docs.chef.io/ctl_chef_client.html)**.
*   Show how to install and use the [Chef Google Cloud cookbooks](https://supermarket.chef.io/cookbooks/google-cloud).

## Before you begin

1.  Create a new Google Cloud project or select an existing one in the **[Cloud Console](https://console.cloud.google.com/project)**.
1.  Enable a [billing account](https://cloud.google.com/billing/docs/how-to/manage-billing-account).
1.  Install the **[Cloud SDK](https://cloud.google.com/sdk/)**.

## Costs

This tutorial uses billable components of Google Cloud, including Compute Engine.

New Google Cloud users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Setup

### Provision a Compute Engine instance

This tutorial is written using the **us-east1-b** Compute Engine zone. You may
choose any zone.

This tutorial is written using the **Ubuntu 16.04 LTS** machine image. You may
use any machine image that supports Chef. See the list of all [supported
distributions for Chef Client](https://downloads.chef.io/chef).

1.  In the Cloud Console, go to the **Compute Engine >> [VM Instances](https://console.cloud.google.com/compute/instances)** page.
1.  Click the **Create Instance** button.
1.  Set **Name** to `chef-workstation`.
1.  For **Zone**, choose **us-east1-b**.
1.  For **Machine type**, choose **f1-micro**.
1.  In the **Boot disk** section, click **Change** to begin configuring your
    boot disk.
1.  In the **Preconfigured image** tab, choose **Ubuntu 16.04 LTS**.
1.  Click **Select** at the bottom of the dialog.
1.  Click the **Create** button at the bottom to create the instance.

You can also use the `gcloud` command instead:

    gcloud compute instances create chef-workstation --machine-type f1-micro \
    --image-family ubuntu-1604-lts --image-project ubuntu-os-cloud \
    --zone us-east1-b

It will take a few moments to create your new instance.

### Download a service account key

You'll need a service account key to authorize Chef to manage your GCP project.

1.  In the Cloud Platform Console, go to **IAM & admin >> [Service
    Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)**.
1.  If prompted, select your Google Cloud project.
1.  Click the **Create Service Account** button.
1.  Set **Name** to `chef-service-account`.
1.  For **Role**, choose **Project** >> **Editor**.
1.  Check the box **Furnish a new private key**.
1.  For **Key type**, select **JSON**.
1.  Click **Create** at the bottom of the dialog.

The service account key should be automatically downloaded to your computer as a
JSON file with a name like `YOUR_PROJECT_NAME-12345678abcdef.json`.

You can also use the `gcloud` command instead:

    gcloud iam service-accounts create chef-service-account --display-name \
    "chef service account"
    gcloud iam service-accounts keys create ~/chef-account-key.json \
    --iam-account chef-service-account@YOUR_PROJECT_NAME.iam.gserviceaccount.com

In this case, the service account key will be downloaded as
`~/chef-account-key.json`.

After your service account key is downloaded, you'll need to upload it to your
new `chef-workstation` Compute Engine instance:

    gcloud compute scp /PATH/TO/SERVICE_ACCOUNT_KEY.json \
    chef-workstation:credentials.json --project YOUR_PROJECT_NAME --zone \
    us-east1-b

### Install Chef client

1.  SSH into your `chef-workstation` instance.

        gcloud compute ssh chef-workstation --zone us-east1-b

1.  Download the chef client package for **Ubuntu 16.04**.

        wget https://packages.chef.io/files/stable/chef/13.8.5/ubuntu/16.04/chef_13.8.5-1_amd64.deb

1.  Install it.

        sudo dpkg -i chef_*

If you selected a different machine image for your Compute Engine
instance, you'll have to [download the correct
package](https://downloads.chef.io/chef) and install it with the appropriate
package manager.

Remain ssh'd into your `chef-workstation` instance.

### Initialize a Chef repository

On your `chef-workstation` instance:

1.  Setup a `cookbooks` directory.

        mkdir -p .chef/cookbooks
        cd .chef

1.  Configure Git.

        git config --global user.email "you@example.com"
        git config --global user.name "Your Name"

    If `git` is not installed, install it:

        sudo apt-get install git

1.  Initialize a Git repo.

        git init
        git commit -m genesis --allow-empty

You should see a message like `[master (root-commit) 7d75bc7] genesis`.

Having at least one commit allows you to start downloading Chef
cookbooks, as you'll do in the next step.

## Configure

### Download the Chef Google Cloud cookbooks

On `chef-workstation`:

1.  Download the [google-cloud
    cookbook](https://supermarket.chef.io/cookbooks/google-cloud) from the
    **[Chef Supermarket](https://supermarket.chef.io/)** via the `knife`
    command.

        knife cookbook site install google-cloud

    `~/.chef/cookbooks` is a default path for the `knife cookbook`
    command. If you want a different path, you'll need to specify it in a custom
    [knife configuration file](https://docs.chef.io/config_rb_knife.html).

When installation finishes, you should see many new directories in the
`cookbooks` directory, such as `google-cloud`, `google-gauth`, etc.

### Write a Chef recipe

On `chef-workstation`:

1.  Create a new recipe directory under the `google-cloud` cookbook.

        mkdir -p cookbooks/google-cloud/recipes

1.  Edit a new recipe file `cookbooks/google-cloud/recipes/default.rb`:

        gauth_credential 'mycred' do
          action :serviceaccount
          path ENV['CRED_PATH'] # e.g. '/path/to/my_account.json'
          scopes [
            'https://www.googleapis.com/auth/compute'
          ]
        end

        gcompute_zone 'us-west1-a' do
          action :create
          project ENV['GCP_PROJECT'] # e.g. 'company-org:chef-gcp-project'
          credential 'mycred'
        end

        gcompute_disk 'instance-test-os-1' do
          action :create
          source_image 'projects/ubuntu-os-cloud/global/images/family/ubuntu-1604-lts'
          zone 'us-west1-a'
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end

        gcompute_network 'mynetwork-test' do
          action :create
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end

        gcompute_region 'us-west1' do
          action :create
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end

        gcompute_address 'instance-test-ip' do
          action :create
          region 'us-west1'
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end

        gcompute_machine_type 'n1-standard-1' do
          action :create
          zone 'us-west1-a'
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end

        gcompute_instance 'instance-test' do
          action :create
          machine_type 'n1-standard-1'
          disks [
            {
              boot: true,
              auto_delete: true,
              source: 'instance-test-os-1'
            }
          ]
          network_interfaces [
            {
              network: 'mynetwork-test',
              access_configs: [
                {
                  name: 'External NAT',
                  nat_ip: 'instance-test-ip',
                  type: 'ONE_TO_ONE_NAT'
                }
              ]
            }
          ]
          zone 'us-west1-a'
          project ENV['GCP_PROJECT']
          credential 'mycred'
        end
    
    This example code is pulled from the [Google Compute Engine Chef
    Cookbook](https://github.com/GoogleCloudPlatform/chef-google-compute).

1.  Set the appropriate environment variables. You can directly inline these
    values in the code; they are parameterized like this for your convenience.

        # The service account key JSON file you uploaded earlier to
        # '~/credentials.json'. However, CRED_PATH requires an absolute path.
        export CRED_PATH='/home/USERNAME/credentials.json'
        export GCP_PROJECT='YOUR_PROJECT_NAME'
   
    Feel free to experiment with more example code from any of the other
    Google Cloud cookbooks. (e.g. the [Google Cloud SQL Chef
    Cookbook](https://github.com/GoogleCloudPlatform/chef-google-sql#example)).

## Deploy

### Run Chef Client

On `chef-workstation`, run `chef-client` in 'local mode' with your recipe:

    chef-client --local-mode --runlist 'recipe[google-cloud::default]'

You should see output streaming by as the command operates. It should terminate
with something like `Chef Client finished, 2/8 resources updated in 35 seconds`.

Awesome! You just provisioned a Compute Engine instance on Google Cloud using a
single machine running Chef Client. You can check the status of your Compute
Engine instance on the **[VM Instances](https://console.cloud.google.com/compute/instances)** page.

## Cleaning up

After you've finished this tutorial, you can clean up the resources you created
on Google Cloud Platform so you won't be billed for them in the future. The
following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial.

To delete the project:

1.  In the Cloud Platform Console, go to the
    **[Projects](https://console.cloud.google.com/iam-admin/projects)** page.
1.  Click the trash can icon to the right of the project name.

**Warning**: Deleting a project has the following consequences:

If you used an existing project, you'll also delete any other work you've done
in the project. You can't reuse the project ID of a deleted project. If you
created a custom project ID that you plan to use in the future, you should
delete the resources inside the project instead. This ensures that URLs that use
the project ID, such as an appspot.com URL, remain available.

### Deleting instances

To delete your Compute Engine instances:

1.  In the Cloud Platform Console, go to the **[VM
    Instances](https://console.cloud.google.com/compute/instances)** page.
1.  Click the checkbox next to the instances named `chef-workstation`,
    `instance-test`, and any other instances you may have provisioned via Chef.
1.  Click the Delete button at the top of the page to delete the instances.

You can use the `gcloud` command instead:

    # Run on your local machine, _not_ the chef-workstation instance.
    gcloud compute instances delete chef-workstation --zone us-east1-b
    gcloud compute instances delete instance-test --zone us-east1-b
    # Repeat with any other instances you may have made.
