provider "google" {
  version = "~> 2.20"
  project = var.project_id
}

# Use this data source to get project details. For more information see API.
# https://www.terraform.io/docs/providers/google/d/google_project.html

data "google_project" "project" {}
resource "google_cloud_scheduler_job" "scheduler" {
  name = "scheduler-demo"
  schedule = "0 0 * * *"
  # This needs to be us-central1 even if the app engine is in us-central.
  # You will get a resource not found error if just using us-central.
  region = var.region

  http_target {
    http_method = "POST"
    uri = "https://dataflow.googleapis.com/v1b3/projects/${var.project_id}/locations/${var.region}/templates:launch?gcsPath=gs://${var.bucket}/templates/dataflow-demo-template"
    oauth_token {
      service_account_email = google_service_account.cloud-scheduler-demo.email
    }

    # need to encode the string
    body = base64encode(<<-EOT
    {
      "jobName": "test-cloud-scheduler",
      "parameters": {
        "region": "${var.region}",
        "autoscalingAlgorithm": "THROUGHPUT_BASED",
      },
      "environment": {
        "maxWorkers": "10",
        "tempLocation": "gs://${var.bucket}/temp",
        "zone": "${var.region}-a",
        "serviceAccountEmail": "${google_service_account.cloud-scheduler-demo.email}"
      }
    }
EOT
    )
  }
}

resource "google_service_account" "cloud-scheduler-demo" {
  account_id = "scheduler-dataflow-demo"
  display_name = "A service account for running dataflow from cloud scheduler"
}

resource "google_project_iam_member" "cloud-scheduler-dataflow-admin" {
  project = var.project_id
  role = "roles/dataflow.admin"
  member = "serviceAccount:${google_service_account.cloud-scheduler-demo.email}"
}

resource "google_project_iam_member" "cloud-scheduler-dataflow-worker" {
  project = var.project_id
  role = "roles/dataflow.worker"
  member = "serviceAccount:${google_service_account.cloud-scheduler-demo.email}"
}

