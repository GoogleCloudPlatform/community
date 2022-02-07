/**
 * Copyright 2021 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

resource "google_cloud_run_service" "default" {
  for_each = toset(var.regions)

  provider = google-beta
  name     = "multi-regional-service-${each.key}"
  location = each.key
  project  = data.google_project.project.project_id

  metadata {
    annotations = {
      "run.googleapis.com/ingress" : "internal-and-cloud-load-balancing"
    }
    labels = {
        "deployment-region" : "${each.key}"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.my_global_app_sa.email
      containers {
        image = "gcr.io/cloudrun/hello"
        ports {
          name           = "http1"
          container_port = 8080
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "run.googleapis.com/client-name"        = "multi-regional-service"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.project,
    google_service_account.my_global_app_sa,
  ]
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  for_each = google_cloud_run_service.default
  location    = each.value.location
  project     = each.value.project
  service     = each.value.name

  policy_data = data.google_iam_policy.noauth.policy_data

  depends_on = [
    google_project_service.project
  ]
}