#!/usr/bin/env bash
# github ianmaddox/gcs-cf-tokenizer
# Utility script to streamline CF deployment
# See ../README.md for license and more info

SRC=`dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"`
gcloud functions deploy authenticated_cf --runtime=nodejs8 --trigger-http --entry-point=example_auth --memory=256MB --source=$SRC
