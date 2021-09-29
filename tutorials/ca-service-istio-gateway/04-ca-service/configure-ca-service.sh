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

gcloud services enable privateca.googleapis.com

CA_LOCATION=${CA_LOCATION:-us-central1}
export CA_LOCATION

ROOT_CA_POOL=${ROOT_CA_POOL:-root-ca-pool-tutorial}
gcloud privateca pools create "$ROOT_CA_POOL" \
    --location "$CA_LOCATION" \
    --tier enterprise
export ROOT_CA_POOL

ROOT_CA=${ROOT_CA:-root-ca-tutorial}
gcloud privateca roots create "$ROOT_CA" \
    --auto-enable \
    --key-algorithm "ec-p384-sha384" \
    --location "$CA_LOCATION" \
    --pool "$ROOT_CA_POOL" \
    --subject "CN=Example Root CA, O=Example Organization" \
    --use-preset-profile root_unconstrained
export ROOT_CA

SUBORDINATE_CA_POOL=${SUBORDINATE_CA_POOL:-subordinate-ca-pool-tutorial}
gcloud privateca pools create "$SUBORDINATE_CA_POOL" \
    --location "$CA_LOCATION" \
    --tier devops
export SUBORDINATE_CA_POOL

SUBORDINATE_CA=${SUBORDINATE_CA:-subordinate-ca-tutorial}
gcloud privateca subordinates create "$SUBORDINATE_CA" \
    --auto-enable \
    --issuer-location "$CA_LOCATION" \
    --issuer-pool "$ROOT_CA_POOL" \
    --key-algorithm "ec-p256-sha256" \
    --location "$CA_LOCATION" \
    --pool "$SUBORDINATE_CA_POOL" \
    --subject "CN=Example Server TLS CA, O=Example Organization" \
    --use-preset-profile subordinate_server_tls_pathlen_0
export SUBORDINATE_CA
