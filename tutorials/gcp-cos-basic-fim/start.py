#!/usr/bin/python3

import os

# Run a filesystem scan every day unless one is in progress.
os.system("echo \"$(($RANDOM % 60))   $(($RANDOM % 24))   *   *   *   /scan.sh 2>&1  >> /logs/fimscan.log \" > /root.crontab")
os.system("fcrontab -u root /root.crontab")
os.system("rm /root.crontab")

# Perform a bootup Scan
os.system("/scan.sh")

# Run cron
os.system("/usr/sbin/fcron -f -d")
