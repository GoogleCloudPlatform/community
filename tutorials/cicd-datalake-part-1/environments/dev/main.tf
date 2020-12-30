# Copyright 2019 Google LLC
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

# cicd-datalake-part-1

terraform {
  required_version = ">= 0.12.0"
}


locals {
  env = "dev"
}

provider "google" {
  project = "${var.project_id}"
  region = "${var.region}"
  zone = "${var.region}-a" 
  version = "~> 2.18.0"
}

resource "random_id" "random_suffix" {
  byte_length = 4
}

locals {
  gcs_bucket_name = "tmp-dir-bucket-${random_id.random_suffix.hex}-${local.env}"
}

// [START gcs-buckets-block]
resource "google_storage_bucket" "tmp_dir_bucket" {
  name = "${local.gcs_bucket_name}"
  storage_class = "REGIONAL"
  location  = "${var.region}"
  project = "${var.project_id}"
  force_destroy = "true"
}

resource "google_bigquery_dataset" "default" {
  project                     = "${var.project_id}"
  dataset_id                  = "${local.env}_datalake_demo"
  friendly_name               = "${local.env}_datalake_demo"
  description                 = "This is the BQ dataset for running the datalake demo"
  location                    = "US"
  default_table_expiration_ms = 3600000
}

resource "google_dataflow_job" "dataflow_job" {
  project               = "${var.project_id}"
  region                = "${var.region}"
  zone                  = "${var.region}-a"
  name                  = "${local.env}_datalake_cicd_batch"
  on_delete             = "cancel"
  max_workers           = 8
  template_gcs_path     = "gs://dataflow-templates/latest/GCS_Text_to_BigQuery"
  temp_gcs_location     = "gs://${local.gcs_bucket_name}/tmp_dir"
  service_account_email = "${var.service_account_email}"
  parameters = {
    javascriptTextTransformFunctionName ="transform"
    JSONPath               = "gs://${var.source_gcs_bucket}/bq_schema.json"
    javascriptTextTransformGcsPath = "gs://${var.source_gcs_bucket}/etl.js"
    inputFilePattern       = "gs://${var.source_gcs_bucket}/cc_records.csv"
    outputTable            = "${var.project_id}:${google_bigquery_dataset.default.dataset_id}.sample_userdata"
    bigQueryLoadingTemporaryDirectory = "gs://${local.gcs_bucket_name}/tmp_dir1"
  }
  depends_on = [google_storage_bucket.tmp_dir_bucket]
}
