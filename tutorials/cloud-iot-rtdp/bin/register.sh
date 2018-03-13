#!/bin/bash
for i in {1..30}
do
gcloud iot devices create device$i --project=$PROJECT --region=$REGION --registry=$REGISTRY --public-key path=rsa_cert.pem,type=rs256
done
