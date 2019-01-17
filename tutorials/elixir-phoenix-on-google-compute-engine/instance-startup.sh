#!/bin/sh

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -ex

# Create a directory for the release. OTP requires $HOME to be set.
export HOME=/app
mkdir -p ${HOME}
cd ${HOME}

# Download the release specified in the instance metadata.
RELEASE_URL=$(curl \
  -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/release-url" \
  -H "Metadata-Flavor: Google")
gsutil cp ${RELEASE_URL} hello-release
chmod 755 hello-release

# Download the Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 \
  -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Start the Cloud SQL Proxy, using the project obtained from project metadata.
mkdir /tmp/cloudsql
PROJECT_ID=$(curl \
  -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" \
  -H "Metadata-Flavor: Google")
./cloud_sql_proxy -projects=${PROJECT_ID} -dir=/tmp/cloudsql &

# Start the application as a daemon on port 8080.
PORT=8080 ./hello-release start
