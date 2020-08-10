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

import time

import pytest

from google.cloud import monitoring_v3
from google.api_core import exceptions
from google.api_core import retry
from jira import JIRA

from tests import constants

import main


@retry.Retry(predicate=retry.if_exception_type(exceptions.NotFound), deadline=10)
def call_get_metric(metric_client, name):
    return metric_client.get_metric_descriptor(name)


@retry.Retry(predicate=retry.if_exception_type(exceptions.NotFound), deadline=10)
def call_get_alert_policy(policy_client, name):
    return policy_client.get_alert_policy(name)


@retry.Retry(predicate=retry.if_exception_type(exceptions.NotFound), deadline=10)
def call_get_notification_channel(notification_channel_client, name):
    return notification_channel_client.get_notification_channel(name)


@retry.Retry(predicate=retry.if_exception_type(AssertionError), deadline=180)
def call_assert_jira_issue_created(jira_client, open_status):
    test_issue = jira_client.search_issues(f'description~"custom/integ-test-metric for {constants.PROJECT_ID}" and status={open_status}')
    assert len(test_issue) == 1


@retry.Retry(predicate=retry.if_exception_type(AssertionError), deadline=180)
def call_assert_jira_issue_resolved(jira_client, resolved_status):
    test_issue = jira_client.search_issues(f'description~"custom/integ-test-metric for {constants.PROJECT_ID}" and status={resolved_status}')
    assert len(test_issue) == 1


@pytest.fixture
def config():
    return main.app.config


@pytest.fixture(scope='function')
def jira_client(config):
    # setup
    oauth_dict = {'access_token': config['JIRA_ACCESS_TOKEN'],
                  'access_token_secret': config['JIRA_ACCESS_TOKEN_SECRET'],
                  'consumer_key': config['JIRA_CONSUMER_KEY'],
                  'key_cert': config['JIRA_KEY_CERT']}
    jira_client = JIRA(config['JIRA_URL'], oauth=oauth_dict)

    yield jira_client

    # tear down
    test_issues = jira_client.search_issues(f'description~"custom/integ-test-metric for {constants.PROJECT_ID}"')
    for issue in test_issues:
        issue.delete()


@pytest.fixture(scope='function')
def metric_descriptor():
    # setup
    metric_client = monitoring_v3.MetricServiceClient()
    gcp_project_path = metric_client.project_path(constants.PROJECT_ID)

    metric_descriptor = metric_client.create_metric_descriptor(
        gcp_project_path,
        constants.TEST_METRIC_DESCRIPTOR)
    metric_descriptor = call_get_metric(metric_client, metric_descriptor.name)

    yield metric_descriptor

    # tear down
    metric_client.delete_metric_descriptor(metric_descriptor.name)


@pytest.fixture(scope='function')
def notification_channel():
    # setup
    notification_channel_client = monitoring_v3.NotificationChannelServiceClient()
    gcp_project_path = notification_channel_client.project_path(constants.PROJECT_ID)

    notification_channel = notification_channel_client.create_notification_channel(
        gcp_project_path,
        constants.TEST_NOTIFICATION_CHANNEL)
    notification_channel = call_get_notification_channel(notification_channel_client, notification_channel.name)

    yield notification_channel

    # tear down
    notification_channel_client.delete_notification_channel(notification_channel.name)


@pytest.fixture(scope='function')
def alert_policy(metric_descriptor, notification_channel):
    # setup
    policy_client = monitoring_v3.AlertPolicyServiceClient()
    gcp_project_path = policy_client.project_path(constants.PROJECT_ID)

    print(metric_descriptor.name)
    print(notification_channel.name)

    test_alert_policy = constants.TEST_ALERT_POLICY_TEMPLATE
    test_alert_policy['notification_channels'].append(notification_channel.name)

    alert_policy = policy_client.create_alert_policy(
        gcp_project_path,
        test_alert_policy)
    alert_policy = call_get_alert_policy(policy_client, alert_policy.name)

    yield alert_policy

    # tear down
    policy_client.delete_alert_policy(alert_policy.name)


def append_to_time_series(point_value):
    client = monitoring_v3.MetricServiceClient()
    gcp_project_path = client.project_path(constants.PROJECT_ID)

    series = monitoring_v3.types.TimeSeries()
    series.metric.type = constants.METRIC_PATH
    series.resource.type = constants.RESOURCE_TYPE
    series.resource.labels['instance_id'] = constants.INSTANCE_ID
    series.resource.labels['zone'] = constants.ZONE
    point = series.points.add()
    point.value.double_value = point_value
    now = time.time()
    point.interval.end_time.seconds = int(now)
    point.interval.end_time.nanos = int(
        (now - point.interval.end_time.seconds) * 10**9)

    client.create_time_series(gcp_project_path, [series])


def test_end_to_end(config, metric_descriptor, notification_channel, alert_policy, jira_client):
    assert metric_descriptor.type == constants.TEST_METRIC_DESCRIPTOR['type']
    assert notification_channel.display_name == constants.TEST_NOTIFICATION_CHANNEL['display_name']
    assert alert_policy.display_name == constants.ALERT_POLICY_NAME
    assert alert_policy.user_labels == constants.TEST_ALERT_POLICY_TEMPLATE['user_labels']
    assert alert_policy.notification_channels[0] == notification_channel.name

    # trigger incident and check jira issue created
    append_to_time_series(constants.TRIGGER_NOTIFICATION_THRESHOLD_DOUBLE + 1)
    call_assert_jira_issue_created(jira_client, "10000") # issue status id for "To Do"

    # resolve incident and check jira issue resolved
    append_to_time_series(constants.TRIGGER_NOTIFICATION_THRESHOLD_DOUBLE - 1)
    call_assert_jira_issue_resolved(jira_client, config['CLOSED_JIRA_ISSUE_STATUS'])
    