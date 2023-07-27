#!/usr/bin/env bash
# Usage:
# Mount the filesystem you wish to scan in $FIM_PATH
# Launch the container and let the scans run
# Monitor log files for unexpected changes

# This is the primary mover for basic-fim. You can add more paths to the IGNORE
# array below. All paths are based in the root of the Docker server
# Set the env variable $FIM_THREADS to control how many parallel processes are used to calculate file hashes
# Paths to ignore in $FIM_PATH
# Env vars:
#  FIM_PATH         [/host-fs]   Path to monitor
#  FIM_THREADS      [4]          Number of threads to use when hashing
#  FIM_SYMLINKS     [false]      Follow symlinks found in FIM_PATH
#  FIM_DATDIR       [/root/.fim] Data file directory
#  FIM_LOGDIR       [/logs]      Log file directory
#  FIM_IGNORE_FILE  []           Glob file ignore filter
#  FIM_IGNORE_PATH  []           Glob path ignore filter

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
DATE_FORMAT="+%Y-%m-%d %H:%M:%S"
DEFAULT_FIM_THREADS=4

THREADS="${FIM_THREADS:=$DEFAULT_FIM_THREADS}"
DATDIR="${FIM_DATDIR:=/root/.fim}"
LOGDIR="${FIM_LOGDIR:=/logs}"
FOLLOW_SYMLINKS=`[ "$FIM_SYMLINKS" == true ] && echo "-L" || echo "-P"`
WATCH_PATH="${FIM_PATH:=/host-fs}"

TMPDIR=$DATDIR/tmp

FINGERPRINTS=$DATDIR/.base
LOCKFILE=$DATDIR/fim.lock

LOGFILE=$LOGDIR/fimscan.log
ERRFILE=$LOGDIR/fimscan.err

MANIFEST=$TMPDIR/basemanifest.tmp
HASHQUEUE=$TMPDIR/fim.tmp
FINGERPRINTSTMP=$TMPDIR/base.tmp
TMPMANIFEST=$TMPDIR/manifest.tmp
FAILEDFILES=$TMPDIR/failed.tmp

# Prepare the workspace
mkdir -p $DATDIR $TMPDIR $LOGDIR

# Fail fast if already running
if [ -f "$LOCKFILE" ];then
  echo "A scan is already in progress." | tee -a $LOGFILE
  exit
fi
touch $LOCKFILE
echo "" | tee -a $LOGFILE

# Clean up any leftovers
rm -f $TMPDIR/*.tmp

if [ ! -z "$FIM_IGNORE_FILE" ]; then
	IGNORE_FILE=" -name "$FIM_IGNORE_FILE" -prune -o "
fi

if [ ! -z "$FIM_IGNORE_PATH" ]; then
	IGNORE_PATH=" -path "$FIM_IGNORE_PATH" -prune -o "
fi

# Construct the file finder command
FIND="find $FOLLOW_SYMLINKS $WATCH_PATH $IGNORE_PATH"
for DIR in "${IGNORE[@]}"; do
    FIND=$(echo $FIND -path $WATCH_PATH$DIR -prune -o)
done
FIND="$FIND $IGNORE_FILE -type f -print"

if [ ! -f "$FINGERPRINTS" ];then
  echo $(date "$DATE_FORMAT") Executing first run | tee -a $LOGFILE
  touch $MANIFEST
else
  # Collect a full map of files
  echo $(date "$DATE_FORMAT") Gathering file manifest| tee -a $LOGFILE
  # Rebuild the original manifest based on the keyfile
  sed -E 's/^.*  (.*)$/\1/' $FINGERPRINTS | sort > $MANIFEST
fi
echo $FIND
# Perform a manifest scan
$FIND | sort > $HASHQUEUE
cp $HASHQUEUE $TMPMANIFEST # HASHQUEUE and manifest can diverge after this point

# Compare to previous scan
if [ -f "$FINGERPRINTS" ];then
  cp /dev/null $HASHQUEUE # Existing fingerprints file. Wipe the hash queue

  # Find changes in the file manifest
  NEWFILES=$(diff -U0 $MANIFEST $TMPMANIFEST | grep ^+/ |sed -E 's/^\+//g')
  MISSINGFILES=$(diff -U0 $MANIFEST $TMPMANIFEST | grep ^-/ |sed -E 's/^\-//g')

  if [ "$MISSINGFILES" != "" ]; then
    REMOVEMISSING=""
    while IFS= read -r MISSINGFILE; do
      echo "REMOVED: $MISSINGFILE" | tee -a $LOGFILE
		MISSINGFILE=$(echo $MISSINGFILE | sed -E 's/(["!$'\''])/\\\1/g')
      REMOVEMISSING=$(echo "$REMOVEMISSING | grep -v \"$MISSINGFILE\"")
    done <<< $"$MISSINGFILES"
    REMOVEMISSING="cat \$FINGERPRINTS $REMOVEMISSING"
    eval $REMOVEMISSING >> $FINGERPRINTSTMP
    cp $FINGERPRINTSTMP $FINGERPRINTS
  fi

  if [ "$NEWFILES" != "" ]; then
    while IFS= read -r NEWFILE; do
      echo "NEW: $NEWFILE" | tee -a $LOGFILE
	   echo "$NEWFILE" >> $HASHQUEUE # Just fingerprint the new files
    done <<< "$NEWFILES"
  fi

  echo $(date "$DATE_FORMAT") Starting fingerprint comparison | tee -a $LOGFILE

  sha256sum -c $FINGERPRINTS 2>>$ERRFILE \
    | grep -vE ": OK$" \
    | tee -a $LOGFILE $FAILEDFILES > /dev/null

  echo $(date "$DATE_FORMAT") Comparison scan complete | tee -a $LOGFILE
  if [ -s "$FAILEDFILES" ]; then
    UPDATEFAILED=""

    while IFS= read -r CHANGEDFILE; do
		CHANGEDFILE=$(echo $CHANGEDFILE | sed -E 's/(.*):[^:]+$/\1/')
		echo "CHANGED: $CHANGEDFILE" | tee -a $LOGFILE
      CHANGEDFILE=$(echo "$CHANGEDFILE" | sed -E 's/(["$])/\\\1/g')
      UPDATEFAILED=$(echo "$UPDATEFAILED | grep -v \"$CHANGEDFILE\"")
    done <<< $(cat $FAILEDFILES)

    echo $(date "$DATE_FORMAT") "Fingerprinting changed files" | tee -a $LOGFILE
    UPDATEFAILED="cat \$FINGERPRINTS $UPDATEFAILED"
    eval $UPDATEFAILED >> $FINGERPRINTSTMP

   cat $FAILEDFILES \
    | awk -F ":" '{ print $1 }' \
    | xargs -I% -P$THREADS -d '\n' sha256sum "%" 2>>$ERRFILE \
    | tee -a $FINGERPRINTSTMP $LOGFILE
    rm $FAILEDFILES
  fi
fi

if [ -s $HASHQUEUE ]; then
  echo $(date "$DATE_FORMAT") "Fingerprinting new files" | tee -a $LOGFILE
  touch $FINGERPRINTSTMP
  xargs -a $HASHQUEUE -I% -P$THREADS -d '\n' sha256sum "%" 2>>$ERRFILE | tee -a $FINGERPRINTSTMP $LOGFILE
fi

if [ -s $FINGERPRINTSTMP ]; then
  echo $(date "$DATE_FORMAT") "Finalizing scan" | tee -a $LOGFILE
  sort -k2 $FINGERPRINTSTMP | uniq -f 1 > $FINGERPRINTS
  chmod 600 $FINGERPRINTS
  rm $FINGERPRINTSTMP
fi

rm $LOCKFILE
rm -f $TMPDIR/*.tmp
echo $(date "$DATE_FORMAT") Scan complete | tee -a $LOGFILE
