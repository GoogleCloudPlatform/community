---
title: Zero-to-Deploy with Chef on GCP
description: Learn how to manage Google Compute Engine with Chef
author: djmailhot
tags: Compute Engine, Chef
date_published: 2018-03-28
---

This tutorial shows how to quickly setup infrastructure on Google Cloud Platform
with the Chef configuration management tool. Follow this tutorial to configure
resources on GCP using the Chef GCP Cookbooks.

## Objectives

Deploy and configure resources on GCP via Chef

## Before you begin

1. Create a project in the **[Google Cloud Platform Console](https://console.cloud.google.com/project)**.
1. Enable a [billing account](https://cloud.google.com/billing/docs/how-to/manage-billing-account).
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/).

## Costs

This tutorial uses billable components of Cloud Platform, including:

+   Google Compute Engine

New Cloud Platform users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Setup environment

### Provision a Compute Engine instance

For the purposes of this tutorial, the default machine type works fine, so you
don't need to change the default setting.

Chef is supported on most operating systems. See the supported distributions on
the [downloads page for Chef Client](https://downloads.chef.io/chef). For this
tutorial, you'll use Ubuntu Xenial.

1.  In the Cloud Platform Console, go to the **[VM
    Instances](https://console.cloud.google.com/compute/instances)** page.
1.  Click the **Create Instance** button.
1.  Set **Name** to `chef-workstation`.
1.  In the **Machine type** section, choose **f1-micro**.
1.  In the **Boot disk** section, click **Change** to begin configuring your
    boot disk.
1.  In the **Preconfigured image** tab, choose **Ubuntu 16.04 LTS**.
1.  Click **Select** at the bottom.
1.  Click the **Create** button at the bottom to create the instance.

It will take a few moments to create your new instance.

### Download your service account key

You'll use a service account key to authorize Chef to manage your GCP project.

1.  In the Cloud Platform Console, go to the **[Service
    Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)**
    page.
1.  Click the **Create Service Account** button.
1.  Set **Name** to `chef-service-account`.
1.  In the **Role** drop down, select **Project** >> **Owner**.
1.  Check the box **Furnish a new private key**.
1.  Make sure the **Key type** is selected as **JSON**.

The service account key should be automatically downloaded to your computer as a
'.json' file.

Finally, you need to upload your credentials file to your new GCE instance:

```
gcloud compute scp /PATH/TO/CREDENTIALS.json
chef-workstation:credentials.json --project YOUR_PROJECT_NAME --zone
YOUR_ZONE
```

### Install Chef client

Ssh into the chef-workstation instance.

1.  Download the chef client package for Ubuntu 16.04.

        wget https://packages.chef.io/files/stable/chef/13.8.5/ubuntu/16.04/chef_13.8.5-1_amd64.deb

1.  Install it.

        sudo dpkg -i chef_*

NOTE: If you selected a different OS for your GCE instance, you'll have to
[download the correct package](https://downloads.chef.io/chef) and install
it with the appropriate package manager.

## Create configuration

### Download Chef GCP cookbooks

1.  Setup a cookbooks directory.

        mkdir -p chef-repo/cookbooks;  cd chef-repo

1.  Initialize a git repo.

        git init;  git commit -m genesis --allow-empty

1.  Download the google-cloud cookbook.

        knife supermarket install google-cloud

    You should see many new directories in the `cookbooks/` directory, such as
    `google-cloud/`, `google-gauth/`, and `google-gcompute/`.

### Write a Chef recipe

1.  Create a new recipe directory under `google-cloud/`.

        mkdir -p cookbooks/google-cloud/recipes

1.  Edit a new file `cookbooks/google-cloud/recipes/default.rb`.
    Copy the example code from the [Google Cloud SQL Chef
    cookbook](https://github.com/GoogleCloudPlatform/chef-google-sql#example)

        gauth_credential 'mycred' do
          action :serviceaccount
          path ENV['CRED_PATH'] # e.g. '/path/to/my_account.json'
          scopes [
            'https://www.googleapis.com/auth/sqlservice.admin'
          ]
        end

        gsql_instance  "sql-test-#{ENV['sql_instance_suffix']}" do
          action :create
          project 'google.com:graphite-playground'
          credential 'mycred'
        end

        gsql_database 'webstore' do
          action :create
          charset 'utf8'
          instance "sql-test-#{ENV['sql_instance_suffix']}"
          project 'google.com:graphite-playground'
          credential 'mycred'
        end

1.  Change each `project 'google.com:graphite-playground'` line to use your
    project

1.  Set the appropriate environment variables

        export CRED_PATH=/path/to/your/service_account_key.json
        export sql_instance_suffix=example-database

    NOTE: Feel free to use example code from any other GCP cookbook.

## Deploy configuration

Run `chef-client` in 'local mode' with your recipe:

        chef-client --local-mode --override-runlist 'recipe[google-cloud::default]'

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

To delete a Compute Engine instance:

1.  In the Cloud Platform Console, go to the **[VM
    Instances](https://console.cloud.google.com/compute/instances)** page.
1.  Click the checkbox next to your postgres-tutorial instance.
1.  Click the Delete button at the top of the page to delete the instance.
