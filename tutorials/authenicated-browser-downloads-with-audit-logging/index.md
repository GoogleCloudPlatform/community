---
title: Authenticated Browser Downloads with Audit Logging
description: Deploy an authenticating proxy in front of a Google Cloud file server, with audit logging
author: ianmaddox
tags: IAP, GCS, GAE, serverless
date_published: 2020-10-01
---

## Overview

This code provides a means of serving images, documents, and other files stored on Google Cloud Storage while requiring the user to be authenticated with a Google. This solution is useful because Cloud Storage Authenticate Browser Downloads [does not support internal logging at this time](https://cloud.google.com/storage/docs/access-control/cookie-based-authentication).

This code uses [Identity-Aware Proxy](https://cloud.google.com/iap/docs), [App Engine Standard](https://cloud.google.com/appengine/docs/standard), and [Cloud Storage](https://cloud.google.com/storage/docs).


## Architecture
```
┏━━━┓    ┏━━━┓    ┏━━━━━━━━━━┓    ┏━━━━━━━━━━━━━┓
┃WEB┃ ►► ┃IAP┃ ►► ┃APP Engine┃ ►► ┃Cloud Storage┃
┗━━━┛    ┗━━━┛    ┗━━━━━━━━━━┛    ┗━━━━━━━━━━━━━┛
```
1. Web users make a request to your file server
1. Unauthenticated users are redirected to a Google login page by IAP
1. Once authenticated, the user's request is forwarded to App Engine
1. App Engine validates the request and retrieves the file from Cloud storage
1. If a watermark or other transformation is required, it is processed
1. The file is then returned to the web user

Users who don't authenticate or who are not authorized to access the files will not reach App Engine. Authenticated requests that do not match an object in GCS result in a 404. Requests with no filename or with a missing file extension receive a 400 Invalid Request error.

## Deploying the code
This is a basic review of the steps required to launch this code. For more information, see the official [Google Cloud solution paper here](http://link-TBD).
1. Download this directory to your workspace
1. Modify app.yaml to identify the GCS bucket that holds the assets
1. Set up and configure Google Cloud SDK and [gcloud tool](https://cloud.google.com/sdk/docs/install)
1. Deploy the application with this command:
> `gcloud app deploy`
1. Enable IAP for the App Engine app you created
1. [Lock down the permissions](https://cloud.google.com/appengine/docs/standard/go/service-account) of the App Engine service account

## Request format
Once deployed, your service should be available at a URL similar to the following:
`https://my-authenticated-fileserver.appspot.com/`
Any file name and path requested from this host should directly map to an object in GCS. For example

A request to
> `https://my-authenticated-fileserver.appspot.com/assets/heroimage.png`

will try to find the object
> `gs://my-asset-bucket/assets/heroimage.png`

Missing files will result in a 404 File Not Found error.

The application deduces the [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types) based on file extension. Therefore, requests without a file extension return a 400 Request Error. Ensure all the files you wish to serve have an accurate extension.

## Opportunities for customization
This code is intended to provide a plain authenticated file server. Often times, there are other requirements for transforming files before delivering them to the user. Here are a few ways this code can be modified to fit more specific needs:

* Image or document watermarking
* Image resizing and other alterations
* DLP redaction to hide sensitive information from users not authorized to view those parts
* PubSub event trigger
* Object request tallying and object deletion (for objects that can only be downloaded N times)
