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


locals {
  env = "dev"
}

provider "google" {
  project = var.project
}

module "pubsub" {
  source  = "../../modules/pubsub"
  
  topic              = "tf-topic"
  project            = "${var.project}"

  push_subscription = {
      name              = "alert-push-subscription"
      push_endpoint     = "${module.cloud_run_with_pubsub.url}"
      auth_account      = "${module.pubsub_service_account.service_account_email}"
  }
}

module "cloud_run_with_pubsub" {
  source  = "../../modules/cloud_run_with_pubsub"
  project = "${var.project}"
  
  pubsub_service_account_email = "${module.pubsub_service_account.service_account_email}"
}

data "google_project" "project" {}

# enable Pub/Sub to create authentication tokens in the project
resource "google_project_iam_binding" "project" {
  project = var.project
  role    = "roles/iam.serviceAccountTokenCreator"
  
  members = [
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  ]
}

module "pubsub_service_account" {
  source  = "../../modules/pubsub_service_account"
  project = var.project
}