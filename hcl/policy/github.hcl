policy "github-user" {
  enabled = true

  config {
    path "kv/*" {
      capabilities = [
        "read",
        "list",
        "create",
        "delete",
        "update"
      ]
    }

    path "sys/tools/hash" {
      capabilities = [
        "update"
      ]
    }

    path "sys/tools/hash/*" {
      capabilities = [
        "update"
      ]
    }
  }
}
