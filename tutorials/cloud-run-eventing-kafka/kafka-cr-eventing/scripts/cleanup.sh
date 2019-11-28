#!/usr/bin/env bash

### this is meant to cleanup 

echo "***** Deleting Scheduled Job *****"
gcloud beta scheduler jobs delete currency-job

echo "***** Deleting Confluent Cloud Kafka Cluster and Topics *****"

ccloud login --url https://confluent.cloud
ccloud kafka topic delete cloudevents
ccloud kafka cluster delete ${CONFLUENT_ID}


echo "***** Deleting Kubernetes Cluser *****"

gcloud container clusters delete ${CLUSTER_NAME}