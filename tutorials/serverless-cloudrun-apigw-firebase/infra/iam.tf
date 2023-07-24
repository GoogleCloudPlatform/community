data "google_project" "project" {
}

# ##################################################
# Frontend Service Account
# ##################################################

resource "google_service_account" "frontend_service_account" {
  project      = var.project_id
  account_id   = "employees-frontend-sa"
  display_name = "employees-frontend-sa"
  description  = "Service account for Amazing Employees Frontend"
}

# ##################################################
# Backend Service Account
# ##################################################

resource "google_service_account" "backend_service_account" {
  project      = var.project_id
  account_id   = "employees-backend-sa"
  display_name = "employees-backend-sa"
  description  = "Service account for Amazing Employees Backend"
}

resource "google_project_iam_member" "backend_iam_member" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend_service_account.email}"
}

resource "google_project_iam_member" "backend_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.backend_service_account.email}"
}

# ##################################################
# Cloud Build Service Account
# ##################################################

resource "google_project_iam_member" "cloud_build_sa" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}