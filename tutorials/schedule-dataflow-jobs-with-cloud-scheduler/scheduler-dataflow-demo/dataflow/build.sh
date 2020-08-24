#!/bin/bash

mvn compile exec:java \
           -Dexec.mainClass=DataflowDemoPipeline \
           -Dexec.args="--runner=DataflowRunner \
                        --project=${PROJECT} \
                        --stagingLocation=${BUCKET}/staging \
                        --gcpTempLocation=${BUCKET}/temp \
                        --region=us-central1 \
                        --templateLocation=${BUCKET}/templates/dataflow-demo-template"
