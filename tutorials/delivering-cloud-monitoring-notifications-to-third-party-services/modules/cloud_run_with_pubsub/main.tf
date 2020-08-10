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


resource "google_project_service" "run" {
  service  = "run.googleapis.com"
  project  = var.project
}

resource "google_cloud_run_service" "cloud_run_pubsub_service" {
  name     = "cloud-run-pubsub-service"
  location = "us-west1"
  project  = var.project

  template {
    spec {
      containers {
        image = "gcr.io/${var.project}/cloud-run-pubsub-service:latest"
      }
    }
    metadata {
      name = "cloud-run-pubsub-service-${uuid()}"
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.run]
}

resource "google_cloud_run_service_iam_binding" "binding" {
  location  = google_cloud_run_service.cloud_run_pubsub_service.location
  project   = var.project
  service   = google_cloud_run_service.cloud_run_pubsub_service.name
  role      = "roles/run.invoker"
  members   = [
    "serviceAccount:${var.pubsub_service_account_email}"
  ]
}