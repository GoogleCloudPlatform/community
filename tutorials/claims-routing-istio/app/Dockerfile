# Copyright 2020 Google LLC
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

# [START claims_routing_identity_platform_app_dockerfile]
FROM golang:1.14 as build
ENV CGO_ENABLED=0
ENV GO111MODULE=on
WORKDIR /workspace
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY pkg ./pkg
RUN go build -v -mod=readonly -installsuffix "static" ./cmd/app

FROM gcr.io/distroless/base-debian10:debug-nonroot
WORKDIR /app
COPY --from=build /workspace/app ./
COPY static ./static
COPY templates ./templates
ENTRYPOINT ["/app/app"]
# [END claims_routing_identity_platform_app_dockerfile]
