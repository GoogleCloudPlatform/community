# ##################################################
#  !!! Below resources are needed only if you are
#      hosting the app with cloud dns and 
#      external load balancer !!! 
# ##################################################

# ##################################################
# Cloud DNS 
# ##################################################

resource "google_dns_managed_zone" "three_tier_serverless_cloud_zone" {
  count = var.cloud_dns_enabled ? 1 : 0

  name     = var.cloud_dns_zone_name
  dns_name = var.cloud_dns_domain

  depends_on = [
    google_project_service.project["dns.googleapis.com"]
  ]
}

resource "google_dns_record_set" "three_tier_serverless_cloud_zone_a_record" {
  count = var.cloud_dns_enabled ? 1 : 0

  project      = var.project_id
  name         = var.cloud_dns_domain
  managed_zone = google_dns_managed_zone.three_tier_serverless_cloud_zone[0].name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.three_tier_serverless_external_ip[0].address]

  depends_on = [
    google_project_service.project["dns.googleapis.com"]
  ]
}

# ##################################################
# External IP Reservation 
# ##################################################

resource "google_compute_global_address" "three_tier_serverless_external_ip" {
  count = var.cloud_dns_enabled ? 1 : 0

  provider = google-beta

  project      = var.project_id
  address_type = "EXTERNAL"
  name         = "three-tier-serverless-external-ip"

  lifecycle {
    prevent_destroy = true
  }
}

# ##################################################
# SSL Cert
# ##################################################

resource "google_compute_ssl_policy" "three_tier_serverless_ssl_policy" {
  count = var.cloud_dns_enabled ? 1 : 0

  name            = "three-tier-serverless-ssl-policy"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}

resource "google_compute_managed_ssl_certificate" "three_tier_serverless_ssl_cert" {
  count = var.cloud_dns_enabled ? 1 : 0

  provider = google-beta
  name     = "three-tier-serverless-ssl-cert"

  managed {
    domains = [var.cloud_dns_domain]
  }
}

# ##################################################
#  Forwarding Rule from Internet 
# ##################################################

resource "google_compute_global_forwarding_rule" "three_tier_https" {
  count = var.cloud_dns_enabled ? 1 : 0

  provider              = google-beta
  project               = var.project_id
  name                  = "three-tier-https"
  target                = google_compute_target_https_proxy.three_tier_serverless_https_proxy[0].self_link
  ip_address            = google_compute_global_address.three_tier_serverless_external_ip[0].address
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL"
  depends_on = [
    google_compute_target_https_proxy.three_tier_serverless_https_proxy[0],
    google_compute_global_address.three_tier_serverless_external_ip[0]
  ]
}

# ##################################################
#  HTTPS Proxy with SSL Certificate
# ##################################################

resource "google_compute_target_https_proxy" "three_tier_serverless_https_proxy" {
  count = var.cloud_dns_enabled ? 1 : 0

  provider = google-beta
  name     = "three-tier-serverless-https-proxy"
  url_map  = google_compute_url_map.three_tier_serverless_url_map[0].id
  ssl_certificates = [
    google_compute_managed_ssl_certificate.three_tier_serverless_ssl_cert[0].name
  ]
  ssl_policy = google_compute_ssl_policy.three_tier_serverless_ssl_policy[0].self_link

  depends_on = [
    google_compute_ssl_policy.three_tier_serverless_ssl_policy[0],
    google_compute_managed_ssl_certificate.three_tier_serverless_ssl_cert[0]
  ]
}

# ##################################################
#  URL Map to Backend Service 
# ##################################################

resource "google_compute_url_map" "three_tier_serverless_url_map" {
  count = var.cloud_dns_enabled ? 1 : 0

  project         = var.project_id
  name            = "three-tier-serverless-url-map"
  default_service = google_compute_backend_service.three_tier_serverless_backend_service[0].self_link

  depends_on = [
    google_compute_backend_service.three_tier_serverless_backend_service[0]
  ]
}

# ##################################################
# Cloud Run Serverless Network Endpoint Group (NEG)
# ##################################################

resource "google_compute_region_network_endpoint_group" "three_tier_serverless_cloudrun_neg" {
  count = var.cloud_dns_enabled ? 1 : 0

  name                  = "three-tier-serverless-cloudrun-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.location
  cloud_run {
    service = "amazing-employees-frontend-service"
  }
}

# ##################################################
# Backend Service to Cloud Run NEG 
# ##################################################

resource "google_compute_backend_service" "three_tier_serverless_backend_service" {
  count = var.cloud_dns_enabled ? 1 : 0

  provider   = google-beta
  name       = "three-tier-serverless-backend-service"
  enable_cdn = false
  protocol   = "HTTPS"
  backend {
    group = google_compute_region_network_endpoint_group.three_tier_serverless_cloudrun_neg[0].id
  }

  iap {
    oauth2_client_id     = "646023161501-3ka6o0vihgmhr684226emotjfoskbrug.apps.googleusercontent.com"
    oauth2_client_secret = "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"
  }

  depends_on = [
    google_compute_region_network_endpoint_group.three_tier_serverless_cloudrun_neg[0]
  ]
}
  