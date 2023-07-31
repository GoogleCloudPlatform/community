""" Copyright 2018, Google, Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless  required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import base64
import os
import json

from google.cloud import dlp_v2

# Instantiate a client.
dlp = dlp_v2.DlpServiceClient()

def job_complete(data, context):
    """Triggered when a DLP job is complete and published a message to a PubSub topic the function listens to.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    #pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    #print(pubsub_message)
    #data=json.loads(pubsub_message)
    
    job_name = data['attributes']['DlpJobName']
    print('Received pub/sub notification from DLP job: {}'.format(job_name))
    
    # Get the DLP job details by the job_name
    job = dlp.get_dlp_job(request={"name": job_name})
    print('Job Name:{name}\nStatus:{status}'.format(name=job.name, status=job.state))
    if len(job.inspect_details.result.info_type_stats)>0:
         print('Inspection Details: {}'.format(job.inspect_details.result.info_type_stats))

def job_request(data, context):
    """Triggered when a job is submitted to a PubSub topci the function listens to
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(data['data']).decode('utf-8')
    print('pubsub_message: {}'.format(pubsub_message))
    payload=json.loads(pubsub_message)
    print ('payload: {}'.format(payload))
    # Convert the project id into a full resource id.
    project_id = payload['ProjectID']
    info_types = payload['InfoTypes']
    dataset_id = payload['DataSetID']
    table_id = payload['TableID']
    pubsub_topic = payload['PubSubTopic']

    parent = f"projects/{project_id}"
    
    # Construct the configuration dictionary.
    inspect_config = {
        'inspect_config': {
            'info_types': info_types,
            'min_likelihood': dlp_v2.Likelihood.POSSIBLE,
            'limits': {
                'max_findings_per_request': 0
            },
        },
        'storage_config': {
            'big_query_options': {
                'table_reference': {
                    'project_id': project_id,
                    'dataset_id': dataset_id,
                    'table_id': table_id
                }
            }
        },
        'actions': [{
            'pub_sub': {
                'topic': 'projects/{project_id}/topics/{topic_id}'.format(project_id=project_id, topic_id=pubsub_topic)
            }
        }]
    }
    print('JOB CONFIG: {}'.format(inspect_config))
    dlp.create_dlp_job(request={"parent": parent, "inspect_job": inspect_config})