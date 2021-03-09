#!/usr/bin/python3

import os
from os import path

# Init the configs so they can be maintained from outside the container
def init_conf(conffile):
    print(f"Initializing conf file {conffile}")
    if os.path.exists(f"/etc/clamav-custom/{conffile}"):
        os.system(f"cp /etc/clamav-custom/{conffile} /etc/clamav/{conffile}")

init_conf("clamd.conf")
init_conf("freshclam.conf")

if os.path.exists("/tmp/clamscan.lock"):
    print("Cleaning up lock file from bad shutdown")
    os.remove("/tmp/clamscan.lock")

# Bootstrap the database if clamav is running for the first time
os.system("[ -f /data/main.cvd ] || freshclam")

# Run the update daemon
os.system("freshclam -d -c 6")

# Run clamav
os.system("clamd")
