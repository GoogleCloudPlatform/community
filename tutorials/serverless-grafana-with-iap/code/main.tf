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

locals {
  apis = ["iam.googleapis.com", "compute.googleapis.com", "run.googleapis.com", "apigateway.googleapis.com", "servicemanagement.googleapis.com", "servicecontrol.googleapis.com", "iap.googleapis.com", "sql-component.googleapis.com", "cloudapis.googleapis.com", "sqladmin.googleapis.com", "secretmanager.googleapis.com", "cloudresourcemanager.googleapis.com"]
}

data "google_project" "project" {
  project_id = var.project_id
}

resource "google_project_service" "project" {
  for_each           = toset(local.apis)
  project            = data.google_project.project.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_service_account" "grafana_sa" {
  account_id   = "grafana"
  display_name = "Service Account for Grafana"
  project      = data.google_project.project.project_id
}

resource "google_project_iam_member" "grafana_monitoring_viewer_role_assignment" {
  project = data.google_project.project.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.grafana_sa.email}"
}

resource "google_cloud_run_service" "default" {
  provider = google-beta
  name     = "grafana"
  location = var.region
  project  = data.google_project.project.project_id

  metadata {
    annotations = {
      "run.googleapis.com/ingress" : "internal-and-cloud-load-balancing"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.grafana_sa.email
      containers {
        image = "mirror.gcr.io/grafana/grafana:${var.grafana_version}"
        ports {
          name           = "http1"
          container_port = 8080
        }
        dynamic "env" {
          for_each = local.static_envs
          content {
            name  = env.key
            value = env.value
          }
        }
        env {
          name = "GF_DATABASE_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.secret.secret_id
              key  = "latest"
            }
          }
        }
        volume_mounts {
          name       = "datasource-volume"
          mount_path = "/etc/grafana/provisioning/datasources"
        }
        volume_mounts {
          name       = "dashboard-yaml-volume"
          mount_path = "/etc/grafana/provisioning/dashboards"
        }
        volume_mounts {
          name       = "dashboard-json-volume"
          mount_path = "/var/lib/grafana/dashboards/gcp"
        }
      }
      volumes {
        name = "datasource-volume"
        secret {
          secret_name = google_secret_manager_secret.datasource.secret_id
          items {
            key  = "latest"
            path = "cloud-monitoring.yaml"
          }
        }
      }
      volumes {
        name = "dashboard-yaml-volume"
        secret {
          secret_name = google_secret_manager_secret.dashboard-yaml.secret_id
          items {
            key  = "latest"
            path = "gclb.yaml"
          }
        }
      }
      volumes {
        name = "dashboard-json-volume"
        secret {
          secret_name = google_secret_manager_secret.dashboard-json.secret_id
          items {
            key  = "latest"
            path = "gclb.json"
          }
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.instance.connection_name
        "run.googleapis.com/client-name"        = "grafana"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.project,
    google_sql_database.database,
    google_sql_user.user,
    google_secret_manager_secret_iam_member.datasource-access,
    google_secret_manager_secret_iam_member.secret-access,
    google_secret_manager_secret_iam_member.dashboard-yaml-access,
    google_secret_manager_secret_iam_member.dashboard-json-access,
  ]
}

resource "google_cloud_run_service_iam_member" "allowAllUsers" {
  project  = data.google_project.project.project_id
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

locals {
  static_envs = {
    GF_LOG_LEVEL                  = "DEBUG"
    GF_SERVER_ROOT_URL            = "https://${var.domain}"
    GF_SERVER_HTTP_PORT           = "8080"
    GF_DATABASE_TYPE              = "mysql"
    GF_DATABASE_HOST              = "/cloudsql/${google_sql_database_instance.instance.connection_name}"
    GF_DATABASE_USER              = google_sql_user.user.name
    GF_DATABASE_NAME              = google_sql_database.database.name
    GF_AUTH_JWT_ENABLED           = "true"
    GF_AUTH_JWT_HEADER_NAME       = "X-Goog-Iap-Jwt-Assertion"
    GF_AUTH_JWT_USERNAME_CLAIM    = "email"
    GF_AUTH_JWT_EMAIL_CLAIM       = "email"
    GF_AUTH_JWT_JWK_SET_URL       = "https://www.gstatic.com/iap/verify/public_key-jwk"
    GF_AUTH_JWT_EXPECTED_CLAIMS   = "{\"iss\": \"https://cloud.google.com/iap\"}"
    GF_AUTH_JWT_AUTO_SIGN_UP      = "true"
    GF_USERS_AUTO_ASSIGN_ORG_ROLE = "Viewer"
    GF_USERS_VIEWERS_CAN_EDIT     = "true"
    GF_USERS_EDITORS_CAN_ADMIN    = "false"
  }
}

resource "google_secret_manager_secret" "datasource" {
  project   = data.google_project.project.project_id
  secret_id = "datasource-yml"
  replication {
    automatic = true
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "datasource-version-data" {
  secret      = google_secret_manager_secret.datasource.name
  secret_data = file("${path.module}/provisioning/datasources/cloud-monitoring.yaml")
}

resource "google_secret_manager_secret_iam_member" "datasource-access" {
  project    = data.google_project.project.project_id
  secret_id  = google_secret_manager_secret.datasource.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.grafana_sa.email}"
  depends_on = [
    google_secret_manager_secret.datasource, 
    google_secret_manager_secret_version.datasource-version-data
  ]
}


resource "google_secret_manager_secret" "dashboard-yaml" {
  project   = data.google_project.project.project_id
  secret_id = "dashboard-yaml"
  replication {
    automatic = true
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "dashboard-yaml-version-data" {
  secret      = google_secret_manager_secret.dashboard-yaml.name
  secret_data = file("${path.module}/provisioning/dashboards/gclb.yaml")
}

resource "google_secret_manager_secret_iam_member" "dashboard-yaml-access" {
  project    = data.google_project.project.project_id
  secret_id  = google_secret_manager_secret.dashboard-yaml.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.grafana_sa.email}"
  depends_on = [
    google_secret_manager_secret.dashboard-yaml, 
    google_secret_manager_secret_version.dashboard-yaml-version-data
  ]
}


resource "google_secret_manager_secret" "dashboard-json" {
  project   = data.google_project.project.project_id
  secret_id = "dashboard-json"
  replication {
    automatic = true
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_secret_manager_secret_version" "dashboard-json-version-data" {
  secret      = google_secret_manager_secret.dashboard-json.name
  secret_data = file("${path.module}/provisioning/dashboards/gclb.json")
}

resource "google_secret_manager_secret_iam_member" "dashboard-json-access" {
  project    = data.google_project.project.project_id
  secret_id  = google_secret_manager_secret.dashboard-json.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.grafana_sa.email}"
  depends_on = [
    google_secret_manager_secret.dashboard-json,
    google_secret_manager_secret_version.dashboard-json-version-data
  ]
}