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
import time

from google.cloud import monitoring_v3
from google.protobuf.duration_pb2 import Duration
from google.api_core.exceptions import NotFound


PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']
TRIGGER_VALUE = 3.0


class Error(Exception):
    """Base class for all errors raised in this module."""


class CustomMetricNotFoundError(Error):
    """Raised when a metric can't be found."""


class DuplicatePolicyError(Error):
    """Raised when policy creation is attempted with a display name that already exists."""


class PolicyNotFoundError(Error):
    """Raised when a policy can't be found."""


class TestCustomMetricClient():
    """Client that can create and modify custom metrics
    used as monitoring data for testing purposes.

    Attributes:
        _project_id: The id of the project to store metrics
        _client: A monitoring_v3.MetricServiceClient instance to modify metric data
    """

    def __init__(self, project_id):
        self._project_id = project_id
        self._client = monitoring_v3.MetricServiceClient()
        self._project_name = self._client.project_path(self._project_id)


    def create_custom_metric(self, metric_name):
        """Creates a custom metric with the given metric name.

        Args:
            metric_name: The name of the metric
        """
        descriptor = monitoring_v3.types.MetricDescriptor()
        descriptor.type = 'custom.googleapis.com/' + metric_name
        descriptor.metric_kind = (
            monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE)
        descriptor.value_type = (
            monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE)
        descriptor.description = 'A custom metric meant for testing purposes'
        descriptor = self._client.create_metric_descriptor(self._project_name, descriptor)
        print(f'Created {descriptor.name}.')


    def get_custom_metric(self, metric_name):
        """Get the custom metric with the given metric name.

        Args:
            metric_name: the name of the metric descriptor

        Raises:
            CustomMetricNotFoundError: if the metric doesn't exist
        """
        try:
            return self._client.get_metric_descriptor(f'projects/{self._project_id}/metricDescriptors/custom.googleapis.com/{metric_name}')
        except NotFound:
            raise CustomMetricNotFoundError(f'{metric_name} does not exist.')


    def append_to_time_series(self, metric_name, point_value):
        """Add a data point with the given point value to the specified metric.

        Args:
            metric_name: The name of the metric to modify
            point_value: The value of the data point to add
        """
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = 'custom.googleapis.com/' + metric_name
        series.resource.type = 'gce_instance'
        series.resource.labels['instance_id'] = '1234567890123456789'
        series.resource.labels['zone'] = 'us-central1-f'
        point = series.points.add()
        point.value.double_value = point_value
        now = time.time()
        point.interval.end_time.seconds = int(now)
        point.interval.end_time.nanos = int(
            (now - point.interval.end_time.seconds) * 10**9)
        self._client.create_time_series(self._project_name, [series])


    def delete_custom_metric(self, metric_name):
        """Delete the given custom metric.

        Args:
            metric_name: Name of metric to delete
        """
        descriptor_name = f'{self._project_name}/metricDescriptors/custom.googleapis.com/{metric_name}'
        self._client.delete_metric_descriptor(descriptor_name)
        print(f'Deleted metric descriptor {descriptor_name}.')


class TestPolicyClient():
    """Client that can create and modify alerting policies and
    trigger/resolve incidents for testing purposes.

    Attributes:
        _project_id: The id of the project to add or modify policies to
        _policy_client: A monitoring_v3.AlertPolicyServiceClient instance to call the alertPolicies API
        _metric_client: A TestCustomMetricClient() instance to modify metric data
        to trigger/resolve incidents
        _threshold_value: Value above which a policy triggers an incident
    """

    def __init__(self, project_id, metric_client):
        self._project_id = project_id
        self._policy_client = monitoring_v3.AlertPolicyServiceClient()
        self._metric_client = metric_client
        self._threshold_value = TRIGGER_VALUE
        self._project_name = self._policy_client.project_path(self._project_id)


    def get_policy(self, policy_name):
        """Get the policy with the given policy display name.

        Args:
            policy_name: the display name of the policy

        Returns:
            the AlertPolicy instance with the given policy display name

        Raises:
            PolicyNotFoundError: if the policy doesn't exist
        """
        try:
            policy = list(self._policy_client.list_alert_policies(name=self._project_name, filter_=f'display_name = "{policy_name}"'))[0]
            return policy
        except IndexError:
            raise PolicyNotFoundError()


    def create_policy(self, policy_name, metric_name):
        """Creates an alert policy with the given policy display name.

        By default, a policy is made with a single condition that triggers
        if a custom metric with the given metric name is above the threshold value.

        Args:
            policy_name: the name to identify the policy by
            metric_name: metric to attach the policy to

        Raises:
            DuplicatePolicyError: If policy with given policy display name already exists.
            CustomMetricNotFoundError: If the given metric doesn't exist.
        """
        try:
            self.get_policy(policy_name)
        except PolicyNotFoundError:
            pass
        else:
            raise DuplicatePolicyError(f'policy with display name {policy_name} already exists.')

        try:
            condition_threshold = monitoring_v3.types.AlertPolicy.Condition.MetricThreshold(
                filter=f'metric.type = "custom.googleapis.com/{metric_name}" AND resource.type = "gce_instance"',
                comparison=monitoring_v3.enums.ComparisonType.COMPARISON_GT,
                threshold_value=self._threshold_value,
                duration=Duration(seconds=0)
            )
            condition = monitoring_v3.types.AlertPolicy.Condition(
                display_name='test condition',
                condition_threshold=condition_threshold
            )
            alert_policy = monitoring_v3.types.AlertPolicy(
                display_name=policy_name,
                user_labels={'type': 'test_policy', 'metric': metric_name},
                conditions=[condition],
                combiner='AND'
            )
            self._policy_client.create_alert_policy(self._project_name, alert_policy)
            print(f'Created {policy_name}.')
        except NotFound:
            raise CustomMetricNotFoundError(f'{metric_name} does not exist.')


    def delete_policy(self, policy_name):
        """Deletes all policies with the given policy display name.

        Args:
            policy_name: the display name of the policy to delete
        """
        policies = list(self._policy_client.list_alert_policies(name=self._project_name, filter_=f'display_name = "{policy_name}"'))

        for policy in policies:
            self._policy_client.delete_alert_policy(policy.name)

        print(f'Deleted {policy_name}.')


    def delete_test_policies(self):
        """Deletes all test policies."""
        policies = list(self._policy_client.list_alert_policies(name=self._project_name, filter_='user_labels["type"] = "test_policy"'))

        for policy in policies:
            self._policy_client.delete_alert_policy(policy.name)

        print('Deleted all test policies.')


    def trigger_incident(self, policy_name):
        """Trigger an incident for the given policy.

        Args:
            policy_name: the name of the policy to trigger
        """
        policy = self.get_policy(policy_name)
        metric_name = policy.user_labels['metric']
        self._metric_client.append_to_time_series(metric_name, self._threshold_value + 1)
        print(f'Triggered incident for {policy_name}.')


    def resolve_incident(self, policy_name):
        """Resolve incidents for the given policy.

        Args:
            policy_name: the name of the policy to resolve incidents for
        """
        policy = self.get_policy(policy_name)
        metric_name = policy.user_labels['metric']
        self._metric_client.append_to_time_series(metric_name, self._threshold_value - 1)
        print(f'Resolved incident(s) for {policy_name}.')
