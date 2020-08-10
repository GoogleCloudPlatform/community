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

"""Module to handle input from Google Monitoring.

This module defines functions and errors to handle input from Google Monitoring,
such as Pub/Sub notifications.
"""

import base64
import binascii


class Error(Exception):
    """Base class for all errors raised in this module."""


class DataParseError(Error):
    """Raised when the encoded 'data' field of a Pub/Sub message cannot be parsed."""


def parse_data_from_message(pubsub_received_message):
    """Parses notification messages from Pub/Sub.

    Args:
        pubsub_received_message: Dictionary containing the Pub/Sub message.
        The message itself should be a base64-encoded string.

    Returns:
        The decoded 'data' value of provided Pub/Sub message, returned as a string.

    Raises:
        DataParseError: If data cannot be parsed.
    """
    try:
        data_base64_string = pubsub_received_message['message']['data']
    except (KeyError, TypeError) as e:
        raise DataParseError('invalid Pub/Sub message format') from e

    try:
        data_bytes = base64.b64decode(data_base64_string)
    except (binascii.Error, ValueError) as e:
        raise DataParseError('data should be base64-encoded') from e
    except TypeError as e:
        raise DataParseError('data should be in a string format') from e

    data_string = data_bytes.decode('utf-8')
    data_string = data_string.strip()

    return data_string
