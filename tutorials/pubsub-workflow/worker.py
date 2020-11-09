#!/usr/bin/env python

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import argparse
import redis
import json
import uuid
from google.cloud import pubsub_v1
from google.cloud import storage

# load in configuration
config = json.load(open('config', 'r'))
# set logging level
logging.basicConfig(level=logging.INFO)
# generate worker ID
worker_id = uuid.uuid4().hex

# establish a connection to Redis
r = redis.Redis(host=config['redis_host'],port=config['redis_port'])
# establish a client for Storage interactions
gcs = storage.Client()

# returns 
#   True if work successfully claimed by this worker
#   False if work was already claimed by another worker
def claim_work(work_id, worker_id):
    # available will be None if that key already set
    available = r.set(work_id, worker_id, nx=True)
    return available==True

# source https://github.com/googleapis/python-pubsub/blob/master/samples/snippets/quickstart/sub.py
def process_work(project_id, subscription_id, workdir):
    """Receives messages from a Pub/Sub subscription."""
    # Initialize a Subscriber/Publisher clients
    available_subscriber = pubsub_v1.SubscriberClient()
    publisher = pubsub_v1.PublisherClient()
    # Create a fully qualified identifiers in the form of
    # `projects/{project_id}/[subscriptions|topics]/{subscription_id}`
    available_subscription_path = available_subscriber.subscription_path(project_id, subscription_id)
    processing_topic = publisher.topic_path(project_id, config['processing_topic'])
    complete_topic = publisher.topic_path(project_id, config['complete_topic'])

    def callback(message):
        # Acknowledge the message. Unack'ed messages will be redelivered.
        message.ack()
        logging.info("ACK_ID: {}".format(message.ack_id))

        # claim work
        if claim_work(message.message_id, worker_id):
            logging.info("Successfully claimed message with ID: {}".format(message.message_id))
            
            # publish processing msg
            processing_msg = {"original_message_id": message.message_id, "worker_id": worker_id}
            publisher.publish(processing_topic, json.dumps(processing_msg).encode('utf-8'), original_message_id=message.message_id, worker_id=worker_id)
            logging.info("Published processing message")

            # do work
            # grab the file
            workfile = os.path.join(workdir, message.attributes['objectId'])
            workbucket = gcs.bucket(message.attributes['bucketId'])
            workfilegcs = workbucket.blob(message.attributes['objectId'])
            workfilegcs.download_to_filename(workfile)
            logging.info("Successfully downloaded file {} from bucket {}".format(workfile, message.attributes['bucketId']))
            
            # modify the file
            with open(workfile, 'r+') as workfilelocal:
                contents = workfilelocal.read()
                workfilelocal.seek(0)
                workfilelocal.write(contents.replace('SVN', 'GIT'))
                logging.info("Replaced {} instances of SVN with GIT for file {}".format(contents.count("SVN"), message.attributes['objectId']))

            # save the modified file
            processedbucket = gcs.bucket(config['processed_bucket'])
            newfilename = "{}.processed".format(message.attributes['objectId'])
            processedfilegcs = processedbucket.blob(newfilename)
            processedfilegcs.upload_from_filename(workfile)
            logging.info("Successfully uploaded file {} from bucket {}".format(newfilename, config['processed_bucket']))

            os.remove(workfile)

            # publish processing msg
            complete_msg = {"original_message_id": message.message_id, "worker_id": worker_id}
            publisher.publish(complete_topic, json.dumps(complete_msg).encode('utf-8'), original_message_id=message.message_id, worker_id=worker_id)
            logging.info("Published complete message")

    streaming_pull_future = available_subscriber.subscribe(
        available_subscription_path, callback=callback
    )
    logging.info("Listening for messages on {}..\n".format(available_subscription_path))

    try:
        # Calling result() on StreamingPullFuture keeps the main thread from
        # exiting while messages get processed in the callbacks.
        streaming_pull_future.result()
    except:  # noqa
        streaming_pull_future.cancel()

    available_subscriber.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_id", help="Google Cloud project ID")
    parser.add_argument("subscription_id", help="Pub/Sub subscription ID")
    parser.add_argument("workdir", help="Directory where files are downloaded and modified", nargs='?', default="tmpwork")

    args = parser.parse_args()
    
    if not os._exists(args.workdir):
        os.makedirs(args.workdir)
    process_work(args.project_id, args.subscription_id, args.workdir)
    os.rmdir(args.workdir)