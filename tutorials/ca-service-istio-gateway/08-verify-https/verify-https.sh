#!/usr/bin/env bash
#
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

gcloud privateca roots describe "$ROOT_CA" \
    --location "$CA_LOCATION" \
    --pool "$ROOT_CA_POOL" \
    --format 'value(pemCaCertificates)' > root-ca.crt

gcloud compute instances create cas-tutorial-vm --no-scopes --no-service-account --zone "$ZONE"

gcloud compute scp root-ca.crt cas-tutorial-vm:~ --zone "$ZONE"

gcloud compute ssh cas-tutorial-vm --zone "$ZONE" \
    --command "curl --silent --cacert root-ca.crt \
        --resolve hello.example.com:443:$LOAD_BALANCER_IP \
        https://hello.example.com/ | head -n1"
