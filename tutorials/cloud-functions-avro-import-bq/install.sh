#!/bin/bash

#update trigger-resource with source buckety
gcloud beta functions deploy ToBigQuery_Stage --trigger-resource avro-import-source --trigger-event google.storage.object.finalize
