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

# This is a Google Cloud Function which can add the necessary labels to these resources.
# Fine-grained permissions needed are in parentheses.
# Compute Engine VMs - compute.instances.get,compute.instances.setLabels
# GKE Clusters - container.clusters.get,container.clusters.update
# Google Cloud Storage buckets - storage.buckets.get,storage.buckets.update
# Cloud SQL databases - cloudsql.instances.get,cloudsql.instances.update



# Sample deployment command
# gcloud functions deploy auto_resource_labeler --runtime python38 --trigger-topic ${TOPIC_NAME} --service-account="${SERVICE_ACCOUNT}" --project ${PROJECT_ID} --retry

from googleapiclient import discovery
from googleapiclient.errors import HttpError
import google.auth
import json
import base64
import re

COMPUTE_INSTANCE_LABEL_KEY="hostname"
CONTAINER_CLUSTER_LABEL_KEY="cluster"
STORAGE_BUCKET_LABEL_KEY="bucket"
SQLADMIN_INSTANCE_LABEL_KEY="instance"

# Label Compute Engine VMs
# https://cloud.google.com/compute/docs/instances/instance-life-cycle
def label_compute_instance(asset_name,asset_resource_data_status):

    # Process only when it is "PROVISIONING"
    if asset_resource_data_status == "PROVISIONING":
        label_key=COMPUTE_INSTANCE_LABEL_KEY

        # Here is a sample asset_name
        # "//compute.googleapis.com/projects/project-id-286220/zones/us-central1-a/instances/instance-4"

        # Extract the properties from the asset name
        pattern = re.compile(r".*\/projects\/(?P<project_id>.*?)\/zones\/(?P<zone>.*?)\/instances\/(?P<instance_id>.*?)$", re.VERBOSE)
        match = pattern.match(asset_name)

        project_id = match.group("project_id")
        zone = match.group("zone")
        instance_id = match.group("instance_id")

        # Retrieve the existing labels from the resource
        service=discovery.build('compute', 'v1')
        service_get_response={}
        try:
            service_get_response=service.instances().get(
                project=project_id,
                zone=zone,
                instance=instance_id
            ).execute()
            print({"service_get_response":json.dumps(service_get_response)})
        except HttpError as exception:
            if exception.resp["status"] == "404":
                # exit gracefully if encountering 404
                # One reason is due to the Compute Engine VMs created by GKE Autopilot clusters, 
                # which generate Compute Engine Instance notifications but are not available via computer API
                print("Cannot find asset_name={} . Exiting gracefully.".format(asset_name))
                return
            else:
                raise exception


        labelFingerprint=service_get_response["labelFingerprint"]
        labels={}
        if "labels" in service_get_response:
            labels=service_get_response["labels"]

        print("Current labelFingerprint={} labels={}".format(labelFingerprint,json.dumps(labels)))

        if label_key in labels and labels[label_key] == instance_id:
            print("The same label key-value already exists.")
        else:
            # Use the instance_id as the label value
            labels[label_key]=instance_id

            service_set_labels_response = service.instances().setLabels(
                project=project_id,
                zone=zone,
                instance=instance_id,
                body={
                    "labels":labels,
                    "labelFingerprint":labelFingerprint
                }
            ).execute()
            print("Finished setting labels on {}".format(instance_id))
            print({"service_set_labels_response":service_set_labels_response})


# Label GKE Clusters
# https://cloud.google.com/kubernetes-engine/docs/how-to/creating-managing-labels
# Labeling is not allowed while the cluster is being created
def label_container_cluster(asset_name,asset_resource_data_status):
    # Process when it is "RUNNING"
    if asset_resource_data_status == "RUNNING":
        label_key=CONTAINER_CLUSTER_LABEL_KEY

        # Here is a sample asset_name
        # "//container.googleapis.com/projects/project-id-305922/locations/us-central1/clusters/autopilot-cluster-1"

        # Replace /zones/ with /locations/ for further processing
        harmonized_asset_name=asset_name.replace("/zones/","/locations/")

        # Extract the properties from the asset name
        pattern = re.compile(r".*\/clusters\/(?P<cluster>.*?)$", re.VERBOSE)
        match = pattern.match(harmonized_asset_name)

        cluster = match.group("cluster")

        # Extract the full name for the API request
        pattern = re.compile(r"^\/\/container.googleapis.com\/(?P<name>.*)$", re.VERBOSE)
        match = pattern.match(harmonized_asset_name)

        name = match.group("name")

        # Add the necessary labels to the resource
        service=discovery.build('container', 'v1')
        service_get_response={}
        try:
            service_get_response=service.projects().locations().clusters().get(
                name=name,
            ).execute()
            print({"service_get_response":json.dumps(service_get_response)})
        except HttpError as exception:
            if exception.resp["status"] == "404":
                # exit gracefully if encountering 404
                # One reason is due to the Compute Engine VMs created by GKE Autopilot clusters, 
                # which generate Compute Engine Instance notifications but are not available via computer API
                print("Cannot find name={} . Exiting gracefully.".format(name))
                return
            else:
                raise exception

        labelFingerprint=service_get_response["labelFingerprint"]
        labels={}
        if "resourceLabels" in service_get_response:
            labels=service_get_response["resourceLabels"]

        print("Current labelFingerprint={} resourceLabels={}".format(labelFingerprint,json.dumps(labels)))

        if label_key in labels and labels[label_key] == cluster:
            print("The same label key-value already exists.")
        else:
            labels[label_key]=cluster

            service_set_labels_response = service.projects().locations().clusters().setResourceLabels(
                name=name,
                body={
                    "resourceLabels":labels,
                    "labelFingerprint":labelFingerprint
                }
            ).execute()
            print("Finished setting labels on {}".format(cluster))
            print({"service_set_labels_response":service_set_labels_response})


# Label Cloud Storage buckets
# https://cloud.google.com/storage/docs/using-bucket-labels
def label_storage_bucket(asset_name):
    label_key=STORAGE_BUCKET_LABEL_KEY

    # Here is a sample asset_name
    # "//storage.googleapis.com/project-id-305922-gcs"

    # Extract the full name for the API request
    pattern = re.compile(r"^\/\/storage.googleapis.com\/(?P<bucket>.*)$", re.VERBOSE)
    match = pattern.match(asset_name)

    bucket = match.group("bucket")

    # Add the necessary labels to the resource
    service=discovery.build('storage', 'v1')
    service_get_response={}
    try:
        service_get_response=service.buckets().get(
            bucket=bucket,
        ).execute()
        print({"service_get_response":json.dumps(service_get_response)})
    except HttpError as exception:
        if exception.resp["status"] == "404":
            # exit gracefully if encountering 404
            # One reason is due to the Compute Engine VMs created by GKE Autopilot clusters, 
            # which generate Compute Engine Instance notifications but are not available via computer API
            print("Cannot find bucket={} . Exiting gracefully.".format(bucket))
            return
        else:
            raise exception

    etag=service_get_response["etag"]
    labels={}
    if "labels" in service_get_response:
        labels=service_get_response["labels"]

    print("Current etag={} labels={}".format(etag,json.dumps(labels)))

    if label_key in labels and labels[label_key] == bucket:
        print("The same label key-value already exists.")
    else:
        labels[label_key]=bucket
        service_set_labels_response = service.buckets().patch(
            bucket=bucket,
            body={
                "labels":labels
            }
        ).execute()
        print("Finished setting labels on {}".format(bucket))
        print({"service_set_labels_response":service_set_labels_response})


# Label Cloud SQL instance
# https://cloud.google.com/sql/docs/sqlserver/label-instance
def label_sqladmin_instance(asset_name,asset_resource_data_state):

    if asset_resource_data_state == "RUNNABLE":
        label_key=SQLADMIN_INSTANCE_LABEL_KEY

        # Here is a sample asset_name
        # "//cloudsql.googleapis.com/projects/project-id-305922/instances/test3"

        # Extract the properties from the asset name
        pattern = re.compile(r".*\/projects\/(?P<project_id>.*?)\/instances\/(?P<instance_id>.*?)$", re.VERBOSE)
        match = pattern.match(asset_name)

        project_id = match.group("project_id")
        instance_id = match.group("instance_id")

        # Retrieve the existing labels from the resource
        service=discovery.build('sqladmin', 'v1beta4')
        service_get_response={}
        try:
            service_get_response=service.instances().get(
                project=project_id,
                instance=instance_id
            ).execute()
            print({"service_get_response":json.dumps(service_get_response)})
        except HttpError as exception:
            if exception.resp["status"] == "404":
                # exit gracefully if encountering 404
                # One reason is due to the Compute Engine VMs created by GKE Autopilot clusters, 
                # which generate Compute Engine Instance notifications but are not available via computer API
                print("Cannot find asset_name={} . Exiting gracefully.".format(asset_name))
                return
            else:
                raise exception


        etag=service_get_response["etag"]
        userLabels={}
        if "settings" in service_get_response and "userLabels" in service_get_response["settings"]:
            userLabels=service_get_response["settings"]["userLabels"]

        print("Current etag={} userLabels={}".format(etag,json.dumps(userLabels)))

        if label_key in userLabels and userLabels[label_key] == instance_id:
            print("The same label key-value already exists.")
        else:
            userLabels[label_key]=instance_id
            service_set_labels_response = service.instances().patch(
                project=project_id,
                instance=instance_id,
                body={
                    "settings":{
                        "userLabels":userLabels
                    }
                }
            ).execute()
            print("Finished setting labels on {}".format(asset_name))
            print({"service_set_labels_response":service_set_labels_response})

def auto_resource_labeler(event, context):

    # Get the project id.  
    credentials, project_id = google.auth.default()

    print("""This Function was triggered by messageId {} published at {} """.format(context.event_id, context.timestamp))

    try:
        # Decode the data with Base64
        message = base64.b64decode(event['data']).decode('utf-8')
        print({"message":message})

        # Convert the string to object
        message_object=json.loads(message)

        # Parse the minimal properties for branching of the labeling logic
        asset_name=message_object["asset"]["name"]
        asset_type=message_object["asset"]["assetType"]

        # skip all the deletion notifications (of any asset types)
        if "deleted" in message_object and message_object["deleted"]==True:
            print("Ignored deleted resource. asset_type={} asset_name={}".format(asset_type,asset_name))
            pass

        # else (not deleted)
        else:
            print("Got notification on asset_type={} asset_name={}".format(asset_type,asset_name))

            # Handle the various supported asset types
            if asset_type == "compute.googleapis.com/Instance":
                # get the status of the resource
                asset_resource_data_status=message_object["asset"]["resource"]["data"]["status"] 
                print("asset_resource_data_status={}".format(asset_resource_data_status))
                label_compute_instance(asset_name,asset_resource_data_status)
            elif asset_type == "container.googleapis.com/Cluster":
                # get the status of the resource
                asset_resource_data_status=message_object["asset"]["resource"]["data"]["status"] 
                print("asset_resource_data_status={}".format(asset_resource_data_status))
                label_container_cluster(asset_name,asset_resource_data_status)
            elif asset_type == "storage.googleapis.com/Bucket":
                if "priorAssetState" in message_object and message_object["priorAssetState"]=="DOES_NOT_EXIST":
                    label_storage_bucket(asset_name)
                else:
                    print("Ignored asset_type={} asset_name={}".format(asset_type,asset_name))
            elif asset_type == "sqladmin.googleapis.com/Instance":
                # get the state of the resource
                asset_resource_data_state=message_object["asset"]["resource"]["data"]["state"] 
                print("asset_resource_data_state={}".format(asset_resource_data_state))
                label_sqladmin_instance(asset_name,asset_resource_data_state)
            else:
                print("Ignored asset_type={} asset_name={}".format(asset_type,asset_name))

        return 'Labeled resource {}'.format(asset_name)

    except RuntimeError:
        error_client.report_exception()
        raise

    return


if __name__ == "__main__":
    pass
