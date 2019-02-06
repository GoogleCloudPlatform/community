#!/bin/bash

# Deletes devices from a GCP IoT registry.
#
# Usage:
#   ./createDevices.sh
#
# The deviceIds to delete are read from devicelist.csv in the ltk root directory.

function info {
  echo "LTK: $1"
}

while IFS=',' read deviceId rest; do

  gcloud iot devices delete $deviceId \
    --project=$LTK_TARGET_PROJECT_ID \
    --region=$LTK_TARGET_REGION \
    --registry=$LTK_TARGET_REGISTRY_ID \
    --quiet

done < $LTK_ROOT/devicelist.csv

# All the devices are deleted so delete this devicelist.
info "Devices deleted from GCP, deleting $LTK_ROOT/devicelist.csv"
rm $LTK_ROOT/devicelist.csv




