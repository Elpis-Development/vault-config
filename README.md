# Vault Init App [![BCH compliance](https://bettercodehub.com/edge/badge/Elpis-Development/vault-config?branch=main)](https://bettercodehub.com/) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/ee00ad76456649d4ba861ddd41b25e7c)](https://www.codacy.com/gh/Elpis-Development/vault-init/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Elpis-Development/vault-init&amp;utm_campaign=Badge_Grade) [![Total alerts](https://img.shields.io/lgtm/alerts/g/Elpis-Development/vault-config.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Elpis-Development/vault-config/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Elpis-Development/vault-config.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Elpis-Development/vault-config/context:python)

## Init Container Run

Deployed Vault application requires setup of the cluster keys and unsealing as well by default. Since the application is fully available from the Vault UI at that moment - we've introduced the auto-configuration process. Besides the standard processed of making the Vault working it also enables required auth methods and apply policies.

Before the Vault and Injector pods are started the custom Init Pod is started and executed. 

## Vault Pod Start

When the Vault deployment process is initiated the Vault-Init sidecar container is also launched in the same pod. The Vault-Init itself is a basic Python application that uses the HVAC library to talk with Vault application using the API. 

When Init app is started - the healh check is performed - the application tries to verify if Vault is UP and ready receive requests. After that - the chain of methods is executed:

```python
def main():
    vault.init_vault()

    while not vault.is_running():
        sleep(30)

    vault.enable_auth_backends()

    vault.enable_secrets()
    vault.apply_policies()
    vault.apply_auth_roles()

    vault.void_root_token()
```

It will start the initialization process and generate some keys required to work with Vault.
1. `init_vault()` - fetches the unseal keys and performs Vault unsealing.
2. After Vault is up and running - the `enable_auth_backends()` is called. It iterates all the .hcl files listed in /hcl/auth, parses them and enables described authentication backends.
3. `enable_secrets()`  do the same parse/post for files at path /hcl/secret. The main purpose is to enable/disable secret engines.
4. The next step is `apply_policies()`. HCL configs on /hcl/policy are read and processed. Based on those configs - app makes request to Vault to add new policy or edit the existing one.
5. `apply_auth_roles()` applies chosen Polices to selected Authentication backends by configs on /hcl/role.
6. After step 5 Vault should be fully configured and ready to go. As the last step we are voiding the Vault root token since it's keeping could cause the security violation. Since as a part of initializaion process we also enabling the internal Kubernetes authentication (so we would be able to take a Kube's JWT and use it to make requests to Vault) - we won't need it anymore.

#### Important! 
The unseal keys may be used to unseal the Vault after failures or restarts, so you'll need to get logs of Vault Init app and fetch the keys from there. You may use command:
```sh
kubectl logs elpis-tools-vault-0 -c "vault-init" | grep "Vault unseal key"
```

## Policy and Auth Management

For current state of things we do support only 4 types of custom configurations (backends setup): Authentications, Policies, Secrets, Roles. 

### Authentication
As an authentication types we do support only 2 of all the Vault may suggest - Github and Kubernetes. They are managed via .hcl confgurations placed at path `/hcl/auth`

#### Github
Github authentications configurations are not limited by the filenames or special file extentions - we just need a proper config for each auth entry:
```hcl
auth "<AUTH NAME (UNIQUE)>" {
  enabled = <TRUE/FALSE>
  type = "github"
  description = "<Any custom description>"
}
```

Example:
```hcl
auth "github" {
  enabled = true
  type = "github"
  description = "Custom GitHub authentication auth backend."
}
```

#### Kubernetes
Merely same as for Github but type should be hardcoded to kubernetes:
```hcl
auth "<AUTH NAME (UNIQUE)>" {
  enabled = <TRUE/FALSE>
  type = "kubernetes"
  description = "<Any custom description>"
}
```

Example:
```hcl
auth "dev" {
  enabled = true
  type = "kubernetes"
  description = "Auth backend to establish Kubernetes auth for the DEV applications."
}
```

#### Policy
Policies are set of rules that allow user to access specific Vault operations or vice-versa - post a deny. Those are managed via .hcl confgurations placed at path `/hcl/policy`

```hcl
policy "<POLICY NAME - UNIQUE>" {
  enabled = <TRUE/FALSE>

  config {
    //Here lies the internal vault configuration
  }
}
```

The config holds the interanl Vault policy configurations. How are those managed is available here: https://www.vaultproject.io/docs/concepts/policies

Example:
```hcl
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
```

#### Secret
Secret backend engines are described as HCL configurations on path `/hcl/secret`
Nothing special about secret configurations since they do consist of two fields:
```hcl
secret "<SECRET NAME - UNIQUE>" {
  enabled = <TRUE/FASLE>
  engine = "<ENGINE TYPE>"
}
```

Example:
```hcl
secret "kv" {
  enabled = true
  engine = "kv-v2"
}
```

The full list of available secret backends could be found here: https://www.vaultproject.io/docs/secrets

### Role
Roles are matching configurations that do include info from Authentications and Policies. They lie on `/hcl/role` 
There are two types of roles - Github and Kubernetes (as for Authentication engines)

#### Github
```hcl
role "<ROLE NAME - UNIQUE>" {
  enabled = <TRUE/FALSE>

  auth_path = "<The unique name of the Github authentication config>"

  org = "<Github Organisation Name>"
  team_name = "<Github Team Name>"
  policies = [
    "<SET OF POLICIES TO APPLY TO GITHUB USERS>"
  ]
  type = "github"
}
```

Example:
```hcl
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
```

#### Kubernetes
```hcl
role "<ROLE NAME - UNIQUE>" {
  enabled = <TRUE/FALSE>

  auth_path = "<The unique name of the Kubernetes authentication config>"

  bound_service_account_name = "<K8S Service Account name>"
  bound_service_account_namespace = "<Operating K8S Namespace>"
  wrap_ttl = "<Token Time-to-live>"
  policies = [
    "<SET OF POLICIES TO APPLY TO KUBERNETES ACCESS>"
  ]
  type = "kubernetes"
}
```

Example:
```hcl
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
```
