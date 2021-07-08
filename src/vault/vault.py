import functools
import logging
import os
import threading
import time
from typing import Final

import hvac
import requests

from exceptions import HealthProbeFailedException, VaultNotReadyException, ValidationException, \
    VaultClientNotAuthenticatedException
from kube.client import KubernetesClient
from .config import HCLConfigBundle, ConfigType, VaultProperties

FAILURE_THRESHOLD = 2
INITIAL_DELAY = 5
PERIOD = 5
SUCCESS_THRESHOLD = 1
TIMEOUT = 3


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)

    return _wrap


class HealthProbe(object):
    def __init__(self, log_level: str = 'INFO', failure_threshold: int = FAILURE_THRESHOLD,
                 initial_delay_seconds: int = INITIAL_DELAY, period_seconds: int = PERIOD,
                 success_threshold: int = SUCCESS_THRESHOLD, timeout_seconds: int = TIMEOUT):

        self.__log = logging.getLogger(HealthProbe.__name__)
        self.__log.setLevel(log_level)

        self.__failure_threshold = failure_threshold
        self.__initial_delay_seconds = initial_delay_seconds
        self.__period_seconds = period_seconds
        self.__success_threshold = success_threshold
        self.__timeout_seconds = timeout_seconds
        self.__closed = False

    def is_closed(self) -> bool:
        return self.__closed

    def run(self, request) -> bool:
        if self.__closed:
            return False

        failures = 0
        successes = 0

        self.__log.info('Health probe started...')

        time.sleep(self.__initial_delay_seconds)

        while not failures == self.__failure_threshold and not successes == self.__success_threshold:
            self.__log.info('Trying to perform health probe...')

            try:
                response = request()

                if response.status_code == 200:
                    successes += 1
                    self.__log.info('Health probe succeeded!')
                else:
                    failures += 1
                    self.__log.info('Health probe failed.')
            except Exception as e:
                failures += 1
                self.__log.info('Health probe failed.')
                self.__log.error(e)

            if not successes == self.__success_threshold:
                self.__log.info('Retrying...')
                time.sleep(self.__period_seconds)

        if failures == self.__failure_threshold:
            self.__closed = True

            self.__log.error('Health probe failed for current request. Please, double-check if source is alive.')

            raise HealthProbeFailedException

        return successes == self.__success_threshold and not failures == self.__failure_threshold


class VaultClient(object):
    MAX_SHARES: Final = 10
    KEY_SEPARATOR: Final = '=' * 86

    def __init__(self):
        self.__vault_properties = VaultProperties()

        self.__log = logging.getLogger(VaultClient.__name__)
        self.__log.setLevel(self.__vault_properties.vault_client_log_level)

        if self.__vault_properties.vault_key_shares > VaultClient.MAX_SHARES \
                or self.__vault_properties.vault_key_threshold > VaultClient.MAX_SHARES:
            raise ValidationException(f'Vault keys cannot be split for more than {VaultClient.MAX_SHARES} parts')

        self.__config_bundle = HCLConfigBundle(self.__vault_properties.vault_client_log_level)

        self.__probe = lambda initial_delay_seconds=5: HealthProbe(
            log_level=self.__vault_properties.vault_client_log_level,
            initial_delay_seconds=initial_delay_seconds)

        if not self.vault_ready():
            raise VaultNotReadyException

        self.__api = hvac.Client(url=self.__vault_properties.vault_address)
        self.__kube_client = KubernetesClient(self.__vault_properties.vault_client_log_level)

        self.__root_token = None

        self.__role_actions = {
            'github': lambda role_name, role: self.__config_github(role_name, role),
            'kubernetes': lambda role_name, role: self.__config_kube(role_name, role)
        }

    # Private helpers
    def __enable_incluster_kube_auth(self):
        sa_name = self.__kube_client.get_service_account_name_for_pod(f'{os.environ["VAULT_K8S_NAMESPACE"]}-vault-0',
                                                                      os.environ['VAULT_K8S_NAMESPACE'])

        self.__log.info(f'Enabling internal Kubernetes auth on /kubernetes with role: ' +
                        f'{self.__vault_properties.vault_kube_internal_role_name} for account: {sa_name} ' +
                        f'with policies: {self.__vault_properties.vault_kube_internal_policies}')

        self.__api.sys.enable_auth_method(method_type='kubernetes', path='kubernetes')

        f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
        jwt = f.read()

        self.__api.write(f'auth/kubernetes/config', None, token_reviewer_jwt=jwt,
                         kubernetes_host=f"https://{os.environ['KUBERNETES_PORT_443_TCP_ADDR']}:443",
                         kubernetes_ca_cert='@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt')

        self.__api.write(f'auth/kubernetes/role/{self.__vault_properties.vault_kube_internal_role_name}',
                         wrap_ttl=self.__vault_properties.vault_kube_internal_ttl,
                         bound_service_account_names=sa_name,
                         bound_service_account_namespaces=os.environ['VAULT_K8S_NAMESPACE'],
                         policies=self.__vault_properties.vault_kube_internal_policies)

        self.__log.info('Internal Kubernetes auth at /kubernetes was enabled.')

    def __config_github(self, role_name: str, role: dict):
        self.__log.info(f'Configuring GitHub role {role_name}...')

        self.__api.write(f'auth/{role["auth_path"]}/config', None, organization=role['org'])

        policies = ','.join(role['policies'])

        self.__api.write(f'auth/{role["auth_path"]}/map/teams/{role["team_name"]}', None,
                         value=policies)

        self.__log.info(f'GitHub role {role_name} is set up.')

    def __config_kube(self, role_name: str, role: dict):
        self.__log.info(f'Configuring Kubernetes role {role_name}...')

        namespace = role['bound_service_account_namespace']
        sa_name = role['bound_service_account_name']

        secrets = self.__kube_client.get_service_account_secrets(sa_name, namespace)

        self.__api.write(f'auth/{role["auth_path"]}/config', None, token_reviewer_jwt=secrets['jwt'],
                         kubernetes_host=f"https://{os.environ['KUBERNETES_PORT_443_TCP_ADDR']}:443",
                         kubernetes_ca_cert=secrets['ca'],
                         disable_local_ca_jwt=True)

        self.__api.write(f'auth/{role["auth_path"]}/role/{role_name}', wrap_ttl=role['wrap_ttl'],
                         bound_service_account_names=sa_name,
                         bound_service_account_namespaces=namespace,
                         policies=role['policies'])

        self.__log.info(f'Kubernetes role {role_name} is set up.')

    # Misc
    @synchronized
    def void_root_token(self) -> bool:
        self.__root_token = None

        return True

    @synchronized
    def close_client(self):
        self.void_root_token()
        self.__api.adapter.close()

    @synchronized
    def vault_ready(self):
        health_probe = self.__probe(self.__vault_properties.vault_ping_initial_delay_seconds)

        if not health_probe.run(
                lambda: requests.get(self.__vault_properties.vault_ping_address)) \
                or health_probe.is_closed():
            raise HealthProbeFailedException

        return True

    @synchronized
    def is_sealed(self):
        if not self.auth():
            raise VaultClientNotAuthenticatedException()

        client = self.__api

        return client.sys.is_sealed()

    @synchronized
    def is_running(self):
        if not self.auth():
            raise VaultClientNotAuthenticatedException()

        client = self.__api

        return client.sys.is_initialized() and not client.sys.is_sealed()

    # Core
    @synchronized
    def auth(self):
        if self.__root_token:
            self.__api.token = self.__root_token
        elif "kubernetes/" in self.__api.sys.list_auth_methods():
            f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
            jwt = f.read()

            self.__api.auth_kubernetes(role=self.__vault_properties.vault_kube_internal_role_name, jwt=jwt)

        return self.__api.is_authenticated()

    @synchronized
    def enable_secrets(self):
        if not self.auth():
            return False

        client = self.__api

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            backends = client.sys.list_mounted_secrets_engines()

            secrets = self.__config_bundle.get_whole_bundle_config(ConfigType.SECRET)

            for secret in secrets:
                secret_engine = secrets[secret]['engine']

                if self.__config_bundle.is_bundle_config_enabled(ConfigType.SECRET, secret):
                    self.__log.info(f'Enabling {secret_engine} on path /{secret}.')

                    client.sys.enable_secrets_engine(secret_engine, path=secret)
                elif f'{secret}/' in backends:
                    self.__log.info(f'Disabling {secret_engine} on path /{secret}.')

                    client.sys.disable_secrets_engine(secret)

            return True
        else:
            return False

    @synchronized
    def apply_policies(self):
        if not self.auth():
            return False

        client = self.__api

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            policy_backends = client.sys.list_policies()

            policies = self.__config_bundle.get_whole_bundle_config(ConfigType.POLICY)

            for policy in policies:
                if self.__config_bundle.is_bundle_config_enabled(ConfigType.POLICY, policy):
                    self.__log.info(f'Enabling policy {policy}.')

                    client.sys.create_or_update_policy(policy, policies[policy]['config'])
                elif f'{policy}/' in policy_backends:
                    self.__log.info(f'Disabling policy {policy}.')

                    client.sys.delete_policy(policy)

            return True
        else:
            return False

    @synchronized
    def enable_auth_backends(self):
        if not self.auth():
            return False

        client = self.__api

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            self.__enable_incluster_kube_auth()

            auth_backends = client.sys.list_auth_methods()

            auth_list = self.__config_bundle.get_whole_bundle_config(ConfigType.AUTH)

            for auth_path in auth_list:
                auth_type = auth_list[auth_path]['type']

                if self.__config_bundle.is_bundle_config_enabled(ConfigType.AUTH, auth_path):
                    self.__log.info(f'Enabling {auth_type} on path /{auth_path}.')

                    client.sys.enable_auth_method(method_type=auth_type,
                                                  description=auth_list[auth_path]["description"],
                                                  path=auth_path)
                elif f'{auth_path}/' in auth_backends:
                    self.__log.info(f'Disabling {auth_type} on path /{auth_path}.')

                    client.sys.disable_auth_method(auth_path)

            return True
        else:
            return False

    @synchronized
    def apply_auth_roles(self):
        if not self.auth():
            return False

        client = self.__api

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            auth_backends = client.sys.list_auth_methods()

            roles = self.__config_bundle.get_whole_bundle_config(ConfigType.ROLE)

            for role_name in roles:
                role = roles[role_name]

                if f'{role["auth_path"]}/' in auth_backends and role['type'] in self.__role_actions \
                        and self.__config_bundle.is_bundle_config_enabled(ConfigType.ROLE, role_name):
                    self.__role_actions[role['type']](role_name, role)
                elif f'{role["auth_path"]}/' in auth_backends:
                    self.__api.delete(f'auth/{role["auth_path"]}/config')

            return True
        else:
            return False

    @synchronized
    def init_vault(self) -> bool:
        client = self.__api

        if not client.sys.is_initialized():
            self.__log.info('Vault is not initialized. Initializing...')

            init_result = client.sys.initialize(
                self.__vault_properties.vault_key_shares,
                self.__vault_properties.vault_key_threshold
            )

            unseal_keys = init_result['keys']
            self.__root_token = init_result['root_token']

            if client.sys.is_initialized() and client.sys.is_sealed():
                log_message = f"Vault was initialized! Performing unseal... Please, share this info only with " \
                              f"trusted sources!'"

                for key in unseal_keys:
                    self.__api.sys.submit_unseal_key(key)

                    log_message += f"\n{VaultClient.KEY_SEPARATOR}\n Vault unseal key: {key} \n{VaultClient.KEY_SEPARATOR}"

                self.__log.info(log_message)
                self.__log.info('Vault was unsealed.')
        else:
            self.__log.info('Vault was already initialized.')

        return client.sys.is_initialized() and not client.sys.is_sealed()
