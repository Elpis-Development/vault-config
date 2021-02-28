auth "kubernetes" {
  enabled = true
  type = "kubernetes"
  description = "Auth backend for same-namespaced vault actions from K8S side."
}

auth "kube-injector" {
  enabled = true
  type = "kubernetes"
  description = "Auth backend for same-namespaced vault actions from K8S side."
}

auth "kube-dev" {
  enabled = true
  type = "kubernetes"
  description = "Auth backend to establish Kubernetes auth for the DEV applications."
}