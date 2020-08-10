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

# NOTE:
# These tests are unit tests that mock Pub/Sub.

import base64
import re

import pytest

import main
from utilities import philips_hue, philips_hue_mock


@pytest.fixture
def config():
    main.app.config.from_object('config.TestPhilipsHueConfig')
    return main.app.config


@pytest.fixture
def flask_client():
    main.app.testing = True
    return main.app.test_client()


@pytest.fixture
def philips_hue_client(config):
    philips_hue_client = philips_hue.PhilipsHueClient(
        config['BRIDGE_IP_ADDRESS'], config['USERNAME'])
    return philips_hue_client


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


def test_invalid_incident_message(flask_client):
    message = '{"invalid": "error"}'
    data = base64.b64encode(message.encode()).decode()

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 400
    assert b'Notification is missing required dict key' in response.data


def test_nondefault_open_incident_alert_message(flask_client, philips_hue_client,
                                                requests_mock, config):
    message = '{"incident": {"policy_name": "policyB", "state": "open"}}'
    data = base64.b64encode(message.encode()).decode()
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 200

    expected_response_data = repr(config['POLICY_HUE_MAPPING']
                                  ['policyB']['open']).encode()
    assert response.data == expected_response_data


def test_nondefault_closed_incident_alert_message(flask_client, philips_hue_client,
                                                  requests_mock, config):
    message = '{"incident": {"policy_name": "policyB", "state": "closed"}}'
    data = base64.b64encode(message.encode()).decode()
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 200

    expected_response_data = repr(config['POLICY_HUE_MAPPING']
                                  ['policyB']['closed']).encode()
    assert response.data == expected_response_data


def test_default_open_incident_alert_message(flask_client, philips_hue_client,
                                             requests_mock, config):
    message = '{"incident": {"policy_name": "unknown_policy", "state": "open"}}'
    data = base64.b64encode(message.encode()).decode()
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 200

    expected_response_data = repr(config['POLICY_HUE_MAPPING']
                                  ['default']['open']).encode()
    assert response.data == expected_response_data


def test_default_closed_incident_alert_message(flask_client, philips_hue_client,
                                               requests_mock, config):
    message = '{"incident": {"policy_name": "unknown_policy", "state": "closed"}}'
    data = base64.b64encode(message.encode()).decode()
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    response = flask_client.post('/', json={'message': {'data': data}})

    assert response.status_code == 200

    expected_response_data = repr(config['POLICY_HUE_MAPPING']
                                  ['default']['closed']).encode()
    assert response.data == expected_response_data
