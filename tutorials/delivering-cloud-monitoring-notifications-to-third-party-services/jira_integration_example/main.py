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

# The code in this module is based on
# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/run/pubsub/main.py.
# See https://cloud.google.com/run/docs/tutorials/pubsub for the accompanying
# Cloud Run/PubSub solutions guide.

"""Runs Cloud Monitoring Notification Integration app with Flask."""

# [START run_pubsub_server_setup]
import logging
import os
import json

from flask import Flask, request
from jira import JIRA, JIRAError

import config
from utilities import pubsub, jira_notification_handler


app_config = config.load()
logging.basicConfig(level=app_config.LOGGING_LEVEL)

# logger inherits the logging level and handlers of the root logger
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(app_config)
# [END run_pubsub_server_setup]


# [START run_pubsub_handler]
@app.route('/', methods=['POST'])
def handle_pubsub_message():
    pubsub_received_message = request.get_json()

    # parse the Pub/Sub data
    try:
        pubsub_data_string = pubsub.parse_data_from_message(pubsub_received_message)
    except pubsub.DataParseError as e:
        logger.error(e)
        return (str(e), 400)

    # load the notification from the data
    try:
        monitoring_notification_dict = json.loads(pubsub_data_string)
    except json.JSONDecodeError as e:
        logger.error(e)
        return (f'Notification could not be decoded due to the following exception: {e}', 400)

    return send_monitoring_notification_to_third_party(monitoring_notification_dict)
# [END run_pubsub_handler]


def send_monitoring_notification_to_third_party(notification):
    """Send a given monitoring notification to a third party service.

    Args:
        notification: The dictionary containing the notification data.

    Returns:
        A tuple containing an HTTP response message and HTTP status code
        indicating whether or not sending the notification to the third
        party service was successful.
    """

    try:
        oauth_dict = {'access_token': app.config['JIRA_ACCESS_TOKEN'],
                      'access_token_secret': app.config['JIRA_ACCESS_TOKEN_SECRET'],
                      'consumer_key': app.config['JIRA_CONSUMER_KEY'],
                      'key_cert': app.config['JIRA_KEY_CERT']}
        jira_client = JIRA(app.config['JIRA_URL'], oauth=oauth_dict)
        jira_notification_handler.update_jira_based_on_monitoring_notification(
            jira_client,
            app.config['JIRA_PROJECT'],
            app.config['CLOSED_JIRA_ISSUE_STATUS'],
            notification)

    except (jira_notification_handler.Error, JIRAError) as e:
        logger.error(e)
        return (str(e), 400)

    return ('', 200)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
