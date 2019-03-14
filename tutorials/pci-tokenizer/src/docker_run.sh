#!/usr/bin/env bash
# Utility script to demonstrate deployment to a local docker server
# This script mounts ../config and makes it the default config location for the app.
# With this functionality, you can add a config/local.json file and override any settings.
# See ../README.md for license and more info
# Requires the environment variable TOKENIZER_DOCKER_IMAGE

if [ -z "$TOKENIZER_DOCKER_IMAGE" ]; then
	echo "Please define the env variable \$TOKENIZER_DOCKER_IMAGE to your Docker image server"
	echo "Example: myorg/gcp-pci-tokenizer"
	exit
fi

docker stop $APP
docker rm $APP
docker run \
  -d \
  --name $APP \
  -e TZ="America/Los_Angeles" \
  -e NODE_ENV="dev" \
  -p 443:443/tcp \
  -p 8080:80/tcp \
  -v `pwd`/config:/config \
  -e NODE_CONFIG_DIR="/config" \
  $TOKENIZER_DOCKER_IMAGE
