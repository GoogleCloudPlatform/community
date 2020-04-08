---
title: Wix Media Platform Python SDK
description: The Wix Media Python SDK is useful for applications on Google App Engine and custom runtimes hosted on Google Compute Engine.
author: devlance
tags: Wix, media, Wix Media Python SDK
date_published: 2014-11-13
---

You can use [Wix Media Platform](wix-media.md) in client, server, and mobile applications on
various platforms and backend technologies. The Python SDK is useful for
applications on Google App Engine and custom runtimes hosted on Google Compute
Engine. [Learn more](wix-media)

## Before you begin

1. [Create a Wix Media Platform][mgr] account
   by connecting with your Google account. You can then upload media files to
   Wix Media Platform through the Media Manager or by using various widgets,
   APIs, and the Wix Media JavaScript SDK or Python SDK.

1. After signing in, copy the **API Key** and **API Secret** values. You will
   add these to your code to authenticate with the Wix Media Platform.

## Getting started with the Wix Media Platform sample app for Google App Engine

Wix Media provides a [sample app][wPython] that
allows you to quickly try out various aspects of their SDK. The following
instructions demonstrate getting the code, setting up a local development
server, and running the sample:

1. If you haven't already, install the [App Engine SDK for Python][gae_sdk].

1. Download the Python Github project:

        git clone https://github.com/wix/wixmedia-python.git

    or [download][wPythonZip] and extract the ZIP file:

        wget https://github.com/wix/wixmedia-python/archive/master.zip
        unzip master.zip

1. In the directory that you cloned or extracted the archive, copy the `wix`
   folder into the example App Engine project folder:

        cd wix-media-python
        cp -R wix examples/gae

1. Edit the `examples/gae/settings.py` file and update the `SECRET_KEY` variable to contain the value from your account in the [Wix Media Manager][mgr].

1. Start the local App Engine development server:

        [path_to_appengine_sdk]/dev_appserver.py examples/gae

1. Launch [http://localhost:8080](http://localhost:8080)
   to view the sample app. The sample demonstrates creating thumbnails using the Wix Media Python SDK.

Use this sample app to experiment with the various methods provided by the Wix
Media SDK. If you want to deploy the app, register a  Google Cloud Platform
project to create your App Engine project and get an application ID.

## Uploading media

The following example shows how to upload an image. Replace `[MY_KEY]` and
`[MY_SECRET]` with the values from your account in the
[Wix Media Manager][mgr].

    from wix import media

    client = media.Client(api_key="[MY_KEY]", api_secret="[MY_SECRET]")
    image  = client.upload_image_from_path('/files/images/cats.jpg')

    image_id = image.get_id()
    print image_id

This example returns the following image ID:

    ggl-685734655894940532967/images/ae1d86b24054482f8477bfbf2d426936/cats.jpg

## Rendering thumbnails

The following example is an App Engine application handler. Using Django
templates, the handler renders an HTML page with two thumbnails:

```py
class RenderImagesHandler(webapp2.RequestHandler):
    def get(self):
        # Image id's can be fetched from datastore ...
        image_ids = [
            'ggl-685734655894940532967/images/ae1d86b24054482f8477bfbf2d426936/cat.jpg',
            'ggl-685734655894940532967/images/c074a4a8ea854ee7b5b893ce2a0c7361/dog.jpg'
        ]

        context = {
            'thumbnail_urls': [
                RenderImagesHandler.create_image_thumbnail_url(image_id) for image_id in image_ids
            ]

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(render_to_string('example.html', context))

    @staticmethod
    def create_image_thumbnail_url(image_id):
        client = media.Client()
        image  = client.get_image_from_id(image_id)

        return image.srz(width=120, height=120).get_url()
```

## Additional resources

+ [WixMedia-Python project on GitHub][wPython]
+ [WixMedia platform overview][wDocs]
+ [WixMedia REST API][wRest]


[mgr]: http://mediacloud.wix.com/dashboard/index.html#/home
[gae_sdk]: /appengine/downloads
[wPython]: https://github.com/wix/wixmedia-python
[wPythonZip]: https://github.com/wix/wixmedia-python/archive/master.zip
[wPythonEx]: https://github.com/wix/wixmedia-python/tree/master/examples/gae
[wDocs]: http://mediacloud.wix.com/docs/
[wRest]: http://mediacloud.wix.com/docs/rest_api.html
