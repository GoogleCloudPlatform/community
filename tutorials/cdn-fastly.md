---
title: Content Delivery with Fastly and Google Cloud Storage
description: This tutorial walks you through the process of setting up Fastly to pull assets from Google Cloud Storage.
author: tzero
tags: Fastly, Cloud Storage, CDN
date_published: 09/09/2015
---

A [content delivery network](https://wikipedia.org/wiki/Content_delivery_network),
or CDN, offers an efficient, cost-effective way of reducing both network
I/O costs and content delivery latency for regularly accessed website
assets. A CDN can be understood as group of geographically distributed
caches, with each cache locaœted in one of several global points of presence
(POPs). The CDN service pulls assets from an origin server at regular
intervals and distributes them to these caches. When a client requests an
asset, the asset is served from the nearest cache.

Though CDNs often greatly improve the speed of content delivery, they are
usually at the mercy of the public Internet; that is, when they pull
content from an origin server, they have to compete with other network
traffic for bandwidth. To mitigate this issue, the CDN provider
[Fastly](https://www.fastly.com/) has
[partnered with Google](https://www.fastly.com/partner/gcp)
to provide a direct connection to Google Cloud Platform's network edge at
several North American locations. This edge connection allows Fastly users
on Cloud Platform to bypass the public Internet during origin pulls,
resulting in significant increases in pull speed.

This tutorial walks you through the process of setting up Fastly to pull
assets from [Google Cloud Storage](https://cloud.google.com/storage/).
In addition, it describes how to configure Fastly's
[Origin Shield](https://docs.fastly.com/guides/about-fastly-services/about-fastlys-origin-shielding-features)
feature to take advantage of Fastly's direct connection to Google's
network edge.

## Costs
This tutorial uses Cloud Storage, a billable component of
Cloud Platform, and Fastly, which charges bandwidth and request fees.

You can use the [pricing calculator](https://cloud.google.com/products/calculator)
to generate a cost estimate based on your projected usage.

Fastly provides a free developer trial that allows you
to [test up to $50 of traffic for free](https://docs.fastly.com/guides/account-types-and-billing/accounts-and-pricing-plans).
See Fastly's [pricing page](https://www.fastly.com/pricing)
for further pricing details.

## Objectives

+  Configure Fastly to source assets from Cloud Storage
+  Configure Fastly to handle cache misses using Origin Shield

## Before you begin

This tutorial assumes that you have the following:

+  A Google Cloud Platform project with the Cloud Storage and Cloud Storage
    JSON APIs enabled. These APIs are enabled by default.
+  A [Fastly account](https://www.fastly.com/signup).
+  A domain name you plan to use for CDN purposes.

## Configure Fastly to pull content from Cloud Storage

### Create a Cloud Storage bucket

Before you can configure Fastly to pull assets from Cloud Storage,
you need to create a Cloud Storage bucket and populate it with assets.

To create a Cloud Storage bucket:

1. In the Cloud Storage Browser in the 
   [Cloud Platform Console](https://console.cloud.google.com/storage/browser),
   click **Create Bucket**.
1. In the **Create Bucket** dialog, fill out the form as follows:

    +  _Name_: _<your_bucket_name>_ (must be unique)
    +  _Storage_: Standard
    +  _Location_: United States

        **Note**: To take advantage of Fastly's direct connection to Google's
        network edge, you must create your bucket in the United States.

1. Click **Create** to create your bucket. You will be taken to your bucket's
    browser page.

Next, you need to add assets that Fastly can pull from your bucket:

1. On your local machine, identify an image that you'd like to upload
    to your bucket.
1. Upload the image to your bucket by dragging it from your local file
    browser and dropping it into your bucket page in the
    Cloud Platform Console. After the image has finished uploading, it
    will appear in the bucket's list of stored objects.
1. On your bucket page, go to your image's list item and click
    **Shared Publicly** to make the image externally accessible.

### Create a new Fastly service

Now that you've set up a Cloud Storage bucket, set up a Fastly service and
configure it to use the bucket as a point of origin:

1. Go to the
    [Fastly configuration page](https://app.fastly.com/#configure).
1. Click **New Service** and fill out the form as follows:

    +  _Name_: Cloud Storage Origin Test
    +  _Server address_: storage.googleapis.com:80
    +  _Domain name_: `[YOUR_DOMAIN_NAME]`

        Note: Fastly recommends against using an
        [apex domain](https://docs.fastly.com/guides/basic-configuration/using-fastly-with-apex-domains).

**Important**: To complete the process of creating your first service, you
must set your domain's CNAME record to `global.prod.fastly.net`. The
process for doing so will vary by domain hosting service. To find
host-specific instructions for your hosting service, see
[Add a CNAME record](https://support.google.com/a/topic/1615038).

### Add your Cloud Storage bucket as a backend

After creating your Fastly service, add your Cloud Storage bucket as a
backend for the service:

1. Click the **Configure** icon in the top navigation bar of the Fastly
configuration page.
1. Click the blue **Configure** button.
1. Click **Settings** in the sidebar.
1. Set the default host name as follows, replacing `[YOUR_BUCKET_NAME]`
    with the name of your Cloud Storage bucket:

        [YOUR_BUCKET_NAME].storage.googleapis.com

1. Optionally, define the length of time your assets should be cached by
    setting a time to live (TTL) value. By default, each asset is cached
    for 3600 seconds (1 hour) before Fastly performs another origin pull.
1. Save your settings.
1. Click the orange **Activate** button to activate your new backend.

Congratulations! You now have a functioning Fastly CDN service that
will periodically pull assets from your storage bucket and store them in
edge caches around the world.

**Note**: It might take 20-30 seconds for the initial origin pull to
propagate across Fastly's network.

### Test your service

You can test your Fastly service by loading the image file that you added
to your bucket earlier in this tutorial. In your web browser, navigate to
the following URL, replacing `[YOUR_DOMAIN]` with your domain and
`[IMAGE_NAME]` with your image file:

    https://[YOUR_DOMAIN].global.prod.fastly.net/[IMAGE_NAME]

For example, if your domain is `www.example.com` and the file is named
`test.png`, you should navigate to the following URL:

    https://www.example.com.global.prod.fastly.net/test.png

## Configure an Origin Shield and connect it to Cloud Platform

Fastly includes a feature called
[Origin Shield](https://docs.fastly.com/guides/about-fastly-services/about-fastlys-origin-shielding-features)
that places a "shield" cache between its edge caches and your origin
server. This shield cache handles all cache misses across Fastly's network;
that is, if one of Fastly's caches does not have the asset that has been
requested, that cache will try to pull the asset from the shield cache
instead of the origin server. The cache will only pull the requested
asset from the origin server if the shield cache does not contain the
asset.

By using an Origin Shield, you can drastically reduce the number of
calls back to your Cloud Storage bucket. And by using an Origin
Shield that is connected to Google's network edge, you can increase
the speed of the shield's origin pulls.

To configure an Origin Shield and connect it to Cloud Platform:

1. In the [Fastly application](https://app.fastly.com/),
    click **Hosts** in the sidebar.
1. Under **Backends**, click the gear next to your
    **storage.googleapis.com** backend and click **Edit**.
1. In the **Edit Backend** dialog, set **Shielding** to either
    **Ashburn, VA** or **San Jose, CA**.
1. Click **Update** to commit your settings.
1. Click **Activate** to deploy the modified service.

## Cleaning up

After you've finished the Fastly tutorial, you can clean up the resources you
created on Google Cloud Platform so you won't be billed for them in the future.
The following sections describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial. If you don't want to delete the project, delete the individual
instances, as described in the next section.

**Warning**: Deleting a project has the following consequences:

+ If you used an existing project, you'll also delete any other work you've done in the project.
+ You can't reuse the project ID of a deleted project. If you created a custom project ID that you
plan to use in the future, you should delete the resources inside the project instead. This ensures
that URLs that use the project ID, such as an appspot.com URL, remain available.

If you are exploring multiple tutorials and quickstarts, reusing projects instead of deleting
them prevents you from exceeding project quota limits.

To delete the project:

1. In the Cloud Platform Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1. In the project list, select the project you want to delete and click **Delete project**.
After selecting the checkbox next to the project name, click **Delete project**.
1. In the dialog, type the project ID, and then click **Shut down** to delete the project.

### Deleting your Fastly service

To delete your Fastly service:

1. Navigate to the
    [Fastly application](https://app.fastly.com/) in
    your web browser.
1. Click the **Configure** icon in the top navigation menu.
1. Select your service from the **Service** dropdown.
1. Click the **Deactivate** button.
1. In the modal dialog, click the **Deactivate** button.
1. Click the **Delete** button.
1. In the modal dialog, click the **Confirm** button to remove the service.

## Next steps

### Visit the Fastly docs

New to Fastly? Explore Fastly's feature set and configuration options by
reviewing the [Fastly documentation](https://docs.fastly.com/guides/).
