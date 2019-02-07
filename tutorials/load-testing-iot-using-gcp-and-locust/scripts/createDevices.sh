#!/bin/bash

# Creates devices in a GCP IoT registry.
#
# Usage:
#   ./createDevices.sh MIN_SEQ MAX_SEQ
#
#   MIN_SEQ is sequence number of first device to create
#   MAX_SEQ is sequence number of last device to create
#
# The deviceIds and private keys are written to devicelist.csv in the ltk root directory.
#
# To create an initial device population, set:
#   MIN_SEQ to 1
#   MAX_SEQ to the desired number of devices
#
# To add more devices to an existing device population, set:
#   MIN_SEQ to the next highest unused device sequence number
#   MAX_SEQ to the total desired number of devices after the new devices are added

MIN_SEQ=$1
MAX_SEQ=$2

function info {
  echo "LTK: $1"
}

info "creating devices LTK$(printf "%05d" $MIN_SEQ) through LTK$(printf "%05d" $MAX_SEQ)"
for i in `seq $MIN_SEQ $MAX_SEQ`; do

  deviceId=LTK$(printf "%05d" $i)

  openssl genrsa -out private_key.pem 2048 1>/dev/null 2>&1
  openssl rsa -in private_key.pem -pubout -out public_key.pem 1>/dev/null 2>&1

  gcloud iot devices create $deviceId \
    --project=$LTK_TARGET_PROJECT_ID \
    --region=$LTK_TARGET_REGION \
    --registry=$LTK_TARGET_REGISTRY_ID \
    --public-key path=public_key.pem,type=rsa-pem
  if [[ $? -eq 0 ]]; then
    csvline="$deviceId,`cat private_key.pem`"
    echo $csvline >> $LTK_ROOT/devicelist.csv
  fi

  rm private_key.pem
  rm public_key.pem
  
done



