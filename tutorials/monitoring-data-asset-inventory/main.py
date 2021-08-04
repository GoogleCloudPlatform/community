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
import time
import collections
from flask import Flask, request
from google.cloud import monitoring_v3
from google.cloud import asset_v1

# The scope cloud be project, folder, or organization
SCOPE_ID = os.getenv("SCOPE_ID")
CUSTOM_METRIC_NAME = "database_assets"

monitoring_client = monitoring_v3.MetricServiceClient()
asset_client = asset_v1.AssetServiceClient()

app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    # Supported asset types:
    # https://cloud.google.com/asset-inventory/docs/supported-asset-types
    asset_types = [
        "sqladmin.googleapis.com/Instance"
    ]
    # Num of assets in one page, which must be between 1 and
    # 1000 (both inclusively)'
    page_size = 100
    data_assets = list_assets(asset_types, page_size)
    send_metric(data_assets)

    return "OK", 200


def list_assets(asset_types, page_size):
    assets = []
    content_type = asset_v1.ContentType.RESOURCE
    asset_client = asset_v1.AssetServiceClient()

    # Call ListAssets v1 to list assets.
    response = asset_client.list_assets(
        request={
            "parent": SCOPE_ID,
            "read_time": None,
            "asset_types": asset_types,
            "content_type": content_type,
            "page_size": page_size,
        }
    )

    for asset in response:
        asset_data = collections.OrderedDict()
        asset_data["location"] = asset.resource.location
        data = asset.resource.data
        asset_data["project"] = data.get("project")
        asset_data["database_version"] = data.get("databaseVersion")
        asset_data["database"] = data.get("databaseVersion").split("_")[0]
        asset_data["state"] = data.get("state")

        assets.append(asset_data)

    return assets


def send_metric(asset_list):
    out_metrics = {}
    data_point_num = 0

    for da in asset_list:
        value = "/".join(da.values())
        if value not in out_metrics:
            out_metrics[value] = 1
        else:
            out_metrics[value] += 1

    epoch = time.time()
    seconds = int(epoch)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": 0}}
    )

    for da in asset_list:
        value = "/".join(da.values())
        if out_metrics[value] > 0:
            proj_id = da["project"]

            # We write the individual metric to its own project
            # So the metric could be viewed in multiple scoping projects
            project_name = f"projects/{proj_id}"

            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{CUSTOM_METRIC_NAME}"
            # Available resource types: https://cloud.google.com/monitoring/api/resources
            series.resource.type = "global"
            series.resource.labels["project_id"] = proj_id

            # If needed, add more labels for filtering and grouping
            for k, v in da.items():
                series.metric.labels[k] = v

            point = monitoring_v3.Point(
                {"interval": interval, "value": {"int64_value": out_metrics[value]}})
            series.points = [point]

            try:
                monitoring_client.create_time_series(
                    request={"name": project_name, "time_series": [series]})
            except Exception as exp:
                print(exp)
            else:
                data_point_num += 1
                out_metrics[value] = 0

    print(f"Successfully wrote {data_point_num} time series.")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
