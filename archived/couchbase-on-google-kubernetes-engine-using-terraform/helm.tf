provider "kubernetes" {
  version = ">= 1.4.0"
 }

 resource "kubernetes_service_account" "tiller" {
  depends_on = [google_container_cluster.gke-cluster]
  metadata {
  name      = "terraform-tiller"
  namespace = "kube-system"
  }

  automount_service_account_token = true
}

resource "kubernetes_cluster_role_binding" "tiller" {
  depends_on = [google_container_cluster.gke-cluster]
  metadata {
    name = "terraform-tiller"
  }

  role_ref {
    kind      = "ClusterRole"
    name      = "cluster-admin"
    api_group = "rbac.authorization.k8s.io"
  }

  subject {
    kind = "ServiceAccount"
    name = "terraform-tiller"
    namespace = "kube-system"
  }
}

provider "helm" {
  version        = "~> 0.9"
  install_tiller = true
  service_account = "${kubernetes_service_account.tiller.metadata.0.name}"
  namespace       = "${kubernetes_service_account.tiller.metadata.0.namespace}"
  tiller_image    = "gcr.io/kubernetes-helm/tiller:v2.14.0"
}

data "helm_repository" "couchbase" {
    name = "couchbase"
    url  = "https://couchbase-partners.github.io/helm-charts/"
}

resource "helm_release" "cb-operator" {
  depends_on = [kubernetes_service_account.tiller]
    name       = "cb-operator"
    repository = "${data.helm_repository.couchbase.metadata.0.name}"
    chart      = "couchbase-operator"
}

resource "helm_release" "cb-cluster" {
  depends_on = [kubernetes_service_account.tiller]
    name       = "cb-cluster"
    repository = "${data.helm_repository.couchbase.metadata.0.name}"
    chart      = "couchbase-cluster"
}

