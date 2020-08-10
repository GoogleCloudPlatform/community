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

import os
from google.protobuf.duration_pb2 import Duration

METRIC_NAME = 'integ-test-metric'
METRIC_PATH = f'custom.googleapis.com/{METRIC_NAME}'
RESOURCE_TYPE = 'gce_instance'
INSTANCE_ID = '1234567890123456789'
ZONE = 'us-central1-f'
ALERT_POLICY_NAME = 'integ-test-policy'
TRIGGER_NOTIFICATION_THRESHOLD_DOUBLE = 3.0
PROJECT_ID = os.environ['PROJECT_ID']

TEST_METRIC_DESCRIPTOR = {
    'type': f'custom.googleapis.com/{METRIC_NAME}',
    'metric_kind': 'GAUGE',
    'value_type': 'DOUBLE',
    'description': 'A custom metric meant for testing purposes'
}

TEST_NOTIFICATION_CHANNEL = {
    'type': 'pubsub',
    'display_name': 'test channel',
    'description': 'A Pub/Sub channel meant for testing purposes',
    'labels': {
        'topic': f'projects/{PROJECT_ID}/topics/tf-topic'
    }
}

TEST_ALERT_POLICY_TEMPLATE = {
    'display_name': ALERT_POLICY_NAME,
    'user_labels': {'type': 'test_policy', 'metric': METRIC_NAME},
    'combiner': 'AND',
    'conditions': [{
        'display_name': 'test condition',
        'condition_threshold': {
            'filter': f'metric.type = "{METRIC_PATH}" AND resource.type = "{RESOURCE_TYPE}"',
            'comparison': 'COMPARISON_GT',
            'threshold_value': TRIGGER_NOTIFICATION_THRESHOLD_DOUBLE,
            'duration': Duration(seconds=0),
        }
    }],
    'notification_channels': []
}

TEST_SERIES = {
    'metric': {
        'type': METRIC_PATH,
    },
    'resource': {
        'type': RESOURCE_TYPE,
        'labels': {
            'instance_id': INSTANCE_ID,
            'zone': ZONE
        }
    }
}
