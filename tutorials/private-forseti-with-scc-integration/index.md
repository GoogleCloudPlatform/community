---
title: Integrate private Forseti Security with Cloud Security Command Center
description: Deploy private Forseti Security scanning tool with integration with Cloud Security Command Center.
author: fawix,valavan007
tags: Forseti Security, Cloud Security Command Center
date_published: 2019-05-31
---

This guide walks you through a private Forseti Security installation, following enterprise best practices.

This guide shows how to do the following:

- Deploy Forseti in its own VPC (not the default VPC).
- Restrict the firewall rules that are pre-configured.
- Optionally, remove the public IP address from Compute Engine instances.
- Configure Cloud SQL to be a private instance.
- Configure Forseti to send violations to Cloud Security Command Center (Cloud SCC).

This guide does *not* show how to do the following:

- Customize Forseti.
- Configure Forseti beyond the basic setup.
- Configure Forseti Enforcer.

This guide was developed using Forseti version 2.14.1.

### Prerequisites

To perform the steps in this tutorial, you need the following:

- Access to a G Suite or Cloud Identity super admin account.
- Access to the  **Security** page in the [Google Admin console](https://admin.google.com).
- Access to the [Google Cloud Platform (GCP) Console](https://console.cloud.google.com).
- Rights to modify IAM permissions at the Organization level.
- A project where you will deploy Forseti. In this guide, we'll use the project name `forseti`.
- Editor or owner permissions for the `forseti` project.

Note: Because of a [bug in the Forseti installer](https://github.com/forseti-security/forseti-security/issues/2759),
you must choose a zone that ends with `-c` (for example,`us-east4-c`) when you define the region and zone where you want to
install Forseti.

### Installing Forseti

In the `forseti` project, do the following:

1.  Go to the [**VPC Networks** page](https://console.cloud.google.com/networking/networks/list) in the GCP Console.
1.  Create a VPC for Forseti with one subnet. Configure it with the following parameters:
       - **Private Google access**: **On**
       - **Flow logs**: **On** (optional)
       - **Dynamic routing mode**: **Regional** ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/f4ab14ea.png)

    In the example above, the VPC was created with the name `forseti` and the subnet with the name `forseti-subnet1`. The
    chosen region is `us-east4`. The chosen zone is `us-east4-c`. During this step, record the network, subnet, and region
    names; you will use them in later steps.

1.  Remove the default network, unless it's being used by other resources.
1.  Open Cloud Shell and configure the gcloud session; these settings will be used by the Forseti installer:

        gcloud config set project [PROJECT_ID]
        gcloud config set compute/region [REGION_NAME]
        gcloud config set compute/zone [ZONE_NAME]
    
    For example, these are the commands using the values from the example above:

        gcloud config set project forseti-pj-id
        gcloud config set compute/region us-east4
        gcloud config set compute/zone us-east4-c

1.  Clone the Forseti repository, which contains the installer that we will use:

        git clone https://github.com/GoogleCloudPlatform/forseti-security.git

1.  Install Forseti and make it use the network that we created. (If you plan to use the SendGrid email service, ensure 
    that you obtain an API key before proceeding, because it will ask you during this step.)

        cd forseti-security
        python install/gcp_installer.py /
        --vpc-host-network [NETWORK_NAME] /
        --vpc-host-subnetwork [SUBNETWORK_NAME] /
        --gsuite-superadmin-email [SUPER_ADMIN_ACCOUNT] /
        --cloudsql-region [REGION_NAME] /
        --gcs-location [REGION_NAME]

    For `[REGION_NAME]`, use the region that you created the subnetwork on.
    
    For example, these are the commands using the values from the example above:

        cd forseti-security
        python install/gcp_installer.py /
        --vpc-host-network forseti /
        --vpc-host-subnetwork forseti-subnet1 /
        --gsuite-superadmin-email [SUPER_ADMIN_ACCOUNT] /
        --cloudsql-region us-east4 /
        --gcs-location us-east4

    With this step, you are essentially running Deployment Manager to create the components necessary to install Forseti.
    You can follow the installation on the [**Deployments** page](http://console.cloud.google.com/dm/deployments) as well as
    the command line.

    Note: In this step, the Forseti installer will try to remove the default firewall rules. Because we removed the
    default VPC network, this step will cause an error in the installation.

### Making Forseti private

At this stage, Forseti is installed, but it is not yet configured as private. In this section, you make Forseti 
private.

In the GCP Console, ensure that you have the `forseti` project selected, and then do the following:

1.  Go to the [**Cloud SQL** page](https://console.cloud.google.com/sql) in the GCP Console.
1.  Find the row for the `forseti-server-db` instance, click the more icon (three dots) at the end of the row, and then
    click **Edit**. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/5dacd607.png)

1.  Add the private IP address, remove the public IP address, and save the changes. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/fed98394.png)

    Note: This is also a good time to ensure that the database is in the same zone as the server VM (optional).

1.  Go to the [**Firewall rules** page](https://console.cloud.google.com/networking/firewalls/list) and edit the rules of
    both `forseti-client-allow-ssh-external` and `forseti-server-allow-ssh-external` to restrict the source IP ranges to
    the locaton (on-premises or datacenter range) that you will be connecting
    from. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/58b996ae.png)

1.  (Optional) Go to the [**VM instances** page](https://console.cloud.google.com/compute/instances) and remove the public
    IP addresses for the server and client VMs. 
    
    If you remove the public IP addresses, then connections to the instances must be through Cloud Identity-Aware Proxy 
    (IAP), Cloud VPN, or Cloud Interconnect. Cloud IAP provides Google Identity verified proxy tunnel to compute instances 
    without internet access. For details on how to set up Cloud IAP to access a Forseti VM through SSH, see
    the [Cloud IAP documentation](https://cloud.google.com/iap/docs/using-tcp-forwarding#ssh_tunneling).

### Configuring Forseti

In this section you will perform the base configuration to get Forseti up and running.

#### Enable domain-wide delegation

Important: You must be logged in with the super admin account for the steps in this section.

For details of domain-wide delegation, see
[Enable domain-wide delegation in G Suite](https://forsetisecurity.org/docs/latest/configure/inventory/gsuite.html) in
the Forseti documentaton.

1.  Navigate to the Service account page on the `forseti` project.
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
1.  Use the menu in the upper-left corner of the GCP Console to navigate to **Security > Security Command Center**.
1.  Enable the service.
1.  At the top of the **Security Command Center** page, click **Add Security Sources**.

1.  Select the **Forseti Cloud SCC Connector** plugin.

1.  Click the **Visit Forseti Security to sign up** button to get started.

1.  Follow the steps to enable the extension. First, select your organization.

1.  Follow the instructions on the screen. When asked for a service account, use the Forseti Server service account.
    Choose the `forseti` project. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/forseti_source_id_2.png)

1.  Copy the `source_id` for later use. The `source_id` is in this format, as shown in the screenshot
    above: `organizations/[ORGANIZATION_ID]/sources/[SOURCE_ID]`

1.  Navigate to the Organization IAM page and ensure the service account was granted
    the **Security Center Findings Editor** role, if not then grant it.

    Note: If you did not re-use the Forseti Server service account and created a new service account for Cloud SCC, you
    need to grant `Security Center Findings Editor` role for both the Foresti Server service acconut and the newly created 
    service account for Cloud SCC.

#### Editing the Forseti configuration file and running Forseti

Go back to Cloud Shell, ensure you are in the `forseti` project, and perform the following steps:

1.  List the buckets:

        gsutil ls

1.  Find the `forseti-server` bucket.

1.  Copy the configuration file from Cloud Storage to Cloud Shell:

        gsutil cp gs://forseti-server-[id]/configs/forseti_conf_server.yaml .

1.  Click the pencil icon to open the editor. ![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/011b3934.png)

1.  Modify the `notifier: violation: cscc` section of the configuration as follows:

        violation:
          cscc:
            enabled: true
            # Cloud SCC uses a source_id. It is unique per
            # organization and must be generated via a self-registration process.
            # The format is: organizations/ORG_ID/sources/SOURCE_ID
            source_id: [paste_value_from_prior_step]
            # Added the following fields:
            mode: api
            organization_id: organizations/[ORG_ID]

1.  Upload the modified file to the bucket:

        gsutil cp forseti_conf_server.yaml gs://forseti-server-[id]/configs/forseti_conf_server.yaml
 
1.  Use SSH to connect to the Forseti server VM: forseti-server-vm.

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
