# Copyright 2021 Google, LLC.
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

import os
import json
import uuid
import time
import random
from flask import Flask, request
from google.cloud import monitoring_v3
from google.api import label_pb2 as ga_label
from google.api import metric_pb2 as ga_metric
from google.cloud import bigquery


PROJECT_ID = os.getenv('PROJECT_ID')
CUSTOM_METRIC_NAME = os.getenv('METRIC_NAME')
SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL')  # in seconds
BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET')
BIGQUERY_TABLE = os.getenv('BIGQUERY_TABLE')


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    client = bigquery.Client()

    # The bigquery_schema.json file has the BigQuery schema. Adjust the query as needed.
    # Keep in mind that there can only be one data point for each time series.
    # You cannot add time series older than existing ones in Cloud Monitoring.
    # For this particular query, we grab all rows in the last time interval, in
    # ascending order
    query_job = client.query(
        f"""
        SELECT *
        FROM `{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
        WHERE report_time >
        TIMESTAMP_SUB(CURRENT_TIMESTAMP(),INTERVAL {SCHEDULE_INTERVAL} SECOND)
        ORDER BY report_time ASC"""
    )
    results = query_job.result()  # Waits for job to complete

    for row in results:
        print("{} : {} report time: {}".format(
            row.item_id, row.item_sold, row.report_time))
        try:
            send_metric(row.item_id, row.item_sold, row.report_time)
        except Exception as ex:
            # Keep going if we can't write the current data point
            print(f"Excepitons....{ex}")

    return "OK", 200


def send_metric(sales_item, sales_num, report_time):
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{CUSTOM_METRIC_NAME}"
    # Available resource types: https://cloud.google.com/monitoring/api/resources
    series.resource.type = "global"
    series.resource.labels["project_id"] = PROJECT_ID

    # If needed, add more labels for filtering and grouping
    series.metric.labels["item"] = sales_item

    epoch = report_time.timestamp()
    seconds = int(epoch)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": 0}}
    )
    point = monitoring_v3.Point(
        {"interval": interval, "value": {"int64_value": sales_num}})
    series.points = [point]
    client.create_time_series(
        request={"name": project_name, "time_series": [series]})

    print("Successfully wrote time series.")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
