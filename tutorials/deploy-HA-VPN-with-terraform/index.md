---
title: Deploy HA VPN with Terraform
description: Deploy full GCP envrionment used in HA VPN interop guides with Terraform.
author: ashishverm
tags: terraform, ha vpn,
date_published: 2019-07-06
---

This tutorial demonstrates how to deploy High Availability VPN resources on Google Cloud Platform
used in interop guides with Terraform.

## Objectives

Create HA VPN with [1-peer-2-address](https://cloud.google.com/vpn/docs/concepts/topologies#1-peer-2-addresses) topology
on Google Cloud Platform.

## Before you begin

This guide assumes you are familiar with Terraform. Instructions provided in this guide
are based on the GCP envrionment depicted in HA VPN interop guides.

See [getting-started-on-gcp-with-terraform](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/getting-started-on-gcp-with-terraform/index.md)
to setup your Terraform envrionment for Google Cloud Platform.

Ensure you have service account with sufficient permissions to deploy resources
used in this tutorial.

## Set up the environment

Below variables are setup as per the values used in HA VPN interop guides.
Change the variable based on your envrionment.

```
sh
export TF_PROJECT=vpn-guide
export TF_CREDS=CREDENTIALS_FILE.json
export TF_NETWORK=network-a
export TF_SUBNET_A=subnet-a-central
export TF_SUBNET_B=subnet-a-west
export TF_CIDR_A=10.0.1.0/24
export TF_CIDR_B=10.0.2.0/24
export TF_HA_VPN_GW_NAME=ha-vpn-gw-a
export TF_CLOUD_ROUTER_NAME=router-a
export TF_EXT_VPN_GW_NAME=peer-gw
export TF_REDUNDANCY_TYPE=TWO_IPS_REDUNDANCY
export TF_PEER_INT_IF_0=209.119.81.225
export TF_PEER_INT_IF_1=209.119.81.226
export TF_VPN_TUN_NAME_0=tunnel-a-to-on-prem-if-0
export TF_SHARED_SECRET=mysharedsecret
export TF_CLOUD_ROUTER_INT_0=if-tunnel-a-to-on-prem-if-0
export TF_CLOUD_ROUTER_INT_1=if-tunnel-a-to-on-prem-if-1
```

## Use Terraform to deploy full GCP envrionment used in HA VPN interop guides

```
// Configure the Google Cloud provider
provider "google" {
 credentials = "${file("CREDENTIALS_FILE.json")}"
 project     = "cpe-vpn-testing"
 region      = "us-central1"
}

// Configure beta provider
provider "google-beta" {
  credentials = "${file("CREDENTIALS_FILE.json")}"
  project     = "cpe-vpn-testing"
  region      = "us-central1"
}

// Create VPC network
resource "google_compute_network" "ha-vpn-test-network" {
  name 			  = "network-a"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
}

// Create subnets
resource "google_compute_subnetwork" "central-subnet" {
  name   = "subnet-a-central"
  ip_cidr_range = "10.0.1.0/24"
  region = "us-central1"
  network  = "network-a"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create subnets
resource "google_compute_subnetwork" "west-subnet" {
  name   = "subnet-a-west"
  region = "us-west1"
  ip_cidr_range = "10.0.2.0/24"
  network  = "network-a"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create HA VPN gateway
resource "google_compute_ha_vpn_gateway" "ha_gateway1" {
  provider = "google-beta"
  region   = "us-central1"
  name     = "ha-vpn-gw-a"
  network  = "network-a"
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create cloud router
resource "google_compute_router" "router-a" {
  name    = "router-a"
  network = "network-a"
  bgp {
    asn = 65001
  }
  depends_on = [google_compute_network.ha-vpn-test-network]
}

// Create external aka peer gateway
resource "google_compute_external_vpn_gateway" "external_gateway" {
  provider        = "google-beta"
  name            = "peer-gw"
  redundancy_type = "TWO_IPS_REDUNDANCY"
  description     = "An externally managed VPN gateway"
  interface {
    id = 0
    ip_address = "209.119.81.225"
  }
  interface {
    id = 1
    ip_address = "209.119.81.226"
  }
}

// Create first VPN tunnel
resource "google_compute_vpn_tunnel" "tunnel0" {
  provider         = "google-beta"
  name             = "tunnel-a-to-on-prem-if-0"
  region           = "us-central1"
  vpn_gateway      = "ha-vpn-gw-a"
  peer_external_gateway = "peer-gw"
  peer_external_gateway_interface = 0
  shared_secret    = "mysharedsecret"
  router           = "router-a"
  vpn_gateway_interface = 0
  depends_on = [google_compute_router.router-a,google_compute_ha_vpn_gateway.ha_gateway1,google_compute_external_vpn_gateway.external_gateway]
}

// Create second VPN tunnel
resource "google_compute_vpn_tunnel" "tunnel1" {
  provider         = "google-beta"
  name             = "tunnel-a-to-on-prem-if-1"
  region           = "us-central1"
  vpn_gateway      = "ha-vpn-gw-a"
  peer_external_gateway = "peer-gw"
  peer_external_gateway_interface = 0
  shared_secret    = "mysharedsecret"
  router           = "router-a"
  vpn_gateway_interface = 1
  depends_on = [google_compute_router.router-a,google_compute_ha_vpn_gateway.ha_gateway1,google_compute_external_vpn_gateway.external_gateway]
}

// Create first cloud router interface
resource "google_compute_router_interface" "router1_interface0" {
  provider = "google-beta"
  name       = "if-tunnel-a-to-on-prem-if-0"
  router     = "router-a"
  region     = "us-central1"
  vpn_tunnel = "tunnel-a-to-on-prem-if-0"
  depends_on = [google_compute_router.router-a,google_compute_vpn_tunnel.tunnel0]
}

// Create first BGP peer
resource "google_compute_router_peer" "router1_peer0" {
  provider = "google-beta"
  name                      = "peer-0"
  router                    = "router-a"
  region                    = "us-central1"
  peer_asn                  = 65002
  advertised_route_priority = 100
  interface                 = "if-tunnel-a-to-on-prem-if-0"
  depends_on = [google_compute_router.router-a,google_compute_router_interface.router1_interface0]
}

// Create second cloud router interface
resource "google_compute_router_interface" "router1_interface1" {
  provider = "google-beta"
  name       = "if-tunnel-a-to-on-prem-if-1"
  router     = "router-a"
  region     = "us-central1"
  vpn_tunnel = "tunnel-a-to-on-prem-if-1"
  depends_on = [google_compute_router.router-a,google_compute_vpn_tunnel.tunnel1]
}

// Create second BGP peer
resource "google_compute_router_peer" "router1_peer1" {
  provider = "google-beta"
  name                      = "peer-1"
  router                    = "router-a"
  region                    = "us-central1"
  peer_asn                  = 65002
  advertised_route_priority = 100
  interface                 = "if-tunnel-a-to-on-prem-if-1"
  depends_on = [google_compute_router.router-a,google_compute_router_interface.router1_interface1]
}

// Create firewall rule to allow traffic from on-prem
resource "google_compute_firewall" "from-on-prem-1" {
  name    = "on-prem-to-network-a"
  network = "network-a"

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  depends_on = [google_compute_network.ha-vpn-test-network]
}
```

## Cleaning up

Destroy the resources created by Terraform:

```sh
terraform destroy
```
