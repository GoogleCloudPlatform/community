#!/usr/bin/env bash
# github ianmaddox/gcs-cf-tokenizer
# Docker container bootstrapping script. This script is called automatically when
# the docker container launches.
# This file is not used with Cloud Functions.
# See ../README.md for license and more info

CONTAINER_ALREADY_STARTED="/tokenizer/.firstrun_executed_flag"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    echo "-- First container startup --"

    cd /tmp
    curl -L https://www.npmjs.com/install.sh | sh

    cd /tokenizer
    git reset --hard HEAD
    git pull

    cd /tokenizer/config

    npm install
    ls -ltrha
    touch $CONTAINER_ALREADY_STARTED
else
    echo "-- Fetching latest code --"
    git pull
fi

node /tokenizer/src/server.js

#This command keeps the container running
tail -f /dev/null
