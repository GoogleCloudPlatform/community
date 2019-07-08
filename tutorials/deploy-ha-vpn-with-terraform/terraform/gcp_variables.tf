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
 * Terraform variable declarations for GCP.
 */

variable gcp_credentials_file_path {
  description = "Specify the GCP credentials .json file."
  type = "string"
}

variable "gcp_project_id" {
  description = "Enter GCP Project ID."
  type = "string"
}

variable gcp_region {
  description = "Default to Iowa region."
  default = "us-central1"
}

variable network1 {
  default = "network-a"
}

variable network1_subnet1 {
  default = "central-subnet"
}

variable network1_subnet2 {
  default = "west-subnet"
}

variable subnet1_ip_cidr {
  default = "10.0.1.0/24"
}

variable subnet2_ip_cidr {
  default = "10.0.2.0/24"
}

variable ha_vpn_gateway {
  default = "ha-vpn-gw-a"
}

variable cloud_router {
  default = "router-a"
}

variable gcp_asn {
  default = "65001"
}

variable peer_asn {
  default = "65002"
}

variable peer_gw_name {
  default = "peer-gw"
}

variable peer_gw_int_0 {
  type = "string"
}

variable peer_gw_int_1 {
  type = "string"
}

variable tunnel_name_if0 {
  default = "tunnel-a-to-on-prem-if-0"
}

variable shared_secret {
  type = "string"
}

variable tunnel_name_if1 {
  default = "tunnel-a-to-on-prem-if-1"
}

variable router_int0 {
  default = "if-tunnel-a-to-on-prem-if-0"
}

variable router_int1 {
  default = "if-tunnel-a-to-on-prem-if-1"
}

variable router_int_name_0 {
  default = "bgp-peer-tunnel-a-to-on-prem-if-0"
}

variable router_int_name_1 {
  default = "bgp-peer-tunnel-a-to-on-prem-if-1"
}

variable bgp_peer_0 {
  default = "peer-a"
}

variable bgp_peer_1 {
  default = "peer-b"
}
