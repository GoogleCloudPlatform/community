---
title: Configure private access to MongoDB Atlas with Serverless VPC Access
description: Learn how to use Serverless VPC Access to allow App Engine, Cloud Functions, or Cloud Run access to a MongoDB Atlas cluster using private IP addressing.
author: russStarr
tags: security, networking, RFC 1918
date_published: 2021-05-18
---

Russ Starr | Customer Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to configure private IP access from serverless services such as App Engine, Cloud Functions, or Cloud Run to a MongoDB Atlas cluster.
This is useful when you want to keep your MongoDB connections scoped to private IP addresses only, instead of allowing public access from the Internet.

In this tutorial, you learn how to use [Serverless VPC Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) to create a connector that
routes traffic from the Google Cloud serverless services to the MongoDB Atlas cluster. You also learn how to establish VPC peering between your Google Cloud VPC 
network and your MongoDB Atlas VPC network.

This tutorial uses Cloud Functions, but you can take similar steps to configure
[App Engine](https://cloud.google.com/appengine/docs/standard/python/connecting-vpc) or
[Cloud Run](https://cloud.google.com/run/docs/configuring/connecting-vpc).

This tutorial uses Python, but you can adapt what you learn in this tutorial to other
[languages supported for Cloud Functions](https://cloud.google.com/functions/docs/writing).

This tutorial assumes that you have basic familiarity using the Google Cloud Console, Cloud Shell, the MongoDB Atlas console, Python, and shell scripts.

The following diagram illustrates the architecture of the solution described in this tutorial:

![architecture](https://storage.googleapis.com/gcp-community/tutorials/serverless-vpc-access-private-mongodb-atlas/architecture.png)

## Objectives

*   Create a MongoDB Atlas cluster.
*   Create a VPC peering relationship between MongoDB Atlas and your Google Cloud VPC network.
*   Create the Serverless VPC Access connector.
*   Create a Cloud Function that triggers on HTTP and makes a connection to the MongoDB cluster.
*   Verify that the Cloud Function is able to reach the MongoDB Atlas cluster.

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [Cloud Functions](https://cloud.google.com/functions)
*   [Cloud Build](https://cloud.google.com/build)
*   [Virtual Private Cloud (VPC)](https://cloud.google.com/vpc)
*   [Serverless VPC Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)

This tutorial also uses billable components of [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) to create a dedicated cluster. Shared clusters don't support
VPC peering.

Use the [Google Cloud pricing calculator](https://cloud.google.com/products/calculator) and [MongoDB pricing page](https://www.mongodb.com/pricing) to generate a 
cost estimate based on your projected usage.

## Before you begin

This tutorial depends on you having some basic resources set up in Google Cloud and MongoDB Atlas.

### Google Cloud setup

1.  [Select or create a Google Cloud project.](https://console.cloud.google.com/projectselector2/home/dashboard)
1.  [Enable billing for your project.](https://support.google.com/cloud/answer/6293499#enable-billing)

### MongoDB Atlas setup

1.  [Create a MongoDB Atlas account.](https://docs.atlas.mongodb.com/tutorial/create-atlas-account/)
1.  [Create a MongoDB organization.](https://docs.atlas.mongodb.com/tutorial/manage-organizations/)
1.  [Create a MongoDB project.](https://docs.atlas.mongodb.com/tutorial/manage-projects/)
1.  [Enable billing for your MongoDB Atlas organization.](https://docs.atlas.mongodb.com/billing/)
1.  [Create a MongoDB Atlas user account](https://docs.atlas.mongodb.com/security-add-mongodb-users/), which is used by Cloud Functions to connect to the
    MongoDB database.

## Enable the VPC Serverless Access API

1.  In the [Google Cloud Console](https://console.cloud.google.com), select the project to use for this tutorial.

1.  Go to the [Serverless VPC Access API page](https://console.cloud.google.com/marketplace/details/google/vpcaccess.googleapis.com).

1.  Click **Enable**.

## Create the VPC Serverless Access connector

1.  Go to the [Serverless VPC Access page](https://console.cloud.google.com/networking/connectors).

1.  Click **Create Connector**.

1.  Enter a name for the connector.

    This tutorial uses `mongo-connector`.

1.  Select a region that match the region of your serverless service.

1.  Keep the `default` network selected.

1.  Under **Subnet**, click **Custom IP Range**, and enter a private IP address range that fits your IP address scheme.
  
    This tutorial uses `10.8.0.0`. 

    You only have the option to use a `/28` mask for this step, so don't include the mask in the field.

    This subnet is used in a later step when you configure the MongoDB Atlas access list.

## Create the MongoDB Atlas cluster

For detailed instructions for creating a MongoDB Atlas cluster, see the
[MongoDB Atlas documentation](https://docs.atlas.mongodb.com/tutorial/create-new-cluster/#procedure).

1.  In the [MongoDB Atlas console](https://cloud.mongodb.com), select the project for your cluster.

1.  On the **Clusters** page, click **Build a Cluster**.

1.  Under **Dedicated Clusters**, click **Create a Cluster**.

    You can also select **Dedicated Multi-Cloud & Multi-Region Clusters**, but the steps in this tutorial assume that you are using a dedicated cluster because
    it is the minimum for VPC Network Peering.

1.  Click **Google Cloud** and your region.

1.  Select a Cluster Tier.

    This tutorial uses **M10**, but any of them will work.

1.  Enter a name for your cluster.

    This tutorial uses the default `Cluster0`.

1.  Click **Create Cluster**.

It takes a few minutes to create the cluster, but you can begin the next section before then.

## Configure the MongoDB Atlas access list

For detailed instructions for adding IP addresses to the MongoDB IP access list, see the
[MongoDB Atlas documentation](https://docs.atlas.mongodb.com/security/ip-access-list/#add-ip-access-list-entries).

1.  In the MongoDB Atlas console, click **Network Access** in the **Security** section.

    ![networkAccess](https://storage.googleapis.com/gcp-community/tutorials/serverless-vpc-access-private-mongodb-atlas/networkAccess.png)

1.  In the **IP Access List** tab, click **Add IP Address**.

1.  For **Access List Entry**, enter the `/28` network that you created for the Serverless VPC Access connector.

    This tutorial uses `10.8.0.0/28`.

1.  Under **Comment**, enter `mongo-connector` so that you remember the relationship with the Google Cloud resource name.

Following these steps restricts your MongoDB Atlas cluster to only the `10.8.0.0/28` subnet.

## Configure MongoDB Atlas VPC peering

For detailed instructions for adding a VPC peering connection, see the
[MongoDB Atlas documentation](https://docs.atlas.mongodb.com/security-vpc-peering/#in-add-a-new-network-peering-connection-for-your-project-2).

1.  In the **Network Access** section, click **Peering**.

1.  Click **Add Peering Connection**.

1.  Click **Google Cloud**, and then click **Next**.

1.  Enter the project ID of your Google Cloud project. 

1.  Enter the VPC network name.
 
    This tutorial uses `default`.

1.  Click **Initiate Peering**.

    Keep this browser tab open so that you can use the project ID and VPC network name in the next section.

    The status remains **Pending** until you configure peering on the Google Cloud side in the next section.

## Configure VPC Network Peering on Google Cloud

1.  In the Google Cloud Console, go to the [**VPC network peering** page](https://console.cloud.google.com/networking/peering/).

1.  Click **Create connection**, and then click **Continue**.

1.  Enter name for the connection.

    This tutorial uses `googlecloud2mongo`.

1.  Under **Your VPC network**, select **default** .

1.  Under **Peered VPC Network**, click **in another project**.

1.  Enter the project ID and VPC network name that were provided at the end of the previous section, in which you configured MongoDB Atlas VPC peering.

1.  Click **Create**.

    These steps are successful when you see the **Active** status for the peering connection. The MongoDB Atlas screen should show the **Available** status
    when the connection is complete.

## Retrieve the connection string for your cluster

1.  In the MongoDB Atlas console, on the **Cluster** page for your newly created cluster, click **Connect**.

1.  For **Choose Connection Type**, select **Private IP for Peering**.

1.  Click **Choose a connection method**.

1.  Click **Connect your application**.

1.  Select Python 3.11 or later.

1.  Copy the connection string, which you use in the Cloud Function in a later section.

    The connection string is in the following format:

        mongodb+srv://[USERNAME]:[PASSWORD]@[CLUSTER_NAME]-pri.[SUBDOMAIN].mongodb.net/
        
    For more information about the MongoDB connection string format, see
    [Private Connection Strings](https://docs.atlas.mongodb.com/reference/faq/connection-changes/#std-label-connstring-private).

1.  Click **Close**.

## Create an empty database

1.  In the MongoDB Atlas console, on the **Cluster** page, click **Collections**.

1.  Click **Add Your First Database**.

1.  For the database name, enter `empty_db`.

1.  For the collection name, enter `empty_collection`.

1.  Click **Create**.

## Create a Cloud Function

In this section, you create and configure a basic Cloud Function, set its requirements, and then add the Python code for the main body of the function. 

### Configure the Cloud Function

1.  In the Google Cloud Console, go to the [**Cloud Functions** page](https://console.cloud.google.com/functions).

1.  Click **Create Function**.

1.  Click **Save**, keeping all settings at their default values.

1.  At the bottom of the page, click **Runtime, Build and Connection Settings**, and then click then **Connections**.

1.  Under **Egress settings**, for **VPC connector**, select `mongo-connector`.

1.  Click **Next**.

### Deploy the requirements for the Cloud Function

1.  For **Runtime**, select **Python 3.9**.

1.  If you are prompted to enable the Cloud Build API, click **Enable API**, and then click **Enable**.

1.  On the left side of the **Cloud Functions** page, click **requirements.txt** and paste the following code:

        # Function dependencies, for example:
        # package>=version
        pymongo
        dnspython

1.  Click **Deploy** to install the required dependencies.

    Before proceeding to the next section, wait for the Cloud Function status to turn green, indicating that the requirements have been deployed..

### Deploy the main Python code for the Cloud Function

1.  Select the Cloud Function.

1.  Click **Edit**, and then click **Next**.

1.  Click **main.py** and replace all Python code with the following:

        from pymongo import MongoClient
        from flask import make_response

        connection_string = "mongodb+srv://[USERNAME]:[PASSWORD]@[CLUSTER_NAME].[SUBDOMAIN].mongodb.net/"

        def hello_world(request):
            request_json = request.get_json()
            if request.args and 'message' in request.args:
                return request.args.get('message')
            elif request_json and 'message' in request_json:
                return request_json['message']
            else:
                client = MongoClient(connection_string)
                db = client.empty_db
                response = make_response()
                response.data = str(db.command("serverStatus"))
                response.headers["Content-Type"] = "application/json"
                return response

1.  Update the `connection_string` variable to reflect your user account, password, and subdomain.

1.  Click **Deploy**.

## Verify that the Cloud Function connects to the MongoDB Atlas cluster

1.  Select the Cloud Function.

1.  Click **Trigger** and copy the trigger URL to your clipboard.

1.  Click the [**Activate Cloud Shell**](https://cloud.google.com/shell/docs/using-cloud-shell#starting_a_new_session) button in the upper-right corner of the
    Cloud Console.

1.  Enter the following command in Cloud Shell, updating the `CFURL` variable with the URL on the clipboard.

        export CFURL="<insert URL here>"
        curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $CFURL
 
    Success! You should see JSON output of the server status information from your MongoDB Atlas cluster, which shows that you have connectivity.

    ![success](https://storage.googleapis.com/gcp-community/tutorials/serverless-vpc-access-private-mongodb-atlas/success.png)

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

You can also delete your MongoDB Atlas cluster if you no longer need it.

## What's next

- [Serverless VPC Access documentation](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)
- [MongoDB connection string URI format](https://docs.mongodb.com/manual/reference/connection-string/)
- Try out other Google Cloud features for yourself. Have a look at our [tutorials](https://cloud.google.com/docs/tutorials).
