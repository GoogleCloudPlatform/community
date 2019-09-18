provider "google" {
  credentials = file("<SERVICE ACCOUNT>.json")

  project = "<PROJECT ID>"
  region  = "europe-west3"
  zone    = "europe-west3-a"
}

resource "google_container_cluster" "gke-cluster" {
  name               = "tf-gke-cluster"
  network            = "default"
  zone               = "europe-west3-a"
  initial_node_count = 3

  provisioner "local-exec" {
    command = "gcloud container clusters get-credentials ${google_container_cluster.gke-cluster.name} --zone ${google_container_cluster.gke-cluster.zone} --project <PROJECT ID>"
  }
}

