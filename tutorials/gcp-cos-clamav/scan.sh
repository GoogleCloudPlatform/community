#!/usr/bin/env /bin/sh
# Perform a scan, but only if one isn't already in progress
LOCK="/tmp/clamscan.lock"

if [ -f "$LOCK" ];then
  echo "Scan already in progress. Aborting."
  exit
else
  touch $LOCK
  echo `date` Starting scan
  clamdscan --multiscan /host-fs
  rm $LOCK
fi
