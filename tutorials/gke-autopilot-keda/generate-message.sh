#!/bin/sh
i=0
while [ $i -ne 100 ]
do
        i=$(($i+1))
        gcloud pubsub topics publish test-topic --message="Hello World $i" --project $GOOGLE_CLOUD_PROJECT
done