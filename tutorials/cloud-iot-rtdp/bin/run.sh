#!/bin/bash
cd ../streaming

mvn exec:java -Dexec.mainClass="com.google.cloud.solutions.rtdp.Simulator" -Dexec.args="-project_id=$PROJECT -registry_id=$REGISTRY -device_id=device -private_key_file=./rsa_private_pkcs8 -algorithm=RS256 -cloud_region=$REGION -num_messages=1000000 -lat=35.660 -lng=139.728"
