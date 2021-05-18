---
title: Hybrid and multi-cloud container image management with Harbor
description: Set up one-way container image replication between Harbor and Google Container Registry.
author: jpatokal
tags: container registry, Anthos, Kubernetes Engine
date_published: 2021-05-19
---

Marc Fong | Application Modernization Specialist | Google

Jani Patokallio | Solutions Architect  | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial describes how to implement a multi-site container registry design with [Harbor](https://goharbor.io/) and
[Google Container Registry](https://cloud.google.com/container-registry/). In this tutorial, you set up one-way, push-based replication of container images from
Harbor to Google Container Registry.

It's becoming increasingly common to need to deploy a single application system across multiple sites. These different sites could be different public 
clouds (multi-cloud) or a combination of public and on-premises data centers (hybrid cloud).

![High-level architecture](https://storage.googleapis.com/gcp-community/tutorials/container-image-management-with-harbor/design.png)

Having container registries local to the Kubernetes clusters at multiple sites speeds the retrieval of application container images by decreasing latency and 
increasing bandwidth, and it prevents a single container registry from being a single point of failure for the application running across independent Kubernetes 
clusters.

Using different container registries for different clusters has a downstream impact, because the Kubernetes deployment manifests deployed to each cluster need to 
use different fully qualified image names. This challenge can be addressed with different templating tools (such Helm, kpt, or Kustomize) but this is out of 
scope for this tutorial. A simple solution using shell scripting is provided at the end of this tutorial for reference and adaptation.

**Note**: As of May 2021, Google Artifact Registry is not supported by Harbor as an external registry endpoint.

## Install Harbor and its prerequisites

This tutorial uses a single-node installation of Harbor on Compute Engine. You can use any Compute Engine virtual machine with at least 2 vCPUs, with
**Allow HTTPS traffic** enabled under **Firewall**.

**Note**: For a highly available installation on Anthos instead, you can use the instructions for
[deploying Harbor with high availability with Helm](https://goharbor.io/docs/2.2.0/install-config/harbor-ha-helm/), which also requires setting up HA 
clusters of PostgreSQL and Redis.

1.  Install the [prerequisites for Harbor](https://goharbor.io/docs/2.2.0/install-config/installation-prereqs/), including Docker Engine and Docker Compose.

1.  Follow the instructions for [installing and configuring Harbor](https://goharbor.io/docs/latest/install-config/). 

1.  For the Harbor HTTPS configuration, use the internal Compute Engine hostname as your fully qualified domain name (FQDN). When you're logged in
    to the VM, set the environment variable `$HARBOR` to this value with the following command:

        HARBOR=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/hostname" -H "Metadata-Flavor: Google")

1.  After installation is complete, test that you can access the Harbor user interface by browsing to `https://[VM_EXTERNAL_IP_ADDRESS]`.

    The default username is `admin`. The default password is `admin/Harbor12345`.

1.  Confirm that you can log in to Docker with the same credentials:

        docker login $HARBOR
        
    This command should return `Login Successful`.

## Set up the Google Container Registry endpoint for Harbor

1.  In the Cloud Console, go to the [**IAM & Admin > Service Accounts** page](https://console.cloud.google.com/iam-admin/serviceaccounts) and
    [create a Google Cloud service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating) with the `Storage Admin` role.
1.  Click the key name and select the **Keys** tab.
1.  Under **Add key**, select **Create a new key** and **JSON**.

    This creates a new key and downloads it to your local machine.

1.  In Harbor, Go to **Administration > Registries > New Endpoint** and fill in the following details in the **Edit Endpoint** dialog box:

    - **Provider**: **Google GCR**
    - **Name**: Your endpoint name. This tutorial uses `gcr-sea-anthos-demo`.
    - **Description**: A description for your endpoint.
    - **Endpoint URL**: `https://gcr.io`
    - **Access ID**: `_json_key`
    - **Access Secret**: Paste your Google Cloud IAM service account JSON key content in this field.
    - **Verify Remote Cert**: Check this box.                                                |

1.  Click **Test Connection**.
1.  Click **OK**.

## Set up replication

1.  Go to **Administration > Replications > New Replication Rule**
2.  Fill in the details from the following table:

    | Key                                          | Value                                              | Notes                                                                                                                                                                                                                                                                                                                                |
    | -------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
    | Name                                         | \[Rule Name\]                                      |                                                                                                                                                                                                                                                                                                                                      |
    | Description                                  | \[Description\]                                    |                                                                                                                                                                                                                                                                                                                                      |
    | Replication Mode                             | Push-based                                         | Harbor will be the primary container registry new images are pushed to. So  replication to other sites should be triggered when new images are pushed into Harbor.                                                                                                                                                                   |
    |                                              |                                                    | Under Source resource filter:                                                                                                                                                                                                                                                                                                        |
    | Name                                         | `library/**`                                       | This example filter will replicate all images under `library`.  See [here](https://goharbor.io/docs/1.10/administration/configuring-replication/create-replication-rules/#replication-rule3:~:text=The%20name%20filter%20and%20tag%20filters%20support%20the%20following%20patterns) for more sample filter patterns. |
    | Tag                                          | (optional)                                         | Filter based on image tag/version.  See [here](https://goharbor.io/docs/1.10/administration/configuring-replication/create-replication-rules/#replication-rule3:~:text=The%20name%20filter%20and%20tag%20filters%20support%20the%20following%20patterns) for more sample filter patterns.                                            |
    | Label                                        | (optional)                                         | Filter based on Harbor labels.  See [here](https://goharbor.io/docs/1.10/administration/configuring-replication/create-replication-rules/#replication-rule3:~:text=The%20name%20filter%20and%20tag%20filters%20support%20the%20following%20patterns) for more sample filter patterns.                                                 |
    | Resource                                     | Image                                              | Only replicate container images to GCR                                                                                                                                                                                                                                                                                               |
    | Destination registry                         | \[Endpoint name from previous step\]               | Name of registry endpoint created earlier.                                                                                                                                                                                                                                                                                           |
    | Destination namespace                        | \[GCP Project Name\]/\[Optional GCR Library Name\] | GCP Project name is mandatory.  Specifying a sub-directory/Library, will result in the creation of a library/folder where all source images will be stored.                                                                                                                                                                          |
    | Trigger Mode                                 | Event Based                                        |                                                                                                                                                                                                                                                                                                                                      |
    | Delete remote resources when locally deleted | ☑                                                  | Check box to keep GCR fully in sync.                                                                                                                                                                                                                                                                                                 |
    | Override                                     | ☑                                                  | Specify to override an image at the destination when one of the same name exists                                                                                                                                                                                                                                                     |
    | Enable rule                                  | ☑                                                  |                                                                                                                                                                                                                                                                                                                                      |

    ![Screenshot of Edit Replication Rule dialog](https://storage.googleapis.com/gcp-community/tutorials/container-image-management-with-harbor/image3.png)

1.  Click **SAVE**

Harbor does not support sub-directories under the Library. Thus any containers stored in Harbor with ".../…" in the name, the sub-directory names will be 
removed.  Eg. `library/private/nginx` will be replicated to `[destination namespace]/nginx` where the `private` sub-directory is dropped.

## Test replication

To test replication, pull a public `nginx` image, tag it and push it to Harbor.  The image will be automatically replicated to GCR.

    $docker pull nginx:latest
    $docker tag nginx:latest $HARBOR/library/private-reg/nginx:latest
    $docker push $HARBOR/library/private-reg/nginx:latest

The screenshots below show the state of Harbor and Google Container Registry after a new image is pushed to the local Harbor registry, and automatic 
synchronization is successful.

![Successful execution in Harbor](https://storage.googleapis.com/gcp-community/tutorials/container-image-management-with-harbor/image4.png)

![State of Google Container Registry](https://storage.googleapis.com/gcp-community/tutorials/container-image-management-with-harbor/image5.png)

![State of Harbor registry](https://storage.googleapis.com/gcp-community/tutorials/container-image-management-with-harbor/image6.png)

## Updating image registry path in image name

Code snippet for replacing repository URLs in fully qualified image names:

Example replacing `registry.private.com/lib/nginx:v1.1` to `gcr.io/lib/nginx:v1.1`

    # export OLD_IMG="registry.private.com/lib/nginx:v1.1"
    $ export NEW_REPO="gcr.io\/lib\/"

    $ NEW_IMG=`echo $OLD_IMG | sed "s/^\(.*\/\)\(.*\)/${NEW_REPO}\2/"`
    $ echo $NEW_IMG
    
    gcr.io/lib/nginx:v1.1

## References

1. https://goharbor.io/docs/1.10/administration/configuring-replication/
