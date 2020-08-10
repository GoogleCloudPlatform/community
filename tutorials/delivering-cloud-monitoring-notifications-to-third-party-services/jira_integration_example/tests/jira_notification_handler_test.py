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

"""Unit tests for functions in jira_notification_handler.py."""

import pytest

from jira import JIRA, Issue
from utilities import jira_notification_handler


def test_update_jira_with_open_incident(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)

    jira_project = 'test_project'
    incident_state = 'open'
    incident_id = '0.abcdef123456'
    jira_status = "Done"
    notification = {'incident': {'state': incident_state, 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource', 'summary': 'test_summary',
                                 'url': 'http://test.com', 'incident_id': incident_id}}
    incident_id_label = f'monitoring_incident_id_{incident_id}'

    expected_summary = '%s - %s' % (notification['incident']['condition_name'],
                                    notification['incident']['resource_name'])
    expected_description = '%s\nSee: %s' % (notification['incident']['summary'],
                                            notification['incident']['url'])
    expected_issue_type = {'name': 'Bug'}
    expected_labels = [incident_id_label]

    jira_notification_handler.update_jira_based_on_monitoring_notification(jira_client, jira_project,
                                                                           jira_status, notification)

    jira_client.create_issue.assert_called_once_with(project=jira_project,
                                                     summary=expected_summary,
                                                     description=expected_description,
                                                     issuetype=expected_issue_type,
                                                     labels=expected_labels)


def test_update_jira_with_closed_incident_corresponding_to_jira_issues(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    mock_searched_issues = [mocker.create_autospec(Issue, instance=True),
                            mocker.create_autospec(Issue, instance=True)]
    jira_client.search_issues.return_value = mock_searched_issues

    jira_project = 'test_project'
    incident_state = 'closed'
    incident_id = '0.abcdef123456'
    jira_status = "Done"
    notification = {'incident': {'state': incident_state, 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource', 'summary': 'test_summary',
                                 'url': 'http://test.com', 'incident_id': incident_id}}

    jira_notification_handler.update_jira_based_on_monitoring_notification(jira_client, jira_project,
                                                                           jira_status, notification)

    incident_id_label = f'monitoring_incident_id_{incident_id}'
    expected_jira_query = f'labels = {incident_id_label} AND status != {jira_status}'
    jira_client.search_issues.assert_called_once_with(expected_jira_query)

    expected_transition_calls = [mocker.call(issue, jira_status) for issue in mock_searched_issues]
    jira_client.transition_issue.assert_has_calls(expected_transition_calls)
    assert jira_client.transition_issue.call_count == len(expected_transition_calls)


def test_update_jira_with_closed_incident_corresponding_to_no_jira_issues(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    mock_searched_issues = []
    jira_client.search_issues.return_value = mock_searched_issues

    jira_project = 'test_project'
    incident_state = 'closed'
    incident_id = '0.abcdef123456'
    jira_status = "Done"
    notification = {'incident': {'state': incident_state, 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource', 'summary': 'test_summary',
                                 'url': 'http://test.com', 'incident_id': incident_id}}

    jira_notification_handler.update_jira_based_on_monitoring_notification(jira_client, jira_project,
                                                                           jira_status, notification)

    incident_id_label = f'monitoring_incident_id_{incident_id}'
    expected_jira_query = f'labels = {incident_id_label} AND status != {jira_status}'
    jira_client.search_issues.assert_called_once_with(expected_jira_query)

    jira_client.transition_issue.assert_not_called()


def test_update_jira_with_invalid_incident_state(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    incident_state = 'unknown_state'
    jira_status = "Done"
    notification = {'incident': {'state': incident_state, 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource', 'summary': 'test_summary',
                                 'url': 'http://test.com', 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.UnknownIncidentStateError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = 'Incident state must be "open" or "closed"'
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_incident_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'incident'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_state_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'condition_name': 'test_condition',
                                 'resource_name': 'test_resource',
                                 'summary': 'test_summary',
                                 'url': 'http://test.com',
                                 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'state'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_condition_name_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'state': 'open',
                                 'resource_name': 'test_resource',
                                 'summary': 'test_summary',
                                 'url': 'http://test.com',
                                 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'condition_name'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_resource_name_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'state': 'open',
                                 'condition_name': 'test_condition',
                                 'summary': 'test_summary',
                                 'url': 'http://test.com',
                                 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'resource_name'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_summary_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'state': 'open',
                                 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource',
                                 'url': 'http://test.com',
                                 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'summary'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_url_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'state': 'open',
                                 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource',
                                 'summary': 'test_summary',
                                 'incident_id': '0.abcdef123456'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'url'"
    assert str(e.value) == expected_error_value


def test_update_jira_with_missing_incident_id_data(mocker):
    jira_client = mocker.create_autospec(JIRA, instance=True)
    jira_project = 'test_project'
    jira_status = "Done"
    notification = {'incident': {'state': 'open',
                                 'condition_name': 'test_condition',
                                 'resource_name': 'test_resource',
                                 'summary': 'test_summary',
                                 'url': 'http://test.com'}}

    with pytest.raises(jira_notification_handler.NotificationParseError) as e:
        assert jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client, jira_project, jira_status, notification)

    expected_error_value = "Notification is missing required dict key: 'incident_id'"
    assert str(e.value) == expected_error_value
