# Allow to read all the secrets to the Kubernetes deployments using the Injector sidecar.
path "secret/*" {
  capabilities = ["read"]
}

