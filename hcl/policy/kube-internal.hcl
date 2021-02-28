path "kv/*" {
  capabilities = [
    "read",
    "list"
  ]
}

// List existing policies
path "sys/policies/acl" {
  capabilities = [
    "list"
  ]
}

// Create and manage ACL policies
path "sys/policies/acl/*" {
  capabilities = [
    "create",
    "read",
    "update",
    "delete",
    "list"
  ]
}

// Manage auth methods broadly across Vault
path "auth/*"
{
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

// Create, update, and delete auth methods
path "sys/auth/*"
{
  capabilities = ["create", "update", "delete", "sudo"]
}