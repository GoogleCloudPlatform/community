# resource "random_id" "bucket_prefix" {
#   byte_length = 8
# }

# resource "google_storage_bucket" "tf_state" {
#   name          = "${random_id.bucket_prefix.hex}-bucket-tfstate"
#   force_destroy = false
#   location      = "US"
#   storage_class = "STANDARD"

#   uniform_bucket_level_access = true # Required by organizational policy constraint
#   public_access_prevention    = "enforced"

#   logging {
#     log_bucket = "f06a2c1ff1e18fb2-bucket-tfstate"
#   }

#   versioning {
#     enabled = true
#   }
# }

resource "google_artifact_registry_repository" "docker_repo" {
  location      = "us-east1"
  repository_id = "amazing-employees"
  description   = "Docker repository for Amazing Employees Application "
  format        = "DOCKER"

  depends_on = [google_project_service.project["artifactregistry.googleapis.com"]]
}
