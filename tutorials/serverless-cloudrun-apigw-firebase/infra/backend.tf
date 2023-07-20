resource "google_api_gateway_api" "api" {
  provider = google-beta
  api_id   = "employees-api"
}

resource "google_api_gateway_api_config" "api_cfg" {
  provider      = google-beta
  api           = google_api_gateway_api.api.api_id
  api_config_id = "employees-config"

  openapi_documents {
    document {
      path     = "spec.yaml"
      contents = base64encode(templatefile("configs/api-gateway--espv2-definition.yml.tmpl", { url = data.google_cloud_run_service.run_service.status[0].url }))
    }
  }
  gateway_config {
    backend_config {
      google_service_account = google_service_account.backend_service_account.email
    }
  }

  depends_on = [
    google_project_service.project["apigateway.googleapis.com"]
  ]
}

resource "google_api_gateway_gateway" "api_gw" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.api_cfg.id
  gateway_id = "employee-gateway"
  region     = var.location
}

data "google_cloud_run_service" "run_service" {
  name     = "amazing-employees-backend-service"
  location = var.location
}
