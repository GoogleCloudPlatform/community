variable "project_id" {}
variable "suffix" {}
variable "org_id" {}
variable "source_id" {}

variable "region" {
  default = "us-central1"
}

variable "function_runtime_sa_name" {
  default = "gcf-scc-sa"
}

variable "local_output_path" {
  default = "tmp"
}
