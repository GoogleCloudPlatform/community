---
title: Integrate private Forseti Security with Cloud Security Command Center
description: Deploy private Forseti Security scanning tool with integration with Cloud Security Command Center.
author: fawix,valavan007
tags: Forseti Security, Cloud Security Command Center
date_published: 2019-05-31
---

Note: This guide has been updated for the new installation process using Terraform. The Python installation script
used in the previous version of this tutorial is no longer supported. However, you can still find the old installation 
procedure
[here](https://github.com/GoogleCloudPlatform/community/blob/987cff06da9c17ff34765a9ce5aa48b3623d64d6/tutorials/private-forseti-with-scc-integration/index.md).

This guide walks you through a private Forseti Security installation on Compute Engine, following enterprise best practices.

This guide shows how to do the following:

- Deploy Forseti in its own virtual private cloud (VPC), not the default VPC.
- Restrict the firewall rules that are preconfigured.
- Optionally, remove the public IP address from Compute Engine instances.
- Configure Cloud SQL to be a private instance.
- Configure Forseti to send violations to Cloud Security Command Center (Cloud SCC).

This guide does *not* show how to do the following:

- Customize Forseti.
- Configure Forseti beyond the basic setup.
- Configure Forseti Enforcer.

This guide was developed using Forseti version 2.24.0 (release v5.1.0).

### Prerequisites

To perform the steps in this tutorial, you need the following:

- Access to a G Suite or Cloud Identity super admin account.
- Access to the  **Security** page in the [Google Admin console](https://admin.google.com).
- Access to the [Google Cloud Platform (GCP) Console](https://console.cloud.google.com).
- Rights to modify IAM permissions at the Organization level.
- A project where you will deploy Forseti. In this tutorial, we use the project name `forseti`.
- Editor or owner permissions for the `forseti` project.

Software that you need:

- [Terraform 0.12.12](https://www.terraform.io/downloads.html) or higher
- [Cloud SDK](https://cloud.google.com/sdk/install)


### Installing Forseti

You have two options when following this tutorial:

*   (Recommended) Clone the installer repository into your local workspace:

    [Forseti Security: Terraform Google Installer](https://github.com/forseti-security/terraform-google-forseti)

    For a stable build, select the latest `module-release` branch.

*   Use a temporary shell workspace managed by Google:

    <a href="https://console.cloud.google.com/cloudshell/open?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fforseti-security%2Fterraform-google-forseti.git&amp;cloudshell_git_branch=modulerelease510&amp;cloudshell_working_dir=examples/install_simple&amp;cloudshell_image=gcr.io%2Fgraphite-cloud-shell-images%2Fterraform%3Alatest&amp;cloudshell_tutorial=.%2Ftutorial.md"><img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Open in Google Cloud Shell"></a>
    
    If you use the Cloud Shell option, be sure to back up your `terraform.tfvars` file at the end of the session.

Regardless of which option you choose for the working environment, the steps below are the same. When the steps below
refer to your *shell session*, this refers to whichever choice of environment you made above.

#### Preparing the GCP environment

If you do not have a dedicated `forseti` project yet, then create one. Navigate to the project
[**Home** page](https://console.cloud.google.com/home/dashboard) and take note of the Project ID information displayed in
the **Project info** panel.

In the `forseti` project, do the following:

1.  Go to the [**VPC Networks** page](https://console.cloud.google.com/networking/networks/list) in the Cloud Console.
1.  Create a VPC for Forseti with one subnet. Configure it with the following parameters:
       - **Private Google access**: **On**
       - **Flow logs**: **On** (optional)
       - **Dynamic routing mode**: **Regional** ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/f4ab14ea.png)

    In the example above, the VPC was created with the name `forseti` and the subnet with the name `forseti-subnet1`. The
    chosen region is `us-east4`. The chosen zone is `us-east4-a`. During this step, record the network, subnet, and region
    names; you will use them in later steps.

1.  Remove the default network.
1.  Open your shell session and confirm that you have the required software installed:

        terraform -v && gsutil -v && gcloud -v

    Sample output:

        Terraform v0.12.16
        gsutil version: 4.46
        Google Cloud SDK 272.0.0

1.  Before the next step, run `gcloud auth list` to ensure that your shell session is authenticated.

    If your shell session is not yet authenticated, then use the `gcloud auth login` command to authenticate.
    
1.  In your shell, run the following commands to set the configuration context for `gcloud`:

        gcloud config set project [PROJECT_ID]
        gcloud config set compute/region [REGION_NAME]
        gcloud config set compute/zone [ZONE_NAME]

    In our example:

        gcloud config set project forseti-project-id
        gcloud config set compute/region us-east4
        gcloud config set compute/zone us-east4-a

#### Run a helper script to create a service account and enable APIs

Before you can run the Terraform module, you must create a service account and enable specific APIs. The Forseti installer
has a helper script that uses `gcloud` for this purpose.

1.  Navigate to `terraform-google-forseti/helpers`.

1.  Run the `setup.sh` script:

        ./setup.sh -p [PROJECT_ID] -o [ORGANIZATION_ID]

    To [find your Organization ID](https://cloud.google.com/resource-manager/docs/creating-managing-organization#retrieving_your_organization_id),
    you can use the `gcloud organizations list` command. You will need the Organization ID for subsequent steps, too.
    
    This step creates a `credentials.json` file in the `helpers` folder, which you will need in a later step. This file
    is removed at the end of the installation procedure.

#### Prepare the Terraform environment

1.  Move the `credentials.json` file to the `terraform-google-forseti/examples/install_simple` folder and navigate to that 
    folder:

        # from the helpers folder
        mv credentials.json ../examples/install_simple
        cd ../examples/install_simple
        
    For details, see the
    [installation documentation](https://github.com/forseti-security/terraform-google-forseti/tree/master/examples/install_simple).

1.  Open the `terraform.tfvars` file with a text editor. This file contains the input provided to the Terraform module.

    The default `terraform.tfvars` file looks like the following:

        project_id = "my-project-id"
        org_id     = "11111111"
        domain     = "mydomain.com"
        region     = "us-east4"

        network         = "default"
        subnetwork      = "default"
        network_project = ""

        gsuite_admin_email      = "admin@mydomain.com"
        sendgrid_api_key        = ""
        forseti_email_sender    = ""
        forseti_email_recipient = ""

1.  Configure the file as follows:

    -   Configure `project_id` with your project ID.
    -   Configure the `org_id` with your Organization ID.
    -   Configure the `domain` with your organization's domain.
    -   Configure network and subnetwork and region with the information you recorded when creating the network. In this
        example it's `forseti`, `forseti-subnet1` and `us-east4` respectively.

    If your organization is set up to use shared networks, you can instead use a network in your host project and
    populate the `network_project` accordingly. Typically, because the Forseti toolset should be contained to GCP, an
    isolated project/network combination is appropriate. Also note that in this case you would need to pass the `-f` flag
    to the helper script in the previous section.

1.  Add the following line to the end of the `terraform.tfvars` file:

        private = true

1.  Your file should look like the following:

        project_id = "forseti-project-id"
        org_id     = "111111111111"
        domain     = "example.com"
        region     = "us-east4"

        network         = "forseti"
        subnetwork      = "forseti-subnet1"
        network_project = ""

        gsuite_admin_email      = "admin@example.com"
        sendgrid_api_key        = ""
        forseti_email_sender    = ""
        forseti_email_recipient = ""

        private = true

1.  If you plan to use the SendGrid email service, ensure that you obtain an API key and configure the `sendgrid_api_key`, 
    `forseti_email_sender`, and `forseti_email_recipient`. We recommend that you use a group alias as the email recipient.

1.  Create a bucket to store the Terraform state. The bucket name must be unique. In this tutorial, we use the project ID
    as the bucket name, but you can use any unique name.

        PROJECT=`gcloud config list --format 'value(core.project)'`
        gsutil mb gs://$PROJECT-tfstate

    Take note of the bucket name for subsequent use.

    Note: If your organization already uses Terraform, you can use the same backend as your other Terraform scripts,
    with a separate folder for the Forseti installation.

1.  Open the `backend.tf` file with a text editor. The default contents should look like the following:

        # terraform {
        #   backend "gcs" {
        #     bucket  = "my-project-tfstate"
        #     prefix  = "terraform/forseti"
        #   }
        # }

1.  Uncomment the block above, and populate the `bucket` value with the bucket name from the previous step. The prefix is
    the folder in which the state will be saved within the bucket. The updated file should look like the following:

        terraform {
            backend "gcs" {
                bucket  = "[PROJECT_ID]-tfstate"
                prefix  = "terraform/forseti"
            }
        }

#### Running the installer module

With the prerequisite work done, you can install Forseti.

1.  Initialize and download the required modules:

        terraform init

1.  Run the installer module:

        terraform apply

At the time of this writing, there is a bug when running with Terraform higher than version `0.12.12` that causes
the following error: `tls_private_key.policy_library_sync_ssh is empty tuple`
([more info](https://github.com/forseti-security/terraform-google-forseti/issues/367)). To work around this issue, open the
`main.tf` file and add the following line after the private lines in the module definition:
`policy_library_sync_enabled = true`. After this modification, the module will look like the following:

    module "forseti-install-simple" {
        source  = "terraform-google-modules/forseti/google"
        version = "~> 5.0.0"

        [... REDACTED for brevity ... ]

        client_private = var.private
        server_private = var.private

        policy_library_sync_enabled = true
    }

You may see other warnings, such as `Warning: Quoted references are deprecated` or `Warning: Interpolation-only expressions 
are deprecated`. These do not affect the installation, and you should be able to proceed with the installation as expected.

### Making Forseti private

At this stage, Forseti is installed, but it is not yet fully private. In this section, you make Forseti
private.

In the Cloud Console, ensure that you have the `forseti` project selected, and then do the following:

1.  Go to the [**Cloud SQL** page](https://console.cloud.google.com/sql) in the Cloud Console.
1.  Find the row for the `forseti-server-db` instance, click the more icon (three dots) at the end of the row, and then
    click **Edit**. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/5dacd607.png)

1.  Add the private IP address, remove the public IP address, and save the changes. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/fed98394.png)

    Note: This is also a good time to ensure that the database is in the same zone as the server VM (optional).

1.  Go to the [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) and edit the rules of
    both `forseti-client-allow-ssh-external` and `forseti-server-allow-ssh-external` to restrict the source IP ranges to
    the locaton (on-premises or datacenter range) that you will be connecting
    from. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/58b996ae.png)

1.  (Optional) Go to the [**VM instances** page](https://console.cloud.google.com/compute/instances) and verify that there
    is no public IP addresses for the server and client VMs; since we set the `private` flag to true, this should be 
    properly configured.

    If you remove the public IP addresses, then connections to the instances must be through Cloud Identity-Aware Proxy
    (IAP), Cloud VPN, or Cloud Interconnect. Cloud IAP provides Google Identity verified proxy tunnel to compute instances
    without internet access. For details on how to set up Cloud IAP to access a Forseti VM through SSH, see
    the [Cloud IAP documentation](https://cloud.google.com/iap/docs/using-tcp-forwarding#ssh_tunneling).

### Configuring Forseti

In this section, you perform the base configuration to get Forseti up and running.

#### Enable domain-wide delegation

Important: You must be logged in with the super admin account for the steps in this section.

For details of domain-wide delegation, see
[Enable domain-wide delegation in G Suite](https://forsetisecurity.org/docs/latest/configure/inventory/gsuite.html) in
the Forseti documentaton.

1.  Navigate to [**IAM & admin > Service Account** page](https://console.cloud.google.com/iam-admin/serviceaccounts) on the `forseti` project.
1.  Find the `Forseti Server` service account, click the more icon (three dots), and then click **Edit**. Note the service
    account address for use in the next
    section. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/c23aed4f.png)

1.  Click the checkbox to select **Enable G Suite Domain-wide Delegation**. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/96628a59.png)

1.  Click **View Client ID**. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/42fa4d69.png)

1.  Copy the value from the **Client ID** field and save it for the next step. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/249d1377.png)

    You can also copy the client ID from the **Edit** page if you are unable to copy it from the popover that displays
    the information.

1.  In the Google Admin Console, go to [Manage API client access](https://admin.google.com/ManageOauthClients)
    in **Security Settings**, and paste the client ID in the client name box.
1.  Authorize the following scopes: `https://www.googleapis.com/auth/admin.directory.group.readonly,https://www.googleapis.com/auth/admin.directory.user.readonly,https://www.googleapis.com/auth/cloudplatformprojects.readonly,https://www.googleapis.com/auth/apps.groups.settings`

#### Enable Cloud SCC with Forseti plugin

1.  In the Forseti project, go to [**API & Services > Library** page](https://console.cloud.google.com/apis/library),
    search for the Cloud Security Command Center API (`securitycenter.googleapis.com`), and enable it.
    
1.  Navigate to the Organization level.

1.  Use the menu in the upper-left corner of the Cloud Console to navigate to **Security > Security Command Center**.

1.  Enable the service.

1.  At the top of the **Security Command Center** page, click **Add Security Sources**.

1.  Select the **Forseti Cloud SCC Connector** plugin.

1.  Click the **Visit Forseti Security to sign up** button to get started.

1.  Follow the steps to enable the extension. First, select your organization.

1.  Follow the instructions on the screen. When asked for a service account, use the Forseti Server service account.
    Choose the `forseti` project. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/forseti_source_id_2.png)

1.  Copy the `source_id` for later use. The `source_id` is in this format, as shown in the screenshot
    above: `organizations/[ORGANIZATION_ID]/sources/[SOURCE_ID]`

1.  Navigate to the Organization IAM page and ensure that the service account has
    the **Security Center Findings Editor** role.

    Note: If you did not re-use the Forseti Server service account and created a new service account for Cloud SCC, you
    need to grant **Security Center Findings Editor** role for both the Foresti Server service acconut and the newly created
    service account for Cloud SCC.

#### Configuring the CSCC integration in Forseti

Now you can edit the Terraform files to enable CSCC integration.

1.  Ensure that you are in the `terraform-google-forseti/examples/install_simple` folder for the next steps.

1.  Add  the following line to the bottom of the `terraform.tfvars` file:

        cscc_violations_enabled = "true"
        cscc_source_id = "organizations/[ORGANIZATION_ID]/sources/[SOURCE]"

    The `cscc_source_id` is the value of `source_id` that you copied in the previous section.

1.  Your file should look like the following:

        project_id = "forseti-project-id"
        org_id     = "111111111111"
        domain     = "example.com"
        region     = "us-east4"

        network         = "forseti"
        subnetwork      = "forseti-subnet1"
        network_project = ""

        gsuite_admin_email      = "admin@example.com"
        sendgrid_api_key        = ""
        forseti_email_sender    = ""
        forseti_email_recipient = ""

        private = true
        cscc_violations_enabled = "true"
        cscc_source_id = "organizations/[ORGANIZATION_ID]/sources/[SOURCE]"

1.  To tell the module how to to use the values set in the previous steps, you edit the `variables.tf` and `main.tf` files.

    Add the following to the bottom of the `variables.tf` file:

        variable "cscc_violations_enabled" {
          description = "enables integraton with Cloud Security Command Center"
          type = bool
          default = false
        }

        variable "cscc_source_id" {
          description = "Source ID to be used in the Cloud Security Command Center configuration"
          default = ""
        }

    In the `main.tf` file, find the `module "forseti-install-simple"` line; this is a code block surrounded by `{}`. Inside
    this code block, add the following lines:

        cscc_violations_enabled = var.cscc_violations_enabled
        cscc_source_id = var.cscc_source_id

    After the modification, the module will look like the following:

        module "forseti-install-simple" {
            source  = "terraform-google-modules/forseti/google"
            version = "~> 5.0.0"

            [... REDACTED for brevity ... ]

            client_private = var.private
            server_private = var.private

            cscc_violations_enabled = var.cscc_violations_enabled
            cscc_source_id = var.cscc_source_id
        }

1.  Run `terraform apply` again:

        terraform apply

#### Validate the configuration

To validate that the configuration was properly applied, do the following:

1.  List the buckets:

        gsutil ls

1.  Find the `forseti-server` bucket.

1.  View the relevant part of configuration file:

        gsutil cat gs://forseti-server-[id]/configs/forseti_conf_server.yaml | grep cscc -A6

    The output should look similar to the following:

        cscc:
            enabled: true
            # Cloud SCC uses a source_id. It is unique per
            # organization and must be generated via a self-registration process.
            # The format is: organizations/ORG_ID/sources/SOURCE_ID
            source_id: organizations/[ORGANIZATION_ID]/sources/[SOURCE]

For further validation, you can trigger a notification manually and verify that it shows up in the Security Command Center 
page:

1.  Use SSH to connect to the Forseti server VM: `forseti-server-vm`.

1.  Reload the server configuration:

        forseti server configuration reload gs://forseti-server-[id]/configs/forseti_conf_server.yaml

1.  Create an inventory:

        forseti inventory create

    At the end of this step, the output gives an inventory ID; copy it for the next step.

        {
          "errors": 0,
          "warnings": 31,
          "step": "bucket/test-function-http-tpc6nm6zh2",
          "finalMessage": false,
          "lastError": "",
          "id": "1556128018126591", # <== This is the inventory ID.
          "lastWarning": ""
        }

    Sometimes the installation procedure does not complete as expected, in which case the VM might give the following error: 

        forseti: command not found

    If you receive this error, you have three options:

      - Restart the Forseti Server VM, because a
        [known issue](https://github.com/forseti-security/forseti-security/issues/2232) might have prevented the process
        from starting correctly.
      - Destroy the installation, ensure that the project is clean, and run `terraform apply` again.
      - Follow the steps detailed
        [here](https://forsetisecurity.org/docs/latest/develop/dev/setup.html#setting-up-a-local-environment) in the Forseti
        Server VM to install it locally.

1.  Create a model based on the inventory, and configure Forseti to use it:

        forseti model create --inventory_index_id [INVENTORY_ID] [MODEL_NAME]
        forseti model use [MODEL_NAME]

1.  Run Forseti Scanner:

        forseti scanner run

1.  Run Forseti Notifier:

        forseti notifier run

1.  Check the output for any violations.

1.  Validate that the Forseti violations are shown as findings in the Cloud Security Command Center page. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/0a78fb27.png)

## Conclusion

This gives you a production-ready base intallation of Forseti. However, it's important to note that you still need to create
an organizaton-specific configuration. Typically, you need to refine the base rules to remove the noise and catch
use-cases that are specific to your organization (for example, allow firewall rules opening SSH and RDP traffic only
for your defined IP ranges).

See the Forseti documentation on
[how to create your own rules](https://forsetisecurity.org/docs/latest/configure/scanner/rules.html).
