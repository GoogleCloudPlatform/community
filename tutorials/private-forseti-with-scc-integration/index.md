---
title: Private Forseti with SCC integration
description: Deploy Private Forseti Security scanning tool with integration with Cloud Security Command Center.
author: fawix,valavan007
tags: Forseti Security, Cloud Security Command Center
date_published: 2019-05-25
---

This guide walks you through a private Forseti installation, following enterprise best practices.

This guide shows how to do the following:
- Deploy Forseti in its own VPC (not the default VPC).
- Restrict the firewall rules that are pre-configured.
- Optionally, remove the public IP from Compute Engine instances.
- Configure Cloud SQL to be a private instance.
- Configure Forseti to send violations to Cloud Security Command Center (Cloud SCC).

This guide does **not** show how to do the following:
- Customize Forseti.
- Configure Forseti beyond the basic setup.
- Configure Forseti Enforcer.

This guide was developed using Forseti version 2.14.1.

### Pre-requisites

To perform the steps in this tutorial, you need the following:

- Access to a G Suite or Cloud Identity super admin account.
- Access to the  **Security** page in the Google Admin console (https://admin.google.com).
- Access to the GCP Console (https://console.cloud.google.com).
- Access to rights to modify IAM permissions at the Organization level.
- A project where you will deploy Forseti. In this guide, we'll use the project name `forseti`.
- Editor or owner permissions for the `forseti` project.

Note: Because of a [bug in the Forseti installer](https://github.com/forseti-security/forseti-security/issues/2759),
you must choose a zone that ends with `-c`, such as  `us-east4-c` when you define the region and zone where you want to
install Forseti. 

### Installing Forseti

In the `forseti` project, do the following:

1.  Go to the [**VPC Networks** page](https://console.cloud.google.com/networking/networks/list) in the GCP Console.
1.  Create a VPC for Forseti with one subnet. Configure it with the following parameters:
       - **Private Google access**: **On**
       - **Flow logs**: **On** (optional)
       - **Dynamic routing mode**: **Regional**

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/f4ab14ea.png)

In the example above, the VPC was created with the name `forseti` and the subnet with the name `forseti-subnet1`. The
chosen region is `us-east4`. The chosen zone is `us-east4-c`. During this step, record the network, subnet, and region
names; you will use them in later steps.

1.  Remove the default network, unless it's being used by other resources.
1.  Open Cloud Shell and configure the gcloud session as follows:

        gcloud config set project [PROJECT_ID]
        gcloud config set compute/region [REGION_NAME]
        gcloud config set compute/zone [ZONE_NAME]

    These settings are used by the Forseti installer.
    
    Using the values from the example above:

        gcloud config set project forseti-pj-id
        gcloud config set compute/region us-east4
        gcloud config set compute/zone us-east4-c

1.  Clone Forseti Repository, this contains the installer we will use:

        git clone https://github.com/GoogleCloudPlatform/forseti-security.git`

5.  Install Forseti and make it use the network that we created. (If you plan to use the SendGrid email service, ensure 
    that you obtain an API key before proceeding, because it will ask you during this step.)

        cd forseti-security
        python install/gcp_installer.py /
        --vpc-host-network [NETWORK_NAME] /
        --vpc-host-subnetwork [SUBNETWORK_NAME] /
        --gsuite-superadmin-email [SUPER_ADMIN_ACCOUNT] /
        --cloudsql-region [REGION_NAME] /
        --gcs-location [REGION_NAME]

    Where the `[REGION_NAME]` should be the same region you created the subnetwork on.
    
    Using the values from the example above:

        cd forseti-security
        python install/gcp_installer.py /
        --vpc-host-network forseti /
        --vpc-host-subnetwork forseti-subnet1 /
        --gsuite-superadmin-email [SUPER_ADMIN_ACCOUNT] /
        --cloudsql-region us-east4 /
        --gcs-location us-east4

    With this step, we are essentially running Deployment Manager to create the components necessary to install Forseti.
    You can follow the installation on the [deployment page](http://console.cloud.google.com/dm/deployments) as well as
    the command line.

    Note: In this step, the Forseti installer will try to remove the default firewall rules. Because we removed the
    default VPC network, this step will cause an error in the installation.

### Making Forseti private

At this stage, Forseti is installed, but it is not yet configured as private. In this section, you make Forseti 
private.

In the GCP Console, ensure that you have the `forseti` project selected, then do the following:

1.  Go to the [**Cloud SQL** page](https://console.cloud.google.com/sql) in the GCP Console.
1.  Find the `forseti-server-db` instance.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/5dacd607.png)

1.  Click **Edit**.
1.  Add the private IP address.
1.  Remove the public IP address.
1.  Save the changes.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/fed98394.png)

Note: This is also a good time to ensure the database is in the same zone as the server VM (optional).

7. Navigate to "VCP Network > Firewall Rules" page and edit the rules of both `forseti-client-allow-ssh-external` and `forseti-server-allow-ssh-external` to restrict the `Source IP Ranges` to that of the locaton (on-premise or datacenter range) you will be connecting from:

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/58b996ae.png)

8. (Optional) Navigate to the "Compute Engine" > "VM Instances" page and remove the public IP of both the server and client VMs.
   - This will require you to access the instances through IAP proxy, VPN or Interconnect.

9. (Optional)  IAP will provide Google Identity verified proxy tunnel to compute instances without internet access. More details on how to setup [IAP](https://cloud.google.com/iap/docs/using-tcp-forwarding#ssh_tunneling) to access forseti VM through SSH.


### Configuring Forseti

In this section you will perform the base configuration to get Forseti up and running.

#### Enable Domain Wide Delegation (DWD)

*Important:*  You need to be logged in with the Super Admin account for the next steps:

[Forseti Documentaton > G Suite](https://forsetisecurity.org/docs/v2.2/configure/inventory/gsuite.html)

1. Navigate to the Service account page on the `forseti` project.
2. Find the `Forseti Server` service acount and click on the more icon (3 dots) and then click on edit.
   - Note the service account address for use in the next section.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/c23aed4f.png)

3. Enable domain wide delegation.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/96628a59.png)

4. Click on `View Client ID`.
![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/42fa4d69.png)

Copy the value from Client ID and save it for the next steps.
Note: you may also copy it from the Edit page if you are unable to copy it from the popover that displays the info.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/249d1377.png)


5. Navigate to the Google Admin page and go to [Manage API client access] (https://admin.google.com/ManageOauthClients) in the Security Settings.
6. Paste the Client ID in the client name box.
7. Authorize the following scopes:
```
https://www.googleapis.com/auth/admin.directory.group.readonly,https://www.googleapis.com/auth/admin.directory.user.readonly,https://www.googleapis.com/auth/cloudplatformprojects.readonly,https://www.googleapis.com/auth/apps.groups.settings
```

#### Enable SCC with Forseti plugin

1. On the Forseti project navigate to "API & Services > Library" and search for the following APIs and enable it:
   - securitycenter.googleapis.com

2. Navigate to the Organization level.
3. Navigate to "Security > Security Command Center" menu.
4. Enable the service.
5. Click on "Add Security Sources".
![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/f98fc029.png)


6. Select the Forseti plugin.
![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/4de2ba3a.png)


7. Click the **Sign-up** button to get started:

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/2c9ff5f6.png)

8. Follow the steps to enable the extension. First select your organization:

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/forseti_source_id.png)

9. Follow the instructions on the screen. When asked for a service account, use the Forseti Server service account. Choose
the `forseti` project.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/forseti_source_id_2.png)

10. Copy the `source_id` for later use. The `source_id` is in this format, as shown in the screenshot above: 

    `organizations/[ORGANIZATION_ID]/sources/[SOURCE_ID]`

11. Navigate to the Organization IAM page and ensure the service account was granted the `Security Center Findings Editor` 
role, if not then grant it.

Note: if you did not re-use the Forseti Server service account and created a new service account for Cloud SCC, you need to
grant `Security Center Findings Editor` role for both the Foresti Server service acconut and the newly created service
account for Cloud SCC.

#### Editing Forseti configuration file and running Forseti


Go back to Cloud Shell, ensure you are in the `forseti` project and execute the following steps:

1. List all the buckets:
```
gsutil ls
```

2. Find the forseti-server bucket.

2. Copy the configuration file from Cloud Storage to Cloud Shell:
```
gsutil cp gs://forseti-server-[id]/configs/forseti_conf_server.yaml .
```

3. Click on the pencil icon to open in the editor ![4a724bc0.png](011b3934.png)

4. Under `notifier > violations > cscc` element section of the configuration, modify it as follows:

```
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
```

 5. Upload the modified file to the bucket:
 ```
 gsutil cp forseti_conf_server.yaml gs://forseti-server-[id]/configs/forseti_conf_server.yaml
 ```

6. SSH into the forseti-server-vm.
7. Reload the server configuration:
```
forseti server configuration reload gs://forseti-server-[id]/configs/forseti_conf_server.yaml
```

8. Create an inventory:
```
forseti inventory create
```

At the end of this step the output should give us an `Inventory ID` - copy it for the next step:
```
{
  "errors": 0,
  "warnings": 31,
  "step": "bucket/test-function-http-tpc6nm6zh2",
  "finalMessage": false,
  "lastError": "",
  "id": "1556128018126591", # <== THIS!
  "lastWarning": ""
}
```

9. Create a model based on the inventory & configure Forseti to use it:
```
forseti model create --inventory_index_id [INVENTORY_ID] [MODEL_NAME]
forseti model use [MODEL_NAME]
```

10. Run forseti scanner:
```
forseti scanner run
```

11. Run forseti notifier:
```
forseti notifier run
```

13. Check the output for any Violations.
12. Validate the Forseti Violations are shown as Findings in the Security Command Center page.

![](https://storage.googleapis.com/gcp-community/tutorials/private-forseti-with-scc-integration/0a78fb27.png)

## Conclusion

This gives you a production-ready base intallation of Forseti. However, it's important to note that you still need to create
an organizaton-specific configuration. Typically, you need to refine the base rules to remove the noise and catch 
use-cases that are specific to your organization (for example, allow firewall rules opening SSH and RDP traffic only for your defined IP ranges).

See the Forseti documentation on
[how to create your own rules](https://forsetisecurity.org/docs/latest/configure/scanner/rules.html).
