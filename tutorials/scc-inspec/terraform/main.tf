terraform {
  required_version = ">= 0.12.0"
}

provider "google" {
  version = ">= 3.50.0"
  project = var.project_id
  region  = var.region
}

locals {
  function_runtime_sa_email = format("%s@%s.iam.gserviceaccount.com",
    var.function_runtime_sa_name, var.project_id)
}

// Create a Cloud Storage bucket to hold the InSpec reports
resource "google_storage_bucket" "bucket_inspec_reports" {
  project = var.project_id
  name = format("inspec-reports_%s", var.suffix)
  storage_class = "STANDARD"
  location  = var.region
  force_destroy = true
}

// give the Cloud Function runtime service account permission to read the reports bucket
resource "google_storage_bucket_iam_binding" "bucket_inspec_reports_binding" {
  bucket = google_storage_bucket.bucket_inspec_reports.name
  role = "roles/storage.admin"
  members = [
    format("serviceAccount:%s", local.function_runtime_sa_email)
  ]
}

// create a Cloud Storage bucket to hold the Cloud Functions src
resource "google_storage_bucket" "bucket_source_archives" {
  project = var.project_id
  name = format("source-archives_%s", var.suffix)
  storage_class = "STANDARD"
  location  = var.region
  force_destroy = true
}

// zip up the Cloud Functions source code
data "archive_file" "local_parser_src" {
  type        = "zip"
  source_dir  = "../reportParser"
  output_path = format("%s/parser_src.zip", var.local_output_path)
}

// upload the zipped source to the bucket
resource "google_storage_bucket_object" "gcs_parser_src" {
  name   = "parser_src.zip"
  bucket = google_storage_bucket.bucket_source_archives.name
  source = data.archive_file.local_parser_src.output_path
}

// deploy the Function
resource "google_cloudfunctions_function" "function_parser" {
  name = "inspec-scc"
  project = var.project_id
  region = var.region
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource = google_storage_bucket.bucket_inspec_reports.name
  }
  available_memory_mb = "512"
  entry_point = "on_finalize"
  runtime = "python38"
  service_account_email = local.function_runtime_sa_email
  source_archive_bucket = google_storage_bucket.bucket_source_archives.name
  source_archive_object = google_storage_bucket_object.gcs_parser_src.name
  environment_variables = {
    SCC_SOURCE = format("organizations/%s/sources/%s", var.org_id, var.source_id)
  }
}
