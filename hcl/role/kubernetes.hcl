role "kube-internal" {
  enabled = true

  auth_path = "kubernetes"

  bound_service_account_name = "elpis-tools-vault"
  bound_service_account_namespace = "elpis-tools"
  wrap_ttl = "1h"
  policies = [
    "kube-internal"
  ]
  type = "kubernetes"
}

role "vault-injector" {
  enabled = true

  auth_path = "vault-injector"

  bound_service_account_name = "elpis-tools-vault-agent-injector"
  bound_service_account_namespace = "elpis-tools"
  wrap_ttl = "1h"
  policies = [
    "kube-internal"
  ]
  type = "kubernetes"
}

role "kube-dev" {
  enabled = true

  auth_path = "kube-dev"

  bound_service_account_name = "default"
  bound_service_account_namespace = "elpis-dev"
  wrap_ttl = "1h"
  policies = [
    "kube-dev"
  ]
  type = "kubernetes"
}