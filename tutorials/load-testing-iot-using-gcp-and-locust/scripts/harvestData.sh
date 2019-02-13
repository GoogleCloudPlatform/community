#!/bin/bash

# Fetches performance data from GCP after a test.
#
# Usage:
#   ./harvestData.sh RUN_DIR START_TIME END_TIME
#
#   RUN_DIR is the name of directory in LTK_ROOT/runs to use for the harvested data (will be created if needed)
#   START_TIME is the start time of the test (beginnning of harvest window)
#   END_TIME is the end time of the test (end of harvest window)
#
#   START_TIME and END_TIME are in UTC time in the format 2019-01-04T20:00:00Z
#
# NOTE: This script can require a log run time to download the logs from GCP.
# 
# Two reports are produced:
#   Driver times - frequency distribution of driver-measured latencies
#   Function times - frequency distribution of function execution times
#
#   Distributions are bucketed to 100msec increments.

RUN_DIR=$1
START_TIME=$2
END_TIME=$3

function info {
  echo "LTK: $1"
}

RESULTS_DIR=$LTK_ROOT/runs/$RUN_DIR
info "Creating $RESULTS_DIR (if it does not exist)"
mkdir $LTK_ROOT/runs >/dev/null 2>&1 || true
mkdir $RESULTS_DIR >/dev/null 2>&1 || true

cd $RESULTS_DIR
rm driver_times.csv >/dev/null 2>&1 || true
rm driver_times_binned.csv >/dev/null 2>&1 || true
rm driver_time_frequencies.out >/dev/null 2>&1 || true
rm function_times.csv >/dev/null 2>&1 || true
rm function_times_binned.csv >/dev/null 2>&1 || true
rm function_time_frequencies.out >/dev/null 2>&1 || true

# Get driver latencies.

info "Setting gcloud command line config to project $LTK_DRIVER_PROJECT_ID"
gcloud config set project $LTK_DRIVER_PROJECT_ID 1>/dev/null 2>&1 || \
  errorExit "Unable to set projectId"

info "Fetching driver log"
gcloud logging read \
  "resource.type=container AND timestamp>=\"$START_TIME\" AND timestamp<=\"$END_TIME\" AND \"*** ON_MESSAGE\"" \
  --format="value(textPayload)" \
  > driver.log

# Get cloud function latencies.

info "Setting gcloud command line config to project $LTK_TARGET_PROJECT_ID"
gcloud config set project $LTK_TARGET_PROJECT_ID 1>/dev/null 2>&1 || \
  errorExit "Unable to set projectId"

info "Fetching application (function) log"
gcloud logging read \
  "resource.type=cloud_function AND timestamp>=\"$START_TIME\" AND timestamp<=\"$END_TIME\" AND (\"*** sending\" OR \"Function execution took\")" \
  --format="value(labels.execution_id,textPayload)" \
  > function.log

# Put the driver and function times into 100msec bins for reporting frequency distributions.

# driver line format
# [2019-01-04 21:08:53,492] locust-worker-0/INFO/stdout: *** ON_MESSAGE LTK00017 0x7f79587c47d0 payload 200 at 154663613324524 ack latency 247 msec
#
# functionline format (may mant be adjacent but "*** sending" will be before "Function execution took" for a given executionId)
# 347857302674139 Function execution took 883 ms, finished with status: 'ok'

# Extract needed fields from the driver.log download.

awk NF driver.log | awk -v OFS=',' '{print $6,$11,$14}' > driver_times.csv

# For each line in the driver_extract, bin the driver time.
info "Binning driver times"
while IFS=',' read deviceId requestId driverTime; do
  if [[ $(( driverTime % 100 )) -eq 0 ]]; then
    driverTimeBucket=$driverTime
  else
    driverTimeBucket=$(( (driverTime/100 + 1) * 100 ))
  fi
    csvline=$deviceId,$requestId,$driverTime,$driverTimeBucket
    echo $csvline >> driver_times_binned.csv
done < driver_times.csv

# Extract needed fields from the function.log download.

grep "Function execution took" function.log | awk -v OFS=',' '{print $1,$5}' > function_times.csv

# For each line in the function_extract, bin the function time.
info "Binning function times"
while IFS=',' read executionId functionTime; do
  if [[ $(( functionTime % 100 )) -eq 0 ]]; then
    functionTimeBucket=$functionTime
  else
    functionTimeBucket=$(( (functionTime/100 + 1) * 100 ))
  fi
    csvline=$executionId,$functionTime,$functionTimeBucket
    echo $csvline >> function_times_binned.csv
done < function_times.csv

# Get frequency distributions of driver times and function times.

awk -F',' '{print $4}' driver_times_binned.csv | sort -n | uniq -c | sort -n -k2 | awk '{print $2, $1}' > driver_time_frequencies.out
awk -F',' '{print $3}' function_times_binned.csv | sort -n | uniq -c | sort -n -k2 | awk '{print $2, $1}' > function_time_frequencies.out

# Display frequency distributions and miscellaneous stats.

echo "**********************************"
echo "Driver Time Frequency Distribution"
echo ""
cat driver_time_frequencies.out
echo ""
echo "**********************************"
echo "Function Time Frequency Distribution"
echo ""
cat function_time_frequencies.out









