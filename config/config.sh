#!/bin/sh
stty -echo

start_time="$(date -u +%s.%N)"

# Navigate to the Vault Base folder.
cd "$HOME" || exit 1

# Create new folder that would contain the cluster keys.
mkdir keys

# Navigate to the keys folder.
cd ./keys || exit 1

echo "Initiating vault..."

# Initiate vault with single-instanced key and save it to the cluster-keys.json file.
vault operator init -key-shares=1 -key-threshold=1 -format=json > cluster-keys.json

echo "Done!"

# Get and store Vault's Root and Unseal tokens into variables.
VAULT_UNSEAL_KEY=$(cat cluster-keys.json | jq -r ".unseal_keys_b64[]")
VAULT_ROOT_TOKEN=$(cat cluster-keys.json | jq -r ".root_token")

echo "Unsealing vault..."

# Unseal Vault with saved key.
vault operator unseal "$VAULT_UNSEAL_KEY"

echo "Done!"
echo "Authentication attempt..."

# Login as root user to enable the Vault API.
vault login "$VAULT_ROOT_TOKEN"

echo "Success!"

# Enable KV2 Secret Storage Engine.
vault secrets enable -path=secret kv-v2

echo "KV Engine was enabled."

## Policies

cd "$VAULT_INIT_HOME/vault-config/acl" || exit 1

echo "Applying required policies..."

# Iterate through all the policies inside the folder and apply them to Vault config.
for filename in policies/*.hcl; do
    [ -e "$filename" ] || continue

    vault policy write "$filename" "$filename.hcl"
done

echo "Done!"

## User/Password Auth

vault auth enable userpass

## Kubernetes auth

echo "Enabling Kubernetes authentication..."

# Enable Kubernetes authentication.
vault auth enable kubernetes

echo "Done!"
echo "Writing Kubernetes configuration..."

# Write k8s configuration properties within Vault.
vault write auth/kubernetes/config \
        token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
        kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
        kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

echo "Done!"
echo "Writing Kubernetes role..."

# Create and apply a new k8s role based on the policy.
vault write auth/kubernetes/role/kube \
        bound_service_account_names="$VAULT_K8S_NAMESPACE-vault" \
        bound_service_account_namespaces="$VAULT_K8S_NAMESPACE" \
        policies=kube \
        ttl=24h

echo "Done!"

end_time="$(date -u +%s.%N)"
elapsed="$(bc <<<"$end_time-$start_time")"

echo "Finished successfully in $elapsed seconds."
