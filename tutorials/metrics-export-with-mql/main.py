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

import logging
import io
import json
import base64
import re
import config
import requests
import subprocess

from datetime import datetime
from google.cloud import bigquery

token = None
DISTRIBUTION = "DISTRIBUTION"

METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/"
METADATA_HEADERS = {"Metadata-Flavor": "Google"}
SERVICE_ACCOUNT = "default"


def get_access_token_from_meta_data():
    url = '{}instance/service-accounts/{}/token'.format(
        METADATA_URL, SERVICE_ACCOUNT)

    # Request an access token from the metadata server.
    r = requests.get(url, headers=METADATA_HEADERS)
    r.raise_for_status()

    # Extract the access token from the response.
    token = r.json()['access_token']
    return token


def get_access_token_from_gcloud(force=False):
    global token
    if token is None or force:
        token = subprocess.check_output(
            ["/usr/bin/gcloud", "auth", "application-default", "print-access-token"],
            text=True,
        ).rstrip()
    return token


def get_mql_result(token, query, pageToken):
    q = f'{{"query":"{query}", "pageToken":"{pageToken}"}}' if pageToken else f'{{"query": "{query}"}}'

    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {token}"}
    return requests.post(config.QUERY_URL, data=q, headers=headers).json()


def build_rows(metric, data):
    """ Build a list of JSON object rows to insert into BigQuery
        This function may fan out the input by writing 1 entry into BigQuery for every point,
        if there is more than 1 point in the timeseries
    """
    logging.debug("build_row")
    rows = []

    labelDescriptors = data["timeSeriesDescriptor"]["labelDescriptors"]
    pointDescriptors = data["timeSeriesDescriptor"]["pointDescriptors"]

    for timeseries in data["timeSeriesData"]:
        labelValues = timeseries["labelValues"]
        pointData = timeseries["pointData"]

        # handle >= 1 points, potentially > 1 returned from Monitoring API call
        for point_idx in range(len(pointData)):
            labels = []
            for i in range(len(labelDescriptors)):
                for v1 in labelDescriptors[i].values():
                    labels.append(
                        {"key": v1, "value": ""})
            for i in range(len(labelValues)):
                for v2 in labelValues[i].values():
                    if type(v2) is bool:
                        labels[i]["value"] = str(v2)
                    else:
                        labels[i]["value"] = v2

            point_descriptors = []
            for j in range(len(pointDescriptors)):
                for k, v in pointDescriptors[j].items():
                    point_descriptors.append({"key": k, "value": v})

            row = {
                "timeSeriesDescriptor": {
                    "pointDescriptors": point_descriptors,
                    "labels": labels,
                }
            }

            interval = {
                "start_time": pointData[point_idx]["timeInterval"]["startTime"],
                "end_time": pointData[point_idx]["timeInterval"]["endTime"]
            }

            # map the API value types to the BigQuery value types
            value_type = pointDescriptors[0]["valueType"]
            bigquery_value_type_index = config.BQ_VALUE_MAP[value_type]
            api_value_type_index = config.API_VALUE_MAP[value_type]
            value_type_label = {}

            value = timeseries["pointData"][point_idx]["values"][0][api_value_type_index]

            if value_type == DISTRIBUTION:
                value_type_label[bigquery_value_type_index] = build_distribution_value(
                    value)
            else:
                value_type_label[bigquery_value_type_index] = value

            point = {
                "timeInterval": interval,
                "values": value_type_label
            }
            row["pointData"] = point
            row["metricName"] = metric
            rows.append(row)

    return rows


def build_distribution_value(value_json):
    """ Build a distribution value based on the API spec below
        See https://cloud.google.com/monitoring/api/ref_v3/rest/v3/TimeSeries#Distribution
    """
    distribution_value = {}
    if "count" in value_json:
        distribution_value["count"] = int(value_json["count"])
    if "mean" in value_json:
        distribution_value["mean"] = round(value_json["mean"], 2)
    if "sumOfSquaredDeviation" in value_json:
        distribution_value["sumOfSquaredDeviation"] = round(
            value_json["sumOfSquaredDeviation"], 2)

    if "range" in value_json:
        distribution_value_range = {}
        distribution_value_range["min"] = value_json["range"]["min"]
        distribution_value_range["max"] = value_json["range"]["max"]
        distribution_value["range"] = distribution_value_range

    bucketOptions = {}
    if "linearBuckets" in value_json["bucketOptions"]:
        linearBuckets = {
            "numFiniteBuckets": value_json["bucketOptions"]["linearBuckets"]["numFiniteBuckets"],
            "width": value_json["bucketOptions"]["linearBuckets"]["width"],
            "offset": value_json["bucketOptions"]["linearBuckets"]["offset"]
        }
        bucketOptions["linearBuckets"] = linearBuckets
    elif "exponentialBuckets" in value_json["bucketOptions"]:
        exponentialBuckets = {
            "numFiniteBuckets": value_json["bucketOptions"]["exponentialBuckets"]["numFiniteBuckets"],
            "growthFactor": round(value_json["bucketOptions"]["exponentialBuckets"]["growthFactor"], 2),
            "scale": value_json["bucketOptions"]["exponentialBuckets"]["scale"]
        }
        bucketOptions["exponentialBuckets"] = exponentialBuckets
    elif "explicitBuckets" in value_json["bucketOptions"]:
        explicitBuckets = {
            "bounds": {
                "value": value_json["bucketOptions"]["explicitBuckets"]["bounds"]
            }

        }
        bucketOptions["explicitBuckets"] = explicitBuckets
    if bucketOptions:
        distribution_value["bucketOptions"] = bucketOptions

    if "bucketCounts" in value_json:
        bucketCounts = {}
        bucket_count_list = []
        for bucket_count_val in value_json["bucketCounts"]:
            bucket_count_list.append(int(bucket_count_val))
        bucketCounts["value"] = bucket_count_list
        distribution_value["bucketCounts"] = bucketCounts

    if "exemplars" in value_json:
        exemplars_list = []
        for exemplar in value_json["exemplars"]:
            exemplar = {
                "value": exemplar["value"],
                "timestamp": exemplar["timestamp"]
            }
            exemplars_list.append(exemplar)
        distribution_value["exemplars"] = exemplars_list

    logging.debug("created the distribution_value: {}".format(
        json.dumps(distribution_value, sort_keys=True, indent=4)))
    return distribution_value


def write_to_bigquery(rows_to_insert):
    """ Write rows to the BigQuery stats table using the BigQuer client
    """
    logging.debug("write_to_bigquery")
    client = bigquery.Client()

    table_id = f'{config.PROJECT_ID}.{config.BIGQUERY_DATASET}.{config.BIGQUERY_TABLE}'
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))

def save_to_bq(token):
    for metric, query in config.MQL_QUERYS.items():
        pageToken = ""
        while (True):
            result = get_mql_result(token, query, pageToken)
            if result.get("timeSeriesDescriptor"):
                row = build_rows(metric, result)
                write_to_bigquery(row)
            pageToken = result.get("nextPageToken")
            if not pageToken:
                print("No more data retrieved")
                break

def export_metric_data(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """
    print("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))
    
    token = get_access_token_from_meta_data()
    save_to_bq(token)


if __name__ == "__main__":
    token = get_access_token_from_gcloud()
    save_to_bq(token)
