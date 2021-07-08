role "kube-dev" {
  enabled = true

  auth_path = "dev"

  bound_service_account_name = "dev"
  bound_service_account_namespace = "elpis-dev"
  wrap_ttl = "1h"
  policies = [
    "kube-dev"
  ]
  type = "kubernetes"
}
