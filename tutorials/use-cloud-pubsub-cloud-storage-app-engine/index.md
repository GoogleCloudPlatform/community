---
title: Use Pub/Sub notifications and Cloud Storage with App Engine
description: Create a shared photo album using Pub/Sub, Cloud Storage, Datastore, and App Engine.
author: gchien44,cmwoods
tags: App Engine, PubSub, Cloud Storage, Datastore
date_published: 2017-09-05
---

Clara Woods | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial teaches you how to integrate several Google products to simulate a
shared photo album, hosted on App Engine standard environment and managed
through the Cloud Console. The web application has three pages:

*  Home/news feed, which displays notifications.
    ![Notifications Page](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/notifications-page.png)
*  Photos, which displays all uploaded photos in thumbnail form.
    ![Photos Page](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/photos-page.png)
*  Search, which allows the user to search for a specific term and displays the thumbnails applicable to the given term.
    ![Search Page](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/search-page.png)

Users interact with the web application only through the Cloud Platform Console;
photos cannot be uploaded or deleted through the website. Behind the scenes, two
buckets exist in [Cloud Storage](https://cloud.google.com/storage/): one to
store the uploaded photos and the other to store the thumbnails of the uploaded
photos. [Datastore](https://cloud.google.com/datastore/) stores all
non-image entities needed for the web application, which is hosted on
[App Engine](https://cloud.google.com/appengine/). Notifications of changes to
the Cloud Storage photo bucket are sent to the application by using
[Pub/Sub](https://cloud.google.com/pubsub/). The
[Google APIs Client Library for the Cloud Vision API](https://developers.google.com/api-client-library/python/apis/vision/v1)
is used to label photos for search.

A general overview of how the application works is shown in the diagrams below.

## Overview

### Receiving a notification

![Receiving a Notification](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/receiving-a-notification.png)

1.  A user uploads or deletes something from their Cloud Storage photo bucket.
1.  A Pub/Sub message is sent.
1.  The Pub/Sub message is received by App Engine.
1.  The Pub/Sub message is formatted and stored as a `Notification` in
    Datastore.
1.  If the event type from the message is `OBJECT_FINALIZE`, the uploaded photo
    is compressed and stored as a thumbnail in a separate Cloud Storage
    thumbnail bucket. If the event type from the message is `OBJECT_DELETE` or
    `OBJECT_ARCHIVE`, the thumbnail matching the name and generation number of
    the deleted or archived photo is deleted from the Cloud Storage thumbnail
    bucket. When an object is removed from your Cloud Storage photo bucket, the
    event type will be `OBJECT_DELETE` if [versioning](https://cloud.google.com/storage/docs/object-versioning)
    is not turned on for your bucket and `OBJECT_ARCHIVE` if versioning is
    turned on for your bucket.
1.  If the event type from the message is `OBJECT_FINALIZE`, then the Google
    Cloud Vision API is used to generate labels for the uploaded photo.
1.  If the event type from the message is `OBJECT_FINALIZE`, then a new
    `ThumbnailReference` is created and stored in Datastore. If the event
    type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, then the
    appropriate `ThumbnailReference` is deleted from Datastore.

### Loading the home page

![Loading Notifications](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-home-page.png)

1.  The user navigates to `[YOUR_PROJECT_ID].appspot.com`.
1.  A predetermined number of `Notifications` are queried from Datastore,
    ordered by date and time, most recent first.
1.  The queried `Notifications` are sent to the front-end to be formatted and
    displayed on the home page.
1.  The HTML file links to an external CSS file for styling.

### Loading the photos page

![Loading Photos](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-photos-page.png)

1.  The user navigates to `[YOUR_PROJECT_ID].appspot.com/photos`.
1.  All the `ThumbnailReferences` are fetched from Datastore, ordered by
    date and time, most recent first.
1.  Each `ThumbnailReference` is used to get a serving url for the corresponding
    thumbnail stored in the Cloud Storage thumbnail bucket.
1.  A dictionary of `ThumbnailReferences` and their serving urls is sent to the
    front-end to be formatted and displayed on the photos page.
1.  The HTML file links to an external CSS file for styling.

### Loading the search page

![Loading Search](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-search-page.png)

1.  The user navigates to `[YOUR_PROJECT_ID].appspot.com/search`. The user
    enters a search term.
1.  All the `ThumbnailReferences` are fetched from Cloud Datastore, ordered by
    date and time, most recent first.
1.  Each queried `ThumbnailReference` that contains the search term as one of
    its `labels` is used to get a serving url for the corresponding thumbnail
    stored in the Cloud Storage thumbnail bucket.
1.  A dictionary of `ThumbnailReferences` that contain the search term as one of
    their `labels` and their serving urls is sent to the front-end to be
    formatted and displayed on the search page.
1.  The HTML file links to an external CSS file for styling.

**Note**: Basic coding (Python, HTML, CSS, JavaScript) and command line knowledge is
necessary to complete this tutorial.

## Objectives

* Store photos in Cloud Storage buckets.
* Store entities in Datastore.
* Configure Pub/Sub notifications.
* Use the Cloud Vision API to implement a photos search.
* Create and deploy a shared photo album as an App Engine project to display
  actions performed through the Cloud Console.

## Costs

This tutorial uses billable components of Google Cloud, including:

* App Engine
* Cloud Storage
* Datastore
* Pub/Sub
* Cloud Vision API

Use the [pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538)
to generate a cost estimate based on your projected usage. New
users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Set up

1.  [Install the Cloud SDK](https://cloud.google.com/sdk/downloads) for
    necessary commands such as `gcloud` and `gsutil`.
1.  [Create a Google Cloud account](https://console.cloud.google.com/)
    for using the Cloud Console.
1.  Enable billing: [create a billing project](https://support.google.com/cloud/answer/6288653).
    Learn more about billing [here](https://cloud.google.com/appengine/docs/standard/python/console/).
1.  In the Cloud Console, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
    Your project has a unique ID that is part of your web application URL.
1. [Enable](https://support.google.com/cloud/answer/6158841) the Cloud Storage,
   Pub/Sub, Datastore, and Cloud Vision APIs.
1.  Open a terminal on your local machine. On the command line, [set the default project](https://cloud.google.com/sdk/docs/managing-configurations)
    to your newly created project by running the following command:

        gcloud config set project [YOUR_PROJECT_ID]

1.  Initialize an App Engine application within your project:

        gcloud app create --region [YOUR_REGION]
        
    To view the list of regions, run:

        gcloud app regions list

    Choose a region that supports the [App Engine standard environment](https://cloud.google.com/appengine/docs/standard/).
1.  In the Cloud Console, [create a bucket](https://cloud.google.com/storage/docs/creating-buckets)
    with `Regional` or `Multi-Regional` storage. The [storage class](https://cloud.google.com/storage/docs/storage-classes)
    does not matter as long as it is not `Nearline` or `Coldline`. This bucket
    is for storing the photos of your shared photo album.
1.  If you want collaborators on your photo album, add the desired collaborators
    as [`Storage Object Admins`](https://cloud.google.com/storage/docs/access-control/iam-roles)
    for your Cloud Storage photo bucket.

    **Note**: Collaborators must also have Google Cloud accounts.

1.  Change the Cloud Storage photo bucket permissions to make it publicly readable so that
    the photos may be viewed on your website. To do this, you'll need to
    [make your bucket data public](https://cloud.google.com/storage/docs/access-control/making-data-public#buckets).
1.  Create another bucket with `Multi-Regional` or `Regional` storage. This
    bucket is for storing the thumbnails of the photos in your shared photo album.
1.  [Create a new topic](https://cloud.google.com/pubsub/docs/quickstart-console#create_a_topic)
    with the same name as your photos bucket.
1.  Create a push subscription through the [command line](https://cloud.google.com/pubsub/docs/admin#create_a_push_subscription)
    or by clicking on the three-dots icon for your photo album topic and clicking on
    `New subscription`. Change the `Delivery Type` to `Push into an endpoint url`.
    This is the url that receives your Pub/Sub messages. For an endpoint url, use
    the following, replacing `[YOUR_PROJECT_ID]` with the ID of your project:

        https://[YOUR_PROJECT_ID].appspot.com/_ah/push-handlers/receive_message

1.  Configure Pub/Sub notifications for your Cloud Storage photo bucket:

        gsutil notification create -f json gs://[YOUR_PHOTO_BUCKET_NAME]

    Replace `[YOUR_PHOTO_BUCKET_NAME]` with the name of the photo bucket you
    created earlier.

## Basic application layout

If you do not feel like coding the entire application from scratch, feel free to
copy the [code for the default application](https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app) from GitHub by running:

    svn export https://github.com/GoogleCloudPlatform/community/trunk/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app

Note that if you choose this option, you still need to make a `lib` directory
and run the `install` command. These tasks are outlined in steps one and three
of the **Libraries and `app.yaml`** section. In addition to these tasks, some
constants in the `main.py` file still need to be changed to suit your Cloud
Storage bucket names. Look for the constants `THUMBNAIL_BUCKET`, `PHOTO_BUCKET`,
`NUM_NOTIFICATIONS_TO_DISPLAY`, and `MAX_LABELS` immediately after the imports
at the top of the file.

The rest of this tutorial assumes that you did not copy the default code, and
are building the application from scratch.

### Libraries and `app.yaml`

The external library and `app.yaml` files are necessary for configuring your App
Engine application and importing the required libraries.

1.  Choose a directory to house your project. From this point forward, this will
    be referred to as the host directory. Inside your host directory, create a
    new directory called `lib` for the storage of external libraries.
1.  In your host directory, create the file `requirements.txt` and copy in the
    following text:

        jinja2>=2.10.1
        webapp2==3.0.0b1
        GoogleAppEngineCloudStorageClient==1.9.22.1
        google-api-python-client==1.6.2

    This specifies which libraries are necessary for your application.

1.  Install the external libraries into your `lib` directory:

        pip install -t lib -r requirements.txt

1.  In your host directory, create the file `appengine_config.py` and copy in
    the following code:

        from google.appengine.ext import vendor
        vendor.add('lib')

1.  In your host directory, create an `app.yaml` file and copy in the following
    code:

        runtime: python27
        api_version: 1
        threadsafe: yes

        handlers:
        - url: /_ah/push-handlers/.*
          script: main.app
          login: admin

        - url: .*
          script: main.app

### HTML files

The HTML files represent the different pages of your web application.

1.  In your host directory, create a `templates` directory to hold all of your
    HTML files. Your basic HTML template file should have a `DOCTYPE` tag and
    `html` tag at the beginning, closed at the end of the file. Within the
    `html` tag you should have `head` and `body` sections. In the `head` tag,
    you should have the `title` of your page, and in the `body` tag you should
    add the links to the other pages of your website as well as the `h1` header
    of your current page. For an example, view the finished [`templates/notifications.html`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/notifications.html) file.
    Do not yet add anything to the HTML files except for this basic layout; the
    other code will be explained in later sections.
1.  Create an HTML file for the home/notifications page of your application
    (url: `http://[YOUR_PROJECT_ID].appspot.com`), following the instructions
    given in the previous step. The notifications page will have a news feed
    listing all recent actions performed on your Cloud Storage photo bucket.
1.  Create an HTML file for the photos page of your application
    (url:`http://[YOUR_PROJECT_ID].appspot.com/photos`). The photos page will
    display the thumbnails and names of all photos uploaded to your Cloud
    Storage photo bucket.
1.  Create an HTML file for the search page of your application
    (url: `http://[YOUR_PROJECT_ID].appspot.com/search`). The search page will
    display the thumbnails and names of the photos uploaded to your Cloud Storage
    photo bucket that match the entered search term.

### The `main.py` file

The `main.py` file contains the backend logic of the website, including
receiving Cloud Pub/Sub messages, communicating with Cloud Storage and
Datastore, and rendering HTML templates.

1.  Create a `main.py` file in your host directory.
1.  Add the required imports to the top of the file:

        import collections
        import json
        import logging
        import os
        import urllib

        import cloudstorage
        import jinja2
        import webapp2
        from google.appengine.api import images
        from google.appengine.ext import blobstore
        from google.appengine.ext import ndb
        import googleapiclient.discovery

1.  Add constants. `THUMBNAIL_BUCKET` is the name of the Cloud Storage bucket
    you created in Set up step #8 to store the thumbnails of photos uploaded to
    your Cloud Storage photo bucket. `PHOTO_BUCKET` is the name of the Cloud
    Storage bucket you created in Set up step #5 to store the photos uploaded to
    your shared photo album. `NUM_NOTIFICATIONS_TO_DISPLAY` regulates the
    maximum number of notifications displayed on the home/notifications page of
    your web application. `MAX_LABELS` regulates the maximum number of labels
    associated with each photo using Cloud Vision API.

        THUMBNAIL_BUCKET = '[YOUR_THUMBNAIL_BUCKET_NAME]'
        PHOTO_BUCKET = '[YOUR_PHOTO_BUCKET_NAME]'
        NUM_NOTIFICATIONS_TO_DISPLAY = [SOME_NUMBER]  # e.g. 5
        MAX_LABELS = [SOME_NUMBER]  # e.g. 10

1.  Set up [jinja2](http://jinja.pocoo.org/docs/2.9/templates/) for HTML
    templating.

        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        jinja_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir))

1.  Create the `Notification` class. `Notifications` are created from Cloud
    Pub/Sub messages and stored in Datastore, to be displayed on the home
    page of your application. `Notifications` have a message, date of posting, and
    generation number, which is used to distinguish between similar
    `notifications` and prevent the display of repeated `notifications`. These
    properties are stored as NDB model properties using the
    [Cloud Datastore NDB Client Library](https://cloud.google.com/appengine/docs/standard/python/ndb/),
    which allows App Engine Python apps to connect to Cloud Datastore.

        class Notification(ndb.Model):
            message = ndb.StringProperty()
            date = ndb.DateTimeProperty(auto_now_add=True)
            generation = ndb.StringProperty()

1.  Create the `ThumbnailReference` class. `ThumbnailReferences` are stored in
    Datastore and contain information about the thumbnails stored in your
    Cloud Storage thumbnail bucket. `ThumbnailReferences` have a `thumbnail_name`
    (the name of the uploaded photo), a `thumbnail_key` (a concatenation of the
    name and generation number of an uploaded photo, used to distinguish
    similarly named photos), date of posting, a list of label descriptions
    assigned to the corresponding photo using Cloud Vision API, and the
    url of the original photo that is stored in Cloud Storage.

        class ThumbnailReference(ndb.Model):
            thumbnail_name = ndb.StringProperty()
            thumbnail_key = ndb.StringProperty()
            date = ndb.DateTimeProperty(auto_now_add=True)
            labels = ndb.StringProperty(repeated=True)
            original_photo = ndb.StringProperty()

1.  Create a `MainHandler` with a `get` method for getting information from the
    server and writing it to the home/notification page HTML file. There are no
    values to pass into the template yet.

        class MainHandler(webapp2.RequestHandler):
            def get(self):
                template_values = {}
                template = jinja_environment.get_template('[NAME OF YOUR HOME PAGE HTML FILE]')
                self.response.write(template.render(template_values))

1.  Create a `PhotosHandler` class with a `get` method for getting information
    from the server and writing it to the photos page HTML file. This should
    look similar to the `MainHandler`.
1.  Create a `SearchHandler` class with a `get` method for getting information
    from the server and writing it to the search page HTML file. This should
    look similar to the `MainHandler` and `PhotosHandler`.
1.  Create a `ReceiveMessage` class with a `post` method for posting information
    to ther server. This `post` method will receive Cloud Pub/Sub messages and
    perform necessary logic using the information. Further detail is in the next
    section.

        class ReceiveMessage(webapp2.RequestHandler):
            def post(self):
                # This method will be filled out in the next section.

1.  Add the following code at the end of your `main.py` file to connect the web
    page urls with their corresponding classes.

        app = webapp2.WSGIApplication([
            ('/', MainHandler),
            ('/photos', PhotosHandler),
            ('/search', SearchHandler),
            ('/_ah/push-handlers/receive_message', ReceiveMessage)
        ], debug=True)

### Checkpoint

1.  [Run your application locally](https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server)
    by running the following command from your host directory:

        dev_appserver.py .

    Visit `localhost:8080` in your web browser to view your web application. You
    should be able to click on the links to  navigate between the pages of your
    website, which should all be blank except for the navigation links and page
    titles.

1.  [Deploy your application](https://cloud.google.com/appengine/docs/standard/python/getting-started/deploying-the-application)
    by running:

        gcloud app deploy

    Your web application should be viewable at
    `http://[YOUR_PROJECT_ID].appspot.com`. You can either navigate there
    directly through your web browser or launch your browser and view the app by
    running the command:

        gcloud app browse

## Creating the notifications page

The first step towards building your application is adding code to display
notifications on the home page. You'll do this by receiving Pub/Sub
messages, creating and storing notifications in Datastore, and writing the
notifications to the HTML page.

### Receiving Pub/Sub messages

During the setup phase, you configured [Pub/Sub push messages](https://cloud.google.com/pubsub/docs/push#receive_push)
to be sent to the url you specified for the `ReceiveMessage` class in your
`main.py` file. When you receive a Pub/Sub message, you must get necessary
information from it and acknowledge its reception.

1.  Obtain the [notification attributes](https://cloud.google.com/storage/docs/pubsub-notifications)
    from the incoming Pub/Sub message. Do this in your `main.py` file, in
    the `ReceiveMessage` class, in your `post` method. A logging statement can
    be used for easier debugging.

        # Logging statement is optional.
        logging.debug('Post body: {}'.format(self.request.body))
        message = json.loads(urllib.unquote(self.request.body))
        attributes = message['message']['attributes']

    `attributes` is a key:value dictionary where the keys are the Cloud Pub/Sub
    attribute names and the values are the attribute values.

1.  Acknowledge the reception of the Cloud Pub/Sub message.

        self.response.status = 204

1.  Save the relevant values from the `attributes` dictionary for later use.

        event_type = attributes.get('eventType')
        photo_name = attributes.get('objectId')
        generation_number = str(attributes.get('objectGeneration'))
        overwrote_generation = attributes.get('overwroteGeneration')
        overwritten_by_generation = attributes.get('overwrittenByGeneration')

1.  Create the `thumbnail_key` using the `photo_name` and `generation_number`.
    Note that using the following logic, only photos with the extensions `.jpg`
    can be uploaded effectively.

        try:
          index = photo_name.index('.jpg')
        except:
          return
        thumbnail_key = '{}{}{}'.format(
            photo_name[:index], generation_number, photo_name[index:])

You now have all of the information needed to create the necessary notification
and communicate with Cloud Storage.

### Creating and storing `Notifications`

1.  Write a `create_notification` helper function to generate notifications.
    Note that if the `event_type` is `OBJECT_METADATA_UPDATE`, the `message`
    field is `None`.

        def create_notification(photo_name,
                            event_type,
                            generation,
                            overwrote_generation=None,
                            overwritten_by_generation=None):
            if event_type == 'OBJECT_FINALIZE':
                if overwrote_generation is not None:
                    message = '{} was uploaded and overwrote an older' \
                        ' version of itself.'.format(photo_name)
                else:
                    message = '{} was uploaded.'.format(photo_name)
            elif event_type == 'OBJECT_ARCHIVE':
                if overwritten_by_generation is not None:
                    message = '{} was overwritten by a newer version.'.format(
                        photo_name)
                else:
                    message = '{} was archived.'.format(photo_name)
            elif event_type == 'OBJECT_DELETE':
                if overwritten_by_generation is not None:
                    message = '{} was overwritten by a newer version.'.format(
                        photo_name)
                else:
                    message = '{} was deleted.'.format(photo_name)
            else:
                message = None

            return Notification(message=message, generation=generation)

1.  Call the `create_notification` helper function in the `post` method of the
    `ReceiveMessage` class.

        new_notification = create_notification(
            photo_name,
            event_type,
            generation_number,
            overwrote_generation=overwrote_generation,
            overwritten_by_generation=overwritten_by_generation)

1.  Check if the new notification has already been stored. Pub/Sub
    messaging guarantees at-least-once delivery, meaning a Pub/Sub notification
    may be received more than once. If the notification already exists, there
    has been no new change to the Cloud Storage photo bucket, and the Pub/Sub
    notification can be ignored.

        exists_notification = Notification.query(
            Notification.message == new_notification.message,
            Notification.generation == new_notification.generation).get()

        if exists_notification:
            return

1.  Do not act for `OBJECT_METADATA_UPDATE` events, as they signal no change to
    the Cloud Storage photo bucket images themselves.

        if new_notification.message is None:
            return

1.  Store the new notification in Datastore. Because of the `if` statements
    added in the previous two steps, this, and all further code in the `ReceiveMessage`
    class, is only executed if the new notification is not a repeat and is not for an
    `OBJECT_METADATA_UPDATE` event.

        new_notification.put()

### Writing `Notifications` to the HTML file

1.  Fetch all `Notifications` from Datastore in reverse date order and
    include them in `template_values`, to be written to the `home/notifications`
    page HTML file. Do this in `main.py`, in the `MainHandler`, in the `get`
    method.

        notifications = Notification.query().order(
            -Notification.date).fetch(NUM_NOTIFICATIONS_TO_DISPLAY)
        template_values = {'notifications': notifications}

1.  In the [`templates/notifications.html`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/notifications.html)
    file, you can see a loop that displays the list you rendered to the template
    in `main.py` and prints the formatted date/time of each notification and the
    notification message. Copy that loop into the `body` of your own
    `notifications.html` file.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  [Upload an image](https://cloud.google.com/storage/docs/object-basics#upload)
    with the extension `.jpg` to your photo bucket.
1.  Open the `Products & services` menu again and navigate to `Datastore`. There
    should be a `Notification` listed with the message
    `[UPLOADED_PHOTO_NAME] was uploaded.`
1.  View your deployed application in your web browser. The new notification
    should be listed on the home page. You may need to refresh the page.

If you encounter errors, open the `Products & services` menu and navigate to
`Logging`. Use the messages there to debug your application.

## Implementing photo upload functionality

When a Pub/Sub notification is received, different actions occur depending
on the `eventType`. If the notification indicates an `OBJECT_FINALIZE` event,
the uploaded photo must be shrunk to a thumbnail, the thumbnail of the photo
must be stored in the Cloud Storage thumbnail bucket, the photo must be labeled
using the Cloud Vision API, and a `ThumbnailReference` must be stored in
Datastore.

Because these actions only occur in the case of a photo upload, an `if` block
should be used inside the `ReceiveMessage` class of `main.py`.

    if event_type == 'OBJECT_FINALIZE':
        # Photo upload-specific code here.

### Creating the thumbnail

To create the thumbnail, the original image from the Cloud Storage photo bucket
should be resized. Use the [Images Python API](https://cloud.google.com/appengine/docs/standard/python/images/)
to perform the required transformations.

1.  Write the `create_thumbnail` helper function.

        def create_thumbnail(photo_name):
            filename = '/gs/{}/{}'.format(PHOTO_BUCKET, photo_name)
            image = images.Image(filename=filename)
            image.resize(width=180, height=200)
            return image.execute_transforms(output_encoding=images.JPEG)

    This returns the thumbnail image data in a `string` format.

1.  Call the `create_thumbnail` helper function in the `post` method of the
    `ReceiveMessage` class.

        thumbnail = create_thumbnail(photo_name)

### Storing the thumbnail in Cloud Storage

The thumbnail should be stored in the Cloud Storage thumbnail bucket under the
name `thumbnail_key` in order to distinguish between different versions of the
same photo. Since two Cloud Pub/Sub notifications, an `OBJECT_FINALIZE` and an
`OBJECT_DELETE`/`OBJECT_ARCHIVE`, are sent in an arbitrary order in the case of
an overwrite, it is possible for two thumbnails with the same `thumbnail_name`
to exist in storage at once. Utilizing the `generation_number` of the photo in
the `thumbnail_key` ensures that the correct thumbnail is deleted when
necessary.

1.  Write the `store_thumbnail_in_gcs` helper function.

        def store_thumbnail_in_gcs(thumbnail_key, thumbnail):
            write_retry_params = cloudstorage.RetryParams(
                backoff_factor=1.1,
                max_retry_period=15)
            filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
            with cloudstorage.open(
                    filename, 'w', content_type='image/jpeg',
                    retry_params=write_retry_params) as filehandle:
                filehandle.write(thumbnail)

1.  Call the `store_thumbnail_in_gcs` helper function in the `post` method of
    the `ReceiveMessage` class.

        store_thumbnail_in_gcs(thumbnail_key, thumbnail)

### Labeling the photo using Cloud Vision

The [Python Google APIs Client Library for the Cloud Vision API](https://developers.google.com/api-client-library/python/apis/vision/v1)
can be used to [annotate](https://developers.google.com/resources/api-libraries/documentation/vision/v1/python/latest/vision_v1.images.html)
images, assigning them labels that describe the contents of the picture. You can
later use these labels to search for specific photos.

1.  Create the `uri` to reference the appropriate photo in the Cloud Storage
    photo bucket.

        uri = 'gs://{}/{}'.format(PHOTO_BUCKET, photo_name)

1.  Write the `get_labels` helper function.

        def get_labels(uri, photo_name):
            service = googleapiclient.discovery.build('vision', 'v1')
            labels = set()

            # Label photo with its name, sans extension.
            index = photo_name.index('.jpg')
            photo_name_label = photo_name[:index]
            labels.add(photo_name_label)

            service_request = service.images().annotate(body={
                'requests': [{
                    'image': {
                        'source': {
                            'imageUri': uri
                        }
                    },
                    'features': [{
                        'type': 'LABEL_DETECTION',
                        'maxResults': MAX_LABELS
                    }]
                }]
            })
            response = service_request.execute()
            labels_full = response['responses'][0].get('labelAnnotations')

            ignore = set(['of', 'like', 'the', 'and', 'a', 'an', 'with'])

            # Add labels to the labels list if they are not already in the list and are
            # not in the ignore list.
            if labels_full is not None:
                for label in labels_full:
                    if label['description'] not in labels:
                        labels.add(label['description'])
                        # Split the label into individual words, also to be added to
                        # labels list if not already.
                        descriptors = label['description'].split()
                        for descript in descriptors:
                            if descript not in labels and descript not in ignore:
                                labels.add(descript)

            return labels

1.  Call the `get_labels` helper function in the `post` method of the
    `ReceiveMessage` class.

        labels = get_labels(uri, photo_name)

The `labels` list has now been obtained and can be used to build the
`ThumbnailReference`.

### Creating and storing the `ThumbnailReference`

At this point, the only other thing you need to create the required
`ThumbnailReference` is the url of the original photo. Obtain this, and the
`ThumbnailReference` can be created and stored.

1.  Write the `get_original_url` helper function to return the url of the
    original photo.

        def get_original_url(photo_name, generation):
            original_photo = 'https://storage.googleapis.com/' \
                '{}/{}?generation={}'.format(
                    PHOTO_BUCKET,
                    photo_name,
                    generation)
            return original_photo

1.  Call the `get_original_url` helper function in the `post` method of the
    `ReceiveMessage` class.

        original_photo = get_original_url(photo_name, generation_number)

1.  Create the `ThumbnailReference` using the information gathered from the
    Pub/Sub message, `get_labels` function, and `get_original_url`
    function.

        thumbnail_reference = ThumbnailReference(
                    thumbnail_name=photo_name,
                    thumbnail_key=thumbnail_key,
                    labels=list(labels),
                    original_photo=original_photo)

1.  Store the newly created `ThumbnailReference` in Cloud Datastore.

        thumbnail_reference.put()

You have now completed all of the code necessary to store the information about
an uploaded photo in Cloud Storage and Datastore.

### Writing thumbnails to the photos HTML file

1.  Write the `get_thumbnail_serving_url` helper function. This function returns
    a [serving url](https://cloud.google.com/appengine/docs/standard/python/images/#get-serving-url)
    that accesses the thumbnail from the Cloud Storage thumbnail bucket.

        def get_thumbnail_serving_url(photo_name):
            filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, photo_name)
            blob_key = blobstore.create_gs_key(filename)
            return images.get_serving_url(blob_key)

1.  Fetch all `ThumbnailReferences` from Datastore in reverse date order.
    Create an ordered dictionary, calling upon the `get_thumbnail_serving_url`
    helper function, with the thumbnail serving urls as keys and the
    `ThumbnailReferences` as values. Include the dictionary in
    `template_values`, to be written to the appropriate HTML file. Do this in
    `main.py`, in the `PhotosHandler`, in the `get` method.

        thumbnail_references = ThumbnailReference.query().order(
            -ThumbnailReference.date).fetch()
        thumbnails = collections.OrderedDict()
        for thumbnail_reference in thumbnail_references:
            img_url = get_thumbnail_serving_url(thumbnail_reference.thumbnail_key)
            thumbnails[img_url] = thumbnail_reference
        template_values = {'thumbnails': thumbnails}

1.  In the [`templates/photos.html`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/notifications.html) file,
    you can see that it loops through the thumbnails dictionary you rendered to
    the template in `main.py` and displays each thumbnail image and its name.
    Copy that loop to your own `photos.html` file.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Upload an image with the extension `.jpg` to your Cloud Storage photo bucket.
1.  Check that the thumbnail version of your newly uploaded photo is in your
    Cloud Storage thumbnail bucket under the correct name.
1.  Check that in Cloud Datastore, there is a `Notification` listed with the
    message `[UPLOADED_PHOTO_NAME] was uploaded.`
1.  Check that in Cloud Datastore, there is a `ThumbnailReference` listed with
    the appropriate information.
1.  View your deployed application in your web browser.
    1. Check that the new notification is listed on the home page. You may need
        to refresh the page.
    1. Check that the thumbnail and name of the uploaded photo are displayed on
        the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Implementing photo delete/archive functionality

If the received Pub/Sub notification indicates an `OBJECT_DELETE` or
`OBJECT_ARCHIVE` event, the thumbnail must be deleted from the Cloud Storage
thumbnail bucket, and the `ThumbnailReference` must be deleted from
Datastore.

Because these actions only occur in the case of a photo delete or archive, an
`elif` statement can be used inside the `ReceiveMessage` class of `main.py`,
where the initial `if` statement of the block is the one specifying the event
type as `OBJECT_FINALIZE`.

    elif event_type == 'OBJECT_DELETE' or event_type == 'OBJECT_ARCHIVE':
        # Photo delete/archive-specific code here.

1.  Write the `delete_thumbnail` helper function to delete the specified
    thumbnail from the Cloud Storage thumbnail bucket and delete the
    `ThumbnailReference` from Datastore.

        def delete_thumbnail(thumbnail_key):
            filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
            blob_key = blobstore.create_gs_key(filename)
            images.delete_serving_url(blob_key)
            thumbnail_reference = ThumbnailReference.query(
                ThumbnailReference.thumbnail_key == thumbnail_key).get()
            thumbnail_reference.key.delete()

            filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
            cloudstorage.delete(filename)

1.  Call the `delete_thumbnail` helper function in the `post` method of the
    `ReceiveMessage` class.

        delete_thumbnail(thumbnail_key)

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Delete an image from your Cloud Storage photo bucket.
1.  Check that the thumbnail version of your deleted photo is no longer in your
    Cloud Storage thumbnail bucket.
1.  Check that in Datastore, there is a `Notification` listed with the
    message `[DELETED_PHOTO_NAME] was deleted.`
1.  Check that in Datastore, the `ThumbnailReference` for your deleted
    photo is no longer listed.
1.  View your deployed application in your web browser.
    1.  Check that the new notification is listed on the home page. You may need
        to refresh the page.
    1.  Check that the thumbnail and name of the uploaded photo are no longer
        displayed on the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Creating the search page

The search page of the web application has a search bar users can enter a
`search-term` into. The `ThumbnailReferences` with the `search-term` in their
`labels` lists are added to the thumbnails dictionary and used to obtain and
display the correct thumbnails in the search page.

1.  Fill out the `get` method. The method is found in `main.py` in the
    `SearchHandler` class.
    1.  Get the `search-term` from the user. The `search-term` should be
        converted to lower case to avoid case sensitivity.

            search_term = self.request.get('search-term').lower()

    1.  In a similar manner as in the `PhotosHandler`, build an ordered
        dictionary with thumbnail serving urls as keys and `ThumbnailReferences`
        as values. However, unlike in the `PhotosHandler`, although you query
        all `ThumbnailReferences` from Datastore, you should only add the
        thumbnails labeled with the `search-term` to the dictionary.

            references = ThumbnailReference.query().order(
                -ThumbnailReference.date).fetch()
            # Build dictionary of img_url of thumbnails to
            # thumbnail_references that have the given label.
            thumbnails = collections.OrderedDict()
            for reference in references:
                labels = reference.labels
                if search_term in labels:
                    img_url = get_thumbnail_serving_url(reference.thumbnail_key)
                    thumbnails[img_url] = reference

    1.  Include the thumbnails dictionary in `template_values`, to be written to
        the search page HTML file.

            template_values = {'thumbnails': thumbnails}

1.  In the [`search.html`](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/notifications.html) file,
    you can see that it defines the HTML for a search bar. And like in the
    photos page HTML file, it loops through the thumbnails dictionary you
    rendered to the template in `main.py`, and displays each thumbnail image and
    its name. It also includes an `else` statement as part of the loop to
    specify behavior in the case the thumbnails dictionary is empty (no search
    results returned). Copy the search bar and loop to your own `search.html`
    file.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  View your deployed application in your web browser. Try using the search
    bar. When you search, the applicable photos should appear in a similar
    manner as the photos page, or else the text `No Search Results` should be
    displayed.

**Note**: Examining the `labels` lists of the `ThumbnailReferences` in Cloud
Datastore can help you determine whether or not the search is functioning as it
is meant to.

If you encounter errors, use the `Logging` messages to debug your application.

#### Congratulations! You now have a functioning shared photo album.

**Note**: Other users you listed as collaborators during the `Set up` section should
also be able to modify the images in your Cloud Storage photo bucket and see their
changes take effect on the website. However, this must be done through the command
line using [gsutil](https://cloud.google.com/storage/docs/gsutil), as your project
does not appear in their Cloud Console.

## Style

Now that you have a functioning website, it's time to add formatting to it.
You'll do this by adding CSS and JavaScript to your already existing HTML files.

### Set up

Before you start incorporating CSS, you have to tell your app to expect a CSS
file and where to find it.

1.  Create a directory inside your host directory to hold your external style sheet.
1.  Open your `app.yaml` file and include the following, replacing
    `[DIRECTORY_NAME]` with whatever you named your directory in step 1.

        - url: /[DIRECTORY_NAME]
            static_dir: [DIRECTORY_NAME]

        - url: /static
            static_dir: static

    Note that this code should go in the `handlers` section of your `app.yaml`
    file and must be above

        - url: .*
            script: main.app

1.  Inside the directory you created, create a CSS file. Leave it blank for now;
    you'll add code to it in the following sections. Note that your file must
    have the extension `.css`.

### Adding style common to every page

First, you'll style the HTML components present on every page of the website.
This includes the body, the links to other pages, and the title of the page. You
should run your app locally after each step to see the changes.

1.  Add the `link` tag to the top of each of your HTML files, as seen in the
    [finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/).
1.  Add the following code to your `CSS` file to set the background color.
    Replace [COLOR] with a color of your choice.

        body {
          background-color: [COLOR];
        }

    You can specify the color by typing in the name of it, such as `blue`, by
    specifying the rgb configuration, or by giving a hexadecimal representation.
    You can find more information on how colors work in CSS [here](https://www.w3schools.com/css/css_colors.asp).

1.  Next you'll create a box to hold the links to other pages. Add the following
    code to your `CSS` file.

        ul.links {
          list-style-type: none;
          margin: 0;
          padding: 0;
          width: 10%;
          background-color: [COLOR];
          position: fixed;
        }

    Note that you should make the `background-color` here different from the color
    in step 1; otherwise it won't look any different than before. Setting the
    width to 10% makes the links box take up 10% of the page. If you change the
    width of your browser around, you should see the links box change with it.
    Setting the position to fixed keeps the link box in the top left corner of
    your webpage even if you scroll down.

1.  You can center the links within their box and change their color by adding
    the following code.

        ul.links li a {
          display: block;
          color: [COLOR];
          padding: 8px 8px;
          text-align: center;
          font-family: '[FONT]', [STYLE];
          border-bottom: 1px solid [COLOR];
        }

    If `font-family` is not specified, the default font will be used. You can
    [choose a font](https://fonts.google.com/) by clicking on one that appeals
    to you and then clicking `Select This Font`. Open the selected font on the
    bottom of your screen and follow the instructions to link it to your html
    and CSS files. The style of the font will be either `serif` or `sans-serif`.

    The `border-bottom` property adds a dividing line between each link. To avoid
    having an extra line at the bottom of the links box, add:

        ul.links li:last-child {
          border-bottom: none;
        }

1.  To change the color of each link and its background when it is hovered over
    with the cursor, add:

        ul.links li a:hover {
          background-color: [COLOR];
          color: [COLOR];
        }

1.  The title of the page is contained in the `h1` HTML blocks. You can center
    it, set the color, font, and font size, and add an underline with the
    following block of code.

        h1 {
          color: [COLOR];
          text-align: center;
          font-family: '[FONT]', [STYLE];
          font-size: [SIZE]px;
          border-bottom: 3px solid [COLOR];
          padding: 15px;
          width: 60%;
          margin: auto;
          margin-bottom: 30px;
        }

   `text-align: center` centers the title in the middle of the page.
   `border-bottom` adds the underline. `padding` sets the space between the
   title and the underline. `width` sets how much of the screen the underline
   occupies. `margin: auto` centers the underline. `margin-bottom` sets the
   spacing between the underline and anything that might go below it. This will
   be applicable in later sections.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Click through the links on each page and make sure the colors and placement
    remain consistent.
1.  Resize your browser window and observe how the components dynamically change
    to account for this.

### Styling the home (notifications) page

Now that you have the basic styling done for the website as a whole, you can
focus on styling the elements unique to each page, starting with the home page.

1.  Indent the notification messages. In your CSS file add:

        ul.notification {
          margin: 10px;
          margin-left: 20%;
          list-style-type: [STYLE];
          font-family: '[FONT]', [STYLE];
        }

    `list-style-type` sets what kind of list the notifications appear in.
    [Pick a value](https://www.w3schools.com/cssref/pr_list-style-type.asp#propertyvalues)
    for it. The `font-family` you choose will affect how the `list-style-type`
    appears.
1.  You can set the color of your bullet points, roman numerals, or whatever
    `list-style-type` you chose above by adding:

        ul.notification li {
          color: [COLOR];
        }

1.  Set the font for the notification message:

        ul.notification li p {
          font-size: [SIZE]px;
          font-family: '[FONT]', [STYLE];
          color: [COLOR];
        }

### Styling the search bar on the search page

Because the search bar is only a feature of the search page, you could style it
directly within the HTML file that controls the search page. However, you'll add
more style instructions for the search bar than you did for displaying the
notifications, so you'll put the style for it in your CSS file to keep the HTML
file from getting too cluttered.

1.  In the CSS file, add style for the `h2` tag that gets displayed when there
    are no search results.

        h2 {
          color: [COLOR];
          text-align: center;
          font-size: [SIZE]px;
          font-family: '[FONT]', [STYLE];
        }

1.  In the CSS file, add code to center the search bar and place it `50px` below
    the underlined title.

        form.search {
          text-align: center;
          font-family: '[FONT]', [STYLE];
          margin-top: 50px;
        }

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Visit the home page to see the notification messages indented and notice
    that the date and time part is smaller than the actual message.
1.  Visit the search page to see the search bar centered along with the
    `"No Search Results"` text.

### Styling the thumbnails for both the photos and search pages

The thumbnails displayed on your website currently should appear in a single
vertical column on the left of the page. In this section you'll reformat them to
appear in a table format.

1.  Add HTML in the files that control the photos and search pages. The code
    instructions for this step should be implemented in both the photos page
    HTML file and the search page HTML file. See the
    [finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/)
    for examples.

    1.  Add a gallery class outside the for loop to hold all the thumbnails,
        such as `gallery`.
    1.  Add class names to the `div` tags inside the for loop, such as `thumbnail`
        and `descent`.

1.  Add CSS to format the classes you just added. The code instructions for this
    step only need to be implemented once in your external CSS file. As long as
    you have the same class names in the two HTML files from step 1, the code
    n this section will be applied to both pages automatically.

    1.  Set the margins on the gallery class so the thumbnails don't appear too
        far on the left of the page (they would interfere with the links if the
        page scrolled down) and appear centered, i.e. not too far on the right
        of the page either.

            div.gallery {
              margin-left: 12%;
              margin-right: 10%;
            }

    1.  Use the thumbnail class to create a box to hold the thumbnail image and
        its caption:
        
            div.thumbnail {
              margin: 5px;
              float: left;
              width: 180px;
              height: 240px;
              border: 1px solid [COLOR];
            }

        `margin` sets the spacing between the thumbnails. The `width` and
        `height` properties match the width and height that thumbnails are
        sized to in `main.py`. `border` outlines the box. You can remove this
        line if you don't want a visible border around your thumbnail boxes.

    1.  Further format the thumbnail class to display thumbnails in a table:

            div.thumbnail:after {
              content: "";
              display: table;
              clear: both;
            }

    1.  Center the thumbnail image within the thumbnail box:

            div.thumbnail img {
              display: block;
              margin: auto;
            }

        Note that while the width of the thumbnail box is 180 pixels, the same
        width that thumbnails are resized to in `main.py`, portrait oriented
        photos may have a smaller width. This ensures that photos are centered
        within the 180 pixels even when they do not occupy 180 pixels.
    1.  Center the caption 10 pixels below the thumbnail image using the
        `descent` class:

            div.descent {
              padding: 10px;
              text-align: center;
              font-family: '[FONT]', [STYLE];
            }

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Navigate to the photos page and check that the thumbnails displayed there
    now appear in a table format with their captions centered underneath.
1.  Navigate to the search page and enter a search term that will yield results.
    The displayed thumbnails should appear in the same format as on the photos
    page.

### Making thumbnails clickable

Now that your thumbnails are nicely formatted, you can make your webpage display
the original photo when a thumbnail is clicked on by incorporating JavaScript
into your HTML files.

1.  Note in [the finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/)
    that the thumbnails have IDs, allowing the images to be
    looked up by id, which is how you will implement an onclick function to
    display the original photo when its thumbnail is clicked.

    `myModal` is what will be displayed when a thumbnail is clicked on. The
    `close` class is what restores the thumbnail view when it is clicked on.
    `closeModal()` is a JavaScript function you'll define in step 3. The class
    `modal-content` includes `mySlides` and the `caption-container`. Only one
    `mySlides` will be displayed at a time with its image. The `caption` will be
    updated to match the `mySlides` being displayed.

1.  Add styling to your external CSS file. This will format both the photos and
    search pages as long as they have the same class names for the HTML you just
    added.

    1.  Add an effect to the thumbnails so that when the cursor hovers over
        them, they turn slightly transparent and the cursor changes to a pointer
        to indicate to the user that they can click on thumbnails.

            div.thumbnail img:hover {
              opacity: 0.7;
              cursor: pointer;
            }

    1.  Format the `modal` that takes over the whole page when a thumbnail is
        clicked:

            div.modal {
              display: none;
              position: fixed;
              z-index: 1;
              padding-top: 100px;
              left: 0;
              top: 0;
              width: 100%;
              height: 100%;
              overflow: auto;
              background-color: rgba(0,0,0,0.95
            }

        `display` is initially set to none because the modal should only be
        displayed when a thumbnail is clicked. The logic for this will be added
        in step 3. `width` and `height` are set to 100% to take up the whole
        page. `background-color` is set to a somewhat transparent black so
        thumbnails will still be partially visible behind the modal.

    1.  Place the `close` button in the top right corner of the modal:

            span.close {
              position: absolute;
              top: 15px;
              right: 35px;
              color: #f1f1f1;
              font-size: 40px;
              font-weight: bold;
              transition: 0.3s;
            }

    1.  Add hover and focus effects to the `close` button:

            span.close:hover,
            span.close:focus {
              color: #bbb;
              text-decoration: none;
              cursor: pointer;
            }

    1.  Format `modal-content`, the box that will hold the original photo and
        caption.

            div.modal-content {
              position: relative;
              margin: auto;
              padding: 0;
              width: 55%;
              max-width: 700px;
            }

        This centers `modal-content` and sets it to take up 55% of the page,
        with a max width of 700 pixels. This means that even if 700 pixels is
        less than 55% of the page, `modal-content` will never be wider than 700
        pixels.

    1.  Set the default display of `mySlides` to none:

            div.mySlides {
              display: none;
            }

    1.  Format the image in `mySlides` to match the width of `modal-content`:

            div.mySlides img {
              display: block;
              margin: auto;
              width: 100%;
              max-width: 700px;
              height: auto;
            }

        `height` is set to auto so the image will retain its original proportions.

    1.  Position `caption-container` below the image in the `modal-content` box,
        where `[COLOR]` is the color the caption text     will be.

            .caption-container {
                text-align: center;
                padding: 2px 16px;
                color: [COLOR];
            }

    1.  Format the `caption` to be centered in `caption-container` and have a
        height of 20 pixels:

            #caption {
              margin: auto;
              display: block;
              width: 80%;
              max-width: 700px;
              text-align: center;
              font-family: '[FONT]', [STYLE];
              padding: 10px 0;
              height: 20px;
            }

1.  Add JavaScript embedded within the HTML. The instructions in this section
    will need to be implemented in both HTML files associated with the photos
    and search pages. Add the following JavaScript to a `script` tag in the
    `body`. See the [finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/)
    for all the JavaScript that needs to be added.

    1.  Implement the function to close the modal after the end of the `gallery`
        class.

            function closeModal() {
                document.getElementById('myModal').style.display = "none";
            }

        This function is called whenever the close button is clicked on and
        resets the `modal` class to not be displayed.

    1.  Within the `gallery` class after the `modal` class, add a for loop and
        embedded script. See the [finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/)
        for the loop and JavaScript that needs to be added.

        This defines a function that gets called whenever a thumbnail is clicked
        on. The `modal` class is displayed and another function, `currentSlide`
        is called.

    1.  Add a variable and implement `currentSlide()` in the same script that
        contains `closeModal()`.

            var slideIndex;

            function currentSlide(n) {
                slideIndex = n;
                showSlides(slideIndex);
            }

        Note that `currentSlide()` calls another function, `showSlides()`.
        You'll implement this next.

    1.  Implement `showSlides`:

            function showSlides(n) {
                var i;
                var slides = document.getElementsByClassName('mySlides');
                var captionText = document.getElementById("caption");
                var image = document.getElementById(slideIndex + "");
                for (i = 0; i < slides.length; i++) {
                slides[i].style.display = "none";
                }
                slides[slideIndex-1].style.display = "block";
                captionText.innerHTML = image.alt;
            }

        This function sets every `mySlides` class to not be displayed except for
        the one that contains the original photo of the thumbnail that was
        clicked. The caption is set to the name of the image displayed.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Navigate to the photos page and hover over a thumbnail. It should become
    less opaque and your cursor should change.
1.  Click on a thumbnail. Observe that the original photo with caption appears
    over the photos page.
1.  Close the modal and restore the thumbnail view.
1.  Check that the search page has the same behavior.

### Making photos scrollable

The next feature to add to your website is scrolling. After clicking on a
thumbnail, the original photo appears. In this section, you'll add the ability
to scroll to either side of that photo and see the original photos of other
thumbnails without having to close the modal and reopen it by clicking on
another thumbnail.

1.  Add HTML for both the photos and search pages. The instructions for this
    step should be implemented in your two HTML files responsible for the photos
    and search pages. See the [finished HTML files](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/) for an example.

    1.  Within the `mySlides` class add the class `numbertext`. This will
        display the current number of the photo displayed, i.e. `1/5`.

        `loop.index` is the current iteration of the `for` loop, and
        `thumbnails|length` is the total number of iterations the `for` loop
        will go through.

    1.  After the `for` loop containing `mySlides`, add the `prev` and `next`
        classes to the two buttons, respectively.

        `&#10094` and `&#10095` are the HTML codes for previous and next arrows,
        respectively. The `plusSlides()` function will be implemented in Step 3.

1.  Add styling to your external CSS file. This will format both the photos and
    search pages as long as they have the same class names for the HTML you just
    added.

    1.  Place the `numbertext` class in the top left of the original photo:

            .numbertext {
              color: [COLOR];
              font-size: 12px;
              font-family: '[FONT]', [STYLE];
              padding: 8px 12px;
              position: absolute;
              top: 0;
            }

    1.  Place the next and previous arrows over the photo:

            .prev,
            .next {
              cursor: pointer;
              position: absolute;
              top: 50%;
              width: auto;
              padding: 15px;
              margin-top: -20px;
              color: white;
              font-weight: bold;
              font-size: 20px;
              font-family: '[FONT]', [STYLE];
              transition: 0.6s ease;
              border-radius: 0 3px 3px 0;
              user-select: none;
              -webkit-user-select: none;
            }

    1.  Reposition the next arrow to be on the right side of the photo:

            .next {
              right: 0;
              border-radius: 3px 0 0 3px;
            }

    1.  Add hover effects to arrows:

            .prev:hover,
            .next:hover {
              background-color: rgba(0, 0, 0, 0.8);
            }

1.  Add JavaScript embedded within the HTML. The instructions in this section
    will need to be implemented in both HTML files associated with the photos
    and search pages.

    1.  Implement the plusSlides function:

            function plusSlides(n) {
              slideIndex +=n;
              showSlides(slideIndex);
            }

    1.  Additional logic needs to be added to `showSlides` to allow wrapping
        around from the last photo to the first photo and when the next arrow is
        clicked and vice versa. Add the following two lines of code above where
        `var image` is declared.

            if (n > slides.length) {slideIndex = 1}
            if (n < 1) {slideIndex = slides.length}

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Navigate to the photos page and click on a thumbnail. The photo that appears
    should now have next and previous arrows as well as a number in the top left
    corner. Click the arrows to scroll through the photos. Check that the
    caption updates correctly as you scroll.
1.  Verify that when you click the previous arrow on the first photo, the last
    photo appears, and that when you click the next arrow on the last photo, the
    first photo appears.
1.  Navigate to the search page and search for something. Clicking on the
    thumbnail results should display the same behavior as on the photos page.

### Adding labels to photos in scrolling view

The last feature you will add to your application is showing the labels
associated with a photo when that photo is displayed in the scrolling view. This
feature will only appear on the photos page and will let users know what search
terms they can use to search for the displayed photo.

1.  Add HTML to your file responsible for the photos page.

    1.  Add a `div` with the class `labels-container` , as seen in [the finished photos.html file](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-photo-album-app/templates/photos.html).

        This will add all the labels associated with each thumbnail into
        `myLabels`. When that thumbnail's corresponding original photo is
        displayed, the `myLabels` class corresponding to that thumbnail will be
        displayed and show all the searches in which the photo will show up.

    1.  Change the name of your `prev` and `next` classes to `prevPhotos` and
        `nextPhotos`. Arrows will need to be positioned differently on the
        photos and search pages because there will be a different offset needed
        to center the arrows on the photo. This is due to the added information
        about labels below the photo on the photos page.

1.  Add styling to your external CSS file.

    1.  First, position the `labels-container` below the `caption-container`:

            div.labels-container {
              text-align: center;
              color: [COLOR];
              margin: 0;
            }

    1.  Next, format the `labels` id:

            #labels {
              margin: auto;
              display: block;
              width: 80%;
              max-width: 700px;
              text-align: center;
              font-family: '[FONT]', [STYLE];
              padding: 10px 0;
              font-size: [SIZE]px;
            }

    1.  You'll also want to format the list of labels held in `myLabels`:

            div.myLabels {
              display: none;
              margin: 0;
              text-align: center;
              font-family: '[FONT]', [STYLE];
              font-size: [SIZE]px;
            }

    1.  Finally, you'll need to reset `margin-top` for the prev and next arrows.
        In your

            .prev,
            .next {
              ...
            }

        style block, add `prevPhotos` and `nextPhotos` to be formatted:

            .prev,
            .next,
            .prevPhotos,
            .nextPhotos {
              ...
            }

        Add a new style block, to keep `prevPhotos` and `nextPhotos` centered on
        the photo after the addition of the `labels-container`:

            .prevPhotos,
            .nextPhotos {
              margin-top: -90px;
            }

        Add `.nextPhotos` to the repositioning of the `next` arrow:

            .next,
            .nextPhotos {
              right: 0;
              border-radius: 3px 0 0 3px;
            }

        Add `.prevPhotos:hover` and `.nextPhotos:hover` effects:

            .prev:hover,
            .next:hover,
            .prevPhotos:hover,
            .nextPhotos:hover {
              background-color: rgba(0, 0, 0, 0.8);
            }

1.  Add JavaScript. Modify the `showSlides(n)` function:

        function showSlides(n) {
          var i;
          var slides = document.getElementsByClassName('mySlides');
          var captionText = document.getElementById("caption");
          var labels = document.getElementsByClassName('myLabels');
          if (n > slides.length) {slideIndex = 1}
          if (n < 1) {slideIndex = slides.length}
          var image = document.getElementById(slideIndex + "");
          for (i = 0; i < slides.length; i++) {
            slides[i].style.display = "none";
            labels[i].style.display = "none";
          }
          slides[slideIndex-1].style.display = "block";
          captionText.innerHTML = image.alt;
          labels[slideIndex-1].style.display = "block";
        }

    This will show the correct `myLabels` the same way the correct `mySlides` is
    shown.

### Checkpoint

1.  Run your application locally to check for basic errors, then deploy your
    application.
1.  Navigate to the photos page and click on a thumbnail. Verify that the
    correct labels are shown underneath the caption.
1.  Scroll through some photos to see the labels change to match the currently
    displayed photo.

Congratulations! You've completed this tutorial and now have a functioning, user-friendly website!

## Clean up

1.  If necessary, [close your billing account](https://support.google.com/cloud/answer/6288653).
1.  [Delete your project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

    **Note**: You won't be able to use this project ID again.
