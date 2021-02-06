import asyncio
import glob
import logging
import os

import async_hvac
import requests

from slack import SlackClient


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

    async def run(self, request) -> bool:
        if self.__closed:
            return False

        failures = 0
        successes = 0

        self.__log.info(f'Health probe started...')

        await asyncio.sleep(self.__initial_delay_seconds)

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
            except ConnectionError:
                failures += 1
                self.__log.info(f'Health probe failed.')

            if not successes == self.__success_threshold:
                self.__log.info(f'Retrying...')
                await asyncio.sleep(self.__period_seconds)

        if failures == self.__failure_threshold:
            self.__closed = True

            self.__log.error(f'Health probe failed for current request. Please, double-check if source is alive.')

        return successes == self.__success_threshold and not failures == self.__failure_threshold


class VaultClient(object):
    def __init__(self, full_verbose: bool = False):
        self.__api = None

        self.__slack_client = SlackClient(full_verbose)

        self.__probe = lambda initial_delay_seconds=5: HealthProbe(full_verbose=full_verbose,
                                                                   initial_delay_seconds=initial_delay_seconds)

        self.__log = logging.getLogger(VaultClient.__class__.__name__)
        self.__log.setLevel(logging.INFO if full_verbose else logging.ERROR)

        self.__key_shares = 2
        self.__key_threshold = 2

        self.__root_token = None

    async def __aenter__(self):
        health_probe = self.__probe(1)

        if not await health_probe.run(
                lambda: requests.get(f"{os.environ['VAULT_ADDR']}{os.environ['VAULT_PING_ADDR']}")) \
                or health_probe.is_closed():
            return None

        self.__api = async_hvac.AsyncClient(url=os.environ['VAULT_ADDR'])
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        if self.__api:
            await self.__api.close()

        if self.__root_token:
            self.__root_token = None

    async def kube_auth(self):
        f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
        jwt = f.read()

        await self.__api.auth_kubernetes(role=os.environ['GITHUB_USER_POLICY'], jwt=jwt)

        return True

    async def enable_secrets(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if await client.is_initialized() and not await client.is_sealed() and await client.is_authenticated():
            backends = await client.list_secret_backends()
            if "kv-v2/" not in backends:
                self.__log.info(f'Enabling KV2 secret engine...')

                await client.enable_secret_backend('kv-v2', mount_point='kv')

                self.__log.info(f'Enabled successfully!')

        return True

    async def apply_policies(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if await client.is_initialized() and not await client.is_sealed() and await client.is_authenticated():
            policies_path = f'/init/acl/policies'

            for filename in glob.glob(os.path.join(policies_path, '*.hcl')):
                head, policy_name = os.path.split(os.path.splitext(filename)[0])

                with open(filename, 'r') as f:
                    policy = f.read()

                    await client.set_policy(policy_name, policy)

        return True

    async def enable_auth(self) -> bool:
        client = self.__api
        client.token = self.__root_token

        if await client.is_initialized() and not await client.is_sealed() and await client.is_authenticated():
            backends = await client.list_auth_backends()
            if "github/" not in backends:
                self.__log.info(f'Enabling GitHub authentication...')

                await client.enable_auth_backend('github')
                await client.write('auth/github/config', None, organization=os.environ['GITHUB_ORG_NAME'])
                await client.write(f'auth/github/map/teams/{os.environ["GITHUB_TEAM_NAME"]}',
                                   None, value=os.environ['GITHUB_USER_POLICY'])

                self.__log.info(f'GitHub enabled!')

            if "kubernetes/" not in backends:
                self.__log.info(f'Enabling Kubernetes authentication...')

                await client.enable_auth_backend('kubernetes')
                f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
                jwt = f.read()
                await client.write('auth/kubernetes/config', None, token_reviewer_jwt=jwt,
                                   kubernetes_host=f"https://{os.environ['KUBERNETES_PORT_443_TCP_ADDR']}:443",
                                   kubernetes_ca_cert="@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
                await client.write(f'auth/kubernetes/role/{os.environ["KUBE_POLICY"]}', wrap_ttl='24h',
                                   bound_service_account_names=f"{os.environ['VAULT_K8S_NAMESPACE']}-vault",
                                   bound_service_account_namespaces=os.environ['VAULT_K8S_NAMESPACE'],
                                   policies=os.environ["KUBE_POLICY"])

                self.__log.info(f'Kubernetes enabled!')

            return True

        return False

    async def init_vault(self) -> bool:
        client = self.__api

        if not await client.is_initialized():
            self.__log.info(f'Vault is not initialized. Initializing...')

            init_result = await client.initialize(self.__key_shares, self.__key_threshold)

            unseal_keys = init_result['keys']
            self.__root_token = init_result['root_token']

            if await client.is_initialized() and await client.is_sealed():
                self.__log.info(f'Vault was initialized. Unsealing vault...')

                await client.unseal_multi(unseal_keys)

                if not await client.is_sealed():
                    self.__log.info(f'Vault was unsealed. Happy using!')

                    unseal_message = f':lock: Vault was initialized!{os.linesep}' \
                                     ':heavy_exclamation_mark: Please, keep these ' \
                                     'unseal keys in safe place: '

                    for key in unseal_keys:
                        unseal_message += os.linesep + f':key:  {key}'

                    await self.__slack_client.post_message(unseal_message)
        else:
            self.__log.info(f'Vault was already initialized.')

            return False

        return await client.is_initialized() and not await client.is_sealed()
