#!/bin/bash
cd ../streaming

mvn compile exec:java -Dexec.mainClass=com.google.cloud.solutions.rtdp.Converter -Dexec.args="--project=$PROJECT --stagingLocation=gs://$BUCKET/temp --topic=$TOPIC --runner=DataflowRunner --streaming=true --numWorkers=1 --zone=$ZONE --workerMachineType=n1-standard-1"
