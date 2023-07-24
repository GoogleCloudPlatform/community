resource "google_artifact_registry_repository" "docker_repo" {
  location      = "us-east1"
  repository_id = "amazing-employees"
  description   = "Docker repository for Amazing Employees Application "
  format        = "DOCKER"

  depends_on = [google_project_service.project["artifactregistry.googleapis.com"]]
}
