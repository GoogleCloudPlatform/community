data "google_project" "project" {
}

# ##################################################
# Terraform Service Account
# ##################################################

resource "google_service_account" "tf_service_account" {
  project      = var.project_id
  account_id   = "terraform-service-account"
  display_name = "terraform-service-account"
  description  = "Service account for Managing Terraform"
}

resource "google_project_iam_member" "tf_iam_member" {
  project = var.project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.tf_service_account.email}"
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

# ##################################################
# IAP Roles
# NOTE: add members as needed on this list   
# ##################################################

resource "google_project_iam_binding" "iap_members" {
  for_each = toset([
    "roles/iap.tunnelResourceAccessor",
    "roles/iap.httpsResourceAccessor",
  ])
  project = var.project_id
  role    = each.key

  members = [
    "user:maksood_mohiuddin@mckinsey.com",
    "user:marco_marulli@mckinsey.com",
    "user:thomas_neff@mckinsey.com",
    "user:alex_dequevedo@mckinsey.com",
    "user:michael_johnson@mckinsey.com",
    "user:suresh_bikmal@mckinsey.com",
    "user:mike_west@mckinsey.com",
    "user:marcellus_miles@mckinsey.com",
    "user:john_roach@mckinsey.com"
  ]
}

resource "google_project_iam_member" "iap_sa" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-iap.iam.gserviceaccount.com"
}