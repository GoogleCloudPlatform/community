#!/usr/bin/env python3
"""
Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import argparse

from requests import post, get
from tomlkit import parse


def get_project_details(project_file: str = 'pyproject.toml') -> (str, str):
    with open(project_file, 'r') as proj:
        toml = parse(proj.read())

    return toml["tool"]["poetry"]["name"], toml["tool"]["poetry"]["version"]


def get_bom_xml(bom_xml: str = 'cyclonedx.xml') -> str:
    with open(bom_xml, 'r') as bom:
        return bom.read()


def get_project_uuid(url: str, api_key: str, project_name: str) -> str:
    headers = {'x-api-key': api_key}
    response = get(f'{url}/api/v1/project/lookup?name={project_name}', headers=headers)
    return response.json()['uuid']


def submit_bom(url: str, api_key: str) -> (int, str, str):
    project_name, project_version = get_project_details()

    headers = {'X-Api-Key': api_key}

    payload = {'bom': get_bom_xml(),
               'projectName': project_name,
               'projectVersion': project_version,
               'autoCreate': True}

    response = post(f'{url}/api/v1/bom', headers=headers, files=payload)
    return response.status_code, response.reason, response.text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Submit an SBOM to Dependency Track.')

    parser.add_argument('--url', help='the Dependency Track URL', required=True)
    parser.add_argument('--api-key', help='the Dependency Track API Key', required=True)
    args = parser.parse_args()

    print(submit_bom(args.url, args.api_key))
