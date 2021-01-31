# Allow to read all the secrets to the Kubernetes deployments using the Injector sidecar.
path "kv/*" {
  capabilities = ["read", "list", "create", "delete", "update"]
}

path "sys/tools/hash" {
  capabilities = ["update"]
}

path "sys/tools/hash/*" {
  capabilities = ["update"]
}