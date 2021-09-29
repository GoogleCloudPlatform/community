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

kpt fn eval 06-cert-issuer --image gcr.io/kpt-fn/apply-setters:v0.2 -- \
    "gcloud.core.project=$PROJECT_ID" \
    "ca-location=$CA_LOCATION"

kpt live init 06-cert-issuer --name cert-issuer --namespace inventory

kpt live apply 06-cert-issuer --reconcile-timeout 3m --output events
