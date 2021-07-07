import json
import os
from configparser import ConfigParser

from exceptions import ChainCatchModifiedException


class AppProperties(object):
    def __init__(self):
        self.__config = ConfigParser()
        self.__config.read(f'{os.environ["HOME"]}/application.properties')

    def read(self, section_name: str, property_key: str):
        return self.__config[section_name][property_key]


class VaultProperties(AppProperties):
    @property
    def vault_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.address')

    @property
    def vault_ping_address(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.ping.address')

    @property
    def vault_kube_internal_policies(self) -> list:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.policies').split(',')

    @property
    def vault_kube_internal_role_name(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.role')

    @property
    def vault_kube_internal_ttl(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.kubernetes.internal.wrapTTL')

    @property
    def vault_key_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.key.threshold'))

    @property
    def vault_key_shares(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.key.shares'))

    @property
    def vault_ping_initial_delay_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.initialDelaySeconds'))

    @property
    def vault_ping_failure_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.failureThreshold'))

    @property
    def vault_ping_period_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.periodSeconds'))

    @property
    def vault_ping_success_threshold(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.successThreshold'))

    @property
    def vault_ping_timeout_seconds(self) -> int:
        return int(self.read(VaultProperties.__name__, 'vault.ping.timeoutSeconds'))

    @property
    def vault_ping_log_level(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.ping.log.level')

    @property
    def vault_client_log_level(self) -> str:
        return self.read(VaultProperties.__name__, 'vault.client.log.level')


class Steps(object):
    def __init__(self):
        self.__registry: dict = {}

    def step(self, step: str):
        self.__registry[step] = {
            'state': 'none'
        }

        return self

    def state(self, step: str, state: str):
        self.__registry[step] = {
            'state': state
        }

        return self

    def reason(self, step: str, state: str, reason: str):
        self.__registry[step] = {
            'state': state,
            'reason': reason
        }

        return self

    def to_str(self):
        return json.dumps(self.__registry)


class Reject(object):
    def __init__(self, exception: Exception):
        self.__exception = exception

    @property
    def exception(self) -> Exception:
        return self.__exception


class Resolve(object):
    def __init__(self, result: None):
        self.__result = result

    @property
    def result(self):
        return self.__result


class Chain(object):
    def __init__(self):
        self.__call_stack = []

        self.__rejected = False
        self.__error_handler = lambda e: None

        self.__previous_result = None

    def then(self, result_processor):
        self.__call_stack.append(result_processor)

        return self

    def catch(self, error_handler):
        self.__error_handler = error_handler

        return self

    def done(self):
        for method in self.__call_stack:
            if not self.__rejected:
                try:
                    result = method(self.__previous_result)
                    if isinstance(result, Reject):
                        self.__rejected = True
                        self.__error_handler(result.exception)
                    elif isinstance(result, Resolve):
                        self.__previous_result = result.result
                    else:
                        self.__previous_result = result
                except Exception as e:
                    self.__rejected = True
                    self.__error_handler(e)
            else:
                break

    @classmethod
    def reject(cls, exception: Exception):
        return Reject(exception)

    @classmethod
    def resolve(cls, result):
        return Resolve(result)

    @classmethod
    def fill(cls, initial_value):
        chain = Chain()
        chain.__previous_result = initial_value
        return chain

    @classmethod
    def link(cls):
        return Chain()
