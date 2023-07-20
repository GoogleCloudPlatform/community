variable "project_id" {
  description = "Project ID of the GCP project where resources will be deployed"
  type        = string
}

variable "location" {
  description = "Location (region) where resources will be deployed"
  type        = string
  default     = "us-east1"
}

variable "cloud_dns_enabled" {
  description = "Feature Flag to enable/disable Cloud DNS. Set to false if deploying to personal Google Cloud account to reduce cost."
  type        = bool
  default     = true
}

variable "cloud_dns_zone_name" {
  description = "Zone Name of Cloud DNS."
  type        = string
  default     = "three-tier-serverless-cloud-zone"
}

variable "cloud_dns_domain" {
  description = "Cloud DNS."
  type        = string
  default     = "serverlessdemo.gcp.cbm.matter.cloud."
}