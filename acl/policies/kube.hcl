# Allow to read all the secrets to the Kubernetes deployments using the Injector sidecar.
path "kv/*" {
  capabilities = ["read", "list"]
}

# List existing policies
path "sys/policies/acl"
{
  capabilities = ["list"]
}

# Create and manage ACL policies
path "sys/policies/acl/*"
{
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

