---
title: Wix Media Platform JavaScript/Node.js SDK
description: The Wix Media JavaScript SDK is an isomorphic library. It works in Node.js and in the browser.
author: devlance
tags: Wix, media, Wix Media JavaScript SDK
date_published: 2014-11-13
---

The [Wix Media](wix-media.md) JavaScript SDK is an isomorphic library: it works in Node.js and
in the browser. The SDK provides a convenient API to access the Wix Media
Services image manipulation APIs. [Learn more](wix-media)

## Before you begin

You need to sign in to Wix Media Manager to create an account and you
need to prepare a Google Compute Engine virtual machine instance to host your
Node.js application.

1. [Create a Wix Media Platform][mgr] account
   by connecting with your Google account. You can then upload media files to
   Wix Media Platform through the Media Manager or by using various widgets,
   APIs, and the Wix Media JavaScript SDK or Python SDK.

1. After signing in, copy the **API Key** and **API Secret** values. You will
   add these to your code to authenticate with the Wix Media Platform.

1. [Quickly deploy Node.js on Compute Engine using Bitnami][bitnami] in just a
   few clicks.

1. After your instance is configured, connect to it using SSH. You
   can [connect using SSH from the browser][instances] or you can use the
   [`gcloud compute ssh [INSTANCE_NAME]`][ssh] command.

1. After Node.js is configured on your system, install the
   Wix Media JavaScript SDK by using the following command:

        npm install wixmedia

You now have a virtual machine instance running Node.js with the Wix Media
JavaScript SDK installed.

## Manipulating images

The following example shows how to manipulate an image using Node.js and the Wix
Media JavaScript SDK.

```js
var BASE_URL = "media.wixapps.netggl-685734655894940532967/images/";
var imageId = "ae1d86b24054482f8477bfbf2d426936"
var image = WixMedia.WixImage(BASE_URL, imageId, “cats.jpg”);
var crop = image.crop().w(1000).h(1000).x(100).y(100);
// prints out the new URL for an image that has width of 1000px and height of 1000px, cropped from 100, 100
console.log(crop.toUrl());
```

The [Wix Media JavaScript SDK][sdk] also
provides native JavaScript support that you can use in other runtimes, such as
in an App Engine application or other types of Compute Engine deployments.
[Learn more about the Wix Media JavaScript API][api].

## Additional resources

+ [WixMedia-Js project on GitHub][sdk]
+ [WixMedia platform overview][wDocs]
+ [WixMedia REST API][wRest]


[mgr]: http://mediacloud.wix.com/dashboard/index.html#/home
[ssh]: /sdk/gcloud/reference/compute/ssh
[nodeInstall]: https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager
[createInstance]: https://console.cloud.google.com/project/_/compute/instancesAdd
[instances]: https://console.cloud.google.com/project/_/compute/instances
[bitnami]: https://bitnami.com/stack/nodejs
[sdk]: https://github.com/wix/wixmedia-js
[api]: http://wix.github.io/wixmedia-js/
[wDocs]: http://mediacloud.wix.com/docs/
[wRest]: http://mediacloud.wix.com/docs/rest_api.html
