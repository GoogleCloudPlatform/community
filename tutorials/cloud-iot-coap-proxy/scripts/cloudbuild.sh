#! /bin/bash
# Simple script to create a container using Cloud Build

# Find dir of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR/../proxy

# If using OSX tar
export COPY_EXTENDED_ATTRIBUTES_DISABLE=true
export COPYFILE_DISABLE=true

TARBALL=/tmp/coap-proxy.tar.gz

tar -c -z --exclude='.git' --exclude='._*' --exclude='.DS_Store' -f $TARBALL .

gcloud builds submit --config ../scripts/cloudbuild.yaml $TARBALL

