---
title: Authenticated browser downloads with audit logging
description: Use this example code to deploy an authenticating proxy in front of a Google Cloud file server with audit logging.
author: ianmaddox
tags: Identity-Aware Proxy, Cloud Storage, App Engine, serverless
date_published: 2020-10-06
---

Ian Maddox | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

The
[code that accompanies this document](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/authenicated-browser-downloads-with-audit-logging/) 
provides an example means of serving images, documents, and other files stored in Cloud Storage while requiring the user to be authenticated with Google. This 
solution is useful because the Cloud Storage 
[authenticated browser downloads feature](https://cloud.google.com/storage/docs/access-control/cookie-based-authentication) does not currently work with internal 
logging.

This example uses [Identity-Aware Proxy](https://cloud.google.com/iap/docs), [App Engine standard environment](https://cloud.google.com/appengine/docs/standard),
and [Cloud Storage](https://cloud.google.com/storage/docs):

1. A web user makes a request to your file server.
1. If the user is not authenticated, they are redirected to a Google login page by Identity-Aware Proxy.
1. After authentication, the user's request is forwarded to App Engine.
1. App Engine validates the request and retrieves the file from Cloud Storage.
1. If a watermark or other transformation is required, it is processed.
1. The file is then returned to the web user.

Requests from users who aren't authenticated or who aren't authorized to access the files don't reach App Engine. Requests that don't match an object in 
Cloud Storage return a `404 File not found` error. Requests with no filename or with a missing filename extension receive a `400 Bad request` error.

## Deploying the code

1.  Download
    [the code in this repository](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/authenicated-browser-downloads-with-audit-logging/).
1.  Modify `app.yaml` to identify the Cloud Storage bucket that holds the assets.
1.  Set up and configure the [Cloud SDK, including the `gcloud` tool](https://cloud.google.com/sdk/docs/install).
1.  Deploy the application:

        gcloud app deploy

1. Enable Identity-Aware Proxy for the App Engine app that you created.
1. [Lock down the permissions](https://cloud.google.com/appengine/docs/standard/go/service-account) of the App Engine service account.

## Request format

When your service is deployed, it is available at a URL similar to the following:

`https://my-authenticated-fileserver.appspot.com/`

Filenames and paths requested from this host map to object addresses in Cloud Storage. For example, a request to
`https://my-authenticated-fileserver.appspot.com/assets/heroimage.png` maps to this object:
`gs://my-asset-bucket/assets/heroimage.png`

A request for a missing file returns a `404 File not found` error.

The application deduces the [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types) based on the filename extension. Therefore,
requests without a filename extension return a `400 Bad Request` error. Ensure that all of the files that you want to serve have an appropriate filename 
extension.

## Opportunities for customization

This code provides a plain authenticated file server. Often, you might have requirements for transforming files before delivering them to the user. Here are a few
ways that this code can be modified to fit more specific needs:

* Image or document watermarking
* Image resizing and other alterations
* Data loss prevention (DLP) redaction to hide sensitive information from users not authorized to view those parts
* Pub/Sub event triggers
* Object request tallying and object deletion, for objects that can only be downloaded a specific number of times
