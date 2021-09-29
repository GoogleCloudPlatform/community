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

REGION=${REGION:-us-central1}
ZONE=${ZONE:-us-central1-f}
CLUSTER_NAME=${CLUSTER_NAME:-istio-ingress-cert-manager-ca-service}

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value core/project)}
GSA_NAME=${GSA_NAME:-cert-manager-ca-service-issuer}
GSA=$GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com
KSA=${KSA:-ksa-google-cas-issuer}

CA_LOCATION=${CA_LOCATION:-us-central1}
ROOT_CA_POOL=${ROOT_CA_POOL:-root-ca-pool-tutorial}
ROOT_CA=${ROOT_CA:-root-ca-tutorial}
SUBORDINATE_CA_POOL=${SUBORDINATE_CA_POOL:-subordinate-ca-pool-tutorial}
SUBORDINATE_CA=${SUBORDINATE_CA:-subordinate-ca-tutorial}

gcloud container clusters delete "$CLUSTER_NAME" --zone "$ZONE" --async --quiet

gcloud privateca pools remove-iam-policy-binding "$SUBORDINATE_CA_POOL" \
    --location "$CA_LOCATION" \
    --member "serviceAccount:$GSA" \
    --role roles/privateca.certificateRequester

gcloud privateca subordinates disable "$SUBORDINATE_CA" --location "$CA_LOCATION" --pool "$SUBORDINATE_CA_POOL" --quiet
gcloud privateca subordinates delete "$SUBORDINATE_CA" --location "$CA_LOCATION" --pool "$SUBORDINATE_CA_POOL" --ignore-active-certificates --quiet

gcloud privateca roots disable "$ROOT_CA" --location "$CA_LOCATION" --pool "$ROOT_CA_POOL" --quiet
gcloud privateca roots delete "$ROOT_CA" --location "$CA_LOCATION" --pool "$ROOT_CA_POOL" --ignore-active-certificates --quiet

gcloud iam service-accounts remove-iam-policy-binding "$GSA" \
    --member "serviceAccount:$PROJECT_ID.svc.id.goog[cert-manager/$KSA]" \
    --role roles/iam.workloadIdentityUser

gcloud iam service-accounts delete "$GSA" --quiet

gcloud compute addresses delete istio-ingress-gateway-ilb --region "$REGION" --quiet

gcloud compute instances delete cas-tutorial-vm --zone "$ZONE" --quiet
