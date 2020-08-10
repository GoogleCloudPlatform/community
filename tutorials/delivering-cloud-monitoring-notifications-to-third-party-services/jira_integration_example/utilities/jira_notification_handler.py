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

"""Module to handle interactions with a Jira server.

This module defines a function to interact with Jira server when a
monitoring notification occurs. In addition, it defines error
classes to be used by the function.
"""

import logging
logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for all errors raised in this module."""


class NotificationParseError(Error):
    """Exception raised for errors in a monitoring notification format."""


class UnknownIncidentStateError(Error):
    """Exception raised for errors in an invalid incident state value."""


def update_jira_based_on_monitoring_notification(jira_client, jira_project,
                                                 jira_status, notification):
    """Updates a Jira server based off the data in a monitoring notification.

    If the monitoring notification is about an open incident, a new issue (of
    type bug) is created. If it is about a closed incident, the issues corresponding
    to the incident (if any) will be searched for and transitioned to the specified
    jira status. These issues will be created / searched for in the jira server that
    the jira client is connected to under the specified jira project.

    Args:
        jira_client: A JIRA object that acts as a client which allows
            interaction with a specific Jira server. This is the server
            where issues will be created / searched for.
        jira_project: The key or id of the Jira project under which to create /
            search for Jira issues.
        jira_status: The status to transition issues corresponding to
                    closed incidents to.
        notification: The dictionary containing the notification data.

    Raises:
        UnknownIncidentStateError: If the incident state is not open or closed.
        NotificationParseError: If notification is missing required dict key.
        JIRAError: If error occurs when using the jira client
    """

    try:
        incident_data = notification['incident']
        incident_id = incident_data['incident_id']
        incident_state = incident_data['state']
        incident_condition_name = incident_data['condition_name']
        incident_resource_name = incident_data['resource_name']
        incident_summary = incident_data['summary']
        incident_url = incident_data['url']
    except KeyError as e:
        raise NotificationParseError(f"Notification is missing required dict key: {str(e)}")

    incident_id_label = f'monitoring_incident_id_{incident_id}'

    if incident_state == 'open':
        summary = '%s - %s' % (incident_condition_name, incident_resource_name)
        description = '%s\nSee: %s' % (incident_summary, incident_url)
        issue = jira_client.create_issue(
            project=jira_project,
            summary=summary,
            description=description,
            issuetype={'name': 'Bug'},
            labels=[incident_id_label])
        logger.info('Created jira issue %s', issue)

    elif incident_state == 'closed':
        incident_issues = jira_client.search_issues(
            f'labels = {incident_id_label} AND status != {jira_status}')

        if incident_issues:
            for issue in incident_issues:
                jira_client.transition_issue(issue, jira_status)
                logger.info('Jira issue %s transitioned to %s status', issue, jira_status)
        else:
            logger.warning('No Jira issues corresponding to incident id %s found to '
                           'transition to %s status', incident_id, jira_status)

    else:
        raise UnknownIncidentStateError(
            'Incident state must be "open" or "closed"')
