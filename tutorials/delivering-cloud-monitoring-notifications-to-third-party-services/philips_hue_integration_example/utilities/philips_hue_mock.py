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

"""Module to provide callback functions for mock HTTP requests to the Philips Hue API."""

import json


def mock_hue_put_response(request, context):
    """Callback for mocking a Philips Hue API response using the requests-mock library,
    specifically for a put request.

    This mock response assumes that the system has a single light with light_id of '1',
    and the expected request is to set the 'on' state as well as 'hue' state.

    See https://requests-mock.readthedocs.io/en/latest/response.html for usage details.

    Args:
        request: The requests.Request object that was provided. The request method is
        assumed to be a put request.
        context: An object containing the collected known data about this response
        (headers, status_code, reason, cookies).

    Returns:
        The response text with confirmation of the arguments passed in.
    """
    expected_path = '/lights/1/state'
    if expected_path not in request.url:
        context.status_code = 400
        return 'invalid Philips Hue url'

    try:
        body_dict = json.loads(request.body)
    except json.JSONDecodeError:
        context.status_code = 400
        return 'put request body should be a JSON-encoded string'

    try:
        on = body_dict['on']
        hue = body_dict['hue']
    except KeyError:
        context.status_code = 400
        return 'missing keys in put request body'


    context.status_code = 200

    response = []
    if on:
        response.append({'success':{'/lights/1/state/on': 'true'}})
    else:
        response.append({'success':{'/lights/1/state/on': 'false'}})

    response.append({'success':{'/lights/1/state/hue': f'{hue}'}})
    return str(response)
