#!/bin/bash

mvn compile exec:java \
           -Dexec.mainClass=DataflowDemoPipeline \
           -Dexec.args="--runner=DataflowRunner \
                        --project=${PROJECT} \
                        --stagingLocation=gs://${BUCKET}/staging \
                        --gcpTempLocation=gs://${BUCKET}/temp \
                        --region=${REGION} \
                        --templateLocation=gs://${BUCKET}/templates/dataflow-demo-template"
