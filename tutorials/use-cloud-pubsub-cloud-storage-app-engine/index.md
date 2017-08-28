---
title: How to Use Cloud Pub/Sub Notifications and Cloud Storage with App Engine
description: Create a shared photo album using Cloud Pub/Sub, Cloud Storage, Datastore, and App Engine.
author: ggchien, cmwoods
tags: App Engine, Cloud Pub/Sub, Cloud Storage, GCS, Datastore, photo album
date published:
---

This tutorial teaches you how to integrate several Google products to simulate a shared photo album, hosted on App Engine and managed through the Cloud Platform Console.

Users interact with the web application only through the Cloud Platform Console; photos cannot be uploaded or deleted through the website. Two buckets exist in [Cloud Storage](https://cloud.google.com/storage/) (GCS): one to store the uploaded photos and the other to store the thumbnails of the uploaded photos. [Cloud Datastore](https://cloud.google.com/datastore/) stores all non-image entities needed for the web application, which is hosted on [App Engine](https://cloud.google.com/appengine/). Notifications of changes to the GCS photo bucket are sent to the application via [Cloud Pub/Sub](https://cloud.google.com/pubsub/). The [Google Cloud Vision API Client Library](https://developers.google.com/api-client-library/python/apis/vision/v1) is used to label photos for search.

A general overview of how the application works is shown in the diagrams below.
![Shared Photo App Workflow](https://storage.googleapis.com/gcp-community/tutorials/use-cloud-pubsub-cloud-storage-app-engine/shared-app-workflow.png)

The overall workflow of receiving a notification:
![Receiving a Notification](https://github.com/GChien44/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/receiving-a-notification.png)

1. A user uploads or deletes something from their GCS photo bucket.
1. A Cloud Pub/Sub message is sent.
1. The Cloud Pub/Sub message is received by App Engine.
1. The Cloud Pub/Sub message is formatted and stored as a `Notification` in Datastore.
1. If the event type from the message is `OBJECT_FINALIZE`, the uploaded photo is compressed and stored as a thumbnail in a separate GCS thumbnail bucket. If the event type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, the thumbnail matching the name and generation number of the deleted or archived photo is deleted from the GCS thumbnail bucket.
1. If the event type from the message is `OBJECT_FINALIZE`, then the Google Cloud Vision API is used to generate labels for the uploaded photo.
1. If the event type from the message is `OBJECT_FINALIZE`, then a new `ThumbnailReference` is created and stored in Datastore. If the event type from the message is `OBJECT_DELETE` or `OBJECT_ARCHIVE`, then the appropriate `ThumbnailReference` is deleted from Datastore.

The overall workflow of loading the home page:
![Loading Notifications](https://github.com/GChien44/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-home-page.png)

0. The user navigates to https://project-test-172118.appspot.com/.
1. A previously-specified number of `Notifications` are queried from Datastore, ordered by date and time, most recent first.
1. The queried `Notifications` are sent to the front-end to be formatted and displayed on the home page.
1. The HTML file links to an external CSS file for styling.

The overall workflow of loading the photos page:
![Loading Photos](https://github.com/GChien44/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-photos-page.png)

0. The user navigates to https://project-test-172118.appspot.com/photos.
1. All the `ThumbnailReferences` are fetched from Datastore, ordered by date and time, most recent first.
1. Each `ThumbnailReference` is used to get a serving url for the corresponding thumbnail stored in the GCS thumbnail bucket.
1. A dictionary of `ThumbnailReferences` and their serving urls is sent to the front-end to be formatted and displayed on the photos page.
1. The HTML file links to an external CSS file for styling.

The overall workflow of loading the search page: 
![Loading Search](https://github.com/GChien44/community/blob/master/tutorials/use-cloud-pubsub-cloud-storage-app-engine/loading-search-page.png)

0. The user navigates to https://project-test-172118.appspot.com/search.
1. All the `ThumbnailReferences` are fetched from Datastore, ordered by date and time, most recent first.
1. Each queried `ThumbnailReference` that contains the search term as one of its `labels` is used to get a serving url for the corresponding thumbnail stored in the GCS thumbnail bucket.
1. A dictionary of `ThumbnailReferences` that contain the search term as one of their `labels` and their serving urls is sent to the front-end to be formatted and displayed on the search page.
1. The HTML file links to an external CSS file for styling.


Note: Basic coding (Python, HTML, CSS, JavaScript) and command line knowledge is necessary to complete this tutorial.

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

## Set up

1. [Install the Google Cloud SDK](https://cloud.google.com/sdk/downloads) for necessary commands such as `gcloud` and `gsutil`.
1. [Create a Google Cloud Platform account](https://console.cloud.google.com/) for using the Cloud Platform Console.
1. In the Cloud Platform Console, [create a new project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Your project has a unique ID that is part of your web application url. 
1. Enable billing: [create a billing project](https://support.google.com/cloud/answer/6288653?hl=en). Learn more about billing [here](https://cloud.google.com/appengine/docs/standard/python/console/).
1. In the command line, [set the default project](https://cloud.google.com/sdk/docs/managing-configurations) to your newly created project by running the following command:

    ```sh
    gcloud config set project [PROJECT ID]
    ```

1. In the Cloud Platform Console, [create a bucket](https://www.google.com/urlsa=D&q=https%3A%2F%2Fcloud.google.com%2Fstorage%2Fdocs%2Fcreating-buckets). This bucket is for storing the photos of your shared photo album.
1. If you want collaborators on your photo album, [add IAM Permissions](https://www.google.com/url?sa=D&q=https%3A%2F%2Fcloud.google.com%2Fstorage%2Fdocs%2Faccess-control%2Fusing-iam-permissions%23bucket-add) to your bucket. Select`Storage Object Admin` as the role for each collaborator you want to add.
1. Change the photos bucket permissions to make it publicly readable so that the photos may be viewed on your website. To do this, you'll need to [make your bucket data public](https://www.google.com/url?sa=D&q=https%3A%2F%2Fcloud.google.com%2Fstorage%2Fdocs%2Faccess-control%2Fmaking-data-public%23buckets).

1. Create another bucket with `Multi-Regional` or `Regional` storage. This bucket is for storing the thumbnails of the photos in your shared photo album.
1. [Create a new topic](https://www.google.com/url?sa=D&q=https%3A%2F%2Fcloud.google.com%2Fpubsub%2Fdocs%2Fquickstart-console%23create_a_topic) with the same name as your photos bucket.
1. Click on the three-dots icon for your photo album topic and click on `New subscription`. Change the `Delivery Type` to `Push into an endpoint url`. This is the url that receives your Cloud Pub/Sub messages. For a url, use the following, replacing [PROJECT-ID] with the name of your project: `http://[PROJECT ID].appspot.com/_ah/push-handlers/receive_message`.
1. Configure Cloud Pub/Sub notifications for your photos bucket by using the command line to run:

    ```sh
    gsutil notification create -f json gs://[PHOTO BUCKET NAME]
    ```

## Basic application layout

If you do not feel like coding the entire application from scratch, feel free to clone the git repository with a default application by running:

  ```sh
  git clone https://github.com/GChien44/tutorial-v2.git
  ```

Note that if you choose this option, you still need to make a `lib` directory and run the `install` command. These tasks are outlined in steps one and three of the **Libraries and `app.yaml`** section. In addition to these tasks, some constants in the `main.py` file still need to be changed to suit your GCS bucket names. Look for the constants THUMBNAIL_BUCKET, PHOTO_BUCKET, NUM_NOTIFICATIONS_TO_DISPLAY, and MAX_LABELS immediately after the imports at the top of the file.

The rest of this tutorial assumes that you did not clone the above git repository, and are building the application from scratch.

### Libraries and `app.yaml`

The external library and `app.yaml` files are necessary for configuring your App Engine application and importing the required libraries.

1. Choose a directory to house your project. From this point forward, this will be referred to as the host directory. Inside your host directory, create a new directory called `lib` for the storage of external libraries.
1. In your host directory, create the file `requirements.txt` and copy in the following text:

    ```txt
    jinja2
    webapp2
    GoogleAppEngineCloudStorageClient
    google-api-python-client
    ```

    This specifies which libraries are necessary for your application.

1. Install the external libraries into your `lib` directory:

    ```sh
    pip install -t lib -r requirements.txt
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
    ```

1. Add constants. `THUMBNAIL_BUCKET` is the name of the GCS bucket you created in Set Up step #8 to store the thumbnails of photos uploaded to your GCS photo bucket. `PHOTO_BUCKET` is the name of the GCS bucket you created in Set Up step #5 to store the photos uploaded to your shared photo album. `NUM_NOTIFICATIONS_TO_DISPLAY` regulates the maximum number of notifications displayed on the home/notifications page of your web application. `MAX_LABELS` regulates the maximum number of labels associated with each photo using Cloud Vision.

    ```py
    THUMBNAIL_BUCKET = '[GCS THUMBNAIL BUCKET NAME]'
    PHOTO_BUCKET = '[GCS PHOTO BUCKET NAME]'
    NUM_NOTIFICATIONS_TO_DISPLAY = [SOME NUMBER]
    MAX_LABELS = [SOME NUMBER]
    ```
 
1. Set up [jinja2](http://jinja.pocoo.org/docs/2.9/templates/) for HTML templating.

    ```py
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir))
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

1. Create a `MainHandler` with a `get` method for getting information from the server and writing it to the home/notification page HTML file. There are no values to pass into the template yet.

    ```py
    class MainHandler(webapp2.RequestHandler):
        def get(self):
          template_values = {}
          template = jinja_environment.get_template('[NAME OF YOUR HOME PAGE HTML FILE]')
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

1. [Deploy your application](https://cloud.google.com/appengine/docs/standard/python/getting-started/deploying-the-application) by running:

    ```sh
    gcloud app deploy
    ```

    Your web application should be viewable at `http://[PROJECT ID].appspot.com`. You can either navigate there directly through your web browser or launch your browser and view the app by running the command:

    ```sh
    gcloud app browse
    ```

## Creating the notifications page

### Receiving Cloud Pub/Sub messages

During the Set Up phase, you configured [Cloud Pub/Sub push messages](https://cloud.google.com/pubsub/docs/push#receive_push) to be sent to the url you specified for the `ReceiveMessage` class in your `main.py` file. When you receive a Pub/Sub message, you must get necessary information from it and acknowledge its reception.

1. In your `main.py` file, in the `ReceiveMessage` class, in your `post` method, obtain the [notification attributes](https://cloud.google.com/storage/docs/pubsub-notifications) from the incoming Cloud Pub/Sub message. A logging statement can be used for easier debugging.

    ```py
    # Logging statement is optional.
    logging.debug('Post body: {}'.format(self.request.body))
    message = json.loads(urllib.unquote(self.request.body))
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
    index = photo_name.index('.jpg')
    thumbnail_key = '{}{}{}'.format(
        photo_name[:index], generation_number, photo_name[index:])
    ```

You now have all of the information needed to create the necessary notification and communicate with GCS.

### Creating and storing `Notifications`

1. Write a `create_notification` helper function to generate notifications. Note that if the `event_type` is `OBJECT_METADATA_UPDATE`, the `message` field is `None`.

    ```py
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
    ```

1. Call the `create_notification` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    new_notification = create_notification(
        photo_name,
        event_type,
        generation_number,
        overwrote_generation=overwrote_generation,
        overwritten_by_generation=overwritten_by_generation)
    ```

1. Check if the new notification has already been stored. Cloud Pub/Sub messaging guarantees at-least-once delivery, meaning a Pub/Sub notification may be received more than once. If the notification already exists, there has been no new change to the GCS photo bucket, and the Pub/Sub notification can be ignored.

    ```py
    exists_notification = Notification.query(
        Notification.message == new_notification.message,
        Notification.generation == new_notification.generation).get()

    if exists_notification:
        return
    ```

1. Do not act for `OBJECT_METADATA_UPDATE` events, as they signal no change to the GCS photo bucket images themselves.

    ```py
    if new_notification.message is None:
      return
    ```

1. Store the new notification in Cloud Datastore. This, and all further code in the `ReceiveMessage` class, is only executed if the new notification is not a repeat and is not for an `OBJECT_METADATA_UPDATE` event.

    ```py
    new_notification.put()
    ```

### Writing `Notifications` to the HTML file

1. In `main.py`, in the `MainHandler`, in the `get` method, fetch all `Notifications` from Cloud Datastore in reverse date order and include them in `template_values`, to be written to the `home/notifications` page HTML file.

    ```py
    notifications = Notification.query().order(
        -Notification.date).fetch(NUM_NOTIFICATIONS_TO_DISPLAY)
    template_values = {'notifications': notifications}
    ```

1. In the `home/notifications` page HTML file, loop through the `notifications` list you rendered to the template in `main.py` and print the formatted date/time of the notification and the notification message.

    ```html
    {% for notification in notifications %}
      <div>
        <p><small>{{notification.date.strftime('%B %d %Y %I:%M')}} UTC: </small>{{notification.message}}</p>
      </div>
    {% endfor %}
    ```

### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. [Upload an image](https://www.google.com/url?sa=D&q=https%3A%2F%2Fcloud-dot-devsite.googleplex.com%2Fstorage%2Fdocs%2Fobject-basics%23upload) with the extension `.jpg` to your photo bucket.
1. Open the `Products & services` menu again and navigate to `Datastore`. There should be a `Notification` listed with the message `[UPLOADED PHOTO NAME] was uploaded.`.
1. View your deployed application in your web browser. The new notification should be listed on the home page. You may need to refresh the page.

If you encounter errors, open the `Products & services` menu and navigate to `Logging`. Use the messages there to debug your application.

## Implementing photo upload functionality

When a Cloud Pub/Sub notification is received, different actions occur depending on the `eventType`. If the notification indicates an `OBJECT_FINALIZE` event, the uploaded photo must be shrunk to a thumbnail, the thumbnail of the photo must be stored in the GCS thumbnail bucket, the photo must be labeled using the Google Cloud Vision API, and a `ThumbnailReference` must be stored in Datastore.

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
        filename = '/gs/{}/{}'.format(PHOTO_BUCKET, photo_name)
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
        write_retry_params = cloudstorage.RetryParams(
            backoff_factor=1.1,
            max_retry_period=15)
        filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
        with cloudstorage.open(
                filename, 'w', retry_params=write_retry_params) as filehandle:
            filehandle.write(thumbnail)
    ```

1. Call the `store_thumbnail_in_gcs` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    store_thumbnail_in_gcs(thumbnail_key, thumbnail)
    ```

### Labeling the photo using Google Cloud Vision

The [Google Cloud Vision API Client Library for Python](https://developers.google.com/api-client-library/python/apis/vision/v1) can be used to [annotate](https://developers.google.com/resources/api-libraries/documentation/vision/v1/python/latest/vision_v1.images.html) images, assigning them labels that describe the contents of the picture. You can later use these labels to search for specific photos.

1. Create the `uri` to reference the appropriate photo in the GCS photo bucket.

    ```py
    uri = 'gs://{}/{}'.format(PHOTO_BUCKET, photo_name)
    ```
 
1. Write the `get_labels` helper function.

    ```py
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
    ```
   
1. Call the `get_labels` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    labels = get_labels(uri, photo_name)
    ```
 
The `labels` list has now been obtained and can be used to build the `ThumbnailReference`.

### Creating and storing the `ThumbnailReference`

At this point, the only other thing you need to create the required `ThumbnailReference` is the url of the original photo. Obtain this, and the `ThumbnailReference` can be created and stored.

1. Write the `get_original_url` helper function to return the url of the original photo.

    ```py
    def get_original_url(photo_name, generation):
        original_photo = 'https://storage.googleapis.com/' \
            '{}/{}?generation={}'.format(
                PHOTO_BUCKET,
                photo_name,
                generation)
        return original_photo
    ```

1. Call the `get_original_url` helper function in the `post` method of the `ReceiveMessage` class.

    ```py
    original_photo = get_original_url(photo_name, generation_number)
    ```

1. Create the `ThumbnailReference` using the information gathered from the Cloud Pub/Sub message, `get_labels` function, and `get_original_url` function.

    ```py
    thumbnail_reference = ThumbnailReference(
                thumbnail_name=photo_name,
                thumbnail_key=thumbnail_key,
                labels=list(labels),
                original_photo=original_photo)
    ```

1. Store the newly created `ThumbnailReference` in Datastore.

    ```py
    thumbnail_reference.put()
    ```

You have now completed all of the code necessary to store the information about an uploaded photo in GCS and Datastore.

### Writing thumbnails to the photos HTML file

1. Write the `get_thumbnail_serving_url` helper function. This function returns a [serving url](https://cloud.google.com/appengine/docs/standard/python/images/#get-serving-url) that accesses the thumbnail from the GCS thumbnail bucket.

    ```py
    def get_thumbnail_serving_url(photo_name):
        filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, photo_name)
        blob_key = blobstore.create_gs_key(filename)
        return images.get_serving_url(blob_key)
    ```

1. In `main.py`, in the `PhotosHandler`, in the `get` method, fetch all `ThumbnailReferences` from Cloud Datastore in reverse date order. Create an ordered dictionary, calling upon the `get_thumbnail_serving_url` helper function, with the thumbnail serving urls as keys and the `thumbnail_references` as values. Include the dictionary in `template_values`, to be written to the appropriate HTML file.

    ```py
    thumbnail_references = ThumbnailReference.query().order(
        -ThumbnailReference.date).fetch()
    thumbnails = collections.OrderedDict()
    for thumbnail_reference in thumbnail_references:
        img_url = get_thumbnail_serving_url(thumbnail_reference.thumbnail_key)
        thumbnails[img_url] = thumbnail_reference
    template_values = {'thumbnails': thumbnails}
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
1. View your deployed application in your web browser.
    1. Check that the new notification is listed on the home page. You may need to refresh the page.
    1. Check that the thumbnail and name of the uploaded photo are displayed on the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Implementing photo delete/archive functionality

Alternatively, if the received Cloud Pub/Sub notification indicates an `OBJECT_DELETE` or `OBJECT_ARCHIVE` event, the thumbnail must be deleted from the GCS thumbnail bucket, and the `ThumbnailReference` must be deleted from Datastore.

Because these actions only occur in the case of a photo delete or archive, an `elif` statement can be used inside the `ReceiveMessage` class of `main.py`, where the initial `if` statement of the block is the one specifying the event type as `OBJECT_FINALIZE`.

```py
elif event_type == 'OBJECT_DELETE' or event_type == 'OBJECT_ARCHIVE':
    # Photo delete/archive-specific code here.
```

1. Write the `delete_thumbnail` helper function to delete the specified thumbnail from the GCS thumbnail bucket and delete the `ThumbnailReference` from Datastore.

    ```py
    def delete_thumbnail(thumbnail_key):
        filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
        blob_key = blobstore.create_gs_key(filename)
        images.delete_serving_url(blob_key)
        thumbnail_reference = ThumbnailReference.query(
            ThumbnailReference.thumbnail_key == thumbnail_key).get()
        thumbnail_reference.key.delete()

        filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
        cloudstorage.delete(filename)
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
1. View your deployed application in your web browser.
    1. Check that the new notification is listed on the home page. You may need to refresh the page.
    1. Check that the thumbnail and name of the uploaded photo are no longer displayed on the photos page.

If you encounter errors, use the `Logging` messages to debug your application.

## Creating the search page

The search page of the web application has a search bar users can enter a `search-term` into. The `ThumbnailReferences` with the `search-term` in their `labels` lists are added to the thumbnails dictionary and used to obtain and display the correct thumbnails to the search page.

1. In `main.py`, in the `SearchHandler` class, fill out the `get` method.
    1. Get the `search-term` from the user. The `search-term` should be converted to lower case to avoid case sensitivity.

        ```py
        search_term = self.request.get('search-term').lower()
        ```

    1. In a similar manner as in the `PhotosHandler`, build an ordered dictionary with thumbnail serving urls as keys and `ThumbnailReferences` as values. However, unlike in the `PhotosHandler`, although you query all `ThumbnailReferences` from Datastore, you should only add the thumbnails labeled with the `search-term` to the dictionary.

        ```py
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
        ```

    1. Include the thumbnails dictionary in `template_values`, to be written to the search page HTML file.

        ```py
        template_values = {'thumbnails': thumbnails}
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

Note: Examining the `labels` lists of the `ThumbnailReferences` in Datastore can help you determine whether or not the search is functioning as it is meant to.

If you encounter errors, use the `Logging` messages to debug your application.

#### Congratulations! You now have a functioning shared photo album.

Note: Other users you listed as `Storage Admins` for your GCS photo bucket should also be able to [upload images to the bucket](https://cloud.google.com/storage/docs/gsutil/commands/cp) and see their changes take effect on the website.

## Style

Now that you a functioning website, it's time to add formatting to it. You'll do this by adding CSS and JavaScript to your already existing HTML files. 

### Set up

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
 
1. Inside the directory you created, create a CSS file. Leave it blank for now; you'll add code to it in the following sections. Note that your file must have the extension `.css`.
1. In each HTML file (you should have three) add the following code inside the `<head>` section, replacing [DIRECTORY NAME] and [FILE NAME] with the appropriate directory and file.

    ```html
    <link rel="stylesheet" type="text/css" href="/[DIRECTORY NAME]/[FILE NAME]">
    ```

### Add style common to every page

First, you'll style the HTML components present on every page of the website. This includes the body, the links to other pages, and the title of the page. You should run your app locally after each step to see the changes.

1. Add the following code to your `CSS` file to set the background color. Replace [COLOR] with a color of your choice. 

    ```css
    body{
      background-color: [COLOR];
    }
    ```

   You can specify the color by typing in the name of it, such as `blue`, by specifying the rgb configuration, or by giving    a hexadecimal representation. You can find more information on how colors work in CSS [here]
   (https://www.w3schools.com/css/css_colors.asp). 
1. Next you'll create a box to hold the links to other pages. Add the following code to your `CSS` file.

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
    The border-bottom property adds a dividing line between each link. To avoid having an extra line at the bottom of the       links box, add:

    ```css
    li:last-child {
      border-bottom: none;
    }
    ```
1. To change the color of each link and its background when it is hovered over with the cursor, add:

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

Now that you have the basic styling done for the website as a whole, you can focus on styling the elements unique to each page, starting with the home page. This time you'll embed the style directly into the HTML instead of placing it in a separate file.
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
1. In the HTML file responsible for the search page, add a class name to the `<form>` tag, so it can be referenced from an external CSS file. For example:

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

The thumbnails displayed on your website currently should appear in a single vertical column on the left of the page. In this section you'll reformat them to appear in a table format.

1. Add HTML in the files that control the photos and search pages. The code instructions for this step should be implemented in both the photos page HTML file and the search page HTML file.
    1. Add a gallery class outside the for loop to hold all the thumbnails:

        ```html
        <div class="gallery">
          {% for img_url, thumbnail_reference in thumbnails.iteritems() %}
          ...
          {% endfor %}
        </div>
        ```

    1. Add class names to the `<div>` tags inside the for loop. For example:

        ```html
        <div class="thumbnail">
          <img src='{{img_url}}'>
          <div class="descent">{{thumbnail_reference.thumbnail_name}}</div>
        </div>
        ```
1. Add CSS to format the classes you just added. The code instructions for this step only need to be implemented once in your external CSS file. As long as you have the same class names in the two HTML files from step 1, the code in this section will be applied to both pages automatically.
    1. Set the margins on the gallery class so the thumbnails don't appear too far on the left of the page (they would           interfere with the links if the page scrolled down) and appear centered, i.e. not too far on the right of the page           either.

        ```css
        div.gallery {
          margin-left: 12%;
          margin-right: 10%;
        }
        ```

    1. Use the thumbnail class to create a kind of box to hold the thumbnail image and its caption:

        ```css
        div.thumbnail {
          margin: 5px;
          float: left;
          width: 180px;
          height: 240px;
          border: 1px solid [COLOR];
        }
        ```
        `margin` sets the spacing between the thumbnails. The `width` and `height` properties match the width and height             that thumbnails are sized to in `main.py`.
    1. Further format the thumbnail class to display thumbnails in a table:

        ```css
        div.thumbnail:after {
          content: "";
          display: table;
          clear: both;
        }
        ```
    1. Center the thumbnail image within the thumbnail box:

        ```css
        div.thumbnail img {
          display: block;
          margin: auto;
        }
        ```
        Note that while the width of the thumbnail box is to 180 pixels, the same width thumbnails are resized to in                `main.py`, portrait oriented photos may have a smaller width. This ensures that photos are centered within the 180          pixels even when they do not occupy 180 pixels.
    1. Center the caption 10 pixels below the thumbnail image using the descent class:

        ```css
        div.descent {
          padding: 10px;
          text-align: center;
        }
        ```

### Checkpoint

1. Run your application locally to check for basic errors, then deploy your application.
1. Navigate to the photos page and check that the thumbnails displayed there now appear in a table format with their captions centered underneath.
1. Navigate to the search page and enter a search term that will yield results. The displayed thumbnails should appear in the same format as on the photos page.

### Make thumbnails clickable

Now that your thumbnails are nicely formatted, you can make your webpage display the original photo when a thumbnail is clicked on by incorporating JavaScript into your HTML files.

1. Add HTML for both the photos and search pages. The instructions for this step should be implemented in your two HTML files responsible for the photos and search pages.
    1. Add an id to the thumbnail image:

        ```html
        <img id='{{thumbnail_reference.thumbnail_name}}' src='{{img_url}}' >
        ```
        This will allow the image to be looked up by id, which is how you will implement an onclick function to display the         original photo when its thumbnail is clicked.
    1. Within the gallery class, after the end of the for loop, insert:

        ```html
        <div id='myModal' class="modal">
          <span class="close" onclick="closeModal()">&times;</span>
          <div class="modal-content">
          {% for img_url, thumbnail_reference in thumbnails.iteritems() %}
            <div class="mySlides">
              <img id='{{loop.index}}' src='{{thumbnail_reference.original_photo}}' alt='{{thumbnail_reference.thumbnail_name}}'>
            </div>
          {% endfor %}
            <div class="caption-container">
              <p id="caption"></p>
            </div>
          </div>
        </div>
        ```
        `myModal` is what will be displayed when a thumbnail is clicked on. The `close` class is what restores the thumbnail         view when it is clicked on. `closeModal()` is a JavaScript function you'll define in step 3. The class `modal-               content` includes `mySlides` and the `caption-container`. Only one `mySlides` will be displayed at a time with its           image. The `caption` will be updated to match the `mySlides` being displayed.

1. Add styling to your external CSS file. This will format both the photos and search pages as long as they have the same class names for the HTML you just added.
    1. Add an effect to the thumbnails so that when the cursor hovers over them, they turn slightly transparent and the         cursor changes to a pointer to indicate to the user that they can click on thumbnails.

        ```css
        div.thumbnail img:hover {
          opacity: 0.7;
          cursor: pointer;
        }
        ```
    1. Format the modal that takes over the whole page when a thumbnail is clicked:

        ```css
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
          background-color: rgba(0,0,0,0.8);
        }
        ```
        `display` is initially set to none because the modal should only be displayed when a thumbnail is clicked. The logic         for this will be added in step 3. `width` and `height` are set to 100% to take up the whole page. `background-color`         is set to a somewhat transparent black so thumbnails will still be partially visible behind the modal.
    1. Place the `close` button in the top right corner of the modal:

        ```css
        span.close {
          position: absolute;
          top: 15px;
          right: 35px;
          color: #f1f1f1;
          font-size: 40px;
          font-weight: bold;
          transition: 0.3s;
        }
        ```
    1. Add hover and focus effects to the `close` button:

        ```css
        span.close:hover,
        span.close:focus {
          color: #bbb;
          text-decoration: none;
          cursor: pointer;
        }
        ```
    1. Format modal-content, the box that will hold the original photo and caption.

        ```css
        div.modal-content {
          position: relative;
          margin: auto;
          padding: 0;
          width: 55%;
          max-width: 700px;
        }
        ```
        This centers modal-content and sets it to take up 55% of the page, with a max width of 700 pixels. This means that           even if 700 pixels is less than 55% of the page, modal-content will never be wider than 700 pixels.
    1. Set the default display of mySlides to none:

        ```css
        div.mySlides {
          display: none;
        }
        ```
    1. Format the image in mySlides to match the width of modal-content:

        ```css
        div.mySlides img {
          display: block;
          margin: auto;
          width: 100%;
          max-width: 700px;
          height: auto;
        }
        ```
        `height` is set to auto so the image will retain its original proportions.
    1. Position `caption-container` below the image in the `modal-content` box, where [COLOR] is the color the caption text     will be.

        ```css
        .caption-container {
          text-align: center;
          padding: 2px 16px;
          color: [COLOR];
        }
        ```
    1. Format the caption to be centered in `caption-container` and have a height of 50 pixels:

        ```css
        #caption {
          margin: auto;
          display: block;
          width: 80%;
          max-width: 700px;
          text-align: center;
          padding: 10px 0;
          height: 50px;
        }
        ```
1. Add JavaScript embedded within the HTML. The instructions in this section will need to be implemented in both HTML files associated with the photos and search pages.
    1. Implement the function to close the modal after the end of the `gallery` class.

        ```javascript
        <script>
          function closeModal() {
            document.getElementById('myModal').style.display = "none";
          }
        </script>
        ```
        This function is called whenever the close button is clicked on and resets the `modal` class to not be displayed.
    1. Within the `gallery` class still, but after the `modal` class, add the following for loop and embedded script:

        ```html
        {% for img_url, thumbnail_reference in thumbnails.iteritems() %}
        <script>
          var modal = document.getElementById('myModal');
          var img = document.getElementById('{{thumbnail_reference.thumbnail_name}}');
          img.onclick = function(){
            modal.style.display = "block";
            currentSlide({{loop.index}});
          }
        </script>
        {% endfor %}
        ```
        This defines a function that gets called whenever a thumbnail is clicked on. The `modal` class is displayed and             another function, `currentSlide` is called.
    1. Add a variable and implement currentSlide() in the same script that contains closeModal().

        ```javascript
        var slideIndex;

        function currentSlide(n) {
          slideIndex = n;
          showSlides(slideIndex);
        }
        ```
        Note that currentSlide() calls another function, showSlides(). You'll implement this next.
    1. Implement showSlides:
 
        ```javascript
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
        ```
        This function sets every `mySlides` class to not be displayed except for the one that contains the original photo of         the thumbnail that was clicked. The caption is set to the name of the image displayed.

### Checkpoint
1. Run your application locally to check for basic errors, then deploy your application.
1. Navigate to the photos page and hover over a thumbnail. It should become less opaque and your cursor should change.
1. Click on a thumbnail. Observe that the original photo with caption appears over the photos page.
1. Close the modal and restore the thumbnail view.
1. Check that the search page has the same behavior.

### Make photos scrollable
The last feature to add to your website is scrolling. After clicking on a thumbnail, the original photo appears. In this section, you'll add the ability to scroll to either side of that photo and see the original photos of other thumbnails without having to close the modal and reopen it by clicking on another thumbnail.

1. Add HTML for both the photos and search pages. The instructions for this step should be implemented in your two HTML files responsible for the photos and search pages.
    1. Within the 'mySlides' class add the class 'numbertext'. This will display the current number of the photo displayed,     i.e. `1/5`. 
        ```html
        <div class="numbertext">{{loop.index}} / {{thumbnails|length}}</div>
        ```
        `loop.index` is the current iteration of the for loop, and `thumbnails|length` is the total number of iterations the for           loop will go through.
    1. After the for loop containing `mySlides` and classes for previous and next buttons:

        ```html
         <a class="prev" onclick="plusSlides(-1)">&#10094</a>
         <a class="next" onclick="plusSlides(1)">&#10095</a>
        ```
        `&#10094` and `&#10095` are the HTML codes for previous and next arrows, respectively. The plusSlides() function             will be implemented in Step 3.

1. Add styling to your external CSS file. This will format both the photos and search pages as long as they have the same class names for the HTML you just added.
    1. Place the `numbertext` class in the top left of the original photo:
        ```css
        .numbertext {
          color: #f2f2f2;
          font-size: 12px;
          padding: 8px 12px;
          position: absolute;
          top: 0;
        }
        ```
    1. Place the next and previous arrows over the photo:
        ```css
        .prev,
        .next {
          cursor: pointer;
          position: absolute;
          top: 50%;
          width: auto;
          padding: 15px;
          margin-top: -50px;
          color: white;
          font-weight: bold;
          font-size: 20px;
          transition: 0.6s ease;
          border-radius: 0 3px 3px 0;
          user-select: none;
          -webkit-user-select: none;
        }
        ```
    1. Reposition the next arrow to be on the right side of the photo:
        ```css
        .next {
          right: 0;
          border-radius: 3px 0 0 3px;
        }
        ```
    1. Add hover effects to arrows:
        ```css
        .prev:hover,
        .next:hover {
          background-color: rgba(0, 0, 0, 0.8);
        }
        ```
1. Add JavaScript embedded within the HTML. The instructions in this section will need to be implemented in both HTML files associated with the photos and search pages.
    1. Implement the plusSlides function:
        ```javascript
        function plusSlides(n) {
          slideIndex +=n;
          showSlides(slideIndex);
        }
        ```
    1. Additional logic needs to be added to showSlides to allow wrapping around from the last photo to the first photo and when the next arrow is clicked and vice versa. Add the following two lines of code above where `var image` is declared.
        ```javascript
        if (n > slides.length) {slideIndex = 1}
        if (n < 1) {slideIndex = slides.length}
        ```

### Checkpoint
1. Run your application locally to check for basic errors, then deploy your application.
1. Navigate to the photos page and click on a thumbnail. The photo that appears should now have next and previous arrows as well as a number in the top left corner. Click the arrows to scroll through the photos. Check that the caption updates correctly as you scroll.
1. Verify that when you click the previous arrow on the first photo, the last photo appears, and that when you click the next arrow on the last photo, the first photo appears.
1. Navigate to the search page and search for something. Clicking on the thumbnail results should display the same behavior as on the photos page.

#### Congratulations! You've completed this tutorial and now have a functioning, user-friendly website!

## Clean up

1. If necessary, [close your billing account](https://support.google.com/cloud/answer/6288653?hl=en).
1. [Delete your project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Note: you won't be able to use this project ID again.
