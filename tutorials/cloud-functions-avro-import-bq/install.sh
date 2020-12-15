#!/bin/bash

# update trigger-resource with source bucket
gcloud beta functions deploy ToBigQuery_Stage --runtime nodejs12 --trigger-resource avro-import-source --trigger-event google.storage.object.finalize
