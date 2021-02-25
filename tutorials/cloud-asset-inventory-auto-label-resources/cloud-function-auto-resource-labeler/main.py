"""
Copyright 2021 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from googleapiclient import discovery
import google.auth
import json
import base64
import re

# This is a Google Cloud Function which can:
# - Add the necessary labels to a VM

# Sample deployment command
# gcloud functions deploy create_notebook --runtime python38 --trigger-topic ${TOPIC_NAME} --service-account="${SERVICE_ACCOUNT}"

# Fine-grained Permissions needed
# - compute.instances.get
# - compute.instances.setLabels

def gce_vm_auto_labeler(event, context):

    # Get the project id.  
    credentials, project_id = google.auth.default()

    print("""This Function was triggered by messageId {} published at {} """.format(context.event_id, context.timestamp))

    try:
        # Decode the data with Base64
        message = base64.b64decode(event['data']).decode('utf-8')
        print({"message":message})

        # Convert the string to object
        message_object=json.loads(message)

        # Parse the minimal properties for branching
        asset_name=message_object["asset"]["name"] # "name": "//compute.googleapis.com/projects/pure-album-286220/zones/us-central1-a/instances/instance-4",
        asset_type=message_object["asset"]["assetType"] # "compute.googleapis.com/Instance"
        print('asset_name={}'.format(asset_name))
        print('asset_type={}'.format(asset_type))

        if "deleted" in message_object and message_object["deleted"]==True:
            # skip all the deletion (of any asset types)
            print("Ignored deleted resource. asset_type={} asset_name={}".format(asset_type,asset_name))
            pass

        # GCE VM
        elif asset_type == "compute.googleapis.com/Instance":

            # https://cloud.google.com/compute/docs/instances/instance-life-cycle
            asset_resource_data_status=message_object["asset"]["resource"]["data"]["status"] # "PROVISIONING"
            print('asset_resource_data_status={}'.format(asset_resource_data_status))

            # Process only when it is "PROVISIONING"
            if asset_resource_data_status == "PROVISIONING":

                # Parse the properties
                pattern = re.compile(r".*\/projects\/(?P<project_id>.*?)\/zones\/(?P<zone>.*?)\/instances\/(?P<instance_id>.*?)$", re.VERBOSE)
                match = pattern.match(asset_name)

                project_id = match.group("project_id")
                zone = match.group("zone")
                instance_id = match.group("instance_id")

                # Add the necessary labels to the compute instance
                compute_service=discovery.build('compute', 'v1')
                compute_get_response=compute_service.instances().get(
                    project=project_id,
                    zone=zone,
                    instance=instance_id
                ).execute()
                print({"compute_get_response":json.dumps(compute_get_response)})

                labelFingerprint=compute_get_response["labelFingerprint"]
                labels={}
                if "labels" in compute_get_response:
                    labels=compute_get_response["labels"]

                print("labelFingerprint={} labels={}".format(labelFingerprint,json.dumps(labels)))
                labels["gce_vm_name"]=instance_id

                compute_set_labels_response = compute_service.instances().setLabels(
                    project=project_id,
                    zone=zone,
                    instance=instance_id,
                    body={
                        "labels":labels,
                        "labelFingerprint":labelFingerprint
                    }
                ).execute()
                print({"compute_set_labels_response":compute_set_labels_response})

        else:
            print("Ignored asset_type={} asset_name={}".format(asset_type,asset_name))

        return 'Labeled resource {}'.format(asset_name)

    except RuntimeError:
        error_client.report_exception()
        raise

    return


if __name__ == "__main__":
    pass