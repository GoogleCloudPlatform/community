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

mkdir -p "${HOME}/bin"
ISTIO_VERSION=${ISTIO_VERSION:-$(curl -sSL https://api.github.com/repos/istio/istio/releases | jq -r '.[].name' | grep '^Istio 1\.11' | grep -Ev 'alpha|beta|rc' | sort -k2rV | head -n1 | cut -d' ' -f2)}
curl -L "https://github.com/istio/istio/releases/download/${ISTIO_VERSION}/istioctl-${ISTIO_VERSION}-$(go env GOOS)-$(go env GOARCH).tar.gz" | tar -zxC "${HOME}/bin" istioctl
PATH=${HOME}/bin:$PATH
export PATH

istioctl manifest generate --filename 02-istio/istio-control-plane-operator.yaml --output 02-istio/control-plane

kpt live init 02-istio/control-plane --name istio-control-plane --namespace inventory
kpt live apply 02-istio/control-plane --reconcile-timeout 10m --output events

REGION=${REGION:-us-central1}
LOAD_BALANCER_IP=$(gcloud compute addresses create \
    istio-ingress-gateway-ilb \
    --region "$REGION" \
    --subnet default \
    --format 'value(address)')
export REGION
export LOAD_BALANCER_IP

kpt fn eval 02-istio --image gcr.io/kpt-fn/apply-setters:v0.2 -- "load-balancer-ip=$LOAD_BALANCER_IP"

istioctl manifest generate --filename 02-istio/istio-ingressgateway-operator.yaml --output 02-istio/ingressgateway

kpt live init 02-istio/ingressgateway --name istio-ingressgateway --namespace inventory
kpt live apply 02-istio/ingressgateway --reconcile-timeout 10m --output events
