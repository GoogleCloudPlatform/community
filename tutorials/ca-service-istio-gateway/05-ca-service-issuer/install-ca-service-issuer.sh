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

GSA_NAME=${GSA_NAME:-cert-manager-ca-service-issuer}
gcloud iam service-accounts create "$GSA_NAME" \
    --display-name "CA Service issuer for cert-manager"
GSA=$GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com
export GSA

gcloud privateca pools add-iam-policy-binding "$SUBORDINATE_CA_POOL" \
    --location "$CA_LOCATION" \
    --member "serviceAccount:$GSA" \
    --role roles/privateca.certificateRequester

CA_SERVICE_ISSUER_VERSION=${CA_SERVICE_ISSUER_VERSION:-v0.5.3}
curl --location "https://github.com/jetstack/google-cas-issuer/releases/download/${CA_SERVICE_ISSUER_VERSION}/google-cas-issuer-${CA_SERVICE_ISSUER_VERSION}.yaml" --output 05-ca-service-issuer/ca-service-issuer.yaml

KSA=$(kubectl apply -f 05-ca-service-issuer/ca-service-issuer.yaml --dry-run=client -o jsonpath='{.items[*].spec.template.spec.serviceAccountName}')
export KSA

gcloud iam service-accounts add-iam-policy-binding "$GSA" \
    --member "serviceAccount:$PROJECT_ID.svc.id.goog[cert-manager/$KSA]" \
    --role roles/iam.workloadIdentityUser

kustomize cfg annotate 05-ca-service-issuer \
    --kind ServiceAccount \
    --name "$KSA" \
    --namespace cert-manager \
    --kv "iam.gke.io/gcp-service-account=$GSA"

kpt live init 05-ca-service-issuer --name ca-service-issuer-controller --namespace inventory
kpt live apply 05-ca-service-issuer --reconcile-timeout 5m --output events
