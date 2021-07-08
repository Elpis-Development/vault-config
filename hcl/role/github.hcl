role "github-user" {
  enabled = true

  auth_path = "github"

  org = "Elpis-Development"
  team_name = "Alpha"
  policies = [
    "github-user"
  ]
  type = "github"
}
