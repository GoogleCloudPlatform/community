---
title: How to Use Cloud Pub/Sub Notifications and Cloud Storage with App Engine
description: Create a shared photo album using Cloud Pub/Sub, Cloud Storage, Datastore, and App Engine.
author: ggchien, cmwoods
tags: App Engine, Cloud Pub/Sub, Cloud Storage, GCS, Datastore, photo album
date published:
---
Some sort of intro here.

## Objectives

* Store photos in Google Cloud Storage buckets.
* Store entities in Datastore.
* Configure Cloud Pub/Sub notifications.
* Use Google Cloud Vision to implement a photos search.
* Create and deploy a shared photo album as an App Engine project to display actions performed through the Cloud Platform Console.

## Costs

This tutorial uses billable components of Cloud Platform, including:

* Google App Engine
* Google Cloud Storage
* Google Cloud Datastore
* Google Cloud Pub/Sub
* Google Cloud Vision

Use the [pricing calculator](https://cloud.google.com/products/calculator/#id=411d8ca1-210f-4f2c-babd-34c6af2b5538) to generate a cost estimate based on your projected usage. New Cloud Platform users might be eligible for a [free trial](https://cloud.google.com/free-trial).

## Overview

This tutorial teaches you how to integrate several Google products to simulate a shared photo album, hosted on App Engine and managed through the Cloud Platform Console. The diagram below shows the overall flow of the application:

![alt text](link to image here "Shared Photo App Workflow")

Two buckets exist in [Cloud Storage](https://cloud.google.com/storage/) (GCS): one to store the uploaded photos themselves, and the other to store the thumbnails of the uploaded photos. [Cloud Datastore](https://cloud.google.com/datastore/) stores all non-image entities needed for the web application, which is hosted on [App Engine](https://cloud.google.com/appengine/). Notifications of changes to the GCS photo bucket are sent to the application via [Cloud Pub/Sub](https://cloud.google.com/pubsub/). The [Google Cloud Vision API Client Library](https://developers.google.com/api-client-library/python/apis/vision/v1) is used to label photos for search. Further detail is revealed in later portions of this tutorial.

Note: Basic coding (Python, HTML, CSS, Javascript) and command line knowledge is necessary to complete this tutorial.

## Set Up

The following instructions assume no prior set up has been done. Skip steps appropriately if you have already completed them.
1. [Install the Google Cloud SDK](https://cloud.google.com/sdk/downloads) for necessary commands such as `gcloud` and `gsutil`.
1. [Create a Pantheon account](https://console.cloud.google.com/) for use of the Cloud Platform Console.
1. In Pantheon, navigate to the upper header bar and create a new project for use as your App Engine project. Your project has a unique ID that is part of your web application url. If necessary, [create a billing project](https://support.google.com/cloud/answer/6288653?hl=en).
1. In the command line, [set the default project](https://cloud.google.com/sdk/docs/managing-configurations) to your newly created project by running the following command:

    ```sh
    gcloud config set project [PROJECT ID]
    ```
    
1. In Pantheon, click on the three-bar icon in the upper left hand corner to open the `Products & services` menu. Click on `Storage`. In the browser, create a bucket with `Multi-Regional` or `Regional` storage. This bucket is for storing the photos of your shared photo album.
1. If you want collaborators on your photo album, click on the three-dots icon for your photo bucket on the right side of the screen. Click `Edit bucket permissions` and add the email addresses of the collaborators as `Storage Admins`.
1. Change the photos bucket permissions to make it publicly readable so that the photos may be viewed on your website. in the command line, run:

    ```sh
    gsutil defacl ch -g allUsers:R gs://[PHOTO BUCKET NAME]
    ```
    
1. Create another bucket with `Multi-Regional` or `Regional` storage. This bucket is for storing the thumbnails of the photos in your shared photo album.
1. Open the `Products & services` menu and click on `Pub/Sub`. Create a new topic with the same name as your photos bucket.
1. Click on the three-dots icon for your photo album topic and click on `New subscription`. Change the `Delivery Type` to `Push into an endpoint url`. This is the url that receives your Cloud Pub/Sub messages. Your url should be something of the format `http://[PROJECT ID].appspot.com/_ah/push-handlers/receive_message`.
1. Configure Cloud Pub/Sub notifications for your photos bucket by using the command line to run

    ```sh
    gsutil notification create -f json gs://[PHOTO BUCKET NAME]
    ```

## Basic Application Layout

If you do not feel like coding the entire application from scratch, feel free to clone the git repository with a default application by running

  ```sh
  git clone https://github.com/GChien44/tutorial-v2.git
  ```

Note that if you choose this option, some parts of the code still need to be changed to suit your GCS bucket names.

From this point forward, it is assumed that you did not clone the above git repository, and are building the application from scratch.

### Libraries and `app.yaml`

The external library and `app.yaml` files are necessary for the configuring your App Engine application and importing the required libraries.

1. Choose a directory to house your project. From this point forward, this will be referred to as the host directory. Inside your host directory, create a new directory called `lib` for the storage of external libraries.
1. Copy the `cloudstorage` library into your `lib` directory from the [Google Cloud Storage client library](https://github.com/GoogleCloudPlatform/appengine-gcs-client) using the command
    
    ```sh
    svn export https://github.com/GoogleCloudPlatform/appengine-gcs-client/trunk/python/src/cloudstorage
    ```
      
1. Create a blank `__init__.py` file in the lib directory to mark `cloudstorage` as importable.
1. In your host directory, run the following command to install the Google Cloud Vision API Client library:
        
    ```sh
    pip install --upgrade -t lib google-api-python-client
    ```
        
1. In your host directory, create the file `appengine_config.py` and copy in the following code:
    
    ```py
    from google.appengine.ext import vendor
    vendor.add('lib')
    ```
     
1. In your host directory, create an `app.yaml` file and copy in the following code:

    ```yaml
    runtime: python27
    api_version: 1
    threadsafe: yes

    handlers:
    - url: /_ah/push-handlers/.*
      script: main.app
      login: admin
      
    - url: .*
      script: main.app

    libraries:
    - name: webapp2
      version: latest
    - name: jinja2
      version: latest
    ```
    
### HTML Files
  
The HTML files represent the different pages of your web application.
  
1. In your host directory, create a `templates` directory to hold all of your HTML files. Each HTML file should have the same basic layout, with a title and links to the other pages of your application:
    
    ```html
    <!DOCTYPE html>
    <html>
    
      <head>
        <title>Page Title</title>
      </head>

      <body>

        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/photos">Photos</a></li>
          <li><a href="/search">Search</a></li>
        </ul>

        <h1>Page Title</h1>

      </body>
    </html>
    ```
    
1. Create an HTML file for the home/notifications page of your application (url: `http://[PROJECT ID].appspot.com`) using the template given above. The notifications page will have a news feed listing all recent actions performed on your GCS photo bucket.
1. Create an HTML file for the photos page of your application (url: `http://[PROJECT ID].appspot.com/photos`) using the template given above. The photos page will display the thumbnails and names of all photos uploaded to your GCS photo bucket.
1. Create an HTML file for the search page of your application (url: `http://[PROJECT ID].appspot.com/search`) using the template given above. The search page will display the thumbnails and names of the photos uploaded to your GCS photo bucket that match the entered search term.
    
### The `main.py` File

The `main.py` file contains the backend logic of the website, including the reception of Cloud Pub/Sub messages, the communication with GCS and Datastore, and the rendering of HTML templates.

1. Create a `main.py` file in your host directory.
1. Add the required imports to the top of the file:
        
    ```py
    import webapp2
    import jinja2
    import os
    import logging
    import json
    import urllib
    import collections
    import cloudstorage as gcs
    import googleapiclient.discovery
    from google.appengine.ext import ndb
    from google.appengine.ext import blobstore
    from google.appengine.api import images
    ```
        
1. Set up [jinja2](http://jinja.pocoo.org/docs/2.9/templates/) for HTML templating.
    
    ```py
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))
    ```
        
1. Add constants. `THUMBNAIL_BUCKET` is the name of the GCS bucket you created in Set Up step #8 to store the thumbnails of photos uploaded to your GCS photo bucket. `PHOTO_BUCKET` is the name of the GCS bucket you created in Set Up step #5 to store the photos uploaded to your shared photo album. `NUM_NOTIFICATIONS_TO_DISPLAY` regulates the maximum number of notifications displayed on the home/notifications page of your web application. `MAX_LABELS` regulates the maximum number of labels obtained for each photo using Cloud Vision.
    
    ```py
    THUMBNAIL_BUCKET = '[GCS THUMBNAIL BUCKET NAME]'
    PHOTO_BUCKET = '[GCS PHOTO BUCKET NAME]'
    NUM_NOTIFICATIONS_TO_DISPLAY = [SOME NUMBER]
    MAX_LABELS = [SOME NUMBER]
    ```
    
1. Create the `Notification` class. Notifications are created from Cloud Pub/Sub messages and stored in Cloud Datastore, to be displayed on the home page of your application. Notifications have a message, date of posting, and generation number, which is used to distinguish between similar notifications and prevent the display of repeated notifications. Information on NDB properties can be found [here](https://cloud.google.com/appengine/docs/standard/python/ndb/).
    
    ```py
    class Notification(ndb.Model):
        message = ndb.StringProperty()
        date = ndb.DateTimeProperty(auto_now_add=True)
        generation = ndb.StringProperty()
    ```
        
1. Create the `ThumbnailReference` class. ThumbnailReferences are stored in Cloud Datastore and contain information about the thumbnails stored in your GCS thumbnail bucket. ThumbnailReferences have a thumbnail_name (the name of the uploaded photo), a thumbnail_key (a concatenation of the name and generation number of an uploaded photo, used to distinguish similarly named photos), date of posting, a list of label descriptions assigned to the corresponding photo using Google Cloud Vision, and the url of the original photo that is stored in GCS.
    
    ```py
    class ThumbnailReference(ndb.Model):
        thumbnail_name = ndb.StringProperty()
        thumbnail_key = ndb.StringProperty()
        labels = ndb.StringProperty(repeated=True)
        original_photo = ndb.StringProperty()
    ```
        
1. Create the `Label` class. Labels are stored in Cloud Datastore and describe the labels assigned to an uploaded photo by the Google Cloud Vision API. Labels have a label_name (description of the label) and labeled_thumbnails (a list of the thumbnail_keys of photos labeled by Google Cloud Vision with label_name).
    
    ```py
    class Label(ndb.Model):
        label_name = ndb.StringProperty()
        labeled_thumbnails = ndb.StringProperty(repeated=True)
    ```
        
1. Create a `MainHandler` with a `get` method for getting information from the server and writing it to the home/notification page HTML file. There are no values to pass into the template yet.
    
    ```py
    class MainHandler(webapp2.RequestHandler):
      def get(self):
        template_values = {}
        template = jinja_environment.get_template("[NAME OF YOUR HOME PAGE HTML FILE]")
        self.response.write(template.render(template_values))
    ```
        
1. Create a `PhotosHandler` class with a `get` method for getting information from the server and writing it to the photos page HTML file. This should look similar to the `MainHandler`.
1. Create a `SearchHandler` class with a `get` method for getting information from the server and writing it to the search page HTML file. This should look similar to the `MainHandler` and `PhotosHandler`.
1. Create a `ReceiveMessage` class with a `post` method for posting information to ther server. This `post` method will receive Cloud Pub/Sub messages and perform necessary logic using the information. Further detail is in the next section.
    
    ```py
    class ReceiveMessage(webapp2.RequestHandler):
        def post(self):
            # This method will be filled out in the next section.
    ```
        
1. Add the following code at the end of your `main.py` file to connect the web page urls with their corresponding classes.
    
    ```py
    app = webapp2.WSGIApplication([
        ('/', MainHandler),
        ('/photos', PhotosHandler),
        ('/search', SearchHandler),
        ('/_ah/push-handlers/receive_message', ReceiveMessage)
    ], debug=True)
    ```
        
### Checkpoint

1. [Run your application locally](https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server) by running the following command from your host directory:

    ```sh
    dev_appserver.py .
    ```
    
    Visit `localhost:8080` in your web browser to view your web application. You should be able to click on the links to  navigate between the pages of your website, which should all be blank except for the navigation links and page titles.

1. [Deploy your application](https://cloud.google.com/appengine/docs/standard/python/getting-started/deploying-the-application) by running

    ```sh
    gcloud app deploy
    ```
    
    Your web application should be viewable at `http://[PROJECT ID].appspot.com`. You can either navigate there directly through your web browser or launch your browser and view the app by running the command

    ```sh
    gcloud app browse
    ```
    
## Creating the Notifications Page

### Receiving Cloud Pub/Sub Messages

During the Set Up phase, you configured [Cloud Pub/Sub push messages](https://cloud.google.com/pubsub/docs/push#receive_push) to be sent to the url you specified for the `ReceiveMessage` class in your `main.py` file. When you receive a Pub/Sub message, you must get necessary information from it and acknowledge its reception.

1. In the your `main.py` file, in the `ReceiveMessage` class, in your `post` method, obtain the [notification attributes](https://cloud.google.com/storage/docs/pubsub-notifications) from the incoming Cloud Pub/Sub message. A logging statement can be used for easier debugging.

    ```py
    # Logging statement is optional.
    logging.debug('Post body: {}'.format(self.request.body))
    message = json.loads(urllib.unquote(self.request.body).rstrip('='))
    attributes = message['message']['attributes']
    ```
    
    `attributes` is a key:value dictionary where the keys are the Pub/Sub attribute names and the values are the attribute values.
    
1. Acknowledge the reception of the Cloud Pub/Sub message.

    ```py
    self.response.status = 204
    ```
    
1. Save the relevant values from the `attributes` dictionary for later use.

    ```py
    event_type = attributes.get('eventType')
    photo_name = attributes.get('objectId')
    generation_number = str(attributes.get('objectGeneration'))
    overwrote_generation = attributes.get('overwroteGeneration')
    overwritten_by_generation = attributes.get('overwrittenByGeneration')
    ```
    
1. Create the thumbnail_key using the `photo_name` and `generation_number`. Note that using the following logic, only photos with the extensions `.jpg` can be uploaded effectively.

    ```py
    index = photo_name.index(".jpg")
    thumbnail_key = photo_name[:index] + generation_number + photo_name[index:]
    ```
    
You now have all of the information needed to create the necessary notification and communicate with GCS.

### Creating and Storing Notifications

1. Write a `create_notification` helper function to generate notifications. Note that if the `event_type` is `OBJECT_UPDATE`, the `message` field is blank.

    ```py
    def create_notification(photo_name, event_type, generation, overwrote_generation=None, overwritten_by_generation=None):
      if event_type == 'OBJECT_FINALIZE':
        if overwrote_generation is not None:
          message = photo_name + ' was uploaded and overwrote an older version of itself.'
        else:
          message = photo_name + ' was uploaded.'
      elif event_type == 'OBJECT_ARCHIVE':
        if overwritten_by_generation is not None:
          message = photo_name + ' was overwritten by a newer version.'
        else:
          message = photo_name + ' was archived.'
      elif event_type == 'OBJECT_DELETE':
        if overwritten_by_generation is not None:
          message = photo_name + ' was overwritten by a newer version.'
        else:
          message = photo_name + ' was deleted.'
      else:
        message = ''

    return Notification(message=message, generation=generation)
    ```
    
1. Call the `create_notification` helper function in the `ReceiveMessage` class.

    ```py
    new_notification = create_notification(photo_name, event_type, generation_number,   
        overwrote_generation=overwrote_generation, overwritten_by_generation=overwritten_by_generation)
    ```
    
1. Check if the new notification has already been stored. Cloud Pub/Sub messaging guarantees at-least-once delivery, meaning a Pub/Sub notification may be received more than once. If the notification already exists, there has been no new change to the GCS photo bucket, and the Pub/Sub notification can be ignored.

    ```py
    exists_notification = Notification.query(Notification.message==new_notification.message,        
        Notification.generation==new_notification.generation).get()
    if exists_notification:
      return
    ```
    
1. Do not act for `OBJECT_UPDATE` events, as they signal no change to the GCS photo bucket images themselves.

    ```py
    if new_notification.message == '':
      return
    ```
    
1. Store the new notification in Cloud Datastore. This, and all further code in the `ReceiveMessage` class, is only executed if the new notification is not a repeat and is not for an `OBJECT_UPDATE` event.

    ```py
    new_notification.put()
    ```
    
### Writing Notifications to the HTML File

1. In `main.py`, in the `MainHandler`, in the `get` method, fetch all Notifications from Cloud Datastore in reverse date order and include them in `template_values`, to be written to the home/notifications page HTML file.

    ```py
    notifications = Notification.query().order(-Notification.date).fetch(NUM_NOTIFICATIONS_TO_DISPLAY)
    template_values = {'notifications':notifications}
    ```
    
1. In the home/notifications page HTML file, loop through the `notifications` list you rendered to the template in `main.py` and print the formatted date/time of the notification and the notification message.

    ```html
    {% for notification in notifications %}
    <div>
      <p><small>{{notification.date.strftime('%B %d %Y %I:%M')}} UTC: </small>{{notification.message}}</p>
    </div>
    {% endfor %}
    ```
    
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. In the [Cloud Platform Console](https://console.cloud.google.com/), use the three-bar icon in the top left corner to open the `Products & services` menu and navigate to `Storage`.
1. Click on the name of your GCS photo bucket. Click `UPLOAD FILES` and upload an image with the extension `.jpg`.
1. Open the `Products & services` menu again and navigate to `Datastore`. There should be a Notification listed with the message `[UPLOADED PHOTO NAME] was uploaded.`.
1. View your deployed application in your web browser. There should be a notification listed on the home page. You may need to refresh the page.

If you encounter errors, open the `Products & services` menu and navigate to `Logging`. Use the messages there to debug your application.

## Implementing Photo Upload Functionality

When a Cloud Pub/Sub notification is received, different actions occur depending on the `eventType`. If the notification indicates an `OBJECT_FINALIZE` event, the uploaded photo must be shrunk to a thumbnail, the thumbnail of the photo must be stored in the GCS thumbnail bucket, the photo must be labeled using the Google Cloud Vision API, a `ThumbnailReference` must be stored in Datastore, and the required `Label` entities must be updated or created to be stored in Datastore.

Because these actions only occur in the case of a photo upload, an `if` block should be used inside the `ReceiveMessage` class of `main.py`.

```py
if event_type == 'OBJECT_FINALIZE':
  # Photo upload-specific code here.
```
    
### Creating the Thumbnail

To create the thumbnail, the original image from the GCS photo bucket should be resized. Use the [Images Python API](https://cloud.google.com/appengine/docs/standard/python/images/) to perform the required transformations.

1. Write the `create_thumbnail` helper function.

    ```py
    def create_thumbnail(self, photo_name):
      filename = '/gs/' + PHOTO_BUCKET + '/' + photo_name
      image = images.Image(filename=filename)
      image.resize(width=180, height=200)
      return image.execute_transforms(output_encoding=images.JPEG)
    ```
    
    This returns the thumbnail in a `string` format.
    
1. Call the `create_thumbnail` helper function in `ReceiveMessage`.

    ```py
    thumbnail = create_thumbnail(self, photo_name)
    ```
    
### Storing the Thumbnail in GCS

The thumbnail should be stored in the GCS thumbnail bucket under the name `thumbnail_key` in order to distinguish between different versions of the same photo. Since two Cloud Pub/Sub notifications, an `OBJECT_FINALIZE` and an `OBJECT_DELETE`/`OBJECT_ARCHIVE`, are sent in an arbitrary order in the case of an overwrite, it is possible for two thumbnails with the same `thumbnail_name` to exist in storage at once. Utilizing the `generation_number` of the photo in the `thumbnail_key` ensures that the correct thumbnail is deleted when necessary.

1. Write the `store_thumbnail_in_gcs` helper function.

    ```py
    def store_thumbnail_in_gcs(self, thumbnail_key, thumbnail):
      write_retry_params = gcs.RetryParams(backoff_factor=1.1)
      filename = '/' + THUMBNAIL_BUCKET + '/' + thumbnail_key
      with gcs.open(filename, 'w') as filehandle:
        filehandle.write(thumbnail)
    ```
    
1. Call the `store_thumbnail_in_gcs` helper function in `ReceiveMessage`.

    ```py
    store_thumbnail_in_gcs(self, thumbnail_key, thumbnail)
    ```
    
### Labeling the Photo Using Google Cloud Vision

