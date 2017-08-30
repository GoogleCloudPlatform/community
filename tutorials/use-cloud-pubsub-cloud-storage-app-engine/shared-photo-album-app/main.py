# Copyright 2017 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This main python file contains the backend logic of the website, including
the reception of Cloud Pub/Sub messages and communication with GCS
and Datastore.
"""

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

# Constants. Note: Change THUMBNAIL_BUCKET and PHOTO_BUCKET to
# be applicable to your project.
THUMBNAIL_BUCKET = 'thumbnails-bucket'
PHOTO_BUCKET = 'shared-photo-album'
NUM_NOTIFICATIONS_TO_DISPLAY = 50
MAX_LABELS = 5

# Set up jinja2 for HTML templating.
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir))


class Notification(ndb.Model):
    """Describes a Notification to be displayed on the home/news
    feed page.

    message: Notification text
    date: date/time of posting
    generation number: generation number of the modified object.
    Used to prevent the display of repeated notifications."""

    message = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    generation = ndb.StringProperty()


class ThumbnailReference(ndb.Model):
    """Describes a ThumbnailReference, which holds information about a given
    thumbnail (not the thumbnail itself).

    thumbnail_name: same as photo name.
    thumbnail_key: used to distinguish similarly named photos. Includes
    photo name and generation number.
    labels: list of label_names that apply to the photo.
    original_photo: url of the original photo, stored in GCS."""

    thumbnail_name = ndb.StringProperty()
    thumbnail_key = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    labels = ndb.StringProperty(repeated=True)
    original_photo = ndb.StringProperty()


class MainHandler(webapp2.RequestHandler):
    """Home/news feed page (notification listing)."""
    def get(self):
        # Fetch all notifications in reverse date order.
        notifications = Notification.query().order(
            -Notification.date).fetch(NUM_NOTIFICATIONS_TO_DISPLAY)
        template_values = {'notifications': notifications}
        template = jinja_environment.get_template('notifications.html')
        self.response.write(template.render(template_values))


class PhotosHandler(webapp2.RequestHandler):
    """All photos page: displays thumbnails of all uploaded photos."""
    def get(self):
        # Get thumbnail references from datastore in reverse date order.
        thumbnail_references = ThumbnailReference.query().order(
            -ThumbnailReference.date).fetch()
        # Build dictionary of img_url of thumbnail to thumbnail_references.
        thumbnails = collections.OrderedDict()
        for thumbnail_reference in thumbnail_references:
            img_url = get_thumbnail_serving_url(
                thumbnail_reference.thumbnail_key)
            thumbnails[img_url] = thumbnail_reference
        template_values = {'thumbnails': thumbnails}
        template = jinja_environment.get_template('photos.html')
        self.response.write(template.render(template_values))


class SearchHandler(webapp2.RequestHandler):
    """Search page: displays search bar and all
    thumbnails applicable to entered search term."""
    def get(self):
        # Get search_term entered by user.
        search_term = self.request.get('search-term').lower()
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
        template_values = {'thumbnails': thumbnails}
        template = jinja_environment.get_template('search.html')
        self.response.write(template.render(template_values))


class ReceiveMessage(webapp2.RequestHandler):
    """For receiving Cloud Pub/Sub push messages and performing
    related logic."""
    def post(self):
        logging.debug('Post body: {}'.format(self.request.body))
        message = json.loads(urllib.unquote(self.request.body))
        attributes = message['message']['attributes']

        # Acknowledge message.
        self.response.status = 204

        # Gather and save necessary values from the Pub/Sub message.
        event_type = attributes.get('eventType')
        photo_name = attributes.get('objectId')
        generation_number = str(attributes.get('objectGeneration'))
        overwrote_generation = attributes.get('overwroteGeneration')
        overwritten_by_generation = attributes.get(
            'overwrittenByGeneration')

        # Create the thumbnail_key using the photo_name and generation_number.
        # Note: Only photos with extension .jpg can be uploaded effectively.
        index = photo_name.index('.jpg')
        thumbnail_key = '{}{}{}'.format(
            photo_name[:index], generation_number, photo_name[index:])

        # Create the Notification using the received information.
        new_notification = create_notification(
            photo_name,
            event_type,
            generation_number,
            overwrote_generation=overwrote_generation,
            overwritten_by_generation=overwritten_by_generation)

        # If the new_notification already has been stored, it is a
        # repeat and can be ignored.
        exists_notification = Notification.query(
            Notification.message == new_notification.message,
            Notification.generation == new_notification.generation).get()

        if exists_notification:
            return

        # Don't act for metadata update events.
        if new_notification.message is None:
            return

        # Store new_notification in datastore.
        new_notification.put()

        # For create events: shrink the photo to thumbnail size,
        # store the thumbnail in GCS, and create a ThumbnailReference
        # and store it in Datastore.
        if event_type == 'OBJECT_FINALIZE':
            thumbnail = create_thumbnail(photo_name)
            store_thumbnail_in_gcs(thumbnail_key, thumbnail)
            original_photo = get_original_url(photo_name, generation_number)
            uri = 'gs://{}/{}'.format(PHOTO_BUCKET, photo_name)
            labels = get_labels(uri, photo_name)
            thumbnail_reference = ThumbnailReference(
                thumbnail_name=photo_name,
                thumbnail_key=thumbnail_key,
                labels=list(labels),
                original_photo=original_photo)
            thumbnail_reference.put()

        # For delete/archive events: delete the thumbnail from GCS
        # and delete the ThumbnailReference.
        elif event_type == 'OBJECT_DELETE' or event_type == 'OBJECT_ARCHIVE':
            delete_thumbnail(thumbnail_key)


# Create a Notification to be stored in Datastore.
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


# Returns serving url for a given thumbnail, specified
# by the photo_name parameter.
def get_thumbnail_serving_url(photo_name):
    filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, photo_name)
    blob_key = blobstore.create_gs_key(filename)
    return images.get_serving_url(blob_key)


# Returns the url of the original photo.
def get_original_url(photo_name, generation):
    original_photo = 'https://storage.googleapis.com/' \
        '{}/{}?generation={}'.format(
            PHOTO_BUCKET,
            photo_name,
            generation)
    return original_photo


# Shrinks specified photo to thumbnail size and returns resulting thumbnail.
def create_thumbnail(photo_name):
    filename = '/gs/{}/{}'.format(PHOTO_BUCKET, photo_name)
    image = images.Image(filename=filename)
    image.resize(width=180, height=200)
    return image.execute_transforms(output_encoding=images.JPEG)


# Stores thumbnail in GCS bucket under name thumbnail_key.
def store_thumbnail_in_gcs(thumbnail_key, thumbnail):
    write_retry_params = cloudstorage.RetryParams(
        backoff_factor=1.1,
        max_retry_period=15)
    filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
    with cloudstorage.open(
              filename, 'w', retry_params=write_retry_params) as filehandle:
        filehandle.write(thumbnail)


# Deletes thumbnail from GCS bucket and deletes thumbnail_reference from
# datastore.
def delete_thumbnail(thumbnail_key):
    filename = '/gs/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
    blob_key = blobstore.create_gs_key(filename)
    images.delete_serving_url(blob_key)
    thumbnail_reference = ThumbnailReference.query(
        ThumbnailReference.thumbnail_key == thumbnail_key).get()
    thumbnail_reference.key.delete()

    filename = '/{}/{}'.format(THUMBNAIL_BUCKET, thumbnail_key)
    cloudstorage.delete(filename)


# Use Cloud Vision API to get labels for a photo.
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


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/photos', PhotosHandler),
    ('/search', SearchHandler),
    ('/_ah/push-handlers/receive_message', ReceiveMessage)
], debug=True)
