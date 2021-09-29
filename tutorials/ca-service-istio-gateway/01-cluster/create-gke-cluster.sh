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

gcloud services enable container.googleapis.com

CLUSTER_NAME=${CLUSTER_NAME:-istio-ingress-cert-manager-ca-service}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value core/project)}
ZONE=${ZONE:-us-central1-f}

gcloud container clusters create "$CLUSTER_NAME" \
    --enable-ip-alias \
    --num-nodes 4 \
    --release-channel regular \
    --scopes cloud-platform \
    --workload-pool "$PROJECT_ID.svc.id.goog" \
    --zone "$ZONE"

export CLUSTER_NAME
export PROJECT_ID
export ZONE

kpt fn eval 01-cluster --image gcr.io/kpt-fn/apply-setters:v0.2 -- "cluster-admin-user=$(gcloud config get-value core/account)"
kpt live init 01-cluster --name gke-cluster --namespace inventory
kpt live apply 01-cluster --reconcile-timeout 2m --output events
