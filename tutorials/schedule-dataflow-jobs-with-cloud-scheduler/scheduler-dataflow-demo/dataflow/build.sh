#!/bin/bash
PROJECT=${GOOGLE_CLOUD_PROJECT}
BUCKET=${TF_ADMIN}
mvn compile exec:java \
           -Dexec.mainClass=DataflowDemoPipeline \
           -Dexec.args="--runner=DataflowRunner \
                        --project=${PROJECT} \
                        --stagingLocation=gs://${BUCKET}/staging \
                        --gcpTempLocation=gs://${BUCKET}/temp \
                        --region=us-central1 \
                        --templateLocation=gs://${BUCKET}/templates/dataflow-demo-template"

