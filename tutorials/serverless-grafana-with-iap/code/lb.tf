resource "google_compute_region_network_endpoint_group" "cloud_run_neg" {
  name                  = "cloud-run-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project = data.google_project.project.project_id
  cloud_run {
    service = google_cloud_run_service.default.name
  }
}

module "lb-http" {
  source  = "GoogleCloudPlatform/lb-http/google//modules/serverless_negs"
  version = "~> 5.1"
  name    = "tf-cr-lb"
  project = data.google_project.project.project_id

  ssl                             = true
  managed_ssl_certificate_domains = [ var.domain ]
  https_redirect                  = true

  backends = {
    default = {
      description = null
      groups = [
        {
          group = google_compute_region_network_endpoint_group.cloud_run_neg.id
        }
      ]
      enable_cdn              = false
      security_policy         = google_compute_security_policy.api-policy.id
      custom_request_headers  = null
      custom_response_headers = null

      iap_config = {
        enable               = true
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      log_config = {
        enable      = false
        sample_rate = null
      }
    }
  }

  depends_on = [
    google_project_service.project
  ]
}

resource "google_compute_security_policy" "api-policy" {
  provider = google-beta
  name = "api-policy"
  project = data.google_project.project.project_id
  
  adaptive_protection_config {
    layer_7_ddos_defense_config {
        enable = true
    }
  }
}

resource "google_iap_client" "project_client" {
  display_name = "LB Client"
  brand        =  "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}" 

  depends_on = [
    google_project_service.project
  ]
}

output "external_ip" {
    value = module.lb-http.external_ip
}
