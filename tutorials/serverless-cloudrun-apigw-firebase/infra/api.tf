# Enable APIs

resource "google_project_service" "project" {
  for_each = toset([
    "iam.googleapis.com",
    "storage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "identitytoolkit.googleapis.com",
    "apigateway.googleapis.com",
    "servicecontrol.googleapis.com",
    "dns.googleapis.com",
    "certificatemanager.googleapis.com",
    "run.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}
