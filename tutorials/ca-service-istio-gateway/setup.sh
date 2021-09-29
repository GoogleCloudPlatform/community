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

source ./01-cluster/create-gke-cluster.sh
source ./02-istio/install-istio.sh
./03-cert-manager/install-cert-manager.sh
source ./04-ca-service/configure-ca-service.sh
source ./05-ca-service-issuer/install-ca-service-issuer.sh
./06-cert-issuer/create-cert-issuer.sh
./07-sample-app/deploy-sample-app.sh
./08-verify-https/verify-https.sh
