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

"""Unit tests for functions in philips_hue.py."""

import re

import pytest

from utilities import philips_hue, philips_hue_mock


@pytest.fixture
def config():
    configs = {
        'BRIDGE_IP_ADDRESS': '127.0.0.1',
        'USERNAME': 'test-user'
    }
    return configs


@pytest.fixture
def philips_hue_client(config):
    philips_hue_client = philips_hue.PhilipsHueClient(
        config['BRIDGE_IP_ADDRESS'], config['USERNAME'])
    return philips_hue_client


def test_set_color(philips_hue_client, requests_mock):
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    response = philips_hue_client.set_color('1', 0)

    assert response.status_code == 200
    assert "{'success': {'/lights/1/state/on': 'true'}}" in response.text
    assert "{'success': {'/lights/1/state/hue': '0'}}" in response.text


def test_set_color_bad_url(philips_hue_client, requests_mock):
    bridge_ip_address = philips_hue_client.bridge_ip_address
    username = philips_hue_client.username
    matcher = re.compile(f'http://{bridge_ip_address}/api/{username}')
    requests_mock.register_uri('PUT', matcher,
                               text=philips_hue_mock.mock_hue_put_response)

    with pytest.raises(philips_hue.BadAPIRequestError) as e:
        assert philips_hue_client.set_color('2', 65535)
    assert str(e.value) == 'invalid Philips Hue url'


def test_get_target_hue_from_incident_invalid_state():
    policy_name = 'unknown_policy'
    incident_state = 'unknown'
    notification = {'incident': {'policy_name': policy_name, "state": incident_state}}
    policy_hue_mapping = {
        'default': {
            'open': 65280,
            'closed': 24432
        }
    }

    with pytest.raises(philips_hue.UnknownIncidentStateError) as e:
        assert philips_hue.get_target_hue_from_monitoring_notification(
            notification, policy_hue_mapping)

    expected_error_value = ("Incident state for Google Cloud alerting policy "
                            "'unknown_policy' must be one of: ['open', "
                            "'closed']; actual: 'unknown'")
    assert str(e.value) == expected_error_value


def test_get_target_hue_with_nondefault_open_incident():
    policy_name = 'policyB'
    incident_state = 'open'
    expected_hue_value = 10126
    notification = {'incident': {'policy_name': policy_name, "state": incident_state}}
    policy_hue_mapping = {
        'policyB': {
            'open': expected_hue_value,
            'closed': 48013
        },
        'default': {
            'open': 65280,
            'closed': 24432
        }
    }

    actual_hue_value = philips_hue.get_target_hue_from_monitoring_notification(
        notification, policy_hue_mapping)

    assert actual_hue_value == expected_hue_value


def test_get_target_hue_with_nondefault_closed_incident():
    policy_name = 'policyB'
    incident_state = 'closed'
    expected_hue_value = 48013
    notification = {'incident': {'policy_name': policy_name, "state": incident_state}}
    policy_hue_mapping = {
        'policyB': {
            'open': 10126,
            'closed': expected_hue_value
        },
        'default': {
            'open': 65280,
            'closed': 24432
        }
    }

    actual_hue_value = philips_hue.get_target_hue_from_monitoring_notification(
        notification, policy_hue_mapping)

    assert actual_hue_value == expected_hue_value


def test_get_target_hue_with_default_open_incident():
    policy_name = 'unknown_policy'
    incident_state = 'open'
    expected_hue_value = 65280
    notification = {'incident': {'policy_name': policy_name, "state": incident_state}}
    policy_hue_mapping = {
        'default': {
            'open': expected_hue_value,
            'closed': 24432
        }
    }

    actual_hue_value = philips_hue.get_target_hue_from_monitoring_notification(
        notification, policy_hue_mapping)

    assert actual_hue_value == expected_hue_value


def test_get_target_hue_with_default_closed_incident():
    policy_name = 'unknown_policy'
    incident_state = 'closed'
    expected_hue_value = 24432
    notification = {'incident': {'policy_name': policy_name, "state": incident_state}}
    policy_hue_mapping = {
        'default': {
            'open': 65280,
            'closed': expected_hue_value
        }
    }

    actual_hue_value = philips_hue.get_target_hue_from_monitoring_notification(
        notification, policy_hue_mapping)

    assert actual_hue_value == expected_hue_value
