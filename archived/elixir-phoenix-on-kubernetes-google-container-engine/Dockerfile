# Copyright 2017 Google LLC
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


# This is a sample Dockerfile for packaging an Elixir Phoenix application
# as a Docker image. It builds a Distillery release and installs it on
# Alpine Linux. The final image launches the application on port 8080. It
# requires the project ID to be passed in the project_id build arg.
#
# This Dockerfile includes two stages and requires Docker 17.05 or later.
#
# To adapt this Dockerfile to your app, you may need to customize the app_name
# and phoenix_subdir build arguments, as outlined below.


################################################################################
# BUILD STAGE
#
# Builds the app, does a Brunch build to build the assets, and creates a
# release. This stage uses the official Alpine Linux - Elixir base image, and
# installs a few additional build tools such as Node.js.

FROM elixir:alpine


##############################################################################
## Build arguments. Modify these to adapt this Dockerfile to your app.      ##
## Alternatively, you may specify --build-arg when running `docker build`.  ##

## The name of your Phoenix application.                                    ##
ARG app_name=hello

## The subdirectory of the Phoenix application within the toplevel project. ##
## If your project is an umbrella project, this should be the relative path ##
## to the Phoenix application, e.g. "apps/hello_web". If this is a simple   ##
## project, this should be "."                                              ##
ARG phoenix_subdir=.

## The build environment. This is usually prod, but you might change it if  ##
## you have staging environments.                                           ##
ARG build_env=prod

## End build arguments.                                                     ##
##############################################################################


# Set up build environment.
ENV MIX_ENV=${build_env} \
    TERM=xterm

# Set the build directory.
WORKDIR /opt/app

# Install build tools needed in addition to Elixir:
# NodeJS is used for Webpack builds of Phoenix assets.
# Hex and Rebar are needed to get and build dependencies.
RUN apk update \
    && apk --no-cache --update add nodejs npm \
    && mix local.rebar --force \
    && mix local.hex --force

# Copy the application files into /opt/app.
COPY . .

# Build the application.
RUN mix do deps.get, compile

# Build assets by running a Webpack build and Phoenix digest.
# If you are using a different mechanism for asset builds, you may need to
# alter these commands.
RUN cd ${phoenix_subdir}/assets \
    && npm install \
    && ./node_modules/webpack/bin/webpack.js --mode production \
    && cd .. \
    && mix phx.digest

# Create the release, and move the artifacts to well-known paths so the
# runtime image doesn't need to know the app name. Specifically, the binary
# is renamed to "start_server", and the entire release is moved into
# /opt/release.
RUN mix release ${app_name} \
    && mv _build/${build_env}/rel/${app_name} /opt/release \
    && mv /opt/release/bin/${app_name} /opt/release/bin/start_server


################################################################################
# RUNTIME STAGE
#
# Creates the actual runtime image. This is based on a the Alpine Linux base
# image, with only the minimum dependencies for running ERTS and the Cloud SQL
# Proxy.

FROM alpine:latest

# The Google Cloud project ID must be provided via a --build-arg.
ARG project_id

# Install dependencies. Bash and OpenSSL are required for ERTS. Also install
# certificates needed to communicate with Google Cloud APIs over HTTPS.
RUN apk update \
    && apk --no-cache --update add bash ca-certificates openssl-dev

# Install the Cloud SQL Proxy in /usr/local/bin/. Also create the directory
# /tmp/cloudsql where SQL connection sockets will be kept.
RUN mkdir -p /usr/local/bin \
    && wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy \
    && chmod +x /usr/local/bin/cloud_sql_proxy \
    && mkdir -p /tmp/cloudsql

# This is the runtime environment for a Phoenix app.
# It listens on port 8080, and runs in the prod environment.
ENV PORT=8080 \
    GCLOUD_PROJECT_ID=${project_id} \
    REPLACE_OS_VARS=true
EXPOSE ${PORT}

# Set the install directory. The app will run from here.
WORKDIR /opt/app

# Obtain the built application release from the build stage.
COPY --from=0 /opt/release .

# Start the server. This first starts the Cloud SQL Proxy in the background,
# then runs the release in the foreground. This will work for simple
# deployments, but a more robust deployment might run the Cloud SQL Proxy in a
# sidecar container.
CMD (/usr/local/bin/cloud_sql_proxy \
      -projects=${GCLOUD_PROJECT_ID} -dir=/tmp/cloudsql &); \
    exec /opt/app/bin/start_server start
