#!/usr/bin/python3

import os
from os import path

# Init the configs so they can be maintained from outside the container
def init_conf(conffile):
    if not os.path.exists(f"/etc/clamav/{conffile}"):
        print(f"Initializing conf file {conffile}")
        if os.path.exists(f"/etc/clamav-custom/{conffile}"):
            os.system(f"cp /etc/clamav-custom/{conffile} /etc/clamav/{conffile}")

init_conf("clamd.conf")
init_conf("freshclam.conf")
init_conf("crontab")

if os.path.exists("/tmp/clamscan.lock"):
    print("Cleaning up lock file from bad shutdown")
    os.remove("/tmp/clamscan.lock")

# If no user provided crontab, schedule a filesystem scan to kick off each hour at a random minute.
if not os.path.exists(f"/etc/clamav/crontab"):
    os.system("echo \"$(($RANDOM % 60))   *   *   *   *   /scan.sh > /proc/1/fd/1 2>&1\" > /etc/clamav/crontab")

os.system("cp /etc/clamav/crontab /root.crontab")
os.system("fcrontab -u root /root.crontab")
os.system("rm /root.crontab")

# Bootstrap the database if clamav is running for the first time
os.system("[ -f /data/main.cvd ] || freshclam")

# Run the update daemon
os.system("freshclam -d -c 6")

# Run cron
os.system("/usr/sbin/fcron -d")

# Run clamav
os.system("clamd")
