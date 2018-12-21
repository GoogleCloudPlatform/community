variable "acme_registration_email" {
  description = "email address to associate with ACME server registration"
}

variable "managed_zone" {
  description = "Cloud DNS managed zone"
}

variable "project" {
  description = "Cloud Platform project that hosts the notebook server(s)"
}

variable "servername" {
  description = "name of notebook server Compute Engine instance"
}

variable "acme_server_url" {
  description = "URL of the ACME server that will generate certificates"
  default = "https://acme-v02.api.letsencrypt.org/directory"
}

variable "disk_size" {
  description = "size, in gigabytes, of the notebook server boot disk"
  default = "16"
} 

variable "jupyter_server_port" {
  description = "port the notebook server will listen on"
  default = "8089"
}

variable "machine_type" {
  description = "type of Compute Engine instance to create for the notebook server"
  default = "n1-standard-2"
}

variable "network" {
  description = "Compute Platform network the notebook server will be connected to"
  default = "default"
}

variable "region" {
  description = "Compute Platform region where the notebook server will be located"
  default = "us-central1"
}

variable "use_acme_cert" {
  description = "true to create ACME certs for the notebook server, false to use self-signed certs"
  default = true
}

variable "zone" {
  description = "Compute Platform zone where the notebook server will be located"
  default = "us-central1-b"
}

