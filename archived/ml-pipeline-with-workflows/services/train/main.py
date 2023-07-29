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

import os
import subprocess
import tempfile
import uuid
import googleapiclient

from google.api_core.client_options import ClientOptions
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from flask import Flask, request

app = Flask(__name__)


PROJECT_ID = os.getenv('PROJECT_ID')
GIT_REPO = os.getenv('GIT_REPO')
BRANCH = os.getenv('BRANCH') or 'master'
MODEL_PATH = os.getenv('MODEL_PATH')

@app.route('/')
def index():
    return 'A service to Submit a training job for the babyweight-keras example. '


@app.route('/api/v1/job/<string:job_id>', methods=['GET'])
def job_info(job_id):
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build(
        'ml', 'v1', credentials=credentials, cache_discovery=False)
    api_request = api.projects().jobs().get(
        name='projects/{}/jobs/{}'.format(PROJECT_ID, job_id))
    resp = None
    try:
        resp = api_request.execute()
    except googleapiclient.errors.HttpError as err:
        resp = {'message': err._get_reason()}
        return resp, 500

    return resp, 200


@app.route('/api/v1/train', methods=['POST'])
def train():
    json_data = request.get_json()

    scale_tier = 'BASIC_GPU'
    region = 'us-central1'
    runtime_version = '2.2'
    python_version = '3.7'
    data_dir = None
    job_dir = None
    num_train_examples = '60000000'
    num_eval_examples = '50000'
    num_evals = '100'
    learning_rate = '0.0001'

    for key in json_data.keys():
        if key == 'scaleTier':
            scale_tier = json_data[key]
        elif key == 'region':
            region = json_data[key]
        elif key == 'runtimeVersion':
            runtime_version = json_data[key]
        elif key == 'pythonVersion':
            python_version = json_data[key]
        elif key == 'dataDir':
            data_dir = json_data[key]
        elif key == 'jobDir':
            job_dir = json_data[key]
        elif key == 'numTrainExamples':
            num_train_examples = str(json_data[key])
        elif key == 'numEvalExamples':
            num_eval_examples = str(json_data[key])
        elif key == 'numEvals':
            num_evals = str(json_data[key])
        elif key == 'learningRate':
            learning_rate = str(json_data[key])

    if data_dir is None or job_dir is None:
        resp = {'message': 'Option dataDir or jobDir is not specified.'}
        return resp, 500

    with tempfile.TemporaryDirectory() as tmpdir:
        id_string = str(uuid.uuid4())
        job_id = 'train-babyweight-{}'.format(id_string).replace('-', '_')
        job_dir = os.path.join(job_dir, id_string)

        clone_cmd = 'cd {}; git init; git config core.sparsecheckout true;'\
                    'git remote add origin {};'\
                    'echo {} > .git/info/sparse-checkout;'\
                    'git pull origin {}'
        clone_cmd = clone_cmd.format(tmpdir, GIT_REPO, MODEL_PATH, BRANCH)
        subprocess.run(clone_cmd, shell=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        train_dir = os.path.join(tmpdir, MODEL_PATH)
        subprocess.run('cd {};python3 setup.py sdist'.format(train_dir),
                       shell=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        package_file = os.path.join(train_dir, 'dist', 'trainer-0.0.0.tar.gz')
        package = '{}/trainer-0.0.0.tar.gz'.format(job_dir)
        subprocess.run('gsutil cp {} {}'.format(package_file, package),
                       shell=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

        training_inputs = {
            'scaleTier': scale_tier,
            'packageUris': [package],
            'pythonModule': 'trainer.task',
            'region': region,
            'jobDir': job_dir,
            'runtimeVersion': runtime_version,
            'pythonVersion': python_version,
            'args': [
                '--data-dir', data_dir,
                '--num-train-examples', num_train_examples,
                '--num-eval-examples', num_eval_examples,
                '--num-evals', num_evals,
                '--learning-rate', learning_rate
            ]
        }
        job_spec = {'jobId': job_id, 'trainingInput': training_inputs}

        credentials = GoogleCredentials.get_application_default()
        api = discovery.build(
            'ml', 'v1', credentials=credentials, cache_discovery=False)
        api_request = api.projects().jobs().create(
            body=job_spec, parent='projects/{}'.format(PROJECT_ID))
        resp = None
        try:
            resp = api_request.execute()
        except googleapiclient.errors.HttpError as err:
            resp = {'message': err._get_reason()}
            return resp, 500

        return resp, 200


@app.route('/api/v1/deploy', methods=['POST'])
def deploy():
    # See: https://cloud.google.com/ai-platform/prediction/docs/regional-endpoints#python
    json_data = request.get_json()

    region = 'us-central1'
    runtime_version = '2.2'
    python_version = '3.7'
    deployment_uri = None
    model_name = 'babyweight'
    version_name = None

    for key in json_data.keys():
        if key == 'region':
            region = json_data[key]
        elif key == 'runtimeVersion':
            runtime_version = json_data[key]
        elif key == 'pythonVersion':
            python_version = json_data[key]
        elif key == 'deploymentUri':
            deployment_uri = json_data[key]
        elif key == 'modelName':
            model_name = json_data[key]
        elif key == 'versionName':
            version_name = json_data[key]

    if deployment_uri is None or version_name is None:
        resp = {'message': 'Option deploymentUri or versionName is not specified.'}
        return resp, 500

    if region == 'us-central1':
        endpoint = 'https://ml.googleapis.com'
    else:
        endpoint = 'https://{}-ml.googleapis.com'.format(region)

    client_options = ClientOptions(api_endpoint=endpoint)
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build('ml', 'v1', credentials=credentials,
                          cache_discovery=False,
                          client_options=client_options)

    api_request = api.projects().models().get(
        name='projects/{}/models/{}'.format(PROJECT_ID, model_name))
    try:
        resp = api_request.execute()
    except googleapiclient.errors.HttpError as err:
        # Create model
        request_body = {'name': model_name}
        api_request = api.projects().models().create(
            parent='projects/{}'.format(PROJECT_ID),
            body=request_body)
        api_request.execute()

    request_body = {'name': version_name,
                    'deploymentUri': deployment_uri,
                    'runtimeVersion': runtime_version,
                    'pythonVersion': python_version}

    api_request = api.projects().models().versions().create(
        parent='projects/{}/models/{}'.format(PROJECT_ID, model_name),
        body=request_body)

    try:
        resp = api_request.execute()
    except googleapiclient.errors.HttpError as err:
        resp = {'message': err._get_reason()}
        return resp, 500

    return resp, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
