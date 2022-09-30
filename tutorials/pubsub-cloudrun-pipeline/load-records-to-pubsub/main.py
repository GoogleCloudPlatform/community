# Copyright 2020 Google, LLC.
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

import os, sys

from flask import Flask, request
from cloudevents.http import from_http
from datetime import datetime
from google.cloud.storage import Client
import google.auth
from concurrent import futures
from google.cloud import pubsub_v1
import time

credentials, project_id = google.auth.default()
pubsub_topic=os.getenv("INPUT_RECORDS_PUBSUB_TOPIC")
PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS=float(os.getenv("PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS"))

app = Flask(__name__)

# https://cloud.google.com/pubsub/docs/publisher#batching
batch_settings = pubsub_v1.types.BatchSettings()
# batch_settings = pubsub_v1.types.BatchSettings(
#     max_messages=10,  # default 100
#     max_bytes=1024,  # default 1 MB
#     max_latency=1,  # default 10 ms
# )

# https://github.com/googleapis/python-bigquery/blob/HEAD/samples/load_table_uri_json.py
def process(bucket_name,object_path):
    publisher = pubsub_v1.PublisherClient(batch_settings)
    topic_path = publisher.topic_path(project_id, pubsub_topic)
    publish_futures = []

    print(f"bucket_name={bucket_name}")
    print(f"object_path={object_path}")
    client = Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(object_path)
    downloaded_file = blob.download_as_text(encoding="utf-8")
    #print(downloaded_file)

    # Resolve the publish future in a separate thread.
    def callback(future: pubsub_v1.publisher.futures.Future) -> None:
        message_id = future.result()
        #print(message_id)

    for line in downloaded_file.splitlines():
        #print(line)
        # Data must be a bytestring
        data = line.encode("utf-8")
        publish_future = publisher.publish(topic_path, data)
        # Non-blocking. Allow the publisher client to batch multiple messages.
        publish_future.add_done_callback(callback)
        publish_futures.append(publish_future)
        # TODO rate limiting
        time.sleep(PUBLISHING_SLEEP_TIME_BETWEEN_RECORDS)

    futures.wait(publish_futures, return_when=futures.ALL_COMPLETED)

    print(f"Published messages with batch settings to {topic_path}.")

    return


@app.route('/', methods=['POST'])
def index():

    # create a CloudEvent
    event = from_http(request.headers, request.get_data())
    print(
        f"Found {event['id']} from {event['source']} {event['subject']} with type "
        f"{event['type']} and specversion {event['specversion']}"
    )

    # construct the GCS object path
    bucket_name=event['source'].rsplit('/', 1)[1]
    object_path=event['subject'].split('/',1)[1]
    full_object_path=f"gs://{bucket_name}/{object_path}"
    print(f"bucket_name {bucket_name}")
    print(f"object_path {object_path}")
    print(f"full_object_path {full_object_path}")
    process(bucket_name=bucket_name,object_path=object_path)

    return (f"Detected change in Cloud Storage object: {object_path}", 200)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    elif len(sys.argv) >= 2:
        process(bucket_name=sys.argv[1],object_path=sys.argv[2])
