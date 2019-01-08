#!/usr/bin/env bash
# github ianmaddox/gcs-cf-tokenizer
# Utility script to streamline CF deployment
# See ../README.md for license and more info

SRC=$(dirname "`dirname \"$BASH_SOURCE\"/`")
gcloud beta functions deploy detokenize --runtime=nodejs8 --trigger-http --entry-point=detokenize --memory=256MB --source=$SRC
