/*
 * Copyright 2019 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


/*
 * Terraform networking resources for GCP.
 */

resource "google_compute_network" "gcp-network" {
  name = "gcp-network"
  auto_create_subnetworks = "false"
}

resource "google_compute_network" "ha-vpn-test-network" {
  name                    = "${var.network1}"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
}

resource "google_compute_subnetwork" "network1-subnet1" {
  name   = "${var.network1_subnet1}"
  ip_cidr_range = "${var.subnet1_ip_cidr}"
  region = "${var.gcp_region}"
  network  = "${var.network1}"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

resource "google_compute_subnetwork" "network1-subnet2" {
  name   = "${var.network1_subnet2}"
  ip_cidr_range = "${var.subnet2_ip_cidr}"
  region = "${var.gcp_region}"
  network  = "${var.network1}"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create HA VPN gateway
resource "google_compute_ha_vpn_gateway" "ha_gateway1" {
  provider = "google-beta"
  region = "${var.gcp_region}"
  name     = "${var.ha_vpn_gateway}"
  network  = "${var.network1}"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create cloud router
resource "google_compute_router" "router-a" {
  name    = "${var.cloud_router}"
  network  = "${var.network1}"
  bgp {
    asn = "${var.gcp_asn}"
  }
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create external aka peer gateway
resource "google_compute_external_vpn_gateway" "external_gateway" {
  provider        = "google-beta"
  name            = "${var.peer_gw_name}"
  redundancy_type = "TWO_IPS_REDUNDANCY"
  description     = "An externally managed VPN gateway"
  interface {
    id = 0
    ip_address = "${var.peer_gw_int_0}"
  }
  interface {
    id = 1
    ip_address = "${var.peer_gw_int_1}"
  }
}

// Create first VPN tunnel
resource "google_compute_vpn_tunnel" "tunnel0" {
  provider         = "google-beta"
  name             = "${var.tunnel_name_if0}"
  region           = "${var.gcp_region}"
  vpn_gateway      = "${var.ha_vpn_gateway}"
  peer_external_gateway = "${var.peer_gw_name}"
  peer_external_gateway_interface = 0
  shared_secret    = "${var.shared_secret}"
  router           = "${var.cloud_router}"
  vpn_gateway_interface = 0
  depends_on = [google_compute_router.router-a,google_compute_ha_vpn_gateway.ha_gateway1,google_compute_external_vpn_gateway.external_gateway]
}

// Create second VPN tunnel
resource "google_compute_vpn_tunnel" "tunnel1" {
  provider         = "google-beta"
  name             = "${var.tunnel_name_if1}"
  region           = "${var.gcp_region}"
  vpn_gateway      = "${var.ha_vpn_gateway}"
  peer_external_gateway = "${var.peer_gw_name}"
  peer_external_gateway_interface = 1
  shared_secret    = "${var.shared_secret}"
  router           = "${var.cloud_router}"
  vpn_gateway_interface = 1
  depends_on = [google_compute_router.router-a,google_compute_ha_vpn_gateway.ha_gateway1,google_compute_external_vpn_gateway.external_gateway]
}

// Create first cloud router interface
resource "google_compute_router_interface" "router1_interface0" {
  provider   = "google-beta"
  name       = "${var.router_int0}"
  router     = "${var.cloud_router}"
  region     = "${var.gcp_region}"
  vpn_tunnel = "${var.tunnel_name_if0}"
  depends_on = [google_compute_router.router-a,google_compute_vpn_tunnel.tunnel0]
}

// Create first BGP peer
resource "google_compute_router_peer" "router1_peer0" {
  provider 		    = "google-beta"
  name                      = "${var.bgp_peer_0}"
  router                    = "${var.cloud_router}"
  region                    = "${var.gcp_region}"
  peer_asn                  = "${var.peer_asn}"
  advertised_route_priority = 100
  interface                 = "${var.router_int0}"
  depends_on = [google_compute_router.router-a,google_compute_router_interface.router1_interface0]
}

// Create second cloud router interface
resource "google_compute_router_interface" "router1_interface1" {
  provider   = "google-beta"
  name       = "${var.router_int1}"
  router     = "${var.cloud_router}"
  region     = "${var.gcp_region}"
  vpn_tunnel = "${var.tunnel_name_if1}"
  depends_on = [google_compute_router.router-a,google_compute_vpn_tunnel.tunnel1]
}

// Create second BGP peer
resource "google_compute_router_peer" "router1_peer1" {
  provider 		    = "google-beta"
  name                      = "${var.bgp_peer_1}"
  router                    = "${var.cloud_router}"
  region                    = "${var.gcp_region}"
  peer_asn                  = "${var.peer_asn}"
  advertised_route_priority = 100
  interface                 = "${var.router_int1}"
  depends_on = [google_compute_router.router-a,google_compute_router_interface.router1_interface1]
}
