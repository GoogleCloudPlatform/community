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
import time

credentials, project_id = google.auth.default()

app = Flask(__name__)

# https://github.com/googleapis/python-bigquery/blob/HEAD/samples/load_table_uri_json.py
def process(record_json_string):
    

    return


@app.route('/', methods=['POST'])
def index():
    # the data is expected to be coming from BigQuery Remote Functions
    # it is a JSON payload with values inside calls[]

    return_value = []
    request_json = request.get_json()
    calls = request_json['calls']
    print(f'Number of records received={len(calls)}')
    for call in calls:
        #print(call)
        return_value.append("Processed")
    return jsonify({"replies": return_value})


if __name__ == "__main__":
    if len(sys.argv) == 1:
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    elif len(sys.argv) >= 2:
        process(record_json_string=sys.argv[1])
