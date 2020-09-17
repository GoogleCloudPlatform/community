---
title: Wix Media Platform on Google Cloud Platform
description: Wix Media Platform is a collection of services for storing, serving, uploading, and managing image, audio, and video files.
author: devlance
tags: Wix, media
date_published: 2014-11-13
---

Wix Media Platform is a collection of services for storing, serving, uploading,
and managing image, audio, and video files. It includes the     following
components:

+ **Image Services** enable you to upload and serve images, as well as
manipulate images on-the-fly while serving.

+ **Video Services** automatically transcode your uploaded videos into a
variety of formats and resolutions. These services let you host and serve
video seamlessly across any Internet-connected device.

+ **Audio Services** enable you to upload and serve professional audio
files, which are automatically transcoded into web-friendly formats.

+ **Media Manager** lets you upload and organize media, as well as view
statistics about media serving.

+ **Playground** helps you produce ready-to-use code snippets and play
      with the services.
+ **SDKs** include client-side and server-side JavaScript libraries, and
      a server-side Python and PHP library, that wrap most of the REST APIs,
      making it easier to work with most of their functionality.


Wix Media Platform is now offered to developers as a service within Google
Cloud Platform.


 **Note**: Wix is a third-party company whose services are not covered by the
Google Cloud Platform Service Level Agreements.

## Get started

+ [**JAVASCRIPT**](wix-media-js)

+ [**PYTHON**](wix-media-python)

## Costs

You can find details about costs at
[Wix Media Platform Pricing](http://www.wixmp.com/docs/pricing.html).


## Media Platform Services

### Images

Wix Media Platform provides powerful image-processing services that support
resizing, cropping, rotating, sharpening, watermarking, and face detection, as
well as offer a number of filters and adjustments. Images can be easily served
with on-the-fly manipulations using the
[SDKs](http://www.wixmp.com/docs/getting_started.html) or the
[Image API](http://www.wixmp.com/docs/image-api.html).

### Audio

Wix Media Platform provides storage for professional, high-quality audio files
that can then be used in commercial music-selling applications. Learn more
about the [File Upload API](http://www.wixmp.com/docs/fileupload-api.html).

### Video

Video files uploaded to Wix Media Platform are automatically transcoded into
  additional formats of various qualities, enabling video playback on any
  browser or Internet-connected device. Learn more about the
[Video Upload API](http://www.wixmp.com/docs/video-api.html).

### Metadata

When you upload a file, Wix Media Platform automatically gives it a unique ID,
and then extracts and stores the file's metadata. You can access a file's
metadata,   such as an image's or video's width and height, or a video's
bitrate, format,   and processing status. You can organize and manage your files
using the  [Management API](http://www.wixmp.com/docs/management-api.html). You
can also create and manage collections of your media files by using the
[Collections API](http://www.wixmp.com/docs/collections-api.html). This API
enables you to create playlists of your media, regardless of their organization
in the folder structure. Media files can be stored once but included in multiple collections.

## Resources

You can use the Wix Media Platform's JavaScript or Python SDKs. The JavaScript
SDK works with Node.js as well as natively in the browser. In both cases, you
can use the SDKs in apps on either Google App Engine or Google Compute Engine.
The following documentation demonstrates getting started with each SDK:

+ [JavaScript](wix-media-js)
+ [Python](wix-media-python)
