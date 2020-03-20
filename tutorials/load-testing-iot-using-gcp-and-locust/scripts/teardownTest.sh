#!/bin/bash

# Deletes the GCP resources set up by setupTest.sh.
# This script should be run at the completion of a test to delete the GKE cluster to avoid billing charges.
#
# Usage:
#   ./teardownTest.sh

function info {
  echo "LTK: $1"
}

function errorExit {
  info "ERROR: $1"
  exit 1
}

### Make sure we are pointing to the correct GCP project.

info "Setting gcloud command line config to project $LTK_DRIVER_PROJECT_ID"
gcloud config set project $LTK_DRIVER_PROJECT_ID 1>/dev/null 2>&1 || \
  errorExit "Unable to set projectId"

# Make sure kubectl is pointing to the driver cluster before we start deleting kubernetes objects.
info "Setting kubectl context to existing cluster."
gcloud container clusters get-credentials ltk-driver --zone $LTK_DRIVER_ZONE

### Clean up kubernetes.

info "Deleting pod for worker"
kubectl delete sts locust-worker >/dev/null 2>&1 || true
info "Deleting service for master"
kubectl delete svc locust-master >/dev/null 2>&1 || true
info "Deleting pod for master"
kubectl delete deployment locust-master >/dev/null 2>&1 || true

### Delete the GKE cluster.

info "Deleting cluster for driver"
if [ `gcloud container clusters list | grep ltk-driver | wc -l` -eq 1 ]; then
  info "Deleting GKE cluster, please be patient."
  gcloud container clusters delete ltk-driver --zone $LTK_DRIVER_ZONE --quiet || \
    errorExit "Unable to delete cluster"
fi

info "Test teardown complete"


