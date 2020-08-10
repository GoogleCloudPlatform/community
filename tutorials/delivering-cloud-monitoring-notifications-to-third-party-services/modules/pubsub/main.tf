# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


resource "google_pubsub_topic" "tf" {
  name    = var.topic
  project = var.project
}

resource "google_pubsub_subscription" "push" {
  name = var.push_subscription.name
  topic = google_pubsub_topic.tf.name
  
  push_config {
    push_endpoint = var.push_subscription.push_endpoint
    oidc_token {
      service_account_email = var.push_subscription.auth_account
    }
  }
}