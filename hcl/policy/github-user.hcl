# TODO: Could be good to wrap policy into HCL object - it may reduce the quantity of files in the Policy folder
# TODO: May group by the auth type as well
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