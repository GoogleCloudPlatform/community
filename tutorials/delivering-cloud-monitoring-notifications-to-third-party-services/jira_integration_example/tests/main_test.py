# Copyright 2019 Google, LLC.
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

# Source code from https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/run/pubsub/main_test.py

import base64
import json

import pytest

import main


@pytest.fixture
def config():
    main.app.config.from_object('config.TestJiraConfig')
    return main.app.config


@pytest.fixture
def flask_client():
    main.app.testing = True
    return main.app.test_client()


def test_empty_payload(flask_client):
    response = flask_client.post('/', json='')

    assert response.status_code == 400
    assert b'invalid Pub/Sub message format' in response.data


def test_invalid_payload(flask_client):
    response = flask_client.post('/', json={'nomessage': 'invalid'})

    assert response.status_code == 400
    assert b'invalid Pub/Sub message format' in response.data


def test_invalid_mimetype(flask_client):
    response = flask_client.post('/', json="{ message: true }")

    assert response.status_code == 400
    assert b'invalid Pub/Sub message format' in response.data


def test_nonstring_pubsub_message(flask_client):
    response = flask_client.post('/', json={'message': True})

    assert response.status_code == 400
    assert b'invalid Pub/Sub message format' in response.data


def test_nonstring_notification_message(flask_client):
    response = flask_client.post('/', json={'message': {'data': True}})

    assert response.status_code == 400
    assert b'data should be in a string format' in response.data


def test_unicode_notification_message(flask_client):
    data = '{"incident": {"stăte": "open"}}'

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 400
    assert b'data should be base64-encoded' in response.data


def test_invalid_notification_message(flask_client):
    message = 'invalid message'
    data = base64.b64encode(message.encode()).decode()

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 400
    assert b'Notification could not be decoded' in response.data


def test_incident_alert_message_with_missing_data(flask_client, mocker):
    message = '{"incident": {}}'
    data = base64.b64encode(message.encode()).decode()

    mocker.patch('main.JIRA', autospec=True)
    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 400


def test_incident_alert_message_with_invalid_state(flask_client, mocker):
    message = ('{"incident": {"state": "invalid_state", "condition_name": "test_condition",'
               '"resource_name": "test_resource", "summary": "test_summary",'
               '"url": "http://test-cloud.com", "incident_id": "0.abcdef123456"}}')
    data = base64.b64encode(message.encode()).decode()

    mocker.patch('main.JIRA', autospec=True)
    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 400


def test_incident_alert_message(flask_client, config, mocker):
    message = ('{"incident": {"state": "open", "condition_name": "test_condition",'
               '"resource_name": "test_resource", "summary": "test_summary",'
               '"url": "http://test-cloud.com", "incident_id": "0.abcdef123456"}}')
    data = base64.b64encode(message.encode()).decode()

    mocker.patch('main.jira_notification_handler.update_jira_based_on_monitoring_notification',
                 autospec=True)
    mocker.patch('main.JIRA', autospec=True)
    jira_client = main.JIRA.return_value # JIRA client to be used when handling pub/sub message

    response = flask_client.post('/', json={'message': {'data': data}})

    main.jira_notification_handler.update_jira_based_on_monitoring_notification.assert_called_once_with(
        jira_client, config['JIRA_PROJECT'], config['CLOSED_JIRA_ISSUE_STATUS'],
        json.loads(message))

    assert response.status_code == 200
