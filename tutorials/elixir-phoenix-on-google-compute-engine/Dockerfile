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


# This is a sample Docker image providing an environment for using Distillery
# to build an OTP release that will run on Debian 9. It is intended to build
# releases that can be deployed to Debian 9 images on Google Cloud Platform.
#
# To use, build this image and give it a tag (for example, `my-image-name`).
#
#     docker build -t my-build-image .
#
# Then copy the executable release file `/app/start_release` out of the image.
#
#     container_id=$(docker create my-build-image)
#     docker cp ${container_id}:/app/start_release start_release
#     docker rm ${container_id}
#
# To adapt this Dockerfile to your app, you may need to customize the app_name
# and phoenix_subdir build arguments, as outlined below.


# The elixir base image is currently based on Debian 9 "Stretch" and can
# be used to build OTP releases with a Stretch-compatible ERTS.
FROM elixir:latest


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


# Set up the build environment.
ENV MIX_ENV=${build_env} \
    TERM=xterm
WORKDIR /app

# Additional installations needed for building (hex, rebar, and nodejs).
RUN apt-get update -y \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y -q --no-install-recommends nodejs \
    && mix local.rebar --force \
    && mix local.hex --force

# Copy the application in. Note that you should generally use a .dockerignore
# file to omit build artifacts from your development environment (e.g. the
# "_build" and "deps" directories, as well as "assets/node_modules" and
# "priv/static" for assets).
COPY . .

# Compile the Elixir app.
RUN mix do deps.get, compile

# Build and digest your assets. This example assumes you are using webpack. You
# may need to modify this if you are using a different system.
RUN cd ${phoenix_subdir}/assets \
    && npm install \
    && ./node_modules/webpack/bin/webpack.js --mode production \
    && cd .. \
    && mix phx.digest

# Create the release using distillery.
RUN mix distillery.release --env=${build_env} --executable --verbose

# Move the standalone executable to a well-known location so it can be copied
# out of the image.
RUN mv _build/${build_env}/rel/${app_name}/bin/${app_name}.run /app/start_release
