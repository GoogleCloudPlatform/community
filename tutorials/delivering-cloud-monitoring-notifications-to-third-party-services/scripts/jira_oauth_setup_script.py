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

"""Generates OAuth credentials for a given Jira server, and optionally
saves those credentials to Google Secret Manager. This is a one-time
setup script that generates the credentials necessary for a client to
connect to a Jira server. It must be ran manually.


  How to use:

  Show help message:
    $ python3 jira_oauth_setup_script.py --help

  Write Jira OAuth credentials to output files:
    $ python3 jira_oauth_setup_script.py JIRA_URL

  Write Jira OAuth credentials to output files and Google Secret Manager:
    $ python3 jira_oauth_setup_script.py --gcp_project_id="PROJECT_ID" JIRA_URL

  Supply your own RSA keys in files named `private.pem` and `public.pem` (can be
  used to skip resetting up the Jira application link when running the script a
  second time either to update the OAuth credentials or due to the script failing
  halfway through the first run):
    $ python3 jira_oauth_setup_script.py --load_keys JIRA_URL

  Specify the consumer key to use for Jira OAuth authorization:
    $ python3 jira_oauth_setup_script.py --consumer_key="CONSUMER_KEY" JIRA_URL
"""


import argparse
from requests_oauthlib import OAuth1Session
from oauthlib.oauth1 import SIGNATURE_RSA
from Crypto.PublicKey import RSA
from google.cloud import secretmanager
from google.api_core.exceptions import AlreadyExists


def create_secret(client, gcp_project_id, secret_id):
    """Create a new secret with the given name in Secret Manager. A secret
    is a logical wrapper around a collection of secret versions. Secret
    versions hold the actual secret material.

    Args:
        client: A Secret Manager client to use to create the secret
        gcp_project_id: The id of the Google Cloud project in which to
                        create the secret
        secret_id: The name of the secret to create
    """

    parent = client.project_path(gcp_project_id)
    response = client.create_secret(parent, secret_id, {
        'replication': {
            'automatic': {},
        },
    })
    print('Created secret: {}'.format(response.name))


def add_secret_version(client, gcp_project_id, secret_id, payload):
    """
    Add a new secret version to the given secret with the provided payload.

    Args:
        client: A Secret Manager client to use to add the secret version
        gcp_project_id: The id of the Google Cloud project in which to
                        add the secret version
        secret_id: The name of the secret to add a new version to
        payload: The payload of the new secret version
    """

    parent = client.secret_path(gcp_project_id, secret_id)

    if isinstance(payload, str):
        payload = payload.encode('UTF-8')

    response = client.add_secret_version(parent, {'data': payload})
    print('Added secret version: {}'.format(response.name))


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=('Generate OAuth credentials for a given Jira server, and optionally '
                     'saves those credentials to Google Secret Manager. This is a one-time '
                     'setup script that generates the credentials necessary for a client to '
                     'connect to a Jira server. It must be ran manually.'))

    parser.add_argument('jira_url',
                        help=('URL of the Jira Server to setup OAuth for, e.g '
                              'https://jira.atlassian.com'))

    parser.add_argument('--gcp_project_id',
                        help=('ID of the Google Cloud project whose Secret Manager '
                              'to store Jira OAuth credentials in.'))

    parser.add_argument('--consumer_key',
                        help=('Consumer key to use for Jira OAuth authorization. '
                              'If not specified, default is "CloudMonitoringOauthKey"'),
                        default='CloudMonitoringOauthKey')

    parser.add_argument('--load_keys',
                        action='store_true',
                        help=('Load already generated private/public RSA keys called '
                              '"private.pem" and "public.pem"'))

    args = parser.parse_args()


    # Create or load in RSA public and private keys
    if args.load_keys:
        with open('private.pem', 'rb') as f:
            private_key_pem = f.read()

        with open('public.pem', 'rb') as f:
            public_key_pem = f.read()

        print("RSA public and private keys loaded")
    else:
        private_key = RSA.generate(2048)
        private_key_pem = private_key.exportKey('PEM')
        with open('private.pem', 'wb') as f:
            f.write(private_key_pem)

        public_key = private_key.publickey()
        public_key_pem = public_key.exportKey('PEM')
        with open('public.pem', 'wb') as f:
            f.write(public_key_pem)

        print("RSA public and private keys created")


    # Setup Jira Oauth
    application_links_url = f'{args.jira_url}/plugins/servlet/applinks/listApplicationLinks'

    print(f"""\nComplete the following steps:
    1. In Jira, navigate to Jira Settings > Applications > Application Links
       OR go to {application_links_url}
    2. In the 'Enter the URL of the application you want to link' field, enter
       http://example.com/ , and then click 'Create new link'. Ignore the 'No response was
       received from the URL you entered' warning that is displayed and click 'Continue'
    3. On the first screen of the 'Link applications' dialog, enter 'Cloud Monitoring App' for
       'Application Name', select the 'Create incoming link' checkbox, and click 'Continue'
    4. On next screen of the 'Link applications' dialog, enter the following consumer details:
        * Consumer Key: {args.consumer_key}
        * Consumer Name: Cloud Monitoring App
        * Public Key:\n{public_key_pem.decode('utf-8')}
    5: Click 'Continue'

    (Note the previous steps are based off of the instructions at https://developer.atlassian.com/server/jira/platform/oauth/#create-an-application-link)
    """)

    input('Once complete, press "Enter" to proceed\n')

    oauth = OAuth1Session(args.consumer_key,
                          signature_method=SIGNATURE_RSA,
                          rsa_key=private_key_pem,
                          signature_type='auth_header',
                          verifier='jira_verifier')

    request_token_url = f'{args.jira_url}/plugins/servlet/oauth/request-token'
    fetch_response = oauth.fetch_request_token(request_token_url)
    oauth_token = fetch_response.get('oauth_token')
    oauth_token_secret = fetch_response.get('oauth_token_secret')

    base_authorization_url = f'{args.jira_url}/plugins/servlet/oauth/authorize'
    authorization_url = oauth.authorization_url(base_authorization_url)
    print(f'Go to the following URL and click allow: {authorization_url}\n')
    input('Once complete, press "Enter" to proceed\n')

    access_token_url = f'{args.jira_url}/plugins/servlet/oauth/access-token'
    oauth_tokens = oauth.fetch_access_token(access_token_url)
    oauth_token = oauth_tokens.get('oauth_token')
    oauth_token_secret = oauth_tokens.get('oauth_token_secret')

    with open('jira_access_token.txt', 'w') as f:
        f.write(oauth_token)
    print('Jira access token stored in jira_access_token.txt')

    with open('jira_access_token_secret.txt', 'w') as f:
        f.write(oauth_token_secret)
    print('Jira access token secret stored in jira_access_token_secret.txt')



    # Store Oauth data necessary to authorize Jira client in Google Secret Manager
    if args.gcp_project_id:
        client = secretmanager.SecretManagerServiceClient()

        try:
            create_secret(client, args.gcp_project_id, 'jira_access_token')
        except AlreadyExists:
            print('Secret named "jira_access_token" already exists; adding new '
                  'secret version with the new access token')

        try:
            create_secret(client, args.gcp_project_id, 'jira_access_token_secret')
        except AlreadyExists:
            print('Secret named "jira_access_token_secret" already exists; adding new '
                  'secret version with the new access token secret')

        try:
            create_secret(client, args.gcp_project_id, 'jira_consumer_key')
        except AlreadyExists:
            print('Secret named "jira_consumer_key" already exists; adding new '
                  'secret version with the new consumer key')

        try:
            create_secret(client, args.gcp_project_id, 'jira_key_cert')
        except AlreadyExists:
            print('Secret named "jira_key_cert" already exists; adding new '
                  'secret version with the new key cert')


        add_secret_version(client, args.gcp_project_id, 'jira_access_token', oauth_token)
        add_secret_version(client, args.gcp_project_id, 'jira_access_token_secret', oauth_token_secret)
        add_secret_version(client, args.gcp_project_id, 'jira_consumer_key', args.consumer_key)
        add_secret_version(client, args.gcp_project_id, 'jira_key_cert', private_key_pem)

    print("Successfully setup Jira OAuth")


if __name__ == '__main__':
    main()
