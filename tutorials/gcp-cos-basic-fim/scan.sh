#!/usr/bin/env bash
# This is the primary mover for basic-fim. You can add more paths to the IGNORE
# array below. All paths are based in the root of the Docker server
IGNORE=(
  '/dev'
  '/sys'
  '/proc'
  '/tmp'
  '/run'
  '/home'
  '/mnt/stateful_partition/home'
  '/mnt/stateful_partition/var/lib/cni'
  '/mnt/stateful_partition/var/lib/docker/containers'
  '/mnt/stateful_partition/var/lib/docker/image'
  '/mnt/stateful_partition/var/lib/docker/overlay2'
  '/mnt/stateful_partition/var/lib/docker/network'
  '/mnt/stateful_partition/var/lib/docker/volumes'
  '/mnt/stateful_partition/var/lib/dockershim'
  '/mnt/stateful_partition/var/lib/kubelet/pods'
  '/mnt/stateful_partition/var/lib/metrics'
  '/mnt/stateful_partition/var/lib/update_engine/prefs'
  '/mnt/stateful_partition/var/log'
  '/mnt/stateful_partition/var_overlay'
  '/var/lib/cni'
  '/var/lib/docker/containers'
  '/var/lib/docker/image'
  '/var/lib/docker/network'
  '/var/lib/docker/overlay2'
  '/var/lib/docker/volumes'
  '/var/lib/dockershim'
  '/var/lib/kubelet/plugins'
  '/var/lib/kubelet/pods'
  '/var/lib/metrics'
  '/var/lib/update_engine/prefs'
  '/var/log'
  '/log/journal'
  )

LOGDIR=/logs
LOGFILE=$LOGDIR/scan.log
ERRFILE=$LOGDIR/scan.err
TMPMANIFEST=/tmp/.manifest.tmp
MANIFEST=/root/.manifest
FINGERPRINTS=/root/.base
FINGERPRINTSTMP=/tmp/.base.tmp
LOCKFILE=/tmp/fim.lock
TMPFILE=/tmp/fim.tmp
FAILEDFILES=/tmp/failed.tmp

# Fail fast if already running
if [ -f "$LOCKFILE" ];then
  echo "A scan is already in progess."
  exit
fi
touch $LOCKFILE
echo "" | tee -a $LOGFILE

# Construct the file finder command
FIND="find -P /host-fs"
for DIR in "${IGNORE[@]}"; do
    FIND=$(echo $FIND -path /host-fs$DIR -prune -o)
done
FIND="$FIND -type f -print"

if [ ! -f "$FINGERPRINTS" ];then
  echo `date` Executing first run | tee -a $LOGFILE
fi

# Collect a full map of files
echo `date` Gathering file manifest | tee -a $LOGFILE

# Perform a manifest scan and create an archive copy
$FIND > $TMPFILE
#cp $TMPFILE $LOGDIR/manifest-`date +%s`.scan
cp $TMPFILE $TMPMANIFEST # tmpfile and manifest can diverge after this point

# Compare to previous scan
if [ -f "$FINGERPRINTS" ];then

  # Find changes in the file manifest
  NEWFILES=$(diff -U0 $MANIFEST $TMPMANIFEST | grep ^+/ |sed -E 's/^\+//g')
  MISSINGFILES=$(diff -U0 $MANIFEST $TMPMANIFEST | grep ^-/ |sed -E 's/^\-//g')

  if [ "$MISSINGFILES" != "" ]; then
    echo `date` "Missing files:" | tee -a $LOGFILE
    echo $MISSINGFILES | xargs -n1 | tee -a $LOGFILE
    echo `date` "Removing missing files from manifest" | tee -a $LOGFILE
    REMOVEMISSING=
    for MISSINGFILE in `echo $MISSINGFILES | xargs -n1`; do
      REMOVEMISSING=$(echo "$REMOVEMISSING | grep -v \"$MISSINGFILE\"")
      echo "$MISSINGFILE: REMOVED" | tee -a $LOGFILE
    done
    REMOVEMISSING="cat \$FINGERPRINTS $REMOVEMISSING"
    eval $REMOVEMISSING > $FINGERPRINTSTMP
    cp $FINGERPRINTSTMP $FINGERPRINTS
  fi

  echo `date` Starting fingerprint comparison | tee -a $LOGFILE
    sha256sum -c $FINGERPRINTS 2>$ERRFILE \
    | grep -vE ": OK$" \
    | tee -a $LOGFILE $FAILEDFILES
  echo `date` Comparison scan complete | tee -a $LOGFILE

  if [ "$NEWFILES" != "" ]; then
    echo `date` "New files found:" | tee -a $LOGFILE
    echo $NEWFILES | xargs -n1 | tee -a $LOGFILE
    echo $NEWFILES | xargs -n1 > $TMPFILE # We only want to fingerprint the new files
  else
    cp /dev/null $TMPFILE
  fi

  if [ -s "$FAILEDFILES" ]; then
    #echo `date` "Failed files:" | tee -a $LOGFILE
    #cat $FAILEDFILES | cut -d ":" -f 1 | tee -a $LOGFILE
    echo `date` "Updating fingerprint on failed files" | tee -a $LOGFILE
    UPDATEFAILED=
    for FAILEDFILE in `cat $FAILEDFILES | cut -d ":" -f 1`; do
      UPDATEFAILED=$(echo "$UPDATEFAILED | grep -v \"$FAILEDFILE\"")
    done
    UPDATEFAILED="cat \$FINGERPRINTS $UPDATEFAILED"
    eval $UPDATEFAILED > $FINGERPRINTSTMP
    cp $FINGERPRINTSTMP $FINGERPRINTS
    chmod 600 $FINGERPRINTS 2> /dev/null
    cat $FAILEDFILES \
    | xargs sha256sum 2>$ERRFILE \
    | tee -a $FINGERPRINTS $LOGFILE
    rm $FAILEDFILES
  fi
fi

if [ -s $TMPFILE ]; then
  echo `date` "Fingerprinting new files" | tee -a $LOGFILE
  chmod 600 $FINGERPRINTS 2> /dev/null
  cat $TMPFILE \
    | xargs sha256sum 2>$ERRFILE \
    | tee -a $FINGERPRINTS
  chmod 400 $FINGERPRINTS
fi

mv $TMPMANIFEST $MANIFEST
rm $LOCKFILE $TMPFILE
echo `date` Scan complete | tee -a $LOGFILE
