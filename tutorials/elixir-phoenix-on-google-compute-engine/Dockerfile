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
# to build an OTP release that will run on Debian 8. It is intended to build
# releases that can be deployed to Debian 8 images on Google Cloud Platform.
#
# To use, build this image and give it a tag `$IMAGE_NAME`. Then from the mix
# project directory, execute:
#
#     docker run --rm -it -v $(pwd):/app $IMAGE_NAME
#
# This process assumes that only `mix release` is required to build a release.
# If any other steps are needed, for example digesting assets, those must be
# executed first. Just remember that any steps involving compiling code or
# packaging the release must be done in the Docker container.


# The elixir base image is currently based on Debian 9 "Stretch" and can
# be used to build OTP releases with a Stretch-compatible ERTS.
FROM elixir:latest

# Set the build directory. The `mix release` command will be run from here.
# When running the container, you should mount the host project directory at
# this location.
WORKDIR /app

# Make sure rebar and hex are installed. If your build process has other
# dependencies, install them here.
RUN mix local.rebar --force && mix local.hex --force

# Ensure MIX_ENV is set to "prod" when releasing, so compilation is properly
# optimized.
ENV MIX_ENV=prod REPLACE_OS_VARS=true TERM=xterm

# Set the default build command. You can change or override it to suit your
# project's requirements.
CMD ["mix", "release", "--env=prod", "--executable", "--verbose"]
