terraform {
  required_providers {
    google = {
      source = "hashicorp/google-beta"
    }
  }

  backend "gcs" {
    bucket = "f06a2c1ff1e18fb2-bucket-tfstate"
    prefix = "three-tier-app"
  }
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}
