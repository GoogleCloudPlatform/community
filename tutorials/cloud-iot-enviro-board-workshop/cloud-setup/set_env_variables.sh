#!/bin/bash
#
# This script sets the environment variables for project environment specific
# information such as project_id, region and zone choice.
#
# Copyright Google Inc. 2019
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
export PROJECT_ID=$(gcloud config list --format 'value(core.project)')
export EVENT_TOPIC=<replace with unique topic name>
export REGISTRY_ID=<replace with unique registry id>
export REGION=europe-west1
export DEVICE_ID=<replace with unique device id>
