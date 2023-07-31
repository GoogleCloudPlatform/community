# Copyright 2020 Google Inc.
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

import json
import os
import uuid

import apache_beam as beam
import googleapiclient

from flask import Flask, request
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import df_pipeline.pipe as pipe

app = Flask(__name__)


PROJECT_ID = os.getenv('PROJECT_ID') 


@app.route('/')
def index():
    return 'A service to Submit a training job for the babyweight-keras example. '


@app.route('/api/v1/job/<string:job_id>', methods=['GET'])
def job_info(job_id):
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build(
            'dataflow', 'v1b3', credentials=credentials, cache_discovery=False)
    request = api.projects().jobs().get(projectId=PROJECT_ID, jobId=job_id)
    resp = None
    try:
        resp = request.execute()
    except googleapiclient.errors.HttpError as err:
        resp = {'message': err._get_reason()}
        return resp, 500

    return resp, 200


@app.route('/api/v1/preprocess', methods=['POST'])
def preprocess():
    json_data = request.get_json()
    limit = None
    region = 'us-central1'
    output_dir = None

    for key in json_data.keys():
        if key == 'limit':
            if json_data[key] is not None:
                limit = str(json_data[key])
        elif key == 'region':
            region = json_data[key]
        elif key == 'outputDir':
            output_dir = json_data[key]

    if output_dir is None:
        resp = {'message': 'Option outputDir is not specified.'}
        return resp, 500

    id_string = str(uuid.uuid4())
    job_name = 'preprocess-babyweight-{}'.format(id_string)
    output_dir = '{}/{}'.format(output_dir, id_string)

    result = pipe.preprocess(limit, output_dir, job_name, region)

    resp = {'jobName': job_name,
            'jobId': result.job_id(),
            'outputDir': output_dir}

    return resp, 200


if __name__ == '__main__':
    app.run(debug=False, threaded=True,
            host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
