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

from flask import Flask, request, jsonify
from cloudevents.http import from_http
from datetime import datetime
import google.auth
import json
from google.cloud import pubsub_v1 as pubsub
import base64
from google.api_core.exceptions import NotFound
import urllib.request
import urllib.parse
import re

credentials, project_id = google.auth.default()
pubsub_topic=os.getenv("OUTPUT_RECORDS_PUBSUB_TOPIC")
url_pattern=os.getenv("URL_PATTERN")

app = Flask(__name__)

def is_decimal(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        # execute if no exception
        return not float(n).is_integer()

def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        # execute if no exception
        return float(n).is_integer()

def getInBetweenString(stringToSearch, startString, endString):
    outputString=stringToSearch[stringToSearch.find(startString)+len(startString):]
    outputString=outputString[0:outputString.find(endString)].strip()
    return outputString

def getInBetweenStringAsInteger(stringToSearch, startString, endString):
    outputString=getInBetweenString(stringToSearch, startString, endString)
    if is_integer(outputString):
        return int(outputString)
    else:
        return 0

def process(input_record_string):

    input_record=json.loads(input_record_string)
    url = url_pattern.format(input_record["id"])

    # scrape
    utc_now_dt=datetime.utcnow()
    f = urllib.request.urlopen(url)
    html_source = f.read().decode('utf-8')

    # Parse returned HTML
    # print(html_source)

    output_record={}
    output_record["jobExecutionId"]=input_record["jobExecutionId"]
    output_record["scrapeDate"]=utc_now_dt.strftime('%Y-%m-%d')
    output_record["scrapeTimestamp"]=f"{utc_now_dt} UTC"

    output_record["skuId"]=input_record["id"]
    output_record["sellerCount"]=getInBetweenStringAsInteger(html_source,"sellerCount: ","<")
    output_record["mfgNumber"]=getInBetweenString(html_source,"mfgNumber: ","<")
    output_record["productTitle"]=getInBetweenString(html_source,"productTitle: ","<")
    output_record["bbWinner"]=getInBetweenString(html_source,"bbWinner: ","<")
    output_record["bbPrice"]=getInBetweenString(html_source,"bbPrice: ","<") # float
    output_record["shipCost"]=getInBetweenString(html_source,"shipCost: ","<") # float
    output_record["siteChoice"]=getInBetweenString(html_source,"siteChoice: ","<")
    output_record["fba"]=getInBetweenString(html_source,"fba: ","<")
    output_record["brand"]=getInBetweenString(html_source,"brand: ","<")
    output_record["productUrl"]=url
    output_record["productCustomerReviews"]=getInBetweenStringAsInteger(html_source,"productCustomerReviews: ","<")
    output_record["productStarRating"]=getInBetweenString(html_source,"productStarRating: ","<") # float
    output_record["productDimensions"]=getInBetweenString(html_source,"productDimensions: ","<")
    output_record["itemWeight"]=getInBetweenString(html_source,"itemWeight: ","<")
    output_record["shipWeight"]=getInBetweenString(html_source,"shipWeight: ","<")
    output_record["itemNumber"]=getInBetweenString(html_source,"itemNumber: ","<")
    output_record["skuCreationDate"]=getInBetweenString(html_source,"skuCreationDate: ","<")
    output_record["returnsPolicy"]=getInBetweenString(html_source,"returnsPolicy: ","<")
    output_record["currentlyUnavailable"]=getInBetweenString(html_source,"currentlyUnavailable: ","<")
    output_record["r1Number"]=getInBetweenStringAsInteger(html_source,"r1Number: ","<")
    output_record["r1Cat"]=getInBetweenString(html_source,"r1Cat: ","<")
    output_record["r2Number"]=getInBetweenStringAsInteger(html_source,"r2Number: ","<")
    output_record["r2Cat"]=getInBetweenString(html_source,"r2Cat: ","<")
    output_record["r3Number"]=getInBetweenStringAsInteger(html_source,"r3Number: ","<")
    output_record["r3Cat"]=getInBetweenString(html_source,"r3Cat: ","<")
    output_record["r4Number"]=getInBetweenStringAsInteger(html_source,"r4Number: ","<")
    output_record["r4Cat"]=getInBetweenString(html_source,"r4Cat: ","<")
    print(json.dumps(output_record))

    #PubSub
    client = pubsub.PublisherClient()
    topic_path = client.topic_path(project_id, pubsub_topic)
    try:
        # Encode the data according to the message serialization type.
        data_str = json.dumps(output_record)
        print(f"Preparing a JSON-encoded message:\n{data_str}")
        data = data_str.encode("utf-8")

        future = client.publish(topic_path, data)
        print(f"Published message ID: {future.result()}")

    except NotFound:
        print(f"{pubsub_topic} not found.")

    return

# This handles data coming from Eventarc
@app.route('/eventarc-handler', methods=['POST'])
def eventarc_handler():

    # create a CloudEvent
    event = from_http(request.headers, request.get_data())
    print(f"event={event}")
    #print(
        #f"Found {event['id']} from {event['source']} {event['subject']} with type "
        #f"{event['type']} and specversion {event['specversion']}"
    #)

    # Data access is handled via `.data` member
    record=base64.b64decode(event.data['message']['data']).decode('utf-8').strip()
    #print(f"Found {raw_record}")

    # process
    process(record)
    return (f"Processed", 200)

# This handles data coming from BigQuery Remote Functions
# "An endpoint with a custom domain, a URL query string or an additional URL path is not supported."
# So the default "/" has to be for BigQuery Remote Functions
@app.route('/', methods=['POST'])
@app.route('/bigquery-remote-functions-handler', methods=['POST'])
def bigquery_remote_functions_handler():

    return_value = []
    request_json = request.get_json()
    calls = request_json['calls']
    for call in calls:
        # expecting the entire first field to contain the json string representing the record
        process(call[0])
        return_value.append("Processed")
    return jsonify({"replies": return_value})

if __name__ == "__main__":
    # for local dev (listening on port 8080)
    if len(sys.argv) == 1:
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    # for local dev to simplify invoke the process function
    elif len(sys.argv) >= 2:
        process(sys.argv[1])
