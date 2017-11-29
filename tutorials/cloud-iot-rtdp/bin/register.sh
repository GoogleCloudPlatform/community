#!/bin/bash
for i in {1..30}
do
gcloud beta iot devices create device$i --project=$PROJECT --region=us-central1 --registry=$REGISTRY --public-key path=rsa_cert.pem,type=rs256
done

