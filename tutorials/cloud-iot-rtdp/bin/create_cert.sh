#!/bin/bash
openssl req -x509 -newkey rsa:2048 -keyout rsa_private.pem -nodes -out rsa_cert.pem -subj "/CN=unused"
mv rsa_private.pem ../streaming/.
cd ../streaming
openssl pkcs8 -outform der -in rsa_private.pem -topk8 -nocrypt -out rsa_private_pkcs8
rm rsa_private.pem
