import functools
import glob
import logging
import os
import threading
import time

import hvac
import requests

from exceptions import HealthProbeFailedException, VaultNotReadyException, ValidationException
from util import VaultProperties, GithubProperties


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)

    return _wrap


class HealthProbe(object):
    def __init__(self, full_verbose: bool = False, failure_threshold: int = 2, initial_delay_seconds: int = 5,
                 period_seconds: int = 5, success_threshold: int = 1, timeout_seconds: int = 3):

        self.__log = logging.getLogger(HealthProbe.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

        self.__failure_threshold = failure_threshold
        self.__initial_delay_seconds = initial_delay_seconds
        self.__period_seconds = period_seconds
        self.__success_threshold = success_threshold
        self.__timeout_seconds = timeout_seconds
        self.__closed = False

    def is_closed(self) -> bool:
        return self.__closed is True

    def run(self, request) -> bool:
        if self.__closed:
            return False

        failures = 0
        successes = 0

        self.__log.info(f'Health probe started...')

        time.sleep(self.__initial_delay_seconds)

        while not failures == self.__failure_threshold and not successes == self.__success_threshold:
            self.__log.info(f'Trying to perform health probe...')

            try:
                response = request()

                if response.status_code == 200:
                    successes += 1
                    self.__log.info(f'Health probe succeeded!')
                else:
                    failures += 1
                    self.__log.info(f'Health probe failed.')
            except Exception:
                failures += 1
                self.__log.info(f'Health probe failed.')

            if not successes == self.__success_threshold:
                self.__log.info(f'Retrying...')
                time.sleep(self.__period_seconds)

        if failures == self.__failure_threshold:
            self.__closed = True

            self.__log.error(f'Health probe failed for current request. Please, double-check if source is alive.')

            raise HealthProbeFailedException

        return successes == self.__success_threshold and not failures == self.__failure_threshold


class VaultClient(object):
    def __init__(self):
        self.__vault_properties = VaultProperties()
        self.__github_properties = GithubProperties()

        self.__probe = lambda initial_delay_seconds=5: HealthProbe(full_verbose=self.__vault_properties.vault_ping_log_full_verbose,
                                                                   initial_delay_seconds=initial_delay_seconds)

        if not self.vault_ready():
            raise VaultNotReadyException

        self.__api = hvac.Client(url=self.__vault_properties.vault_address)

        self.__log = logging.getLogger(VaultClient.__class__.__name__)
        self.__log.setLevel(logging.INFO if self.__vault_properties.vault_client_log_full_verbose else logging.ERROR)

        if self.__vault_properties.vault_key_shares > 13 or self.__vault_properties.vault_key_threshold > 13:
            raise ValidationException("Vault keys cannot be split for more than 13 parts")

        self.__root_token = None

    @synchronized
    def vault_ready(self):
        health_probe = self.__probe(self.__vault_properties.vault_ping_initial_delay_seconds)

        if not health_probe.run(
                lambda: requests.get(self.__vault_properties.vault_ping_address)) \
                or health_probe.is_closed():
            raise HealthProbeFailedException

        return True

    @synchronized
    def close_client(self):
        self.__api.adapter.close()

    @synchronized
    def is_sealed(self):
        client = self.__api
        client.token = self.__root_token

        return client.sys.is_sealed()

    @synchronized
    def kube_auth(self):
        f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
        jwt = f.read()

        self.__api.auth_kubernetes(role=self.__vault_properties.vault_kube_policy_name, jwt=jwt)

        return True

    @synchronized
    def enable_secrets(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            backends = client.list_secret_backends()
            if "kv-v2/" not in backends:
                self.__log.info(f'Enabling KV2 secret engine...')

                client.sys.enable_secrets_engine('kv-v2', path='kv')

                self.__log.info(f'Enabled successfully!')

        return True

    @synchronized
    def apply_policies(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            policies_path = f'/init/acl/policies'

            for filename in glob.glob(os.path.join(policies_path, '*.hcl')):
                head, policy_name = os.path.split(os.path.splitext(filename)[0])

                with open(filename, 'r') as f:
                    policy = f.read()

                    client.sys.create_or_update_policy(policy_name, policy)

        return True

    @synchronized
    def enable_auth(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if client.sys.is_initialized() and not client.sys.is_sealed() and client.is_authenticated():
            backends = client.sys.list_auth_methods()
            if "github/" not in backends:
                self.__log.info(f'Enabling GitHub authentication...')

                client.sys.enable_auth_method('github')
                client.write('auth/github/config', None, organization=self.__github_properties.org_name)
                client.write(f'auth/github/map/teams/{self.__github_properties.team_name}',
                             None, value=self.__vault_properties.vault_github_policy_name)

                self.__log.info(f'GitHub enabled!')

            if "kubernetes/" not in backends:
                self.__log.info(f'Enabling Kubernetes authentication...')

                client.sys.enable_auth_method('kubernetes')
                f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
                jwt = f.read()
                client.write('auth/kubernetes/config', None, token_reviewer_jwt=jwt,
                             kubernetes_host=f"https://{os.environ['KUBERNETES_PORT_443_TCP_ADDR']}:443",
                             kubernetes_ca_cert="@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
                client.write(f'auth/kubernetes/role/{self.__vault_properties.vault_kube_policy_name}', wrap_ttl='24h',
                             bound_service_account_names=f"{os.environ['VAULT_K8S_NAMESPACE']}-vault",
                             bound_service_account_namespaces=os.environ['VAULT_K8S_NAMESPACE'],
                             policies=self.__vault_properties.vault_kube_policy_name)

                self.__log.info(f'Kubernetes enabled!')

            return True

        return False

    @synchronized
    def init_vault(self) -> bool:
        client = self.__api

        if not client.sys.is_initialized():
            self.__log.info(f'Vault is not initialized. Initializing...')

            init_result = client.sys.initialize(
                self.__vault_properties.vault_key_shares,
                self.__vault_properties.vault_key_threshold
            )

            unseal_keys = init_result['keys']
            self.__root_token = init_result['root_token']

            if client.sys.is_initialized() and client.sys.is_sealed():
                self.__log.info(f'Vault was initialized, but is sealed.')

                for key in unseal_keys:
                    print(os.linesep)
                    print(f"Vault unseal key: {key}")

                print(os.linesep)

        else:
            self.__log.info(f'Vault was already initialized.')

            return False

        return client.sys.is_initialized()
