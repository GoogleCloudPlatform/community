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

"""Flask config for Jira integration."""

import os
from dotenv import load_dotenv
from utilities import secrets

load_dotenv()

class JiraConfig:
    """Base Jira config."""

    FLASK_ENV = 'production'
    LOGGING_LEVEL = 'INFO'
    TESTING = False
    DEBUG = False
    CLOSED_JIRA_ISSUE_STATUS = 'Done'



class ProdJiraConfig(JiraConfig):
    """Production Jira config."""

    def __init__(self):
        self._jira_url = None
        self._jira_access_token = None
        self._jira_access_token_secret = None
        self._jira_consumer_key = None
        self._jira_key_cert = None
        self._jira_project = None
        self._gcloud_project_id = os.environ.get('PROJECT_ID')


    @property
    def JIRA_URL(self):
        if self._jira_url is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_url')
            self._jira_url = secret.get_secret_value()

        return self._jira_url


    @property
    def JIRA_ACCESS_TOKEN(self):
        if self._jira_access_token is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_access_token')
            self._jira_access_token = secret.get_secret_value()

        return self._jira_access_token


    @property
    def JIRA_ACCESS_TOKEN_SECRET(self):
        if self._jira_access_token_secret is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_access_token_secret')
            self._jira_access_token_secret = secret.get_secret_value()

        return self._jira_access_token_secret


    @property
    def JIRA_CONSUMER_KEY(self):
        if self._jira_consumer_key is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_consumer_key')
            self._jira_consumer_key = secret.get_secret_value()

        return self._jira_consumer_key


    @property
    def JIRA_KEY_CERT(self):
        if self._jira_key_cert is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_key_cert')
            self._jira_key_cert = secret.get_secret_value()

        return self._jira_key_cert


    @property
    def JIRA_PROJECT(self):
        if self._jira_project is None:
            secret = secrets.GoogleSecretManagerSecret(
                self._gcloud_project_id, 'jira_project')
            self._jira_project = secret.get_secret_value()

        return self._jira_project



class DevJiraConfig(JiraConfig):
    """Development Jira config."""

    FLASK_ENV = 'development'
    LOGGING_LEVEL = 'DEBUG'
    DEBUG = True
    TESTING = True


    def __init__(self):
        self._jira_url = None
        self._jira_access_token = None
        self._jira_access_token_secret = None
        self._jira_consumer_key = None
        self._jira_key_cert = None
        self._jira_project = None


    @property
    def JIRA_URL(self):
        if self._jira_url is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_URL')
            self._jira_url = secret.get_secret_value()

        return self._jira_url


    @property
    def JIRA_ACCESS_TOKEN(self):
        if self._jira_access_token is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_ACCESS_TOKEN')
            self._jira_access_token = secret.get_secret_value()

        return self._jira_access_token


    @property
    def JIRA_ACCESS_TOKEN_SECRET(self):
        if self._jira_access_token_secret is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_ACCESS_TOKEN_SECRET')
            self._jira_access_token_secret = secret.get_secret_value()

        return self._jira_access_token_secret


    @property
    def JIRA_CONSUMER_KEY(self):
        if self._jira_consumer_key is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_CONSUMER_KEY')
            self._jira_consumer_key = secret.get_secret_value()

        return self._jira_consumer_key


    @property
    def JIRA_KEY_CERT(self):
        if self._jira_key_cert is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_KEY_CERT')
            self._jira_key_cert = secret.get_secret_value()

        return self._jira_key_cert


    @property
    def JIRA_PROJECT(self):
        if self._jira_project is None:
            secret = secrets.EnvironmentVariableSecret('JIRA_PROJECT')
            self._jira_project = secret.get_secret_value()

        return self._jira_project



class TestJiraConfig(JiraConfig):
    """Test Jira config."""

    FLASK_ENV = 'test'
    LOGGING_LEVEL = 'DEBUG'
    DEBUG = True
    TESTING = True

    CLOSED_JIRA_ISSUE_STATUS = 'Done'
    JIRA_URL = 'https://jira.atlassian.com'
    JIRA_ACCESS_TOKEN = 'test-access-token'
    JIRA_ACCESS_TOKEN_SECRET = 'test-access-token-secret'
    JIRA_CONSUMER_KEY = 'test-consumer-key'
    JIRA_KEY_CERT = 'test-key-cert'
    JIRA_PROJECT = 'test-project'



_ENVIRONMENT_TO_CONFIG_MAPPING = {
    'prod': ProdJiraConfig,
    'dev': DevJiraConfig,
    'test': TestJiraConfig,
    'default': ProdJiraConfig
}



def load():
    environment_name = os.environ.get('FLASK_APP_ENV', 'default')
    return _ENVIRONMENT_TO_CONFIG_MAPPING[environment_name]()
