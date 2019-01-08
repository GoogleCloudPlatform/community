#!/usr/bin/env bash
# Utility script to streamline CF deployment
# See ../README.md for license and more info

SRC=$(dirname "`dirname \"$BASH_SOURCE\"/`")
gcloud beta functions deploy tokenize --runtime=nodejs8 --trigger-http --entry-point=tokenize --memory=256MB --source=$SRC
