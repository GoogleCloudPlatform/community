#!/usr/bin/python3
import os

# Forward the FIM env vars
os.system("echo FIM_PATH=$FIM_PATH >> /root.crontab")
os.system("echo FIM_THREADS=$FIM_THREADS >> /root.crontab")
os.system("echo FIM_SYMLINKS=$FIM_SYMLINKS >> /root.crontab")
os.system("echo FIM_DATDIR=$FIM_DATDIR >> /root.crontab")
os.system("echo FIM_LOGDIR=$FIM_LOGDIR >> /root.crontab")
os.system("echo FIM_IGNORE_FILE=$FIM_IGNORE_FILE >> /root.crontab")
os.system("echo FIM_IGNORE_PATH=$FIM_IGNORE_PATH >> /root.crontab")
os.system("echo FIM_IGNORE_REGEX=$FIM_IGNORE_REGEX >> /root.crontab")
# Run a filesystem scan every day unless one is in progress.
os.system("echo \"$(($RANDOM % 60))   $(($RANDOM % 24))   *   *   *   /fim/scan.sh 2>&1  >> /logs/fimcron.log \" >> /root.crontab")
os.system("fcrontab -u root /root.crontab")
os.system("rm /root.crontab")

# Perform a bootup Scan
os.system("/fim/scan.sh &")

# Run cron
os.system("/usr/sbin/fcron -f -d")
