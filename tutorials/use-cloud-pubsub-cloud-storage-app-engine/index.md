---
title: How to Use Cloud Pub/Sub Notifications and Cloud Storage with App Engine
description: Create a shared photo album using Cloud Pub/Sub, Cloud Storage, Datastore, and App Engine.
author: ggchien, cmwoods
tags: App Engine, Cloud Pub/Sub, Cloud Storage, GCS, Datastore, photo album
date published:
---

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

This tutorial teaches you how to integrate several Google products to simulate a shared photo album, hosted on App Engine and managed through the Cloud Platform Console.

Users interact with the web application only through the Cloud Platform Console; photos cannot be uploaded or deleted through the application itself. Two buckets exist in [Cloud Storage](https://cloud.google.com/storage/) (GCS): one to store the uploaded photos themselves, and the other to store the thumbnails of the uploaded photos. [Cloud Datastore](https://cloud.google.com/datastore/) stores all non-image entities needed for the web application, which is hosted on [App Engine](https://cloud.google.com/appengine/). Notifications of changes to the GCS photo bucket are sent to the application via [Cloud Pub/Sub](https://cloud.google.com/pubsub/). The [Google Cloud Vision API Client Library](https://developers.google.com/api-client-library/python/apis/vision/v1) is used to label photos for search.

The overall workflow of the application is shown in the diagram below:

![Shared Photo App Workflow](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/tutorial-workflow.png)

Receiving a Notification (purple arrows):
1. A user uploads or deletes something from their GCS bucket.
1. A Cloud Pub/Sub message is sent.
1. The Cloud Pub/Sub message is received by App Engine.
1. The Cloud Pub/Sub message is formatted and stored as a `Notification` in Datastore.
1. If the event type from the message is `OBJECT_FINALIZE`, the uploaded photo is compressed and stored as a thumbnail in a separate GCS thumbnail bucket. If the event type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, the thumbnail matching the name and generation number of the deleted or archived photo is deleted from the GCS thumbnail bucket.
1. If the event type from the message is `OBJECT_FINALIZE`, then the Google Cloud Vision API is used to generate labels for the uploaded photo.
1. If the event type from the message is `OBJECT_FINALIZE`, then a new `ThumbnailReference` is created and stored in Datastore. If the event type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, then the appropriate `ThumbnailReference` is removed from all `Labels` that contain it.
1. If the event type from the message is `OBJECT_FINALIZE`, then the `ThumbnailReference` is added to all applicable `Labels`. New Labels are created and added to Datastore as needed. If the event type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, then the appropriate `ThumbnailReference` is deleted from Datastore.

Loading the Home Page (green arrows)\*:
1. A previously-specified number of `Notifications` are queried from Datastore, ordered by date and time, most recent first.
1. The queried `Notifications` are sent to the front-end to be formatted and displayed on the home page.

Loading the Photos Page (red arrows)\*:
1. All the `ThumbnailReferences` are fetched from Datastore, ordered by date and time, most recent first.
1. Each `ThumbnailReference` is used to get a serving url for the corresponding thumbnail stored in GCS.
1. A dictionary of `ThumbnailReferences` and their serving urls is sent to the front-end to be formatted and displayed on the photos page.

Loading the Search Page (pink arrows)\*:
1. A Datastore query attempts to find a `Label` that matches the search term entered in the search box.
1. If a matching `Label` is found, Datastore is queried for each `ThumbnailReference` that `Label` contains.
1. Each `ThumbnailReference` queried is used to get a serving url for the corresponding thumbnail stored in GCS.
1. A dictionary of `ThumbnailReferences` and their serving urls is sent to the front-end to be formatted and displayed on the search page.

\* Step 0: The user navigates to the url that causes the page to load.

Note: Basic coding (Python, HTML, CSS, Javascript) and command line knowledge is necessary to complete this tutorial.

## Set up

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

## Basic application layout

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
    
### HTML files
  
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
    
### The `main.py` file

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
        date = ndb.DateTimeProperty(auto_now_add=True)
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
    
## Creating the notifications page

### Receiving Cloud Pub/Sub messages

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

### Creating and storing `Notifications`

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
    
1. Call the `create_notification` helper function in the `post` method of the `ReceiveMessage` class.

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
    
### Writing `Notifications` to the HTML file

1. In `main.py`, in the `MainHandler`, in the `get` method, fetch all `Notifications` from Cloud Datastore in reverse date order and include them in `template_values`, to be written to the home/notifications page HTML file.

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
1. Open the `Products & services` menu again and navigate to `Datastore`. There should be a `Notification` listed with the message `[UPLOADED PHOTO NAME] was uploaded.`.
1. View your deployed application in your web browser. The new notification should be listed on the home page. You may need to refresh the page.

If you encounter errors, open the `Products & services` menu and navigate to `Logging`. Use the messages there to debug your application.

## Implementing photo upload functionality

When a Cloud Pub/Sub notification is received, different actions occur depending on the `eventType`. If the notification indicates an `OBJECT_FINALIZE` event, the uploaded photo must be shrunk to a thumbnail, the thumbnail of the photo must be stored in the GCS thumbnail bucket, the photo must be labeled using the Google Cloud Vision API, a `ThumbnailReference` must be stored in Datastore, and the required `Label` entities must be updated or created to be stored in Datastore.

Because these actions only occur in the case of a photo upload, an `if` block should be used inside the `ReceiveMessage` class of `main.py`.

```py
if event_type == 'OBJECT_FINALIZE':
  # Photo upload-specific code here.
```
    
### Creating the thumbnail

To create the thumbnail, the original image from the GCS photo bucket should be resized. Use the [Images Python API](https://cloud.google.com/appengine/docs/standard/python/images/) to perform the required transformations.

1. Write the `create_thumbnail` helper function.

    ```py
    def create_thumbnail(photo_name):
      filename = '/gs/' + PHOTO_BUCKET + '/' + photo_name
      image = images.Image(filename=filename)
      image.resize(width=180, height=200)
      return image.execute_transforms(output_encoding=images.JPEG)
    ```
    
    This returns the thumbnail in a `string` format.
    
1. Call the `create_thumbnail` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    thumbnail = create_thumbnail(photo_name)
    ```
    
### Storing the thumbnail in GCS

The thumbnail should be stored in the GCS thumbnail bucket under the name `thumbnail_key` in order to distinguish between different versions of the same photo. Since two Cloud Pub/Sub notifications, an `OBJECT_FINALIZE` and an `OBJECT_DELETE`/`OBJECT_ARCHIVE`, are sent in an arbitrary order in the case of an overwrite, it is possible for two thumbnails with the same `thumbnail_name` to exist in storage at once. Utilizing the `generation_number` of the photo in the `thumbnail_key` ensures that the correct thumbnail is deleted when necessary.

1. Write the `store_thumbnail_in_gcs` helper function.

    ```py
    def store_thumbnail_in_gcs(thumbnail_key, thumbnail):
      write_retry_params = gcs.RetryParams(backoff_factor=1.1)
      filename = '/' + THUMBNAIL_BUCKET + '/' + thumbnail_key
      with gcs.open(filename, 'w') as filehandle:
        filehandle.write(thumbnail)
    ```
    
1. Call the `store_thumbnail_in_gcs` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    store_thumbnail_in_gcs(thumbnail_key, thumbnail)
    ```
    
### Labeling the photo using Google Cloud Vision

The [Google Cloud Vision API Client Library for Python](https://developers.google.com/api-client-library/python/apis/vision/v1) can be used to [annotate](https://developers.google.com/resources/api-libraries/documentation/vision/v1/python/latest/vision_v1.images.html) images, assigning them labels that describe the contents of the picture. You will later use these labels to search for specific photos.

The design of this shared photo album web application uses cross referencing to allow for faster search for and deletion of thumbnails. Since every `Label` has the property `labeled_thumbnails`, a list of `thumbnail_keys` representing photos labeled with the applicable `label_name`, it is relatively simple to obtain the thumbnails that should be displayed for a given search term. Similarly, since every `ThumbnailReference` has the property `labels`, a list of `label_names` representing the labels given by Cloud Vision to the corresponding photo, `thumbnail_keys` can be deleted from the appropriate `labels` lists efficiently in the case of an `OBJECT_DELETE` or `OBJECT_ARCHIVE`.

Therefore, in the case of a photo upload, `label_names` must be added to the `ThumbnailReference`, and `thumbnail_keys` must be added to the appropriate `Labels`.

1. Obtain the `labels` list for a given photo.
    1. Create the `uri` to reference the appropriate photo in the GCS photo bucket.
        
        ```py
        uri = 'gs://' + PHOTO_BUCKET + '/' + photo_name
        ```
        
    1. Write the `get_labels` helper function.
    
        ```py
        def get_labels(uri, photo_name):
          service = googleapiclient.discovery.build('vision', 'v1')
          labels = []

          # Label photo with its own name, sans extension.
          # This allows you to search a photo by its name.
          index = photo_name.index(".jpg")
          photo_name_label = photo_name[:index]
          labels.append(photo_name_label)

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

          ignore = ['of', 'like', 'the', 'and', 'a', 'an', 'with']

          # Add labels to the labels list if they are not already in the list and are
          # not in the ignore list.
          if labels_full is not None:
            for label in labels_full:
              if label['description'] not in labels:
                labels.append(label['description'])
                # Split the label into individual words, also to be added to labels list
                # if not already.
                descriptors = label['description'].split()
                  for descript in descriptors:
                    if descript not in labels and descript not in ignore:
                      labels.append(descript)

           return labels
        ```
        
    1. Call the `get_labels` helper function in the `post` method of the `ReceiveMessage` class.
    
        ```py
        labels = get_labels(uri, photo_name)
        ```
        
1. Add the `thumbnail_key` of the photo to the `labeled_thumbnails` lists of the required `Labels`.
    1. Write the `add_thumbnail_reference_to_labels` helper function.
    
        ```py
        def add_thumbnail_reference_to_labels(labels, thumbnail_key):
          for label in labels:
            label_to_append_to = Label.query(Label.label_name==label).get()
            if label_to_append_to is None:
              # Create and store new Label if does not already exist.
              thumbnail_list_for_new_label = []
              thumbnail_list_for_new_label.append(thumbnail_key)
              new_label = Label(label_name=label, labeled_thumbnails=thumbnail_list_for_new_label)
              new_label.put()
            else:
              # Add thumbnail to Label list if Label already exists.
              label_to_append_to.labeled_thumbnails.append(thumbnail_key)
              label_to_append_to.put()
        ```
        
    1. Call the `add_thumbnail_reference_to_labels` helper function in the `post` method of the `ReceiveMessage` class.
    
        ```py
        add_thumbnail_reference_to_labels(labels, thumbnail_key)
        ```
        
Although the `thumbnail_keys` have now been added to the appropriate `Labels`, it is still necessary to add the `label_names` to the `ThumbnailReference`. This is further elaborated in the next section.

### Creating and storing the `ThumbnailReference`

At this point, the only other thing you need to create the required `ThumbnailReference` is the url of the original photo. Obtain this, and the `ThumbnailReference` can be created and stored.

1. Write the `get_original` helper function to return the url of the original photo.

    ```py
    def get_original(photo_name, generation):
      return 'https://storage.googleapis.com/' + PHOTO_BUCKET + '/' + photo_name + '?generation=' + generation
    ```
    
1. Call the `get_original` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    original_photo = get_original(photo_name, generation_number)
    ```
    
1. Create the `ThumbnailReference` using the information gathered from the Cloud Pub/Sub message, `get_labels` function, and `get_original` function.

    ```py
    thumbnail_reference = ThumbnailReference(thumbnail_name=photo_name, thumbnail_key=thumbnail_key, labels=labels, 
        original_photo=original_photo)
    ```
    
1. Store the newly created `ThumbnailReference` in Datastore.

    ```py
    thumbnail_reference.put()
    ```
    
You have now completed all of the code necessary to store the information about an uploaded photo in GCS and Datastore.

### Writing thumbnails to the photos HTML file

1. Write the `get_thumbnail` helper function. This function returns a [serving url](https://cloud.google.com/appengine/docs/standard/python/images/#get-serving-url) that accesses the thumbnail from the GCS thumbnail bucket.

    ```py
    def get_thumbnail(photo_name):
      filename = '/gs/' + THUMBNAIL_BUCKET + '/' + photo_name
      blob_key = blobstore.create_gs_key(filename)
      return images.get_serving_url(blob_key)
    ```

1. In `main.py`, in the `PhotosHandler`, in the `get` method, fetch all `ThumbnailReferences` from Cloud Datastore in reverse date order. Create an ordered dictionary, calling upon the `get_thumbnail` helper function, with the thumbnail serving urls as keys and the `thumbnail_references` as values. Include the dictionary in `template_values`, to be written to the appropriate HTML file.

    ```py
    thumbnail_references = ThumbnailReference.query().order(-ThumbnailReference.date).fetch()
    thumbnails = collections.OrderedDict()
    for thumbnail_reference in thumbnail_references:
      img_url = get_thumbnail(thumbnail_reference.thumbnail_key)
      thumbnails[img_url] = thumbnail_reference
    template_values = {'thumbnails':thumbnails}
    ```
    
1. In the `templates` directory, in the photos page HTML file, loop through the thumbnails dictionary you rendered to the template in `main.py` and display the thumbnail image and its name.

    ```html
    {% for img_url, thumbnail_reference in thumbnails.iteritems() %}
      <div>
        <img src='{{img_url}}'>
        <div>{{thumbnail_reference.thumbnail_name}}</div>
      </div>
    {% endfor %}
    ```
    
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. Upload an image with the extension `.jpg` to your GCS photo bucket.
1. Check that the thumbnail version of your newly uploaded photo is in your GCS thumbnail bucket under the correct name.
1. Check that in Datastore, there is a `Notification` listed with the message `[UPLOADED PHOTO NAME] was uploaded.`.
1. Check that in Datastore, there is a `ThumbnailReference` listed with the appropriate information.
1. Check that in Datastore, there are `Labels` corresponding with the ones listed in the new `ThumbnailReference` entity.
1. View your deployed application in your web browser.
    1. Check that the new notification is listed on the home page. You may need to refresh the page.
    1. Check that the thumbnail and name of the uploaded photo are displayed on the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Implementing photo delete/archive functionality

Alternatively, if the received Cloud Pub/Sub notification indicates an `OBJECT_DELETE` or `OBJECT_ARCHIVE` event, the corresponding `thumbnail_key` must be removed from all necessary `Labels`, the thumbnail must be deleted from the GCS thumbnail bucket, and the `ThumbnailReference` must be deleted from Datastore.

Because these actions only occur in the case of a photo delete or archive, an `elif` statement can be used inside the `ReceiveMessage` class of `main.py`, where the initial `if` statement of the block is the one specifying the event type as `OBJECT_FINALIZE`.

```py
elif event_type == 'OBJECT_DELETE' or event_type == 'OBJECT_ARCHIVE':
    # Photo delete/archive-specific code here.
```
    
### Removing the thumbnail from `Labels`

1. Write the `remove_thumbnail_from_labels` helper function to remove the given `thumbnail_key` from all applicable `Labels`.

    ```py
    def remove_thumbnail_from_labels(thumbnail_key):
      thumbnail_reference = ThumbnailReference.query(ThumbnailReference.thumbnail_key==thumbnail_key).get()
      labels_to_delete_from = thumbnail_reference.labels
      for label_name in labels_to_delete_from:
        label = Label.query(Label.label_name==label_name).get()
        labeled_thumbnails = label.labeled_thumbnails
        labeled_thumbnails.remove(thumbnail_key)
        # If there are no more thumbnails with a given Label, delete the Label.
        if not labeled_thumbnails:
          label.key.delete()
        else:
          label.put()
    ```

1. Call the `remove_thumbnail_from_labels` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    remove_thumbnail_from_labels(thumbnail_key)
    ```
    
### Deleting the thumbnail and `ThumbnailReference`

1. Write the `delete_thumbnail` helper function to delete the specified thumbnail from the GCS thumbnail bucket and delete the `ThumbnailReference` from Datastore.

    ```py
    def delete_thumbnail(thumbnail_key):
      # Delete the serving url of the thumbnail.
      filename = '/gs/' + THUMBNAIL_BUCKET + '/' + thumbnail_key
      blob_key = blobstore.create_gs_key(filename)
      images.delete_serving_url(blob_key)
      # Delete the ThumbnailReference from Datastore.
      thumbnail_reference = ThumbnailReference.query(ThumbnailReference.thumbnail_key==thumbnail_key).get()
      thumbnail_reference.key.delete()
      # Delete the thumbnail from the GCS thumbnail bucket.
      filename = '/' + THUMBNAIL_BUCKET + '/' + thumbnail_key
      gcs.delete(filename)
    ```
    
1. Call the `delete_thumbnail` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    delete_thumbnail(thumbnail_key)
    ```
    
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. Delete an image from your GCS photo bucket.
1. Check that the thumbnail version of your deleted photo is no longer in your GCS thumbnail bucket.
1. Check that in Datastore, there is a `Notification` listed with the message `[DELETED PHOTO NAME] was deleted.`.
1. Check that in Datastore, the `ThumbnailReference` for your deleted photo is no longer listed.
1. Check that in Datastore, none of the `Labels` contain the name of your recently deleted photo, and none of the `Labels` are blank.
1. View your deployed application in your web browser.
    1. Check that the new notification is listed on the home page. You may need to refresh the page.
    1. Check that the thumbnail and name of the uploaded photo are no longer displayed on the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Creating the search page

The search page of the web application has a search bar users can enter a `search-term` into. The `Label` with the `label_name` corresponding to the `search-term` is queried from Datastore, and the `labeled_thumbnails` list is used to obtain and display the appropriate thumbnails on the search page.

1. In `main.py`, in the `SearchHandler` class, fill out the `get` method.
    1. Get the `search-term` from the user and use it to query the appropriate `Label`.
    
        ```py
        search_term = self.request.get('search-term').lower()
        label = Label.query(Label.label_name==search_term).get()
        ```
        
    1. In a similar manner as in the `PhotosHandler`, build an ordered dictionary of thumbnail serving urls as keys and `ThumbnailReferences` as values. However, unlike in the `PhotosHandler`, you should only add to the dictionary the thumbnails under the appropriate `Label`.
    
        ```py
        thumbnails = collections.OrderedDict()
        if label is not None:
          thumbnail_keys = label.labeled_thumbnails
          for thumbnail_key in thumbnail_keys:
            img_url = get_thumbnail(thumbnail_key)
            thumbnails[img_url] = ThumbnailReference.query(ThumbnailReference.thumbnail_key==thumbnail_key).get()
        ```
        
    1. Reverse the order of the thumbnails dictionary and include it in `template_values`, to be written to the search page HTML file. The dictionary order needs to be reversed because `thumbnail_keys` were added to the `Label` in order from oldest to newest, but should be displayed on the search page starting with the most recent first.
    
        ```py
        thumbnails = collections.OrderedDict(reversed(list(thumbnails.items())))
        template_values = {'thumbnails':thumbnails}
        ```
        
1. Fill out the search page HTML file.
    1. Set up the search bar.
    
        ```html
        <form action="/search" method="get">
          <input name="search-term" placeholder="Search">
          <button>Search</button>
        </form>
        ```
        
    1. Like in the photos page HTML file, loop through the thumbnails dictionary you rendered to the template in `main.py` and display the thumbnail image and its name. Include an `else` statement as part of your loop to specify behavior in the case the thumbnails dictionary is empty (no search results returned).
        
        ```html
        {% for img_url, thumbnail_reference in thumbnails.iteritems() %}
          <div>
            <img src='{{img_url}}'>
            <div>{{thumbnail_reference.thumbnail_name}}</div>
          </div>
        {% else %}
          <h2>No Search Results</h2>
        {% endfor %}
        ```
    
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. View your deployed application in your web browser. Try using the search bar. When you search, the applicable photos should appear in a similar manner as the photos page, else the text `No Search Results` should be displayed.

Note: Examining the `Labels` and `ThumbnailReferences` in Datastore helps you determine whether or not the search is functioning as it is meant to.

If you encounter errors, use the `Logging` messages to debug your application.

#### Congratulations! You now have a functioning shared photo album.

## Style

Now that you a functioning website, it's time to add formatting to it. We'll do this by adding CSS and JavaScript to your already existing HTML files. 

### Set-Up

Before you start incorporating CSS, you have to tell your app to expect a CSS file and where to find it.

1. Create a directory inside your host directory to hold your external style sheet.
1. Open your `app.yaml` file and include the following, replacing [DIRECTORY NAME] with whatever you named your directory in step 1.

    ```yaml
    - url: /[DIRECTORY NAME]
      static_dir: [DIRECTORY NAME]
          
    - url: /static
      static_dir: static
    ```
   Note that this code should go in the `handlers` section of your `app.yaml` file and must be above
   
    ```yaml
    - url: .*
      script: main.app
    ```
        
1. Inside the directory you created, create a CSS file. Leave it blank for now; we'll add code to it in the next section. Note that your file must have the extension `.css`.
1. In each HTML file (you should have three) add the following code inside the `<head>` section, replacing [DIRECTORY NAME] and [FILE NAME] with the appropriate directory and file.

    ```html
    <link rel="stylesheet" type="text/css" href="/[DIRECTORY NAME]/[FILE NAME]">
    ```

### Add style common to every page

First, we'll style the HTML components present on every page of the website. This includes the body, the links to other pages, and the title of the page. You should run your app locally after each step to see the changes.

1. Add the following code to your `CSS` file to set the background color. Replace [COLOR] with a color of your choice. 

    ```css
    body{
      background-color: [COLOR];
    }
    ```

   You can specify the color by typing in the name of it, such as `blue`, by specifying the rgb configuration, or by giving    a hexadecimal representation. You can find more information on how colors work in CSS [here]
   (https://www.w3schools.com/css/css_colors.asp). 
1. Next you'll create a box to hold the links to other pages. Add the following code your `CSS` file.

    ```css
    ul {
      list-style-type: none;
      margin: 0;
      padding: 0;
      width: 10%;
      background-color: [COLOR];
      position: fixed;
    }
    ```
    
    Note that you should make the background-color here different from the color in step 1; otherwise it won't look any         different than before. Setting the width to 10% makes the links box take up 10% of the page. If you change the width of     your browser around, you should see the links box change with it. Setting the position to fixed keeps the link box in       the top left corner of your webpage even if you scroll down.
1. You can center the links within their box and change their color by adding the following code.

    ```css
    li a {
      display: block;
      color: [COLOR];
      padding: 8px 8px;
      text-align: center;
      border-bottom: 1px solid [COLOR];
    }
    ```
    The border-bottom property adds a dividing line between each link. To avoid having an extra line at the bottom of the       links box, add 

    ```css
    li:last-child {
      border-bottom: none;
    }
    ```
1. To change the color of each link and its background when it is hovered over with the cursor, add

    ```css
    li a:hover {
      background-color: [COLOR];
      color: [COLOR];
    }
    ```
        
1. The title of the page is contained in the `<h1>` HTML blocks. You can center it, set the color and font size, and add an underline with the following block of code.

    ```css
    h1 {
      color: [COLOR];
      text-align: center;
      font-size: [SIZE]px;
      border-bottom: 3px solid [COLOR];
      padding: 15px;
      width: 60%;
      margin: auto;
      margin-bottom: 30px;
    }
    ```
        
   `text-align: center` centers the title in the middle of the page. `border-bottom` adds the underline. `padding` sets the     space between the title and the underline. `width` sets how much of the screen the underline occupies. `margin: auto`       centers the underline. `margin-bottom` sets the spacing between the underline and anything that might go below it. This     will be applicable in later sections.
   
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. Click through the links on each page and make sure the colors and placement remain consistent. 
1. Resize your browser window and observe how the components dynamically change to account for this.

### Style the home (notifications) page

Now that you have the basic styling done for the website as a whole, you can focus on styling the elements unique to each page. Let's start with the home page. This time we'll embed the style directly into the HTML instead of placing it in a separate file.
1. Indent and set the font size for the notification messages. In your html file that controls the home page, modify the `<div>` to include a style instruction:

    ```html
    <div style="margin-left:20%;font-size:20px;">
    ```
1. Make the font size for the date and time part smaller. To do this modify the `<small>` tag:

    ```html
    <small style="font-size:12px;">
    ```

### Style the search bar on the search page

Because the search bar is only a feature of the search page, you could style it directly within the HTML file that controls the search page. However, you'll add more style instructions for the search bar than you did for displaying the notifications, so you'll put the style for it in your CSS file to keep the HTML file from getting too cluttered.

1. In the CSS file, add style for the `<h2>` tag that gets displayed when there are no search results.

    ```css
    h2 {
      color: [COLOR];
      text-align: center;
      font-size: [SIZE]px;
    }
    ```
1. In the HTML file responsible for the search page, add a class name to the `<form>` tag, so it can be referenced from an external CSS file. For example, 

    ```html
    <form class="search" action="/search" method="get">
    ```
    Note that the class name does not matter as long as you are consistent in referencing it.
1. In the CSS file, add code to center the search bar and place it 50px below the underlined title.

    ```css
    form.search {
      text-align: center;
      margin-top: 50px;
    }
    ```
### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. Visit the home page to see the notification messages indented and notice that the date and time part is smaller than the actual message.
1. Visit the search page to see the search bar centered along with the `"No Search Results"` text.

### Style the thumbnails for both the photos and search pages

1. Add HTML
1. Add CSS

### Make thumbnails clickable

1. Add HTML
1. Add CSS
1. Add JavaScript

### Make photos scrollable

1. Add HTML
1. Add CSS
1. Add JavaScript

